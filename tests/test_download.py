from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest
import respx
from tenacity import wait_none

from urna_aberta.download import stream_download, sync_file
from urna_aberta.manifest import ManifestEntry

URL = "https://cdn.tse.jus.br/estatistica/sead/odsele/tema/arquivo_2026.zip"
DESTINO = "/Volumes/urna/landing/tse/tema/2026/arquivo_2026.zip"


class ManifestoFalso:
    def __init__(self) -> None:
        self.itens: dict[str, ManifestEntry] = {}

    def get(self, url: str) -> ManifestEntry | None:
        return self.itens.get(url)

    def put(self, entry: ManifestEntry) -> None:
        self.itens[entry.url] = entry


class Envio:
    """Registra os uploads e confere que o arquivo existe no momento do envio."""

    def __init__(self) -> None:
        self.enviados: list[tuple[str, bytes]] = []

    def __call__(self, local: Path, destino: str) -> None:
        self.enviados.append((destino, local.read_bytes()))


class QuedaDeRede(httpx.SyncByteStream):
    """Entrega parte do corpo e derruba a conexão no meio do stream."""

    def __init__(self, parte: bytes) -> None:
        self.parte = parte

    def __iter__(self) -> Iterator[bytes]:
        yield self.parte
        raise httpx.ReadError("conexão caiu")


def cdn(
    mock: respx.MockRouter, corpo: bytes, etag: str
) -> tuple[respx.Route, respx.Route]:
    h = {"content-length": str(len(corpo)), "etag": etag, "last-modified": "ontem"}
    return (
        mock.head(URL).mock(return_value=httpx.Response(200, headers=h)),
        mock.get(URL).mock(return_value=httpx.Response(200, headers=h, content=corpo)),
    )


def sincronizar(manifesto: ManifestoFalso, envio: Envio, pasta: Path) -> str:
    with httpx.Client() as client:
        return sync_file(
            client,
            URL,
            workdir=pasta,
            volume_path=DESTINO,
            manifest=manifesto,
            upload=envio,
            wait=wait_none(),
        )


def test_primeira_vez_baixa_envia_e_registra(tmp_path: Path) -> None:
    m, e = ManifestoFalso(), Envio()
    with respx.mock() as mock:
        cdn(mock, b"conteudo", '"e1"')
        assert sincronizar(m, e, tmp_path) == "novo"
    assert e.enviados == [(DESTINO, b"conteudo")]
    item = m.itens[URL]
    assert (item.size, item.etag, item.last_modified) == (8, '"e1"', "ontem")
    assert len(item.sha256) == 64 and item.downloaded_at
    assert list(tmp_path.iterdir()) == []  # o arquivo local foi apagado


def test_segunda_execucao_sem_mudanca_nao_rebaixa(tmp_path: Path) -> None:
    m, e = ManifestoFalso(), Envio()
    with respx.mock() as mock:
        _, get = cdn(mock, b"conteudo", '"e1"')
        sincronizar(m, e, tmp_path)
        assert sincronizar(m, e, tmp_path) == "inalterado"
        assert get.call_count == 1
    assert len(e.enviados) == 1


def test_hash_diferente_marca_republicado(tmp_path: Path) -> None:
    m, e = ManifestoFalso(), Envio()
    with respx.mock() as mock:
        cdn(mock, b"versao 1", '"e1"')
        sincronizar(m, e, tmp_path)
        antes = m.itens[URL].sha256
    with respx.mock() as mock:
        cdn(mock, b"versao 2 maior", '"e2"')
        assert sincronizar(m, e, tmp_path) == "republicado"
    assert m.itens[URL].sha256 != antes
    assert [d for d, _ in e.enviados] == [DESTINO, DESTINO]


def test_metadado_muda_mas_conteudo_igual_nao_reenvia(tmp_path: Path) -> None:
    m, e = ManifestoFalso(), Envio()
    with respx.mock() as mock:
        cdn(mock, b"conteudo", '"e1"')
        sincronizar(m, e, tmp_path)
    with respx.mock() as mock:
        cdn(mock, b"conteudo", '"e2"')
        assert sincronizar(m, e, tmp_path) == "inalterado"
    assert len(e.enviados) == 1
    assert m.itens[URL].etag == '"e2"'


def test_queda_no_meio_do_stream_nao_deixa_arquivo_nem_manifesto(
    tmp_path: Path,
) -> None:
    m, e = ManifestoFalso(), Envio()
    h = {"content-length": "100", "etag": '"e1"', "last-modified": "ontem"}
    with respx.mock() as mock:
        mock.head(URL).mock(return_value=httpx.Response(200, headers=h))
        mock.get(URL).mock(
            return_value=httpx.Response(200, headers=h, stream=QuedaDeRede(b"x" * 10))
        )
        with pytest.raises(httpx.ReadError):
            sincronizar(m, e, tmp_path)
    assert list(tmp_path.iterdir()) == []  # nem arquivo final nem .part
    assert m.itens == {} and e.enviados == []


def test_proxima_execucao_conclui_apos_queda(tmp_path: Path) -> None:
    m, e = ManifestoFalso(), Envio()
    corpo = b"x" * 100
    h = {"content-length": "100", "etag": '"e1"', "last-modified": "ontem"}
    with respx.mock() as mock:
        mock.head(URL).mock(return_value=httpx.Response(200, headers=h))
        mock.get(URL).mock(
            return_value=httpx.Response(200, headers=h, stream=QuedaDeRede(b"x"))
        )
        with pytest.raises(httpx.ReadError):
            sincronizar(m, e, tmp_path)
    with respx.mock() as mock:
        cdn(mock, corpo, '"e1"')
        assert sincronizar(m, e, tmp_path) == "novo"
    assert e.enviados == [(DESTINO, corpo)]


def test_tentativa_com_queda_e_repetida_e_conclui(tmp_path: Path) -> None:
    m, e = ManifestoFalso(), Envio()
    corpo = b"y" * 50
    h = {"content-length": "50", "etag": '"e1"', "last-modified": "ontem"}
    with respx.mock() as mock:
        mock.head(URL).mock(return_value=httpx.Response(200, headers=h))
        mock.get(URL).mock(
            side_effect=[
                httpx.Response(200, headers=h, stream=QuedaDeRede(b"y" * 5)),
                httpx.Response(200, headers=h, content=corpo),
            ]
        )
        assert sincronizar(m, e, tmp_path) == "novo"
    assert e.enviados == [(DESTINO, corpo)]


def test_arquivo_menor_que_content_length_falha_sem_deixar_rastro(
    tmp_path: Path,
) -> None:
    h = {"content-length": "100"}
    with respx.mock() as mock, httpx.Client() as client:
        mock.get(URL).mock(
            return_value=httpx.Response(200, headers=h, content=b"curto")
        )
        with pytest.raises(httpx.ReadError):
            stream_download(client, URL, tmp_path / "a.zip", wait=wait_none())
    assert list(tmp_path.iterdir()) == []


def test_download_calcula_sha256_em_streaming(tmp_path: Path) -> None:
    import hashlib

    corpo = b"abc" * 1_000_000  # maior que um chunk de 1 MiB
    with respx.mock() as mock, httpx.Client() as client:
        mock.get(URL).mock(
            return_value=httpx.Response(
                200, headers={"content-length": str(len(corpo))}, content=corpo
            )
        )
        sha, n = stream_download(client, URL, tmp_path / "a.zip")
    assert (sha, n) == (hashlib.sha256(corpo).hexdigest(), len(corpo))
    assert (tmp_path / "a.zip").read_bytes() == corpo
