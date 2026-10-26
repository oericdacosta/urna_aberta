# 14: Reconciliação e golden do 1º turno

**What to build:** A prova de que os números estão certos: totais batem entre os arquivos do próprio TSE e com os relatórios oficiais de totalização do 1º turno.

**Blocked by:** 13 (Fatos de votação e comparecimento)

**Status:** ready-for-agent

- [ ] Soma por seção = por município = detalhe da apuração, com tolerância zero
- [ ] Comparecimento mais abstenção = aptos, e votos totais ≤ comparecimento ≤ aptos
- [ ] Soma dos municípios = UF = Brasil para presidente
- [ ] Totais oficiais de presidente (Brasil e UF; brancos, nulos, comparecimento, aptos) congelados como golden, com URL e data da coleta
- [ ] Divergências ficam registradas numa tabela de resultados de reconciliação, sem correção silenciosa
- [ ] Falha na reconciliação ou no golden bloqueia a publicação (P1)
