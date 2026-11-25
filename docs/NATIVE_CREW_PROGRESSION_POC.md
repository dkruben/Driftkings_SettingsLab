# Fase 3D — Native Crew Progression PoC

Baseline `fa8c699000535276e12a08f1fb089ebd7783a26b`, branch feature/wot-2.4.2-ct, CT 2.4.2.0 Common Test #995, fontes 2.4.2.5516.

**FASE 3D FUNCIONALMENTE VALIDADA — APTO PARA COMMIT LOCAL.** Testes novamente executados com rastreabilidade na Fase 3D.3; aviso Scaleform mantido como risco residual em observação, com causa não determinada. Não representa PASS definitivo da gestão de memória. Staging e commit aguardam autorização expressa; sem push ou Fase 3E. As secções anteriores à Fase 3D.3 abaixo são históricas.

## Fase 3D.3 — rastreabilidade e encerramento documental — 2026-11-09

**APTO PARA COMMIT LOCAL**, sem autorização implícita para executar staging ou commit. A validação funcional anterior dos oito cenários é preservada como confirmação do utilizador. O aviso Scaleform continua como risco residual em observação, com causa não determinada; a investigação de memória não foi encerrada como PASS definitivo.

### Snapshot e nova execução

Branch `feature/wot-2.4.2-ct`, HEAD `fa8c699000535276e12a08f1fb089ebd7783a26b`; 20 caminhos da Fase 3D (13 modificados e sete novos), staging vazio e worktrees preservados. Evidência local ignorada pelo Git e fora dos recursos de packaging: `build/diagnostics/phase3d3/20261109T131245Z/`. Não incluir esta pasta no futuro commit.

Snapshot antes dos testes: `2bf769feb61120aa1ae64e2e7a0842cafe63061cbb6a6d29639049b8d3326ea6`. O identificador é o SHA-256 do mapa ordenado de caminhos/hashes em `snapshot-before.json`; inclui todos os ficheiros rastreados e novos não ignorados, os 20 caminhos da fase, hashes específicos dos testes, ferramentas, comandos e timestamp UTC. `snapshot-after-tests.json` confirma hashes idênticos, sem alteração de origem/testes/gerados durante os testes. As alterações posteriores desta execução limitam-se aos três documentos autorizados e ficam separadas em `snapshot-final.json`.

Ferramentas: Python 3.14.3, Python 2.7.18, Node.js v20.19.2, npm 11.12.1 e ESLint 10.13.0. Manifestos/lock de dependências incluídos no snapshot; inventário npm guardado com as versões. Não houve instalação ou atualização de dependências.

Resultados históricos abaixo mantêm-se históricos; esta nova execução confirma os resultados para o snapshot acima. Todos os horários da tabela são UTC em 09/11/2026. Cada linha está ligada ao mesmo snapshot; comandos exatos, início/fim completos, exit code e SHA-256 dos logs constam de `results.json`.

| Suite | Comando | Total/alcance | Resultado / exit code | Início–fim UTC | Log na pasta de evidência |
|---|---|---|---|---|---|
| python3 | `python -B tests/run_python.py --suite all` | 864 testes | PASS / 0 | 13:12:48–13:13:19 | `python3.log` |
| python27 | `F:/Python27/python.exe -B tests/run_python.py --suite runtime` | 675 testes | PASS / 0 | 13:13:19–13:13:46 | `python27.log` |
| frontend | `npm.cmd --prefix build_tools/javascript test` | 25 suites | PASS / 0 | 13:13:46–13:13:49 | `frontend.log` |
| lint | `npm.cmd --prefix build_tools/javascript run lint` | zero avisos | PASS / 0 | 13:13:49–13:13:50 | `lint.log` |
| build-data | `python -B build_tools/validate_build_data.py` | 39 manifests / 307 módulos / 317 assets | PASS / 0 | 13:13:50–13:13:51 | `build-data.log` |
| locales | `python -B build_tools/validate_locales.py` | 18 locales / zero não traduzidos | PASS / 0 | 13:13:51–13:13:52 | `locales.log` |
| defaults | `python -B build_tools/generate_defaults.py --check` | 35 componentes | PASS / 0 | 13:13:52–13:13:52 | `defaults.log` |
| names | `python -B build_tools/check_undefined_names.py` | zero nomes indefinidos | PASS / 0 | 13:13:52–13:13:53 | `names.log` |
| artifacts | `python -B tests/run_python.py --suite artifacts --wotmod build/debug/beta/0.1.8-beta.2/driftkings.wotmod` | 5 testes | PASS / 0 | 13:13:53–13:13:53 | `artifacts.log` |
| diff-check | `git diff --check` | sem erros de whitespace | PASS / 0 | 13:13:53–13:13:53 | `diff-check.log` |

As suites executadas incluem os testes reais existentes `test_crew_bridge.js`, `test_native_crew_plugin.js`, `test_native_crew_runtime.py`, `test_native_crew_catalog.py` e `test_native_crew_package.py`: getRow estrito, snapshots/veículos, evento sem payload, argumentos JSON, ownership, CrewDetails, coexistência nas seis ordens, identidades, falhas recuperáveis e packaging. Fault injection ocorreu apenas nos testes isolados existentes, nunca no CT; não foram alterados testes/fixtures para obter PASS. Os cinco testes de artefactos leram a build 3D existente; não houve nova build.

### Incorporação da investigação 3D.1

Uma ocorrência original às **12:28:09.825**: `Memory arena contains allocations. Lobby = true, Battle = false`. MemReportFull/HeapDetailed/FileSummary não identificaram objetos, tamanhos ou owners. A mensagem é emitida pelo gestor nativo Scaleform; hosting Scaleform–Wulf não demonstra partilha de arenas com Gameface nem atribui a alocação ao plugin.

| Sessão posterior | Evidência de encerramento | Limitação |
|---|---|---|
| A — 12:43:57–12:46:40 | `Memory arenas are empty`, 12:46:36.592; saída normal | Cinco tooltips identificados pelo utilizador como eventos de Natal, não da tripulação |
| B — 12:47:55–12:57:19 | `Memory arenas are empty`, 12:57:15.651; saída normal | Utilizador tentou batalha mas faltavam jogadores; regressou ao hangar. Não houve batalha efetiva nem confirmação adicional de três ciclos |
| C — 13:01:28–13:03:39 | `Memory arenas are empty`, 13:03:35.981; saída normal | Interações de tripulação observáveis; nem todos os passos, alternância das opções ou restauração inicial são demonstráveis pelo log |

O aviso original **não foi reproduzido nestas três sessões**. Não existe relação causal demonstrada com a migração 3D, nem prova de inexistência absoluta de fugas. Os oito PASS funcionais anteriores são evidência separada fornecida pelo utilizador; não são deduzidos destas sessões de reprodução. Excertos, hashes de origem e relatórios preservados em `build/diagnostics/phase3d1/`; o relatório do cenário C incorpora as clarificações posteriores de A/B. As evidências originais não foram reescritas.

Correção factual: são **oito grupos de registo backend** na sessão original. O oitavo, linhas **5494–5496**, às **12:28:02.946–.947**, está no excerto preservado `build/diagnostics/phase3d1/20261109T124256Z/original-shutdown-excerpt.log`; foi omitido da enumeração anterior. Não se inferem oito instâncias JS simultâneas.

### Riscos residuais e decisão

| Ponto | Classificação | Estado |
|---|---|---|
| Aviso Scaleform original sem owner; três sessões seguintes negativas | Risco residual | EM OBSERVAÇÃO, causa não determinada |
| Import rejeitado antes de executar o entrypoint; loader pode reter promises rejeitadas | Limitação arquitetural | Recuperação local não garantida |
| Ausência de observação individual de todos os init/destroy JS no CT | Limitação de observabilidade | Não resolvida pelos testes isolados |
| Cenário B complementar com batalha efetiva | Teste pendente | Indisponível por falta de jogadores |
| Heap, retenções e performance completos | Não medido | Sem profiling completo de memória |

Sem regressão bloqueante identificada; estas limitações não são automaticamente regressões. **APTO PARA COMMIT LOCAL** após nova execução rastreável e atualização documental, mantendo os riscos acima. Não significa encerramento da investigação de memória, independência global de OpenWG, publicação ou autorização para a Fase 3E.

Integridade reconfirmada: pacote local/instalado `7c50836f5f53eaf97a8c3a63433cc71e6889089b4d50b8fd98770888477ad89c`; backup 3C `09b70a3b4a48194514393fa1f7cae1b7281a42434d1cbae9b78ce064cf4c9bec`. Nenhum pacote foi alterado, compilado, instalado ou restaurado; CT não iniciado. Sem staging, commit, push, alteração funcional/testes/catálogo/packaging ou worktrees. Os checkpoints seguintes documentam as etapas históricas anteriores.

## Auditoria final de logs e lifecycle — 2026-11-09

### Estado e limites da operação

Branch feature/wot-2.4.2-ct, HEAD fa8c699000535276e12a08f1fb089ebd7783a26b. Estado inicial: 19 ficheiros modificados/novos da implementação, staging vazio, worktrees preservados e nenhuma alteração alheia identificada. Esta tarefa alterou exclusivamente este documento, STATUS e CT_COMPATIBILITY. Não houve código, teste, catálogo ou recurso alterado; não houve build, instalação, rollback, commit ou push. O cliente já estava aberto pelo autor; foi encerrado pelo autor a pedido da auditoria, sem intervenção no processo pelo agente.

### Identificação da sessão

O game.log agrega duas sessões. A primeira, iniciada às 11:02:53, pertence à Fase 3C e foi excluída dos resultados da Fase 3D. A segunda começa na linha 891, às **11:59:17**, depois da instalação Fase 3D concluída às 11:55:42. Header binário 2.4.2.1571 #2654956; metadata Driftkings identifica CT 2.4.2.0 Common Test #995 e mod 0.1.8-beta.2. O marcador específico Crew progression native plugin distingue a implementação da anterior, que usava a mesma versão debug. A identidade da build é complementada pelo hash instalado, não inferida apenas da versão.

Ficheiro final: `C:/Games/World_of_Tanks_CT/game.log`, 5622 linhas, 826805 bytes, SHA-256 `cf90a96a1ef5542c9f0fc2ae1656fb98373b731668f4e1f5ed2d57f0004447bf`. Encerramento às **12:28:14.337**, linha 5619, CAT Client was deinitialized. Processos CT ausentes após encerramento. O monitor `win64/Logs/monitor_20261109_1159450748.log` regista Normal exit às 12:28:14.360; não se confunde esta mensagem com prova de ausência de alocações residuais.

### Serviços e registos nativos

- Linha 1247, 11:59:43.462: Startup complete, 35 componentes, 13 serviços active, failures=[] e disabled={} — PASS efetivamente registado.
- Linhas 1065/1066: ModsListAPI e OpenWG carregados, necessários aos consumidores restantes.
- RandomHangar inicialmente enumerados na auditoria histórica: linhas 1427, 3680, 3816, 5159, 5297, 5356 e 5385.
- Oito grupos de registo Python dos três plugins (enumeração corrigida na Fase 3D.3): 1430–1432, 3683–3685, 3818–3820, 5162–5164, 5299–5301, 5358–5360, 5387–5389 e 5494–5496. Horas: 12:00:07.112; 12:14:05.600; 12:15:13.215; 12:21:41.338; 12:22:06.552; 12:22:59.392; 12:24:17.902; 12:28:02.946–.947. Todos indicam OpenWG injection not requested.
- São reentradas/recriações de hangar, não prova de oito instâncias JS simultâneas. Há duas entradas BattleSpace e regressos reconhecíveis no excerto; os três ciclos completos são evidência fornecida pelo autor, não uma contagem deduzida só destes registos.
- Existem 32 aberturas ParamTooltipView e abertura da ficha de tripulante; não expõem o conteúdo dos argumentos, valores ou callbacks de cada tooltip.

Não foram identificados Traceback, importações falhadas, falhas de publicação, erros Wulf/ViewModel, rejeições unhandled, colisões de slot, timeout ou marcadores específicos de falha/cleanup dos três plugins. Classificação: SEM ERRO IDENTIFICADO no material disponível, não prova absoluta do funcionamento interno.

Os marcadores JS de API ready, início do relógio e renderer das marcas não aparecem. Alias numéricos, URLs, identidades SDK, fábrica, init e destroy não estão expostos pelo log. O descarte bem-sucedido também não tem marcador JS individual emitido por estes entrypoints. Três registos Python não comprovam três execuções JS independentes; os resultados do autor, código, testes e pacote são evidências complementares.

### Erros e avisos classificados

| Evidência | Classificação |
|---|---|
| 12 ERROR das partículas Ch62_BZ_75_M, em três grupos | Problema de partículas conhecido; sem alteração ou correção nesta fase |
| Dois CellAppLoginRequestProtocol::onAttemptsExhausted e um REASON_GENERAL_NETWORK | Erros de conectividade/CellApp, sem vínculo demonstrado ao bridge; não ocultados como sessão sem erros |
| Avisos font: inherit / font-size: inherit | Declarações correspondentes existem no CSS preexistente de resultados; o novo bridge não adiciona CSS. Atribuição exata não exposta no log |
| Resource not found userMissions.missionIcons.c_32._silver / c_80._silver | Avisos do widget de missões; relação com a progressão não demonstrada |
| Avisos de texturas, imagens Scaleform, CGF e MouseCursor NOT DELETED | Contexto C++/UI registado separadamente; não equivalem a prova de fuga do plugin |
| Linha 5561, 12:28:09.825: Scaleform Memory arena contains allocations. Lobby = true, Battle = false | **PENDÊNCIA TÉCNICA DE TEARDOWN**, origem indeterminada |

O erro Scaleform surge após destruição de scaleform/lobby, lobby.swf e waitingTransitionsApp.swf, linhas 5533–5558. Os relatórios MemReportFull, MemReportHeapDetailed e MemReportFileSummary, linhas 5562–5570, estão vazios: não identificam objetos, tamanhos ou owners. Depois, o manager termina e o cliente fecha normalmente. A sessão anterior Fase 3C registava Memory arenas are empty, linha 835, mas teve um percurso diferente; não é uma comparação controlada. Não se atribui esta diferença automaticamente à Fase 3D, nem se descarta a mensagem como inofensiva.

Não foram feitas medições de memória, perfis de desempenho ou fault injection no CT real. Sem telemetria JS individual e sem identificação das alocações, não existe evidência suficiente para afirmar descarte perfeito ou regressão causal da progressão. A decisão é auditoria técnica pendente, não regressão identificada.

### Contratos e coexistência revistos

Catálogo: 22 entradas, duas próprias, três nativas e 17 OpenWG. Comparação AST com fa8c6990: apenas CrewProgression muda. Os aliases declarados são mods/driftkings/main/clock, mods/driftkings/hangar_marks_of_excellence/model e mods/driftkings/crew_progression/model, distintos; números alocados no runtime não aparecem no log. URLs e identidades SDK permanecem distintas: unknown, driftkings/hangar_marks/marks_plugin.js e driftkings/crew_progression/crew_plugin.js.

Código/backend e testes confirmam descriptor sem substituição de slot ocupado, remoção por instância+URL, native_payload_model sem pedido gf_mod_inject e exclusão dos três owners do bootstrap OpenWG. Não há dependências cruzadas. CrewDetails, carrossel, launcher e restantes consumidores mantêm OpenWG, e as bibliotecas externas permanecem presentes com hashes fixados. Não representa independência global de OpenWG.

Revisão de crew.js: global/método preservados; invID com comparação estrita, slot não usado como ID; retorno slot/id/lines/kinds e null em indisponibilidade. Binding/payload alterado invalida snapshot conhecido e agenda releitura. Estado é limpo antes de cleanup e getRow antigo devolve null após dispose. Event('dk-carousel-config') mantém nome e ausência de payload, notifica após dados, perda e retirada da API. O percurso CrewSlot → dkCrewProgression → JSON.stringify → ParamTooltipView/Model.params → documento separado mantém schemas e patches intactos. Não existe uma nova ponte entre documentos.

CrewController e a instalação de CrewDetails preservam a baseline. O registo g_controller.views não é limpo pelo frontend, que não chama stop no controlador Python. A View da progressão só retira a sua entrada se ainda a possuir. Os testes executam o backend/controller e implementação real de CrewDetails com serviços/Wulf isolados, e o frontend real de CrewDetails com o bridge: removê-lo/falhá-lo não impede atualização dos details. Isto é PASS de contrato/teste, complementado por PASS funcional do autor; não é telemetria runtime de cada remoção.

### Testes novamente executados

| Comando/verificação | Resultado desta auditoria |
|---|---|
| python -B tests/run_python.py --suite all | 864 PASS |
| F:/Python27/python.exe -B tests/run_python.py --suite runtime | 675 PASS |
| npm --prefix build_tools/javascript test | 25 suites PASS |
| npm --prefix build_tools/javascript run lint | PASS |
| python -B tests/run_python.py --suite artifacts --wotmod build/debug/beta/0.1.8-beta.2/driftkings.wotmod | 5 PASS |
| validate_build_data.py | PASS: 39 manifests, 307 módulos, 317 assets, 54 defaults, 2 dependências |
| validate_locales.py | PASS: 18 locales, zero não traduzidos |
| generate_defaults.py --check | PASS, sem geração em escrita |
| check_undefined_names.py | PASS, zero nomes indefinidos |
| git diff --check | PASS |

As suites existentes incluem identidade, seis ordens dos três plugins, crew.js real, getRow, eventos, serialização, ownership, CrewDetails, falhas recuperáveis e artefactos. Mensagens de falha deliberada nas suites são fault injection isolada, não falhas do CT. Não foram alterados testes ou acrescentados novos nesta auditoria.

### Validação funcional real comunicada pelo autor

| Cenário | Resultado | Fonte |
|---|---|---|
| Progressão visível nos tooltips | PASS | Utilizador, pedido de auditoria final |
| XP e estimativas de batalhas corretos | PASS | Utilizador |
| Troca de veículos sem dados antigos/trocados | PASS | Utilizador |
| Ativar/desativar progressão e tooltips | PASS | Utilizador |
| Carrossel e CrewDetails normais | PASS | Utilizador |
| Relógio, hidePrestige e marcas normais | PASS | Utilizador |
| Três ciclos garagem/batalha/garagem sem duplicações | PASS | Utilizador |
| Botão Driftkings, configurações e restantes módulos | PASS | Utilizador |

Estas oito confirmações foram aceites sem solicitar repetição. O encerramento adicional foi realizado pelo autor para completar a leitura do log, sem repetir essa checklist. Não se converte esta confirmação em evidência automática de fábrica/init/destroy do loader.

### Instalação, backup e decisão

Local e instalado: SHA-256 `7c50836f5f53eaf97a8c3a63433cc71e6889089b4d50b8fd98770888477ad89c`, 13 596 155 bytes, 625 entradas. Comparação integral de conteúdos local/instalado idêntica. Três entrypoints presentes, sem gui/gameface/js/index.js global. Cinco testes de artefactos confirmam os recursos protegidos e bundles dos patches contra a referência Fase 3C. OpenWG 1.2.2 e ModsListAPI 1.8.0 presentes e com os hashes declarados.

Backup independente da instalação: build/backups/ct-phase3d-install-20261109T115513440506Z/fase3c-09b70a3b4a48194514393fa1f7cae1b7281a42434d1cbae9b78ce064cf4c9bec.wotmod — 13 584 784 bytes, hash integral `09b70a3b4a48194514393fa1f7cae1b7281a42434d1cbae9b78ce064cf4c9bec`, novamente verificado. Rollback localizado documentado abaixo permanece disponível; não foi executado. A comparação histórica de instalação dos 706 ficheiros não foi repetida após o jogo escrever logs/configurações; nesta auditoria não houve escrita no CT.

| Área | Decisão |
|---|---|
| Validação funcional | PASS — oito confirmações do autor |
| Integridade de instalação | PASS — hashes, inventário e backup |
| Testes automáticos | PASS — nova execução |
| Serviços e registo Python | PASS — estados efetivamente registados |
| Falhas do bridge/plugins no material disponível | SEM ERRO IDENTIFICADO |
| Lifecycle de contrato | PASS nos testes; operação/transições confirmadas pelo autor |
| init/destroy JS e libertação interna em runtime | PENDENTE de observabilidade; não comprovados individualmente |
| Teardown Scaleform Lobby | PENDENTE de atribuição/investigação do erro da linha 5561 |

**FASE 3D FUNCIONALMENTE VALIDADA — AUDITORIA TÉCNICA PENDENTE.** Não existe regressão causal identificada que permita classificar a fase como bloqueada por código, mas não se aprova como encerramento técnico satisfatório um erro de alocações ainda não explicado.

Próximo passo recomendado, sujeito a nova autorização: reproduzir o encerramento com uma sequência controlada equivalente e, se necessário, comparar com a build Fase 3C preservada, mantendo mods/configurações e condições comparáveis. Uma comparação exigindo reinstalação/rollback não está autorizada nesta tarefa. Identificar recorrência e owner antes de propor correção. Nenhum commit é autorizado; eventual encerramento Git apenas após resolver/classificar a pendência e nova autorização explícita. Não iniciar Fase 3E. Limites de importação/promise retida e de recursos pendentes documentados anteriormente continuam válidos.

## Gates revalidados antes da implementação

Workspace limpo, staging vazio e dois plugins existentes preservados. Hashes CT confirmados: lib.js `392787b879bf47f1b2e3194cd6045286105a9756c3f26c8787f543f836b12051`; bundle.js `7e28391b4c51daa555b04d103a4031f7734b8d0728df03f7b73b47fa781873e5`.

O SDK usa `Symbol.for(url.split("mono/")[1] || "unknown")`. URL aprovada por contrato: `coui://gui/gameface/mods/driftkings/mono/driftkings/crew_progression/crew_plugin.js`. Caminho físico no pacote: `res/gui/gameface/mods/driftkings/mono/driftkings/crew_progression/crew_plugin.js`. Identidade `driftkings/crew_progression/crew_plugin.js`, distinta de unknown (relógio) e driftkings/hangar_marks/marks_plugin.js (marcas). Sem alias virtual, recurso nativo substituído ou dependências entre plugins. A importação efetiva do novo recurso continua dependente de validação CT.

CrewView pertence ao RandomHangar. O consumidor getRow está no bundle nativo desse documento; os argumentos são serializados por useParamTooltip e publicados em ParamTooltipModel.params no documento separado do tooltip. Os patches carousel_2.4.2_ct.json e crew_tooltip_2.4.2_ct.json são preservados. CrewDetails conserva modelo OpenWG e o mesmo controlador/registo partilhados. A View da progressão já remove apenas a sua entrada quando ainda é o owner; não é necessário alterar esse controlador.

## Rollback preparado antes da migração

Sem executar automaticamente: preservar os diffs; repor payload_model(FEATURE) apenas no adaptador da progressão e remover apenas os seus hooks de descriptor; retirar campos transport/plugin exclusivamente do contrato CrewProgression; retirar entrypoint e inventário/lint específicos; repor apenas as adaptações de crew.js; reconciliar testes de contagens e regenerar bootstrap pelo comando oficial. Não restaurar ficheiros partilhados completos sobre trabalho posterior. Preservar relógio, marcas, launcher, carrossel, CrewDetails, patches, perfis e configurações. Sem reset/clean/stash. Antes de substituir a build local, preservar o pacote Fase 3C por hash. Qualquer instalação/rollback CT exige autorização separada.

## Arquitetura e ficheiros

Três plugins independentes. Apenas o transporte de DriftkingsCrewProgression mudou; 22 contratos: duas janelas próprias, três nativos e 17 OpenWG. CrewDetails, carrossel e launcher continuam OpenWG; as duas dependências externas permanecem na distribuição. Sem agregador, framework genérico ou nova ponte entre documentos.

| Ficheiro | Responsabilidade |
|---|---|
| gameface/lobby/crew_progression.py | native_payload_model e descriptor próprio no UserMissionsPresenter; restantes funções preservadas |
| interface_catalog.py | transport/plugin exclusivamente da progressão |
| crew_progression/crew.js | Mesma API/evento, com lifecycle, validação de snapshot e guardas locais |
| mono/driftkings/crew_progression/crew_plugin.js | Novo entrypoint ES module, estados, carga e descarte próprios |
| generate_ui_catalog.py, components.json, eslint.config.cjs | Whitelist explícita de três consumidores, inventário e suporte ES module |
| shared/bootstrap.js | Alteração gerada: retira apenas a progressão do catálogo OpenWG |
| Testes de contagens existentes | Atualização de 18 para 17, preservando asserts dos consumidores legados |
| Testes novos | Catálogo/identidade, backend/controller/CrewDetails, API/eventos/JSON, três plugins/falhas e artefactos |

O backend mantém build_model, payload, publicação transacional, subscrições de veículo/cache, controller, configuração, install_card, CrewDetails.install e lifecycle de CrewView. O registo de Views continua partilhado: não existe clear/stop global novo. CrewView._finalize já remove apenas a sua entrada se ainda lhe pertencer. Os hooks de descriptor chamam o original, não substituem alias ocupado e removem apenas a instância publicada com a URL esperada. Não há dependências entre os três descritores ou fallback OpenWG.

As fontes de cálculos/recolha/apresentação Python, modelo HTML, relógio, marcas, launcher, carrossel, CrewDetails, patches e configurações mantêm-se sem alterações; testes comparam também com a baseline fa8c6990. A factory native_payload_model existente é reutilizada sem alterar gameface/core.py.

## API, evento e tooltip

`window.__dkCrewProgression.getRow(tankmanId)` continua a comparar `rows[i].id === id`. ID de inventário numérico, não slot; strings não são convertidas em números. A linha mantém slot/id/lines/kinds; ausência, estado invisível, indisponibilidade ou destruição devolvem null. Apenas linhas extraídas de JSON são devolvidas; funções, geração, DOM e recursos do owner não são serializados.

O frontend mantém snapshot substituído atomicamente e emite Event('dk-carousel-config'), sem payload, depois de atualizações, perda do modelo, inicialização necessária e retirada da API. Os slots releem o global. Ordem de inicialização invertida é tolerada pela guarda existente e pela leitura inicial; não há sincronização artificial entre plugins.

Percurso preservado: getRow → CrewSlot no documento hangar → argumentos tankman/dkCrewProgression/resId → useParamTooltip('crew_info', argumentos) → JSON.stringify → ParamTooltipView → ParamTooltipModel.params → documento mono/hangar/tooltips → lines/kinds. O tooltip não consulta o global. Os patches JSON e os bundles nativos resultantes são byte-equivalentes aos da build Fase 3C. Os testes de serialização verificam a extensão dkCrewProgression; não executam o renderer nativo real nem o schema completo de tankman do CT.

## Snapshots e invalidação localizada

Os testes criados antes da migração demonstraram uma condição na API antiga: um payload novo já publicado podia coexistir com a linha anterior em cache até ao evento. Agora getRow verifica se o binding ainda existe, se o modelo foi substituído e se payload difere da assinatura. Nesse intervalo retira o snapshot, devolve null e agenda uma releitura com notificação, sem alterar argumentos nem cálculos. Não apresenta a cache anterior como se correspondesse ao modelo novo já observado. Timers de releitura são cancelados quando um refresh direto os substitui.

Limite: vehicleId permanece no payload e o contrato não ganhou um segundo argumento obrigatório. Não existe uma nova ligação ao estado nativo do veículo. Se uma mudança do jogo ainda não se refletiu de todo no modelo da progressão, esta API não consegue detetá-la antecipadamente, em particular quando o mesmo invID é movido entre veículos. A ordenação real de cache, retorno automático, atualização e tooltip deve ser validada no CT; não se promete deteção de dados que o frontend ainda não recebeu.

## Estados, falhas e descarte

O módulo não tem imports estáticos opcionais nem efeitos na avaliação inicial. A fábrica devolve init/destroy, getState, getSnapshotState, getDiagnostics e getPendingResources. Estados de transporte: created, initializing, ready, failed, destroying, destroyed. Ready significa API ligada e disponível; snapshot é distinguido como waiting/empty/ready e torna-se unavailable no entrypoint quando a API é retirada. Ausência temporária do modelo é tolerada, sem falsificar dados.

O script publicado pode terminar antes de engine.whenReady. O entrypoint aguarda o callback de prontidão do bridge e a confirmação do owner da geração, além do evento load; não confunde script carregado com API pronta. Limite de espera de 10 segundos contém recursos/engine pendentes após o entrypoint executar. Erros recuperáveis marcam failed, registam causa, limpam e resolvem init com componente vazio válido para o loader. Um erro não é convertido em ready.

crew.js publica owner cedo; todos os callbacks verificam geração, estado e owner. A limpeza retira dados antes de tentar operações que possam falhar, tenta todas as remoções, cancela timers próprios, retira apenas o seu global e notifica depois. Referências antigas de getRow devolvem null. Falhas de APIs de limpeza são diagnosticadas; não existe garantia absoluta de libertação se o motor recusar a operação. O frontend não tem acesso nem chama stop/clear no controlador Python de CrewDetails.

Scripts clássicos pedidos podem executar tarde. Destroy invalida a geração e cancela o timer, resolve sem rejeição recuperável e mantém somente o retirement do pedido ainda pendente. Uma nova geração é recusada enquanto esse pedido não terminar. Contagem pendente e diagnóstico permanecem visíveis. Se load/error nunca chegar, a funcionalidade fica indisponível nesse contexto, sem retry automático ou cancelamento físico prometido.

Falhas do próprio import/sintaxe/avaliação do entrypoint não podem ser capturadas por código que não executou. O loader CT continua a poder reter promises rejeitadas por URL e a falhar na reconciliação de remoção. Não foi modificado, corrigido ou envolvido num handler global. O relógio e as marcas preservam os seus contratos validados e limites anteriores.

## Testes e fault injection

Resultados reais: 864 testes Python 3, 675 runtime Python 2.7, 25 suites frontend, lint e validadores aprovados. Grupo lobby com 86 testes também repetido em Python 3/2.7 após acrescentar a proteção contra finalização tardia sobre outra View. Cinco testes de artefactos aprovados após build.

Comandos: `python -B tests/run_python.py --suite all`; `F:/Python27/python.exe -B tests/run_python.py --suite runtime`; `npm --prefix build_tools/javascript test`; `npm --prefix build_tools/javascript run lint`; `python -B build_tools/validate_build_data.py`; `python -B build_tools/validate_locales.py`; `python -B build_tools/generate_defaults.py --check`; `python -B build_tools/check_undefined_names.py`; `git diff --check`.

- Backend real com serviços/Wulf isolados: mesmo payload, veículo/cache, configurações, duas subscrições, instalação de CrewDetails, stop/start/contexto e remoção individual. A implementação real protegida de CrewDetails é carregada e continua a publicar após remoção da CrewView; as suas Views permanecem no registo. Alias ocupado, substituição da mesma URL e resource inválido não removem os dois plugins existentes.
- crew.js real: strict ID/string/slot, ausência de API, snapshots vazios/invisíveis, payload novo antes do evento, substituição/perda do modelo, evento inicial/atualização/limpeza/descarte em ambas as ordens, JSON opcional e arrays de strings. Schema inválido, falha de discovery/subscrição e falhas de cleanup são diagnosticados, com API retirada e snapshot limpo.
- Os três entrypoints e renderers reais são executados num DOM simulado nas seis ordens de inicialização. CrewDetails frontend real protegido mantém apresentação e atualiza após falha/destruição da progressão; relógio, hidePrestige e marcas continuam ativos. Remoção individual e recriação preservam outros owners.
- Fault injection isolada: recurso ausente, erro sintático de renderer, erro síncrono de criação do script, promessa rejeitada de engine.whenReady, subscrição parcial após publicação da API, payload inválido/getter que lança, callbacks tardios, timeout, destroy durante carga, owner substituído, falha de unsubscribe/off e reentrada com geração antiga pendente. Nenhuma falha recuperável é enviada como rejeição ao loader.
- Harness existente identificado como MODELO DE CONTRATO, não loader CT real: import/URL/sintaxe/export/fábrica inválidos, init síncrono/rejeitado, destroy síncrono/rejeitado, colisão intencional, cache rejeitada e reconciliação bloqueada. Acrescentada execução dos três entrypoints através desse modelo, com três identidades e remoção individual.
- Patches são apenas lidos/consumidos pelo build oficial: ficheiros fonte preservados e output main/tooltips comparado byte a byte ao pacote Fase 3C; nenhuma alteração nos patches ou instalação real de falhas.

Estes resultados são testes de contrato, integração isolada e artefactos. Não são execução do loader/Gameface real no CT.

## Build debug CT

Referência Fase 3C preservada ANTES de substituir o caminho local: `build/reference/fase3c-09b70a3b4a48194514393fa1f7cae1b7281a42434d1cbae9b78ce064cf4c9bec.wotmod`, cópia verificada por SHA-256. O CT conserva o mesmo hash Fase 3C; não foi instalado o PoC novo.

Comando oficial: `python -B build_tools/compiler.py --mode debug --channel beta --version 0.1.8-beta.2 --keep-source-version --game-root C:/Games/World_of_Tanks_CT --reference-root E:/Wot_Mods_/Drift_Kings_ModPack/WoT_Tools/wot-src-CT`.

Artefacto: `E:/Wot_Mods_/Drift_Kings_ModPack/Driftkings_SettingsLab/build/debug/beta/0.1.8-beta.2/driftkings.wotmod`.

- Debug CT 2.4.2.0, pacote 0.1.8-beta.2; fonte mantém 0.1.8-beta.1, sem modificar release.json.
- Tamanho: 13 596 155 bytes; 625 entradas; 307 módulos Python, 317 assets e 54 defaults.
- SHA-256: `7c50836f5f53eaf97a8c3a63433cc71e6889089b4d50b8fd98770888477ad89c`.
- Inclui crew_plugin.js na URL física aprovada, crew.js, model.html e declaração Wulf; relógio e marcas originais; outros 17 consumidores, carrossel/CrewDetails/launcher e dependências preservados.
- Sem res/gui/gameface/js/index.js global, ficheiros de testes/fault injection ou configurações pessoais.
- `python -B tests/run_python.py --suite artifacts --wotmod build/debug/beta/0.1.8-beta.2/driftkings.wotmod` — cinco PASS.

## Critérios de aceitação

| Critérios | Estado e evidência |
|---|---|
| Terceiro descriptor, identidade, URL física, native model, exclusividade e ausência de dupla injeção | PASS técnico — backend, catálogo, testes e pacote; importação CT pendente |
| getRow, comparação estrita, formato e snapshot atual/limpeza | PASS nos testes reais do bridge; limite de mudanças ainda não publicadas documentado |
| Evento sem payload, ordem invertida e JSON lines/kinds opcional | PASS em integração simulada; tooltip visual CT pendente |
| Payload, cálculos, configurações, controlador e registo partilhado | PASS — proteção de baseline e backend real em ambiente isolado |
| CrewDetails, carrossel, patches, relógio, marcas, launcher e 17 OpenWG preservados | PASS de fonte/artefacto e regressão automática |
| Falhas recuperáveis, estado failed, diagnóstico, geração tardia, descarte e ausência de limpeza global | PASS no harness; falhas anteriores ao entrypoint e APIs nativas que recusem cleanup continuam limitadas |
| Python 3/2.7, frontend, fault injection, catálogo, packaging, build e rollback | PASS |
| Instalação CT e validação funcional real | PENDENTE — autorização separada necessária |

## Checklist CT futura e Git

Após autorização específica: confirmar pacote por hash, registo Python do terceiro plugin e telemetria JS quando disponível. Verificar tooltips de tripulantes com/sem progressão e slots vazios, valores/XP/batalhas/cores/traduções, ativar/desativar opções, veículos em sequência rápida, tripulante movido/retornado, tooltip aberto durante atualização, reentrada e três ciclos sem duplicações. Confirmar simultaneamente relógio/hidePrestige, marcas, launcher, carrossel, barracks, ficha pessoal e restantes CrewDetails. Ausência de erros Python não prova init/destroy JS.

HEAD permanece fa8c699000535276e12a08f1fb089ebd7783a26b, staging vazio, alterações locais exclusivamente desta fase. Sem commit/push, alterações de worktrees ou bibliotecas externas. O ciclo debug CT conserva a versão temporária 0.1.8-beta.2 e distingue builds pelo SHA-256, não só pela versão.

## Instalação controlada autorizada — 2026-11-09

Concluída às 11:55:42 UTC no cliente `v.2.4.2.0 Common Test #995`. Cliente encerrado, com processos verificados antes dos inventários, imediatamente antes da substituição e após a verificação final. Não foi iniciado o jogo. Nenhum código foi alterado, nenhuma nova build foi executada e não houve commit/push, release, tag ou avanço de fase.

Origem: `E:/Wot_Mods_/Drift_Kings_ModPack/Driftkings_SettingsLab/build/debug/beta/0.1.8-beta.2/driftkings.wotmod`. Destino: `C:/Games/World_of_Tanks_CT/mods/2.4.2.0 Common Test/driftkings.wotmod`. Origem e pacote instalado verificados integralmente com SHA-256 autorizado `7c50836f5f53eaf97a8c3a63433cc71e6889089b4d50b8fd98770888477ad89c`.

O destino anterior foi confirmado como Fase 3C, SHA-256 `09b70a3b4a48194514393fa1f7cae1b7281a42434d1cbae9b78ce064cf4c9bec`. Backup independente criado a partir do ficheiro instalado e novamente verificado após a instalação:

`build/backups/ct-phase3d-install-20261109T115513440506Z/fase3c-09b70a3b4a48194514393fa1f7cae1b7281a42434d1cbae9b78ce064cf4c9bec.wotmod`.

Inventários integrais do cliente, antes/depois, com SHA-256, tamanho e mtime: 706 ficheiros em ambos. Única diferença: `mods/2.4.2.0 Common Test/driftkings.wotmod`. OpenWG 1.2.2, ModsListAPI 1.8.0, configurações e restantes mods preservados; dependências também reconfirmadas pelos hashes fixados. O pacote tem 625 entradas, inclui os três entrypoints nativos e não inclui res/gui/gameface/js/index.js global ou ficheiros de testes. Presença no pacote não equivale a execução real dos três plugins.

Relatório PASS, caminhos, hashes e manifestos guardados junto ao backup em `installation-report.json`, `before.json` e `after.json`. A validação funcional permanece exclusivamente pendente do teste do autor no CT.
