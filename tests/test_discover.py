from pathlib import Path

import httpx
import pytest
import respx
from tenacity import wait_none

from urna_aberta.ckan import CKAN_URL, CkanError, head, package_resources
from urna_aberta.config import ElectionConfig, load_election

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("path", sorted((ROOT / "config/elections").glob("*.yaml")))
def test_yamls_validos(path: Path) -> None:
    assert load_election(path).datasets


def test_campo_desconhecido_rejeitado() -> None:
    with pytest.raises(ValueError):
        ElectionConfig.model_validate(
            {
                "ano": 1,
                "turnos": [1],
                "cargos": [],
                "datasets": [],
                "catalog": "c",
                "x": 1,
            }
        )


@respx.mock
def test_recursos_e_retry_5xx() -> None:
    body = {
        "success": True,
        "result": {
            "resources": [
                {
                    "url": "https://cdn/a.zip",
                    "name": "a",
                    "format": "CSV",
                    "last_modified": None,
                    "metadata_modified": "2026-01-01",
                },
                {"url": None, "name": "sem url"},
            ]
        },
    }
    route = respx.get(CKAN_URL).mock(
        side_effect=[
            httpx.Response(503),
            httpx.Response(502),
            httpx.Response(200, json=body),
        ]
    )
    with httpx.Client() as c:
        rs = package_resources(c, "x", wait=wait_none())
    assert route.call_count == 3
    assert [r.url for r in rs] == ["https://cdn/a.zip"]
    assert rs[0].last_modified == "2026-01-01"


@respx.mock
def test_5xx_esgota_tentativas() -> None:
    route = respx.get(CKAN_URL).mock(return_value=httpx.Response(500))
    with httpx.Client() as c, pytest.raises(httpx.HTTPStatusError):
        package_resources(c, "x", wait=wait_none())
    assert route.call_count == 4


@respx.mock
def test_dataset_ausente() -> None:
    respx.get(CKAN_URL).mock(
        return_value=httpx.Response(404, json={"success": False, "error": {}})
    )
    with httpx.Client() as c, pytest.raises(CkanError):
        package_resources(c, "nao-existe", wait=wait_none())


@respx.mock
def test_head() -> None:
    respx.head("https://cdn/a.zip").mock(
        return_value=httpx.Response(
            200,
            headers={"content-length": "42", "etag": '"e"', "last-modified": "ontem"},
        )
    )
    with httpx.Client() as c:
        h = head(c, "https://cdn/a.zip")
    assert (h.size, h.etag, h.last_modified) == (42, '"e"', "ontem")
