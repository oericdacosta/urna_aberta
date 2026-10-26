# 03: Gate de viabilidade do Databricks

**What to build:** Prova, com um workflow manual do Actions, o caminho real do dado: baixar um ZIP pequeno do CDN do TSE no runner, subir a um Volume do Databricks e lê-lo lá. O resultado decide a arquitetura de ingestão.

**Passos manuais do usuário:** criar o workspace Databricks Free Edition, gerar o token (PAT) e cadastrá-lo como secret do repositório. O agente não faz isso por você.

**Blocked by:** 01 (Esqueleto do repositório)

**Status:** ready-for-agent

- [ ] Documento de viabilidade registra: PAT permitido?, service principal existe?, dá para criar catálogo?, Volumes disponíveis?, cota diária e limite de armazenamento
- [ ] Registra se o runner do Actions consegue conectar ao SQL warehouse
- [ ] Registra se o Databricks alcança `cdn.tse.jus.br` (egress), mesmo que o desenho não dependa disso
- [ ] Workflow manual baixa um ZIP pequeno, sobe ao Volume e uma consulta SQL lê as linhas
- [ ] Decisões que mudam o desenho (ex.: sem catálogo próprio) ficam registradas no documento de viabilidade
