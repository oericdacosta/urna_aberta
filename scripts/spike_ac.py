# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "databricks-sdk>=0.40",
#   "databricks-sql-connector>=3.5",
#   "httpx>=0.27",
# ]
# ///
# ruff: noqa: E501
"""Spike descartável: votação por seção do Acre, do CDN do TSE ao bronze no Databricks.

Uso: uv run --env-file .env scripts/spike_ac.py
Env: DATABRICKS_HOST, DATABRICKS_TOKEN (obrigatórias); DATABRICKS_WAREHOUSE_ID (opcional).
Cria urna.landing (Volume tse) e urna.bronze.tse_votacao_secao. O token nunca é impresso.
"""

import csv
import hashlib
import io
import os
import sys
import time
import zipfile
from collections.abc import Callable

import httpx
from databricks import sql
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import VolumeType

URL = "https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao/votacao_secao_2026_AC.zip"
MEMBRO = "votacao_secao_2026_AC.csv"
CAT, LANDING, BRONZE, VOL = "urna", "landing", "bronze", "tse"
TABELA = f"{CAT}.{BRONZE}.tse_votacao_secao"
BASE = f"/Volumes/{CAT}/{LANDING}/{VOL}"
tempos: dict[str, float] = {}


def etapa[T](nome: str, fn: Callable[[], T]) -> T:
    t0 = time.perf_counter()
    r = fn()
    tempos[nome] = time.perf_counter() - t0
    print(f"[{tempos[nome]:6.1f}s] {nome}")
    return r


def idempotente(fn: Callable[[], object]) -> None:
    try:
        fn()
    except Exception as e:  # noqa: BLE001
        if "already exists" not in str(e):
            raise


def main() -> int:
    host = os.environ["DATABRICKS_HOST"].rstrip("/")
    token = os.environ["DATABRICKS_TOKEN"]
    w = WorkspaceClient(host=host, token=token)

    # 1. Download e contagem de referência no CSV de origem
    dados = etapa("download do ZIP", lambda: httpx.get(URL, timeout=300).content)
    sha = hashlib.sha256(dados).hexdigest()
    csv_bytes = zipfile.ZipFile(io.BytesIO(dados)).read(MEMBRO)
    print(
        f"ZIP {len(dados):,} bytes | CSV {len(csv_bytes):,} bytes | sha256 {sha[:16]}"
    )

    def contar() -> int:
        txt = io.TextIOWrapper(io.BytesIO(csv_bytes), encoding="latin-1", newline="")
        return sum(1 for _ in csv.reader(txt, delimiter=";")) - 1

    esperado = etapa("contagem de referência (csv do Python)", contar)
    print(f"linhas no CSV de origem: {esperado:,}")

    # 2. Pouso no Volume
    idempotente(lambda: w.schemas.create(name=LANDING, catalog_name=CAT))
    idempotente(lambda: w.schemas.create(name=BRONZE, catalog_name=CAT))
    idempotente(
        lambda: w.volumes.create(
            catalog_name=CAT,
            schema_name=LANDING,
            name=VOL,
            volume_type=VolumeType.MANAGED,
        )
    )
    zip_path = f"{BASE}/votacao_secao/2026/votacao_secao_2026_AC.zip"
    csv_path = f"{BASE}/_unzipped/votacao_secao/2026/{MEMBRO}"
    for d in (f"{BASE}/votacao_secao/2026", f"{BASE}/_unzipped/votacao_secao/2026"):
        w.files.create_directory(d)
    etapa(
        "upload do ZIP ao Volume",
        lambda: w.files.upload(zip_path, io.BytesIO(dados), overwrite=True),
    )
    etapa(
        "upload do CSV ao Volume",
        lambda: w.files.upload(csv_path, io.BytesIO(csv_bytes), overwrite=True),
    )

    # 3. Bronze via SQL warehouse
    wid = (
        os.environ.get("DATABRICKS_WAREHOUSE_ID") or next(iter(w.warehouses.list())).id
    )
    with (
        sql.connect(
            server_hostname=host.removeprefix("https://"),
            http_path=f"/sql/1.0/warehouses/{wid}",
            access_token=token,
        ) as c,
        c.cursor() as cur,
    ):

        def um(q: str) -> list[tuple[object, ...]]:
            cur.execute(q)
            return [tuple(r) for r in cur.fetchall()]

        etapa(
            "warehouse: primeira consulta (inclui partida a frio)",
            lambda: um("SELECT 1"),
        )
        etapa(
            "bronze: CREATE TABLE AS SELECT read_files",
            lambda: cur.execute(
                f"""
                CREATE OR REPLACE TABLE {TABELA} AS
                SELECT *,
                       '{URL}' AS _source_url,
                       _metadata.file_name AS _source_file,
                       '{sha}' AS _file_hash,
                       current_timestamp() AS _ingested_at,
                       'ISO-8859-1' AS _encoding
                FROM read_files('{csv_path}', format => 'csv', delimiter => ';',
                                header => true, encoding => 'ISO-8859-1',
                                inferSchema => false)
                """
            ),
        )
        n = int(um(f"SELECT count(*) FROM {TABELA}")[0][0])  # type: ignore[call-overload]
        print(f"linhas na tabela bronze: {n:,} | esperado: {esperado:,}")

        tipos = um(f"DESCRIBE TABLE {TABELA}")
        nao_string = [
            (r[0], r[1]) for r in tipos if r[1] not in ("string", "timestamp")
        ]
        print(f"colunas: {len(tipos)} | fora de string/timestamp: {nao_string}")

        acentos = um(
            f"SELECT DISTINCT NM_MUNICIPIO FROM {TABELA} "
            "WHERE NM_MUNICIPIO RLIKE '[^A-Z0-9 \\\\-\\']' ORDER BY 1"
        )
        print(
            "municípios com caracteres fora de A-Z (checagem de encoding):",
            [r[0] for r in acentos],
        )
        print(
            "amostra de 1 linha (sem dados pessoais nesta tabela):",
            um(
                f"SELECT NM_MUNICIPIO, NR_ZONA, NR_SECAO, DS_CARGO FROM {TABELA} LIMIT 1"
            ),
        )

        # Cota: tentativa de ler as tabelas de sistema (podem não existir na Free Edition)
        for nome, q in (
            (
                "system.billing.usage (hoje)",
                "SELECT sku_name, sum(usage_quantity) FROM system.billing.usage "
                "WHERE usage_date >= current_date() - 1 GROUP BY 1",
            ),
            (
                "system.query.history (ultimas 10)",
                "SELECT statement_type, total_duration_ms, read_bytes "
                "FROM system.query.history ORDER BY start_time DESC LIMIT 10",
            ),
        ):
            try:
                print(f"{nome}: {um(q)}")
            except Exception as e:  # noqa: BLE001
                print(f"{nome}: INDISPONIVEL ({type(e).__name__}: {str(e)[:120]})")

    total = sum(tempos.values())
    print(f"tempo total medido: {total:.1f}s")
    ok = n == esperado
    print("RESULTADO:", "contagem confere" if ok else "CONTAGEM DIVERGE")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
