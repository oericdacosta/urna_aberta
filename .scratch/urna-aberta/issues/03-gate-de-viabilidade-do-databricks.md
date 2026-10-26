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

## Estado (2026-10-26)

Nenhum critério marcado: todos dependem de um workspace Free Edition, que não está disponível (sem `DATABRICKS_*` no ambiente; o `~/.databrickscfg` só tem perfis OAuth interativos, que não foram usados para não escrever em workspaces do usuário).

Entregue: `scripts/viabilidade.py`, `.github/workflows/viabilidade.yml` e `docs/viabilidade.md`. Verificado localmente: CKAN, HEAD e download do menor ZIP (2.511.067 bytes, confere com `content-length`), ruff e mypy strict no script. Verificado na doc: cota existe mas sem valor numérico, egress restrito a domínios confiáveis, warehouse único 2X-Small. A doc não menciona PAT, service principal, catálogo próprio nem limite de armazenamento.

Falta (usuário): passos manuais da seção 5 de `docs/viabilidade.md`, depois disparar o workflow e registrar os resultados no documento.
