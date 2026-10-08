# Fase 10.3 — original-smoke-v2

Em 09/10/2026, **WINDOWSFILES_V2_ORIGINAL_SMOKE = PASS**: resultado técnico PASS
e resposta humana explícita NO_ALERT. A Fase 10 permanece FROZEN; a Fase 10.3
ainda não está totalmente validada. Não foram executados regressão completa,
PJOrion, release, publicação ou deployment.

1. Hashes pré-teste e pós-teste coincidem. WindowsFiles.cs:
   f8723f20839aa0fdfb25afc7ac7dee317af28d512087099906a154b7ce5b58f1;
   helper: 8fb6ecc64c05ec1c8ddff4eaa7cfc463d24e5cbe33bd95aa6bc6f245a3a1afd0;
   windows_files.py: 10c8a55da9ae0e4fa60b41f812dcaa03a576de7dccf593bedd8c9def60a408c2.
   Foram também verificados os 444 ficheiros da baseline funcional e o source
   do teste original, SHA 208b67fd96d8a8c044521c8cbe601101569f5af31ee50d98374daa84d6fdd051.
2. Runtime: SourceTree hg.exe verificado,
   ac78054d2d998e22b872b4caa231009fcfff9da7793532cc8a5af8cbce4022d2,
   Python 2.7.15 x86. Runner carrega o módulo original e seleciona um método,
   sem alterar source/assertions/fixtures/order/cleanup. Nenhum outro teste corre.
3. Diretório novo build/diagnostics/windows-files-v2/original-smoke-v2/;
   attempt.json criado exclusivamente antes do lançamento. Script recusa pasta
   existente e não admite force/retry/overwrite. Uma tentativa executada:
   python -B build_tools/windows_files_original_probe.py --attempt original-smoke-v2.
   Os artefactos anteriores, incluindo L2-v2b, permanecem intactos.
4. Árvore observada: launcher Python 3 PID 18624 → Hg PID 27164 → helper
   WindowsFiles PID 20564. Janela Lisboa 00:22:33.663070–00:22:39.486096.
   argv, timestamps, executáveis e parents constam de attempt/launch/events.
5. Handshake READY\t1, exatamente uma sessão/helper, fecho normal pelo stdin.
6. Pedidos V=34, todos concluídos OK/V.
7. Pedidos R=1, concluído OK/R. Foram observadas 36 respostas incluindo READY.
8. Primeiro acknowledgement cria notified.json pelo write_new original; segundo
   acknowledgement substitui notice-gz1sra → notified.json no mesmo download-receipt.
   Source regular, target existente e sameDirectory observados; source consumido.
   SHA do temporary e target após substituição coincidem:
   0c310d694c6a3ce325b6f75fea3687c57a533c99817f886caab3e2aa526433ce.
   Target anterior:
   a4f265e0e30566a3afea5d10e4faeee10966abe035c0665ccfb25bfd9394386f.
   O código funcional verificado continua a fazer flush/fsync/close no caller;
   o helper verifica ancestrais/source/target, diretório/volume, regular file e
   readonly, repete flush(true)/close e chama ReplaceFileW. O OK/R só ocorre
   depois desse caminho real, sem copy/truncate/delete fallback. Nenhum adapter
   foi usado em scan, safe_path, _package_matches, replace_receipt ou acknowledge.
9. Deduplication: quatro scans devolveram [installed], [], [failed], [],
   intercalados com os dois acknowledgements originais. Após o segundo ack,
   notified.json corresponde ao fingerprint do resultado failed/installIOError
   válido para o ticket. Não houve alteração de algoritmos ou assertions.
10. PowerShell count=0 na cadeia instrumentada.
11. cmd count=0; shell=True count=0.
12. Exit codes: launcher=0 observado pela execução do comando; Hg=0;
    helper=0 registado após EOF do stdin. Zero timeout, EOF prematuro, erros
    inesperados de IPC ou WinError 5. operation-completed.json e result.json
    presentes; teste original executado=1, sucesso, sem skip.
13. Fixture original mantida em build/updater-tests/tmpi7m2g9. Snapshot inicial:
    ticket, manifest, package 1.0.0 e result installed/helperPid=123.
    Snapshot antes do cleanup: ticket/manifest/package inalterados, result
    failed/installIOError/helperPid=456 e notified.json com fingerprint final.
    Nenhum temporary notice-* sobrou. O finally original removeu a fixture;
    cleanupComplete=True. Snapshots/JSON/hashes estão no completion report.
14. Technical result=PASS; source funcional, teste e recursos intactos.
15. Gate solicitado após a tentativa; utilizador respondeu NO_ALERT.
    Registo externo gates/original-smoke-v2-human.json; decisão agregada
    build/diagnostics/windows-files-v2/original-gate-result.json.
16. Estado: original smoke validado; próxima etapa REGRESSION VALIDATION.
    Fase 10 FROZEN e Fase 10.3 global incompleta até validar os passos restantes.
17. Findings abertos: a primeira extração antecede a validação nativa completa
    dos ancestrais da cache; ReplaceFileW sem backup tem limitações documentadas
    nos erros raros, sem garantia universal de rollback. Não alterados nesta
    tarefa. Este teste original não cobre todos os ataques externos negativos
    nem todas as falhas Win32; manter a cobertura específica de path security
    e regressões separadas. Não declarar a segurança global resolvida.

Os únicos ficheiros de código adicionados nesta tarefa são os diagnósticos
build_tools/windows_files_original_hg.py e windows_files_original_probe.py.
Wrappers observacionais delegam os mesmos argumentos para as implementações
originais, registam os resultados e retornam os mesmos valores. A fixture
permanece na localização e no formato definidos pelo teste original.

## Próxima etapa preparada — não executada

A validação seguinte deverá executar Python 2.7.18 x64 smoke, smoke de bytecode
compilado, e os testes de updater/results/installer/recovery/path security.
Depois, suite source completa e git diff --check. Manter Python 2.7/WoT sem
_ctypes como requisito, os hashes e configurações preservados, os fixtures
dentro do workspace e os resultados por runtime explicitamente reportados.
Somente depois dessa revisão decidir se a Fase 10 pode ser descongelada.
Este PASS não autoriza PJOrion, release, beta ou publicação.

Análise de bootstrap e limites da API: docs/WINDOWS_FILES_V2B.md e
docs/windows-files-audit.md. A substituição continua através de ReplaceFileW,
sem fallback destrutivo, com as limitações documentadas da API.
