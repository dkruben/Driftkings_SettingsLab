# Revisão funcional das traduções — 22/10/2026

> Atualização de contexto — 26/10/2026: Os números de remoções e alterações abaixo descrevem a revisão de 22/10. Os catálogos atuais incluem os controlos posteriores de General/relógio e marcadores: 1491 chaves de componentes e 170 do painel, em 18 idiomas. A validação atual exige cobertura completa; revisão linguística humana continua distinta de cobertura de chaves. Ver o [estado atual](STATUS.md) e o [guia de contribuição](CONTRIBUTING.md).

Revisão dos 18 recursos YML contra as definições e o código de runtime.
Removidas 91 chaves obsoletas por idioma; atualizadas 23 chaves inglesas e as correspondentes traduções; acrescentadas quatro chaves em cada idioma.
A validação das declarações percorre os controlos atuais nos 18 idiomas, incluindo as opções e os separadores agora ligados às traduções.

## Evidência e alterações

- Autoaim: apenas realce do alvo nativo; removidos textos de seleção através de obstáculos e ângulo de aquisição.
- Marcas: removidos estilos e atalhos de apresentação antigos; mantidas as opções atuais do Gameface, estimativas de replay e tooltips realmente utilizados.
- Resultado: ajuda de macros sem mapa ou tipo de batalha repetidos; cores por rating e separadores da linha nativa.
- Árvore tecnológica: a opção inclui XP livre no cálculo de XP para investigação; não troca XP por ouro.
- Diretivas: reposição automática enquanto disponíveis no depósito.
- Consumíveis: grandes consumíveis equipados, sem referência enganadora a pagamento em ouro.
- Temporizador de deteção: estimativa configurável; removida a indicação de duração garantida.
- Painel de equipas: separadores e opção de configuração do jogo traduzidos.
- Distância ao alvo: escolhas usam os textos de cada idioma, sem expor identificadores internos.
- Estatísticas: percentagens de força relativa, não probabilidade de vitória calibrada.

## Chaves removidas

- `TEXT.autoaim_target_indicator.UI_setting_angle_text`
- `TEXT.autoaim_target_indicator.UI_setting_angle_value`
- `TEXT.autoaim_target_indicator.UI_setting_catchHiddenTarget_text`
- `TEXT.autoaim_target_indicator.UI_setting_catchHiddenTarget_tooltip`
- `TEXT.autoaim_target_indicator.UI_setting_disableArtyMode_text`
- `TEXT.autoaim_target_indicator.UI_setting_disableArtyMode_tooltip`
- `TEXT.battle_marks_of_excellence.UI_HangarStatsStart`
- `TEXT.battle_marks_of_excellence.UI_marks_assist`
- `TEXT.battle_marks_of_excellence.UI_marks_combined`
- `TEXT.battle_marks_of_excellence.UI_marks_compact`
- `TEXT.battle_marks_of_excellence.UI_marks_current`
- `TEXT.battle_marks_of_excellence.UI_marks_damage`
- `TEXT.battle_marks_of_excellence.UI_marks_detailed`
- `TEXT.battle_marks_of_excellence.UI_marks_legacy`
- `TEXT.battle_marks_of_excellence.UI_marks_normal`
- `TEXT.battle_marks_of_excellence.UI_menu_UIConfig`
- `TEXT.battle_marks_of_excellence.UI_menu_UIMyp`
- `TEXT.battle_marks_of_excellence.UI_menu_UIReplay`
- `TEXT.battle_marks_of_excellence.UI_menu_UIReplayColor`
- `TEXT.battle_marks_of_excellence.UI_menu_UIReplayColorDamage`
- `TEXT.battle_marks_of_excellence.UI_menu_UIReplayDamage`
- `TEXT.battle_marks_of_excellence.UI_menu_UIcircon`
- `TEXT.battle_marks_of_excellence.UI_menu_UIkorbenDallasNoMercy`
- `TEXT.battle_marks_of_excellence.UI_menu_UIoldskool`
- `TEXT.battle_marks_of_excellence.UI_menu_UIskill4ltu`
- `TEXT.battle_marks_of_excellence.UI_menu_UIspoter`
- `TEXT.battle_marks_of_excellence.UI_menu_UIspoterNew`
- `TEXT.battle_marks_of_excellence.UI_setting_UI_text`
- `TEXT.battle_marks_of_excellence.UI_setting_UI_tooltip`
- `TEXT.battle_marks_of_excellence.UI_setting_buttonShow_text`
- `TEXT.battle_marks_of_excellence.UI_setting_buttonShow_tooltip`
- `TEXT.battle_marks_of_excellence.UI_setting_displayMode_text`
- `TEXT.battle_marks_of_excellence.UI_setting_showInBattleHalfPercents_text`
- `TEXT.battle_marks_of_excellence.UI_setting_showInBattleHalfPercents_tooltip`
- `TEXT.battle_marks_of_excellence.UI_setting_showInHangar_text`
- `TEXT.battle_marks_of_excellence.UI_setting_showInHangar_tooltip`
- `TEXT.battle_marks_of_excellence.UI_setting_techTreeMarkOfGunPercentSize_value`
- `TEXT.battle_marks_of_excellence.battleMessageSizeDown`
- `TEXT.battle_marks_of_excellence.battleMessageSizeLimitMax`
- `TEXT.battle_marks_of_excellence.battleMessageSizeLimitMin`
- `TEXT.battle_marks_of_excellence.battleMessageSizeReset`
- `TEXT.battle_marks_of_excellence.battleMessageSizeUp`
- `TEXT.battle_statistics.UI_setting_teamChances_text`
- `TEXT.battle_statistics.UI_setting_teamChances_tooltip`
- `TEXT.common.UI_mog_legacy`
- `TEXT.enemy_spotting_status.UI_setting_AssistRadio_default`
- `TEXT.enemy_spotting_status.UI_setting_AssistRadio_description`
- `TEXT.enemy_spotting_status.UI_setting_AssistStun_default`
- `TEXT.enemy_spotting_status.UI_setting_AssistStun_description`
- `TEXT.enemy_spotting_status.UI_setting_AssistTrack_default`
- `TEXT.enemy_spotting_status.UI_setting_AssistTrack_description`
- `TEXT.enemy_spotting_status.UI_setting_Spotted_default`
- `TEXT.enemy_spotting_status.UI_setting_Spotted_description`
- `TEXT.enemy_spotting_status.UI_setting_iconSizeX_default`
- `TEXT.enemy_spotting_status.UI_setting_iconSizeY_default`
- `TEXT.enemy_spotting_status.UI_setting_macrosList`
- `TEXT.enemy_spotting_status.UI_setting_soundAssist_default`
- `TEXT.enemy_spotting_status.UI_setting_soundAssist_text`
- `TEXT.enemy_spotting_status.UI_setting_soundAssist_tooltip`
- `TEXT.enemy_spotting_status.UI_setting_soundSpotted_default`
- `TEXT.enemy_spotting_status.UI_setting_soundSpotted_text`
- `TEXT.enemy_spotting_status.UI_setting_soundSpotted_tooltip`
- `TEXT.enemy_spotting_status.UI_setting_sound_default`
- `TEXT.hangar_preferences.UI_setting_clock24Hour_text`
- `TEXT.hangar_preferences.UI_setting_clockSeconds_text`
- `TEXT.hangar_preferences.UI_setting_clockStyle_text`
- `TEXT.hangar_preferences.UI_setting_customClockFormat_text`
- `TEXT.hangar_preferences.UI_setting_customClockFormat_tooltip`
- `TEXT.high_caliber_progress.UI_setting_textLock_text`
- `TEXT.high_caliber_progress.UI_setting_textLock_tooltip`
- `TEXT.team_panels.UI_setting_dead_text`
- `TEXT.team_panels.UI_setting_dead_tooltip`
- `TEXT.team_panels.UI_setting_help_text`
- `TEXT.team_panels.UI_setting_help_tooltip`
- `TEXT.team_panels.UI_setting_hpEnabled_text`
- `TEXT.team_panels.UI_setting_hpEnabled_tooltip`
- `TEXT.team_panels.UI_setting_lost_text`
- `TEXT.team_panels.UI_setting_lost_tooltip`
- `TEXT.team_panels.UI_setting_mode_always`
- `TEXT.team_panels.UI_setting_mode_holding`
- `TEXT.team_panels.UI_setting_mode_text`
- `TEXT.team_panels.UI_setting_mode_toggle`
- `TEXT.team_panels.UI_setting_mode_tooltip`
- `TEXT.team_panels.UI_setting_neverSeen_text`
- `TEXT.team_panels.UI_setting_neverSeen_tooltip`
- `TEXT.team_panels.UI_setting_spottedEnabled_text`
- `TEXT.team_panels.UI_setting_spottedEnabled_tooltip`
- `TEXT.team_panels.UI_setting_spotted_text`
- `TEXT.team_panels.UI_setting_spotted_tooltip`
- `TEXT.team_panels.UI_setting_toggleKey_text`
- `TEXT.team_panels.UI_setting_toggleKey_tooltip`

## Chaves corrigidas

- `TEXT.battle_marks_of_excellence.UI_setting_showInReplay_tooltip`
- `TEXT.battle_marks_of_excellence.UI_tooltips`
- `TEXT.battle_performance.UI_setting_battleResultsFormat_text`
- `TEXT.battle_performance.UI_setting_battleResultsFormat_tooltip`
- `TEXT.battle_performance.UI_setting_battleResultsWindow_text`
- `TEXT.battle_performance.UI_setting_battleResultsWindow_tooltip`
- `TEXT.battle_performance.UI_setting_textLock_text`
- `TEXT.battle_performance.UI_setting_textLock_tooltip`
- `TEXT.battle_preferences.UI_setting_clipLoad_text`
- `TEXT.battle_preferences.UI_setting_clipLoad_tooltip`
- `TEXT.battle_preferences.UI_setting_directivesOnlyFromStorage_tooltip`
- `TEXT.battle_preferences.UI_setting_showBattleHint_text`
- `TEXT.battle_preferences.UI_setting_showBattleHint_tooltip`
- `TEXT.battle_statistics.UI_setting_format_tooltip`
- `TEXT.enemy_spotting_status.UI_description`
- `TEXT.hangar_preferences.UI_setting_allowExchangeXPInTechTree_text`
- `TEXT.hangar_preferences.UI_setting_allowExchangeXPInTechTree_tooltip`
- `TEXT.hangar_preferences.UI_setting_hideBtnCounters_tooltip`
- `TEXT.high_caliber_progress.UI_setting_backGroundEnabled_text`
- `TEXT.repair_controls.UI_setting_useGoldKits_text`
- `TEXT.sixth_sense_alert.UI_setting_lampShowTime_tooltip`
- `TEXT.sixth_sense_alert.UI_setting_userIcon_tooltip`
- `TEXT.team_panels.UI_panel_clientDefault`

## Chaves acrescentadas

- `TEXT.battle_statistics.UI_teamStrength`
- `TEXT.team_panels.UI_panel_generalTab`
- `TEXT.team_panels.UI_panel_loadingTab`
- `TEXT.team_panels.UI_panel_templatesTab`

A revisão confirma o significado funcional; a revisão por falantes nativos de terminologia e fluência mantém-se pendente nas traduções assistidas.
