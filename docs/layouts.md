# Layouts reais dos arquivos de 2026

Levantamento feito em 2026-10-26 sobre os arquivos publicados no CDN do TSE. Os contratos de
cabeçalho (um por família de arquivo) ficam em `config/contracts/<familia>.yaml` e são
carregados por `urna_aberta.contracts`; a ingestão deve chamar `Contract.check_header` e
falhar quando o cabeçalho lido divergir. Mudou coluna: sobe `contract_version` e o YAML.

## Como foi medido e o que NÃO foi coberto

- Os ZIPs foram lidos por requisições `Range` (diretório central + início de cada membro),
  sem baixar os arquivos inteiros. Do primeiro CSV de cada ZIP leram-se os primeiros 24 MiB
  descomprimidos; dos demais CSVs, o primeiro 1 MiB (cortado na última linha completa).
- Cabeçalho: lido em **todos** os CSVs listados abaixo (todas as UFs de cada ZIP). Em cada
  família o cabeçalho é idêntico entre todos os membros lidos.
- Valores (especiais, tipos, nulos) vêm apenas desse início dos arquivos, na ordem em que o TSE
  os grava; não são estatística do arquivo completo. Valores raros que só aparecem mais
  adiante podem não ter sido vistos. A coluna "linhas" da tabela é o tamanho da amostra.
- Só foi visto o turno 1 (`NR_TURNO` = 1 em todas as linhas amostradas de resultados). Se o
  turno 2 sair em arquivos novos ou dentro dos mesmos, o layout dele **não** foi verificado.
- Não cobertos: conteúdo dos PDFs (`leiame.pdf`, relatórios de totalização, propostas de
  governo, certidões criminais) e das fotos (JPG); os CSVs só foram verificados nos ZIPs
  listados em `docs/fontes.md`. O ZIP `certidao_criminal_2026_AC.zip` falhou na leitura remota
  do diretório central (`Truncated central directory`); não foi investigado (o formato
  interno é PDF, fora do escopo dos contratos).
- Os dados lidos são de uma fotografia em andamento (arquivos com `Last-Modified` de 06 a
  25/10/2026); contagens e tamanhos mudam quando o TSE regenerar os arquivos.

## Formato (verificado nas 23 famílias de CSV)

| Item | Resultado | Evidência |
|---|---|---|
| Encoding | ISO-8859-1 (latin-1) | UTF-8 estrito falha em todos os membros com bytes não ASCII (todos, exceto `detalhe_votacao_secao_ZZ`, 606 bytes, só ASCII); acentos decodificados como latin-1 saem corretos. Nenhum byte 0x80-0x9F na amostra, então não há evidência de cp1252 (isso não prova que nunca ocorra) |
| BOM | ausente | primeiros bytes de todos os membros lidos |
| Separador | `;` | maior contagem na linha de cabeçalho e número de campos igual ao do cabeçalho em todas as linhas amostradas (0 linhas divergentes) |
| Aspas | `"` | cabeçalho todo entre aspas; no corpo, colunas de texto entre aspas e colunas numéricas (inteiros, decimais) sem aspas. A convenção é por coluna e não variou entre linhas, salvo vazio (abaixo) |
| Fim de linha | CRLF | todos os membros |
| Datas / horas | `dd/mm/aaaa`, `HH:MM:SS`, `dd/mm/aaaa HH:MM:SS` (só `detalhe_votacao_secao`) | regex sobre todas as linhas amostradas |
| Decimais | vírgula (`VR_BEM_CANDIDATO`, `NR_LATITUDE`, `NR_LONGITUDE`); ponto (`VR_DESPESA_MAX_CAMPANHA`) | o separador muda de coluna para coluna; contrato traz `decimal_comma`/`decimal_point` |
| Códigos com zeros à esquerda | `CD_MUNICIPIO` (5 dígitos), `NR_CEP`, `NR_PROCESSO`, `NR_TELEFONE_LOCAL`, identificadores pessoais | marcados `zero_padded: true` ou tipo `str` no contrato; devem ser lidos como texto |
| Vazio | `""` (campo entre aspas, mesmo em coluna numérica) | `historico_candidatura.CD_SITUACAO_JULGAMENTO`; vazios também em `DT_NASCIMENTO` e `NR_IDADE_DATA_POSSE` (4 linhas cada, coincidindo em número com as linhas "não divulgável") |

Os tipos do contrato são inferidos da amostra: `str` quando a coluna mistura formatos ou tem
zeros à esquerda; qualquer coluna pode ganhar valores novos fora da amostra.

## Estrutura dos ZIPs

- ZIPs de um único arquivo-fonte por UF (`votacao_secao_2026_{UF}.zip`,
  `perfil_eleitor_secao_2026_{UF}.zip`): contêm `<familia>_2026_{UF}.csv` e `leiame.pdf`.
  `votacao_secao` tem `BR` (presidente) e as 27 UFs; `perfil_eleitor_secao` tem as 27 UFs e
  `ZZ` (exterior), sem `BR`.
- ZIPs nacionais com vários CSVs (padrão `<familia>_2026_{UF}.csv`): 27 UFs + `BR` + `BRASIL`
  (+ `ZZ` em alguns) + `leiame.pdf`. Na amostra de `votacao_candidato_munzona`, `BR` só tem
  Presidente (linhas por município de cada UF); as UFs têm governador, senador e deputados.
- **`_BRASIL.csv` é redundante**: o tamanho descomprimido de `BRASIL` é praticamente igual à
  soma de todos os outros CSVs do ZIP (razão 0,997 a 1,000 nos arquivos grandes; a diferença é
  o cabeçalho repetido), e na amostra suas linhas trazem todas as UFs e cargos. Ingerir
  `BRASIL` junto com as UFs duplicaria os dados (verificado por tamanho e amostra, não
  linha a linha). Nos arquivos pequenos (`consulta_vagas`, razão 0,86) a conta não fecha e não
  foi investigada.
- `leiame.pdf` está em todo ZIP de CSV (conteúdo tratado na auditoria de PII).
- Recursos sem CSV, sem contrato: relatórios de totalização (PDF), fotos (JPG), propostas de
  governo (PDF), certidões criminais (PDF).

## Famílias, contratos e tamanho da amostra

`UF` nos nomes = sigla do membro. "Arquivos" = CSVs com cabeçalho lido; "linhas" = linhas
amostradas (início dos arquivos, ver limites acima). Número de colunas = tamanho do contrato.

| Família (= `config/contracts/<familia>.yaml`) | CKAN | Membro | Colunas | Arquivos | Linhas |
|---|---|---|---|---|---|
| `bem_candidato` | candidatos-2026 | `bem_candidato_2026_{UF}.csv` | 19 | 29 | 70,555 |
| `consulta_cand` | candidatos-2026 | `consulta_cand_2026_{UF}.csv` | 50 | 29 | 22,015 |
| `consulta_cand_complementar` | candidatos-2026 | `consulta_cand_complementar_2026_{UF}.csv` | 49 | 29 | 23,929 |
| `consulta_coligacao` | candidatos-2026 | `consulta_coligacao_2026_{UF}.csv` | 28 | 29 | 7,027 |
| `consulta_vagas` | candidatos-2026 | `consulta_vagas_2026_{UF}.csv` | 15 | 29 | 382 |
| `detalhe_votacao_munzona` | resultados-2026 | `detalhe_votacao_munzona_2026_{UF}.csv` | 47 | 29 | 31,984 |
| `detalhe_votacao_secao` | resultados-2026 | `detalhe_votacao_secao_2026_{UF}.csv` | 37 | 30 | 108,550 |
| `eleitorado_local_votacao` | eleitorado-2026 | `eleitorado_local_votacao_2026_{UF}.csv` | 41 | 29 | 85,367 |
| `historico_candidatura` | candidatos-2026 | `historico_candidatura_2026_{UF}.csv` | 31 | 29 | 51,889 |
| `motivo_cassacao` | candidatos-2026 | `motivo_cassacao_2026_{UF}.csv` | 14 | 29 | 2,628 |
| `municipio_tse_ibge` | codigos-oficiais-de-uf-e-municipios-segundo-o-tse-e-o-ibge | `municipio_tse_ibge.csv` | 10 | 1 | 5,571 |
| `perfil_comparecimento_abstencao` | comparecimento-e-abstencao-2026 | `perfil_comparecimento_abstencao_2026_{UF}.csv` | 45 | 29 | 199,214 |
| `perfil_comparecimento_abstencao_eleitor_deficiencia` | comparecimento-e-abstencao-2026 | `perfil_comparecimento_abstencao_eleitor_deficiencia_2026_{UF}.csv` | 20 | 29 | 186,383 |
| `perfil_comparecimento_abstencao_eleitor_tte` | comparecimento-e-abstencao-2026 | `perfil_comparecimento_abstencao_eleitor_tte_2026.csv` | 25 | 1 | 133,468 |
| `perfil_eleitor_deficiencia` | eleitorado-2026 | `perfil_eleitor_deficiencia_2026_{UF}.csv` | 30 | 29 | 153,083 |
| `perfil_eleitor_secao` | eleitorado-2026 | `perfil_eleitor_secao_2026_{UF}.csv` | 30 | 28 | 2,805,462 |
| `perfil_eleitorado` | eleitorado-2026 | `perfil_eleitorado_2026_{UF}.csv` | 27 | 29 | 276,811 |
| `rede_social_candidato` | candidatos-2026 | `rede_social_candidato_2026_{UF}.csv` | 11 | 29 | 67,777 |
| `transf_temporaria_secao` | eleitorado-2026 | `transf_temporaria_secao_2026.csv` | 17 | 1 | 192,692 |
| `transferencia_temporaria` | eleitorado-2026 | `transferencia_temporaria_2026.csv` | 13 | 1 | 215,049 |
| `votacao_candidato_munzona` | resultados-2026 | `votacao_candidato_munzona_2026_{UF}.csv` | 50 | 29 | 72,404 |
| `votacao_partido_munzona` | resultados-2026 | `votacao_partido_munzona_2026_{UF}.csv` | 38 | 29 | 79,171 |
| `votacao_secao` | resultados-2026 | `votacao_secao_2026_{UF}.csv` | 26 | 28 | 2,369,286 |
A lista de colunas de cada família está no respectivo YAML (nome, tipo, `zero_padded`,
`special`).

## Catálogo de valores especiais

Padrões procurados na amostra: `#NULO`, `#NULO#`, `#NE` e inteiros `-1` a `-9`. Cada linha
abaixo foi observada na amostra (contagem = ocorrências na amostra, não no arquivo inteiro).

Convenções inferidas do pareamento código/descrição (mesmas contagens nas duas colunas), não
documentadas pela fonte:

- `-1` no código com `#NULO` na descrição: valor nulo/sem informação.
- `-3` no código com `#NE` na descrição: "não existe"/não aplicável ao momento (sempre
  aparecem juntos; ex.: situação de candidatura em arquivos gerados antes do julgamento).
- `-4` com `NÃO DIVULGÁVEL` (e `Não divulgável` em colunas de texto): dado deliberadamente
  omitido; apareceu em 4 linhas de `consulta_cand`/`consulta_cand_complementar`, em colunas de
  identificação e perfil pessoal.
- `-1` também é sentinela numérica em colunas que não têm descrição par
  (`NR_SECAO_PRINCIPAL`, `NR_TELEFONE_LOCAL`, `NR_LATITUDE`, `NR_LONGITUDE`,
  `NR_PROTOCOLO_CANDIDATURA`, `SQ_SUBSTITUIDO`, `SQ_ORDEM_SUPLENCIA`, `NR_PROCESSO`, ...).
- `SQ_CANDIDATO` em `votacao_secao`: `-1` ocorre em votos nulo/branco (`NR_VOTAVEL` 96/95) e
  `-3` em votos de legenda (nomes de partido); verificado na amostra.
- `CD_FAIXA_ETARIA = -3` nos perfis de eleitorado: significado não confirmado.
- Placeholders textuais fora do padrão acima, só em colunas de texto: `NÃO INFORMADO`
  (perfis), `NÃO DIVULGÁVEL`, `NÃO INFORMADA`, `NÃO SABE`, `NÃO DETERMINADA` (etnia/grupo
  indígena), `NÃO ELEITO` e `Não eleito` (valor legítimo de `DS_SIT_TOT_TURNO`, não nulo).
- Falsos positivos descartados: textos livres que começam com `#` (nome de urna, URL de rede
  social) não são sentinelas.

| Valor | Coluna | Famílias onde apareceu | Ocorrências na amostra |
|---|---|---|---|
| `#NE` | `DS_DETALHE_SITUACAO_CAND` | `consulta_cand_complementar`, `votacao_candidato_munzona` | 96,333 |
| `#NE` | `DS_SITUACAO_CANDIDATO_PLEITO` | `consulta_cand_complementar` | 23,929 |
| `#NE` | `DS_SITUACAO_CANDIDATO_URNA` | `consulta_cand_complementar` | 23,929 |
| `#NE` | `DS_SITUACAO_CANDIDATURA` | `consulta_cand`, `historico_candidatura`, `votacao_candidato_munzona` | 112,019 |
| `#NE` | `DS_SITUACAO_JULGAMENTO` | `historico_candidatura` | 32,064 |
| `#NE` | `NM_TIPO_DESTINACAO_VOTOS` | `consulta_coligacao` | 4,803 |
| `#NE` | `ST_REELEICAO` | `consulta_cand_complementar` | 23,925 |
| `#NULO` | `DS_COMPOSICAO_FEDERACAO` | `consulta_cand`, `consulta_coligacao`, `votacao_candidato_munzona`, `votacao_partido_munzona` | 118,292 |
| `#NULO` | `DS_COR_RACA_FEFC` | `consulta_cand_complementar` | 435 |
| `#NULO` | `DS_ETNIA_INDIGENA` | `consulta_cand_complementar` | 10,407 |
| `#NULO` | `DS_GENERO_FEFC` | `consulta_cand_complementar` | 436 |
| `#NULO` | `DS_SITUACAO_CANDIDATO_TOT` | `consulta_cand_complementar` | 1,237 |
| `#NULO` | `DS_SITUACAO_CASSACAO` | `consulta_cand_complementar`, `votacao_candidato_munzona` | 96,333 |
| `#NULO` | `DS_SITUACAO_CASSACAO_MIDIA` | `consulta_cand_complementar` | 23,929 |
| `#NULO` | `DS_SITUACAO_DCONST_DIPLOMA` | `votacao_candidato_munzona` | 72,404 |
| `#NULO` | `DS_SITUACAO_DIPLOMA` | `consulta_cand_complementar` | 23,929 |
| `#NULO` | `DS_SITUACAO_JULGAMENTO_PLEITO` | `consulta_cand_complementar` | 1,237 |
| `#NULO` | `DS_SITUACAO_JULGAMENTO_URNA` | `consulta_cand_complementar` | 1,237 |
| `#NULO` | `DS_SIT_TOT_TURNO` | `consulta_cand`, `historico_candidatura` | 3,774 |
| `#NULO` | `NM_COLIGACAO` | `consulta_coligacao` | 3,284 |
| `#NULO` | `NM_FEDERACAO` | `consulta_cand`, `consulta_coligacao`, `votacao_candidato_munzona`, `votacao_partido_munzona` | 118,292 |
| `#NULO` | `NM_SOCIAL_CANDIDATO` | `consulta_cand`, `votacao_candidato_munzona` | 94,316 |
| `#NULO` | `NM_TIPO_DESTINACAO_VOTOS` | `consulta_cand_complementar` | 2,188 |
| `#NULO` | `SG_FEDERACAO` | `consulta_cand`, `consulta_coligacao`, `votacao_candidato_munzona`, `votacao_partido_munzona` | 118,292 |
| `#NULO#` | `DS_TIPO_TRANSFERENCIA` | `perfil_comparecimento_abstencao_eleitor_tte` | 34 |
| `-1` | `CD_COR_RACA` | `perfil_comparecimento_abstencao` | 68,174 |
| `-1` | `CD_COR_RACA_FEFC` | `consulta_cand_complementar` | 435 |
| `-1` | `CD_ETNIA_INDIGENA` | `consulta_cand_complementar` | 10,407 |
| `-1` | `CD_GENERO_FEFC` | `consulta_cand_complementar` | 436 |
| `-1` | `CD_GRUPO_INDIGENA` | `perfil_comparecimento_abstencao` | 195,946 |
| `-1` | `CD_IDENTIDADE_GENERO` | `perfil_comparecimento_abstencao`, `perfil_eleitor_deficiencia`, `perfil_eleitor_secao`, `perfil_eleitorado` | 2,054,223 |
| `-1` | `CD_IDIOMA_INDIGENA` | `perfil_comparecimento_abstencao` | 162,250 |
| `-1` | `CD_IDIOMA_QUILOMBOLA` | `perfil_comparecimento_abstencao` | 163,512 |
| `-1` | `CD_INTERPRETE_LIBRAS` | `perfil_comparecimento_abstencao`, `perfil_eleitor_deficiencia`, `perfil_eleitor_secao`, `perfil_eleitorado` | 2,054,227 |
| `-1` | `CD_QUILOMBOLA` | `perfil_comparecimento_abstencao`, `perfil_eleitor_deficiencia`, `perfil_eleitor_secao`, `perfil_eleitorado` | 2,054,222 |
| `-1` | `CD_RACA_COR` | `perfil_eleitor_deficiencia`, `perfil_eleitor_secao`, `perfil_eleitorado` | 1,986,049 |
| `-1` | `CD_SITUACAO_CANDIDATO_TOT` | `consulta_cand_complementar` | 1,237 |
| `-1` | `CD_SITUACAO_CASSACAO` | `consulta_cand_complementar`, `votacao_candidato_munzona` | 96,333 |
| `-1` | `CD_SITUACAO_CASSACAO_MIDIA` | `consulta_cand_complementar` | 23,929 |
| `-1` | `CD_SITUACAO_DCONST_DIPLOMA` | `votacao_candidato_munzona` | 72,404 |
| `-1` | `CD_SITUACAO_DIPLOMA` | `consulta_cand_complementar` | 23,929 |
| `-1` | `CD_SITUACAO_JULGAMENTO_PLEITO` | `consulta_cand_complementar` | 1,237 |
| `-1` | `CD_SITUACAO_JULGAMENTO_URNA` | `consulta_cand_complementar` | 1,237 |
| `-1` | `CD_SITU_ZONA` | `eleitorado_local_votacao` | 84,667 |
| `-1` | `CD_SIT_TOT_TURNO` | `consulta_cand`, `historico_candidatura` | 3,774 |
| `-1` | `NR_FEDERACAO` | `consulta_cand`, `consulta_coligacao`, `votacao_candidato_munzona`, `votacao_partido_munzona` | 118,292 |
| `-1` | `NR_LATITUDE` | `eleitorado_local_votacao` | 3,176 |
| `-1` | `NR_LONGITUDE` | `eleitorado_local_votacao` | 3,176 |
| `-1` | `NR_PROCESSO` | `motivo_cassacao` | 2,628 |
| `-1` | `NR_PROTOCOLO_CANDIDATURA` | `consulta_cand_complementar` | 23,929 |
| `-1` | `NR_SECAO_PRINCIPAL` | `eleitorado_local_votacao` | 81,137 |
| `-1` | `NR_TELEFONE_LOCAL` | `eleitorado_local_votacao` | 32,963 |
| `-1` | `SQ_CANDIDATO` | `votacao_secao` | 182,642 |
| `-1` | `SQ_ORDEM_SUPLENCIA` | `consulta_cand_complementar` | 11,257 |
| `-1` | `SQ_SUBSTITUIDO` | `consulta_cand_complementar` | 23,607 |
| `-1` | `VR_DESPESA_MAX_CAMPANHA` | `consulta_cand_complementar` | 1,068 |
| `-3` | `CD_DETALHE_SITUACAO_CAND` | `consulta_cand_complementar`, `votacao_candidato_munzona` | 96,333 |
| `-3` | `CD_FAIXA_ETARIA` | `perfil_comparecimento_abstencao`, `perfil_comparecimento_abstencao_eleitor_deficiencia`, `perfil_eleitor_deficiencia`, `perfil_eleitor_secao`, `perfil_eleitorado` | 102 |
| `-3` | `CD_MUNICIPIO_NASCIMENTO` | `consulta_cand_complementar` | 23,929 |
| `-3` | `CD_SITUACAO_CANDIDATO_PLEITO` | `consulta_cand_complementar` | 23,929 |
| `-3` | `CD_SITUACAO_CANDIDATO_URNA` | `consulta_cand_complementar` | 23,929 |
| `-3` | `CD_SITUACAO_CANDIDATURA` | `consulta_cand`, `historico_candidatura`, `votacao_candidato_munzona` | 112,019 |
| `-3` | `CD_SITUACAO_JULGAMENTO` | `historico_candidatura` | 32,064 |
| `-3` | `SQ_CANDIDATO` | `votacao_secao` | 130,206 |
| `-4` | `CD_COR_RACA` | `consulta_cand` | 4 |
| `-4` | `CD_COR_RACA_FEFC` | `consulta_cand_complementar` | 4 |
| `-4` | `CD_ESTADO_CIVIL` | `consulta_cand` | 4 |
| `-4` | `CD_ETNIA_INDIGENA` | `consulta_cand_complementar` | 4 |
| `-4` | `CD_GENERO` | `consulta_cand` | 4 |
| `-4` | `CD_GENERO_FEFC` | `consulta_cand_complementar` | 4 |
| `-4` | `CD_GRAU_INSTRUCAO` | `consulta_cand` | 4 |
| `-4` | `CD_NACIONALIDADE` | `consulta_cand_complementar` | 4 |
| `-4` | `CD_OCUPACAO` | `consulta_cand` | 4 |
| `-4` | `NR_CPF_CANDIDATO` | `consulta_cand` | 4 |
| `-4` | `NR_TITULO_ELEITORAL_CANDIDATO` | `consulta_cand` | 4 |
| `-4` | `VR_DESPESA_MAX_CAMPANHA` | `consulta_cand_complementar` | 4 |

## Tamanhos reais e inventário

`docs/fontes.md` é gerado por `urna_aberta.discover` (tamanho comprimido via HEAD) e continua
correto: os tamanhos dos ZIPs não divergiram. O que o HEAD não mostra é o tamanho
descomprimido, lido do diretório central dos ZIPs (soma dos CSVs, **sem** `BRASIL`, que é
redundante):

| Conjunto | ZIPs (GiB) | CSVs descomprimidos (GiB) |
|---|---|---|
| Todas as famílias de CSV dos 5 datasets habilitados | 6,8 | 50,5 |
| `perfil_eleitor_secao` (28 ZIPs) | 2,6 | 21,5 |
| `votacao_secao` (28 ZIPs) | 2,6 | 18,7 |
| `votacao_candidato_munzona` | 0,42 | 3,0 |
| `perfil_comparecimento_abstencao` | 0,21 | 2,8 |
| `perfil_eleitorado` | 0,38 | 2,0 |
| `detalhe_votacao_secao` | 0,16 | 0,84 |

Com `BRASIL` incluído, o total descomprimido dos ZIPs nacionais quase dobra. Fora desses
números ficam relatórios, fotos, propostas e certidões (só as certidões criminais somam
dezenas de GiB, ex.: `SP` 2,3 GiB, `RJ` 1,6 GiB). Os maiores membros isolados são
`votacao_secao_2026_SP` e `perfil_eleitor_secao_2026_SP` (4,6 e 4,4 GiB descomprimidos).
