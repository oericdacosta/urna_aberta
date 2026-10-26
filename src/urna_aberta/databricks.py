"""Acesso ao Databricks: upload ao Volume e o manifesto em tabela Delta."""

import os
import shutil
from pathlib import Path

from databricks import sql
from databricks.sdk import WorkspaceClient

from urna_aberta.manifest import ManifestEntry

COLUNAS = (
    "url, size, etag, last_modified, sha256, status, volume_path, downloaded_at, "
    "bronze_sha256"
)


def workspace() -> WorkspaceClient:
    return WorkspaceClient(
        host=os.environ["DATABRICKS_HOST"].rstrip("/"),
        token=os.environ["DATABRICKS_TOKEN"],
    )


def upload_to_volume(w: WorkspaceClient, local: Path, volume_path: str) -> None:
    """Envia o arquivo em streaming (sem carregá-lo inteiro em memória)."""
    w.files.create_directory(volume_path.rsplit("/", 1)[0])
    with local.open("rb") as f:
        w.files.upload(volume_path, f, overwrite=True)


def download_from_volume(w: WorkspaceClient, volume_path: str, local: Path) -> None:
    """Baixa um arquivo do Volume para o disco em streaming."""
    contents = w.files.download(volume_path).contents
    assert contents is not None
    try:
        with local.open("wb") as f:
            shutil.copyfileobj(contents, f, 1 << 20)
    finally:
        contents.close()


class Sql:
    """Executa SQL no warehouse (uma conexão por chamada)."""

    def __init__(self) -> None:
        host = os.environ["DATABRICKS_HOST"].rstrip("/")
        wid = (
            os.environ.get("DATABRICKS_WAREHOUSE_ID")
            or next(iter(workspace().warehouses.list())).id
        )
        self._conn = {
            "server_hostname": host.removeprefix("https://"),
            "http_path": f"/sql/1.0/warehouses/{wid}",
            "access_token": os.environ["DATABRICKS_TOKEN"],
        }

    def __call__(
        self, query: str, params: dict[str, object] | None = None
    ) -> list[tuple[object, ...]]:
        with sql.connect(**self._conn) as c, c.cursor() as cur:
            cur.execute(query, params)
            return [tuple(r) for r in cur.fetchall()] if cur.description else []


class DatabricksManifest:
    """Manifesto na tabela `<catalogo>.ops.ingest_manifest`."""

    def __init__(self, catalogo: str = "urna", executar: Sql | None = None) -> None:
        self._executar = executar or Sql()
        self.tabela = f"{catalogo}.ops.ingest_manifest"
        self._executar(f"CREATE SCHEMA IF NOT EXISTS {catalogo}.ops")
        self._executar(
            f"""CREATE TABLE IF NOT EXISTS {self.tabela} (
                url STRING, size BIGINT, etag STRING, last_modified STRING,
                sha256 STRING, status STRING, volume_path STRING,
                downloaded_at STRING, bronze_sha256 STRING)"""
        )
        colunas = [str(r[0]) for r in self._executar(f"DESCRIBE TABLE {self.tabela}")]
        if "bronze_sha256" not in colunas:  # tabela criada antes desta coluna
            self._executar(
                f"ALTER TABLE {self.tabela} ADD COLUMNS (bronze_sha256 STRING)"
            )

    def get(self, url: str) -> ManifestEntry | None:
        linhas = self._executar(
            f"SELECT {COLUNAS} FROM {self.tabela} WHERE url = :url", {"url": url}
        )
        return ManifestEntry(*linhas[0]) if linhas else None  # type: ignore[arg-type]

    def put(self, entry: ManifestEntry) -> None:
        self._executar(
            f"""MERGE INTO {self.tabela} t
                USING (SELECT :url AS url, :size AS size,
                       CAST(:etag AS STRING) AS etag,
                       CAST(:last_modified AS STRING) AS last_modified,
                       :sha256 AS sha256, :status AS status,
                       :volume_path AS volume_path, :downloaded_at AS downloaded_at,
                       CAST(:bronze_sha256 AS STRING) AS bronze_sha256) s
                ON t.url = s.url
                WHEN MATCHED THEN UPDATE SET *
                WHEN NOT MATCHED THEN INSERT *""",
            dict(entry.__dict__),
        )
