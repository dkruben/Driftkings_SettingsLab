# Fase 3F.2A — Native BattleInfo Extension Integration

**SOURCE INTEGRATION PASS**, limitado a origem, testes e auditoria estática. Referência CT 2.4.2.0 Common Test #995. Branch `feature/wot-2.4.2-ct`; HEAD preservado `769c81d10e7fc4707ee2ffe6d7003a060d40486b`.

## A–B — Preflight e inventário

Working tree e staging inicialmente vazios; baseline de 1058 ficheiros em `build/diagnostics/phase3f2a/20261109T231011Z/baseline.json`. Worktrees e refs preservados; entradas prunable preexistentes não foram reparadas. Inventário final abaixo, incluindo ajustes estritamente necessários às expectativas históricas dos testes.

## C–D — Core e adapter

`native_extension_core.js` transporta o core hardened 3F.1D: sessões/gerações, cancelamento lógico, ResourceScope, rollback parcial e Promise única de retirada por owner. A Promise é registada antes de chamar destroy. RETIRING mantém-se até terminar; falhas produzem CLEANUP_FAILED e diagnóstico, sem impedir os outros disposers. Sem React, Wulf, payload funcional ou registry global no core.

O adapter específico BattleInfo usa React, ErrorBoundary e slots com identidade estável. O patch acrescenta uma sexta zona e preserva integralmente os cinco filhos oficiais. Só existe um consumidor real: eficiência. Dois consumidores independentes são exercitados apenas em testes. Nenhum pathToPlugins, loader Mission Progress substituído ou index.js global alterado.

## E — AST e pipeline

Acorn 8.19.0 fixado como ferramenta de desenvolvimento. Gerador opt-in `native_battleinfo_patch`; `replace_exact` preservado. Seleção inequívoca do recurso, hash de entrada, contexto CT #995, âncora estrutural única, hashes dos inputs runtime normalizados LF, parser/output verificados. Reaplicação, contexto desconhecido, recurso ambíguo, hashes incorretos e âncoras ausentes/duplicadas rejeitados. Transformação integral em memória, parse posterior e reversão exata antes de disponibilizar output. Nenhum output parcial.

SHA-256 original: `0857328db3a7e880b48c1785c77acd24e436d8862cd47c3ea41b52ef96059267`.

SHA-256 output integrado em memória: `fdb10d97190bb9ba4600f59826b3515c8235c54a0aaa77a2ff138e3b520118a2`.

Difere do output laboratorial `d2ab64bdea2600b14f6b6bb773abceb6375d5edc9aa56851b4fff076c7e7b7fd`: adapter real, um consumidor real, factory FlashText privada e módulos integrados. O núcleo mantém os mecanismos hardened; o harness laboratorial não foi incorporado no cliente. A opção de autoria verifyOutput=false só calcula o hash esperado em testes/autoria; o pipeline exige verificação completa.

## F–G — Transporte e binding

ResultsModel usa native_payload_model com transporte explícito native_battle_results, duas propriedades e zero comandos. Payload enabled/html, cálculos, macros, deduplicação, serviço, eventos funcionais e HUD preservados. Três plugins anteriores continuam sem comandos; carrossel preserva o seu comando existente.

Binding identifica resource ID, referência do child/model e geração local; invalida o anterior e limpa dados antes da substituição. Eventos tardios verificam token e modelo vivo. Remoção, recriação, troca de batalha, disabled, reabertura e unsubscribe são exercitados com serviços simulados.

## H–I — Renderer e recursos

Renderer usa exclusivamente o contentor React atribuído, preservando ID dk-battle-efficiency, HTML, separadores e opções FlashText. CSS, fonts.css e flash_text.js originais não foram modificados. O helper existente é emprestado quando disponível; caso contrário, uma factory lexical privada encapsula o mesmo helper original, sem criar/substituir/apagar globais. CSS tem leases por documento/URL, aquisição parcial com disposer pré-registado, referência partilhada e empréstimo não destrutivo de links externos. Cancelamento retira o registo pendente, permitindo reentrada.

## J–K — Isolamento e catálogo

Apenas results deixa o bootstrap OpenWG. Catálogo de origem: 5 nativos, 15 OpenWG, 2 janelas próprias; beta.3 instalada continua 4/16/2. Quatro plugins anteriores, CrewDetails, HUD, launcher, Settings Panel, configurações, CSS/fontes/helper e patches antigos preservados. Plano estático: 39 manifestos, 307 Python, 324 assets, 54 defaults e 2 dependências. EntryPoint results_extension.js e módulos locais incluídos; ferramentas npm não entram no pacote. Bundle pendente de geração é esperado e não foi produzido.

## L–O — Verificações executadas

| Verificação | Resultado |
| --- | --- |
| python -B tests/run_python.py --suite all | 879 PASS, 0 FAIL, 0 SKIP |
| Python 2.7, tests/run_python.py --suite runtime | 682 PASS, 0 FAIL, 0 SKIP |
| node tests/run_frontend.js | 27 suites PASS; nova suite com 13 grupos |
| npm --prefix build_tools/javascript run lint | PASS, zero warnings |
| Catálogo, build data e nomes indefinidos | PASS; bundle novo pendente, nomes indefinidos 0 |
| git diff --check | PASS |

Logs em build/diagnostics/phase3f2a/20261109T231011Z. Execução inicial de build tests teve duas falhas nas expectativas históricas de build_config; corrigidas para exigir configuração antiga integralmente igual após retirar apenas o novo gerador. Primeiro harness frontend tinha document ausente; fixture corrigida. Execuções finais aprovadas. Python all não inclui a suite artifacts. Não se reclama PASS de empacotamento nem de novo .wotmod. O ensaio AST usa buffers e fixtures .pkg temporárias, sem distribuição. React/test-renderer 19.2.3 locais; cache de laboratório lida sem alterações, instalação tooling offline. Sem dependências do cliente instaladas.

## P–Q — Limitações e decisão

SOURCE INTEGRATION PASS não equivale a validação CT. Import relativo/coui, proxies reais Wulf, layout/fontes, renderer visual, engine e lifecycle real precisam de validação 3F.2B. Node VM mapeia imports para módulos reais integrados; React tem a mesma versão numérica do laboratório, sem equivalência demonstrada ao ambiente do jogo. Mission Progress preservado em cinco fixtures; não se reclama observação real nesta fase. Promises do loader externo não podem ser fisicamente canceladas; callbacks tardios são invalidados logicamente. Aviso Scaleform 3D.1 em observação, causa não determinada; não se declara ausência absoluta de fugas.

Rollback conceptual: mediante autorização futura, retirar apenas estas alterações de origem e restaurar catálogo/bootstrap/gerador anteriores; antes de qualquer futura instalação criar backup verificável. Nenhum rollback ou alteração CT foi executado. A beta.3 atual não necessita de rollback nesta fase.

## R–S — Integridade e entrega

Pacote beta.3 local e instalado preservado: `f0ff0cde074b25e0ee5d3f3c0647c870d01a85e6c8dfb8ed5b17bdf0709259a8`.

Backup 3D preservado: `7c50836f5f53eaf97a8c3a63433cc71e6889089b4d50b8fd98770888477ad89c`.

Sem build/distribuição, instalação, início CT, staging, commit, push, tag ou release. HEAD, main/develop e worktrees preservados. Fontes CT relevantes somente leitura; original verificado por hash. Evidência final e hashes individuais: `build/diagnostics/phase3f2a/20261109T231011Z/final-manifest.json`. Working tree conserva a implementação para revisão.

## Seguimento — Fases 3F.2B, 3F.2C e 3F.2D-FIX — 2026-11-10

Este relatório descreve a Fase 3F.2A; as pendências de build e de validação CT nele indicadas foram entretanto tratadas. Build experimental `0.1.8-beta.4` com **ARTIFACT PASS**, instalação controlada e **CT RUNTIME PASS** no CT #995: ver [STATUS.md](STATUS.md). Continuam por testar o estado sem dados e a extensão desativada, e o lifecycle JavaScript no Gameface real não foi instrumentado.

Alterações de teste da 3F.2D-FIX, sem mudança funcional na integração: `tests/build/test_native_results_source.py` deixou de usar `git show` e compara com `tests/fixtures/native_baselines.json` (através de `tests/support/baselines.py`); ganhou um teste dos pré-requisitos Node.js/`acorn` e um teste opcional do patch AST real sob output isolado. `build_tools/validate_build_data.py` verifica Node.js e o `acorn` fixado antes de executar o patch, com a mensagem `npm --prefix build_tools/javascript ci --ignore-scripts`. O inventário abaixo é o da Fase 3F.2A; estes dois ficheiros novos de suporte de testes não constam dele.

## Inventário exato — 33 caminhos (22 modificados, 11 novos)

- `build_data/build_config.json`
- `build_data/components.json`
- `build_data/patches/battle_results_2.4.2_ct.json`
- `build_tools/compiler.py`
- `build_tools/generate_ui_catalog.py`
- `build_tools/javascript/package-lock.json`
- `build_tools/javascript/package.json`
- `build_tools/native_battleinfo_patch.cjs`
- `build_tools/validate_build_data.py`
- `docs/CT_COMPATIBILITY.md`
- `docs/NATIVE_BATTLE_RESULTS_POC.md`
- `docs/STATUS.md`
- `eslint.config.cjs`
- `mod/res/gui/gameface/mods/driftkings/battle_performance/battleinfo_adapter.js`
- `mod/res/gui/gameface/mods/driftkings/battle_performance/results.js`
- `mod/res/gui/gameface/mods/driftkings/battle_performance/results_binding.js`
- `mod/res/gui/gameface/mods/driftkings/mono/driftkings/battle_results/results_extension.js`
- `mod/res/gui/gameface/mods/driftkings/shared/bootstrap.js`
- `mod/res/gui/gameface/mods/driftkings/shared/native_assets.js`
- `mod/res/gui/gameface/mods/driftkings/shared/native_extension_core.js`
- `mod/res/scripts/client/driftkings/gameface/core.py`
- `mod/res/scripts/client/driftkings/gameface/lobby/battle_performance.py`
- `mod/res/scripts/client/driftkings/interface_catalog.py`
- `tests/artifacts/test_native_marks_package.py`
- `tests/build/test_native_carousel_catalog.py`
- `tests/build/test_native_clock_catalog.py`
- `tests/build/test_native_crew_catalog.py`
- `tests/build/test_native_hangar_marks_catalog.py`
- `tests/build/test_native_results_source.py`
- `tests/frontend/lobby/test_native_results.js`
- `tests/runtime/lobby/test_native_carousel.py`
- `tests/runtime/lobby/test_native_clock.py`
- `tests/runtime/lobby/test_native_results.py`
