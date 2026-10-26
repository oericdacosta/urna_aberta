# 06: Auditoria de PII nos leiames

**What to build:** Ler os leiames oficiais e classificar cada coluna dos datasets de 2026 como identificador direto, quase-identificador, sensível ou sem risco. Confirma se o CPF e o e-mail dos candidatos vêm mascarados em 2026.

**Blocked by:** 04 (Descoberta CKAN e configuração de 2026)

**Status:** ready-for-agent

- [ ] Tabela de classificação de colunas por dataset (direta / quase / sensível / nenhuma)
- [ ] Resposta registrada: o CPF de candidatos em 2026 vem real ou mascarado?
- [ ] Colunas que devem ser descartadas ou hasheadas na silver listadas
- [ ] Decisão registrada sobre quais datasets entram no escopo (candidatos e eleitorado liberados ou não)
