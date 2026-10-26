# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "databricks-sdk>=0.40",
#   "databricks-sql-connector>=3.5",
#   "httpx>=0.27",
# ]
# ///
"""Gate de viabilidade: CDN do TSE -> Volume do Databricks -> leitura via SQL.

Uso: uv run scripts/viabilidade.py
Env: DATABRICKS_HOST, DATABRICKS_TOKEN (obrigatórias); DATABRICKS_CATALOG,
DATABRICKS_SCHEMA, DATABRICKS_VOLUME, DATABRICKS_WAREHOUSE_ID (opcionais).
O token nunca é impresso. Cada sonda imprime OK/FALHA; sai com 1 se alguma falhar.
"""

import hashlib
import io
import os
import sys
import zipfile
from collections.abc import Callable

import httpx
from databricks import sql
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import VolumeType

URL = (
    "https://cdn.tse.jus.br/estatistica/sead/odsele/"
    "detalhe_votacao_munzona/detalhe_votacao_munzona_2026.zip"
)
MEMBRO = "detalhe_votacao_munzona_2026_AC.csv"  # menor UF dentro do ZIP
falhas: list[str] = []


def sonda(
    nome: str, fn: Callable[[], object], obrigatoria: bool = True
) -> object | None:
    try:
        r = fn()
    except Exception as e:  # noqa: BLE001 - o objetivo é registrar qualquer falha
        msg = str(e).replace(os.environ["DATABRICKS_TOKEN"], "***")
        rotulo = "FALHA" if obrigatoria else "INFO "
        print(f"{rotulo} {nome}: {type(e).__name__}: {msg[:300]}")
        if obrigatoria:
            falhas.append(nome)
        return None
    print(f"OK    {nome}: {r}")
    return r


def idempotente(fn: Callable[[], object]) -> object:
    """Roda a criação; se o recurso já existe (execução anterior), não é falha."""
    try:
        return fn()
    except Exception as e:  # noqa: BLE001
        if "already exists" in str(e):
            return "ja existia"
        raise


def main() -> int:
    host = os.environ["DATABRICKS_HOST"].rstrip("/")
    token = os.environ["DATABRICKS_TOKEN"]
    cat = os.environ.get("DATABRICKS_CATALOG", "urna")
    sch = os.environ.get("DATABRICKS_SCHEMA", "viabilidade")
    vol = os.environ.get("DATABRICKS_VOLUME", "raw")

    # 1. CDN: HEAD + download no runner
    h = httpx.head(URL, follow_redirects=True, timeout=30)
    print(
        "HEAD",
        h.status_code,
        {k: h.headers.get(k) for k in ("content-length", "etag", "last-modified")},
    )
    dados = httpx.get(URL, follow_redirects=True, timeout=120).content
    assert len(dados) == int(h.headers["content-length"]), "tamanho difere do HEAD"
    print(
        "download ok:",
        len(dados),
        "bytes sha256",
        hashlib.sha256(dados).hexdigest()[:16],
    )
    csv = zipfile.ZipFile(io.BytesIO(dados)).read(MEMBRO)

    # 2. Capacidades do workspace
    w = WorkspaceClient(host=host, token=token)
    sonda("usuario (PAT valido)", lambda: bool(w.current_user.me().user_name))
    sonda("catalogos visiveis", lambda: [c.name for c in w.catalogs.list()])
    sonda(
        "criar catalogo por API (a Free Edition exige a interface)",
        lambda: (
            (
                w.catalogs.create(name="urna_viabilidade"),
                w.catalogs.delete("urna_viabilidade", force=True),
            )[0].name
        ),  # noqa: E501
        obrigatoria=False,
    )
    sonda("service principals", lambda: len(list(w.service_principals.list())))
    sonda(
        "criar schema",
        lambda: idempotente(
            lambda: w.schemas.create(name=sch, catalog_name=cat).full_name
        ),
    )
    sonda(
        "criar volume",
        lambda: idempotente(
            lambda: (
                w.volumes.create(
                    catalog_name=cat,
                    schema_name=sch,
                    name=vol,
                    volume_type=VolumeType.MANAGED,
                ).full_name
            )
        ),
    )

    # 3. Upload via Files API
    base = f"/Volumes/{cat}/{sch}/{vol}"
    sonda(
        "upload zip",
        lambda: (
            w.files.upload(
                f"{base}/{URL.rsplit('/', 1)[1]}", io.BytesIO(dados), overwrite=True
            )
            or base
        ),
    )  # noqa: E501
    sonda(
        "upload csv",
        lambda: (
            w.files.upload(f"{base}/{MEMBRO}", io.BytesIO(csv), overwrite=True)
            or MEMBRO
        ),
    )  # noqa: E501
    sonda(
        "listar volume", lambda: [f.name for f in w.files.list_directory_contents(base)]
    )

    # 4. SQL warehouse a partir do runner
    wid = (
        os.environ.get("DATABRICKS_WAREHOUSE_ID") or next(iter(w.warehouses.list())).id
    )
    path = f"/sql/1.0/warehouses/{wid}"

    def consulta() -> object:
        with (
            sql.connect(
                server_hostname=host.removeprefix("https://"),
                http_path=path,
                access_token=token,
            ) as c,
            c.cursor() as cur,
        ):
            cur.execute(
                f"SELECT count(*) AS n FROM read_files('{base}/{MEMBRO}', format => 'csv', delimiter => ';', header => true)"  # noqa: E501
            )
            n = cur.fetchone()[0]  # type: ignore[index]
            assert n > 0, "nenhuma linha lida"
            return f"{n} linhas em {MEMBRO}"

    sonda("SQL warehouse le o Volume", consulta)
    print("Egress do Databricks ao CDN: nao testavel daqui (ver docs/viabilidade.md).")
    print("RESULTADO:", "FALHAS: " + ", ".join(falhas) if falhas else "tudo OK")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
