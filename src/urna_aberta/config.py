"""Configuração validada de uma eleição."""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DatasetConfig(_Strict):
    id: str
    enabled: bool


class ElectionConfig(_Strict):
    ano: int
    turnos: list[int]
    cargos: list[str]
    ufs: list[str] | None = None
    datasets: list[DatasetConfig]
    catalog: str


def load_election(path: Path) -> ElectionConfig:
    return ElectionConfig.model_validate(yaml.safe_load(path.read_text("utf-8")))
