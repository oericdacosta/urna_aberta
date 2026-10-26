# Gate de viabilidade do Databricks Free Edition

Data de elaboração: 2026-10-26. Legenda de status:

- **verificado na doc**: lido na documentação oficial na data indicada.
- **verificado localmente**: executado nesta máquina, sem workspace.
- **PENDENTE (requer workspace)**: só se resolve com um workspace Free Edition e o workflow `viabilidade`.

Nada marcado como verificado depende de credenciais. Nenhum resultado de workspace foi inventado.

## 1. Caminho do dado

CDN do TSE -> runner do GitHub Actions -> Volume do Databricks (Files API) -> leitura por SQL warehouse.
O download roda no runner porque o egress do Databricks é restrito (ver 3.3).

Script: `scripts/viabilidade.py` (dependências inline PEP 723; `uv run scripts/viabilidade.py`).
Workflow: `.github/workflows/viabilidade.yml` (`workflow_dispatch`, `permissions: {}`, secrets
`DATABRICKS_HOST` e `DATABRICKS_TOKEN`). O script imprime OK/FALHA por sonda e nunca imprime o token.

## 2. Verificado localmente (CDN do TSE)

| Item | Resultado | Status |
|---|---|---|
| CKAN `package_show` de `resultados-2026` e `comparecimento-e-abstencao-2026` | `success: true`; o campo `size` dos recursos vem nulo, então o tamanho exige HEAD | verificado localmente |
| Menor recurso CSV (HEAD, 2026-10-26) | `detalhe_votacao_munzona_2026.zip`, 2.511.067 bytes. Os demais: `perfil_comparecimento_abstencao_eleitor_tte` 10,6 MB; `votacao_secao_2026_RR` 5,4 MB (menor UF); `votacao_partido_munzona` 22,9 MB; maiores chegam a 452 MB | verificado localmente |
| Cabeçalhos do HEAD | `HTTP/2 200`, `content-length: 2511067`, `etag: "2650db-65eac471f9365"`, `last-modified: Sun, 25 Oct 2026 15:58:00 GMT`, `accept-ranges: bytes`, `application/zip` | verificado localmente |
| Download completo | 2.511.067 bytes, igual ao `content-length`; ZIP válido com 28 CSVs por UF + `BR`/`BRASIL` + `leiame.pdf`; CSV em `;` e latin1 com aspas | verificado localmente |
| Membro usado no teste de leitura | `detalhe_votacao_munzona_2026_AC.csv` (27 KB), enviado ao Volume junto com o ZIP | verificado localmente (extração) |

URL: `https://cdn.tse.jus.br/estatistica/sead/odsele/detalhe_votacao_munzona/detalhe_votacao_munzona_2026.zip`.

Implicação: o `Last-Modified`/`ETag` do HEAD servem de chave de mudança para ingestão incremental.
O SQL não lê ZIP; por isso o ZIP é guardado como bruto e o CSV extraído no runner é o que se consulta.

## 3. Free Edition: documentação oficial

Fontes (lidas em 2026-10-26):

- https://docs.databricks.com/aws/en/getting-started/free-edition-limitations (atualizada em 2026-10-18)
- https://docs.databricks.com/aws/en/getting-started/free-edition (atualizada em 2026-09-11)
- https://docs.databricks.com/aws/en/volumes/volume-files

### 3.1 O que a doc afirma

| Item | O que diz a doc | Status |
|---|---|---|
| Compute | Somente serverless; sem configuração customizada | verificado na doc |
| SQL warehouse | Um warehouse, tamanho máximo 2X-Small | verificado na doc |
| Jobs | Máximo de 5 tarefas concorrentes por conta | verificado na doc |
| Cota diária | Existe uma cota ("fair usage"); ao exceder, o compute fica indisponível pelo resto do dia (em casos extremos, do mês); dados e configurações não são apagados. O valor numérico NÃO é publicado | verificado na doc (valor: PENDENTE) |
| Armazenamento | A doc não publica limite numérico. "Custom workspace storage locations" não são suportadas (só o armazenamento padrão) | verificado na doc (limite: PENDENTE) |
| Egress | "Outbound internet access is restricted to a limited set of trusted domains"; a lista não está nessas páginas | verificado na doc (alcance ao CDN: PENDENTE) |
| Conta | Um workspace e um metastore por conta; sem console de conta nem APIs de conta; sem SSO/SCIM; login por e-mail OTP, Google ou Microsoft; uso não comercial; sem SLA; contas inativas podem ser apagadas | verificado na doc |
| Volumes (Unity Catalog) | A doc de Volumes não restringe a Free Edition. Upload pela UI limitado a 5 GB; acima disso, SDK | verificado na doc (disponibilidade na Free: PENDENTE) |
| Armazenamento padrão incluído | "Your new workspace includes serverless compute and default storage" | verificado na doc |

### 3.2 Pontos que a doc não responde

A doc da Free Edition não menciona PAT, service principal nem criação de catálogo. A ausência de menção
não é prova de suporte. Isso exige teste no workspace (seção 4).

### 3.3 Decisão de desenho já justificada pela doc

Como o egress é restrito a "trusted domains", o download do TSE permanece no runner do Actions e o
Databricks só recebe o arquivo pelo Volume. Isso vale mesmo que o teste de egress passe (item 4.3).

## 4. PENDENTE (requer workspace)

| Pergunta | Como o script/workflow responde | Status |
|---|---|---|
| 4.1 PAT permitido? | Sonda "usuario (PAT valido)" (`current_user.me`) | PENDENTE (requer workspace) |
| 4.1 Service principal existe/pode ser criado? | Sonda "service principals" (lista). Criar um SP exige admin de workspace; pode ser testado também em Settings > Identity and access | PENDENTE (requer workspace) |
| 4.2 Dá para criar catálogo próprio? | Sonda "criar catalogo proprio" (cria e apaga `urna_viabilidade`); lista os catálogos visíveis | PENDENTE (requer workspace) |
| 4.2 Volumes disponíveis? | Sondas "criar schema", "criar volume", "upload zip/csv", "listar volume" | PENDENTE (requer workspace) |
| 4.3 Runner conecta ao SQL warehouse? | Sonda "SQL warehouse le o Volume" (`databricks-sql-connector` do runner) | PENDENTE (requer workspace) |
| 4.4 Databricks alcança `cdn.tse.jus.br`? | Não dá para testar por SQL. Rodar em um notebook serverless: `import urllib.request; print(urllib.request.urlopen(urllib.request.Request("https://cdn.tse.jus.br/estatistica/sead/odsele/detalhe_votacao_munzona/detalhe_votacao_munzona_2026.zip", method="HEAD"), timeout=30).status)` e registrar status ou erro | PENDENTE (requer workspace) |
| 4.5 Valor da cota diária e limite de armazenamento | Não publicados na doc; observar na UI do workspace e após cargas maiores | PENDENTE (requer workspace) |
| 4.6 Workflow ponta a ponta (ZIP -> Volume -> SELECT conta linhas) | Disparar `viabilidade` e anexar o log | PENDENTE (requer workspace) |

O catálogo e o schema padrão assumidos pelo script são `workspace` e `viabilidade`; sobrescrevíveis por
`DATABRICKS_CATALOG`, `DATABRICKS_SCHEMA`, `DATABRICKS_VOLUME` e `DATABRICKS_WAREHOUSE_ID`
(variáveis de ambiente; no workflow, acrescentar em `env:` se o padrão não servir).

## 5. Passos manuais para o usuário

1. Criar o workspace em https://www.databricks.com/learn/free-edition (e-mail OTP, Google ou Microsoft).
2. No workspace: Settings > Developer > Access tokens > Generate new token. Validade de 90 dias,
   comentário `urna-aberta-viabilidade`. Se a opção não existir, registrar isso aqui: é uma decisão de
   desenho (usar alternativa OAuth).
3. Copiar a URL do workspace (`https://dbc-xxxx.cloud.databricks.com`, sem barra final).
4. No GitHub: Settings > Secrets and variables > Actions > New repository secret: `DATABRICKS_HOST` e <!-- pragma: allowlist secret -->
   `DATABRICKS_TOKEN`.
5. Em Actions > viabilidade > Run workflow. Alternativa local:
   `DATABRICKS_HOST=... DATABRICKS_TOKEN=... uv run scripts/viabilidade.py`.
6. Rodar a sonda de egress (4.4) em um notebook do workspace.
7. Anotar neste documento cada resultado (OK/FALHA e mensagem) trocando PENDENTE pelo resultado, e
   registrar na seção 6 qualquer decisão que mude o desenho.
8. Se o SQL warehouse estiver parado, iniciá-lo antes do workflow (o primeiro `connect` pode demorar).

## 6. Decisões que mudam o desenho

Registradas apenas as já sustentadas por evidência:

- Download no runner, envio por Files API ao Volume (3.3).
- Guardar o ZIP bruto e consultar o CSV extraído; o SQL não lê ZIP (seção 2).
- Cargas fatiadas por arquivo e retomáveis, por causa da cota diária e do warehouse 2X-Small (3.1).

A preencher após o teste: catálogo próprio ou schema por ambiente no catálogo padrão; PAT ou alternativa;
service principal ou PAT de usuário.
