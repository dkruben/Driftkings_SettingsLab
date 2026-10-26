# Revisão de _constants.py

> Atualização de contexto — 26/10/2026: A listagem e as contagens abaixo pertencem à revisão original; não foram recalculadas nesta atualização. O relógio atual usa `main.clock.formats`, a compatibilidade Python 2/3 está em `common/utils/compat.py` e o pacote publicado contém 293 módulos Python. Para o código atual, consultar os validadores e testes indicados no guia de contribuição. Ver o [estado atual](STATUS.md) e o [guia de contribuição](../CONTRIBUTING.md).

Registo da análise estática original, com resolução de imports e aliases.

Módulos analisados: 269. Atributos definidos: 412. Sem referências a atributos: 78.

A ausência de referência à constante não significa que a opção JSON esteja sem efeito. Muitas chaves são usadas diretamente como texto. Não remover defaults, traduções ou opções com base apenas nesta lista.

## Atributos sem referências

### GLOBAL

- `FONT` = `font`
- `ALIGN` = `align`
- `CENTER` = `center`
- `DISTANCE` = `distance`
- `ANGLE` = `angle`
- `SIZE` = `size`
- `BLUR_X` = `blurX`
- `BLUR_Y` = `blurY`
- `STRENGTH` = `strength`
- `SHADOW` = `shadow`
- `QUALITY` = `quality`
- `LEADING` = `leading`
- `VISIBLE` = `visible`
- `BORDER` = `border`
- `INDEX` = `index`
- `LINE` = `_`
- `EMPTY_LYNE` = `  `
- `IMAGE` = `image`
- `BLUR` = `blur`

### THIRD_PERSON_ZOOM

- `MAX` = `max`
- `MIN` = `min`
- `SCROLL_SENSITIVITY` = `scrollSensitivity`
- `START_DEAD_DIST` = `startDeadDist`

### PENETRATION_INDICATOR

- `POSITION` = `position`

### BATTLE_STATISTICS

- `TEXT_SHADOW` = `textShadow`

### AIMING_RETICLES

- `SHOW_CLIENT_AND_SERVER_RETICLE` = `showClientAndServerReticle`

### HIGH_CALIBER_PROGRESS

- `BACKGROUND` = `background`

### BATTLE_MARKS_OF_EXCELLENCE

- `BUTTON_SHOW` = `buttonShow`
- `SHOW_IN_HANGAR` = `showInHangar`
- `PANEL_SIZE` = `panelSize`
- `BATTLE_MESSAGE` = `battleMessage`
- `BATTLE_MESSAGE_ALT` = `battleMessageAlt`
- `BATTLE_MESSAGE_STATUS_UP` = `battleMessage{status}Up`
- `BATTLE_MESSAGE_C_STATUS_UP` = `battleMessage{c_status}Up`
- `BATTLE_MESSAGE_STATUS_DOWN` = `battleMessage{status}Down`
- `BATTLE_MESSAGE_C_STATUS_DOWN` = `battleMessage{c_status}Down`
- `BATTLE_MESSAGE_STATUS_UNKNOWN` = `battleMessage{status}Unknown`
- `BATTLE_MESSAGE_C_STATUS_UNKNOWN` = `battleMessage{c_status}Unknown`
- `BATTLE_MESSAGE_BATTLE_MARK_OF_GUN` = `battleMessage{battleMarkOfGun}`
- `BATTLE_MESSAGE_C_BATTLE_MARK_OF_GUN` = `battleMessage{c_battleMarkOfGun}`
- `BATTLE_MESSAGE_CURRENT_MARK_OF_GUN` = `battleMessage{currentMarkOfGun}`
- `BATTLE_MESSAGE_C_CURRENT_MARK_OF_GUN` = `battleMessage{c_currentMarkOfGun}`
- `BATTLE_MESSAGE_NEXT_MARK_OF_GUN` = `battleMessage{nextMarkOfGun}`
- `BATTLE_MESSAGE_C_NEXT_MARK_OF_GUN` = `battleMessage{c_nextMarkOfGun}`
- `BATTLE_MESSAGE_DAMAGE_CURRENT` = `battleMessage{damageCurrent}`
- `BATTLE_MESSAGE_C_DAMAGE_CURRENT` = `battleMessage{c_damageCurrent}`
- `BATTLE_MESSAGE_DAMAGE_CURRENT_PERCENT` = `battleMessage{damageCurrentPercent}`
- `BATTLE_MESSAGE_C_DAMAGE_CURRENT_PERCENT` = `battleMessage{c_damageCurrentPercent}`
- `BATTLE_MESSAGE_DAMAGE_NEXT_PERCENT` = `battleMessage{damageNextPercent}`
- `BATTLE_MESSAGE_C_DAMAGE_NEXT_PERCENT` = `battleMessage{c_damageNextPercent}`
- `BATTLE_MESSAGE_DAMAGE_TO_MARK65` = `battleMessage{damageToMark65}`
- `BATTLE_MESSAGE_C_DAMAGE_TO_MARK65` = `battleMessage{c_damageToMark65}`
- `BATTLE_MESSAGE_DAMAGE_TO_MARK85` = `battleMessage{damageToMark85}`
- `BATTLE_MESSAGE_C_DAMAGE_TO_MARK85` = `battleMessage{c_damageToMark85}`
- `BATTLE_MESSAGE_DAMAGE_TO_MARK95` = `battleMessage{damageToMark95}`
- `BATTLE_MESSAGE_C_DAMAGE_TO_MARK95` = `battleMessage{c_damageToMark95}`
- `BATTLE_MESSAGE_DAMAGE_TO_MARK100` = `battleMessage{damageToMark100}`
- `BATTLE_MESSAGE_C_DAMAGE_TO_MARK100` = `battleMessage{c_damageToMark100}`
- `BATTLE_MESSAGE_DAMAGE_TO_MARK_INFO` = `battleMessage{damageToMarkInfo}`
- `BATTLE_MESSAGE_C_DAMAGE_TO_MARK_INFO` = `battleMessage{c_damageToMarkInfo}`
- `BATTLE_MESSAGE_DAMAGE_TO_MARK_INFO_LEVEL` = `battleMessage{damageToMarkInfoLevel}`
- `BATTLE_MESSAGE_C_DAMAGE_TO_MARK_INFO_LEVEL` = `battleMessage{c_damageToMarkInfoLevel}`
- `BATTLE_MESSAGE_ASSIST_SPOT` = `battleMessage{assistSpot}`
- `BATTLE_MESSAGE_ASSIST_TRACK` = `battleMessage{assistTrack}`
- `BATTLE_MESSAGE_ASSIST_SPAM` = `battleMessage{assistSpam}`
- `UI` = `UI`

### VEHICLE_HEALTH

- `COLORS` = `colors`

### TEAM_PANELS

- `SCHEMA_VERSION` = `schemaVersion`

### ACCOUNT_MANAGER

- `NAME` = `account_manager`

### HANGAR_PREFERENCES

- `TEXT` = `text`
- `PANEL` = `panel`

### HANGAR_MARKS_OF_EXCELLENCE

- `STAR_ANIMATION_WINDOW` = `starAnimationWindow`

### SOUND_BANK_LOADER

- `DEFAULT_POOL` = `defaultPool`
- `LOW_ENGINE_POOL` = `lowEnginePool`
- `MEMORY_LIMIT` = `memoryLimit`
- `STREAMING_POOL` = `streamingPool`
- `IOPOOL_SIZE` = `IOPoolSize`
- `MAX_VOICES` = `max_voices`

## Constantes de topo sem referências

- `CONFIG_SECTIONS`

## Interpretação e prioridade

- CONFIG_SECTIONS não tem consumidores no repositório atual. O registo efetivo usa components/component_list e as definições de settings.
- ACCOUNT_MANAGER.NAME não tem consumidores diretos no cliente, mas é necessário aos geradores de defaults e catálogo UI por análise AST. Deve ser preservado.
- HANGAR_PREFERENCES.TEXT e PANEL são resíduos do relógio antigo. O relógio atual usa customClockText e os campos clockX/clockY/clockScale.
- As constantes BATTLE_MARKS_OF_EXCELLENCE.BATTLE_MESSAGE_* e vários controlos de apresentação antigos não são referenciados pelo painel Gameface atual.
- As seis constantes SOUND_BANK_LOADER não referenciadas representam opções ainda presentes nos defaults e consumidas através de strings e metadados automáticos. São aliases não usados, não funcionalidades abandonadas.
- BATTLE_STATISTICS.TEXT_SHADOW e TEAM_PANELS.SCHEMA_VERSION também correspondem a dados existentes. A ausência de referência ao alias não permite apagar o campo.
- Os limites antigos de THIRD_PERSON_ZOOM continuam relevantes na migração de configurações, que usa strings em core/camera_settings.py; a constante é redundante, mas a migração deve ser preservada.

Não foram removidas constantes, configurações ou traduções nesta revisão.

## Limpeza aplicada

Removidos 77 atributos listados e CONFIG_SECTIONS. ACCOUNT_MANAGER.NAME foi preservado: build_tools/generate_defaults.py e generate_ui_catalog.py descobrem os nomes das secções por análise AST. Defaults, traduções e lógica de migração preservados.
