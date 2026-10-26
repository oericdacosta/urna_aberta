# Gate de viabilidade do Databricks Free Edition

Data de elaboração: 2026-10-26. Legenda de status:

- **verificado na doc**: lido na documentação oficial na data indicada.
- **verificado localmente**: executado nesta máquina, sem workspace.
- **verificado no workspace**: executado em 2026-10-26 contra o workspace Free Edition do projeto, com token pessoal (script local).
- **PENDENTE**: ainda não executado.

Os itens "verificado no workspace" vêm do log real do script; os PENDENTE ainda não foram executados.

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

## 4. Resultados no workspace

| Pergunta | Resultado | Status |
|---|---|---|
| 4.1 PAT permitido? | Sim. `current_user.me` retornou o usuário com o token pessoal (Settings > Developer > Access tokens). | verificado no workspace |
| 4.1 Service principal | Nenhum existe (lista vazia). Criar um não foi testado. Sem console de conta, o OIDC do GitHub não é opção: o PAT é o caminho. | verificado no workspace (criação: não testada) |
| 4.2 Catálogo próprio | **Por API/SQL: FALHA.** `InvalidState: Metastore storage root URL does not exist. Default Storage is enabled in your account. You can use the UI to create a new catalog using Default Storage`. **Pela interface** (Catalog > Create catalog, Default Storage): funcionou, e o catálogo `urna` passou a aparecer na lista. O catálogo padrão `workspace` não existe neste workspace; existem `analytics`, `raw` e os de sistema. | verificado no workspace |
| 4.2 Volumes | Criar o schema `urna.viabilidade` e o Volume gerenciado `raw`: OK. Upload do ZIP (2,5 MB) e do CSV pela Files API: OK. Listagem do Volume: OK. | verificado no workspace |
| 4.3 Cliente externo conecta ao SQL warehouse | O `databricks-sql-connector`, rodando fora do Databricks (esta máquina), leu o CSV do Volume: 92 linhas, igual às 92 do CSV de origem (conferido separadamente). Falta repetir no runner do GitHub. | verificado no workspace (runner do GitHub: PENDENTE) |
| 4.4 Databricks alcança `cdn.tse.jus.br`? | Sim: HEAD retornou 200, executado num notebook serverless. | verificado no workspace |
| 4.5 Valor da cota diária e limite de armazenamento | Não publicados na doc e ainda não observados. Observar na UI e após cargas maiores. | PENDENTE |
| 4.6 Workflow no GitHub (ZIP -> Volume -> SELECT conta linhas) | Os secrets já estão cadastrados; falta o push e disparar `viabilidade`. | PENDENTE |

O script reporta FALHA na sonda "criar catalogo proprio": é o resultado esperado e documentado acima, não um defeito.
O catálogo, schema e Volume padrão do script são `urna`, `viabilidade` e `raw`, sobrescrevíveis por
`DATABRICKS_CATALOG`, `DATABRICKS_SCHEMA`, `DATABRICKS_VOLUME` e `DATABRICKS_WAREHOUSE_ID`.

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

Decididas após os testes no workspace:

- Catálogo próprio `urna`, criado pela interface com Default Storage (a API recusa). Os schemas por camada vivem dentro dele.
- Autenticação por PAT de usuário. Não há service principal nem OIDC.
- O Databricks alcança o CDN (200), mas o download continua no runner: a lista de domínios confiáveis não é publicada e não vale depender dela.

Ainda em aberto: valor da cota diária e limite de armazenamento (4.5) e o teste a partir do runner do GitHub (4.3 e 4.6).
