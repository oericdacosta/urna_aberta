import logging
import shutil
import zipfile
from pathlib import Path

import pytest

from urna_aberta.bronze import ContractError, contract_para, load_zip
from urna_aberta.contracts import Contract, load_all
from urna_aberta.manifest import ManifestEntry

ZIP_VOL = "/Volumes/urna/landing/tse/tema/2026/tema_2026.zip"
RAIZ = "/Volumes/urna/landing/tse"
COLS = ["DT_GERACAO", "NM_MUNICIPIO", "QT_VOTOS"]
META = {
    "_rescued_data",
    "_source_url",
    "_source_file",
    "_file_hash",
    "_ingested_at",
    "_encoding",
}


def contrato(colunas: list[str] = COLS) -> Contract:
    return Contract.model_validate(
        {
            "contract_version": 1,
            "family": "tema",
            "ckan_dataset": "x",
            "zip": ["https://cdn/tema_2026.zip"],
            "member_pattern": "tema_2026_{UF}.csv",
            "format": {
                "encoding": "iso-8859-1",
                "bom": False,
                "delimiter": ";",
                "quotechar": '"',
                "quoting": "q",
                "line_terminator": "CRLF",
            },
            "columns": [{"name": c, "type": "str"} for c in colunas],
        }
    )


ENTRY = ManifestEntry(
    url="https://cdn/tema_2026.zip",
    size=1,
    etag=None,
    last_modified=None,
    sha256="a" * 64,
    status="novo",
    volume_path=ZIP_VOL,
    downloaded_at="2026-10-26T00:00:00+00:00",
)


def csv_bytes(header: list[str], linhas: list[list[str]]) -> bytes:
    h = ";".join(f'"{c}"' for c in header)
    corpo = "\r\n".join(";".join(f'"{v}"' for v in ln) for ln in linhas)
    return (h + "\r\n" + corpo + "\r\n").encode("latin-1")


def fazer_zip(tmp: Path, membros: dict[str, bytes]) -> Path:
    caminho = tmp / "origem.zip"
    with zipfile.ZipFile(caminho, "w") as z:
        for nome, dados in membros.items():
            z.writestr(nome, dados)
    return caminho


class Ambiente:
    """Volume e warehouse falsos: registra uploads e consultas."""

    def __init__(self, zip_local: Path, tabela: list[str] | None = None) -> None:
        self.zip_local = zip_local
        self.enviados: dict[str, bytes] = {}
        self.consultas: list[tuple[str, dict[str, object] | None]] = []
        self.tabela = tabela  # colunas já existentes (None = será criada igual ao CSV)

    def fetch(self, vol: str, local: Path) -> None:
        assert vol == ZIP_VOL
        shutil.copy(self.zip_local, local)

    def put(self, local: Path, vol: str) -> None:
        self.enviados[vol] = local.read_bytes()

    def sql(
        self, q: str, p: dict[str, object] | None = None
    ) -> list[tuple[object, ...]]:
        self.consultas.append((q, p))
        if q.startswith("DESCRIBE TABLE"):
            cols = self.tabela if self.tabela is not None else [c.lower() for c in COLS]
            return [(c, "string", None) for c in [*cols, *sorted(META)]]
        if q.startswith("SELECT count"):
            return [(3, 1)]
        return []

    def carregar(self, contract: Contract | None = None) -> list:  # type: ignore[type-arg]
        return load_zip(
            contract=contract or contrato(),
            entry=ENTRY,
            fetch=self.fetch,
            put=self.put,
            sql=self.sql,
        )

    def inserts(self) -> list[str]:
        return [q for q, _ in self.consultas if q.startswith("INSERT")]


def membros_ok() -> dict[str, bytes]:
    c = csv_bytes(COLS, [["26/10/2026", "BRASILÉIA", "10"]])
    return {"tema_2026_AC.csv": c, "tema_2026_SP.csv": c, "tema_2026_BRASIL.csv": c}


def test_carrega_cada_csv_e_pula_o_brasil(tmp_path: Path) -> None:
    amb = Ambiente(fazer_zip(tmp_path, membros_ok()))
    res = amb.carregar()
    assert [r.arquivo for r in res] == ["tema_2026_AC.csv", "tema_2026_SP.csv"]
    assert len(amb.inserts()) == 2
    assert not any("BRASIL" in v for v in amb.enviados)


def test_substitui_so_as_linhas_do_arquivo_e_nunca_recria_a_tabela(
    tmp_path: Path,
) -> None:
    amb = Ambiente(fazer_zip(tmp_path, membros_ok()))
    amb.carregar()
    amb.carregar()  # reprocessar
    for q in amb.inserts():
        assert "REPLACE WHERE _source_file = :arquivo" in q
    todas = " ".join(q for q, _ in amb.consultas).upper()
    assert "CREATE OR REPLACE" not in todas and "DROP TABLE" not in todas
    arquivos = [p["arquivo"] for q, p in amb.consultas if q.startswith("INSERT") and p]
    assert arquivos == ["tema_2026_AC.csv", "tema_2026_SP.csv"] * 2


def test_tudo_texto_com_metadados_e_nomes_minusculos(tmp_path: Path) -> None:
    amb = Ambiente(fazer_zip(tmp_path, membros_ok()))
    amb.carregar()
    ddl = next(q for q, _ in amb.consultas if q.startswith("CREATE TABLE"))
    for c in COLS:
        assert f"`{c.lower()}` STRING" in ddl
    assert "`_ingested_at` TIMESTAMP" in ddl
    ins = amb.inserts()[0]
    for m in ("_source_url", "_source_file", "_file_hash", "_ingested_at", "_encoding"):
        assert f"AS `{m}`" in ins
    p = next(p for q, p in amb.consultas if q.startswith("INSERT"))
    assert p == {
        "url": ENTRY.url,
        "arquivo": "tema_2026_AC.csv",
        "sha": "a" * 64,
        "enc": "ISO-8859-1",
    }


def test_acentos_chegam_intactos_e_o_encoding_e_declarado(tmp_path: Path) -> None:
    corpo = csv_bytes(COLS, [["26/10/2026", "EPITACIOLÂNDIA AÇAÍ", "1"]])
    amb = Ambiente(fazer_zip(tmp_path, {"tema_2026_AC.csv": corpo}))
    amb.carregar()
    assert amb.enviados[f"{RAIZ}/_unzipped/tema/2026/tema_2026_AC.csv"] == corpo
    assert "encoding => 'ISO-8859-1'" in amb.inserts()[0]


@pytest.mark.parametrize(
    "header",
    [
        ["DT_GERACAO", "QT_VOTOS"],  # coluna ausente
        ["DT_GERACAO", "NM_CIDADE", "QT_VOTOS"],  # renomeada (ausente + nova)
    ],
)
def test_coluna_ausente_ou_renomeada_vai_para_quarentena_e_falha(
    tmp_path: Path, header: list[str]
) -> None:
    ruim = csv_bytes(header, [["x"] * len(header)])
    amb = Ambiente(fazer_zip(tmp_path, {"tema_2026_AC.csv": ruim}))
    with pytest.raises(ContractError, match="quarentena"):
        amb.carregar()
    assert f"{RAIZ}/_quarantine/tema/2026/tema_2026_AC.csv" in amb.enviados
    assert not any("_unzipped" in v for v in amb.enviados)
    assert amb.inserts() == []


def test_coluna_nova_gera_aviso_e_e_preservada(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    novo = csv_bytes([*COLS, "DS_NOVA"], [["a", "b", "1", "z"]])
    amb = Ambiente(fazer_zip(tmp_path, {"tema_2026_AC.csv": novo}))
    with caplog.at_level(logging.WARNING):
        res = amb.carregar()
    assert res[0].novas_colunas == ("DS_NOVA",)
    assert "DS_NOVA" in caplog.text
    alter = [q for q, _ in amb.consultas if q.startswith("ALTER TABLE")]
    assert alter and "`ds_nova` STRING" in alter[0]
    assert "`DS_NOVA` AS `ds_nova`" in amb.inserts()[0]


def test_coluna_de_outro_layout_entra_nula(tmp_path: Path) -> None:
    amb = Ambiente(
        fazer_zip(tmp_path, membros_ok()),
        tabela=[*[c.lower() for c in COLS], "ds_antiga"],
    )
    amb.carregar()
    assert "CAST(NULL AS STRING) AS `ds_antiga`" in amb.inserts()[0]


def test_linhas_rejeitadas_sao_contadas(tmp_path: Path) -> None:
    res = Ambiente(fazer_zip(tmp_path, membros_ok())).carregar()
    assert (res[0].linhas, res[0].rejeitadas) == (3, 1)


def test_cabecalho_com_nome_perigoso_e_recusado(tmp_path: Path) -> None:
    ruim = csv_bytes(
        ["DT_GERACAO", "x` STRING); DROP TABLE t; --", "QT_VOTOS"], [["a", "b", "c"]]
    )
    amb = Ambiente(fazer_zip(tmp_path, {"tema_2026_AC.csv": ruim}))
    with pytest.raises(ContractError, match="inválido"):
        amb.carregar()
    assert amb.consultas == [("CREATE SCHEMA IF NOT EXISTS urna.bronze", None)]


def test_contrato_certo_para_cada_url() -> None:
    contratos = load_all()
    c = contract_para(
        "https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao/votacao_secao_2026_AC.zip",
        contratos,
    )
    assert c.family == "votacao_secao"
    with pytest.raises(ContractError):
        contract_para("https://exemplo.com/outro.zip", contratos)
