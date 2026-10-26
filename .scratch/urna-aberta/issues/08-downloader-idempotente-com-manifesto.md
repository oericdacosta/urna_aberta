# 08: Downloader idempotente com manifesto

**What to build:** Baixar arquivos do TSE de forma confiável e sem repetição: detecta mudança, baixa em streaming com verificação de integridade e registra tudo em um manifesto.

**Blocked by:** 07 (Spike: UF do AC ponta a ponta)

**Status:** ready-for-agent

- [x] Segunda execução sem mudança no CDN não rebaixa nada
- [x] Download interrompido não deixa arquivo parcial e retoma na próxima execução
- [x] sha256, tamanho, ETag/Last-Modified e data ficam registrados no manifesto de ingestão
- [x] Hash diferente do registrado marca o arquivo como republicado
- [x] Testes simulam queda de rede no meio do stream
- [x] Download e descompactação em streaming para disco, sem carregar o arquivo inteiro em memória (o maior membro, a votação por seção de SP, tem 4,6 GiB)
- [x] O arquivo local é apagado depois do upload ao Volume (o total de CSV passa de 50 GiB e o disco do runner é limitado)

## Estado (2026-10-26)

Concluído. Verificado: 19 testes offline (incluindo queda de rede no meio do stream e retry), quebra deliberada do código em 4 pontos (todas pegas pelos testes), e execução real no Databricks com o Acre: `novo`, `inalterado` (sem baixar) e `republicado` (com hash e ETag alterados no manifesto). Streaming medido com o ZIP de SP (767 MB): 37 MB de pico de memória.

Limites conhecidos: sem retomada por byte (cada tentativa recomeça do zero, ver comentário em `download.py`); a tabela `ops.ingest_manifest` tem uma linha de teste do Acre; o upload ao Volume foi medido só com 7,6 MB.
