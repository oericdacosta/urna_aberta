# 10: Workflow de ingestão

**What to build:** Um workflow do Actions que, sozinho ou sob demanda, descobre o que mudou, ingere só os arquivos novos ou alterados em paralelo e depois roda o dbt. Cobre os datasets de resultados e comparecimento do 1º turno.

**Blocked by:** 09 (Carga bronze genérica)

**Status:** ready-for-agent

- [ ] Disparável por cron e manualmente, com entradas de eleição, dataset e forçar
- [x] A etapa de descoberta devolve uma matriz só com arquivos novos ou alterados
- [ ] Ingestão em matriz por arquivo, com paralelismo limitado e falha de um job não derrubando os outros
- [ ] Execuções simultâneas não se sobrepõem
- [ ] Falha do workflow abre uma issue automaticamente
- [ ] Reativar o agendamento desativado por inatividade está documentado (o GitHub não oferece reativação automática confiável)
- [ ] O job do maior arquivo (votação por seção de SP, 4,6 GiB de CSV) cabe no limite de 6 h do job e no disco do runner
- [ ] Todos os arquivos pendentes (36) carregados no bronze, cada um conferido contra a contagem do CSV de origem

## Estado (2026-10-26)

Pronto e testado localmente: `urna_aberta.ingest` (discover, file, all), o workflow `.github/workflows/ingest.yml` (validado com `actionlint`), 39 testes offline com quebra deliberada do código, e carga real no Databricks de 5 arquivos pequenos (Acre, Amapá e Roraima convivendo na mesma tabela, detalhe da apuração com 28 CSVs, comparecimento TTE). A descoberta contra o workspace lista 36 arquivos (3,48 GiB).

Falta rodar no GitHub Actions: o disco local só tem 801 MB livres e o ZIP de SP exige cerca de 5,4 GB. Os critérios acima ficam desmarcados até haver uma execução real. O passo do dbt entra junto com o projeto dbt.
