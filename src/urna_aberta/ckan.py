"""Cliente mínimo do CKAN do TSE e HEAD no CDN."""

from dataclasses import dataclass

import httpx
from tenacity import (
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)
from tenacity.wait import wait_base

CKAN_URL = "https://dadosabertos.tse.jus.br/api/3/action/package_show"


class CkanError(Exception):
    """Dataset ausente ou resposta inválida do CKAN."""


@dataclass(frozen=True)
class Resource:
    url: str
    name: str
    format: str
    last_modified: str | None


@dataclass(frozen=True)
class HeadInfo:
    size: int | None
    etag: str | None
    last_modified: str | None


def _transient(exc: BaseException) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    return isinstance(exc, httpx.TransportError)


def _retrying(wait: wait_base | None) -> Retrying:
    return Retrying(
        retry=retry_if_exception(_transient),
        stop=stop_after_attempt(4),
        wait=wait or wait_exponential(multiplier=1, max=20),
        reraise=True,
    )


def package_resources(
    client: httpx.Client, package_id: str, wait: wait_base | None = None
) -> list[Resource]:
    """Lista os recursos de um dataset; 5xx é repetido com backoff."""

    def get() -> httpx.Response:
        resp = client.get(CKAN_URL, params={"id": package_id})
        if resp.status_code >= 500:
            resp.raise_for_status()
        return resp

    resp = _retrying(wait)(get)
    body = (
        resp.json()
        if resp.headers.get("content-type", "").startswith("application/json")
        else {}
    )
    if resp.status_code != 200 or not body.get("success"):
        raise CkanError(f"dataset {package_id!r} ausente (HTTP {resp.status_code})")
    return [
        Resource(
            url=r["url"],
            name=r.get("name") or "",
            format=r.get("format") or "",
            last_modified=r.get("last_modified") or r.get("metadata_modified"),
        )
        for r in body["result"]["resources"]
        if r.get("url")
    ]


def head(client: httpx.Client, url: str, wait: wait_base | None = None) -> HeadInfo:
    """HEAD no CDN: Content-Length, ETag e Last-Modified (o size do CKAN é nulo)."""

    def go() -> httpx.Response:
        resp = client.head(url, follow_redirects=True)
        resp.raise_for_status()
        return resp

    h = _retrying(wait)(go).headers
    length = h.get("content-length")
    return HeadInfo(
        size=int(length) if length else None,
        etag=h.get("etag"),
        last_modified=h.get("last-modified"),
    )
