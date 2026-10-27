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
| `views/__init__.py` | `flash/battle/registry.py` | Publish our battle package; the client owns view registration and lifecycle.; `driftkings.core.hud_visibility`, `driftkings.interface_catalog`, `driftkings.views.battle.overlay` |
| `core/overlay.py` | `flash/core.py` | Owned battle scene. State survives a late Flash load or view recreation.; `driftkings.logger` |
| `views/battle/__init__.py` | `flash/battle/__init__.py` | Native Scaleform package contract, loaded once by each battle application.; `driftkings.views`, `driftkings.views.battle.handler` |
| `views/battle/aiming_countdown.py` | `flash/battle/aiming_countdown.py` | Presentation adapter for DispersionTimer; gameplay state stays in its component.; `driftkings._constants`, `driftkings.core.battle_events`, `driftkings.logger`, `driftkings.meta.battle.dispersion_timer` |
| `views/battle/battle_performance.py` | `flash/battle/battle_performance.py` | battle_performance.py; `driftkings._constants`, `driftkings.core.overlay`, `driftkings.settings.service`, `driftkings.views.battle.label` |
| `views/battle/battle_statistics.py` | `flash/battle/battle_statistics.py` | battle_statistics.py; `driftkings._constants`, `driftkings.core.overlay`, `driftkings.settings.service`, `driftkings.views.battle.label` |
| `views/battle/debug_panel.py` | `flash/battle/debug_panel.py` | Clock transport owned by the native battle debug panel's view lifecycle.; `driftkings._constants`, `driftkings.meta.battle.debug_panel`, `driftkings.settings.service`, `driftkings.ui` |
| `views/battle/gun_traverse_limits.py` | `flash/battle/gun_traverse_limits.py` | Flash rendering for aiming angles; coordinates are supplied by the controller.; `driftkings._constants`, `driftkings.core.overlay`, `driftkings.settings.service` |
| `views/battle/handler.py` | `flash/battle/handler.py` | Create library components when the client loads a native battle page.; `driftkings.interface_catalog`, `driftkings.logger`, `driftkings.views` |
| `views/battle/label.py` | `flash/battle/label.py` | Position, shadow and lifecycle shared by configurable battle text labels.; `driftkings.core.overlay`, `driftkings.settings.service` |
| `views/battle/minimap_enhancements.py` | `flash/battle/minimap_enhancements.py` | minimap_enhancements.py; `driftkings._constants`, `driftkings.common.utils.game`, `driftkings.common.utils.wgutils`, `driftkings.core.callbacks`, `driftkings.meta.battle.minimap`, `driftkings.settings.registry`, `driftkings.settings.service`, `driftkings.ui.common.events` |
| `views/battle/overlay.py` | `flash/battle/overlay.py` | Native DAAPI transport for the shared Driftkings battle scene.; `driftkings._constants`, `driftkings.core.overlay`, `driftkings.meta.battle.overlay` |
| `views/battle/penetration_indicator.py` | `flash/battle/penetration_indicator.py` | Presentation adapter for ArmorCalculator; gameplay state stays in its component.; `driftkings._constants`, `driftkings.meta.battle.armor_calculator`, `driftkings.settings.service`, `driftkings.ui.common.events` |
| `views/battle/player_ratings.py` | `flash/battle/player_ratings.py` | player_ratings.py; `driftkings._constants`, `driftkings.common.utils.colorratting`, `driftkings.core.battle_capabilities`, `driftkings.core.battle_events`, `driftkings.core.hooks`, `driftkings.core.panel_model`, `driftkings.gameface.battle.panel_gameface`, `driftkings.logger`, `driftkings.meta.battle.players_panel`, `driftkings.settings.service`, `driftkings.settings.settings_data` |
| `views/battle/shell_flight_time.py` | `flash/battle/shell_flight_time.py` | Presentation adapter for FlightTimer; gameplay state stays in its component.; `driftkings._constants`, `driftkings.common.utils.wgutils`, `driftkings.core.battle_policy`, `driftkings.meta.battle.flight_timer` |
| `views/battle/sixth_sense_alert.py` | `flash/battle/sixth_sense_alert.py` | Presentation adapter for SixthSense; gameplay state stays in its component.; `driftkings._constants`, `driftkings.meta.battle.sixth_sense` |
| `views/battle/target_distance.py` | `flash/battle/target_distance.py` | target_distance.py; `driftkings._constants`, `driftkings.core.hud_visibility`, `driftkings.core.keyboard`, `driftkings.logger`, `driftkings.meta.battle.distance_marker`, `driftkings.settings.service` |
| `views/battle/target_information.py` | `flash/battle/target_information.py` | target_information.py; `driftkings._constants`, `driftkings.core.overlay`, `driftkings.settings.service` |
| `views/battle/vehicle_health.py` | `flash/battle/vehicle_health.py` | Presentation adapter for OwnHealth; gameplay state stays in its component.; `driftkings._constants`, `driftkings.common.utils.formatting`, `driftkings.meta.battle.own_health`, `driftkings.settings.service` |
| `meta/battle/__init__.py` | `flash/battle/meta/__init__.py` | Battle Flash contracts; import each component explicitly.;  |
| `meta/battle/armor_calculator.py` | `flash/battle/meta/armor_calculator.py` | armor_calculator.py; `driftkings.meta.battle.base` |
| `meta/battle/base.py` | `flash/battle/meta/base.py` | Common DAAPI lifecycle; the native page owns component destruction.; `driftkings.core.battle_capabilities`, `driftkings.core.diagnostics`, `driftkings.core.hud_visibility`, `driftkings.settings.service` |
| `meta/battle/debug_panel.py` | `flash/battle/meta/debug_panel.py` | debug_panel.py; `driftkings.meta.battle.base` |
| `meta/battle/dispersion_timer.py` | `flash/battle/meta/dispersion_timer.py` | dispersion_timer.py; `driftkings.meta.battle.base` |
| `meta/battle/distance_marker.py` | `flash/battle/meta/distance_marker.py` | distance_marker.py; `driftkings.meta.battle.base` |
| `meta/battle/flight_timer.py` | `flash/battle/meta/flight_timer.py` | flight_timer.py; `driftkings.meta.battle.base` |
| `meta/battle/minimap.py` | `flash/battle/meta/minimap.py` | minimap.py; `driftkings.meta.battle.base` |
| `meta/battle/overlay.py` | `flash/battle/meta/overlay.py` | overlay.py; `driftkings.meta.battle.base` |
| `meta/battle/own_health.py` | `flash/battle/meta/own_health.py` | own_health.py; `driftkings.meta.battle.base` |
| `meta/battle/players_panel.py` | `flash/battle/meta/players_panel.py` | players_panel.py; `driftkings.core.diagnostics`, `driftkings.meta.battle.base` |
| `meta/battle/sixth_sense.py` | `flash/battle/meta/sixth_sense.py` | sixth_sense.py; `driftkings.meta.battle.base` |
| `views/hangar/battle_performance_hooks.py` | `flash/lobby/battle_performance_hooks.py` | battle_performance_hooks.py; `driftkings._constants`, `driftkings.common.utils.formatting`, `driftkings.core.hooks`, `driftkings.logger`, `driftkings.settings.service` |
| `views/hangar/hangar_preferences_hooks.py` | `flash/lobby/hangar_preferences_hooks.py` | hangar_preferences_hooks.py; `driftkings._constants`, `driftkings.core.hooks`, `driftkings.settings.service` |
| `views/hangar/profile_statistics.py` | `flash/lobby/profile_statistics.py` | Format the native Flash statistics and vehicle dossier fields.; `driftkings.common.utils.colorratting`, `driftkings.core.hooks`, `driftkings.core.profile_ratings`, `driftkings.logger`, `driftkings.settings.service`, `driftkings.stats.vehinfo`, `driftkings.ui` |

### Código misto e fronteiras a separar

- `core/lifecycle.py`: manter serviço e notificações funcionais; instalação de LoginView/LobbyView passa para `flash/lifecycle.py`, com mesmo proprietário.
- `core/hud_visibility.py`: manter estado partilhado com Gameface; roteamento DAAPI e hooks de BattlePageMeta passam para `flash/battle/hud_visibility.py`. Instalador Gameface existente preservado.
- `battle/minimap_enhancements.py`: regras e controlador de estado permanecem; classes PersonalEntriesPlugin/ArenaVehiclesPlugin e hook MinimapComponent passam para `flash/battle/minimap_plugins.py`. Políticas puras continuam em `core/minimap.py`.
- `battle/aiming_reticles.py`: cálculos, controlo de input/rotação e estado permanecem; CustomCrosshairContainer, factories, linkages e hook de SharedPage passam para `flash/battle/aiming_reticles.py`.
- `battle/penetration_indicator.py`: cálculos de penetração permanecem; plugin de apresentação ShotResultIndicatorPlugin e hook crosshair passam para `flash/battle/penetration_hooks.py`.
- `battle/battle_preferences.py`: extrair hooks exclusivamente visuais para adaptador; manter regras, cálculos, sons, boosters, dados de jogadores e eventos funcionais.
- `battle/sixth_sense_alert.py`: mensagens/chat permanecem funcionais; manipulação da visibilidade do indicador nativo passa ao adaptador.
- `battle/vehicle_markers.py` e `core/vehicle_markers`: conservar schema, cálculos, validação, dados de contexto/ratings; separar instalação/ponte nativa e apresentação para `flash/battle/vehicle_markers`. Hooks reversíveis genéricos conservam-se como serviço partilhado.
- Distância: o controlador existente mistura projeção, drag, hit-test e pedido por frame do SWF; é adaptador de apresentação. Dados de entidades/estado funcional não devem ser transferidos desnecessariamente.
- Cronómetro de mira/tempo de voo: extrair cálculos matemáticos independentes de DAAPI para helper funcional, preservando chamadas e resultados.
- `views/marks_model.py` e `crew_progression_model.py` são helpers de dados usados também pelo Gameface: permanecem, sem Wulf/DAAPI.
- `views/hangar` contém três módulos Scaleform; serão centralizados em `flash/lobby`, sem tocar nas views Gameface.
- Imports de constantes nativas, recolha de dados (ex. ProfileUtils), comandos de consumíveis e controlos de simulação não serão confundidos com implementação de views.

### Registos, lifecycle e recursos

- Catálogo é fonte única: mudar apenas dez caminhos Python. AS3/aliases/secções/componentes/superfícies preservados.
- `BattlePackageRegistration.PACKAGE` deve apontar para `driftkings.flash.battle`; atualizar ServiceSpec, testes e strings.
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
| 4 — Testes arquiteturais, documentação e changelog | Concluída | 12 testes novos Python 2.7/3: OK |
| 5 — Validação completa, build e GitHub | Concluída | Todas as validações locais e GitHub Actions: OK |

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

- Etapa 1: criados packages Flash passivos; OverlayScene movido para `flash/core.py` e BattleViews/registo para `flash/battle/registry.py`. Extraída a instalação Scaleform de lifecycle/HUD; serviço e estado partilhado permanecem no core. Imports e testes alinhados, sem alterar o bridge Gameface. 429 testes core: OK; 0 nomes indefinidos. Auditoria inicial publicada em `27ff790`.

- Etapa 2: movidas as views/metas de batalha e as três views Scaleform de hangar. BattleLabel/CachedBattleLabel ficaram em `flash/battle/common.py`; package nativo passou a `driftkings.flash.battle`. Atualizados dez caminhos do catálogo, imports estáticos/diferidos, testes e pesquisa de metas no validador de build. Mantidos helpers de dados partilhados em views; removidos apenas os `__init__` antigos sem utilização. 429 testes core: OK; catálogo e build data validados; nenhuma alteração AS3/SWF. Núcleo publicado em `e9a4635`.

### Complemento da auditoria durante a separação dos módulos mistos

Antes de migrar estas dependências adicionais, confirmou-se: `common/utils/game.sendPanelMessage` contém transporte DAAPI (destino `flash/battle/messages.py`); `components/account_manager` contém leitura de coordenadas/formulário nativo e chamadas AS3 (destino `flash/lobby/login.py`, mantendo credenciais/autenticação no serviço); `components/game_log_manager` mistura filtros com encaminhamento Flash (destino `flash/battle/game_log.py`, mantendo filtros funcionais); hooks Scaleform de chat/resultados/tooltip em `lobby/hangar_preferences` passam a `flash/lobby/native_preferences.py`. Hooks que apenas recolhem dados (ribbons/seleção de tripulação) continuam funcionais. Estas dependências complementam o inventário, sem alargar a tarefa a regras ou recursos visuais.

- Etapa 3: extraídos plugins nativos de minimapa, plugin de penetração, factories/containers/linkages de mira, hooks visuais de preferências, transporte de mensagens, encaminhamento de logs e ponte do formulário de login. Marcadores conservam `validate/apply/values` funcionais no core; lifecycle/transporte estão em `flash/battle/vehicle_markers`. Cálculos numéricos de mira/voo extraídos para `core/aiming_timing.py`; projeção/hit-test/drag do marcador de distância permanecem no adaptador por dependerem do contrato por frame do SWF.
- Componentes fornecem configuração/estado aos bridges existentes sem novas frameworks. Minimap/penetração ligam as referências uma vez na importação do componente, antes da ativação dos hooks. Estado e controlos de simulação das miras ficam funcionais, usando métodos de linkage do adaptador. Core/serviços de diagnóstico/hook reversível e consumidores de eventos de recolha continuam fora de Flash.
- Corrigidos os stubs de mensagens e plugins nos testes para as novas fronteiras; mantidos todos os testes de comportamento existentes. 429 testes Python 3 e 429 Python 2.7 passaram; catálogo/build data válidos (317 módulos); 0 nomes indefinidos. Nenhuma frequência alterada ou ganho de FPS alegado. Views/metas publicadas em `19db2a3`.

- Etapa 4: adicionados 12 testes de arquitetura, executados em Python 2.7/3: resolução real das views/metas dos dez contratos, correspondência de métodos DAAPI no AS3 existente, cache escalar/recriação/falhas, registo único e descarregamento, rollback de start, instalação/desativação dos hooks HUD, cancelamento de callbacks de pesquisa, imports antigos/fronteiras, ciclos imediatos, cálculos numéricos e valores/posição do formulário de login. O contrato RatingViews é uma factory de RosterView; o teste valida a classe realmente registada. Imports Flash ordenados; documentação e release.json atualizados sem mudar a versão publicada. Módulos mistos publicados em `8d97f92`.

## Estrutura final

```text
driftkings/
  flash/
    __init__.py
    core.py
    lifecycle.py
    battle/
      __init__.py
      aiming_countdown.py
      aiming_reticles.py
      battle_performance.py
      battle_statistics.py
      common.py
      debug_panel.py
      game_log.py
      gun_traverse_limits.py
      handler.py
      hud_visibility.py
      messages.py
      minimap_enhancements.py
      minimap_plugins.py
      overlay.py
      penetration_hooks.py
      penetration_indicator.py
      player_ratings.py
      preferences_hooks.py
      registry.py
      shell_flight_time.py
      sixth_sense_alert.py
      target_distance.py
      target_information.py
      vehicle_health.py
      meta/
        __init__.py
        armor_calculator.py
        base.py
        debug_panel.py
        dispersion_timer.py
        distance_marker.py
        flight_timer.py
        minimap.py
        overlay.py
        own_health.py
        players_panel.py
        sixth_sense.py
      vehicle_markers/
        __init__.py
        presentation.py
        ratings.py
        runtime.py
    lobby/
      __init__.py
      battle_performance_hooks.py
      hangar_preferences_hooks.py
      login.py
      native_preferences.py
      profile_statistics.py
  gameface/                # implementação anterior preservada
  battle/, lobby/, components/  # regras, estado e recolha
  core/                    # serviços/modelos independentes
    aiming_timing.py       # cálculos extraídos dos adaptadores
  views/                   # apenas helpers de dados sem motor
    marks_model.py
    crew_progression_model.py
```

## Dependências e ficheiros

- Movidos os ficheiros do mapa inicial; `views/__init__.py` conserva apenas o package de helpers. Os antigos packages `views/battle`, `views/hangar`, `meta/battle` e `meta` deixaram de conter fontes; não existem shims de importação.
- Criados os packages passivos, `flash/lifecycle.py`, `flash/battle/hud_visibility.py`, `core/aiming_timing.py` e os bridges extraídos: `aiming_reticles`, `minimap_plugins`, `penetration_hooks`, `preferences_hooks`, `game_log`, `messages`, `vehicle_markers/{runtime,presentation,ratings}`, `lobby/{login,native_preferences}`. Novo teste: `tests/core/test_flash_architecture.py`.
- `interface_catalog.py`: apenas os dez campos `FLASH_COMPONENTS[*].python` alterados. AS3, aliases, secções, componentes e superfícies preservados. Os 14 contratos Gameface permanecem intactos.
- Core ServiceSpec → `flash.battle.registry:BattleViews` → package `driftkings.flash.battle` → `handler`/metas/views. Componentes → adaptadores Flash; cálculos/configuração/estado continuam nos componentes/core. Os adaptadores usam referências diferidas ou configuração explícita antes da ativação de hooks, evitando ciclos imediatos.
- `build_tools/generate_ui_catalog.py` pesquisa metas na nova localização. Não foi necessário regenerar/modificar os artefactos AS3/JS porque os seus contratos públicos não mudaram.
- A ponte de login é dependência real da janela de contas Gameface, mas a API do controller foi preservada e nenhum ficheiro Gameface precisou de mudar.
- Hooks de tripulação, ribbons e consultas ProfileUtils/constantes que apenas recolhem dados ou executam regras mantêm-se funcionais. Não são Views nem manipulam flashObject.
- Problemas resolvidos durante a migração: pesquisa de metas ainda apontava para o diretório antigo; stubs de mensagens/plugins ainda simulavam a fronteira antiga; testes distinguem corretamente a factory RatingViews da classe RosterView e suportam AST de Python 2.7 e 3.14. Nenhum erro foi mascarado com novos fallbacks.

## Resultados finais — 27 outubro 2026

| Validação | Resultado |
| --- | --- |
| Core Python 3 / Python 2.7 | 441 / 441 testes: OK |
| Settings panel Python 3 / Python 2.7 | 27 / 27 testes: OK |
| Installer Python 3 | 33 testes: OK |
| Testes novos Flash | 12 em ambos os runtimes: OK |
| `npm test` / `npm run lint` | OK / OK |
| Catálogos de tradução | 18 idiomas; 1491 chaves de componentes, 170 de painel; 0 não traduzidas |
| Defaults gerados | Sincronizados; 34 componentes |
| Nomes indefinidos / isort Flash | 0 / OK |
| Catálogo e build data | 10 Flash, 14 Gameface, 12 injetados; 39 manifests, 317 módulos, 223 assets, 53 defaults |
| Comparação AST das metas com `abe544c` | Classes, métodos, assinaturas e corpos iguais; apenas imports alterados |
| Comparação de contratos | Apenas dez caminhos Python Flash mudaram; restante catálogo e todos os contratos Gameface iguais |
| Recursos e Gameface | Nenhuma alteração em `flash_source`, `mod/res/gui` ou `driftkings/gameface` |
| Build debug beta nativa | OK; 317 módulos compilados/verificados com Python 2.7; geradores battle_flash/vehicle_markers_flash executados; WOTMOD em `build/debug/beta/0.1.3-beta.2` |
| GitHub Actions do código | Aprovado para `56138ce` |

- Etapa 5: validações acima concluídas; [CI do código aprovado](https://github.com/dkruben/Driftkings_SettingsLab/actions/runs/40424997042). Os commits técnicos anteriores (`e9a4635`, `19db2a3`, `8d97f92`) também passaram no GitHub.
- A build é local de desenvolvimento; nenhuma tag/release foi publicada e a instalação EU não foi alterada. Não há ganho de CPU/memória/FPS comprovado nesta tarefa.
- A lista de testes no cliente e de oportunidades de desempenho acima permanece pendente para aceitação nativa/medição; testes simulados não demonstram equivalência visual no jogo.
- Este registo final é enviado num commit de documentação separado, cujo CI também será acompanhado. Estado do repositório e hashes por etapa verificáveis no histórico do branch `develop`.

- Ajuste de nomes — 27 outubro 2026: por indicação do autor, os subpackages de ambas as tecnologias passam a `battle` e `lobby`. Atualizados diretórios, imports, strings de registo, catálogo, testes e documentação; os contextos nativos WG, nomes de funcionalidades e recursos visuais são preservados.
- Validação do ajuste de nomes: 441 testes core em Python 2.7 e 3, 22 testes de arquitetura em Python 3, catálogo/build data/isort e build WOTMOD com 317 módulos: OK. Nenhuma referência antiga no runtime/build e nenhum recurso visual alterado.

- Limpeza posterior — 27 outubro 2026: removida a deteção do antigo script standalone que impedia a inicialização dos marcadores integrados, juntamente com o import ResMgr usado exclusivamente nessa deteção. Mantidos os créditos históricos. Guia de marcadores e changelog atualizados.
- Validação desta limpeza: 41 testes de marcadores em Python 2.7 e 3, 0 nomes indefinidos e build data válidos.

- Correção posterior baseada no log EU: removidas chamadas TextField não suportadas no relógio; cartões Gameface usam fontes nativas declaradas; seleção de calibração de replay rejeita curvas planas/invertidas. Âmbito e evidência no [relatório EU](EU_LOG_2026-10-27.md). 444 testes core em ambos os runtimes, JavaScript/lint e build nativa: OK. Nenhuma instalação/configuração/cache EU alterada nesta correção.

- Novo log EU de 01:20–01:32 confirma zero avisos sharpness/thickness. Corrigida a resolução literal de `inherit` com Warhelios declarada nos cartões e removido o mesmo padrão do carrossel/alias `$FieldFont`; fontes TTF verificadas nos packages EU. Marcas `unavailable` continuam pendentes de diagnóstico.
