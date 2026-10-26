"""Contratos de cabeçalho por família de arquivo (config/contracts/*.yaml)."""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, field_validator

CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "config" / "contracts"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Format(_Strict):
    encoding: str
    bom: bool
    delimiter: str
    quotechar: str
    quoting: str
    line_terminator: str


class Column(_Strict):
    name: str
    type: Literal[
        "str",
        "int",
        "decimal_comma",
        "decimal_point",
        "date_dmy",
        "time",
        "datetime_dmy",
    ]
    zero_padded: bool = False
    special: list[str] = []


class Contract(_Strict):
    contract_version: int
    family: str
    ckan_dataset: str
    zip: list[str]
    member_pattern: str
    format: Format
    columns: list[Column]

    @field_validator("columns")
    @classmethod
    def _columns_ok(cls, cols: list[Column]) -> list[Column]:
        names = [c.name for c in cols]
        if not names:
            raise ValueError("contrato sem colunas")
        dups = {n for n in names if names.count(n) > 1}
        if dups:
            raise ValueError(f"colunas duplicadas: {sorted(dups)}")
        return cols

    def diff_header(self, header: list[str]) -> tuple[list[str], list[str]]:
        """Devolve (ausentes, novas) do cabeçalho lido em relação ao contrato."""
        expected = [c.name for c in self.columns]
        return (
            [c for c in expected if c not in header],
            [c for c in header if c not in expected],
        )

    def check_header(self, header: list[str]) -> None:
        """Levanta ValueError se o cabeçalho lido difere do contrato."""
        expected = [c.name for c in self.columns]
        if header != expected:
            missing = [c for c in expected if c not in header]
            extra = [c for c in header if c not in expected]
            raise ValueError(
                f"{self.family}: cabeçalho diverge do contrato "
                f"(ausentes={missing}, novas={extra})"
            )


def load_contract(path: Path) -> Contract:
    return Contract.model_validate(yaml.safe_load(path.read_text("utf-8")))


def load_all(directory: Path = CONTRACTS_DIR) -> dict[str, Contract]:
    return {p.stem: load_contract(p) for p in sorted(directory.glob("*.yaml"))}
