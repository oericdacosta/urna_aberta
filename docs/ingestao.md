# Ingestão

Workflow: `.github/workflows/ingest.yml`. Código: `src/urna_aberta/ingest.py`.

## Como funciona

1. **discover** lista os CSVs (com contrato) dos datasets habilitados em `config/elections/<ano>.yaml` que são novos, mudaram no
   CDN ou ainda não foram carregados no bronze, do menor para o maior. A saída vira a matriz do Actions.
2. **ingest** roda um job por arquivo (3 em paralelo, `fail-fast: false`): baixa, envia ao Volume, carrega no bronze e só então
   marca o ZIP como carregado (`bronze_sha256` no manifesto). Se a carga falha, o próximo run tenta de novo.
3. **alerta** abre uma issue quando algo falha.

Só há uma ingestão por vez (`concurrency: ingest`). Cron diário às 03:17 (Brasília), ou manual em Actions > ingest > Run workflow,
com ano da eleição, dataset (opcional) e "recarregar".

Cada arquivo carregado é conferido contra o CSV de origem: se o bronze não tem o mesmo número de linhas, a carga falha.

## Escopo atual

`resultados-2026`, `comparecimento-e-abstencao-2026` e o de-para TSE↔IBGE: 36 ZIPs, 3,48 GiB comprimidos.
`candidatos-2026` e `eleitorado-2026` estão desligados em `2026.yaml` até terem tratamento de dados pessoais.

## Rodar localmente

```bash
uv run --env-file .env python -m urna_aberta.ingest discover       # o que falta
uv run --env-file .env python -m urna_aberta.ingest file --url <zip>
uv run --env-file .env python -m urna_aberta.ingest all            # tudo, em sequência
```

O disco precisa de ZIP + um CSV: o maior (votação por seção de SP) pede cerca de 5,4 GB livres.

## Agendamento desativado por inatividade

O GitHub desativa workflows agendados em repositórios sem atividade por 60 dias. Não existe forma confiável de um workflow
agendado se reativar sozinho (ele também seria desativado). O que mantém o repositório ativo é o uso normal e o Dependabot
semanal. Se o cron parar, reative com `gh workflow enable ingest.yml` ou pela aba Actions.

## Limites conhecidos

- Cada arquivo faz várias consultas SQL com conexão nova: um ZIP com 28 CSVs levou 212 s, quase tudo em sobrecarga.
- O limite de tamanho de upload da Files API não foi verificado; o maior CSV (SP, ~4,6 GiB) é o teste.
- O `eleitorado-2026` tem CSVs bem maiores (`perfil_eleitor_secao`, ~21,5 GiB descomprimido) que talvez não caibam no runner.
