import pytest

from urna_aberta.contracts import CONTRACTS_DIR, load_all


def test_todos_os_contratos_carregam() -> None:
    contracts = load_all()
    assert len(contracts) >= 23
    for name, c in contracts.items():
        assert c.family == name
        assert c.contract_version >= 1
        names = [col.name for col in c.columns]
        assert names and len(names) == len(set(names))


def test_todo_contrato_tem_arquivo_yaml() -> None:
    assert list(CONTRACTS_DIR.glob("*.yaml"))


def test_check_header_detecta_mudanca() -> None:
    c = load_all()["votacao_secao"]
    header = [col.name for col in c.columns]
    c.check_header(header)
    with pytest.raises(ValueError, match="ausentes"):
        c.check_header(header[:-1])
    with pytest.raises(ValueError, match="novas"):
        c.check_header([*header, "NOVA"])
