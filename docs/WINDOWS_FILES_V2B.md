# Fase 10.3 — diagnóstico Unicode e receipt-l2-v2b

Estado em 09/10/2026: **WINDOWSFILES_V2_L2 = PASS**, técnico PASS + confirmação
humana NO_ALERT. A Fase 10 permanece FROZEN. O teste original, PJOrion, release,
beta, publicação e deployment não foram executados nesta tarefa.

1. Gate anterior: resposta explícita NO_ALERT para receipt-l2-v2, janela Lisboa
   09/10 às 00:02:13. Confirmação registada em
   build/diagnostics/windows-files-v2/gates/receipt-l2-v2-human.json. Os 11
   ficheiros do diretório anterior foram preservados byte a byte; nenhum marker,
   result ou attempt foi alterado/completado.
2. Causa: os.walk com root str no Python 2 devolvia path-á em bytes MBCS.
   json.dumps interpretava a chave str como UTF-8 e recusava o byte 0xE1.
3. Alteração exclusivamente diagnóstica: módulo
   build_tools/windows_files_diagnostic_json.py, função _to_json_unicode.
   unicode permanece igual; bytes Windows são descodificados estritamente em
   mbcs; dict keys/values e listas/tuplos são normalizados para o relatório.
   json_bytes emite UTF-8. A snapshot normaliza a chave relativa, e os logs e
   completion usam a mesma serialização. Nenhum path entregue ao updater é
   modificado. As wrappers adicionais apenas observam request/response/close.
4. Testes sem backend: test_windows_files_diagnostic_json.py cobre ASCII,
   espaços, acentos, português, separadores mistos, str MBCS, unicode e reproduz
   o erro original antes da correção. Python 2.7.15 x86 Hg: 8/8; Python 3: 7
   passaram + 1 skip para o erro específico de Python 2. Nenhum import Driftkings
   no runner Hg, nenhum safe_path/helper nestes testes. Resultado e hashes:
   build/diagnostics/windows-files-v2/unicode-tests/result.json.
5. Baseline: 444 ficheiros source/build/resources registados antes das edições;
   comparação adicional com hashes funcionais da tentativa anterior. Todos
   iguais antes/depois de L2-v2b. Build scripts relevantes não foram alterados.
   A construção AST da fixture/package é idêntica ao diagnóstico preservado,
   descontando o novo diretório da tentativa. SHA do template:
   dca5c12a884a35aff58f3ae1310c801d7ca16f7a7ef4254433c7bdb534f32cde.
6. Tentativa nova: build/diagnostics/windows-files-v2/receipt-l2-v2b/.
   Marker attempt.json criado com modo exclusivo antes do processo; o launcher
   recusa diretório existente, não admite force/retry/overwrite, exige gate
   anterior NO_ALERT, testes Unicode atuais e hashes intactos.
   Comando executado uma única vez:
   python -B build_tools/windows_files_v2_probe.py --attempt receipt-l2-v2b.
7. Árvore: Python 3 launcher PID 27692 → hg.exe/Python 2.7.15 x86 PID 4348 →
   Driftkings.WindowsFiles.exe PID 21104. Horário Lisboa:
   00:17:17.877028–00:17:20.496237. argv e parent PIDs preservados em launch.json
   e process-events.jsonl. Hg exit=0; helper exit=0 após EOF normal do stdin.
8. Handshake observado: READY\t1, exatamente uma resposta. Hash do recurso e
   ficheiro extraído verificado pelo cliente/helper; binário sem recompilação.
9. Pedidos: V=8, R=0. Sete OK/V; um ERR/1001 para o NUL deliberadamente inválido.
   Cache, download-dir, ticket, manifest, result, ready ausente e Unicode
   validados. Nenhum WinError inesperado, zero WinError 5, zero timeout,
   zero EOF prematuro. Não houve acknowledgement/replace neste nível.
10. Cadeia instrumentada: zero powershell.exe, zero cmd.exe, um helper reutilizado.
11. Resultado técnico PASS: operation-completed.json e result.json presentes;
    Results.scan termina installed/error=None. Fixture hashes/metadata iguais
    antes e depois. Nenhuma leitura/instalação na instalação WoT.
12. Segundo gate: perguntado após a tentativa, respondido NO_ALERT pelo
    utilizador. Registo externo gates/receipt-l2-v2b-human.json; classificação
    agregada em build/diagnostics/windows-files-v2/l2-gate-result.json.
13. Fase 10 permanece FROZEN. O PASS é deste nível, não da Fase 10.3 completa.
    git diff --check passou; avisos de conversão CRLF em alterações anteriores
    não são erros do check. Não foi executada uma suite funcional/regressão.
14. Bootstrap pre-write: proposta abaixo; nenhuma alteração funcional nesta etapa.
15. ReplaceFileW: permanece sem fallback destrutivo; não garante rollback
    universal nos erros raros da API, conforme auditoria e documentação oficial.

## Hashes funcionais confirmados antes e depois

| Ficheiro | SHA-256 |
| --- | --- |
| source/updater/WindowsFiles.cs | f8723f20839aa0fdfb25afc7ac7dee317af28d512087099906a154b7ce5b58f1 |
| build/windows-files/Driftkings.WindowsFiles.exe | 8fb6ecc64c05ec1c8ddff4eaa7cfc463d24e5cbe33bd95aa6bc6f245a3a1afd0 |
| source/scripts/client/Driftkings/core/updater/windows_files.py | 10c8a55da9ae0e4fa60b41f812dcaa03a576de7dccf593bedd8c9def60a408c2 |
| hg.exe | ac78054d2d998e22b872b4caa231009fcfff9da7793532cc8a5af8cbce4022d2 |

Os hashes completos de updater/build estão em unicode-baseline.json e no
attempt.json novo, dentro de build/diagnostics/windows-files-v2/. Os ficheiros
alterados/adicionados nesta etapa são apenas os três diagnósticos
windows_files_v2_hg.py, windows_files_v2_probe.py, windows_files_diagnostic_json.py,
o runner windows_files_unicode_hg.py, o teste de serialização e documentação.

## Proposta de redução da janela de bootstrap

O problema permanece: a primeira extração escreve antes da validação nativa dos
ancestrais. A identidade dos bytes não prova a localização física de destino.
O startup posterior recusa reparse, mas não desfaz uma escrita redirecionada.

| Opção | Avaliação |
| --- | --- |
| A: verificações Python anteriores à escrita + confirmação nativa posterior | Reduz erros comuns: root local, limites, symlinks que o runtime detete, cache inválida. Não garante junctions no Python 2.7/WoT sem atributos Win32; mantém a janela e não basta como resolução. |
| B: extrair num diretório já confiável | Só é suficiente com confiança demonstrada no diretório e ancestrais. TEMP, LOCALAPPDATA ou um nome derivado do package/processo não bastam: continuam suscetíveis a reparse e races. ResMgr/package virtual não fornece diretamente um executável físico lançável. |
| C: criação nativa com handles e recusa de reparse antes da escrita | É a direção mais forte, mas exige uma capacidade nativa disponível antes da primeira extração. O helper extraído na própria cache ainda não resolve esse primeiro passo. Precisa de uma âncora de lançamento previamente instalada/verificada ou de uma capacidade nativa local comprovada no runtime. |

Proposta para etapa separada: primeiro demonstrar a âncora de confiança compatível
com WoT sem _ctypes; depois validar/abrir cada ancestral com handles, recusar
qualquer reparse, manter diretórios contra alterações durante criação exclusiva,
escrever/flush/verificar o hash por handle e só lançar a localização validada.
Para extrações posteriores, uma sessão nativa já confiável pode ajudar, mas
não substitui a prova da primeira extração. Não adicionar uma operação IPC de
escrita arbitrária: nomes/resource/hash/tamanho devem ser fixos e locais.

O significado de OPEN_REPARSE_POINT e o acesso a diretórios estão documentados
em [CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew).
Usar a flag apenas no leaf não comprova segurança de todos os ancestrais;
a estratégia requer validação e locks da cadeia e testes próprios.
Nada desta proposta foi implementado ou declarado resolvido nesta etapa.

## Limitações de ReplaceFileW

A [documentação oficial](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-replacefilew)
descreve efeitos parciais para erros 1176/1177 quando não há backup. Mantém-se
“substituição através de ReplaceFileW, sem fallback destrutivo, com limitações
documentadas da API”. O presente L2 só valida paths: não oferece nova evidência
de replacement/rollback. R=0 é intencional.

## Instruções preparadas para o teste original — não executadas

Após autorização explícita da próxima tarefa, criar um novo diagnóstico com
marker exclusivo e nome distinto, em build/diagnostics/windows-files-v2/.
Usar o Hg verificado com source limpo; inicializar o backend com os mesmos
recursos/helper verificados, restringindo as fixtures ao workspace. Selecionar
apenas UpdaterSmokeTests.test_post_restart_receipt_python27_windows_paths_and_deduplication
de build_tools/tests/test_updater_smoke.py, preservando os asserts e a semântica
original, incluindo os dois acknowledgements/deduplication e cleanup.
Não usar adapters em _package_matches ou em safe_path nesse teste original.

Antes de lançar: verificar hashes funcionais/helper, gates anteriores NO_ALERT,
fixture e runner aprovado. Registar todos os V/R, respostas/handshake, árvore,
argv, hash, timestamps e saída final. Exigir resultado final além de exit=0,
zero PowerShell/cmd e ausência de WinError 5/timeout/EOF prematuro. Após essa
tentativa parar para outro gate humano do Bitdefender; nenhum PJOrion/suite
completa/release antes das validações seguintes. Não existe comando de execução
novo para esse teste nesta entrega, para evitar iniciar uma etapa não autorizada.
