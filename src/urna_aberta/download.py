"""Download idempotente de arquivos do TSE: detecta mudança, baixa em streaming,
confere o tamanho, envia ao Volume e registra no manifesto."""

import argparse
import hashlib
import os
import tempfile
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import httpx
from tenacity.wait import wait_base

from urna_aberta.ckan import head, retrying
from urna_aberta.manifest import Manifest, ManifestEntry

CHUNK = 1 << 20  # 1 MiB


def stream_download(
    client: httpx.Client, url: str, dest: Path, wait: wait_base | None = None
) -> tuple[str, int]:
    """Baixa para `dest` em streaming e devolve (sha256, bytes).

    Escreve em `dest.part` e só renomeia no fim; qualquer falha apaga o parcial.
    Erro de rede e 5xx são repetidos; arquivo menor que o Content-Length também.
    # ponytail: sem retomada por byte (Range); cada tentativa recomeça do zero.
    """
    part = dest.with_name(dest.name + ".part")

    def go() -> tuple[str, int]:
        sha, n = hashlib.sha256(), 0
        try:
            with (
                client.stream("GET", url, follow_redirects=True) as r,
                part.open("wb") as f,
            ):
                r.raise_for_status()
                esperado = r.headers.get("content-length")
                for chunk in r.iter_bytes(CHUNK):
                    f.write(chunk)
                    sha.update(chunk)
                    n += len(chunk)
            if esperado is not None and n != int(esperado):
                raise httpx.ReadError(f"recebidos {n} de {esperado} bytes")
            os.replace(part, dest)
        except BaseException:
            part.unlink(missing_ok=True)
            raise
        return sha.hexdigest(), n

    return retrying(wait)(go)


def sync_file(
    client: httpx.Client,
    url: str,
    *,
    workdir: Path,
    volume_path: str,
    manifest: Manifest,
    upload: Callable[[Path, str], None],
    wait: wait_base | None = None,
) -> str:
    """Leva o arquivo do CDN ao Volume só se mudou: novo/inalterado/republicado."""
    info = head(client, url, wait)
    anterior = manifest.get(url)
    if (
        anterior
        and anterior.size == info.size
        and anterior.etag == info.etag
        and anterior.last_modified == info.last_modified
    ):
        return "inalterado"

    local = workdir / url.rsplit("/", 1)[1]
    try:
        sha, size = stream_download(client, url, local, wait)
        if anterior and anterior.sha256 == sha:
            status = "inalterado"  # metadado mudou, conteúdo não: não reenvia
        else:
            status = "republicado" if anterior else "novo"
            upload(local, volume_path)
    finally:
        local.unlink(missing_ok=True)  # o disco do runner é pequeno para ~50 GiB

    manifest.put(
        ManifestEntry(
            url=url,
            size=size,
            etag=info.etag,
            last_modified=info.last_modified,
            sha256=sha,
            status=status,
            volume_path=volume_path,
            downloaded_at=datetime.now(UTC).isoformat(timespec="seconds"),
            bronze_sha256=anterior.bronze_sha256
            if anterior and anterior.sha256 == sha
            else None,
        )
    )
    return status


def volume_path_for(url: str, catalogo: str, ano: int | str) -> str:
    """ZIP no Volume: /Volumes/<catalogo>/landing/tse/<tema>/<ano>/<arquivo>."""
    tema, arquivo = url.rsplit("/", 2)[-2:]
    return f"/Volumes/{catalogo}/landing/tse/{tema}/{ano}/{arquivo}"


def main(argv: list[str] | None = None) -> int:
    from urna_aberta.databricks import DatabricksManifest, upload_to_volume, workspace

    p = argparse.ArgumentParser(description="Baixa um arquivo do TSE para o Volume.")
    p.add_argument("--url", required=True)
    p.add_argument("--ano", default="2026")
    args = p.parse_args(argv)

    catalogo = os.environ.get("DATABRICKS_CATALOG", "urna")
    volume_path = volume_path_for(args.url, catalogo, args.ano)
    w = workspace()
    with httpx.Client(timeout=httpx.Timeout(30, read=120)) as client:
        with tempfile.TemporaryDirectory() as tmp:
            status = sync_file(
                client,
                args.url,
                workdir=Path(tmp),
                volume_path=volume_path,
                manifest=DatabricksManifest(catalogo),
                upload=lambda local, dest: upload_to_volume(w, local, dest),
            )
    print(f"{status}: {args.url} -> {volume_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
