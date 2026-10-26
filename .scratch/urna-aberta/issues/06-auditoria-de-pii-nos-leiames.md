# 06: Auditoria de PII nos leiames

**What to build:** Ler os leiames oficiais e classificar cada coluna dos datasets de 2026 como identificador direto, quase-identificador, sensível ou sem risco. Confirma se o CPF e o e-mail dos candidatos vêm mascarados em 2026.

**Blocked by:** 04 (Descoberta CKAN e configuração de 2026)

**Status:** ready-for-agent

- [x] Tabela de classificação de colunas por dataset (direta / quase / sensível / nenhuma): `docs/pii.md` seção 2. Cobre os 5 datasets habilitados, coluna a coluna (metadados constantes agrupados). Fonte: leiames + amostras. Só `perfil_eleitor_secao` (fora do escopo) foi perfilado em um único estado (AC).
- [x] Resposta registrada: o CPF de candidatos em 2026 vem real ou mascarado? **Real** (21.014 de 21.017 linhas no `consulta_cand_2026_BRASIL.csv`, todas com dígito verificador válido; 3 mascaradas com `-4`). Título e data de nascimento também reais; e-mail 100% `NÃO DIVULGÁVEL`; não há coluna de endereço nem telefone. Contradiz o leiame (que diz "não divulgável"); em 2024 o CPF vinha mascarado. Ver `docs/pii.md` seção 1. Não verificado: se os CPFs pertencem a pessoas reais, e os 27 arquivos por UF individualmente (só SP, AC, BR).
- [x] Colunas que devem ser descartadas ou hasheadas na silver listadas: `docs/pii.md` seção 3.
- [x] Decisão registrada sobre quais datasets entram no escopo: `docs/pii.md` seção 6. Candidatos e eleitorado liberados com condições, exceto os dois arquivos de deficiência (não liberados: uma linha por eleitor, 99,3% únicos no DF). Aplicar a exclusão exige mudar a configuração de 2026 (não feito aqui). A decisão final é do dono do projeto; é uma recomendação.
