# Plano de trabalho — centralização Python Gameface

## Contrato de trabalho

- Branch: `develop`; base: `7b997b2c3ebe2c322c43a1cd5e10d736e9a1483b`. Árvore inicialmente limpa.
- Executar incrementalmente; em cada etapa atualizar este registo, validar, commitar e fazer push. Não publicar uma versão nem instalar no EU nesta tarefa.
- Preservar regras, payloads, configurações, recursos nativos, URLs, HTML/CSS/JS, APIs WG/Wulf/openwg e Python 2.7. Sem alterações visuais ou funcionais.
- Decisão prévia: usar `driftkings/gameface` em minúsculas. Alinha os packages existentes e evita imports com capitalização divergente em Windows/Linux; `batalha` e `hangar` separam os contextos pedidos.
- `interface_catalog.py` continua a única fonte dos 14 contratos; `registry.py` recebe o registo de janelas existente, sem duplicar catálogo.

## Inventário e mapa antes da migração

Todos os caminhos seguintes são relativos a `mod/res/scripts/client/driftkings`. Os módulos inventariados já são adaptadores de apresentação; os serviços de cálculo e recolha permanecem em `core`, `battle`, `lobby` e `components`.

| Atual | Proposto | Função e dependências diretas Driftkings |
| --- | --- | --- |
| `ui/gameface.py` | `gameface/core.py` | Owned UI lifecycle connected to the Gameface dependency required by ModList.; `driftkings.interface_catalog` |
| `views/hangar/windows.py` | `gameface/registry.py` | Central catalog for independent windows and loading-screen surfaces.;  |
| `views/battle/common.py` | `gameface/batalha/common.py` | Shared lifecycle for owned Gameface children of the native battle HUD.; `driftkings.core.hooks`, `driftkings.interface_catalog`, `driftkings.settings.service`, `driftkings.ui.gameface`, `driftkings.views.hangar.common` |
| `views/battle/high_caliber_gameface.py` | `gameface/batalha/high_caliber_gameface.py` | MainGun HUD presentation. All targets and states arrive from the battle component.; `driftkings._constants`, `driftkings.core.hud_visibility`, `driftkings.logger`, `driftkings.settings.service`, `driftkings.views.battle.common`, `driftkings.views.marks_model` |
| `views/battle/panel_gameface.py` | `gameface/batalha/panel_gameface.py` | panel_gameface.py; `driftkings._constants`, `driftkings.core.diagnostics`, `driftkings.core.hooks`, `driftkings.interface_catalog`, `driftkings.logger`, `driftkings.settings.service`, `driftkings.ui.gameface` |
| `views/battle/battle_marks_of_excellence.py` | `gameface/batalha/battle_marks_of_excellence.py` | Owned Gameface child of WG 2.4.1 RandomHUDView; no Scaleform overlay.; `driftkings._constants`, `driftkings.core.hud_visibility`, `driftkings.core.marks_state`, `driftkings.logger`, `driftkings.settings.service`, `driftkings.views.battle.common`, `driftkings.views.marks_model` |
| `views/hangar/common.py` | `gameface/hangar/common.py` | Shared lifecycle for component-owned Gameface hangar cards.; `driftkings.core.hooks`, `driftkings.core.settings_controller`, `driftkings.ui.gameface` |
| `views/hangar/account_manager.py` | `gameface/hangar/account_manager.py` | Standalone Gameface windows for account selection and editing.; `driftkings.core.accounts`, `driftkings.interface_catalog`, `driftkings.logger`, `driftkings.ui.gameface` |
| `views/hangar/battle_performance.py` | `gameface/hangar/battle_performance.py` | battle_performance.py; `driftkings._constants`, `driftkings.core.hooks`, `driftkings.interface_catalog`, `driftkings.settings.service`, `driftkings.ui.gameface` |
| `views/hangar/crew_details.py` | `gameface/hangar/crew_details.py` | Progression summaries owned by native crew personal views and tooltips.; `driftkings._constants`, `driftkings.core.crew_progression`, `driftkings.core.hooks`, `driftkings.interface_catalog`, `driftkings.lobby.crew_progression`, `driftkings.logger`, `driftkings.settings.service`, `driftkings.ui.gameface`, `driftkings.views.crew_progression_model`, `driftkings.views.hangar`, `driftkings.views.hangar.common` |
| `views/hangar/crew_progression.py` | `gameface/hangar/crew_progression.py` | Owned data bridge for annotations beside native crew slots.; `driftkings._constants`, `driftkings.interface_catalog`, `driftkings.lobby.crew_progression`, `driftkings.logger`, `driftkings.settings.service`, `driftkings.ui.gameface`, `driftkings.views.crew_progression_model`, `driftkings.views.hangar`, `driftkings.views.hangar.common` |
| `views/hangar/hangar_marks_of_excellence.py` | `gameface/hangar/hangar_marks_of_excellence.py` | hangar_marks_of_excellence.py; `driftkings._constants`, `driftkings.common.utils.colorratting`, `driftkings.core.marks_state`, `driftkings.settings.service`, `driftkings.ui.gameface`, `driftkings.views.hangar.common`, `driftkings.views.marks_model` |
| `views/hangar/hangar_preferences.py` | `gameface/hangar/hangar_preferences.py` | hangar_preferences.py; `driftkings._constants`, `driftkings.core.hooks`, `driftkings.interface_catalog`, `driftkings.logger`, `driftkings.settings.service`, `driftkings.ui.gameface` |
| `views/hangar/main.py` | `gameface/hangar/main.py` | main.py; `driftkings._constants`, `driftkings.core.hooks`, `driftkings.logger`, `driftkings.settings.service`, `driftkings.ui.gameface`, `driftkings.views.hangar.common` |
| `views/hangar/profile_ratings.py` | `gameface/hangar/profile_ratings.py` | Rating colors for the native achievements summary, without replacing values.; `driftkings.common.utils.colorratting`, `driftkings.core.hooks`, `driftkings.interface_catalog`, `driftkings.logger`, `driftkings.settings.service`, `driftkings.ui.gameface` |
| `views/hangar/settings_window.py` | `gameface/hangar/settings_window.py` | Gameface presentation of DK Mod Settings: integrated settings window.  The window logic lives in driftkings.settings.panel.presenter; this module only moves JSON between the Wulf view models and the presenter.; `driftkings.core.fog_package`, `driftkings.core.keyboard`, `driftkings.core.keycodes`, `driftkings.interface_catalog`, `driftkings.settings.panel`, `driftkings.settings.panel.controls`, `driftkings.settings.panel.presenter`, `driftkings.ui.gameface` |
| `views/hangar/tech_tree_marks_of_excellence.py` | `gameface/hangar/tech_tree_marks_of_excellence.py` | Presentation adapter for MarksOnGunTechTree; gameplay state stays in its component.; `driftkings.core.hooks`, `driftkings.ui.gameface` |
| `views/hangar/vehicle_carousel.py` | `gameface/hangar/vehicle_carousel.py` | vehicle_carousel.py; `driftkings._constants`, `driftkings.common.utils.compat`, `driftkings.core`, `driftkings.core.carousel_options`, `driftkings.settings.service`, `driftkings.ui.gameface`, `driftkings.views.hangar.common` |

### Interfaces, recursos e ciclo de vida

| Interface | Contexto | Implementação atual | Recurso preservado |
| --- | --- | --- | --- |
| `DriftkingsAccountManager` | window | `driftkings.views.hangar.account_manager` | `mods/driftkings/account_manager/window` |
| `DriftkingsCarouselStats` | hangar | `driftkings.views.hangar.vehicle_carousel` | `mods/driftkings/vehicle_carousel/model` |
| `DriftkingsCrewDetails` | hangar | `driftkings.views.hangar.crew_details` | `mods/driftkings/crew_details/model` |
| `DriftkingsCrewProgression` | hangar | `driftkings.views.hangar.crew_progression` | `mods/driftkings/crew_progression/model` |
| `DriftkingsDKModSettings` | window | `driftkings.views.hangar.settings_window` | `mods/driftkings/settings_window/window` |
| `DriftkingsHangarClock` | hangar | `driftkings.views.hangar.main` | `mods/driftkings/main/clock` |
| `DriftkingsHangarHeaderOptions` | header | `driftkings.views.hangar.hangar_preferences` | `mods/driftkings/hangar_preferences/header_options` |
| `DriftkingsMainGun` | battle | `driftkings.views.battle.high_caliber_gameface` | `mods/driftkings/high_caliber_gameface/model` |
| `DriftkingsMarksOnGunBattle` | battle | `driftkings.views.battle.battle_marks_of_excellence` | `mods/driftkings/battle_marks_of_excellence/model` |
| `DriftkingsMarksOnGunHangar` | hangar | `driftkings.views.hangar.hangar_marks_of_excellence` | `mods/driftkings/hangar_marks_of_excellence/model` |
| `DriftkingsMarksOnGunTechTree` | tech_tree | `driftkings.views.hangar.tech_tree_marks_of_excellence` | `mods/driftkings/tech_tree_marks_of_excellence/model` |
| `DriftkingsProfileRatings` | hangar | `driftkings.views.hangar.profile_ratings` | `mods/driftkings/profile_ratings/model` |
| `DriftkingsRatingPlayers` | tab | `driftkings.views.battle.panel_gameface` | `mods/driftkings/panel_gameface/model` |
| `driftkingsbattleEfficiency` | results | `driftkings.views.hangar.battle_performance` | `mods/driftkings/battle_performance/model` |

### Fronteiras e referências indiretas

- `BattleCardAdapter`: reutilizar instalação idempotente, WeakKeyDictionary, listeners de HUD/cursor, comandos de posição, publicação e destruição. MainGun e marcas conservam subclasses; painel TAB conserva o lifecycle próprio de ViewImpl.
- Hangar: preservar HangarController, WeakKeyDictionary, eventos de carregamento/finalização, comandos e publicação deduplicada. Janelas conservam controllers e factories existentes.
- `views/hangar/hangar_preferences_hooks.py`: separar hooks modernos Gameface para `gameface/hangar/preferences_hooks.py`; hooks Scaleform ficam no local atual.
- `core/hud_visibility.py`: manter estado partilhado/Scaleform; extrair hooks TabView para `gameface/batalha/hud_visibility.py`, conservando o proprietário e a ativação do serviço.
- `views/battle/handler.py`: verificar integração nativa Wulf e separar apenas a integração Gameface, preservando o registo Scaleform.
- `components/main.py`: verificar imports Wulf de janelas nativas; integração de relógio/janelas próprias aponta para os novos adaptadores.
- `core/battle_capabilities.py`, `core/mod_compatibility.py` e `components/sound_bank_loader.py`: políticas, diagnóstico e integração nativa não constituem Views Gameface próprias; manter funcionalidade fora do package.
- `views/hangar/profile_statistics.py`, `battle_performance_hooks.py`, restantes views de batalha e `views/__init__.py`: Scaleform, preservar; atualizar apenas imports de bridges.
- `views/marks_model.py` e `crew_progression_model.py`: helpers de dados sem Wulf, preservar.
- Resolver imports diferidos/import_module, strings de ServiceSpec no core, catálogo, testes com caminhos de ficheiro e ferramentas de build.
- Recursos constantes ainda em módulos lobby: deslocar resolução para o adaptador quando exclusivamente visual; preservar FEATURE funcional se usado pelo componente.
- Não acrescentar exceções genéricas ou mecanismos de compatibilidade; exceções preexistentes não serão ampliadas.

## Etapas e validação

| Etapa | Âmbito | Estado | Evidência |
| --- | --- | --- | --- |
| 0 | Auditoria, mapa e decisão de nomes | Concluída | Inventário acima; nenhum código migrado |
| 1 | Package, núcleo, publicação partilhada, registo e comuns | Concluída | 419 testes core Python 3: OK |
| 2 | Adaptadores batalha, HUD e referências | Concluída | 419 testes core: OK |
| 3 | Adaptadores hangar e hooks mistos | Pendente | Testes controllers/carousel/profile/janelas |
| 4 | Contratos, fronteiras, documentação e release.json | Pendente | Testes arquitetura/imports/ciclos |
| 5 | Validação completa e build | Pendente | Python 2/3, npm, lint, build, GitHub CI |

## Registo de execução

- Etapa 0: analisados a árvore limpa, os 14 contratos, infraestrutura comum, serviços, imports estáticos/dinâmicos, testes e fronteiras Scaleform/Gameface. Mapa preparado antes de qualquer migração. Este documento acompanha cada commit de etapa; os hashes são consultáveis com `git log --oneline -- docs/PLANO_GAMEFACE.md`.

## Validação obrigatória no cliente

- Duas batalhas consecutivas: MainGun, marcas, TAB, esconder/mostrar HUD, cursor, posição e bloqueio; nenhuma interface órfã ao regressar ao hangar.
- Navegação hangar/tripulação/perfil/árvore/resultados, alterações de configuração, relógio e cabeçalho: não duplicar painéis nem listeners.
- Abrir/fechar/reabrir definições e contas, encaminhar comandos, guardar/aplicar e confirmar configurações preservadas.
- Automatização não prova o comportamento do runtime nativo; estes testes permanecem explicitamente pendentes até execução em jogo.

- Etapa 1 (`22d12d1`): movidos núcleo, registo de janelas e comuns; publicação extraída para `gameface/payloads.py` sem imports do motor, eliminando dependência batalha → hangar. Imports e testes atualizados; 419 testes core passaram. Auditoria inicial: `58086e7`. Uma leitura com encoding Windows impediu a atualização deste registo no commit de código; corrigida usando UTF-8 explícito antes de prosseguir.

- Etapa 2: migrados individualmente MainGun, marcas e TAB para `gameface/batalha`; catálogo, imports e testes alinhados. Hooks TabView extraídos do serviço HUD, mantendo proprietário/ativação originais. `handler.py` mantém-se Scaleform: WindowLayer apenas seleciona a página Flash nativa. Corrigida a pesquisa do teste de pares de eventos para abranger a árvore cliente inteira. 419 testes core: OK.
