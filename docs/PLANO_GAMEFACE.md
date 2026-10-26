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
| 3 | Adaptadores hangar e hooks mistos | Concluída | 419 testes core: OK |
| 4 | Contratos, fronteiras, documentação e release.json | Concluída | 10 novos testes de arquitetura: OK; catálogo/build data válidos |
| 5 | Validação completa e build | Validação local concluída; CI final em acompanhamento | Python 2/3, npm, lint e build: OK |

## Registo de execução

- Etapa 0: analisados a árvore limpa, os 14 contratos, infraestrutura comum, serviços, imports estáticos/dinâmicos, testes e fronteiras Scaleform/Gameface. Mapa preparado antes de qualquer migração. Este documento acompanha cada commit de etapa; os hashes são consultáveis com `git log --oneline -- docs/PLANO_GAMEFACE.md`.

## Validação obrigatória no cliente

- Duas batalhas consecutivas: MainGun, marcas, TAB, esconder/mostrar HUD, cursor, posição e bloqueio; nenhuma interface órfã ao regressar ao hangar.
- Navegação hangar/tripulação/perfil/árvore/resultados, alterações de configuração, relógio e cabeçalho: não duplicar painéis nem listeners.
- Abrir/fechar/reabrir definições e contas, encaminhar comandos, guardar/aplicar e confirmar configurações preservadas.
- Automatização não prova o comportamento do runtime nativo; estes testes permanecem explicitamente pendentes até execução em jogo.

- Etapa 1 (`22d12d1`): movidos núcleo, registo de janelas e comuns; publicação extraída para `gameface/payloads.py` sem imports do motor, eliminando dependência batalha → hangar. Imports e testes atualizados; 419 testes core passaram. Auditoria inicial: `58086e7`. Uma leitura com encoding Windows impediu a atualização deste registo no commit de código; corrigida usando UTF-8 explícito antes de prosseguir.

- Etapa 2: migrados individualmente MainGun, marcas e TAB para `gameface/batalha`; catálogo, imports e testes alinhados. Hooks TabView extraídos do serviço HUD, mantendo proprietário/ativação originais. `handler.py` mantém-se Scaleform: WindowLayer apenas seleciona a página Flash nativa. Corrigida a pesquisa do teste de pares de eventos para abranger a árvore cliente inteira. 419 testes core: OK.

- Etapa 3: migrados os 11 adaptadores hangar e os contratos respetivos; recursos de relógio, carrossel e marcas saíram dos componentes funcionais. Extraídos também os hooks ativos de presenters nativos de `lobby/hangar_preferences.py` para `native_preferences.py` e os hooks de layout/filtros/tooltips do carrossel. O componente fornece configuração e caches sem dependências circulares de inicialização. Separados os hooks Gameface do ficheiro misto `hangar_preferences_hooks.py`, preservando a ausência de ativação desse módulo não referenciado. A recolha de dados acionada por CrewPresenter permanece funcional. Todos os 419 testes core passaram. Batalha publicada em `bed9b5a`.

- Etapa 4: adicionados 10 testes cobrindo execução dos 14 adaptadores com fronteiras do motor simuladas, contexto/catálogo único, localização de Views, ciclos de imports imediatos, imports passivos, resolução nativa, transação e cache de payload, registo de janelas e hooks HUD/hangar. Corrigido um import `gameface_spec` em marcas de hangar identificado pelo verificador de nomes indefinidos; 0 nomes indefinidos. Imports do package ordenados com isort. Catálogo: 10 Flash, 14 Gameface e 12 injetados; build data: 301 módulos, 39 manifests, 223 assets, 53 defaults. Atualizados CONTRIBUTING, guias atuais, nota histórica, STATUS e changelog sem alterar a versão publicada. Hangar publicado em `8456378`.

## Estrutura final e dependências

```text
driftkings/gameface/
  __init__.py
  core.py                 # recursos nativos e assets Wulf
  payloads.py             # publicação transacional, sem motor
  registry.py             # registo de janelas existente
  batalha/
    __init__.py
    common.py             # BattleCardAdapter existente
    battle_marks_of_excellence.py
    high_caliber_gameface.py
    panel_gameface.py
    hud_visibility.py     # lifecycle TAB nativo
  hangar/
    __init__.py
    common.py
    account_manager.py
    battle_performance.py
    crew_details.py
    crew_progression.py
    hangar_marks_of_excellence.py
    hangar_preferences.py
    main.py
    native_preferences.py # hooks ativos extraídos do componente
    preferences_hooks.py  # parte Gameface do módulo misto
    profile_ratings.py
    settings_window.py
    tech_tree_marks_of_excellence.py
    vehicle_carousel.py
```

- Os 18 ficheiros do mapa inicial foram movidos, removendo as implementações antigas sem shims. Criados 3 `__init__.py`, `payloads.py`, `batalha/hud_visibility.py`, `hangar/native_preferences.py` e `hangar/preferences_hooks.py`. Criado `tests/core/test_gameface_architecture.py`. O teste de eventos pesquisa agora todo o cliente.
- Componentes funcionais → adaptadores de contexto → núcleo/catalogue e APIs WG. Adaptadores usam dados dos componentes via referências diferidas; não existem ciclos de imports imediatos entre os módulos Gameface.
- `interface_catalog.py`: alterados apenas os 14 campos `python`. IDs, recursos, contextos, owners, scripts, estilos e URLs preservados. `core` aponta WindowViews para `gameface.registry`. Os testes seguem os caminhos novos.
- Hooks de preferências ativos são instalados no mesmo âmbito do proprietário funcional. Não foram ativados os hooks do antigo módulo misto não referenciado, para não introduzir alterações funcionais.
- `core/battle_capabilities` continua a consultar capacidades nativas; diálogo de aviso de sound banks usa o builder nativo, sem implementação de View própria; CrewPresenter apenas aciona recolha de dados. Estas dependências não são adaptadores de apresentação próprios.
- Nenhuma alteração em `mod/res/gui`: HTML/CSS/JS, declarações nativas e bootstrap idênticos à base. Sem alterações às configurações EU nem instalação de pacote.

## Resultados finais de validação local

| Verificação | Resultado |
| --- | --- |
| Core Python 3 / Python 2.7 | 429 / 429 testes: OK |
| Settings panel Python 3 / Python 2.7 | 27 / 27 testes: OK |
| Installer Python 3 | 33 testes: OK |
| `npm test` / `npm run lint` | OK / OK |
| Catálogos de tradução | 18 idiomas; 1491 chaves de componentes, 170 de painel; 0 não traduzidas |
| Defaults gerados | Sincronizados; 34 componentes |
| Nomes indefinidos / isort do package | 0 / OK |
| Catálogo UI e build inputs | 14 Gameface, 10 Flash, 12 injetados; 39 manifests, 301 módulos, 223 assets, 53 defaults |
| Comparação com a base | Somente os 14 caminhos Python mudaram no catálogo; nenhum outro campo; nenhum recurso visual modificado |
| Pesquisa dos caminhos Python antigos | Nenhuma referência ativa em runtime, testes, build tools ou build data |
| Build debug beta com toolchain real | OK; 301 módulos compilados/verificados em Python 2.7; WOTMOD gerado em `build/debug/beta/0.1.3-beta.2` |

- Etapa 5: concluídas as validações acima. A build foi repetida após as correções finais. A reposição nativa do layout/filtros do carrossel também ficou no adaptador, chamada pelo `fini` funcional.
- Corrigidos os testes de hooks que usavam metadados de funções num namespace de builtins simulado: Python 2.7 restringe essa escrita. Aplicado o mesmo padrão de setter externo já usado pelos testes de BattleCardAdapter. A autoria de hooks do runtime é preservada.
- CI intermédio de `8456378` detetou o import em falta documentado na etapa 4; CI de `d916f05` detetou a limitação dos testes Python 2.7, corrigida nesta etapa. Estes resultados não são tratados como validações aprovadas. O CI do commit final será acompanhado após push.
- Nenhuma versão publicada, tag alterada ou instalação EU substituída. Os testes no cliente listados acima continuam pendentes.
