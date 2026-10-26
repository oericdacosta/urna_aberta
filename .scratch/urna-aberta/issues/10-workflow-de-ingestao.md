# 10: Workflow de ingestão

**What to build:** Um workflow do Actions que, sozinho ou sob demanda, descobre o que mudou, ingere só os arquivos novos ou alterados em paralelo e depois roda o dbt. Cobre os datasets de resultados e comparecimento do 1º turno.

**Blocked by:** 09 (Carga bronze genérica)

**Status:** ready-for-agent

- [ ] Disparável por cron e manualmente, com entradas de eleição, dataset e forçar
- [ ] A etapa de descoberta devolve uma matriz só com arquivos novos ou alterados
- [ ] Ingestão em matriz por arquivo, com paralelismo limitado e falha de um job não derrubando os outros
- [ ] Execuções simultâneas não se sobrepõem
- [ ] Falha do workflow abre uma issue automaticamente
- [ ] Há um mecanismo para o agendamento não ser desativado por inatividade
