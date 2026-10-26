# 09: Carga bronze genérica

**What to build:** Carregar qualquer arquivo de um dataset de 2026 para o bronze, fiel à fonte e com metadados de origem. Reexecutar nunca duplica, e arquivo fora do contrato não chega à silver.

**Blocked by:** 08 (Downloader idempotente com manifesto), 05 (Cabeçalhos reais de 2026 e contratos)

**Status:** ready-for-agent

- [ ] Todas as colunas entram como texto, com metadados de origem, hash, data de ingestão e encoding
- [ ] Reprocessar o mesmo arquivo mantém a contagem de linhas
- [ ] Coluna ausente ou renomeada sem mapeamento põe o arquivo em quarentena e falha a carga
- [ ] Coluna nova gera aviso e é preservada
- [ ] Acentos íntegros num caso de teste (ex.: nomes com cedilha)
