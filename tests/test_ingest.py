from dataclasses import replace
from pathlib import Path

import httpx
import pytest
import respx
from tenacity import wait_none
from test_download import Envio, ManifestoFalso

from urna_aberta.bronze import LoadResult
from urna_aberta.ckan import CKAN_URL
from urna_aberta.config import ElectionConfig
from urna_aberta.contracts import Contract
from urna_aberta.ingest import pendentes, processar
from urna_aberta.manifest import ManifestEntry

CDN = "https://cdn.tse.jus.br/estatistica/sead/odsele"


def contratos() -> dict[str, Contract]:
    c = Contract.model_validate(
        {
            "contract_version": 1,
            "family": "tema",
            "ckan_dataset": "ds",
            "zip": [f"{CDN}/tema/tema_2026_{{UF}}.zip"],
            "member_pattern": "tema_2026_{UF}.csv",
            "format": {
                "encoding": "iso-8859-1",
                "bom": False,
                "delimiter": ";",
                "quotechar": '"',
                "quoting": "q",
                "line_terminator": "CRLF",
            },
            "columns": [{"name": "A", "type": "str"}],
        }
    )
    return {"tema": c}


def config(**habilitado: bool) -> ElectionConfig:
    ids = habilitado or {"ds": True}
    return ElectionConfig.model_validate(
        {
            "ano": 2026,
            "turnos": [1],
            "cargos": [],
            "catalog": "urna",
            "datasets": [{"id": i, "enabled": e} for i, e in ids.items()],
        }
    )


def url(uf: str) -> str:
    return f"{CDN}/tema/tema_2026_{uf}.zip"


def servir(mock: respx.MockRouter, recursos: dict[str, tuple[str, int]]) -> None:
    """recursos: url -> (formato, tamanho). O CKAN lista todos; o CDN responde HEAD."""
    mock.get(CKAN_URL).mock(
        return_value=httpx.Response(
            200,
            headers={"content-type": "application/json"},
            json={
                "success": True,
                "result": {
                    "resources": [
                        {"url": u, "name": u, "format": f}
                        for u, (f, _) in recursos.items()
                    ]
                },
            },
        )
    )
    for u, (_, tam) in recursos.items():
        mock.head(u).mock(
            return_value=httpx.Response(
                200,
                headers={
                    "content-length": str(tam),
                    "etag": f'"{tam}"',
                    "last-modified": "d",
                },
            )
        )


def entrada(
    u: str, tam: int, *, carregado: bool = True, etag: str | None = None
) -> ManifestEntry:
    return ManifestEntry(
        url=u,
        size=tam,
        etag=etag or f'"{tam}"',
        last_modified="d",
        sha256="h" * 64,
        status="novo",
        volume_path=f"/Volumes/urna/landing/tse/tema/2026/{u.rsplit('/', 1)[1]}",
        downloaded_at="2026-10-26T00:00:00+00:00",
        bronze_sha256="h" * 64 if carregado else None,
    )


def descobrir(manifesto: ManifestoFalso, **kw: object) -> list[dict[str, object]]:
    cfg = kw.pop("config", config())
    with httpx.Client() as c:
        return pendentes(c, cfg, manifesto, contratos(), wait=wait_none(), **kw)  # type: ignore[arg-type]


def test_so_entram_csv_com_contrato_novos_ou_alterados() -> None:
    m = ManifestoFalso()
    m.put(entrada(url("SP"), 500))  # carregado e igual ao CDN: fica de fora
    with respx.mock(assert_all_called=False) as mock:
        servir(
            mock,
            {
                url("AC"): ("CSV", 100),  # novo
                url("SP"): ("CSV", 500),
                f"{CDN}/tema/relatorio.pdf": ("PDF", 9),  # não é CSV
                f"{CDN}/outro/sem_contrato.zip": ("CSV", 9),  # sem contrato
            },
        )
        achados = descobrir(m)
    assert [a["arquivo"] for a in achados] == ["tema_2026_AC.zip"]


def test_ordem_do_menor_para_o_maior() -> None:
    with respx.mock(assert_all_called=False) as mock:
        servir(
            mock,
            {url("SP"): ("CSV", 900), url("AC"): ("CSV", 10), url("MG"): ("CSV", 300)},
        )
        achados = descobrir(ManifestoFalso())
    assert [a["arquivo"] for a in achados] == [
        "tema_2026_AC.zip",
        "tema_2026_MG.zip",
        "tema_2026_SP.zip",
    ]


def test_mudou_no_cdn_ou_nao_chegou_ao_bronze_volta_para_a_fila() -> None:
    m = ManifestoFalso()
    m.put(entrada(url("AC"), 100, etag='"antigo"'))  # ETag mudou
    m.put(entrada(url("MG"), 300, carregado=False))  # baixado, falhou no bronze
    m.put(entrada(url("SP"), 900))  # ok
    with respx.mock(assert_all_called=False) as mock:
        servir(
            mock,
            {url("AC"): ("CSV", 100), url("MG"): ("CSV", 300), url("SP"): ("CSV", 900)},
        )
        achados = descobrir(m)
    assert {a["arquivo"] for a in achados} == {"tema_2026_AC.zip", "tema_2026_MG.zip"}


def test_force_inclui_tudo_e_dataset_desligado_ou_filtrado_fica_de_fora() -> None:
    m = ManifestoFalso()
    m.put(entrada(url("SP"), 900))
    with respx.mock(assert_all_called=False) as mock:
        servir(mock, {url("SP"): ("CSV", 900)})
        assert len(descobrir(m, force=True)) == 1
        assert descobrir(m, config=config(ds=False), force=True) == []
        assert descobrir(m, dataset="outro", force=True) == []


class Carga:
    def __init__(self, falhar: bool = False) -> None:
        self.chamadas = 0
        self.falhar = falhar

    def __call__(self, e: ManifestEntry) -> list[LoadResult]:
        self.chamadas += 1
        if self.falhar:
            raise RuntimeError("warehouse caiu")
        return [LoadResult("tema_2026_AC.csv", 1, 0, ())]


def rodar(m: ManifestoFalso, carga: Carga, tmp: Path, **kw: bool) -> str:
    h = {"content-length": "5", "etag": '"e1"', "last-modified": "d"}
    with respx.mock(assert_all_called=False) as mock, httpx.Client() as c:
        mock.head(url("AC")).mock(return_value=httpx.Response(200, headers=h))
        mock.get(url("AC")).mock(
            return_value=httpx.Response(200, headers=h, content=b"12345")
        )
        status, _ = processar(
            c,
            url("AC"),
            workdir=tmp,
            volume_path="/Volumes/urna/landing/tse/tema/2026/tema_2026_AC.zip",
            manifest=m,
            upload=Envio(),
            carregar=carga,
            **kw,
        )
    return status


def test_marca_como_carregado_so_depois_da_carga(tmp_path: Path) -> None:
    m, carga = ManifestoFalso(), Carga()
    assert rodar(m, carga, tmp_path) == "novo"
    e = m.itens[url("AC")]
    assert e.bronze_sha256 == e.sha256 and carga.chamadas == 1


def test_segunda_execucao_nao_recarrega(tmp_path: Path) -> None:
    m, carga = ManifestoFalso(), Carga()
    rodar(m, carga, tmp_path)
    rodar(m, carga, tmp_path)
    assert carga.chamadas == 1


def test_carga_que_falha_nao_marca_e_a_proxima_execucao_tenta_de_novo(
    tmp_path: Path,
) -> None:
    m = ManifestoFalso()
    with pytest.raises(RuntimeError):
        rodar(m, Carga(falhar=True), tmp_path)
    assert m.itens[url("AC")].bronze_sha256 is None  # baixou, mas não carregou
    carga = Carga()
    rodar(m, carga, tmp_path)
    assert carga.chamadas == 1 and m.itens[url("AC")].bronze_sha256 is not None


def test_republicado_volta_a_ser_carregado(tmp_path: Path) -> None:
    m, carga = ManifestoFalso(), Carga()
    rodar(m, carga, tmp_path)
    m.itens[url("AC")] = replace(m.itens[url("AC")], sha256="0" * 64, etag='"velho"')
    assert rodar(m, carga, tmp_path) == "republicado"
    assert carga.chamadas == 2
