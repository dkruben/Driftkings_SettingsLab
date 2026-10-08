# Fase 10.3 — estado parcial, gate humano pendente

Atualização posterior: o gate anterior foi confirmado NO_ALERT, a instrumentação
Unicode foi corrigida e receipt-l2-v2b obteve PASS + NO_ALERT. Ver
`docs/WINDOWS_FILES_V2B.md`. O restante deste documento descreve o estado histórico
da primeira tentativa; os artefactos dessa tentativa permanecem intactos.

## Entrega e estado

1. Auditoria anterior à edição: `docs/windows-files-audit.md`.
2. Causa operacional: L2 antigo reproduziu interrupção com vários PowerShell
   EncodedCommand, sem PJOrion, e confirmação ATD. Não se conhece o limiar/regra.
3. Desenho: helper próprio WindowsFiles.cs com duas operações fixas de IPC.
4. Razão: Python 2.7 sem _ctypes não oferece as garantias Win32 necessárias;
   não foi comprovada alternativa equivalente no runtime WoT.
5. Ficheiros desta correção: source/updater/WindowsFiles.cs;
   source/scripts/client/Driftkings/core/updater/windows_files.py e __init__.py;
   build_tools/build_windows_files.py, build_lab.py e build_unified.py;
   build_tools/tests/test_windows_files_v2.py;
   build_tools/windows_files_v2_hg.py e windows_files_v2_probe.py;
   docs/windows-files-audit.md e este relatório. Alterações anteriores de outras
   fases permanecem separadas; nenhuma publicação/deployment foi executada.
6. PowerShell removido do backend safe_path e replace_receipt. Sem cmd/shell.
7. Helper novo, mínimo e offline, separado do Installer.cs, compilado localmente.
   SHA-256 compilado: 8fb6ecc64c05ec1c8ddff4eaa7cfc463d24e5cbe33bd95aa6bc6f245a3a1afd0.
8. Protocolo: READY/1; V/path; R/source/target. Paths são dados UTF-8/base64,
   argumentos fixos, root local, mensagens limitadas, timeouts, fail closed.
   Um processo por sessão; pipe bloqueante, requests serializados, sem polling.
9. Reparse: GetFileAttributesW verifica cada ancestral e leaf; qualquer bit
   FILE_ATTRIBUTE_REPARSE_POINT bloqueia. Handles de ancestrais durante operação.
10. Replace: notice-* → notified.json no mesmo download-* local; flush/close;
    ReplaceFileW sem backup, como anteriormente. Sem copy/truncate fallback.
11. Win32: 12 testes passaram, zero skips. Arquivos/diretórios normais, Unicode,
    espaços, mixed separators, case insensitive, paths ausentes, junction real,
    symlinks reais, traversal/UNC/device/ADS/root escapes, ACL denied real,
    readonly/locked target, hash/ausência do helper, atomic success/failures.
    Comando: python -m unittest discover -s build_tools/tests -p test_windows_files_v2.py
12. Python 2.7: Hg iniciou em 2.7.15 x86; o diagnóstico falhou antes de testar
    o backend. Compatibilidade completa dos runtimes/bytecode/_ctypes pendente.
13. receipt-l2-v2: uma tentativa, marker exclusivo e preservado sob
    build/diagnostics/windows-files-v2/receipt-l2-v2. Resultado técnico:
    ABNORMAL_TERMINATION, exit=255, sem operation-completed.json. Erro conhecido
    do próprio diagnóstico: UnicodeDecodeError ao serializar chave de path mbcs
    da fixture em json.dumps. Nenhum safe_path nem helper foi lançado.
    Janela Lisboa: 09/10/2026 00:02:13.258523–00:02:13.729622.
    Python launcher PID 3776 → Hg PID 28828; zero PowerShell, zero cmd,
    zero helper, source/resource hashes inalterados durante a tentativa.
14. Bitdefender: UNKNOWN, confirmação humana solicitada; não assumir NO_ALERT.
15. Teste original: não executado; depende de L2-v2 PASS + NO_ALERT.
16. Suite source/updater: não executada; depende dos dois gates explícitos.
17. Fase 10 permanece FROZEN. Não executar PJOrion/release, tag ou publicar.
18. Limitações: gate AV, correção do diagnóstico Unicode com marker novo,
    compatibilidade/regressões ainda pendentes e limites de bootstrap/ReplaceFileW
    descritos na auditoria. Não declarar ausência de perda de segurança nem
    PASS global antes da resolução e validação desses pontos.

## Próximo passo autorizado, após resposta ao gate

Se ALERT, parar e preservar detalhes. Se UNKNOWN, manter a validação pendente.
Se NO_ALERT, corrigir a serialização mbcs→Unicode do próprio diagnóstico e
preparar uma tentativa com nome/marker novos, sem apagar/reutilizar receipt-l2-v2.
Um novo PASS técnico ainda exige nova confirmação AV antes do teste original.
Não repetir L2 antigo nem probe antigo. Não alterar o Bitdefender.
