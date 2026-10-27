# Plano local — centralização Python Flash/Scaleform

## Âmbito e ponto de partida

- Branch `develop`, base `abe544ceb7c5dc67cd7bb868fc08631d929f6a02`; árvore local limpa na auditoria.
- Registar cada etapa neste ficheiro, validar antes do commit e fazer push. Preservar alterações externas que apareçam durante a execução.
- Separar Python por tecnologia; preservar identificadores AS3, aliases, métodos DAAPI, payloads, recursos, configurações e ordem de inicialização. Python 2.7/3.
- Não mover nem editar AS3/SWF/fontes/gráficos/configuração de compilação. Não publicar release nem instalar no EU. Gameface só pode mudar se houver dependência real.
- Não alterar frequências nem aplicar throttling. Não afirmar melhoria de FPS sem medições no cliente.

## Auditoria anterior à migração

### Dez contratos e utilização runtime

| Alias | Classe Python atual | AS3 preservado | Origem e utilização |
| --- | --- | --- | --- |
| `ArmorCalculatorView` | `driftkings.views.battle.penetration_indicator.ArmorCalculator` | `driftkings.battle.components.armor_calculator.armorcalculatorui` | `battle.penetration_indicator`: getBattleViews, registado pelo Core; superfícies battle |
| `DispersionTimerView` | `driftkings.views.battle.aiming_countdown.DispersionTimer` | `driftkings.battle.components.dispersion_timer.dispersiontimerui` | `battle.aiming_countdown`: getBattleViews, registado pelo Core; superfícies battle |
| `DistanceMarkerView` | `driftkings.views.battle.target_distance.DistanceMarkerView` | `driftkings.battle.components.distance_marker.distancemarkerui` | `battle.target_distance`: getBattleViews, registado pelo Core; superfícies battle |
| `DriftkingsDebugPanel` | `driftkings.views.battle.debug_panel.DebugPanelView` | `driftkings.battle.components.debug_panel.debugpanelui` | `battle.battle_preferences`: getBattleViews, registado pelo Core; superfícies battle |
| `DriftkingsOverlay` | `driftkings.views.battle.overlay.OverlayView` | `driftkings.battle.components.overlay.overlayui` | Registo automático do serviço BattleViews; superfícies battle |
| `DriftkingsRatingScreens` | `driftkings.views.battle.player_ratings.RatingViews` | `driftkings.battle.components.ratings.ratingscreens` | `battle.team_panels`: getBattleViews, registado pelo Core; superfícies battle, ratings |
| `FlightTimerView` | `driftkings.views.battle.shell_flight_time.FlightTime` | `driftkings.battle.components.flight_timer.flighttimerui` | `battle.shell_flight_time`: getBattleViews, registado pelo Core; superfícies battle |
| `MinimapEnhancementsView` | `driftkings.views.battle.minimap_enhancements.MinimapEnhancementsView` | `driftkings.battle.components.minimap.minimapenhancementsui` | `battle.minimap_enhancements`: getBattleViews, registado pelo Core; superfícies battle |
| `OwnHealthView` | `driftkings.views.battle.vehicle_health.OwnHealth` | `driftkings.battle.components.health.ownhealthui` | `battle.vehicle_health`: getBattleViews, registado pelo Core; superfícies battle |
| `SixthSenseView` | `driftkings.views.battle.sixth_sense_alert.SixthSense` | `driftkings.battle.components.sixth_sense.sixthsenseui` | `battle.sixth_sense_alert`: getBattleViews, registado pelo Core; superfícies battle |

Os dez contratos são referenciados pelo runtime. BattleViews valida alias, FLASH_CLASS e secção; o package devolve ComponentSettings; BattleViewHandler cria os componentes na página nativa. A seleção por `config.enabled`, contexto e superfícies controla utilização efetiva; isto não significa que todos sejam visíveis em qualquer batalha. Overlay é registado pelo serviço; os outros nove pelos componentes.

### Mapa de ficheiros e dependências

Caminhos relativos a `mod/res/scripts/client/driftkings`. Nenhum ficheiro abaixo foi ainda migrado.

| Atual | Destino | Função / dependências |
| --- | --- | --- |
| `views/__init__.py` | `flash/batalha/registry.py` | Publish our battle package; the client owns view registration and lifecycle.; `driftkings.core.hud_visibility`, `driftkings.interface_catalog`, `driftkings.views.battle.overlay` |
| `core/overlay.py` | `flash/core.py` | Owned battle scene. State survives a late Flash load or view recreation.; `driftkings.logger` |
| `views/battle/__init__.py` | `flash/batalha/__init__.py` | Native Scaleform package contract, loaded once by each battle application.; `driftkings.views`, `driftkings.views.battle.handler` |
| `views/battle/aiming_countdown.py` | `flash/batalha/aiming_countdown.py` | Presentation adapter for DispersionTimer; gameplay state stays in its component.; `driftkings._constants`, `driftkings.core.battle_events`, `driftkings.logger`, `driftkings.meta.battle.dispersion_timer` |
| `views/battle/battle_performance.py` | `flash/batalha/battle_performance.py` | battle_performance.py; `driftkings._constants`, `driftkings.core.overlay`, `driftkings.settings.service`, `driftkings.views.battle.label` |
| `views/battle/battle_statistics.py` | `flash/batalha/battle_statistics.py` | battle_statistics.py; `driftkings._constants`, `driftkings.core.overlay`, `driftkings.settings.service`, `driftkings.views.battle.label` |
| `views/battle/debug_panel.py` | `flash/batalha/debug_panel.py` | Clock transport owned by the native battle debug panel's view lifecycle.; `driftkings._constants`, `driftkings.meta.battle.debug_panel`, `driftkings.settings.service`, `driftkings.ui` |
| `views/battle/gun_traverse_limits.py` | `flash/batalha/gun_traverse_limits.py` | Flash rendering for aiming angles; coordinates are supplied by the controller.; `driftkings._constants`, `driftkings.core.overlay`, `driftkings.settings.service` |
| `views/battle/handler.py` | `flash/batalha/handler.py` | Create library components when the client loads a native battle page.; `driftkings.interface_catalog`, `driftkings.logger`, `driftkings.views` |
| `views/battle/label.py` | `flash/batalha/label.py` | Position, shadow and lifecycle shared by configurable battle text labels.; `driftkings.core.overlay`, `driftkings.settings.service` |
| `views/battle/minimap_enhancements.py` | `flash/batalha/minimap_enhancements.py` | minimap_enhancements.py; `driftkings._constants`, `driftkings.common.utils.game`, `driftkings.common.utils.wgutils`, `driftkings.core.callbacks`, `driftkings.meta.battle.minimap`, `driftkings.settings.registry`, `driftkings.settings.service`, `driftkings.ui.common.events` |
| `views/battle/overlay.py` | `flash/batalha/overlay.py` | Native DAAPI transport for the shared Driftkings battle scene.; `driftkings._constants`, `driftkings.core.overlay`, `driftkings.meta.battle.overlay` |
| `views/battle/penetration_indicator.py` | `flash/batalha/penetration_indicator.py` | Presentation adapter for ArmorCalculator; gameplay state stays in its component.; `driftkings._constants`, `driftkings.meta.battle.armor_calculator`, `driftkings.settings.service`, `driftkings.ui.common.events` |
| `views/battle/player_ratings.py` | `flash/batalha/player_ratings.py` | player_ratings.py; `driftkings._constants`, `driftkings.common.utils.colorratting`, `driftkings.core.battle_capabilities`, `driftkings.core.battle_events`, `driftkings.core.hooks`, `driftkings.core.panel_model`, `driftkings.gameface.batalha.panel_gameface`, `driftkings.logger`, `driftkings.meta.battle.players_panel`, `driftkings.settings.service`, `driftkings.settings.settings_data` |
| `views/battle/shell_flight_time.py` | `flash/batalha/shell_flight_time.py` | Presentation adapter for FlightTimer; gameplay state stays in its component.; `driftkings._constants`, `driftkings.common.utils.wgutils`, `driftkings.core.battle_policy`, `driftkings.meta.battle.flight_timer` |
| `views/battle/sixth_sense_alert.py` | `flash/batalha/sixth_sense_alert.py` | Presentation adapter for SixthSense; gameplay state stays in its component.; `driftkings._constants`, `driftkings.meta.battle.sixth_sense` |
| `views/battle/target_distance.py` | `flash/batalha/target_distance.py` | target_distance.py; `driftkings._constants`, `driftkings.core.hud_visibility`, `driftkings.core.keyboard`, `driftkings.logger`, `driftkings.meta.battle.distance_marker`, `driftkings.settings.service` |
| `views/battle/target_information.py` | `flash/batalha/target_information.py` | target_information.py; `driftkings._constants`, `driftkings.core.overlay`, `driftkings.settings.service` |
| `views/battle/vehicle_health.py` | `flash/batalha/vehicle_health.py` | Presentation adapter for OwnHealth; gameplay state stays in its component.; `driftkings._constants`, `driftkings.common.utils.formatting`, `driftkings.meta.battle.own_health`, `driftkings.settings.service` |
| `meta/battle/__init__.py` | `flash/batalha/meta/__init__.py` | Battle Flash contracts; import each component explicitly.;  |
| `meta/battle/armor_calculator.py` | `flash/batalha/meta/armor_calculator.py` | armor_calculator.py; `driftkings.meta.battle.base` |
| `meta/battle/base.py` | `flash/batalha/meta/base.py` | Common DAAPI lifecycle; the native page owns component destruction.; `driftkings.core.battle_capabilities`, `driftkings.core.diagnostics`, `driftkings.core.hud_visibility`, `driftkings.settings.service` |
| `meta/battle/debug_panel.py` | `flash/batalha/meta/debug_panel.py` | debug_panel.py; `driftkings.meta.battle.base` |
| `meta/battle/dispersion_timer.py` | `flash/batalha/meta/dispersion_timer.py` | dispersion_timer.py; `driftkings.meta.battle.base` |
| `meta/battle/distance_marker.py` | `flash/batalha/meta/distance_marker.py` | distance_marker.py; `driftkings.meta.battle.base` |
| `meta/battle/flight_timer.py` | `flash/batalha/meta/flight_timer.py` | flight_timer.py; `driftkings.meta.battle.base` |
| `meta/battle/minimap.py` | `flash/batalha/meta/minimap.py` | minimap.py; `driftkings.meta.battle.base` |
| `meta/battle/overlay.py` | `flash/batalha/meta/overlay.py` | overlay.py; `driftkings.meta.battle.base` |
| `meta/battle/own_health.py` | `flash/batalha/meta/own_health.py` | own_health.py; `driftkings.meta.battle.base` |
| `meta/battle/players_panel.py` | `flash/batalha/meta/players_panel.py` | players_panel.py; `driftkings.core.diagnostics`, `driftkings.meta.battle.base` |
| `meta/battle/sixth_sense.py` | `flash/batalha/meta/sixth_sense.py` | sixth_sense.py; `driftkings.meta.battle.base` |
| `views/hangar/battle_performance_hooks.py` | `flash/hangar/battle_performance_hooks.py` | battle_performance_hooks.py; `driftkings._constants`, `driftkings.common.utils.formatting`, `driftkings.core.hooks`, `driftkings.logger`, `driftkings.settings.service` |
| `views/hangar/hangar_preferences_hooks.py` | `flash/hangar/hangar_preferences_hooks.py` | hangar_preferences_hooks.py; `driftkings._constants`, `driftkings.core.hooks`, `driftkings.settings.service` |
| `views/hangar/profile_statistics.py` | `flash/hangar/profile_statistics.py` | Format the native Flash statistics and vehicle dossier fields.; `driftkings.common.utils.colorratting`, `driftkings.core.hooks`, `driftkings.core.profile_ratings`, `driftkings.logger`, `driftkings.settings.service`, `driftkings.stats.vehinfo`, `driftkings.ui` |

### Código misto e fronteiras a separar

- `core/lifecycle.py`: manter serviço e notificações funcionais; instalação de LoginView/LobbyView passa para `flash/lifecycle.py`, com mesmo proprietário.
- `core/hud_visibility.py`: manter estado partilhado com Gameface; roteamento DAAPI e hooks de BattlePageMeta passam para `flash/batalha/hud_visibility.py`. Instalador Gameface existente preservado.
- `battle/minimap_enhancements.py`: regras e controlador de estado permanecem; classes PersonalEntriesPlugin/ArenaVehiclesPlugin e hook MinimapComponent passam para `flash/batalha/minimap_plugins.py`. Políticas puras continuam em `core/minimap.py`.
- `battle/aiming_reticles.py`: cálculos, controlo de input/rotação e estado permanecem; CustomCrosshairContainer, factories, linkages e hook de SharedPage passam para `flash/batalha/aiming_reticles.py`.
- `battle/penetration_indicator.py`: cálculos de penetração permanecem; plugin de apresentação ShotResultIndicatorPlugin e hook crosshair passam para `flash/batalha/penetration_hooks.py`.
- `battle/battle_preferences.py`: extrair hooks exclusivamente visuais para adaptador; manter regras, cálculos, sons, boosters, dados de jogadores e eventos funcionais.
- `battle/sixth_sense_alert.py`: mensagens/chat permanecem funcionais; manipulação da visibilidade do indicador nativo passa ao adaptador.
- `battle/vehicle_markers.py` e `core/vehicle_markers`: conservar schema, cálculos, validação, dados de contexto/ratings; separar instalação/ponte nativa e apresentação para `flash/batalha/vehicle_markers`. Hooks reversíveis genéricos conservam-se como serviço partilhado.
- Distância: o controlador existente mistura projeção, drag, hit-test e pedido por frame do SWF; é adaptador de apresentação. Dados de entidades/estado funcional não devem ser transferidos desnecessariamente.
- Cronómetro de mira/tempo de voo: extrair cálculos matemáticos independentes de DAAPI para helper funcional, preservando chamadas e resultados.
- `views/marks_model.py` e `crew_progression_model.py` são helpers de dados usados também pelo Gameface: permanecem, sem Wulf/DAAPI.
- `views/hangar` contém três módulos Scaleform; serão centralizados em `flash/hangar`, sem tocar nas views Gameface.
- Imports de constantes nativas, recolha de dados (ex. ProfileUtils), comandos de consumíveis e controlos de simulação não serão confundidos com implementação de views.

### Registos, lifecycle e recursos

- Catálogo é fonte única: mudar apenas dez caminhos Python. AS3/aliases/secções/componentes/superfícies preservados.
- `BattlePackageRegistration.PACKAGE` deve apontar para `driftkings.flash.batalha`; atualizar ServiceSpec, testes e strings.
- Manter WeakSet de handlers, cancelamento de callbacks de descoberta, descarregamento reverso, exclusão dos registos próprios e deduplicação escalar de ComponentMeta.
- Flash labels partilham BattleLabel/CachedBattleLabel; mover para common sem criar outro lifecycle.
- Build usa descoberta de módulos; validar packaging e catálogo gerado, sem reescrever recursos por mera mudança de import.

## Etapas

| Etapa | Estado | Validação / evidência |
| --- | --- | --- |
| 0 — Auditoria e mapa antes de código | Concluída | Inventário acima |
| 1 — Núcleo, registo e lifecycle partilhado | Concluída | 429 testes core Python 3; 0 nomes indefinidos |
| 2 — Views, metas e adaptadores existentes | Concluída | 429 testes core, catálogo e build inputs válidos |
| 3 — Separação de apresentação dos módulos mistos | Concluída | 429 testes core em Python 2.7/3; 0 nomes indefinidos |
| 4 — Testes arquiteturais, documentação e changelog | Pendente | Fronteiras, contratos, ciclos, hooks |
| 5 — Validação completa, build e GitHub | Pendente | Python 2.7/3, npm/lint, AS3/SWF, WOTMOD e CI |

## Registo de execução

- Etapa 0: documento do pedido lido; branch/árvore confirmadas; inspecionados contratos, views, metas, lifecycle, hooks, serviços, recursos e módulos mistos. Plano produzido antes de alterar código. Hashes de cada etapa disponíveis em `git log --oneline -- docs/PLANO_FLASH.md`.

## Oportunidades de desempenho identificadas (sem melhoria medida)

- OverlayScene faz deepcopy e publica updates mesmo quando valores podem ser iguais; animações e reanexação exigem cuidado antes de deduplicar.
- ComponentMeta já deduplica setters escalares e só confirma cache após sucesso; não duplicar essa infraestrutura.
- BattleViewHandler já cancela pesquisas e limita tentativas; manter sem timers paralelos.
- Distância calcula projeção por frame solicitado pelo Flash; medir antes de modificar frequência.
- Minimap plugins já mantêm cache de payloads e callback de posições perdidas; medir custo de formatação em eventos frequentes.
- Preservar reset dos caches na troca de flashObject, libertação de listeners/WeakSets e cancelamento de callbacks ao terminar batalha.

## Validação pendente no cliente

- Batalhas consecutivas e modos especiais/replay; criação dos dez contratos quando aplicáveis, fim da batalha sem componentes/callbacks órfãos.
- TAB, ocultar HUD, cursor/drag, posições bloqueadas, overlay e recriação de página.
- Mira/penetração/tempo de voo, minimapa e marcadores (normal/ALT, vida, cores e ratings), sexto sentido e painéis de jogadores.
- Preferências de batalha e hangar, perfil/resultados e ativação/desativação preservadas.
- Medições comparativas de CPU/memória/FPS continuam necessárias antes de atribuir ganhos a esta reorganização.

- Etapa 1: criados packages Flash passivos; OverlayScene movido para `flash/core.py` e BattleViews/registo para `flash/batalha/registry.py`. Extraída a instalação Scaleform de lifecycle/HUD; serviço e estado partilhado permanecem no core. Imports e testes alinhados, sem alterar o bridge Gameface. 429 testes core: OK; 0 nomes indefinidos. Auditoria inicial publicada em `27ff790`.

- Etapa 2: movidas as views/metas de batalha e as três views Scaleform de hangar. BattleLabel/CachedBattleLabel ficaram em `flash/batalha/common.py`; package nativo passou a `driftkings.flash.batalha`. Atualizados dez caminhos do catálogo, imports estáticos/diferidos, testes e pesquisa de metas no validador de build. Mantidos helpers de dados partilhados em views; removidos apenas os `__init__` antigos sem utilização. 429 testes core: OK; catálogo e build data validados; nenhuma alteração AS3/SWF. Núcleo publicado em `e9a4635`.

### Complemento da auditoria durante a separação dos módulos mistos

Antes de migrar estas dependências adicionais, confirmou-se: `common/utils/game.sendPanelMessage` contém transporte DAAPI (destino `flash/batalha/messages.py`); `components/account_manager` contém leitura de coordenadas/formulário nativo e chamadas AS3 (destino `flash/hangar/login.py`, mantendo credenciais/autenticação no serviço); `components/game_log_manager` mistura filtros com encaminhamento Flash (destino `flash/batalha/game_log.py`, mantendo filtros funcionais); hooks Scaleform de chat/resultados/tooltip em `lobby/hangar_preferences` passam a `flash/hangar/native_preferences.py`. Hooks que apenas recolhem dados (ribbons/seleção de tripulação) continuam funcionais. Estas dependências complementam o inventário, sem alargar a tarefa a regras ou recursos visuais.

- Etapa 3: extraídos plugins nativos de minimapa, plugin de penetração, factories/containers/linkages de mira, hooks visuais de preferências, transporte de mensagens, encaminhamento de logs e ponte do formulário de login. Marcadores conservam `validate/apply/values` funcionais no core; lifecycle/transporte estão em `flash/batalha/vehicle_markers`. Cálculos numéricos de mira/voo extraídos para `core/aiming_timing.py`; projeção/hit-test/drag do marcador de distância permanecem no adaptador por dependerem do contrato por frame do SWF.
- Componentes fornecem configuração/estado aos bridges existentes sem novas frameworks. Minimap/penetração ligam as referências uma vez na importação do componente, antes da ativação dos hooks. Estado e controlos de simulação das miras ficam funcionais, usando métodos de linkage do adaptador. Core/serviços de diagnóstico/hook reversível e consumidores de eventos de recolha continuam fora de Flash.
- Corrigidos os stubs de mensagens e plugins nos testes para as novas fronteiras; mantidos todos os testes de comportamento existentes. 429 testes Python 3 e 429 Python 2.7 passaram; catálogo/build data válidos (317 módulos); 0 nomes indefinidos. Nenhuma frequência alterada ou ganho de FPS alegado. Views/metas publicadas em `19db2a3`.
