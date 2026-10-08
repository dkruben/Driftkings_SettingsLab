# Fase 10.3 — regression validation

**WINDOWSFILES_V2_REGRESSION = PASS. FASE 10.3 = PASS WITH OPEN HARDENING FINDING.**
O utilizador confirmou NO_ALERT para a janela 09/10/2026, 00:27:36–00:34:40,
hora de Lisboa. A Fase 10 fica descongelada para a etapa seguinte. PJOrion,
release, publicação, tags e deployment não foram executados nesta tarefa.

Todos os relatórios e logs desta regressão estão em build/windows-files-regression/.
O resumo legível por máquina é result.json; baseline.json regista commit,
branch, VERSION, working tree e hashes anteriores aos testes.

1. **Hashes pré-teste confirmados**: WindowsFiles.cs
   f8723f20839aa0fdfb25afc7ac7dee317af28d512087099906a154b7ce5b58f1;
   helper 8fb6ecc64c05ec1c8ddff4eaa7cfc463d24e5cbe33bd95aa6bc6f245a3a1afd0;
   windows_files.py 10c8a55da9ae0e4fa60b41f812dcaa03a576de7dccf593bedd8c9def60a408c2;
   Hg ac78054d2d998e22b872b4caa231009fcfff9da7793532cc8a5af8cbce4022d2.
   Branch main, commit 3c9a4639c3ffbd109f71b5637defb92ab9c96794,
   VERSION de trabalho 0.1.2-beta.1. Working tree já continha alterações de
   fases anteriores. Source funcional, incluindo todos os .py/.cs, permaneceu
   igual durante esta tarefa; nenhuma key i18n mudou.
2. **Runtimes**: Python 3.14 host; F:/Python27/python.exe 2.7.18 x64;
   SourceTree hg.exe 2.7.15 x86, hash verificado. Smokes novos de regressão normal,
   sem reutilizar resultados antigos como substituto.
3. **2.7.18**: source PASS, compiled PASS. Imports passivos, bootstrap/hash,
   READY/1, Unicode/espaços/missing/NUL inválido, replace real e Results reais,
   cleanup e EOF/exit=0. Cada contrato fez 20 V e 1 R numa sessão.
4. **2.7.15**: source PASS, compiled PASS, package debug PASS; mesmos contratos
   relevantes, uma sessão por execução, helper exit=0 e cleanup concluído.
5. **Compiled bytecode**: 16 módulos compilados em cada runtime, updater e
   parent packages. Payloads sem .py; todos os imports Driftkings verificados
   como .pyc dentro do payload próprio. Também executado o bytecode extraído
   diretamente do WOTMOD debug e os recursos/helper desse package, no Hg.
6. **No-_ctypes**: todos os cinco smokes bloqueiam imports de ctypes e _ctypes,
   provam o bloqueio e continuam a executar helper, Results.scan/acknowledge e
   replacement. ctypes só é usado no host para criar fixtures Win32 de teste.
7. **Path security**: 15/15 PASS, zero skips. Windows real: symlink/junction/
   ancestor junction, ACL denied, readonly/locked, arquivos/diretórios, Unicode,
   espaços, mixed separators/case, missing, UNC/device/traversal/ADS/root escape,
   helper missing/hash, handshake inválido, timeout e EOF. Timeout usa falha
   injetada no receive queue com helper real, verifica kill/no retry; EOF vem
   de terminar o helper real. Nenhum skip silencioso de Win32 obrigatório.
8. **Results**: 14/14, ticket/manifest/result, statuses installed/rolledBack/
   cancelled/failed, dedup, notified.json e falha de replacement. Fixture antiga
   de junction passou de PowerShell a Win32 real. Não se alteraram assertions
   de resultados nem semântica funcional para obter PASS.
9. **Installer**: 36/36, incluindo transações nativas, READY/resume, identidade,
   version/size/hash, recovery/backup/rollback/cancel/process/path segurança.
10. **UpdaterService**: test_updater 38/38, context 29/29, download 32/32,
    file_work 17/17 e smoke 12/12. Total específico updater: 178/178.
    O diagnóstico original não foi repetido: o método equivalente correu como
    parte da suite normal, com setup de recursos v2. O corpo do método original
    permanece exatamente igual ao HEAD, confirmado em verification.json.
11. **Gameface/UI**: nove suites JavaScript passaram: accounts, carousel layout/
    lifecycle/native, settings, dependencies, hangar updates, roster e ui_bridge.
    Tests Python de presenter/settings/lifecycle/restart/states também passaram
    na suite completa; UI funcional não foi alterada.
12. **Python/Flash**: nove componentes de contrato passaram, sem mudanças de
    contratos. Build debug mantém 33 componentes habilitados.
13. **i18n**: 12 catálogos validados, 35 secções por catálogo; os dois grupos
    adicionais de UI/sistema não são componentes de package. Todas as keys
    inglesas existem no catálogo resolvido; source i18n intacto. Smoke do build
    também validou defaults e UTF-8.
14. **Suite source completa**: total 745, PASS 744, FAIL 0, ERROR 0, SKIP 1.
    Skip explícito: test_windows_files_diagnostic_json.
    DiagnosticJsonTests.test_original_failure_reproduced_before_fix, exclusivo
    de Python 2. Esse caso passou no Python 2.7.15 (8/8 testes Unicode na etapa
    anterior). Baseline anterior da Fase 10: 722; acréscimo de 15 testes Win32
    e oito testes de diagnóstico Unicode = 745. Nenhum Win32 obrigatório skip.
    Tests de limites PJOrion na suite usam mocks/fixtures, não executam a ferramenta.
15. **Build debug**: python -B build_tools/build_lab.py --no-obfuscation,
    exit=0, sem --release/--flash. Scripts foram inspecionados: outputs locais
    build/; leitura da instalação só para gerar o bridge existente de Carousel.
    Não houve instalação/publicação. Helpers, UI declarations, bytecode, assets
    e presets locais gerados pelo fluxo normal.
16. **Package inspection**: build/unified/Driftkings.wotmod, 396 entradas,
    247 .pyc Python 2.7, 50 assets Gameface, entry point único mod_Driftkings.pyc,
    identity driftkings.unified, version 0.1.2-beta.1, CRC PASS. SWF preexistente
    preservado. Nenhum .py, .ps1/.cmd/.bat ou recurso PowerShell no package.
    SHA-256 WOTMOD debug:
    e2e2c0e05767f4af6372d5c6fd60247c13c9070b2187e879a8e832dc0f200987.
    Package é debug sem ofuscação: não é uma beta/release publicável.
17. **Static search**: zero ocorrências/dependências do mecanismo removido em
    source/scripts/client e source/updater, para powershell.exe, EncodedCommand,
    cmd.exe e shell=True. Quatro ocorrências build_tools classificadas: uma
    flag de observação EncodedCommand no diagnóstico histórico e três strings
    cmd.exe usadas para contar/proibir processos nos runners. Nenhuma é execução.
    Processos observados nas suites Windows/updater/source: zero PowerShell,
    zero cmd e zero shell=True. Nenhum probe adicional/histórico foi executado.
18. **Git diff --check**: PASS, exit=0. Avisos CRLF→LF/LF→CRLF são avisos Git
    preexistentes, não erros de whitespace. build/, .pyc e caches são ignorados;
    logs/markers não foram adicionados ao índice. SWF modificado e ZIP removido
    já constavam da working tree e foram preservados. Nenhum commit/staging.
19. **Bitdefender**: NO_ALERT, confirmado explicitamente pelo utilizador após a
    regressão. Nenhuma configuração/exclusão/proteção AV foi alterada.
20. **Bootstrap**: OPEN SECURITY HARDENING. Primeira extração antecede a
    validação nativa completa dos ancestrais. Não resolvido nesta regressão,
    sem nova regressão funcional. Proposta separada em WINDOWS_FILES_V2B.md.
21. **ReplaceFileW**: sem backup há limitações documentadas em erros raros;
    nenhum fallback destrutivo e nenhuma promessa de rollback universal.
22. **Decisão**: PASS WITH OPEN HARDENING FINDING; Fase 10 descongelada para
    a próxima etapa. Este resultado não executa PJOrion/release/publicação.

## Recompilação dos helpers no build debug

O build normal recompilou WindowsFiles.cs, sem editar o source. O timestamp PE
mudou de 1791500303 para 1791502367; 42 bytes do binário mudaram. O SHA passou
de 8fb6…afd0 (pré-teste) para
3677504a29de7895b61a8d66204105d5f879a0e98c9728b46084aff739ed2893 (debug).
Não tratar essa recompilação prevista como um hash funcional pré-teste divergente.
Os três outputs build/windows-files/{exe,helper.json,build-report.json} são as
únicas divergências da baseline; source hash mantém-se idêntico. O novo binário
foi validado contra metadata/build-report e executado a partir do package real.
As cópias verificadas do helper antigo nos diagnósticos permanecem preservadas.

Installer debug: 19968 bytes,
8b3f55eaf8de63c7216943a9238957c0738103ad309e9098ea950c71b318e65e.
WindowsFiles debug: 11264 bytes. Os hashes de ambos coincidem no package e
build local, e os reports correspondem ao source compilado. O WOTMOD anterior
de build/release permaneceu intacto.

## Ajustes limitados ao suporte de testes

Adicionados windows_files_test_support.py e runners windows_files_regression_*.py.
test_updater_results e test_updater_smoke receberam setup/teardown do recurso
local; o teste de replacement failure injeta erro na API replace_receipt em vez
da antiga run(script), removida. Mantém o assert de receipt anterior intacto.
test_windows_files_v2 recebeu três testes de transporte e removeu o skip de
privilégio de symlink: a cobertura obrigatória tem de executar ou falhar.

Não ocultar os erros de preparação do harness: no primeiro runner Hg faltava
argparse (movido para o CLI fora do import); a verificação de origem comparava
separadores mistos (normalizada); o wrapper Popen como função impedia subclass
de asyncio (trocado por subclass observacional); a suite normal não tinha ROOT
em sys.path (adicionado); o primeiro inspector usava chave POSIX numa baseline
com separadores Windows (corrigido). A primeira execução source terminou com
305 PASS/1 ERROR de import do runner, e a primeira windows com 1 ERROR de import.
Esses logs/resultados estão preservados com sufixo harness-import-failure.
Os resultados finais acima provêm de execuções completas posteriores; nenhum
erro de produto foi corrigido/movido/ignorado para obter os resultados.

Os findings abertos ficam separados da validação funcional. A decisão de
hardening do primeiro bootstrap requer uma tarefa própria.
