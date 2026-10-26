# urna-aberta

ELT de dados abertos eleitorais do TSE para o Databricks, com GitHub Actions e dbt.
**Escopo atual: somente as eleições de 2026** (1º e 2º turno).

O objetivo é uma fundação de dados limpa e conectada, para análise, ciência de dados
e engenharia de IA.

## Começando

Requisitos: Python 3.12+, [uv](https://docs.astral.sh/uv/) e make.

```bash
make setup   # instala dependências e o pre-commit
make test    # roda os testes
make lint    # ruff + mypy
```

Também há um devcontainer em `.devcontainer/`.

## Documentos

- [PRIVACY.md](PRIVACY.md) e [DATA_LICENSE.md](DATA_LICENSE.md): rascunhos.

Fonte dos dados: Tribunal Superior Eleitoral (TSE), Portal de Dados Abertos. Projeto não oficial.
