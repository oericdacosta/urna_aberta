# 03: Gate de viabilidade do Databricks

**What to build:** Prova, com um workflow manual do Actions, o caminho real do dado: baixar um ZIP pequeno do CDN do TSE no runner, subir a um Volume do Databricks e lê-lo lá. O resultado decide a arquitetura de ingestão.

**Passos manuais do usuário:** criar o workspace Databricks Free Edition, gerar o token (PAT) e cadastrá-lo como secret do repositório. O agente não faz isso por você.

**Blocked by:** 01 (Esqueleto do repositório)

**Status:** ready-for-agent

- [x] Documento de viabilidade registra: PAT permitido?, service principal existe?, dá para criar catálogo?, Volumes disponíveis?, cota diária e limite de armazenamento
- [x] Registra se o runner do Actions consegue conectar ao SQL warehouse
- [x] Registra se o Databricks alcança `cdn.tse.jus.br` (egress), mesmo que o desenho não dependa disso
- [x] Workflow manual baixa um ZIP pequeno, sobe ao Volume e uma consulta SQL lê as linhas
- [x] Decisões que mudam o desenho (ex.: sem catálogo próprio) ficam registradas no documento de viabilidade

## Estado (2026-10-26)

Concluído, exceto os valores numéricos de cota diária e armazenamento, que a doc não publica e ainda não foram observados (registrado em `docs/viabilidade.md`, item 4.5). Executado com token pessoal contra o Free Edition (catálogo `urna`, criado pela interface), localmente e no runner do GitHub Actions: download, upload ao Volume, listagem e leitura de 92 linhas por SQL.
