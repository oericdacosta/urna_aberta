# Spike: votação por seção do Acre, do CDN ao bronze

Executado em 2026-10-26 por `scripts/spike_ac.py` (descartável), no workspace Free Edition, catálogo `urna`.
Fonte: `votacao_secao_2026_AC.zip`, publicado pelo TSE em 06/10/2026 (1º turno).

## O que foi feito

CDN do TSE -> máquina local (download e descompactação em memória) -> Volume `urna.landing.tse`
(ZIP original e CSV extraído) -> `CREATE OR REPLACE TABLE urna.bronze.tse_votacao_secao AS SELECT ... FROM read_files(...)`
pelo SQL warehouse. Todas as colunas entram como texto, com metadados de origem
(`_source_url`, `_source_file`, `_file_hash`, `_ingested_at`, `_encoding`).

## Verificação (fato)

| Item | Resultado |
|---|---|
| Linhas no CSV de origem | 241.907 (contadas com o módulo `csv` do Python) |
| Linhas na tabela bronze | 241.907 |
| Soma de `QT_VOTOS` | 2.439.855 no CSV e na tabela (verificação mais forte que a contagem) |
| `_rescued_data` não nulo | 0 linhas |
| Colunas da tabela | 32 = 26 do CSV + 6 extras (5 de metadados + `_rescued_data`, que o `read_files` acrescenta sozinho) |
| Tipos | tudo `string`, exceto `_ingested_at` (timestamp) |
| Encoding | `encoding => 'ISO-8859-1'` funciona; municípios saem corretos (`BRASILÉIA`, `EPITACIOLÂNDIA`, `FEIJÓ`, `JORDÃO`, `PLÁCIDO DE CASTRO`, `TARAUACÁ`...) |
| Repetível | segunda execução idêntica; o `CREATE OR REPLACE` não duplica |

## Tempo medido (fato, duas execuções)

| Etapa | 1ª | 2ª |
|---|---|---|
| Download do ZIP (7,2 MiB) | 0,4 s | 0,4 s |
| Upload do ZIP ao Volume | 1,8 s | 2,0 s |
| Upload do CSV (69,3 MB) | 16,4 s | 13,1 s |
| Bronze (`read_files` + CTAS, 241.907 linhas) | 9,6 s | 5,1 s |
| Total medido | 29,0 s | 21,3 s |

O upload sai de uma máquina doméstica (cerca de 4-5 MB/s) e deve ser bem mais rápido no runner do GitHub, mas isso não foi medido.
A partida a frio do warehouse não apareceu: a primeira consulta levou 0,3-0,4 s porque ele já estava ativo.

## Cota (não medida)

`system.billing.usage` voltou vazio e `system.query.history` mostra duração e bytes lidos, sem custo.
Não há como medir a cota diária por SQL. A cota só é observável na interface do workspace ou ao bater no limite.
Esta carga não causou aviso de cota, e é pequena (uma UF, 69 MB).

## Extrapolação (estimativa, não medição)

O Acre é a menor ordem de grandeza deste dataset. `votacao_secao_SP` tem 4,6 GiB de CSV, cerca de 68 vezes o Acre.
Se o tempo escalar de forma linear (não foi verificado), a carga de SP levaria algo como 10 a 20 minutos no warehouse 2X-Small
e proporcionalmente mais no upload. O dataset inteiro tem cerca de 18,7 GiB de CSV em `votacao_secao`.
A cota diária do Free Edition, cujo valor não é publicado, é o limite que realmente decide.

## Problemas descobertos e o que muda

1. **Memória e disco.** O spike mantém ZIP e CSV inteiros em memória. Isso serve para o Acre (77 MB) e não para SP (4,6 GiB):
   o download e a descompactação precisam ser em streaming para disco, e o arquivo local deve ser apagado após o upload,
   porque o total de CSV passa de 50 GiB.
2. **Uma tabela, várias UFs.** `votacao_secao` vem em um ZIP por UF. `CREATE OR REPLACE TABLE` por arquivo apagaria as outras UFs.
   A carga precisa substituir só as linhas do arquivo (`INSERT ... REPLACE WHERE _source_file = ...`).
3. **`_rescued_data`.** O `read_files` devolve essa coluna de graça. Valor não nulo indica linha que não casou com o esquema
   e deve contar como linha rejeitada.
4. **Nomes de colunas.** O spike manteve os nomes originais em maiúsculas. Normalizar (minúsculas, sem acento) é decisão da carga.
5. **Tempo do job.** O maior arquivo individual precisa caber no limite de 6 h por job do GitHub Actions e no disco do runner.

## Objetos criados no workspace

`urna.landing` (Volume `tse`, com o ZIP e o CSV do Acre), `urna.bronze` e a tabela `urna.bronze.tse_votacao_secao` (só Acre).
São resíduos do spike: a carga definitiva os recria.
