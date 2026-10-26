# Auditoria de PII nos datasets de 2026

Data da auditoria: 2026-10-26. Arquivos gerados pelo TSE em 25/10/2026 (campo `DT_GERACAO`). Escopo: os cinco datasets habilitados em `config/elections/2026.yaml` (resultados, comparecimento e abstenção, candidatos, eleitorado, códigos de UF/município), mais uma seção "fora do escopo atual".

## 0. Como ler este documento

Cada afirmação traz a fonte entre colchetes e é marcada como fato ou inferência.

- [leiame]: `leiame.pdf` dentro do ZIP oficial do dataset, texto extraído com `pdftotext`.
- [amostra]: medição feita nos ZIPs de 2026 do CDN do TSE. Nenhum valor individual foi gravado; só contagens, comprimentos, formatos e proporções.
- [norma]: texto de lei ou resolução. A Res. TSE 23.609/2019 art. 33 §2º aparece transcrita no leiame. Os artigos da LGPD (Lei 13.709/2018) vêm do conhecimento do autor e não foram reconsultados em fonte online nesta auditoria.
- FATO: verificado nos dados ou no leiame. INFERÊNCIA: conclusão minha, não verificada.

Legenda da classificação: **D** identificador direto, **Q** quase-identificador, **S** sensível (LGPD art. 5º II), **N** sem risco relevante.
Ação na silver: **manter**, **descartar**, **hash** (HMAC com chave secreta fora do repositório), **generalizar**, **suprimir** (células pequenas).

## 1. Resposta direta: dados pessoais dos candidatos em 2026

Fonte: `consulta_cand_2026.zip`, arquivo `consulta_cand_2026_BRASIL.csv`. Foi lido o arquivo inteiro, não uma amostra: 21.017 linhas (candidaturas, todas as UFs). Conferência cruzada com `_SP` (2.630 linhas), `_AC` (392) e `_BR` (32).

| Campo | Em 2026 | Evidência |
|---|---|---|
| `NR_CPF_CANDIDATO` | **REAL**. 21.014 de 21.017 linhas (99,99%) têm 11 dígitos. As 3 restantes valem `-4` (mascaradas: 1 senador, 1º suplente, 2º suplente). | [amostra] Os 21.014 CPFs passam 100% na validação dos dígitos verificadores. Isso é compatível com CPF real. Um número aleatório passaria em cerca de 1%. Há 20.875 valores distintos. Os repetidos correspondem ao mesmo candidato em mais de uma linha (por exemplo, turnos). |
| `DS_EMAIL` | **MASCARADO**. 100% das 21.017 linhas valem `NÃO DIVULGÁVEL`. | [amostra], confirmado em SP, AC e BR. |
| `NR_TITULO_ELEITORAL_CANDIDATO` | **REAL**. 21.014 linhas com 12 dígitos; 3 com `-4`. | [amostra] 97,2% dos 21.014 passam no dígito verificador do título (algoritmo que escrevi; a diferença de 2,8% pode ser erro do meu validador ou título atípico, não foi investigada). Considero real com confiança menor que a do CPF. |
| `DT_NASCIMENTO` | **REAL**. 21.014 linhas no formato `dd/mm/aaaa`; 3 vazias. Anos entre 1934 e 2007. | [amostra] |
| Endereço residencial | **Não existe coluna** nos arquivos de candidatos. | [leiame] e cabeçalhos. A coluna `DS_URL` de redes sociais e as de bens não são endereço, mas veja a seção 4. |
| Telefone | **Não existe coluna** de telefone de candidato. | [leiame] e cabeçalhos. Mas `DS_URL` (redes sociais) contém links `wa.me`/`tel:`/`mailto:`; ver seção 4. |
| `NM_CANDIDATO`, `NM_URNA_CANDIDATO` | Reais (nomes). Não foram gravados aqui. | [amostra] só formato. |
| Município de nascimento (`NM_MUNICIPIO_NASCIMENTO`, complementar) | Real. | [amostra] |

Contradição entre leiame e dados (FATO):

- O leiame de `consulta_cand` diz que, pela Res. TSE 23.609/2019 art. 33 §2º (incluído pela Res. 23.729/2024), CPF, e-mail pessoal, telefone pessoal e documento pessoal "não serão divulgados" e que `NR_CPF_CANDIDATO` é "não divulgável". O texto fala em "Eleições 2024". [leiame, norma]
- O arquivo de 2026 traz CPF real para quase todos. [amostra]
- Comparação que fiz no mesmo dataset: em 2024 (`consulta_cand_2024_AC.csv`, 2.311 linhas) o CPF é `-4` em 100% das linhas, e título e nascimento são reais. Em 2022 (`consulta_cand_2022_AC.csv`, 542 linhas) o CPF é real em 540 de 542. [amostra]
- INFERÊNCIA: o texto do leiame não foi atualizado, ou o mascaramento de 2026 falhou ou foi desligado. Eu não consigo distinguir. Quem decide é o TSE (estatistica@tse.jus.br). Para este projeto, o que vale é o dado real: tratar como se o CPF e o título estivessem expostos por engano e não propagá-los.

O que NÃO foi verificado:
- Se os CPFs e títulos são de pessoas reais (só validei formato e dígito verificador; não cruzei com nenhuma base).
- Se o mascaramento depende da UF além de SP, AC, BR e do arquivo BRASIL; os 27 arquivos de UF não foram lidos individualmente (o BRASIL os consolida).
- Se arquivos posteriores a 25/10/2026 mudam. O TSE reescreve os arquivos ("em constante processo de atualização" [leiame]); a conclusão vale para a geração de 25/10/2026.
- Endereço e telefone: ausência de coluna é fato; ausência desses dados dentro de campos de texto livre foi checada só por heurística (seção 4).

## 2. Classificação por dataset e coluna

Colunas de metadado de geração e de eleição (`DT_GERACAO`, `HH_GERACAO`, `ANO_ELEICAO`/`AA_ELEICAO`, `CD_TIPO_ELEICAO`, `NM_TIPO_ELEICAO`, `NR_TURNO`, `CD_ELEICAO`, `DS_ELEICAO`, `DT_ELEICAO`, `TP_ABRANGENCIA`, `SG_UF`, `SG_UE`, `NM_UE`, `CD_CARGO`, `DS_CARGO`, `HH/DT_ULTIMA_TOTALIZACAO`) são **N** em todos os datasets e ficam de fora das tabelas abaixo. [amostra: valores constantes ou de baixa cardinalidade]

Marcadores de valor ausente nos arquivos [leiame]: `#NULO`/`-1` (em branco), `#NE`/`-3` (não era registrado), `-4`/`NÃO DIVULGÁVEL` (candidato não divulgável). A silver precisa normalizá-los para nulo, senão `-4` entra como número.

### 2.1 candidatos-2026

#### consulta_cand (50 colunas; 21.017 linhas no BRASIL)

| Coluna | Classe | Ação silver | Justificativa |
|---|---|---|---|
| `SQ_CANDIDATO` | Q (chave interna) | manter | Chave de junção entre os arquivos. Não é o CPF. [leiame] |
| `NR_CPF_CANDIDATO` | **D** | **descartar** | CPF real em 2026 (seção 1). |
| `NR_TITULO_ELEITORAL_CANDIDATO` | **D** | **descartar** | Título real. |
| `DS_EMAIL` | D (mascarado) | descartar | 100% `NÃO DIVULGÁVEL`, sem valor analítico. Se algum dia vier preenchido, vira D. |
| `DT_NASCIMENTO` | D/Q (com nome, identifica) | **descartar** ou **generalizar** para ano | Combinada com o nome é quase única. Usar `NR_IDADE_DATA_POSSE` (complementar) para análise. |
| `NM_CANDIDATO` | D | manter (condição: finalidade eleitoral) | Candidato é figura pública; nome é o ponto do produto. Ver seção 6. |
| `NM_URNA_CANDIDATO` | D | manter | Nome de urna, público por natureza. |
| `NM_SOCIAL_CANDIDATO` | S + D | **descartar** na camada pública | Em 20.959 de 21.017 linhas vale `#NULO`; as 58 restantes revelam identidade de gênero (travesti/transexual, [leiame]). INFERÊNCIA: dado sensível por associação. |
| `NR_CANDIDATO` | Q | manter | Número na urna, público. |
| `SG_PARTIDO`, `NR_PARTIDO`, `NM_PARTIDO`, `NR_/NM_/SG_FEDERACAO`, `DS_COMPOSICAO_FEDERACAO`, `TP_AGREMIACAO`, `SQ_COLIGACAO`, `NM_COLIGACAO`, `DS_COMPOSICAO_COLIGACAO` | S (opinião política / filiação) | manter | LGPD art. 5º II lista opinião política e filiação a organização de caráter político. A candidatura é pública por lei e o partido é inerente a ela; o dado é divulgado pela Justiça Eleitoral com finalidade eleitoral. Manter, com a condição da seção 6. |
| `SG_UF_NASCIMENTO` | Q | manter ou generalizar | Baixa cardinalidade (29). |
| `CD_GENERO`, `DS_GENERO` | Q | manter | Binário no leiame (2/4). 3 linhas `-4`. |
| `CD_GRAU_INSTRUCAO`, `DS_GRAU_INSTRUCAO` | Q | manter | |
| `CD_ESTADO_CIVIL`, `DS_ESTADO_CIVIL` | Q | manter | |
| `CD_COR_RACA`, `DS_COR_RACA` | **S** (origem racial) | manter com condição | Dado sensível; é a base das políticas de cota (FEFC). Manter só agregado ou no nível da candidatura pública. |
| `CD_OCUPACAO`, `DS_OCUPACAO` | Q | manter | Alta cardinalidade; combinada com UF/cargo pode ser única. |
| `CD_SITUACAO_CANDIDATURA`, `DS_SITUACAO_CANDIDATURA` | N | manter | Constantes `-3`/`#NE` em 2026. [amostra] |
| `CD_SIT_TOT_TURNO`, `DS_SIT_TOT_TURNO` | N | manter | Resultado da candidatura. |

#### consulta_cand_complementar (49 colunas)

| Coluna | Classe | Ação silver |
|---|---|---|
| `SQ_CANDIDATO`, `SQ_SUBSTITUIDO`, `SQ_ORDEM_SUPLENCIA` | Q | manter |
| `NR_PROTOCOLO_CANDIDATURA` | N | manter (constante `-1`) |
| `NR_PROCESSO` | Q/D (número de processo judicial de 20 dígitos, 100% preenchido) | descartar na camada pública. INFERÊNCIA: permite consultar o processo no PJe e chegar a documentos do candidato. |
| `CD_NACIONALIDADE`, `DS_NACIONALIDADE` | Q | manter |
| `CD_MUNICIPIO_NASCIMENTO` | N | constante `-3` |
| `NM_MUNICIPIO_NASCIMENTO` | Q | generalizar para UF ou descartar. Preenchido com nome real. |
| `NR_IDADE_DATA_POSSE` | Q | manter (substitui nascimento) |
| `ST_QUILOMBOLA` | **S** (origem étnica) | manter só agregado |
| `CD_ETNIA_INDIGENA`, `DS_ETNIA_INDIGENA` | **S** (origem étnica) | manter só agregado |
| `CD_GENERO_FEFC`, `DS_GENERO_FEFC`, `CD_COR_RACA_FEFC`, `DS_COR_RACA_FEFC` | S | idem cor/raça acima |
| `VR_DESPESA_MAX_CAMPANHA` | N | manter |
| `ST_REELEICAO`, `ST_DECLARAR_BENS`, `ST_PREST_CONTAS`, `ST_SUBSTITUIDO`, `ST_CANDIDATO_INSERIDO_URNA` | N | manter |
| `DT_ACEITE_CANDIDATURA` | N | manter |
| `NM_TIPO_DESTINACAO_VOTOS`, `CD/DS_SITUACAO_*`, `CD/DS_DETALHE_SITUACAO_CAND`, `CD/DS_SITUACAO_CASSACAO*`, `CD/DS_SITUACAO_DIPLOMA` | N | manter. Situação jurídica de candidatura é pública; vários campos vêm constantes. |

#### bem_candidato (19 colunas; 77.446 linhas; 13.918 candidatos)

| Coluna | Classe | Ação silver |
|---|---|---|
| `SQ_CANDIDATO`, `NR_ORDEM_BEM_CANDIDATO` | Q | manter |
| `CD_TIPO_BEM_CANDIDATO`, `DS_TIPO_BEM_CANDIDATO` | Q | manter |
| `VR_BEM_CANDIDATO` | Q (patrimônio) | manter. Dado pessoal não sensível pelo art. 5º II, mas financeiro; é declarado por força de lei na candidatura. |
| `DS_BEM_CANDIDATO` | **Q/D** (texto livre) | **descartar** ou **sanear** | Heurística por regex em texto livre (não confirmada linha a linha): 4.222 linhas com palavra de endereço (rua, avenida, quadra, lote, CEP), 333 com padrão de CPF, 430 com padrão de placa, 1.370 com padrão de CNPJ, 249 com matrícula/inscrição/cartório, 79 com padrão de telefone, 0 com e-mail. Podem ser falsos positivos, mas o texto livre exige sanear. |
| `DT_ULT_ATUAL_BEM_CANDIDATO`, `HH_ULT_ATUAL_BEM_CANDIDATO` | N | manter |

#### rede_social_candidato (11 colunas; 63.250 linhas)

| Coluna | Classe | Ação silver |
|---|---|---|
| `SQ_CANDIDATO`, `NR_ORDEM_REDE_SOCIAL` | Q | manter |
| `DS_URL` | D (perfil pessoal) | manter apenas links de perfil público. **Descartar** as linhas `wa.me`, `tel:`, `mailto:` e `chat.whatsapp.com`: 2.274 linhas casam (regex), 235 trazem padrão de e-mail e 171 padrão de telefone (heurística, pode haver falso positivo). INFERÊNCIA: parte são telefones pessoais ou de campanha, o que a regra do art. 33 §2º visa proteger. |

#### consulta_coligacao (28), consulta_vagas (15), motivo_cassacao (14)

| Coluna | Classe | Ação silver |
|---|---|---|
| Colunas de agremiação (`NR_/SG_/NM_PARTIDO`, federação, coligação, composição) | S (filiação política institucional) | manter. É dado de partido, não de pessoa. |
| `CD_SITUACAO_LEGENDA`, `DS_SITUACAO`, `NM_TIPO_DESTINACAO_VOTOS` | N | manter |
| `QT_VAGA`, `DT_POSSE` | N | manter |
| `SQ_CANDIDATO` (motivo_cassacao) | Q | manter |
| `DS_TP_MOTIVO`, `DS_MOTIVO` | Q (situação jurídica individual: indeferimento, inelegibilidade) | manter, por ser público e de finalidade eleitoral; com `SQ_CANDIDATO` liga a uma pessoa. `NR_PROCESSO` é `-1` em 100%. |

#### historico_candidatura (31 colunas; 55.976 linhas, candidaturas de 2004 a 2026)

| Coluna | Classe | Ação silver |
|---|---|---|
| `SQ_CANDIDATO_ATUAL`, `SQ_CANDIDATO` | Q | manter. Nota: `SQ_CANDIDATO` passado é a única ponte entre eleições sem CPF. |
| `NM_CANDIDATO`, `NM_URNA_CANDIDATO` | D | manter, com a condição da seção 6 |
| `NR_CANDIDATO`, `NR_PARTIDO`, `SG_PARTIDO`, `NM_PARTIDO` | Q/S | manter |
| `CD/DS_SITUACAO_CANDIDATURA`, `CD/DS_SITUACAO_JULGAMENTO`, `CD/DS_SIT_TOT_TURNO`, `TP_ABRANGENCIA_ELEICAO`, `CD_ELEICAO`, `DS_ELEICAO`, `DT_ELEICAO`, `ANO_ELEICAO*`, `NM_UE`, `SG_UE`, `SG_UF*` | N/Q | manter. Histórico individual de candidaturas e indeferimentos; INFERÊNCIA: perfilamento longitudinal de pessoa, mas é público. |

Nota (FATO, [amostra]): `historico_candidatura` não tem CPF.

### 2.2 resultados-2026

| Dataset / coluna | Classe | Ação silver |
|---|---|---|
| `votacao_candidato_munzona`: `SQ_CANDIDATO`, `NR_CANDIDATO`, `NM_CANDIDATO`, `NM_URNA_CANDIDATO` | Q / D | manter |
| `votacao_candidato_munzona`: `NM_SOCIAL_CANDIDATO` | S | descartar (no AC é `#NULO` em 100%, mas pode vir preenchido em outras UFs. **Não verificado** nos outros arquivos) |
| `votacao_candidato_munzona`: `SG/NR/NM_PARTIDO`, federação, coligação | S (filiação política) | manter |
| `votacao_candidato_munzona`: `QT_VOTOS_NOMINAIS*`, `NM_TIPO_DESTINACAO_VOTOS`, `CD/DS_SIT_TOT_TURNO`, situação de julgamento/cassação/diploma | N | manter |
| `votacao_candidato_munzona`: `CD_MUNICIPIO`, `NM_MUNICIPIO`, `NR_ZONA` | Q | manter (agregado por zona) |
| `votacao_partido_munzona`: partido, federação, coligação, `QT_VOTOS_*` | S institucional / N | manter |
| `detalhe_votacao_munzona`: `QT_APTOS`, `QT_COMPARECIMENTO`, `QT_ABSTENCOES`, `QT_VOTOS_*`, `QT_SECOES_*` | N | manter (agregado por zona) |
| `detalhe_votacao_secao`: `NR_SECAO`, `NR_LOCAL_VOTACAO` | Q | manter com a ressalva da seção 5 (seção pequena) |
| `detalhe_votacao_secao`: `NM_LOCAL_VOTACAO`, `DS_LOCAL_VOTACAO_ENDERECO` | N/Q (endereço de escola ou prédio público, não de pessoa) | manter. [amostra]: formato "logradouro, número". Não é residência de eleitor. INFERÊNCIA. |
| `detalhe_votacao_secao`: `QT_APTOS`, `QT_COMPARECIMENTO`, `QT_ABSTENCOES`, `QT_VOTOS_*`, `DT_RECEBIMENTO_BU_HOR_TSE`, `DT_PRIM_TOT_PARCIAL_HOR_TSE`, `CD/DS_MODELO_URNA`, `DS_ORIGEM_VOTO`, `ST_SECAO_*` | N | manter |
| `votacao_secao` (por UF e BR): `NR_VOTAVEL`, `NM_VOTAVEL`, `SQ_CANDIDATO` | Q / D | manter |
| `votacao_secao`: `QT_VOTOS` | Q (célula pequena, seção 5) | manter; ver risco |
| `votacao_secao`: `NR_ZONA`, `NR_SECAO`, `NR_LOCAL_VOTACAO`, `NM_LOCAL_VOTACAO`, `DS_LOCAL_VOTACAO_ENDERECO` | Q / N | manter |

### 2.3 comparecimento-e-abstencao-2026

#### perfil_comparecimento_abstencao (45 colunas; agregado por UF, município, zona e perfil)

| Coluna | Classe | Ação silver |
|---|---|---|
| `CD/DS_GENERO` | Q | manter |
| `CD/DS_ESTADO_CIVIL` | Q | manter |
| `CD/DS_FAIXA_ETARIA` | Q | manter |
| `CD/DS_GRAU_INSTRUCAO` | Q | manter |
| `CD/DS_COR_RACA` | **S** | manter só agregado com supressão |
| `CD/DS_QUILOMBOLA`, `CD/DS_GRUPO_INDIGENA`, `CD/DS_IDIOMA_INDIGENA`, `CD/DS_IDIOMA_QUILOMBOLA` | **S** (origem étnica) | suprimir células pequenas; grupo indígena tem 53 valores, alto risco |
| `CD/DS_IDENTIDADE_GENERO` | **S** (INFERÊNCIA: identidade de gênero é conservadoramente sensível) | suprimir células pequenas |
| `CD/DS_INTERPRETE_LIBRAS` | **S** (saúde/deficiência, INFERÊNCIA) | suprimir células pequenas |
| `QT_APTOS`, `QT_COMPARECIMENTO`, `QT_ABSTENCAO` e variantes (`_DEFICIENCIA`, `_TTE`, `_FACULTATIVO`, `_OBRIGATORIO`, `_DEFIC_*`) | Q (contagem pequena) | suprimir se < k (seção 5) |
| `NM_MUNICIPIO`, `NR_ZONA`, `CD_MUNICIPIO` | Q | manter |

#### perfil_comparecimento_abstencao_eleitor_deficiente (20 colunas)

| Coluna | Classe | Ação silver |
|---|---|---|
| `SQ_ELEITOR` | **D** (identificador sequencial de eleitor) | **descartar** |
| `CD/DS_TIPO_DEFICIENCIA` | **S** (saúde) | descartar neste nível |
| `ST_COMPARECIMENTO` | S (conduta eleitoral individual: votou/faltou) | descartar neste nível |
| `CD/DS_GENERO`, `ESTADO_CIVIL`, `FAIXA_ETARIA`, `GRAU_INSTRUCAO`, `NR_ZONA`, município | Q | só em agregado |

Este arquivo é **uma linha por eleitor com deficiência** (campo `SQ_ELEITOR`, e o leiame diz que o sequencial "auxilia na contagem de eleitores que declararam possuir algum tipo de deficiência" [leiame]). Não medi unicidade de `SQ_ELEITOR` nem classes k=1 neste arquivo (só no de perfil de deficiência, seção 2.4).

#### perfil_comparecimento_abstencao_eleitor_tte (25 colunas)

| Coluna | Classe | Ação silver |
|---|---|---|
| UF/município/zona de origem e destino | Q | manter |
| `CD/DS_TIPO_TRANSFERENCIA` (preso provisório, militar, convocado, acessibilidade, indígena/quilombola) | S (INFERÊNCIA: situação prisional, de saúde ou étnica) | suprimir células pequenas |
| gênero, estado civil, faixa etária, grau de instrução | Q | manter agregado |
| `QT_APTOS_EM_TTE`, `QT_COMPARECIMENTO_TTE`, `QT_ABSTENCAO_TTE` | Q (contagem pequena) | suprimir se < k |

### 2.4 eleitorado-2026

#### perfil_eleitorado (27 colunas)

Mesma estrutura de dimensões do perfil de comparecimento: município, zona, gênero, estado civil, faixa etária, escolaridade, raça/cor, identidade de gênero, quilombola, intérprete de Libras, e contagens `QT_ELEITORES`, `QT_ELEITORES_BIOMETRIA`, `QT_ELEITORES_DEFICIENCIA`, `QT_ELEITORES_NOME_SOCIAL`. Classificação e ação iguais às da seção 2.3. `QT_ELEITORES_NOME_SOCIAL` e `QT_ELEITORES_DEFICIENCIA` são **S** em contagem pequena: suprimir.

#### perfil_eleitor_deficiente (30 colunas) — risco alto

| Coluna | Classe | Ação silver |
|---|---|---|
| `SQ_ELEITOR` | **D** | **descartar** |
| `NR_ZONA`, `NR_SECAO` | Q | descartar neste nível |
| `CD/DS_TIPO_DEFICIENCIA` | **S** (saúde) | descartar neste nível |
| `CD/DS_GENERO`, `ESTADO_CIVIL`, `FAIXA_ETARIA`, `GRAU_ESCOLARIDADE` | Q | só em agregado |
| `CD/DS_RACA_COR`, `CD/DS_IDENTIDADE_GENERO`, `CD/DS_QUILOMBOLA`, `CD/DS_INTERPRETE_LIBRAS` | **S** | só em agregado |
| `ST_ELEITOR_BIOMETRIA`, `CD/DS_MUN_SITU_BIOMETRICA` | N / Q | manter agregado |
| município, UF | Q | manter |

Medição no `_DF` (27.484 linhas; [amostra]):
- 24.832 `SQ_ELEITOR` distintos para 27.484 linhas (um eleitor pode aparecer mais de uma vez, p. ex. por mais de um tipo de deficiência; INFERÊNCIA).
- Há 6.562 seções distintas; o máximo é 37 linhas por seção.
- Com zona, seção, gênero e faixa etária, 69,4% das linhas estão em classes de tamanho 1. Com todas as 9 dimensões, 99,3%.
- Conclusão (FATO sobre os dados, INFERÊNCIA sobre o risco): o arquivo é microdado de pessoas com saúde registrada (deficiência) em nível de seção. Quem conhece um vizinho ou colega com deficiência consegue localizá-lo. É dado de saúde, **sensível**, art. 5º II.

Fora do escopo local mas na mesma família: `perfil_eleitor_secao_<UF>` (30 colunas; só `_AC` perfilado). É agregado por seção com raça/cor, identidade de gênero, etc. Mesma regra de supressão.

### 2.5 codigos-oficiais-de-uf-e-municipios

`municipio_tse_ibge.csv` (10 colunas, 5.571 linhas): `CD_UF_TSE`, `CD_UF_IBGE`, `SG_UF`, `NM_UF`, `CD_MUNICIPIO_TSE`, `NM_MUNICIPIO_TSE`, `CD_MUNICIPIO_IBGE`, `NM_MUNICIPIO_IBGE`. Todas **N**. Manter.

## 3. Colunas a descartar ou hashear na silver

Descartar (não vão nem para a silver, nem para a gold):
- `NR_CPF_CANDIDATO`
- `NR_TITULO_ELEITORAL_CANDIDATO`
- `DS_EMAIL` (hoje sempre `NÃO DIVULGÁVEL`)
- `DT_NASCIMENTO` (usar `NR_IDADE_DATA_POSSE`; se precisar de ano, guardar só o ano)
- `NM_MUNICIPIO_NASCIMENTO` (ou reduzir a UF)
- `NR_PROCESSO` (candidatos complementar)
- `NM_SOCIAL_CANDIDATO` (em todos os arquivos)
- `DS_BEM_CANDIDATO` (texto livre; ou sanear com regex e revisão)
- `DS_URL` das linhas `wa.me`, `tel:`, `mailto:`, `chat.whatsapp.com`
- `SQ_ELEITOR`, `NR_SECAO`, `NR_ZONA`, `CD/DS_TIPO_DEFICIENCIA`, `ST_COMPARECIMENTO` dos arquivos de deficiência (todos eles, no nível de linha por eleitor)

Hashear: nenhuma coluna precisa de hash se a junção entre anos usar `SQ_CANDIDATO` (é por eleição, não liga eleições) ou nome + UF + cargo. Se for indispensável ligar a mesma pessoa entre eleições, usar HMAC-SHA256 do CPF com chave secreta guardada fora do repositório e fora de `data/`, e nunca publicar a chave. INFERÊNCIA: o CPF tem só 10^9 valores válidos, então hash sem chave (SHA puro) é reversível por força bruta. Recomendo não ligar por CPF.

A camada bruta (bronze) em `data/` contém tudo, inclusive CPF e título. `data/` está no `.gitignore` (FATO, conferido), então não vai para o repositório. Não publicar a bronze.

## 4. Campos de texto livre

Medidos só por padrão (regex). Contagens em [amostra], interpretação é INFERÊNCIA:

| Coluna | Linhas | Padrão de endereço | Padrão de CPF | Padrão de telefone | Padrão de e-mail |
|---|---|---|---|---|---|
| `bem_candidato.DS_BEM_CANDIDATO` | 77.446 | 4.222 | 333 | 79 | 0 |
| `rede_social_candidato.DS_URL` | 63.250 | n/a | n/a | 171 | 235 |

Há ainda 2.274 URLs `wa.me`/`whatsapp`/`tel:`/`mailto:`. Não abri nenhum valor para confirmar.

## 5. Riscos de reidentificação

1. **Células pequenas nos perfis do eleitorado e do comparecimento** (FATO, [amostra], arquivo `_TO`). `perfil_eleitorado_2026_TO.csv` tem 168.714 linhas; 48,5% têm `QT_ELEITORES = 1` e 76,4% têm `QT_ELEITORES <= 4`. O arquivo de comparecimento tem a mesma proporção em `QT_APTOS`. Cada linha é uma combinação de município, zona, gênero, estado civil, faixa etária, escolaridade, raça/cor, identidade de gênero, quilombola e Libras. Muitas combinações são uma única pessoa. INFERÊNCIA: o TSE publica isso, mas o projeto não deve republicar nem facilitar o cruzamento sem suprimir.
2. **Seção eleitoral é pequena**. Em `votacao_secao_BR` (primeiras 100.000 linhas), 64,8% das linhas têm `QT_VOTOS` entre 0 e 9. Cruzando `votacao_secao` com `perfil_eleitor_secao` e com o arquivo de deficiência, sobra uma seção com poucos eleitores e perfil conhecido: risco ao sigilo do voto (INFERÊNCIA). O voto continua secreto individualmente; o risco é de dedução por exclusão em seção minúscula.
3. **Arquivos de deficiência** (seção 2.4): 99,3% das linhas do `_DF` são únicas por combinação de atributos; é microdado de saúde.
4. **TTE por seção** (`transf_temporaria_secao`): origem, destino e tipo (preso provisório, militar); células com 1 eleitor (INFERÊNCIA, não medido).
5. **Candidatos**:
   - A tríade nome, data de nascimento e município de nascimento é praticamente única; mais CPF e título, vira chave para fraude de identidade (FATO sobre o conteúdo, INFERÊNCIA sobre o uso).
   - Combinação UF, cargo, partido, raça/cor e gênero: das 6.391 classes, 3.071 (48%) têm um único candidato ([amostra] no BRASIL). Isso não é problema porque candidatos são públicos pelo nome, mas indica que raça/cor e gênero ligados a uma pessoa nomeada não protegem ninguém. A atenção deve ir para quem republica.
   - `bem_candidato` + `NM_MUNICIPIO_NASCIMENTO` + `DS_BEM_CANDIDATO` (texto livre) podem localizar bens e residência.
6. **Cruzamentos com bases externas**: CPF real do candidato liga a Receita, redes sociais, vazamentos. Por isso a decisão de descartar na silver.
7. **Efeito de agregação por tempo**: `historico_candidatura` cobre 2004 a 2026; candidato com candidatura indeferida em 2008 continua ligado ao nome em 2026.

Regra mínima sugerida para a gold (INFERÊNCIA, k escolhido por mim, ajustável): suprimir ou agrupar células de contagem < 5 em qualquer dataset de perfil do eleitorado, comparecimento, TTE e deficiência; agrupar acima de município (sem zona/seção) para qualquer cruzamento de três ou mais atributos sensíveis.

## 6. Decisão recomendada de escopo

Base normativa (norma, não reconsultada online): LGPD art. 7º §3º (dados pessoais de acesso público têm o tratamento condicionado à finalidade, boa-fé e interesse público que justificaram a disponibilização), art. 7º §4º, art. 5º II e art. 11 (dados sensíveis), art. 12 (anonimização); Res. TSE 23.609/2019 art. 33 §2º (transcrita no leiame de `consulta_cand`).

| Dataset | Decisão | Condições |
|---|---|---|
| `codigos-oficiais-de-uf-e-municipios-...` | **Liberado** | Nenhuma. |
| `resultados-2026` | **Liberado** | `NM_SOCIAL_CANDIDATO` descartado. Em `votacao_secao`, avisar do risco de seção pequena e não publicar cruzamento com perfil da seção. |
| `candidatos-2026` | **Liberado com condições** | (a) descartar `NR_CPF_CANDIDATO`, `NR_TITULO_ELEITORAL_CANDIDATO`, `DS_EMAIL`, `DT_NASCIMENTO`, `NR_PROCESSO`, `NM_SOCIAL_CANDIDATO`, `DS_BEM_CANDIDATO` (texto livre) e links de contato em `DS_URL` na silver; (b) a bronze fica só local; (c) cor/raça, etnia e quilombola só em agregado; (d) registrar no repositório a divergência entre o leiame e os dados e reportar ao TSE (estatistica@tse.jus.br); (e) finalidade declarada: transparência e análise eleitoral. |
| `comparecimento-e-abstencao-2026` | **Liberado com condições**, exceto o arquivo de deficiência | Perfil geral e TTE: supressão de células < 5 e sem cruzamento com raça/cor + identidade de gênero + quilombola/indígena no mesmo recorte. `perfil_comparecimento_abstencao_eleitor_deficiente`: **não liberado** (linha por eleitor com saúde e comparecimento). Reavaliar só como contagem agregada por município. |
| `eleitorado-2026` | **Liberado com condições**, exceto o arquivo de deficiência | `perfil_eleitorado`: supressão de células < 5, mesmas condições acima. `perfil_eleitor_deficiente`: **não liberado** no nível atual (uma linha por eleitor, seção e atributos; 99,3% únicos). Reavaliar como contagem por município e tipo de deficiência com supressão. |

Se o dono do projeto quiser liberar os dois arquivos de deficiência como estão, isso precisa ser uma decisão explícita e registrada, com análise do art. 11 da LGPD. Esta auditoria não recomenda.

Implicação para a configuração: o dataset `eleitorado-2026` e o `comparecimento-e-abstencao-2026` estão habilitados por inteiro. Para aplicar a decisão acima será preciso uma lista de arquivos excluídos (os dois de deficiência), o que exige alteração de `config/elections/2026.yaml` ou do código de descoberta. Não alterei esses arquivos.

## 7. Fora do escopo atual (só pelos leiames e nomes de arquivo)

Não habilitados em `config/elections/2026.yaml`. Classificação conforme os leiames e cabeçalhos; arquivos grandes não foram baixados.

| Dataset | Dados pessoais | Observação |
|---|---|---|
| `certidao_criminal_<UF>` | **D/S**: PDFs de certidão criminal de candidatos (antecedentes) | O ZIP do AC tem 1.711 PDFs (FATO, listagem). Documento pessoal; dado de condenação é de alta sensibilidade. Não habilitar. Não li o conteúdo. |
| `proposta_governo_<UF>` | N/Q | PDFs de plano de governo. Podem conter contatos. Não habilitar sem varredura. |
| `fotos` (`foto_cand2026_<UF>_div.zip`) | **Q/S**: imagem facial de candidato | Imagem facial é dado biométrico em potencial; INFERÊNCIA: sensível se usada para reconhecimento. Não habilitar sem finalidade. |
| `eleitorado_local_votacao` | Q: endereço, bairro, CEP, `NR_TELEFONE_LOCAL`, latitude e longitude do local de votação; contagens por seção | Dados institucionais (escola, prédio público), não de pessoa. Leiame e cabeçalho lidos. Cuidado com `QT_ELEITOR_SECAO` pequena. |
| `perfil_eleitor_secao_<UF>` | S/Q: perfil por seção com raça/cor, identidade de gênero, quilombola | Só `_AC` perfilado (50.000 linhas). Mesma regra de supressão. Seção pequena é arriscada. |
| `transferencia_temporaria`, `transf_temporaria_secao` | Q/S: contagens de transferência por tipo | Cabeçalho lido. Agregado; seção com contagem 1. |
| `relatorio_resultado_totalizacao_<UF>` | N | Relatório PDF de totalização. Só o nome do arquivo; leiame não lido. |
| Prestação de contas de campanha | INFERÊNCIA, não verificada | Não aparece no inventário de 2026 deste repositório; não li nenhum leiame. Por conhecimento geral, costuma ter CPF/CNPJ de doadores e fornecedores, o que exigiria auditoria própria. |
| Boletim de urna | INFERÊNCIA, não verificada | Idem. É por seção (votos), com o mesmo risco de seção pequena. |

## 8. Limites desta auditoria

- Os ZIPs de 2026 grandes foram lidos por trecho (leitura em streaming, primeiras 50.000 a 300.000 linhas do primeiro CSV relevante). Padrões de mascaramento valem para o que foi lido. Candidatos foi lido por inteiro apenas no arquivo BRASIL.
- A classificação de "sensível" para identidade de gênero, intérprete de Libras e tipo de transferência (preso provisório) é interpretação conservadora minha da LGPD art. 5º II; não é uma lista oficial.
- Dígito verificador válido não prova que o CPF ou o título seja de uma pessoa real.
- Regex em texto livre dá estimativa, com falsos positivos e negativos.
- Normas citadas pelo conhecimento do autor, exceto a transcrição no leiame.
- Os leiames em PDF foram convertidos com `pdftotext -layout` e guardados em `data/leiames/<dataset>/` (ignorado pelo git).
- Durante a extração de leiames, o script que usei extraiu também todos os PDFs do ZIP de certidão criminal do AC e do de proposta de governo do AC e do de relatório de totalização do AC para `data/leiames/`; apaguei esses diretórios sem ler o conteúdo.
