"""Carga bronze: do ZIP no Volume para tabelas Delta fiéis à fonte (tudo STRING).

Cada CSV do ZIP vira linhas em `<catalogo>.bronze.tse_<familia>`, identificadas por
`_source_file`. Recarregar um arquivo substitui só as linhas dele (REPLACE WHERE),
nunca recria a tabela. Arquivo que não cumpre o contrato vai para quarentena.
"""

import argparse
import csv
import logging
import os
import re
import shutil
import tempfile
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from urna_aberta.contracts import Contract, load_all
from urna_aberta.manifest import ManifestEntry

log = logging.getLogger(__name__)

CHUNK = 1 << 20
IGNORADOS = ("_BRASIL.csv",)  # duplica a soma dos CSVs por UF
IDENT = re.compile(r"^[A-Za-z0-9_]+$")
MEMBRO = re.compile(r"^[A-Za-z0-9_.-]+\.csv$")
METADADOS = (
    ("_rescued_data", "STRING"),
    ("_source_url", "STRING"),
    ("_source_file", "STRING"),
    ("_file_hash", "STRING"),
    ("_ingested_at", "TIMESTAMP"),
    ("_encoding", "STRING"),
)

Sql = Callable[[str, dict[str, object] | None], list[tuple[object, ...]]]
Fetch = Callable[[str, Path], None]  # Volume -> disco local
Put = Callable[[Path, str], None]  # disco local -> Volume


class ContractError(Exception):
    """Arquivo fora do contrato: ele vai para quarentena e a carga falha."""


@dataclass(frozen=True)
class LoadResult:
    arquivo: str
    linhas: int
    rejeitadas: int  # linhas com _rescued_data não nulo (ficam na tabela)
    novas_colunas: tuple[str, ...]


def normalizar(nome: str) -> str:
    """Nome de coluna no bronze: minúsculas, mantendo o resto do nome do TSE."""
    return nome.lower()


def read_header(path: Path, contract: Contract) -> list[str]:
    f = contract.format
    with path.open(encoding=f.encoding, newline="") as fh:
        return next(csv.reader(fh, delimiter=f.delimiter, quotechar=f.quotechar))


def _raiz(volume_zip: str) -> tuple[str, str, str]:
    # /Volumes/<catalogo>/<schema>/<volume>/<tema>/<ano>/<arquivo>.zip
    partes = volume_zip.split("/")
    return "/".join(partes[:5]), partes[5], partes[6]


def _carregar_csv(
    local: Path,
    membro: str,
    *,
    contract: Contract,
    entry: ManifestEntry,
    catalogo: str,
    put: Put,
    sql: Sql,
) -> LoadResult:
    raiz, tema, ano = _raiz(entry.volume_path)
    header = read_header(local, contract)
    # O cabeçalho vem de um arquivo não confiável e vira nome de coluna em SQL.
    if not all(IDENT.match(c) for c in header):
        put(local, f"{raiz}/_quarantine/{tema}/{ano}/{membro}")
        raise ContractError(f"{membro}: nome de coluna inválido no cabeçalho")
    ausentes, novas = contract.diff_header(header)
    if ausentes:
        put(local, f"{raiz}/_quarantine/{tema}/{ano}/{membro}")
        raise ContractError(
            f"{membro}: faltam colunas do contrato {ausentes} "
            f"(novas: {novas}); arquivo em quarentena"
        )
    if novas:
        log.warning(
            "%s: colunas novas fora do contrato %s (preservadas)", membro, novas
        )

    csv_vol = f"{raiz}/_unzipped/{tema}/{ano}/{membro}"
    put(local, csv_vol)

    tabela = f"{catalogo}.bronze.tse_{contract.family}"
    original = {normalizar(c): c for c in header}  # nome no bronze -> nome no CSV
    colunas = ", ".join(f"`{c}` STRING" for c in original)
    meta = ", ".join(f"`{c}` {t}" for c, t in METADADOS)
    sql(f"CREATE TABLE IF NOT EXISTS {tabela} ({colunas}, {meta})", None)

    existentes = [str(r[0]) for r in sql(f"DESCRIBE TABLE {tabela}", None) if r[0]]
    faltam = [c for c in original if c not in {e.lower() for e in existentes}]
    if faltam:
        sql(
            f"ALTER TABLE {tabela} ADD COLUMNS ("
            + ", ".join(f"`{c}` STRING" for c in faltam)
            + ")",
            None,
        )
        existentes += faltam

    valor = {
        "_rescued_data": "_rescued_data",
        "_source_url": ":url",
        "_source_file": ":arquivo",
        "_file_hash": ":sha",
        "_ingested_at": "current_timestamp()",
        "_encoding": ":enc",
    }
    selecao = ", ".join(
        f"{valor[c.lower()]} AS `{c}`"
        if c.lower() in valor
        else f"`{original[c.lower()]}` AS `{c}`"
        if c.lower() in original
        else f"CAST(NULL AS STRING) AS `{c}`"  # coluna de outro layout
        for c in existentes
    )
    f = contract.format
    params: dict[str, object] = {
        "url": entry.url,
        "arquivo": membro,
        "sha": entry.sha256,
        "enc": f.encoding.upper(),
    }
    sql(
        f"INSERT INTO {tabela} REPLACE WHERE _source_file = :arquivo "
        f"SELECT {selecao} FROM read_files('{csv_vol}', format => 'csv', "
        f"delimiter => '{f.delimiter}', quote => '{f.quotechar}', header => true, "
        f"encoding => '{f.encoding.upper()}', inferSchema => false)",
        params,
    )
    n, rej = sql(
        f"SELECT count(*), count(_rescued_data) FROM {tabela} "
        "WHERE _source_file = :arquivo",
        {"arquivo": membro},
    )[0]
    return LoadResult(membro, int(n), int(rej), tuple(novas))  # type: ignore[call-overload]


def load_zip(
    *,
    contract: Contract,
    entry: ManifestEntry,
    fetch: Fetch,
    put: Put,
    sql: Sql,
    catalogo: str = "urna",
) -> list[LoadResult]:
    """Carrega no bronze todos os CSVs de um ZIP que está no Volume (menos o BRASIL)."""
    sql(f"CREATE SCHEMA IF NOT EXISTS {catalogo}.bronze", None)
    resultados: list[LoadResult] = []
    with tempfile.TemporaryDirectory() as tmp:
        zpath, local = Path(tmp) / "entrada.zip", Path(tmp) / "membro.csv"
        # ponytail: baixa o ZIP do Volume de volta; fundir ao downloader se pesar.
        fetch(entry.volume_path, zpath)
        with zipfile.ZipFile(zpath) as zf:
            for info in zf.infolist():
                nome = info.filename
                if not nome.endswith(".csv") or nome.endswith(IGNORADOS):
                    continue
                if not MEMBRO.match(nome):
                    raise ContractError(f"nome de membro inesperado no ZIP: {nome!r}")
                with zf.open(info) as src, local.open("wb") as dst:
                    shutil.copyfileobj(src, dst, CHUNK)
                try:
                    resultados.append(
                        _carregar_csv(
                            local,
                            nome,
                            contract=contract,
                            entry=entry,
                            catalogo=catalogo,
                            put=put,
                            sql=sql,
                        )
                    )
                finally:
                    local.unlink(missing_ok=True)
    return resultados


def contract_para(url: str, contratos: dict[str, Contract]) -> Contract:
    for c in contratos.values():
        for padrao in c.zip:
            regex = re.escape(padrao).replace(r"\{UF\}", "[A-Z]{2}")
            if re.fullmatch(regex, url):
                return c
    raise ContractError(f"nenhum contrato cobre {url}")


def main(argv: list[str] | None = None) -> int:
    from urna_aberta.databricks import (
        DatabricksManifest,
        Sql,
        download_from_volume,
        upload_to_volume,
        workspace,
    )

    p = argparse.ArgumentParser(description="Carrega um ZIP do Volume no bronze.")
    p.add_argument("--url", required=True)
    args = p.parse_args(argv)

    catalogo = os.environ.get("DATABRICKS_CATALOG", "urna")
    executar = Sql()
    entry = DatabricksManifest(catalogo, executar).get(args.url)
    if entry is None:
        print(f"{args.url} não está no manifesto: rode urna_aberta.download antes.")
        return 1
    w = workspace()
    resultados = load_zip(
        contract=contract_para(args.url, load_all()),
        entry=entry,
        fetch=lambda vol, local: download_from_volume(w, vol, local),
        put=lambda local, vol: upload_to_volume(w, local, vol),
        sql=executar,
        catalogo=catalogo,
    )
    for r in resultados:
        extra = f" | colunas novas: {list(r.novas_colunas)}" if r.novas_colunas else ""
        print(f"{r.arquivo}: {r.linhas} linhas, {r.rejeitadas} rejeitadas{extra}")
    print(
        f"total: {sum(r.linhas for r in resultados)} linhas "
        f"em {len(resultados)} arquivos"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
