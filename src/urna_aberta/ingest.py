"""Ingestão de uma eleição: descobre o que falta e leva cada ZIP até o bronze.

discover  lista os arquivos novos, alterados ou ainda não carregados (matriz do Actions)
file      ingere um arquivo: download -> Volume -> bronze -> marca no manifesto
all       discover + file em sequência (execução local)
"""

import argparse
import json
import os
import re
import sys
import tempfile
import traceback
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import httpx
from tenacity.wait import wait_base

from urna_aberta.bronze import LoadResult, contract_para, load_zip
from urna_aberta.ckan import head, package_resources
from urna_aberta.config import ElectionConfig, load_election
from urna_aberta.contracts import Contract, load_all
from urna_aberta.download import sync_file, volume_path_for
from urna_aberta.manifest import Manifest, ManifestEntry

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config" / "elections"


def pendentes(
    client: httpx.Client,
    config: ElectionConfig,
    manifest: Manifest,
    contratos: dict[str, Contract],
    *,
    dataset: str | None = None,
    force: bool = False,
    wait: wait_base | None = None,
) -> list[dict[str, object]]:
    """CSVs com contrato que são novos, mudaram no CDN ou ainda não foram ao bronze.

    Do menor para o maior, para o arquivo de SP ser o último a rodar.
    """
    itens: list[dict[str, object]] = []
    for d in config.datasets:
        if not d.enabled or (dataset and d.id != dataset):
            continue
        for r in package_resources(client, d.id, wait):
            if r.format.upper() != "CSV":
                continue
            try:
                contract_para(r.url, contratos)
            except Exception:  # PDF, JPEG ou arquivo sem contrato: fora do bronze
                continue
            info = head(client, r.url, wait)
            e = manifest.get(r.url)
            mudou = e is None or (e.size, e.etag, e.last_modified) != (
                info.size,
                info.etag,
                info.last_modified,
            )
            if force or mudou or e.bronze_sha256 != e.sha256:  # type: ignore[union-attr]
                itens.append(
                    {
                        "url": r.url,
                        "dataset": d.id,
                        "arquivo": r.url.rsplit("/", 1)[1],
                        "size": info.size or 0,
                    }
                )
    return sorted(itens, key=lambda i: int(i["size"]))  # type: ignore[call-overload]


def processar(
    client: httpx.Client,
    url: str,
    *,
    workdir: Path,
    volume_path: str,
    manifest: Manifest,
    upload: Callable[[Path, str], None],
    carregar: Callable[[ManifestEntry], list[LoadResult]],
    force: bool = False,
) -> tuple[str, list[LoadResult]]:
    """Download (se mudou) e carga no bronze (se esse hash ainda não foi carregado)."""
    status = sync_file(
        client,
        url,
        workdir=workdir,
        volume_path=volume_path,
        manifest=manifest,
        upload=upload,
    )
    entry = manifest.get(url)
    assert entry is not None
    if entry.bronze_sha256 == entry.sha256 and not force:
        return status, []
    resultados = carregar(entry)  # só marca como carregado se a carga terminar
    manifest.put(replace(entry, bronze_sha256=entry.sha256))
    return status, resultados


def _eleicao(valor: str) -> str:
    if not re.fullmatch(r"\d{4}", valor):
        raise argparse.ArgumentTypeError("eleição deve ser um ano de 4 dígitos")
    return valor


def _http() -> httpx.Client:
    return httpx.Client(timeout=httpx.Timeout(30, read=120))


def _ingerir(
    url: str, eleicao: str, catalogo: str, force: bool
) -> tuple[str, list[LoadResult]]:
    from urna_aberta.databricks import (
        DatabricksManifest,
        Sql,
        download_from_volume,
        upload_to_volume,
        workspace,
    )

    w, executar = workspace(), Sql()
    manifest = DatabricksManifest(catalogo, executar)
    contrato = contract_para(url, load_all())
    with _http() as client, tempfile.TemporaryDirectory() as tmp:
        return processar(
            client,
            url,
            workdir=Path(tmp),
            volume_path=volume_path_for(url, catalogo, eleicao),
            manifest=manifest,
            upload=lambda local, dest: upload_to_volume(w, local, dest),
            carregar=lambda e: load_zip(
                contract=contrato,
                entry=e,
                fetch=lambda vol, local: download_from_volume(w, vol, local),
                put=lambda local, vol: upload_to_volume(w, local, vol),
                sql=executar,
                catalogo=catalogo,
            ),
            force=force,
        )


def _imprimir(url: str, status: str, resultados: list[LoadResult]) -> None:
    arquivo = url.rsplit("/", 1)[1]
    if not resultados:
        print(f"{arquivo}: {status}, já carregado no bronze")
        return
    linhas = sum(r.linhas for r in resultados)
    rej = sum(r.rejeitadas for r in resultados)
    print(
        f"{arquivo}: {status}, {linhas} linhas em {len(resultados)} arquivos, "
        f"{rej} rejeitadas"
    )


def _descobrir(
    eleicao: str, dataset: str | None, force: bool
) -> list[dict[str, object]]:
    from urna_aberta.databricks import DatabricksManifest

    config = load_election(CONFIG_DIR / f"{eleicao}.yaml")
    with _http() as client:
        return pendentes(
            client,
            config,
            DatabricksManifest(config.catalog),
            load_all(),
            dataset=dataset,
            force=force,
        )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    for nome in ("discover", "all"):
        s = sub.add_parser(nome)
        s.add_argument("--eleicao", type=_eleicao, default="2026")
        s.add_argument("--dataset")
        s.add_argument("--force", action="store_true")
    f = sub.add_parser("file")
    f.add_argument("--url", required=True)
    f.add_argument("--eleicao", type=_eleicao, default="2026")
    f.add_argument("--force", action="store_true")
    args = p.parse_args(argv)

    catalogo = os.environ.get("DATABRICKS_CATALOG", "urna")
    if args.cmd == "file":
        status, res = _ingerir(args.url, args.eleicao, catalogo, args.force)
        _imprimir(args.url, status, res)
        return 0

    itens = _descobrir(args.eleicao, args.dataset, args.force)
    if args.cmd == "discover":
        matriz = json.dumps({"include": itens}, separators=(",", ":"))
        print(f"{len(itens)} arquivos pendentes")
        if saida := os.environ.get("GITHUB_OUTPUT"):
            with open(saida, "a", encoding="utf-8") as fh:
                fh.write(f"matrix={matriz}\ncount={len(itens)}\n")
        else:
            print(matriz)
        return 0

    falhas: list[str] = []  # all: segue após uma falha e resume no fim
    for i, item in enumerate(itens, 1):
        url = str(item["url"])
        print(f"[{i}/{len(itens)}] {item['arquivo']}", flush=True)
        try:
            status, res = _ingerir(url, args.eleicao, catalogo, args.force)
            _imprimir(url, status, res)
        except Exception:  # noqa: BLE001
            traceback.print_exc()
            falhas.append(str(item["arquivo"]))
    print(f"concluído: {len(itens) - len(falhas)} ok, {len(falhas)} falhas {falhas}")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
