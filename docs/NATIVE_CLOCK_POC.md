# Fase 3A — relógio com arranque por plugin nativo CT

2026-11-09. Branch `feature/wot-2.4.2-ct`, baseline `945316ceeccc10ea8b3c9fcb73f520de5223f68d`.

**FASE 3A CONCLUÍDA E VALIDADA no CT 2.4.2.0 Common Test #995, no âmbito confirmado pelo autor.** Testes automáticos e checklist funcional concluídos. OpenWG permanece instalado para os outros 19 consumidores e na distribuição. Não representa independência global do OpenWG nem validação de futuras versões. A telemetria JS de arranque/destroy não foi observada; a confirmação funcional real é a declaração do autor.

## Checkpoints 0 e 1 — leitura antes de código

Workspace inicialmente limpo, versão fonte `0.1.8-beta.1`, CT instalado `2.4.2.0 Common Test #995`, SRC `.version_name` `2.4.2.5516`. Pacote instalado da Fase 2: SHA-256 `41d2e35472e2d51165125ae4de21aa0965df3b369bf9c48ba63cc43807515adf`. OpenWG 1.2.2 e ModsList 1.8.0 nos hashes fixados no contrato. Worktrees não modificados.

As fontes externas e os pacotes nativos foram consultados sem extração/modificação. Não foram executados scripts do projeto, testes, geradores ou builds antes da decisão do gate.

## Evidências nativas e limites

Caminhos Python nativos abaixo relativos a `WoT_Tools/wot-src-CT/sources/res/scripts/client/`:

- `frameworks/wulf/view/view.py:18`: ViewSettings liga layout/modelo; `sharedLayoutID` é encaminhado ao proxy. Isto não comprova acesso ao DOM de outra view.
- `frameworks/wulf/view/view.py:199` e `:211`: remoção e associação de filhos.
- `gui/impl/pub/view_component.py:59`, `:69`, `:133`, `:156`: inicialização, filhos, ligação à root e descarte. O root Wulf não é prova de contexto DOM.
- `gui/impl/lobby/hangar/presenters/user_missions_presenter.py:37`, `:105`, `:113`: a garagem publica UserMissionsPluginModel no mapa `plugins`, com URL e lista de dependências.
- `gui/impl/gen/view_models/views/lobby/hangar/user_missions_plugin_model.py:9`: get/set URL e dependências; o array inicia vazio.
- `gui/impl/lobby/user_missions/hangar_widget/services/missions_container_service.py:96`: recolha dos plugins nativos, com start/stopListening e gestão de visibilidade. Não foi criado um segundo serviço nem usado um registo global permanente.
- `gui/shared/system_factory.py:1465`: registo/recolha de plugins de missões. Este contrato foi estudado, mas não alterado nem utilizado para registar um listener permanente do PoC.

Contratos JavaScript efetivamente lidos nos pacotes CT:

1. `gui-part1.pkg!gui/gameface/_dist/production/mono/hangar/chunks/lib.js:1`: `loadPlugin(url)` faz import dinâmico, exige `default.plugin`, chama a fábrica e utiliza `init`/`destroy`. `injectGFPlugins` disponibiliza o ambiente dos plugins. SHA-256: `392787b879bf47f1b2e3194cd6045286105a9756c3f26c8787f543f836b12051`.
2. `gui-part2.pkg!gui/gameface/_dist/production/mono/hangar/main/bundle.js:2`: importa e chama `injectGFPlugins` (alias `_e`), lê os descritores publicados, carrega dependências, chama `init`, monta o componente devolvido e chama `destroy` quando o plugin sai/desmonta. SHA-256: `7e28391b4c51daa555b04d103a4031f7734b8d0728df03f7b73b47fa781873e5`.
3. O código do plugin importado é executado pelo módulo da garagem no mesmo documento. O PoC devolve um componente vazio e desenha apenas os elementos atuais do relógio, sem introduzir um cartão de missão.

Não foi inferido que qualquer `R.plugins.js` seja automaticamente executado. A ativação comprovada utilizada é o mapa de descritores consumido pelo bundle da garagem. O JS do PoC é um asset `coui://` normal; o layout/modelo do relógio mantém o registo `R.mods.driftkings.main.clock` existente.

## Gate técnico

| Alternativa | JS | Modelo | Contexto necessário | Descarte | Classificação |
| --- | --- | --- | --- | --- | --- |
| View nativa própria | HTML próprio permite scripts | Modelo próprio | DOM da garagem não comprovado | Wulf | PARCIALMENTE COMPROVADA |
| Child View Wulf isoladamente | Não prova execução de HTML filho | Sim | Não prova DOM hospedeiro | Sim | PARCIALMENTE COMPROVADA |
| Plugin nativo da garagem | Import dinâmico comprovado | Modelo do relógio continua em subViews | Mesmo documento da garagem | init/destroy | COMPROVADA POR CONTRATO |
| Adaptador localizado | Publica descritor para loader existente | Mantém ClockView | Via plugin | Remoção do mapa | COMPROVADA POR CONTRATO |
| Híbrida escolhida | Plugin nativo + renderer atual | Wulf atual | Preserva DOM/hidePrestige | Wulf + plugin | COMPROVADA POR CONTRATO; validação real pendente |

O contrato fundamenta os oito requisitos do gate. Não comprova automaticamente layout, escala, disponibilidade do widget em todas as variantes ou comportamento visual no cliente real.

## Fluxo do relógio e transporte exclusivo

`components/main.py:init` continua a instalar o adaptador e iniciar ClockController. ClockView continua filha de RandomHangar; publica o mesmo payload/config por transações e acompanha shown/hidden/finalize. Formatos, calendário, posição, escala e perfis não foram alterados.

A seleção técnica está no catálogo: apenas `DriftkingsHangarClock` tem `transport=native_user_missions` e URL `main/clock_plugin.js`. Não é uma preferência persistente. A nova fábrica `native_payload_model` publica só `payload` e `DriftkingsUI`; não chama gf_mod_inject e não cria ModInjectModel. O import global OpenWG e as fábricas antigas permanecem, pois os outros consumidores ainda precisam deles. Assim, isto é autonomia do arranque JS do relógio, não autonomia do pacote Python completo.

O gerador exclui apenas o relógio do bloco OpenWG do bootstrap: 19 owners continuam nesse transporte, um usa o plugin nativo e duas janelas continuam próprias. Não há fallback que execute os dois transportes. Uma falha nativa é registada, sem reinjetar o relógio pelo OpenWG.

O hook localizado de UserMissionsPresenter chama o original primeiro e acrescenta exclusivamente o descritor do relógio no seu ID próprio. Não substitui descritores ocupados. No finalize remove apenas o descritor que ainda tem a URL esperada; o loader nativo efetua o destroy. Os hooks pertencem ao owner já existente `components.main`.

`clock_plugin.js` implementa independentemente o contrato `default.plugin() -> init()/destroy()`, carrega fontes/CSS e o renderer ES5 existente, espera a criação do owner e devolve componente vazio. Destruição em carregamento pendente espera essa geração e elimina owner, scripts e links. Não descarta um owner previamente ocupado. Nenhum código OpenWG foi copiado.

## hidePrestige

`main/clock.js:193–201` cria um estilo no DOM da garagem com `[class*="Information_prestige_"] { display:none; }` quando pedido. A regra CSS aplica-se também a elementos nativos recriados que correspondam ao seletor. Ao desativar, limpa a regra; no dispose remove o estilo. O relógio não depende de conseguir atravessar o DOM de uma view isolada: o plugin executa no documento hospedeiro.

`clock.js`, `clock.css` e `clock.html` permanecem byte-equivalentes à baseline (normalizando finais de linha). O teste novo executa o renderer real e confirma a alternância da política e remoção dos efeitos no descarte. Esta simulação não substitui a verificação visual do prestígio no CT.

## Compatibilidade JavaScript

Apenas `clock_plugin.js` é ES module (export default e Promise), exigido pelo import nativo demonstrado. Tem exceção ESLint específica ES2015/module. O renderer e os outros scripts continuam sob ES5. Não foi alterado `gui/gameface/js/index.js`, nenhum bundle original ou biblioteca externa.

## Resultados automáticos e build

- 856 testes Python 3 runtime/build aprovados.
- 672 testes runtime Python 2.7 aprovados.
- 21 suites frontend aprovadas, incluindo launcher da Fase 2.
- Três testes de artefactos compilados aprovados.
- Lint, imports, nomes indefinidos, defaults, traduções, contratos e catálogo aprovados.
- Catálogo: 22 contratos Gameface; 19 injetados OpenWG e um nativo.

Os novos testes backend verificam ausência de injeção no modelo nativo, preservação das 19 chamadas OpenWG dos outros owners, payload, hidePrestige, conflitos de slot, falha de registo e descarte. Testes de build verificam empacotamento, exclusão do relógio do bootstrap e rejeição de transporte nativo noutros módulos. O frontend importa realmente o ES module em Node e executa o renderer real num DOM simulado, incluindo timer, formatos, ocultação, hidePrestige, erro de carregamento, recriação e destruição durante carregamento pendente.

Falhas iniciais corrigidas: captura do logger no teste usava capitalização incorreta; o novo asset não constava inicialmente de components.json. Corrigidos o teste e o inventário, sem remover asserts ou mascarar dependências. Os testes finais passaram.

Build debug CT: `python -B build_tools/compiler.py --mode debug --channel beta --version 0.1.8-beta.2 --keep-source-version --game-root C:/Games/World_of_Tanks_CT --reference-root E:/Wot_Mods_/Drift_Kings_ModPack/WoT_Tools/wot-src-CT`.

Artefacto: `build/debug/beta/0.1.8-beta.2/driftkings.wotmod`. Mantém o ciclo local CT com versão fonte `0.1.8-beta.1`; não é release. SHA-256: `d08148935218a1fd9ee697e31f3e686928b4ac16bfc8e7d39a906b30d6eb3d14`. Plugin, renderer, CSS e bootstrap correspondem às fontes. Não inclui `res/gui/gameface/js/index.js`.

**Não instalado.** O CT mantém o pacote validado da Fase 2, hash `41d2e35472e2d51165125ae4de21aa0965df3b369bf9c48ba63cc43807515adf`. OpenWG e ModsList não foram removidos. A build local no caminho acima passou a ser o PoC; identificar sempre pelo hash, não apenas pela versão.

## Teste CT a autorizar separadamente

Depois de instalação autorizada com backup: verificar log Python `Clock native plugin registered; OpenWG injection not requested` e, quando exposto pelo logger Gameface, `Clock started by native user-missions plugin`. Confirmar pacote por hash. Evidência de transporte inclui modelo sem ModInjectModel, relógio ausente do bloco OpenWG gerado e execução pelo loader nativo; mera ausência de erros não prova independência.

Validar relógio, posição/escala, hora em atualização, formatos, configurações, hidePrestige ligado e desligado, ocultação, regresso ao hangar, recriação e instância única. Validar launcher e restantes módulos. Verificar especialmente garagem com widget de missões oculto/reconstruído, dependência nova da disponibilidade desse presenter. Não remover OpenWG para este teste: os restantes 19 consumidores continuam a utilizá-lo. A independência num runtime sem OpenWG requer futura migração ou isolamento próprio autorizado.

## Riscos e rollback delimitado

Riscos: contrato interno de plugins e DOM sujeito a versões; widget de missões pode não existir/ser montado em certos contextos; necessidade de confirmar ordenação real de init/destroy e do ciclo Wulf; dupla execução deve continuar impossível. Sem promessas de FPS/memória.

Sem rollback automático. Para repor somente o transporte do relógio, preservar antes qualquer trabalho posterior:

1. Retirar os dois campos técnicos novos do contrato do relógio e voltar a usar payload_model em gameface/lobby/main.py.
2. Retirar apenas os imports/hook de UserMissionsPresenter e o descritor nativo dessa função.
3. Regenerar o catálogo para voltar a incluir o relógio no bootstrap OpenWG.
4. Retirar o novo clock_plugin.js, a sua entrada de assets e a exceção ESLint específica.
5. Retirar a nova fábrica nativa e testes do PoC apenas se deixarem de ter consumidores; restaurar os hunks do gerador relativos a este transporte.
6. Atualizar estes registos e executar validação apropriada. Nenhum perfil ou outro módulo precisa de reposição.

Como nada foi instalado, não há recuperação do cliente a executar nesta fase. Não usar reset/clean/stash. A Fase 2 permanece preservada na baseline. Não há commit, push ou Fase 3B.

## Instalação autorizada no CT — 2026-11-09

Após autorização explícita do autor, o PoC foi instalado em `C:/Games/World_of_Tanks_CT/mods/2.4.2.0 Common Test/driftkings.wotmod`, com o CT e processos associados fechados. Hash instalado confirmado: `d08148935218a1fd9ee697e31f3e686928b4ac16bfc8e7d39a906b30d6eb3d14`.

Backup verificado da Fase 2: `build/backups/ct-native-clock-20261109-054305/driftkings.wotmod`, hash `41d2e35472e2d51165125ae4de21aa0965df3b369bf9c48ba63cc43807515adf`. Recuperação: com CT fechado, copiar esse ficheiro de volta ao destino acima e confirmar o hash anterior; não executar automaticamente.

Os restantes ficheiros de mods/res_mods mantiveram os hashes durante a instalação, incluindo perfis e bibliotecas externas. OpenWG e ModsList preservados. O jogo não foi iniciado pelo agente; validação funcional e do transporte nativo no CT continua pendente. As declarações anteriores de não instalação são checkpoints históricos anteriores a esta autorização. Sem commit ou push.

## Primeira leitura do log do PoC — 2026-11-09

Sessão iniciada às 05:43, ainda em execução durante a leitura. Snapshot consultado: 2112 linhas, SHA-256 `e53e307d4a4d341790f6e7c29e94ffad0d6e05fd99a21be67adf96dccc63839c`; o ficheiro pode continuar a crescer. O pacote instalado foi novamente confirmado no hash do PoC.

Na linha 1855, o Driftkings inicia com todos os serviços ativos, `failures=[]` e `disabled={}`. Às 05:44:36, linha 2034, há a mensagem Python `Clock native plugin registered; OpenWG injection not requested`. Isto confirma o registo do descritor nativo no backend.

No snapshot não foram encontrados Traceback, ImportError, ReferenceError, TypeError, SyntaxError, falha de registo/descarte do plugin ou erro identificado do launcher. As quatro entradas ERROR da sessão correspondem às partículas BZ-75 conhecidas. Os erros de SVG sociais presentes no log acumulado pertencem às sessões anteriores no trecho consultado.

A mensagem JS `Clock started by native user-missions plugin` não aparece no log consultado. A ausência pode refletir a exposição/nível do logging Gameface e não prova falha; também não permite declarar o frontend executado. Confirmação visual do relógio, atualização, formatos, escala e hidePrestige continua pendente. Descarte/encerramento também não foi avaliado, pois o CT estava aberto. Sem correções, recompilação, instalação ou alteração do cliente nesta revisão.

## Confirmação funcional do autor — 2026-11-09

Após a leitura do log e a pergunta específica sobre apresentação/atualização do relógio e ocultação/reposição do prestígio, o autor respondeu “Sim funciona”. Ficam confirmados pelo autor esses comportamentos na build PoC instalada, hash `d08148935218a1fd9ee697e31f3e686928b4ac16bfc8e7d39a906b30d6eb3d14`.

A confirmação visual é distinta da evidência do transporte: o log confirma o registo nativo Python; o catálogo exclui o relógio do bootstrap OpenWG e o modelo nativo não cria ModInjectModel. A mensagem específica de arranque JavaScript não foi observada no log consultado. Não se declara uma execução global sem OpenWG: a biblioteca permaneceu instalada para os outros 19 consumidores.

Não foram confirmados individualmente todos os formatos, escalas, modos, ciclos de destruição/recriação ou regressões dos outros módulos nesta sessão. Esses pontos continuam pendentes de validação específica. As pendências anteriores de apresentação/atualização/hidePrestige são históricas. Nenhuma alteração de código, nova build, instalação, commit ou push foi executada para registar esta confirmação; sem Fase 3B.

## Verificação final condicionada — 2026-11-09

**FASE 3A IMPLEMENTADA — VALIDAÇÃO PENDENTE. Commit suspenso.** O pedido final exige confirmação adicional dos formatos, posição/escala, ativar/desativar, alternância repetida do prestígio, três ciclos de regresso à garagem e regressões nesta build. Foi apresentada checklist ao autor; os resultados adicionais ainda não foram recebidos nesta verificação. A confirmação anterior permanece válida para relógio visível/atualização e prestígio nos dois estados.

### Auditoria e testes finais

Branch `feature/wot-2.4.2-ct`, HEAD `945316ceeccc10ea8b3c9fcb73f520de5223f68d`; inicialmente os 12 ficheiros rastreados e cinco novos da Fase 3A, sem alterações alheias identificadas. Nenhuma refatoração/correção de código necessária. Original renderer/CSS/HTML, launcher, serviço de settings, versões e contrato de dependências comparados com HEAD e preservados. Os outros 21 contratos Gameface são idênticos à baseline. O modelo do relógio não cria ModInjectModel e o catálogo gerado só mantém os 19 owners OpenWG.

Comandos repetidos: `python -B tests/run_python.py --suite all` (856 PASS); `F:/Python27/python.exe -B tests/run_python.py --suite runtime` (672 PASS); `npm --prefix build_tools/javascript test` (21 suites PASS); lint, validate_build_data, generate_ui_catalog (sem --write), validate_locales, generate_defaults --check, check_undefined_names, isort --check-only e diff --check PASS. Três testes de artefactos passaram contra a build existente; sem nova build. Os testes usam o módulo ES e renderer reais com fronteiras/DOM simulados, não constituindo prova de todos os comportamentos no motor Gameface.

Hash instalado e da build local confirmado: `d08148935218a1fd9ee697e31f3e686928b4ac16bfc8e7d39a906b30d6eb3d14`. Backup da Fase 2 existe e mantém `41d2e35472e2d51165125ae4de21aa0965df3b369bf9c48ba63cc43807515adf`. Assets do plugin/renderer/bootstrap no WOTMOD correspondem às fontes; nenhum index.js global incluído.

### Log após encerramento

CT e processos associados ausentes durante a verificação. O log termina às 05:47:27 com desinicialização do cliente. Snapshot completo observado: 2506 linhas, SHA-256 `1b9e59567f18ef82ac08f7ebc270971914205808965e6ee63e1f3e04bfa9c626`.

Na sessão PoC iniciada às 05:43, o arranque na linha 1855 regista serviços ativos, `failures=[]`, `disabled={}`. Registo nativo às 05:44:36, 05:45:22 e 05:47:17 (linhas 2034, 2133 e 2391). Estes registos não provam três ciclos completos de batalha/replay, nem ausência visual de duplicações. Não foram encontrados erros identificados de import, plugin, ViewModel ou callbacks assíncronos. Quatro entradas ERROR de partículas BZ-75; os SVG sociais observados anteriormente pertencem às sessões anteriores. Nenhuma correção desses problemas foi efetuada.

A mensagem JS de arranque continua ausente e não existe telemetria explícita de destroy/estado final de serviços. A confirmação visual anterior é evidência independente de funcionamento do renderer; o registo Python não é tratado isoladamente como prova JS. Não se deduz falha de descarte da ausência de mensagem, nem se declaram callbacks residuais impossíveis apenas pelo log.

### Critérios e pendências

| Critério | Estado/evidência |
| --- | --- |
| Ponto de entrada e contrato default.plugin/init/destroy | PASS por contrato nativo; módulo ES real testado |
| Renderer, atualização e prestígio ligado/desligado | PASS por confirmação anterior do autor |
| Registo nativo e serviços sem falhas | PASS por log |
| Formatos, posição/escala, ativação/desativação no CT | PENDENTE de confirmação específica |
| Alternância repetida de hidePrestige sem resíduos | PENDENTE no CT; PASS automático em DOM simulado |
| Três ciclos garagem/batalha ou replay/regresso sem duplicação | PENDENTE |
| Descarte/callbacks residuais | PASS automático; nenhum erro identificado no log encerrado; prova funcional completa PENDENTE |
| Launcher e outros módulos nesta build | Contratos preservados e regressão automática PASS; confirmação real específica PENDENTE |
| Testes, build existente e ausência de index.js global | PASS automático/inspeção |
| Rollback delimitado e backup | PASS por inspeção |

Não houve staging, commit, push, reinstalação, alteração de perfis, bibliotecas ou worktrees nesta verificação. Só este documento e STATUS foram atualizados para registar resultados e pendências. A condição para commit ainda não está satisfeita. Sem Fase 3B ou planos concretos para outros consumidores.

## Encerramento após respostas à checklist — 2026-11-09

**FASE 3A CONCLUÍDA E VALIDADA.** As respostas do autor à checklist final completam as pendências funcionais essenciais e permitem o único commit local autorizado. Não houve alteração do código ou dos testes depois da verificação final aprovada; não foi necessário repetir as suites por uma alteração apenas documental.

Respostas recebidas:

- À pergunta sobre formatos de hora/data, posição, escala, ativar/desativar e ausência de duplicações: “sim estavam no local correto”. Regista-se a confirmação afirmativa da checklist, com ênfase explícita na posição correta; não se inventa uma lista adicional de formatos/resoluções ensaiados.
- À pergunta sobre alternância repetida do prestígio sem resíduos, três ciclos garagem → batalha/replay → garagem sem duplicações e encerramento normal: “sim”.
- À pergunta sobre botão Driftkings, abertura/fecho X/Esc, atalho e regressões dos outros módulos de garagem/batalha: “sim”.

O CT está fechado, o PoC instalado e a build mantêm o hash documentado, e o backup da Fase 2 foi novamente confirmado. O log acumulado inclui uma sessão adicional de teste, terminada às 05:54:41: 3391 linhas, SHA-256 `d510d843725a0d72b3355f658611400ae8abb6ce27fec25d3c7588705a413cfd`. Nessa sessão, arranque com `failures=[]` e `disabled={}` na linha 2866 e registos nativos às 05:52:31, 05:53:06 e 05:54:02 (3045, 3201, 3253). Sem exceções identificadas do relógio; quatro erros conhecidos de partículas BZ-75. A revisão anterior do log permanece como evidência histórica. Não se atribui à mensagem Python uma prova isolada de execução JS: a confirmação real do relógio/hidePrestige, a rota de transporte exclusiva e os testes complementam o registo. A falta de telemetria explícita de destroy permanece uma limitação observacional; não foram identificados erros de descarte ou duplicações nos testes/log/cenário declarado.

| Critério de aceitação | Resultado final |
| --- | --- |
| Entrada nativa, default.plugin e init no contexto correto | PASS por contrato, execução automática do módulo real e confirmação funcional do autor |
| Renderer e atualização | PASS automático e real |
| Formatos/configurações e posição/escala | PASS automático e confirmação afirmativa da checklist; sem extrapolar formatos/resoluções não especificados |
| hidePrestige nos dois estados e alternância sem resíduos | PASS automático e real declarado |
| Reentrada após três ciclos sem duplicação | PASS por declaração do autor |
| Descarte/callbacks residuais | PASS nos testes automáticos; ciclo/encerramento real declarado e sem erros identificados; telemetria JS direta ausente |
| Launcher e restantes consumidores | PASS na regressão automática e checklist real declarada; contratos preservados |
| Integridade da build, testes e ausência de index.js global | PASS por verificação automática/inspeção |
| Rollback e backup | PASS por inspeção |

Resultados finais permanecem: 856 testes Python 3, 672 runtime Python 2.7, 21 suites frontend e três testes de artefactos aprovados. Sem falhas bloqueantes identificadas. A auditoria limita o diff à Fase 3A, com staging explícito apenas de código/recursos/testes/documentação desta fase; nenhum perfil, log, backup ou artefacto compilado será incluído. Versões e dependências mantidas. Um único commit local, sem push, é autorizado pelo pedido de encerramento após satisfação destas condições. Sem Fase 3B ou migração/planeamento concreto dos restantes consumidores.

Na inspeção do staging, diff --cached --check detetou uma linha vazia adicional no fim de `test_native_clock.py`, que não era abrangida pelo diff de ficheiros não rastreados anterior. Foi removida apenas essa linha; AST antes/depois idêntica, sem mudança de teste/comportamento. Verificação de staging repetida sem erros.
