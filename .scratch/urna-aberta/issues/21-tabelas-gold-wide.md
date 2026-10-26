# 21: Tabelas gold wide

**What to build:** Duas tabelas prontas para consulta direta, estáveis e documentadas: resultado por candidato e município, e perfil do candidato.

**Blocked by:** 13 (Fatos de votação e comparecimento), 19 (Candidatos 2026)

**Status:** ready-for-agent

- [ ] Nomes consistentes em snake_case, sem exposição de peculiaridades do TSE
- [ ] Contrato de colunas: só se adiciona, nunca se renomeia (mudança incompatível vira nova versão)
- [ ] Comentários de tabela e coluna persistidos no Unity Catalog, com unidade, domínio e granularidade
- [ ] Tags de domínio, granularidade e PII
- [ ] Testes de não-nulo, unicidade e valores aceitos
