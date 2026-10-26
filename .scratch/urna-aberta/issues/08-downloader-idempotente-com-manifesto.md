# 08: Downloader idempotente com manifesto

**What to build:** Baixar arquivos do TSE de forma confiável e sem repetição: detecta mudança, baixa em streaming com verificação de integridade e registra tudo em um manifesto.

**Blocked by:** 07 (Spike: UF do AC ponta a ponta)

**Status:** ready-for-agent

- [ ] Segunda execução sem mudança no CDN não rebaixa nada
- [ ] Download interrompido não deixa arquivo parcial e retoma na próxima execução
- [ ] sha256, tamanho, ETag/Last-Modified e data ficam registrados no manifesto de ingestão
- [ ] Hash diferente do registrado marca o arquivo como republicado
- [ ] Testes simulam queda de rede no meio do stream
- [ ] Download e descompactação em streaming para disco, sem carregar o arquivo inteiro em memória (o maior membro, a votação por seção de SP, tem 4,6 GiB)
- [ ] O arquivo local é apagado depois do upload ao Volume (o total de CSV passa de 50 GiB e o disco do runner é limitado)
