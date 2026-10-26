# Camada bronze

Código: `src/urna_aberta/bronze.py`. Uso: `python -m urna_aberta.bronze --url <zip do TSE>` (o ZIP precisa estar
no manifesto, ou seja, ter passado por `python -m urna_aberta.download`).

## O que a carga faz

Para cada CSV do ZIP que está no Volume `urna.landing.tse`:

1. Extrai o CSV em streaming para o disco e lê o cabeçalho.
2. Compara com o contrato da família (`config/contracts/`):
   - coluna **ausente** (ou renomeada, que aparece como ausente + nova): o CSV vai para
     `_quarantine/<tema>/<ano>/` no Volume e a carga **falha**;
   - coluna **nova**: gera aviso e é preservada (a tabela ganha a coluna com `ALTER TABLE`);
   - nome de coluna fora de `[A-Za-z0-9_]`: recusado, porque o cabeçalho vira SQL.
3. Sobe o CSV para `_unzipped/<tema>/<ano>/` e carrega em `urna.bronze.tse_<familia>` com `read_files`.
4. Substitui só as linhas daquele arquivo (`INSERT INTO ... REPLACE WHERE _source_file = :arquivo`). A tabela nunca é recriada.

O membro `*_BRASIL.csv` é pulado: ele repete a soma dos CSVs por UF.

## Esquema

Todas as colunas do CSV como `STRING`, mais: `_rescued_data`, `_source_url`, `_source_file` (nome do CSV),
`_file_hash` (sha256 do ZIP, vindo do manifesto), `_ingested_at` (timestamp) e `_encoding`.

## Decisões

- **Nomes de coluna em minúsculas** (`dt_geracao`, `sq_candidato`). O Delta não diferencia maiúsculas, então é só convenção, e
  casa com o resto do dbt. O spike mantinha as maiúsculas do TSE. Não há remoção de acento porque os nomes já são ASCII.
- **Linhas rejeitadas ficam na tabela.** Linha com `_rescued_data` não nulo (o que o `read_files` não conseguiu encaixar)
  é contada como rejeitada e continua no bronze, nunca é descartada. A silver deve filtrar `_rescued_data IS NULL`.
- **Colunas de outro layout** (uma tabela com a união das colunas): o arquivo que não as tem as preenche com `NULL`.

## Verificação (2026-10-26, Databricks Free Edition)

| Caso | Resultado |
|---|---|
| Votação por seção do Acre | 241.907 linhas; soma de `qt_votos` igual ao CSV (2.439.855); 0 rejeitadas |
| Acentos (latin-1) | `BRASILÉIA`, `FEIJÓ`, `JORDÃO`, `PLÁCIDO DE CASTRO`... corretos |
| Reprocessar o Acre | mesma contagem (241.907), 1 `_source_file` |
| Detalhe da apuração (ZIP com 28 CSVs) | 30.716 linhas, igual ao contado nos CSVs de origem; `BRASIL` pulado |
| Recarregar o ZIP inteiro | contagem idêntica nos 28 arquivos |

## Limites

- Só duas famílias rodaram no Databricks (`votacao_secao`, `detalhe_votacao_munzona`). As outras usam o mesmo código, mas pelos testes offline.
- A quarentena só foi exercitada nos testes offline, não no Databricks.
- Nenhum arquivo grande passou por aqui (o maior membro, `votacao_secao_SP`, tem 4,6 GiB). A carga baixa o ZIP do Volume de volta
  (um passo a mais) e extrai um CSV por vez, então o disco precisa de ZIP + um CSV.
- A regra de pular `_BRASIL` foi conferida por tamanho; em `consulta_vagas` a razão BRASIL/soma é 0,86, não 1, e não foi investigada.
