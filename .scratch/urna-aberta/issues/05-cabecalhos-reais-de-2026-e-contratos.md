# 05: Cabeçalhos reais de 2026 e contratos

**What to build:** Baixar amostras reais dos arquivos de 2026 e documentar o que de fato existe: encoding, separador, nulos, colunas. Cada dataset ganha um contrato de header que a ingestão vai usar para detectar mudanças.

**Blocked by:** 04 (Descoberta CKAN e configuração de 2026)

**Status:** ready-for-agent

- [x] Encoding e separador confirmados por dataset (nenhuma premissa sobre o formato segue como não verificada)
  - Verificado nas 23 famílias de CSV (ISO-8859-1, sem BOM, `;`, CRLF, texto entre aspas). Ressalva: cp1252 vs latin-1 não distinguível (sem bytes 0x80-0x9F na amostra); só turno 1 visto. Ver `docs/layouts.md`.
- [x] Lista real de colunas por dataset documentada
  - Cabeçalho lido em todos os CSVs de cada ZIP (idêntico entre UFs); listas em `config/contracts/*.yaml`.
- [x] Contrato de header versionado por dataset
  - 23 contratos (`contract_version: 1`), `src/urna_aberta/contracts.py` e `tests/test_contracts.py`. Não há contrato para PDFs/JPGs (relatórios, fotos, propostas, certidões).
- [x] Valores especiais (#NULO, #NE, -1, -3) catalogados com onde aparecem
  - Catálogo em `docs/layouts.md`, só da amostra (início dos arquivos; primeiros 24 MiB do 1o CSV de cada ZIP, 1 MiB dos demais). Significados são inferidos do pareamento código/descrição; `CD_FAIXA_ETARIA=-3` sem significado confirmado. Valores raros fora da amostra e turno 2 não cobertos.
- [x] Tamanhos reais atualizam a estimativa do inventário
  - Tamanhos comprimidos de `docs/fontes.md` não divergiram; acrescentado o tamanho descomprimido (~50 GiB de CSV, ~6,8 GiB de ZIP) e o achado de que `_BRASIL.csv` duplica as UFs. Ver `docs/layouts.md`.
