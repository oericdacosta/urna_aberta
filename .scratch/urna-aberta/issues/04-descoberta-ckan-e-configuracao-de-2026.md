# 04: Descoberta CKAN e configuração de 2026

**What to build:** Uma CLI que consulta o CKAN do TSE, lista todos os recursos dos datasets habilitados em 2026 e mede o tamanho real de cada um via HEAD no CDN. A configuração da eleição é um YAML validado.

**Blocked by:** 01 (Esqueleto do repositório)

**Status:** ready-for-agent

- [ ] Um YAML de 2026 lista os datasets (resultados, comparecimento, candidatos, eleitorado, de-para TSE↔IBGE) com `id` CKAN explícito e flag de habilitado
- [ ] Validação rejeita campos desconhecidos
- [ ] A CLI gera um inventário de fontes com URL, tamanho e data de modificação de cada arquivo
- [ ] Testes unitários com respostas do CKAN simuladas cobrem recurso ausente e erro 5xx com retry
