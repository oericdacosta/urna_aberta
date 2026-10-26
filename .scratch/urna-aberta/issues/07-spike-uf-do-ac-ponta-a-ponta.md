# 07: Spike: UF do AC ponta a ponta

**What to build:** Um caminho feito à mão, mas completo: baixar a votação por seção do Acre, subir ao Volume, carregar no bronze e consultar uma contagem. É a primeira fatia vertical e mede tempo e custo reais.

**Blocked by:** 03 (Gate de viabilidade do Databricks), 05 (Cabeçalhos reais de 2026 e contratos)

**Status:** ready-for-agent

- [x] Tabela bronze do Acre consultável no Databricks
- [x] Contagem de linhas igual ao CSV de origem
- [ ] Tempo e uso de cota medidos e registrados
- [x] Problemas descobertos (encoding, tamanho, limites) viram ajustes nos tickets seguintes

## Estado (2026-10-26)

Executado com `scripts/spike_ac.py` e registrado em `docs/spike-ac.md`: 241.907 linhas no CSV e na tabela bronze, soma de `QT_VOTOS` idêntica, tempo total de 21 a 29 s. Os problemas encontrados viraram critérios nos tickets de downloader, carga bronze e workflow.

Em aberto: o uso de cota. O tempo foi medido, mas a cota diária do Free Edition não é mensurável por SQL (`system.billing.usage` vem vazio). Fica sem marcar até haver observação na interface do workspace.
