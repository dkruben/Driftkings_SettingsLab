# Migração final dos consumidores OpenWG — fonte

Production NA #999 passed file-level checks for the bundled exact and BattleInfo AST patches against actual installed game resources. The native vehicle-marker SWF differs from CT #996. [Resource evidence and runtime scope](releases/0.1.7-beta.2-readiness.md).

Data: 2026-11-11. Cliente: CT 2.4.2.0 #995.

> Nota de leitura — 2026-11-15: este corpo conserva o relatório histórico da
> migração de fonte no CT #995. Referências a trabalho «por commitar», testes
> pendentes e ausência de build descrevem essa execução, não o estado após C6.
> A atualização final deste documento e a secção 43 do
> [progresso](plans/DRIFTKINGS_REORGANIZATION_PROGRESS.md)
> distinguem a implementação atual das evidências históricas.

Veredicto: **OPENWG MIGRATION SOURCE PASS**.

## Estado preservado

Commit local beta.8: `bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3`.
Mensagem: `feat(gameface): migrate remaining battle HUD components to native shared window`.
Os 14 ficheiros foram confirmados contra os hashes do preflight beta.8 antes do commit;
staging e working tree ficaram limpos nesse ponto. A validação beta.8 em replay foi comunicada
pelo utilizador; a confirmação em batalha real continua pendente devido ao servidor CT.

## Inventário direcionado e mecanismo por consumidor

Todos usavam `payload_model`/`attach_assets`, que acrescentavam `DriftkingsUI` e pediam
`gf_mod_inject` para carregar `shared/bootstrap.js`. As views Wulf e os renderers já existiam.

| Consumidor | Entrada e lifecycle existentes | Dados/configurações | Renderer preservado | Estado/mecanismo |
|---|---|---|---|---|
| `DriftkingsFooterLauncher` | `FooterLauncher.start/stop`; `LobbyFooter._initChildren` e quatro variantes; `LauncherView._finalize` | Contexto `GuiGlobalSpaceID.LOBBY`, título e comando `onOpen` do controlador das definições | `launcher/launcher.js`, `launcher.css`; âncora `Footer_section_*` antes do menu | `native_document`: modelo Wulf sem injeção e assets no HTML nativo do footer. Sem novo botão/fallback fora do footer |
| `DriftkingsProfileRatings` | `AchievementMainView._onLoading`, `SummaryView.__updatePage`; subscrição de definições desligada em `_finalize` | Dossier RandomStats, escala e opções `profile_ratings`; valores oficiais preservados | `profile_ratings/ratings.js`; cores nas estatísticas oficiais | `native_document`: HTML de `AchievementsMainView` |
| `DriftkingsCrewDetails` | `_onLoading`/fill das quatro views, `itemsCache.onSyncCompleted`, referências fracas e limpeza em `_finalize` | Seleção do tripulante, XP/progressão, opções e traduções `crew_management` | `crew_details/details.js`, `details.css`; mesmas âncoras e IDs dos cartões | `native_document`: HTML de BarracksView, TankmanTooltip, PersonalFileView e ServiceRecordView |
| `DriftkingsHangarHeaderOptions` | `LobbyHeader._getChildComponents`, `_onLoading`, alteração de enabled e desconexão em `_finalize` | `hangar_preferences`, visibilidade premium/WoT Plus e expiração premium do itemsCache | `hangar_preferences/header_options.js`; mesmos elementos premium/WoT Plus | `native_document`: HTML nativo do header |
| `DriftkingsMarksOnGunTechTree` | `TechTreeView._onLoading`, fill/updateNodeOverrides e `_finalize`; cache/seleção existente | `tech_tree_marks_of_excellence`, IDs e estados dos veículos, marcas/mestria | `tech_tree_marks_of_excellence/marks.js`, `marks.css`, `shared/marks_tokens.css` | `native_document`: HTML nativo da árvore tecnológica |
| `DriftkingsRatingPlayers` | `GamefaceLoading`; TabView loaded/shown/hidden/finalize; hook sazonal removido | `team_panels`, roster por modo, visibilidade e comando `onPerformance` | `panel_gameface/ratings.js`, `rating_rows.js`, `shared/rating_text.js` | `native_document`: documento do TAB clássico; suporte específico Halloween removido por autorização do responsável |

## RatingPlayers concluído — remoção sazonal autorizada

O responsável autorizou a remoção do suporte Halloween exclusivamente no RatingPlayers.
O TAB usa `gui/gameface/_dist/production/battle/battle_page/TabView/TabView.html`, recurso
verificado nos pacotes CT #995. O patch exato acrescenta apenas os três scripts retidos:
`shared/rating_text.js`, `panel_gameface/rating_rows.js` e `panel_gameface/ratings.js`,
com carregamento defer e uma única ocorrência por documento.

O ponto Wulf mantém `TabView._onLoaded`, `_onShown`, `_onHidden` e `_finalize`.
O modelo independente conserva `DriftkingsUI`, payload JSON e o comando `onPerformance`.
A aplicação mantém a ordem dos IDs do playerList nativo e os cálculos/formatos anteriores.
Carregamentos repetidos não criam um segundo filho, e views de outros contextos não são substituídas.
Ao remover o modelo, o renderer liberta o callback e restaura os elementos oficiais; no unload
cancela o timer, desconecta listeners/observer e limpa os overlays. Reabertura e duas batalhas
foram exercitadas em testes isolados.

Ramos sazonais removidos:

- `EXTENSION_TABS`, resolução tardia/watch de `halloween...TabScreen`, estado hookOwner/watched
  e construção do payload `hwTab` no adaptador Gameface.
- Construção das linhas `summary` e a chamada watch em `flash/battle/player_ratings.py`.
- O valor TAB do adaptador Halloween passou a `None`; a classificação do evento, os dados,
  a ordenação, as regras de estatísticas e os outros componentes sazonais permanecem.
- `panel_gameface/halloween_tab.js`, os seus ramos no renderer e a entrada de assets no catálogo.
- Os testes exclusivos do renderer/TAB Halloween foram substituídos por testes do TAB nativo;
  os testes sazonais de outros módulos mantêm-se. As expectativas de TAB sazonal passaram
  legitimamente a exigir ausência de linhas, sem alterações aos baselines históricos.

Os modos que já usam o TAB clássico, incluindo random e fort_rush/Black Signal, mantêm essa
integração. Stronghold/Flash e Frontline mantêm os respetivos adaptadores anteriores.

## Alteração mínima

- Reutilização do gerador existente `gameface_patch` / `replace_exact`: nove patches específicos
  com SHA-256 de entrada e saída e correspondência exata de uma ocorrência de `</body>`.
- Cada patch acrescenta os links CSS e os scripts `defer` declarados no catálogo, uma vez e em ordem.
  O resto do documento nativo é preservado byte a byte; buffers divergentes são recusados.
- As entradas `native_document` incluem os documentos exatos. A validação cruza identidade,
  gerador, assets e alvos do pacote. Os nove assets gerados foram declarados nos componentes próprios.
- `payload_model` seleciona o modelo nativo já existente para esse transporte. A importação
  OpenWG passa a acontecer apenas dentro de `attach_assets`, quando há um consumidor OpenWG.
- Sem alterações aos nove HUD, ao documento `battle_statistics/model.html`, aos cinco consumidores
  migrados anteriormente e respetivos patches, ou aos cinco plugins nativos anteriores. O renderer
  RatingPlayers só perdeu os ramos sazonais e ganhou a limpeza do callback após remoção do modelo.
- A geração dos novos documentos ocorrerá apenas numa build futura autorizada. Nesta execução
  os patches foram aplicados em memória para teste, sem compilar ou instalar.

## Validação

- Uma execução completa Python 3: 936 testes; 1 ignorado e uma expectativa sazonal antiga falhou.
- Uma execução completa runtime Python 2.7: 691 testes; a mesma expectativa sazonal antiga falhou.
- A única falha esperava seis linhas TAB Halloween. Foi corrigida para exigir zero linhas, conforme
  a remoção autorizada, e o ficheiro foi retestado: 8 testes PASS em Python 3 e 8 PASS em Python 2.7.
  Todos os restantes testes das execuções completas passaram. Não se repetiu a regressão completa.
- isort identificou uma linha em branco nos imports do adaptador alterado; foi corrigida, sem mudança
  de comportamento, e a verificação integral isort passou.
- Frontend: 29 suites, OK.
- ESLint, isort em UTF-8, catálogo, 332 assets, defaults, JSON, 18 locales e diff --check: PASS.
- Novos testes verificam 20 modelos/commands sem importar ou chamar OpenWG, incluindo o TAB,
  todos os buffers reais do CT, rejeição de hashes incorretos e cobertura exata dos nove documentos.
- Testes frontend executam os renderers originais a partir das tags dos patches, verificando
  âncoras, clique, cores, tripulação, seleção de veículos, remoção do modelo e limpeza no unload.
- Baselines históricos e hashes anteriores não foram alterados.

Catálogo real: **20 nativos / 0 OpenWG / 2 janelas próprias do lobby**.
Nenhum dos 20 consumidores nativos importa OpenWG ou pede `gf_mod_inject` ao criar os modelos
nos testes. O bootstrap gerado não lista consumidores. O helper legado de injeção e a deteção
passiva de compatibilidade continuam presentes, mas não são usados pelos 20 consumidores.
ModsListAPI, ModsSettingsAPI e os pacotes externos instalados permanecem preservados e fora do âmbito.

## Riscos para validação CT posterior

1. Ordem de inicialização real dos scripts defer e dos bundles nativos nos nove documentos.
2. Footer padrão, Comp7, Comp7Light, Last Stand e Battle Royale: um botão, âncora correta,
   hover/clique e estado de visibilidade, sem fallback fora do footer.
3. Perfil: abrir/fechar, mudar de página e ativar/desativar cores sem valores substituídos.
4. Tripulação: trocar tripulante, filtros/paginação do quartel, tooltip, ficha pessoal e histórico;
   ausência de linhas duplicadas e atualizações corretas de XP.
5. Cabeçalho: opções premium/WoT Plus, expiração e restauração da visibilidade.
6. Árvore: mudar nação/seleção e atualizar veículos; marcas, mestria e cores sem badges pendentes.
7. TAB: abrir/fechar várias vezes, aliados/inimigos e ordem nativa, cores, nomes, valores,
   estatísticas, ícones, campos adicionais, hover e teclado; testar random e fort_rush quando disponíveis.
8. Duas batalhas: sem duplicações, overlays invisíveis, listeners/timers pendentes ou degradação
   de desempenho; preservar os nove HUD beta.8 e a visibilidade oficial.
9. Confirmar a ausência intencional de modificações RatingPlayers no Halloween, se o evento regressar.
10. Os patches são específicos do CT #995; outros buffers devem falhar na verificação, sem fallback silencioso.

Não foi criada build, efetuada instalação, removido pacote externo ou criado commit destas novas migrações.

## Ficheiros desta implementação — inventário histórico anterior ao C1

- `build_data/build_config.json`
- `build_data/components.json`
- `build_tools/generate_ui_catalog.py`
- `mod/res/gui/gameface/mods/driftkings/panel_gameface/halloween_tab.js`
- `mod/res/gui/gameface/mods/driftkings/panel_gameface/ratings.js`
- `mod/res/gui/gameface/mods/driftkings/shared/bootstrap.js`
- `mod/res/scripts/client/driftkings/core/mode_adapters.py`
- `mod/res/scripts/client/driftkings/flash/battle/player_ratings.py`
- `mod/res/scripts/client/driftkings/gameface/battle/panel_gameface.py`
- `mod/res/scripts/client/driftkings/gameface/core.py`
- `mod/res/scripts/client/driftkings/interface_catalog.py`
- `tests/build/test_native_carousel_catalog.py`
- `tests/build/test_native_clock_catalog.py`
- `tests/build/test_native_crew_catalog.py`
- `tests/build/test_native_hangar_marks_catalog.py`
- `tests/build/test_native_results_source.py`
- `tests/build/test_own_window_catalog.py`
- `tests/frontend/battle/test_halloween_tab.js`
- `tests/frontend/battle/test_own_battle_window.js`
- `tests/runtime/battle/test_halloween_panel.py`
- `tests/runtime/battle/test_halloween_tab.py`
- `tests/runtime/battle/test_mode_adapters.py`
- `tests/runtime/battle/test_own_battle_window.py`
- `tests/runtime/battle/test_team_rosters.py`
- `tests/runtime/lobby/test_native_carousel.py`
- `tests/runtime/lobby/test_native_clock.py`
- `tests/runtime/lobby/test_native_crew_runtime.py`
- `tests/support/__init__.py`
- `tests/support/rosters.py`
- `build_data/patches/native_document_crewdetails_0_2.4.2_ct.json`
- `build_data/patches/native_document_crewdetails_1_2.4.2_ct.json`
- `build_data/patches/native_document_crewdetails_2_2.4.2_ct.json`
- `build_data/patches/native_document_crewdetails_3_2.4.2_ct.json`
- `build_data/patches/native_document_footerlauncher_0_2.4.2_ct.json`
- `build_data/patches/native_document_hangarheaderoptions_0_2.4.2_ct.json`
- `build_data/patches/native_document_marksonguntechtree_0_2.4.2_ct.json`
- `build_data/patches/native_document_profileratings_0_2.4.2_ct.json`
- `build_data/patches/native_document_ratingplayers_0_2.4.2_ct.json`
- `docs/openwg-native-migration.md`
- `tests/build/test_native_document_catalog.py`
- `tests/frontend/battle/test_native_rating_tab.js`
- `tests/frontend/lobby/test_native_documents.js`
- `tests/runtime/battle/test_native_rating_tab.py`
- `tests/runtime/lobby/test_native_documents.py`

## Estado após C6 — atualização documental de 2026-11-15

C1–C6 estão commitados localmente em `reorganization/settingslab`; C7 está apenas
em preparação, sem commit. Não houve integração em `develop`, push ou release.
O histórico exato e as limitações estão na secção 43 do progresso referido acima.

O catálogo mantém **20 nativos / 0 consumidores OpenWG / 2 janelas próprias do lobby**:
nove cartões `own_window`, seis consumidores `native_document`, quatro
`native_user_missions` e um `native_battle_results`. Os nove HUD partilham uma janela
Wulf com host neutro `BATTLE_HUD_HOST`, recurso `mods/driftkings/battle_hud/window`,
com nove modelos independentes. Não são nove janelas e o host não pertence a um cartão.
Os sete componentes Flash do catálogo continuam presentes; não foram todos migrados.

C1 integrou as superfícies nativas e o host; C2 normalizou seis nomes internos AS3;
C3 integrou teardown Flash recuperável e cinco guardas de callbacks antigos;
C4 integrou o SVG DK e os seus estados; C5 integrou identidade e bridges CT #996;
C6 integrou o workspace curto. Os contratos payload, comandos, posições e renderers
mantêm as responsabilidades existentes; inicialização e destruição são exercitadas
pelos testes de cada superfície, sem garantia absoluta de libertação em todos os modos.

A referência atual é CT 2.4.2.0 #996, revisão 2660091. Carrossel, Crew Tooltip e
vehicle markers selecionam variantes/locks explícitos #995/#996; builds desconhecidas
são recusadas sem fallback silencioso. Os nove documentos HTML mantêm pins históricos
#995 e hashes exatos: não são retagados nem aceitam buffers divergentes por aproximação.

O helper legado de injeção e a deteção de compatibilidade continuam no código;
OpenWG não foi eliminado integralmente do modpack. ModsListAPI, ModsSettingsAPI e
pacotes externos instalados permanecem preservados. A independência runtime sem
OpenWG continua por demonstrar; a contagem do catálogo não prova essa independência.

O runtime beta.10 no CT #996, incluindo dois combates, foi comunicado pelo responsável
e consolidado em F7-G3, com limitações. Não houve nova build nem runtime na preparação
dos commits. EU, release pública e integração em `develop` continuam pendentes.
