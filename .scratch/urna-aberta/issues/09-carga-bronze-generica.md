# 09: Carga bronze genérica

**What to build:** Carregar qualquer arquivo de um dataset de 2026 para o bronze, fiel à fonte e com metadados de origem. Reexecutar nunca duplica, e arquivo fora do contrato não chega à silver.

**Blocked by:** 08 (Downloader idempotente com manifesto), 05 (Cabeçalhos reais de 2026 e contratos)

**Status:** ready-for-agent

- [x] Todas as colunas entram como texto, com metadados de origem, hash, data de ingestão e encoding
- [x] Reprocessar o mesmo arquivo mantém a contagem de linhas
- [x] Coluna ausente ou renomeada sem mapeamento põe o arquivo em quarentena e falha a carga
- [x] Coluna nova gera aviso e é preservada
- [x] Acentos íntegros num caso de teste (ex.: nomes com cedilha)
- [x] Carregar uma UF substitui só as linhas daquele arquivo (REPLACE WHERE por arquivo de origem), nunca recria a tabela inteira
- [x] Linha com `_rescued_data` não nulo (coluna que o `read_files` devolve) conta como rejeitada
- [x] Decisão registrada sobre nomes de coluna no bronze: o spike manteve os originais em maiúsculas

## Estado (2026-10-26)

Concluído e documentado em `docs/bronze.md`. Verificado: 30 testes offline (incluindo quarentena, coluna nova, `REPLACE WHERE`, acentos, nome de coluna perigoso), quebra deliberada do código em 4 pontos (todas pegas), e carga real no Databricks: Acre (241.907 linhas, soma de votos igual ao CSV) e o ZIP de detalhe da apuração (30.716 linhas em 28 arquivos, `BRASIL` pulado, recarga idêntica).

Limites: só 2 famílias rodaram no Databricks; a quarentena só foi exercitada offline; nenhum arquivo grande passou pela carga (SP, 4,6 GiB).
