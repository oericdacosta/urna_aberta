"""Manifesto de ingestão: o que já foi baixado do CDN, com hash e metadados."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ManifestEntry:
    url: str
    size: int
    etag: str | None
    last_modified: str | None
    sha256: str
    status: str  # novo | inalterado | republicado
    volume_path: str
    downloaded_at: str  # ISO-8601 UTC
    bronze_sha256: str | None = None  # sha256 do ZIP já carregado no bronze


class Manifest(Protocol):
    def get(self, url: str) -> ManifestEntry | None: ...

    def put(self, entry: ManifestEntry) -> None: ...
