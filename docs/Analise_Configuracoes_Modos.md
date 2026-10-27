# Driftkings — comparação XVM WG, configurações e modos

> Atualização de contexto — 26/10/2026: As decisões e evidências abaixo descrevem as etapas de outubro, não o estado integral atual. A beta 0.1.3-beta.2 já foi publicada. Os marcadores usam agora ficheiros XVM-style, contextos por equipa/estado/ALT, estatísticas partilhadas e editor integrado; o âmbito dos modos continua explícito. Referência atual: EU 2.4.1.5498. Os snapshots de auditoria continuam locais. Ver o [estado atual](STATUS.md) e o [guia de contribuição](../CONTRIBUTING.md).

Data: 2026-10-19. Repositório de partida: `fe55729`. Referência local XVM: `WoT_Tools/Atualizados/XVM`, commit `19b8a78` de 2026-10-15. Cliente fonte consultado: EU `2.4.1.5488`.

## Âmbito e decisões do utilizador

Manter apresentação e preferências Driftkings; corrigir compatibilidade. A análise de modos identifica o que o código realmente permite e as dependências necessárias, sem ativar módulos em todos os modos por presunção.

Foram autorizados e implementados nesta etapa: remover `sniper_camera.dynamicZoom` sem consumidor; separar câmaras arcade/pós-destruição/artilharia; manter os valores Driftkings no arcade e deixar a artilharia ler os defaults do cliente.

Sem commit, push ou release nesta etapa. Os ficheiros instalados no jogo não foram alterados. O relatório Markdown está agora versionado em `docs/`; os dados de auditoria continuam locais e ignorados pelo Git.

## Método e limites

Resolvida a árvore real `release/configs/default_wg/@xvm.xc` com o próprio JSONxLoader local, incluindo referências entre ficheiros. Comparadas as configs WG, sem importar os defaults Lesta. O nome “Atualizados” não prova compatibilidade: a revisão e a versão consultadas estão identificadas acima.

Inventário inicial, antes das correções autorizadas: 45 JSON em `res/configs/Driftkings/default`, 1 173 entradas escalares/listas (inclui entradas repetidas entre representações do minimapa), 41 chaves homónimas diretamente comparáveis em hangar/carrossel/sniper. A build valida 46 documentos default no contrato completo.

Uma pesquisa por consumidores produziu 178 candidatos sem referência literal óbvia. **Não são 178 erros**: muitos campos são construídos dinamicamente, encaminhados genericamente para Flash ou consumidos por kwargs. Por exemplo, brilho/saturação da barra de vida são encaminhados para `percentToRgb`. Só os problemas abaixo classificados como confirmados têm evidência adicional.

Não houve validação nova em batalha. Uma API/classe disponível é condição necessária, não prova de funcionamento num evento com respawn ou veículos especiais.

Dados locais: `docs/xvm_audit/xvm_wg_resolved.json`, `shared_values_comparison.json`, `battle_hooks.json`, `unreferenced_candidates.json`.

## Comparação por área

| Área Driftkings | Referência XVM WG | Resultado e ação |
| --- | --- | --- |
| `sniper_camera` | `battle.camera.sniper`, `camera.noFlashBang` | Zooms e binoculars têm implementação. `dynamicZoom` não tinha consumidor: removido. Não copiar `zooms` para `zoomSteps` sem conversão. As regras de validação Driftkings exigem pelo menos 4 níveis únicos >= 2. |
| `third_person_zoom` | `battle.camera.arcade/postmortem/strategic` | Havia um único intervalo para 3 câmaras e a distância de morte também era usada no arcade. Perfis separados implementados; inclui também a câmara alternativa `ArtyCamera` do cliente. |
| `vehicle_carousel` | `hangar.carousel`, `carouselNormal/Small.xc` | Semelhança elevada de aparência e estrutura, mas não compatibilidade total. Preservar recursos Driftkings. `SORT_KEYS` não implementa todos os critérios XVM: faltam, por exemplo, `maxBattleTier`, `xtdb`, `xte`, `wtr`. Não adicionar defaults que dependam deles. |
| `minimap_enhancements` | `minimap`, `minimapAlt`, labels/circles/lines | Estruturas diferentes: XVM tem labelsData e campos genéricos; Driftkings usa esquemas próprios. Necessária tradução explícita, sem substituição direta dos JSON. O minimapa nativo existente foi preservado; não reintroduzido Tactical Minimap. |
| `team_panels` | `playersPanel`, `battleLoading`, `statisticForm` | Existem macros, templates, refs e campos extras. O avaliador suporta condicionais aninhadas, mas os valores disponíveis não equivalem a todos os serviços XVM. Validar por ecrã e renderer, não só por sintaxe. |
| `hangar_preferences` | `hangar`, `combatIntelligence`, `sessionStatsButton`, widgets | Várias opções equivalentes estão achatadas no Driftkings. Os valores diferentes são escolhas do utilizador. Presets antigos do relógio ainda constam do JSON embora `normalize_loaded` os remova; candidato a limpeza canónica numa etapa seguinte. |
| `crew_management` | `hangar.enableCrewAutoReturn`, `crewReturnByDefault` | Funções relacionadas, com nomes diferentes e extensões próprias de XP/estimativa. Não transportar nomes XVM para o JSON sem mapeamento. |
| `sixth_sense_alert` / bancos de som | `battle.sixthSense`, `sounds` | Imagem e som exigem recursos, nomes de eventos e consumidores reais. Listas de bancos/mapeamentos XVM não têm contrato idêntico ao nosso loader. |
| Estatísticas/cores | `colors`, stats e serviços XVM | Reutilizar conceitos de escalas e apresentação. As estatísticas Driftkings usam o seu backend WG; isto não fornece automaticamente XTE, XTDB, XM QP ou macros Python XVM. |
| Restantes módulos | Sem equivalente direto obrigatório | MainGun, retículas, reparação manual, sincronização da torre e restantes utilitários conservam os seus contratos próprios. Ausência no XVM não torna o módulo incompatível. |

## Problemas confirmados e trabalho necessário

### Implementado nesta etapa

1. `sniper_camera.dynamicZoom.enabled/stepsOnly`: declarados nos defaults, sem leitura no runtime. Removidos do JSON e descartados ao carregar/aplicar configs antigas. Nenhuma implementação fictícia criada.
2. `third_person_zoom`: perfis `arcade`, `postmortem`, `strategic`, `arty`; arcade e pós-destruição iniciam com 10–400, sensibilidade 11, distância inicial 60, preservando a configuração anterior. Artilharia usa `useClientDefaults: true`: os valores efetivos são os lidos pelos métodos WG, não números inferidos do XVM.
3. Os valores 40–120/sensibilidade 5 nos perfis de artilharia são apenas o ponto de partida do override manual, inspirado na referência XVM. **Não são apresentados como os valores nativos efetivos**. Enquanto `useClientDefaults` estiver ativo, não são aplicados.
4. Migração dos campos antigos `min/max/scrollSensitivity/startDeadDist` antes do merge: preserva valores pessoais em arcade e pós-destruição e respeita perfis novos já explícitos. Uma distância inicial antiga fora dos limites é ajustada ao intervalo, tal como o clamp da câmara. Valores inválidos não finitos continuam rejeitados.
5. Controlos do painel para os quatro perfis, validação de intervalos e de distância inicial, defaults Python/snapshot regenerados. O novo esquema exige reinício do cliente como a configuração anterior.
6. Deixou de haver o mecanismo que limpava dicionários de configuração de câmaras globalmente antes da leitura: os hooks deixam o cliente ler primeiro e aplicam apenas o perfil selecionado. Desativar o módulo não força valores.

### Confirmado, ainda por corrigir após definição da próxima etapa

- **Macros do minimapa não são macros XVM completas.** `core/minimap.py:MACRO` suporta vehicle/name/level/type/state/hp/maxHp/hpPercent/lostSeconds e truncagem simples. Demonstração executada: `{{vehicle}} {{hp}}/{{hp-max}}` produz `Tiger 500/{{hp-max}}`. É necessário converter `hp-max` para `maxHp` ou acrescentar aliases testados; condicionais/cores XVM não podem ser despejadas neste renderer de texto simples.
- **Região dos painéis:** `views/battle/player_ratings.py` coloca `values['region']='EU'` para os valores das macros. Isto é incorreto como macro global numa instância NA/ASIA. O backend `core/player_ratings.py` já suporta `eu/com/asia`, pelo que não se deve confundir esta etiqueta com a seleção real da API. Corrigir a origem da região com a semântica WG do cliente, não por texto fixo.
- **Tradução de macros:** `core/panel_model.py:screen` passa `{'Destroyed':'Destruido'}` ao avaliador; outros idiomas não recebem aqui uma tradução própria. Encaminhar o catálogo ativo, mantendo compatibilidade com os templates atuais.
- **Torre do servidor:** `battle/server_turret_sync.py` atribui diretamente `gun_rotation_shared.decodeRestrictedValueFromUint` e `decodeAngleFromUint` no import. Estas substituições globais não consultam `enabled`, não escolhem modo e não têm restauração no `fini`. Refatorar para ownership/restauração e justificar que a alteração global ainda é necessária no cliente atual antes de aprovar suporte amplo por modo.
- **Campos do indicador de alvo:** `catchHiddenTarget`, `angle`, `disableArtyMode` ficaram como compatibilidade antiga; o módulo atual apenas desenha uma caixa no alvo já bloqueado pelo jogo. Não implementar aquisição/seguimento de alvo a partir destes campos. Limpar/migrar os campos obsoletos ou implementar somente uma restrição de apresentação para artilharia após decisão explícita.
- **Presets de relógio:** `clockStyle/clockSeconds/clock24Hour/customClockFormat` estão nos defaults, mas são explicitamente retirados em `HangarPreferencesSettings.normalize_loaded`. Limpar o JSON para refletir a implementação atual baseada em `customClockText`, sem perder esse texto/posição.
- **Duas representações do minimapa:** o JSON de topo tem `minimapSchema:0`; os documentos separados canónicos têm `1`. A geração usa os separados. A normalização existe e os valores atuais dos círculos coincidem; não foi confirmado um defeito visual. Unificar a fonte de manutenção para evitar divergência futura.

### Lacunas que exigem código novo, não correção de um número

Critérios de ordenação XVM adicionais; schemas de labelsData e extraFields do minimapa; tabelas/macros cujo dado só existe em serviços XVM; callbacks/macros `py:`; importação de referências `${...}`/`.xc`; conversão entre HTML Flash e texto Gameface. Não são suportados apenas por se adicionar a chave a um JSON.

O loader Driftkings continua a receber os seus JSON. O JSONxLoader foi usado somente nesta auditoria local, sem acrescentar dependência XVM ao mod.

## Modos: restrições reais no código

Legenda: **B** bloqueado explicitamente; **C** candidato condicionado à API/UI nativa correspondente; **I** herda a arena de origem do replay. C não significa testado ou garantido.

| Módulo | Restrição atual / condições reais | Implicação para outros modos |
| --- | --- | --- |
| `battle_marks_of_excellence` | `battle_policy`: exige bonusType REGULAR e dados do veículo | Treino, Topography, Frontline e eventos ficam B pela política atual. Não presumir elegibilidade de Grandes Batalhas: EPIC_RANDOM também fica fora de REGULAR. Replay I mais opção showInReplay. |
| `high_caliber_progress` | REGULAR e guiType RANDOM/EPIC_RANDOM; sem alvo inicial não publica | Mesma exclusão por bonusType; a aceitação de guiType EPIC_RANDOM por si só não ultrapassa a política. |
| `battle_statistics` | REGULAR; depende dos dados estatísticos/equipas | Outros modos B hoje; alargar exige validar significado dos cálculos e dados por modo, não retirar simplesmente o guard. |
| `battle_performance` | whitelist própria SUPPORTED_BONUS_TYPES={REGULAR} | B nos restantes, independente da política central. Há uma lista adicional de modos no ficheiro, mas a condição de exibição usa SUPPORTED_BONUS_TYPES. |
| `minimap_enhancements` | `battle_range` e plugins nativos; evita substituir quando deteta XVM | Training e Comp7/Frontline constam da whitelist, mas C por plugins específicos/respawn. MAPS_TRAINING/Topography e EVENT_BATTLES não constam. XVM usa uma blacklist diferente e exclui Comp7/Frontline para o seu minimapa: não copiar como regra para o nosso. |
| `team_panels` | Sem gate central por modo; Flash + Gameface TAB e ramo White Tiger | C nos modos com essas interfaces e roster convencional. Frontline e eventos exigem validar respawn, mais de 15 participantes, ordenação, observador e tipo de ecrã. Não prometer cobertura só pelo registo global. |
| `sniper_camera` | Métodos da SniperCamera; `_readConfigs` ignora replay | C onde existe sniper nativo. No replay a lista de zoom e noSniperDynamic não são aplicados por esse hook; outros efeitos têm hooks próprios. |
| `third_person_zoom` | Classes Arcade/Strategic/Arty e modo pós-destruição | C onde o modo usa essas classes; artilharia mantém nativo por defeito. Câmaras próprias de eventos/observador não ficam automaticamente cobertas. |
| `aiming_reticles` | AvatarInputHandler, gun markers e SharedPage | C nos modos com esse caminho; rever marcadores duplos, canhões auxiliares e mecânicas de evento. |
| `aiming_countdown` | Crosshair e componente Flash | C com controlador de mira e view correspondente; treino/Topography candidatos se o HUD nativo os fornece. |
| `gun_traverse_limits` | Câmaras/ângulos, MapCase e apresentação própria | C; mascarar em seleção de veículo, morte, respawn e observação. Eventos com armas diferentes precisam de validação. |
| `artillery_blast_radius` | Descriptor SPG, munição e ctrlModeName | Condição de veículo/munição, não apenas modo. C em qualquer arena com SPG compatível; ocultar onde não há esses dados. |
| `shell_flight_time` | `battle_policy` exige batalha e, conforme config, SPG; gunRotator/crosshair | Não tem restrição REGULAR. C em treino/Topography/outros modos com essas APIs. Já oculta em modos de morte, seleção e respawn. |
| `penetration_indicator` | plugins de mira, colisão e descriptor da arma | C; veículos especiais, partes destrutíveis, armas auxiliares e projéteis especiais exigem teste próprio. |
| `target_distance` | input handler + VehicleMarkerPlugin | C se o marcador nativo e entidade-alvo existem; não presumir em câmaras de observador/evento. |
| `target_information` | targetFocus/Blur e dados do descriptor | C com alvo normal e dados disponíveis; estatísticas derivadas não equivalem a capacidades especiais desconhecidas. |
| `autoaim_target_indicator` | alvo nativo já bloqueado, vivo, visível, sem colisão de cobertura | C onde o jogo disponibiliza esse alvo; não adquire nem dirige mira. Não deve ganhar capacidades por copiar flags antigas. |
| `enemy_spotting_status` | eventos de feedback de deteção/assistência | C quando o modo emite esses eventos; ausência de evento não significa necessariamente erro da config. |
| `sixth_sense_alert` | SixthSenseIndicator e ícone carregado | C onde existe o indicador nativo; preserva o aviso original enquanto o substituto não está pronto. |
| `vehicle_health` | veículo controlado, estado HEALTH, arena period e HUD | C em modos normais; Frontline/eventos precisam de confirmar troca de veículo, respawn e maxHP. |
| `repair_controls` | consumíveis/painel nativo e veículo controlado; replay bloqueado | C em treino/outros modos com consumíveis convencionais; não tratar habilidades de evento como kits normais. Continua manual. |
| `battle_preferences` | Conjunto de hooks de UI, sons, chat, hints, recarga e equipas | Deve ter política por opção, não um sim/não para o módulo inteiro. Hints de tutorial, voz/sons de evento, chat e reload têm capacidades diferentes. |
| `server_turret_sync` | hook de ângulos + substituições globais descritas acima | Sem gate real por modo; pendente ownership e análise de mecânicas. Não classificar “compatível com todos”. |

### Módulos fora de batalha

`hangar_preferences` (incluindo Account Manager), `crew_management`, `vehicle_carousel`, `clan_reward_collection`, `hangar_marks_of_excellence`, `tech_tree_marks_of_excellence` são módulos de login/hangar/árvore. Avaliar os diferentes hangares e veículos de evento, sem “ativá-los numa batalha”.

`sound_bank_loader` e `game_log_manager` são serviços transversais: o carregamento do serviço não implica desenhar UI ou executar ações em todos os modos. O updater é infraestrutura, não módulo de batalha.

### Arquitetura que explica as diferenças

`views/__init__.py` regista o pacote Flash em todos os guiTypes conhecidos e extensões já registadas. `views/battle/handler.py` procura as páginas efetivas. Isto disponibiliza uma biblioteca; não valida os pressupostos de cada componente.

`RandomHUDView` também é usado por várias páginas além das aleatórias no SRC WG. Portanto, o nome da classe não restringe sozinho os módulos Gameface a Random. As restrições de stats/medalhas vêm de `battle_policy`.

`battle_capabilities.current_mode` distingue random/comp7/frontline/event/white_tiger/special, mas Training/Topography não têm categorias explícitas e podem cair em `special`. A política não usa uma matriz completa de capacidades por componente. Nem todos os módulos a consultam.

O SRC base não garante conhecer todas as extensões ativas no cliente NA/EU/ASIA. Os enums/huds das extensões devem ser resolvidos pelo cliente; evitar números mágicos copiados das listas XVM WG/Lesta.

## Plano recomendado, com ordem de execução

1. Concluir esta etapa com testes e build das duas correções autorizadas, preservando os defaults visuais Driftkings.
2. Corrigir região/i18n dos painéis e preparar testes para NA/ASIA e idiomas diferentes de português.
3. Limpar os defaults explicitamente aposentados (relógio/alvo) e a duplicação de representação do minimapa; não reativar funcionalidades antigas.
4. Definir um contrato de compatibilidade por schema: campo suportado, condicionado, obsoleto, ausente ou externo. Acrescentar aviso explícito para macros não suportadas em vez de deixar tokens literais.
5. Rever/restaurar as alterações globais da torre do servidor e comparar os hooks de retículas para não alterar comportamentos quando desativados.
6. Implementar política por capacidade: HUD disponível, veículo controlado, respawn, arma/munição, consumíveis, estatísticas e elegibilidade. Separar política do modo de controlo da câmara.
7. Testar primeiro treino/Topography para UI e controlos, replay para apresentação, e depois cada modo especial com casos próprios. Estes testes não validam cálculos/medalhas apenas por parecerem corretos num replay.
8. Só publicar novos defaults depois dos contratos e testes por modo. Não substituir preferências existentes por valores XVM.

## Verificações desta etapa

60 testes core e 25 de settings passaram em Python 3 e Python 2.7. Incluem 9 testes novos das câmaras: migração, preservação de perfis explícitos, clamp legado, intervalos inválidos, leitura real dos defaults nativos por stubs, overrides independentes, início pós-destruição, desativação e remoção de dynamicZoom no loader.

`validate_build_data.py`, `validate_locales.py`, testes Gameface e ESLint ES5 passaram. As novas chaves dos modos têm tradução própria em pt/en/es/de/fr e fallback inglês nos restantes catálogos, permitido pelo CONTRIBUTING; revisão nativa pendente.

Compilação e sintaxe de todos os JS verificadas no fecho da etapa. Ainda é necessário confirmar as câmaras no WoT: arcade, pós-destruição, vistas de artilharia, mudança de modo, replay e reinício entre batalhas. Nenhuma das restantes propostas deste relatório foi aplicada automaticamente.

Verificação adicional do instalador: 19/21 testes passaram. Dois falham porque `GeneratorTests.setUp` copia todo `installer/setup`, incluindo assets locais ignorados, enquanto os casos testados assumem que não há previews/ícone. Nenhum ficheiro de instalador nem asset foi alterado nesta etapa. Os testes precisam de fixtures isoladas desses assets para serem reproduzíveis no ambiente local.

## Atualização — etapa 1 concluída

Corrigida a macro `region` para usar `realm.CURRENT_REALM` do cliente em vez de `EU`, incluindo a região na chave da cache dos contextos. A escolha de servidores da API de estatísticas não foi alterada.

`Roster` recebe um catálogo de traduções; o adaptador encaminha `UI_panel_destroyed` do idioma ativo. A mesma tradução funciona em painel, loading, TAB e campos extra. A mudança de tradução invalida apenas as caches de apresentação necessárias. A macro existente `{{l10n:Destroyed}}` foi preservada e há traduções nos 18 catálogos.

Novos testes executam o pipeline real de roster/macros/cache para EU, NA, ASIA e CT, mudança de idioma, campos extra e fallback de chave desconhecida. Passaram 63 testes core e 25 settings em Python 2.7 e 3; Gameface, ESLint ES5, sintaxe JS, validação de build/locales e verificação de nomes indefinidos também passaram.

A tentativa de compilação foi bloqueada antes da geração: a referência local passou para `2.4.1.5493`, enquanto o contrato de build e o manifesto SWC continuam a declarar `2.4.1.5488`. Não foram alterados o SRC, o contrato nem o manifesto para contornar essa verificação. Não foi gerado um novo `.wotmod` desta etapa e não houve teste dentro do WoT.

Etapas 2 (limpeza dos defaults), 3 (aliases/validação de macros do minimapa) e 4 (ownership/restauração da torre) continuam por implementar. Sem commit/push automático.

## Atualização — etapa 2 concluída

Removidos dos defaults `clock24Hour`, `clockSeconds`, `clockStyle` e `customClockFormat`. Preservados `customClockText`, posição X/Y, escala, fundo e todas as opções ativas do hangar. Removidos `angle`, `catchHiddenTarget` e `disableArtyMode` dos defaults do indicador de alvo; apenas `enabled` permanece. Não foi alterado o comportamento da caixa sobre o alvo nativo.

As normalizações de ambos os módulos descartam os campos obsoletos ao carregar/aplicar, sem modificar opções desconhecidas pessoais. Removidas as constantes sem consumidores correspondentes; defaults Python e snapshot regenerados pelo gerador oficial. Os ficheiros instalados no cliente não foram editados diretamente.

Passaram 66 testes core e 25 settings em Python 2.7 e 3, testes Gameface, ESLint ES5, verificação de nomes indefinidos, validação de build e sincronização de defaults. Três testes novos verificam preservação do formato/posição/opções pessoais, remoção idempotente e o contrato dos JSON canónicos.

Etapas 1 e 2 concluídas localmente; continuam pendentes 3 (minimapa) e 4 (torre). Mantém-se o bloqueio de compilação por divergência do SRC já identificado na etapa 1. Sem commit nem push automático.

## Atualização de caminhos Flash — 27 outubro 2026

As referências a `views/battle`, `meta/battle`, `views/hangar` e ao registo em `views/__init__.py` neste relatório são históricas. A apresentação Scaleform atual está em `flash/`, conforme o [inventário e plano Flash](PLANO_FLASH.md). Os helpers de dados independentes das tecnologias permanecem em `views`.
