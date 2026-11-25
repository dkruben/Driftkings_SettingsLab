# Fase 3C — Native Hangar Marks PoC

Baseline: `57881e7b1b099191c4a286fbb842cf2954646c0b`, CT 2.4.2.0 #995, fontes 2.4.2.5516.

**FASE 3C CONCLUÍDA E VALIDADA no CT 2.4.2.0 Common Test #995, no âmbito funcional confirmado pelo autor.** Auditoria final, testes, integridade da build e rollback aprovados. Encerramento em commit local `feat(gameface): add native hangar marks plugin`, sem push. Fase 3D não iniciada. Checkpoints anteriores mantêm o estado histórico.

## Auditoria final e encerramento — 2026-11-09

Estado inicial: branch `feature/wot-2.4.2-ct`, HEAD `57881e7b1b099191c4a286fbb842cf2954646c0b`, 18 ficheiros alterados/novos da Fase 3C e staging vazio. Nenhuma alteração alheia identificada. Worktrees preservados. Nesta auditoria não foi alterado código, regenerada build, instalado pacote ou iniciado o cliente; apenas documentação de encerramento atualizada, incluindo CT_COMPATIBILITY.

### Sessão CT e evidências

`C:/Games/World_of_Tanks_CT/game.log`: 887 linhas, SHA-256 `291a3f80d8816e1eb6ac54b96f526b16bc4e5868daae52f9c715f75af1269c91`. Sessão de 2026-11-09, início 11:02:53, após instalação concluída às 11:02:01 UTC; encerramento do cliente registado às 11:09:32.805. Header binário 2.4.2.1571 #2654956; metadata Driftkings identifica explicitamente CT 2.4.2.0 Common Test #995 e mod 0.1.8-beta.2. O cliente está encerrado.

- Linha 360, 11:03:22.698: Startup complete, 35 componentes, 13 serviços active, `failures=[]`, `disabled={}`.
- Linhas 539, 709 e 757: três RandomHangar distintos, uniqueID 26, 110 e 168.
- Linhas 542/543 (11:03:47.650), 711/712 (11:04:47.598/599), 759/760 (11:09:08.158): registo Python do relógio e marcas, ambos com `OpenWG injection not requested`.
- Linhas 806/807: encerramento da apresentação e diagnóstico dos marcadores; não constituem telemetria de destroy dos plugins de garagem.
- Linha 884: CAT Client was deinitialized. Há encerramento da sessão; não há telemetria individual JS de descarte.

Não foram encontrados Traceback, importações falhadas, erros Wulf ou marcadores de falha dos dois plugins, unhandledrejection/UnhandledPromiseRejection/PromiseRejection, loadPlugin, colisão, timeout, renderer failed ou Cannot dispose UI owner. Os quatro ERROR observados, linhas 297–300, referem-se às partículas BZ-75 já conhecidas. Existem avisos C++ de texturas e um DeviceCallback MouseCursor no encerramento; não são evidência de fuga dos plugins e não foram corrigidos nem atribuídos à Fase 3C.

Os marcadores JS `Hangar marks renderer loaded by native plugin` e `Clock started by native` não aparecem neste log. Alias numéricos, URLs, identidades SDK, fábrica, init e destroy não estão expostos nesta telemetria. A ordem dos registos Python não prova ordem de execução JS. O log prova registo backend e três entradas no hangar, não prova sozinho três ciclos completos ou descarte independente. Operação visual e ciclos são confirmados pelo autor; transporte exclusivo, identidade e ownership são fundamentados adicionalmente no código, pacote e testes.

### Confirmação funcional e classificação

Além do funcionamento geral e da ativação/desativação já confirmados, o autor respondeu “sim” à pergunta final sobre: relógio e marcas simultaneamente, hidePrestige, troca repetida de veículos com atualização, três ciclos garagem → batalha/replay → garagem sem duplicações e launcher funcional. Esta confirmação satisfaz os cenários essenciais de coexistência/transição exigidos para o commit. Não se inventam contagens de batalhas no log ou confirmações individuais de todas as escalas/resoluções.

| Critério | Estado | Fonte/limite |
|---|---|---|
| Marcas visíveis e ativar/desativar | PASS | Confirmação do autor |
| Valores e percentagens | PASS automático; funcionamento geral confirmado | Testes do renderer real em DOM simulado; sem declaração visual individual de cada valor |
| Gráfico e etiquetas | PASS automático/preservação | Teste existente de marcas, corpo visual preservado; aspeto geral aprovado pelo autor |
| Posicionamento | PASS automático/preservação | Teste da coluna nativa/fallback; funcionamento geral aprovado |
| Escala | PASS de preservação; PENDENTE matriz visual específica | HTML/CSS preservados; não foi declarada verificação isolada em múltiplas escalas |
| Mudança repetida de veículos e atualização | PASS | Confirmação explícita do autor + teste de alteração de payload |
| Reentrada e ausência de duplicações | PASS | Confirmação dos três ciclos; log mostra três carregamentos do hangar |
| Relógio visível/operacional e sem regressões | PASS | Confirmação de coexistência + regressão automática do relógio original |
| hidePrestige | PASS | Confirmação explícita + teste do renderer original |
| Relógio sem duplicações | PASS | Confirmação dos ciclos sem duplicação + testes |
| Dois plugins e identidades distintas | PASS | Registos Python, catálogo, identidade SDK e testes; execução JS não instrumentada no log |
| Nenhuma falha de carregamento/ownership identificada | PASS no âmbito auditado | Código, testes e ausência de diagnósticos relevantes; não equivale a observação de todo o JS |
| Outros 18 consumidores OpenWG preservados | PASS | Comparação do catálogo com baseline e testes de bootstrap/transporte |
| Launcher funcional | PASS | Confirmação explícita do autor + teste frontend |
| Três ciclos garagem/batalha ou replay | PASS | Confirmação explícita do autor; não deduzido apenas do log |
| Ausência de erros novos relevantes identificados | PASS no âmbito auditado | Log e confirmação do autor, ressalvados avisos C++ não atribuídos |
| Telemetria JS direta de init/destroy e medições de memória | PENDENTE / não realizada | Não exigida como prova única do funcionamento; sem alegação de ausência absoluta de fugas |

### Revisão, testes repetidos e build

Review do diff e dos oito ficheiros novos: alteração limitada às marcas da garagem, testes, inventário/lint e documentação. `gameface/core.py`, relógio inteiro, launcher, cálculos de marcas, HTML/CSS, kit partilhado, marcas de batalha/árvore, perfis e contratos das dependências permanecem sem diff. Comparação AST do catálogo: só DriftkingsMarksOnGunHangar muda, mantendo 22 entradas (2 próprias, 2 nativas, 18 OpenWG). Erros permanecem observáveis por estado failed, diagnóstico e recursos pendentes; falhas recuperáveis não são declaradas renderer ready. Nenhum defeito bloqueante identificado; nenhum código corrigido nesta revisão.

Novas execuções nesta auditoria: `python -B tests/run_python.py --suite all` — 860 PASS; `F:/Python27/python.exe -B tests/run_python.py --suite runtime` — 673 PASS; `npm --prefix build_tools/javascript test` — 23 suites PASS; lint PASS; testes de artefactos — 4 PASS. validate_build_data, validate_locales, generate_defaults --check, check_undefined_names e diff --check PASS. As mensagens esperadas de fault injection nos testes não são falhas da sessão CT.

Build local e instalada: 13 584 784 bytes, SHA-256 `09b70a3b4a48194514393fa1f7cae1b7281a42434d1cbae9b78ce064cf4c9bec`; comparação integral dos conteúdos das 624 entradas idêntica. Entry point, renderer, relógio, bootstrap e HTML/CSS incluídos; nenhum res/gui/gameface/js/index.js global. Backup de instalação continua com 13 571 712 bytes e SHA-256 `d08148935218a1fd9ee697e31f3e686928b4ac16bfc8e7d39a906b30d6eb3d14`. Não houve nova build/instalação nem nova comparação dos 706 ficheiros; a comparação integral de instalação permanece a evidência histórica dessa operação.

### Decisão, Git e rollback final

**FASE 3C CONCLUÍDA E VALIDADA**, no âmbito confirmado pelo autor, complementado por testes e auditoria do log. Uma matriz adicional de escalas/resoluções, instrumentação JS e medições de memória continuam fora do que se declara comprovado. Preservam-se os limites de importação, cache/reconciliação rejeitada e retirement documentados; não existe independência global de OpenWG.

Consolidação apenas dos caminhos da Fase 3C e documentação aplicável num único commit local `feat(gameface): add native hangar marks plugin`; verificar identidade do commit pelo git log. Nenhum log, backup, perfil ou artefacto compilado pertence ao staging. Sem push, tags, release ou Fase 3D.

Rollback final mantém o procedimento localizado abaixo e os dois backups verificados. Uma futura reposição do pacote Fase 3A requer autorização separada, cliente encerrado e verificação dos hashes; não foi executada. No código, reverter apenas o transporte/descriptor/entrypoint/lifecycle das marcas e reconciliar catálogo/bootstrap, preservando relógio, launcher, outras marcas e configurações.

## Confirmação funcional do autor — 2026-11-09

Após testar a build instalada, o autor confirmou: “Está a funcionar bem e sem problemas”. O relato anterior sobre desativação foi explicitamente retirado pelo autor, que confirmou que essa opção funcionava corretamente. A investigação desse relato não alterou código.

O hash instalado foi reconfirmado: `09b70a3b4a48194514393fa1f7cae1b7281a42434d1cbae9b78ce064cf4c9bec`. Esta confirmação valida o funcionamento no âmbito relatado pelo autor. Não equivale a registo individual de todos os itens da checklist, prova de três ciclos completos ou nova análise de logs; esses detalhes não foram declarados nesta confirmação. Os limites do loader e da recuperação documentados permanecem. Nenhuma nova alteração de código, instalação, build, commit ou push foi realizada.

## Gate e identidade

Hashes nativos reconfirmados: lib.js `392787b879bf47f1b2e3194cd6045286105a9756c3f26c8787f543f836b12051`; bundle.js `7e28391b4c51daa555b04d103a4031f7734b8d0728df03f7b73b47fa781873e5`.

O SDK calcula `Symbol.for(url.split("mono/")[1] || "unknown")`. O relógio conserva URL e identidade `unknown`. As marcas usam `coui://gui/gameface/mods/driftkings/mono/driftkings/hangar_marks/marks_plugin.js`, identidade `driftkings/hangar_marks/marks_plugin.js`.

Não há alias virtual: o URL corresponde literalmente a `res/gui/gameface/mods/driftkings/mono/driftkings/hangar_marks/marks_plugin.js` no pacote. `mono/` é um diretório físico neste namespace próprio; o SDK usa o segmento apenas para identidade. O loader importa a URL recebida sem reescrever o caminho. Exemplos CT de URLs absolutas coui constam dos modelos nativos de progresso (por exemplo `common_battle_quests_progress_model.py:6`). O relógio já valida o namespace próprio `mods/driftkings`. A resolução é fundamentada por esses contratos e pelo inventário; importação efetiva da nova URL no CT permanece pendente.

Dois descritores independentes, sem dependências cruzadas. Não se modifica o loader nem o relógio. Falhas anteriores à execução do entrypoint não são recuperáveis pelo próprio plugin. O loader pode reter rejeições e bloquear reconciliação; não foi corrigido.

## Rollback preparado antes da migração

Sem executar automaticamente: preservar primeiro os diffs e trabalho posterior. Repor apenas `payload_model` no adaptador de marcas e remover os seus hooks de UserMissionsPresenter; retirar os campos transport/plugin exclusivamente do contrato das marcas; retirar entrypoint e inventário/lint associados; reverter apenas o lifecycle de marks.js; ajustar testes específicos; regenerar bootstrap com `python -B build_tools/generate_ui_catalog.py --write`. Usar a baseline como referência para estes trechos, sem restaurar ficheiros partilhados completos. Preservar relógio, launcher, outros consumidores, dependências, perfis e configurações. Sem reset/clean/stash. Uma futura reversão no CT exige substituir apenas o pacote autorizado pelo artefacto de referência preservado e identificado por hash.

## Validação real necessária

Autorizar instalação separadamente. Confirmar valores, percentagens, gráfico, cores, fontes, posição, escala, opções, mudança de veículo, reentrada e três ciclos garagem/batalha; relógio e hidePrestige; launcher; outros módulos. Analisar logs e verificar ausência de duplicações. Testes de contrato/DOM simulado não são execução do loader real.

## Implementação e ownership

`gameface/lobby/hangar_marks_of_excellence.py` conserva a View, payload, eventos de veículo/cache, configurações e publicação transacional. Usa `native_payload_model` e publica um descriptor próprio após o original do presenter. Não substitui slots ocupados. Remove apenas o alias cujo descriptor ainda é a instância publicada e cuja URL coincide; uma substituição da mesma URL não autoriza remover o novo owner. Erros de registo são diagnosticados, sem fallback OpenWG. Este uso conservador da identidade do objeto Wulf deve ser confirmado no CT.

O relógio mantém integralmente os seus ficheiros. Não se criou helper genérico ou agregador. O catálogo tem 22 contratos: 2 janelas próprias, 2 nativos e 18 OpenWG. O gerador aceita explicitamente os dois consumidores nativos e rejeita identidades SDK coincidentes. As dependências de distribuição não mudaram.

O novo entrypoint não tem imports estáticos, DOM, listeners ou timers na avaliação inicial. A fábrica devolve init/destroy, `getState()`, `getDiagnostics()` e `getPendingResources()`. Estados: created, initializing, ready, failed, destroying, destroyed. Carrega CSS próprio e o kit existente (se ausente), seguido pelo renderer original. Não remove o kit global ou estilos pertencentes a outros consumidores.

Falhas recuperáveis registam causa, marcam failed, tentam limpeza e resolvem init com um componente vazio válido para o loader. Ready refere-se ao carregamento do renderer; não prova dados/aspeto visual no CT. Um erro posterior de callback muda o estado para failed. Não há retry automático nem sucesso silencioso.

`marks.js` conserva o corpo de renderização byte-equivalente normalizando finais de linha, HTML/CSS e cálculos. A adaptação limita-se ao lifecycle: owner público `__dkHangarMarks` publicado cedo, token de geração, ligação read-only local ao modelo, callbacks guardados, cancelamento de timeout/intervalo/animation frame, descarte independente de listeners/subscrição e remoção do DOM parcial. A ligação local evita alterar `shared/marks_panel.js`, cujo connect não contém fronteiras para falhas parciais/callbacks. O kit continua a fornecer os mesmos helpers visuais. Cleanup tenta todas as operações mesmo após erro, registando as que falham; uma API nativa que recuse libertação pode deixar referência inerte, sem garantia absoluta de libertação.

## Recursos pendentes e limite de recuperação

Cada recurso tem limite de espera de 10 segundos para que um renderer opcional não suspenda indefinidamente o allSettled nativo. Falha/timeout resolve o init com estado failed. Destroy é idempotente, resolve sem propagar erros recuperáveis e cancela timers próprios.

Um script clássico já pedido pode executar tarde. O seu callback de retirement e o token cancelado são mantidos até load/error, para impedir criar DOM numa geração destruída. Uma nova geração é recusada enquanto esse pedido não terminar. O número pendente é observável e a destruição regista recursos ainda a terminar. Se o evento nunca chegar, a funcionalidade fica indisponível nesse contexto; não se promete cancelamento físico do pedido. Não há listeners globais para esconder rejeições.

Import/sintaxe/avaliação do próprio entrypoint permanecem fora desta contenção. O loader CT pode reter a rejeição por URL e rejeitar reconciliações ao remover o descriptor. Remover/repor descriptor não é mecanismo de recuperação comprovado. O entrypoint não corrige o loader; o relógio conserva também os seus percursos originais de erro. Em falha de import real, preservar evidência e recuperar a sessão/artefacto conhecido, sem tentar churn automático do mapa.

## Testes e evidências

O teste novo de identidade/transporte foi criado antes da migração: os 186 testes build iniciais tiveram uma falha esperada (transporte das marcas ainda OpenWG). Após implementação, não foram removidos asserts para mascarar essa condição.

- Python 3: 860 testes da suite completa aprovados; 187 testes build incluem catálogo, identidade, integridade e corpo visual preservado.
- Python 2.7: 673 testes runtime aprovados; grupo lobby de 84 testes também aprovado após acrescentar coexistência dos hooks reais em ambas as ordens.
- Frontend: 23 suites aprovadas, incluindo renderer visual existente, relógio original e launcher.
- Fault injection executa entrypoints e renderers reais em DOM simulado: CSS/script ausentes, DOM parcial, subscrição, callback, timer, payload inválido, cleanup com exceção, timeout, destroy durante carga, chamadas repetidas, geração antiga pendente, inicialização em duas ordens, dados de outro veículo, preservação do relógio e alternância de hidePrestige após falha das marcas.
- Harness separado e identificado como MODELO DE CONTRATO do loader CT: URL/import/sintaxe/export/fábrica inválidos, init síncrono/rejeitado, destroy síncrono/rejeitado, rejeição retida, reconciliação rejeitada, colisão intencional de identidade, remoção pendente e contexto novo. Não executa nem modifica o loader nativo.
- Quatro testes de artefactos aprovados: recursos exatos no pacote, exclusão dos dois consumidores do bootstrap OpenWG, preservação dos outros 18 e verificação de fontes/movies existentes.
- Lint, validate_build_data, validate_locales, generate_defaults --check, check_undefined_names e git diff --check aprovados. 39 manifests, 307 módulos Python, 316 assets, 54 defaults e 2 dependências.

Comandos usados: `python -B tests/run_python.py --suite all`; `F:/Python27/python.exe -B tests/run_python.py --suite runtime`; `npm --prefix build_tools/javascript test`; `npm --prefix build_tools/javascript run lint`; `python -B build_tools/validate_build_data.py`; `python -B build_tools/validate_locales.py`; `python -B build_tools/generate_defaults.py --check`; `python -B build_tools/check_undefined_names.py`; `git diff --check`.

## Build CT e referência preservada

Comando: `python -B build_tools/compiler.py --mode debug --channel beta --version 0.1.8-beta.2 --keep-source-version --game-root C:/Games/World_of_Tanks_CT --reference-root E:/Wot_Mods_/Drift_Kings_ModPack/WoT_Tools/wot-src-CT`.

Artefacto: `E:/Wot_Mods_/Drift_Kings_ModPack/Driftkings_SettingsLab/build/debug/beta/0.1.8-beta.2/driftkings.wotmod`.

- Versão do pacote: 0.1.8-beta.2, debug CT 2.4.2.0; versão fonte permanece 0.1.8-beta.1.
- Tamanho: 13 584 784 bytes; 624 entradas.
- SHA-256: `09b70a3b4a48194514393fa1f7cae1b7281a42434d1cbae9b78ce064cf4c9bec`.
- Inventário: novo mono/driftkings/hangar_marks/marks_plugin.js; marks.js, marks.css e model.html originais da funcionalidade (apenas lifecycle de JS adaptado); kit/CSS/fontes partilhados; clock_plugin.js original. Sem res/gui/gameface/js/index.js global e sem testes de falha no pacote.
- Testes: `python -B tests/run_python.py --suite artifacts --wotmod build/debug/beta/0.1.8-beta.2/driftkings.wotmod` — 4 PASS.

Antes da substituição local preservou-se `build/reference/fase3a-d08148935218a1fd9ee697e31f3e686928b4ac16bfc8e7d39a906b30d6eb3d14.wotmod`, hash verificado. O compilador também preserva diretórios anteriores em build/previous. A instalação CT permanece no hash `d08148935218a1fd9ee697e31f3e686928b4ac16bfc8e7d39a906b30d6eb3d14`.

## Critérios de aceitação

| Grupo | Estado |
|---|---|
| Dois plugins, identidade distinta, URL fundamentada, contrato export, init/destroy, ownership e ausência de dependências cruzadas | PASS técnico; abertura do novo URL no CT pendente |
| Relógio, launcher, perfis, marcas de batalha/árvore, outros 18 transportes e kit partilhado preservados | PASS de código e regressão automatizada |
| Falhas recuperáveis, diagnósticos, failed distinto de ready, DOM parcial, callbacks cancelados e continuidade do relógio | PASS no harness isolado; sem garantia absoluta perante APIs nativas que falhem na limpeza |
| Limites de importação/reconciliação e recursos pendentes documentados | PASS |
| Python 3/2.7, frontend, lint, catálogo, identidade, fault injection, build, artefactos e rollback | PASS |
| Instalação CT, teste visual, troca de veículos, coexistência em jogo, três ciclos e análise de logs | PENDENTE |

## Integridade Git

HEAD permanece `57881e7b1b099191c4a286fbb842cf2954646c0b`, na branch feature/wot-2.4.2-ct. Alterações locais da Fase 3C sem staging, commit ou push. Ficheiros modificados: adaptador de marcas, renderer/lifecycle, catálogo, bootstrap gerado, gerador, inventário, lint e testes de contagem. Novos: entrypoint, testes de backend/build/frontend/artefactos, harness e este documento. STATUS recebe apenas o checkpoint atual; histórico anterior preservado.

## Instalação controlada autorizada — 2026-11-09

Concluída às 11:02 UTC, exclusivamente no CT 2.4.2.0 Common Test #995. Processos verificados antes do inventário, antes da substituição e após a verificação: cliente encerrado. Não foi iniciado o jogo. Nenhum código foi alterado nesta operação.

Origem debug e destino instalado verificados com SHA-256 integral `09b70a3b4a48194514393fa1f7cae1b7281a42434d1cbae9b78ce064cf4c9bec`. Destino: `C:/Games/World_of_Tanks_CT/mods/2.4.2.0 Common Test/driftkings.wotmod`.

O destino anterior foi confirmado como Fase 3A, SHA-256 `d08148935218a1fd9ee697e31f3e686928b4ac16bfc8e7d39a906b30d6eb3d14`. Backup criado a partir desse ficheiro e novamente verificado após a instalação:

`build/backups/ct-phase3c-install-20261109T110133967625Z/fase3a-d08148935218a1fd9ee697e31f3e686928b4ac16bfc8e7d39a906b30d6eb3d14.wotmod`.

Inventário integral do cliente: 706 ficheiros, aproximadamente 59,13 GiB; comparação SHA-256, tamanho e mtime antes/depois. Única diferença: `mods/2.4.2.0 Common Test/driftkings.wotmod`. OpenWG, ModsListAPI, configurações e restantes ficheiros do cliente preservados. Manifestos `before.json`, `after.json` e `installation-report.json` no mesmo diretório do backup, resultado PASS. Os registos anteriores de pacote ainda não instalado descrevem o momento da build.

Validação funcional, visual, troca de veículos, coexistência, três ciclos e análise dos logs continuam PENDENTES da sessão do autor. Sem commit, push, release ou alterações de código.
