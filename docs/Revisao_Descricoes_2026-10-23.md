# Descrições dos controlos — revisão do inglês

> Atualização de contexto — 26/10/2026: A tabela abaixo é o registo histórico da revisão de 23/10, não uma lista de alterações por aprovar. As descrições atuais vivem nos 18 catálogos YML. Os testes percorrem as definições atuais, verificam descrições por idioma e abertura/aplicação de todas as páginas. Totais atuais: 1491 chaves de componentes e 170 do painel; os 506 textos e 1005 controlos abaixo pertencem ao levantamento original. Ver o [estado atual](STATUS.md) e o [guia de contribuição](../CONTRIBUTING.md).

Registo do rascunho de 23/10/2026, preparado antes da tradução para os 18 idiomas. Cada texto foi conferido com o código da altura.

**Total:** 506 textos — 348 novos e 158 revistos. Com eles, todos os 1005 controlos do painel ficam com descrição.

- **Nova**: o controlo não tinha descrição.
- **Revista**: substitui a descrição antiga (indicada em "antes").
- As chaves `UI_tooltip_*` cobrem campos repetidos: um texto serve todas as variantes (lados esquerdo/direito, slots e campos extra).

## aiming_countdown

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_blue_tooltip` | Choose Color for dispersion timer very good: | Timer color while aiming is 75–89% complete. | Nova |
| `UI_setting_green_tooltip` | Choose Color for dispersion timer good: | Timer color while aiming is 50–74% complete. | Nova |
| `UI_setting_orange_tooltip` | Choose Color for dispersion timer low: | Timer color while aiming is 15–34% complete. | Nova |
| `UI_setting_purple_tooltip` | Choose Color for dispersion timer great: | Timer color once aiming is at least 90% complete. | Nova |
| `UI_setting_red_tooltip` | Choose Color for dispersion timer bad: | Timer color while aiming is below 15% complete. | Nova |
| `UI_setting_template_tooltip` | Template | Text of the timer. Macros: %(timer).1fs remaining aiming time, %(percent)d%% aiming progress, %(color)s color for the current progress. | Revista<br><sub>antes: Macros '%(color)s', %(timer).1fs, %(percent)d%%</sub> |
| `UI_setting_x_tooltip` | Position X | Horizontal offset of the timer from the crosshair, in pixels. Negative values move it left. | Nova |
| `UI_setting_y_tooltip` | Position Y | Vertical offset of the timer from the crosshair, in pixels. Negative values move it up. | Nova |
| `UI_setting_yellow_tooltip` | Choose Color for dispersion timer normal: | Timer color while aiming is 35–49% complete. | Nova |

## aiming_reticles

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_gunMarkerMinimumSize_tooltip` | Gun Marker Minimum Size | Smallest size the gun marker can shrink to, in pixels. | Revista<br><sub>antes: Minimum size of the gun marker in pixels</sub> |
| `UI_setting_percentCorrection_tooltip` | Reticle Size Correction | Corrects the aiming circle size. 0% keeps the game size; 100% applies the full correction. | Revista<br><sub>antes: Adjust the scale factor of the reticle</sub> |
| `UI_setting_serverReticleAimingCircleOpacity_tooltip` | Aiming Circle Opacity | Opacity of the server aiming circle, in percent. | Revista<br><sub>antes: Adjust the opacity of the server aiming circle</sub> |
| `UI_setting_serverReticleAimingCircleShape_tooltip` | Aiming Circle Shape | Shape of the server aiming circle. | Revista<br><sub>antes: Select the shape of the server aiming circle</sub> |
| `UI_setting_serverReticleGunMarkerOpacity_tooltip` | Gun Marker Opacity | Opacity of the server gun marker, in percent. | Revista<br><sub>antes: Adjust the opacity of the server gun marker</sub> |
| `UI_setting_serverReticleGunMarkerShape_tooltip` | Gun Marker Shape | Shape of the server gun marker. | Revista<br><sub>antes: Select the shape of the server gun marker</sub> |
| `UI_setting_showClientAndServerReticleBeta_tooltip` | Client and Server Reticle (Beta) | Shows the client and server reticles at the same time. The server reticle follows the server's aiming data. | Revista<br><sub>antes: Show both client and server reticle simultaneously</sub> |
| `UI_setting_showServerSpgStrategicReticle_tooltip` | SPG Strategic Reticle | Also shows the server reticle in the SPG strategic (top-down) view. | Revista<br><sub>antes: Enable server reticle for SPG strategic mode</sub> |

## artillery_blast_radius

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_buttonShowDot_tooltip` | Button: show\|hide Dot | Shows or hides the aiming dot during battle. | Nova |
| `UI_setting_buttonShowSplash_tooltip` | Button: show\|hide Splash | Shows or hides the splash radius during battle. | Nova |
| `UI_setting_showDotOnDefault_tooltip` | Show Dot on default | Shows a dot at the aiming point when the battle starts. | Nova |
| `UI_setting_showModeArcade_tooltip` | Arcade mode available | Allows the splash and dot in arcade (third-person) view. | Nova |
| `UI_setting_showModeArty_tooltip` | Arty mode available | Allows the splash and dot in the SPG strategic and artillery views. | Nova |
| `UI_setting_showModeSniper_tooltip` | Sniper mode available | Allows the splash and dot in sniper view. | Nova |
| `UI_setting_showSplashOnDefault_tooltip` | Show Splash on default | Shows the shell's splash radius at the aiming point when the battle starts. | Nova |

## autoaim_target_indicator

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_color_tooltip` | Indicator color | Color of the frame drawn around the vehicle locked by autoaim. | Nova |

## battle_marks_of_excellence

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_background_tooltip` | Show panel background | Shows the panel background. The opacity is set separately. | Revista<br><sub>antes: Enable the panel background. Opacity is configured separately.</sub> |
| `UI_setting_buttonReset_tooltip` | Button: Reset Settings | Resets the panel size to its default during battle. | Nova |
| `UI_setting_buttonSizeDown_tooltip` | Button: Size -10% | Makes the panel 10% smaller during battle. | Nova |
| `UI_setting_buttonSizeUp_tooltip` | Button: Size +10% | Makes the panel 10% larger during battle. | Nova |
| `UI_setting_colorRating_tooltip` | Color table | Color table used for mark values. | Revista<br><sub>antes: Color scale for marks of excellence.</sub> |
| `UI_setting_showDamage_tooltip` | Show damage | Shows your combined damage (damage plus the highest assist) in this battle. | Nova |
| `UI_setting_showDelta_tooltip` | Show estimated delta | Shows the estimated change of the mark in this battle. | Nova |
| `UI_setting_showInBattle_tooltip` | Show activation message | Shows a message when the battle starts. It does not change whether the panel is visible. | Revista<br><sub>antes: Show a message at battle start. This does not control panel visibility.</sub> |
| `UI_setting_showInReplay_tooltip` | Replay: enabled | Shows the panel in replays. Replay values are estimates; set the base mark and average damage below when no history is available. | Revista<br><sub>antes: Replay values are estimates. Configure the base mark percentage and average damage when historical data is unavailable.</sub> |
| `UI_setting_showInStatistic_tooltip` | Statistic: enabled | Adds your average damage, the damage needed for the next mark and the damage for each mark level to the Marks of Excellence achievement tooltip. | Nova |
| `UI_setting_showMarks_tooltip` | Show marks | Shows the stars for the marks already earned. | Nova |
| `UI_setting_showProgress_tooltip` | Show progress | Shows the progress bar towards the next mark. | Nova |
| `UI_setting_showTargets_tooltip` | Show targets | Shows the estimated target damage and the damage still needed. | Nova |
| `UI_tooltip_accentColor` | Accent color | Color used for the main values and the progress bar. | Nova |
| `UI_tooltip_backgroundOpacity` | Background opacity | Opacity of the panel background (0 transparent, 1 opaque). | Nova |
| `UI_tooltip_battleMessageSizeInPercent` | Panel scale | Size of the panel, in percent of its normal size. | Nova |
| `UI_tooltip_gameface_enabled` | Enable battle panel | Shows the Marks of Excellence panel in battle. | Nova |
| `UI_tooltip_locked` | Lock panel position | Prevents moving the panel. When unlocked, show the cursor (Ctrl) and drag the panel; the position is saved. | Nova |
| `UI_tooltip_miniMode` | Mini battle panel | Uses a narrower panel with the essential values. | Nova |
| `UI_tooltip_panel_x` | X | Horizontal position of the panel, in UI units, from the screen edge it is anchored to. Dragging the panel updates this value. | Nova |
| `UI_tooltip_panel_y` | Y | Vertical position of the panel, in UI units, from the screen edge it is anchored to. Dragging the panel updates this value. | Nova |
| `UI_tooltip_replayBaseDamage` | Replay base average damage | Average damage used as the starting point in replays when no history is available. | Nova |
| `UI_tooltip_replayBasePercent` | Replay base mark (%) | Mark percentage used as the starting point in replays when no history is available. | Nova |
| `UI_tooltip_showRequiredDamage` | Estimated damage needed | Shows the estimated damage you still need in this battle. | Nova |
| `UI_tooltip_showTargetDamage` | Estimated target | Shows the estimated damage target for the next mark. | Nova |

## battle_performance

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_battleResultsFormat_tooltip` | Results statistics format | Text added to the battle results line. Macros: {wn8}, {xwn8}, {eff}, {xeff}, {diff}, {dmg}, {xte}; colors: {c:wn8}, {c:xwn8}, {c:eff}, {c:xeff}, {c:diff}, {c:dmg}, {c:xte}. Use \| or <tab> for a separator. | Revista<br><sub>antes: Displays ratings after the vehicle status in the native results line. Font and size follow the game UI; the map is already shown.  WN8: {wn8} / {c:wn8} XWN8: {xwn8} / {c:xwn8} EFF:</sub> |
| `UI_setting_battleResultsWindow_tooltip` | Battle results statistics | Adds the ratings after the vehicle status in the information line of the battle results. Font and size follow the game interface. | Revista<br><sub>antes: Displays ratings after the vehicle status in the native results line. Font and size follow the game UI; the map is already shown.</sub> |
| `UI_setting_colorRatting_tooltip` | Choose Color Rating | Color table used for the ratings. | Revista<br><sub>antes: Select the color scheme for ratings</sub> |
| `UI_setting_format_tooltip` | Text Format, Available Macros: | Text of the in-battle efficiency panel. Macros: {wn8}, {xwn8}, {eff}, {xeff}, {diff}, {dmg}, {xte}; colors: {c:wn8}, {c:eff}, {c:diff}, {c:dmg}, {c:x}. | Revista<br><sub>antes: Available Macros:  WN8:'{wn8}', Color:'{c:wn8}' XWN8:'{xwn8}', Color:'{c:x}' EFF:'{eff}', Color:'{c:eff}' XEFF:'{xeff}', Color:'{c:x}' DIFF:'{diff}', Color:'{c:diff}' DMG:'{dmg}', </sub> |
| `UI_setting_textLock_tooltip` | Lock panel position | Prevents moving the in-battle panel with the mouse. When unlocked, drag it while the cursor is visible. | Revista<br><sub>antes: Lock panel position</sub> |

## battle_preferences

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_addEnemyName_tooltip` | Add Enemy Name | Adds the player's name next to the vehicle name in the damage log. | Revista<br><sub>antes: Adds the name of the enemy vehicle to the damage log.</sub> |
| `UI_setting_clipLoad_tooltip` | Send reload status | When you manually reload a magazine, sends the remaining reload time to the team chat. | Revista<br><sub>antes: Send the remaining reload time to battle chat when manually reloading the magazine.</sub> |
| `UI_setting_color_tooltip` | Choose Map Border Color: | Color of the map border on every map. | Revista<br><sub>antes: This color will be applied to all Maps</sub> |
| `UI_setting_directivesOnlyFromStorage_tooltip` | Directives Only From Storage | Keeps directives on automatic resupply only while you have them in the depot, so none are bought. | Revista<br><sub>antes: Automatically resupply directives only while they are available in the depot.</sub> |
| `UI_setting_disableSoundCommander_tooltip` | Disable Sound Commander | Turns off special commander voices, so the standard crew voice is used. | Revista<br><sub>antes: Disable Sound Commander in battle.</sub> |
| `UI_setting_hideHint_tooltip` | Hide Hint | Turns off the battle hint panel completely. | Revista<br><sub>antes: Disable battle hint.</sub> |
| `UI_setting_inBattle_tooltip` | Clock In Battle | Shows a clock in battle. | Revista<br><sub>antes: Show clock in battle</sub> |
| `UI_setting_loadTxt_tooltip` | Text Format | Chat message sent when you reload. Macros: {load} remaining seconds, {pos} map square. Leave it empty to use the game's reload command. | Revista<br><sub>antes: Use macros to edit the message  (macros: '{load}' - '{pos}')</sub> |
| `UI_setting_maxChatLines_tooltip` | Max Chat Lines | Maximum number of messages kept in the battle chat. | Revista<br><sub>antes: Limit the number of battle chat lines.</sub> |
| `UI_setting_muteTeamBaseSound_tooltip` | Mute Team Base Sound | Mutes the base capture sound. | Revista<br><sub>antes: Disable team base sound wen this option is enabled.</sub> |
| `UI_setting_postmortemTips_tooltip` | Show Postmortem Tips | Shows the tips panel at the bottom of the screen after your vehicle is destroyed. Turn it off to hide it. | Revista<br><sub>antes: Show the pop-up panel at the bottom after your vehicle is destroyed.</sub> |
| `UI_setting_removeFog_tooltip` | Remove fog | Builds a separate package from this installation's maps without fog. It is installed or removed after you close the game, so a restart is required. Turning this mod off also removes the package. | Revista<br><sub>antes: Generates a separate package from this installation’s maps. Installation or removal happens after closing the game. Requires a restart. Disabling this module also removes the packa</sub> |
| `UI_setting_showBattleHint_tooltip` | Hide battle hints | Hides the game's battle hints, such as the tips shown at the top of the screen. | Revista<br><sub>antes: Hide battle hints</sub> |
| `UI_setting_showFriends_tooltip` | Show Friends | Marks players from your friends list in the team panels. Not used in replays. | Revista<br><sub>antes: Show friends in players panel.</sub> |
| `UI_setting_showPlayerSatisfactionWidget_tooltip` | Show Player Satisfaction Widget | Shows the player satisfaction rating widget. Turn it off to hide it. | Revista<br><sub>antes: Display battle rating "player satisfaction" widget.</sub> |
| `UI_setting_showPostmortemDogTag_tooltip` | Show Postmortem Dog Tag | Shows the dog tag panel after your vehicle is destroyed. Turn it off to hide the panel. | Revista<br><sub>antes: Show the pop-up panel with the dog tag after your vehicle is destroyed.</sub> |
| `UI_setting_stunSound_tooltip` | Stun Sound | Mutes the stun sound effect when your vehicle is stunned. | Revista<br><sub>antes: Disable Stun Sound Effect.</sub> |

## battle_statistics

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_colorRating_tooltip` | Color table | Color table used to compare the two teams. | Revista<br><sub>antes: Color scale for statistics.</sub> |
| `UI_setting_format_tooltip` | Text Format | Text of the team comparison. Macros: {header}, {allyChance}, {compareSign}, {enemyChance}. The percentages compare estimated team strength; they are not a calibrated chance of winning. | Revista<br><sub>antes: The percentages compare estimated vehicle strength. They are not a calibrated probability of winning.</sub> |

## common

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_native_enabled_tooltip` | Enable mod | Turns this mod on or off. When it is off, the game behaves as if the mod were not installed. | Nova |

## crew_management

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_autoReturnDelay_tooltip` | Auto Return Delay (seconds) | Wait after switching vehicles before the crew is returned, in seconds. | Revista<br><sub>antes: Delay before automatically returning crew</sub> |
| `UI_setting_crewAutoReturn_tooltip` | Crew Auto Return | Returns the vehicle's previous crew when you pick a vehicle in the vehicle selection pop-up. | Revista<br><sub>antes: Automatically return crew to their vehicle</sub> |
| `UI_setting_crewReturnByDefault_tooltip` | Crew Return By Default | Also returns the previous crew automatically whenever you switch vehicles in the hangar. Requires Crew Auto Return. | Revista<br><sub>antes: Return crew by default when switching vehicles</sub> |
| `UI_setting_excludePremiumVehicles_tooltip` | Exclude Premium Vehicles | Never returns crew automatically to Premium vehicles. | Revista<br><sub>antes: Do not auto-return crew for premium vehicles</sub> |
| `UI_setting_showBarracksProgression_tooltip` | Crew progression in the barracks | Shows crew progression for crew members in the barracks. | Nova |
| `UI_setting_showCrewDetails_tooltip` | Progression in the personal file | Shows crew progression in the crew member's personal file. | Nova |
| `UI_setting_showCrewProgression_tooltip` | Crew progression in the hangar tooltip | Shows crew progression in the tooltip of crew members in the hangar. | Nova |
| `UI_setting_showCrewTooltips_tooltip` | Progression in crew tooltips | Shows crew progression in crew member tooltips. | Nova |
| `UI_setting_showEstimatedBattles_tooltip` | Show estimated battles | Shows how many battles the next level should take, based on the vehicle's XP history. Accelerated training, reserves and bonuses can change the result. | Revista<br><sub>antes: Based on the vehicle XP history. Accelerated training, reserves and bonuses can change the result.</sub> |
| `UI_setting_showNotifications_tooltip` | Show Notifications | Shows a system notification each time the crew is returned. | Revista<br><sub>antes: Show system notifications when crew is returned</sub> |
| `UI_setting_showRemainingXP_tooltip` | Show remaining XP | Shows the XP still needed for the next skill level. | Nova |

## enemy_spotting_status

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_AssistRadio_tooltip` | Radio assist: | Notification shown when you earn spotting assist damage. Macros: {icons}, {names}, {vehicles}, {icons_names}, {icons_vehicles}, {full}, {damage}. | Revista<br><sub>antes: Customize the message shown when you get radio assist damage</sub> |
| `UI_setting_AssistStun_tooltip` | Stun assist: | Notification shown when you earn stun assist damage. Macros: {icons}, {names}, {vehicles}, {icons_names}, {icons_vehicles}, {full}, {damage}. | Revista<br><sub>antes: Customize the message shown when you get stun assist damage</sub> |
| `UI_setting_AssistTrack_tooltip` | Track assist: | Notification shown when you earn tracking assist damage. Macros: {icons}, {names}, {vehicles}, {icons_names}, {icons_vehicles}, {full}, {damage}. | Revista<br><sub>antes: Customize the message shown when you get track assist damage</sub> |
| `UI_setting_Spotted_tooltip` | Spotted: | Notification shown when you spot enemy vehicles. Macros: {icons}, {names}, {vehicles}, {icons_names}, {icons_vehicles}, {full}. | Revista<br><sub>antes: Customize the message shown when you spot an enemy vehicle</sub> |
| `UI_setting_iconSizeX_tooltip` | Icon width | Width of the vehicle icons in the notifications, in pixels. | Revista<br><sub>antes: Width of vehicle icons in notifications</sub> |
| `UI_setting_iconSizeY_tooltip` | Icon height | Height of the vehicle icons in the notifications, in pixels. | Revista<br><sub>antes: Height of vehicle icons in notifications</sub> |
| `UI_setting_messageColorAssistRadio_tooltip` | Radio assist message color | Text color of the notification for spotting assist damage. | Revista<br><sub>antes: Color used for the "Radio Hit Assist" notification text</sub> |
| `UI_setting_messageColorAssistStun_tooltip` | Stun assist message color | Text color of the notification for stun assist damage. | Revista<br><sub>antes: Color used for the "Stun Hit Assist" notification text</sub> |
| `UI_setting_messageColorAssistTrack_tooltip` | Track assist message color | Text color of the notification for tracking assist damage. | Revista<br><sub>antes: Color used for the "Track Hit Assist" notification text</sub> |
| `UI_setting_messageColorSpotted_tooltip` | Spotted message color | Text color of the notification for vehicles you spot. | Revista<br><sub>antes: Color used for the "Spotted" notification text</sub> |
| `UI_setting_sound_tooltip` | Enable battle sounds | Plays a sound when you spot an enemy or earn assist damage. | Revista<br><sub>antes: Toggle sound notifications for spotted enemies and assist damage</sub> |

## game_log_manager

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_logSwapper_tooltip` | Enable Reverse Log. | Swaps the positions of the top and bottom damage logs. | Revista<br><sub>antes: Reverses the position of the damage log in the battle interface.</sub> |
| `UI_setting_wgLogHideAssist_tooltip` | WG Log Hide Assist | Hides assist damage from the game's damage log. | Revista<br><sub>antes: Hides damage assist messages in the standard WG battle log.</sub> |
| `UI_setting_wgLogHideBlock_tooltip` | WG Log Hide Block | Hides blocked damage from the game's damage log. | Revista<br><sub>antes: Hides blocked damage messages in the standard WG battle log.</sub> |
| `UI_setting_wgLogHideCritics_tooltip` | WG Log Hide Critics | Hides critical hits received from the game's damage log. | Revista<br><sub>antes: Hides critical hit messages in the standard WG battle log.</sub> |

## gun_traverse_limits

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_horizontal_tooltip` | Horizontal marker type | Markers at the left and right of the crosshair that show how far the gun can still traverse. | Revista<br><sub>antes: Type of markers to the left and right of the crosshair showing horizontal edge positions of your gun.   	 	 	 	 	 </sub> |
| `UI_setting_vertical_tooltip` | Vertical marker type | Markers above and below the crosshair that show how far the gun can still be raised or lowered. | Revista<br><sub>antes: Type of markers above and below the crosshair showing vertical edge positions of your gun.  					</sub> |

## hangar_marks_of_excellence

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_colorRating_tooltip` | Choose Color Rating | Color table used for marks, WN8 and win rate in the panel. | Revista<br><sub>antes: Select the color scheme for MoE, WN8 and winrate</sub> |
| `UI_setting_compactMode_tooltip` | Compact panel | Hides secondary vehicle statistics to make the panel smaller. | Revista<br><sub>antes: Hide secondary vehicle statistics.</sub> |
| `UI_setting_goalSelection_tooltip` | Mark objective | Mark used as the target in the panel. Automatic selects the next mark not yet earned. The damage shown is a proportional estimate, not a server threshold or a prediction for the next battle. | Revista<br><sub>antes: Automatic selects the next unearned mark. Damage is a proportional estimate, not a server threshold or next-battle prediction.</sub> |
| `UI_setting_historyBattles_tooltip` | Recent battles in history | Number of recent progress updates kept in the history. One update can include several battles. The history starts when this version is installed. | Revista<br><sub>antes: Updates may group several battles. History starts when this version is installed.</sub> |
| `UI_setting_positionX_tooltip` | Horizontal position (X) | Horizontal position of the panel, in UI units, from the screen edge it is anchored to. Dragging the panel updates this value. | Revista<br><sub>antes: Smaller: left. Larger: right.</sub> |
| `UI_setting_positionY_tooltip` | Vertical position (Y) | Vertical position of the panel, in UI units, from the screen edge it is anchored to. Dragging the panel updates this value. | Revista<br><sub>antes: Smaller: up. Larger: down.</sub> |
| `UI_setting_showInHangar_tooltip` | Hangar: enabled | Shows the Marks of Excellence panel for the selected vehicle in the hangar. | Nova |
| `UI_setting_showInStatistic_tooltip` | Tooltip: enabled | Adds your average damage, the damage needed for the next mark and the damage for each mark level to the Marks of Excellence achievement tooltip. | Nova |
| `UI_setting_showTooltipTargets_tooltip` | Tooltip: show target levels | Adds the damage needed for each mark level to the achievement tooltip. | Nova |
| `UI_setting_textLock_tooltip` | Lock panel position | Prevents moving the panel. When unlocked, drag its header with the left mouse button; the position is saved. | Revista<br><sub>antes: Prevent header dragging. When unlocked, drag with the left mouse button; the position is saved.</sub> |
| `UI_tooltip_accentColor` | Accent color | Color used for the main values and the progress bar. | Nova |
| `UI_tooltip_card_backgroundAlpha` | Background opacity | Opacity of the panel background (0 transparent, 1 opaque). | Nova |
| `UI_tooltip_scale` | Panel scale | Size of the panel compared with its normal size. | Nova |
| `UI_tooltip_showAdvancedStatistics` | Advanced statistics | Shows additional statistics, such as the moving average used by the game. | Nova |
| `UI_tooltip_showDamageStatistics` | Damage statistics | Shows the vehicle's damage averages used for the mark. | Nova |
| `UI_tooltip_showHistory` | Observed progress history | Shows the recent mark changes recorded from your battles. | Nova |
| `UI_tooltip_showMilestones` | Mark milestones | Shows the estimated damage for the 65%, 85% and 95% marks. | Nova |
| `UI_tooltip_showProgress` | Progress bar | Shows the progress bar towards the next mark. | Nova |
| `UI_tooltip_showVehicleInfo` | Vehicle information | Shows the vehicle name, tier and type in the panel. | Nova |

## hangar_preferences

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_allowChannelButtonBlinking_tooltip` | Allow Channel Button Blinking | Lets the clan and private chat buttons blink when there are new messages. Turn it off to stop the blinking. | Revista<br><sub>antes: Allow messenger bar channel (clan or private chat) button blinking.</sub> |
| `UI_setting_allowExchangeXPInTechTree_tooltip` | Include Free XP in the tech tree | Includes Free XP when the tech tree calculates the XP available to research vehicles. It does not convert XP or spend gold. | Revista<br><sub>antes: Include Free XP when calculating XP available to research vehicles. Does not exchange XP for gold.</sub> |
| `UI_setting_autoLogin_tooltip` | Automatic Login | Logs in automatically with the saved account when the login screen opens. Not used with Wargaming Game Center. | Revista<br><sub>antes: Automatically log into the game</sub> |
| `UI_setting_blockVehicleIfLowAmmo_tooltip` | Block Battle On Low Ammo | Prevents starting a battle when the selected vehicle has less ammunition than the limit below. | Revista<br><sub>antes: Prevent entering battle when the selected vehicle has low ammo.</sub> |
| `UI_setting_clockBackground_tooltip` | Clock background | Shows a background behind the clock. | Nova |
| `UI_setting_clockScale_tooltip` | Clock size (%) | Size of the clock, from 50% to 200%. | Nova |
| `UI_setting_clockX_tooltip` | Clock: horizontal position | Horizontal offset of the clock from the right edge of the screen, in UI units. | Nova |
| `UI_setting_clockY_tooltip` | Clock: vertical position | Vertical offset of the clock from the top of the screen, in UI units. | Nova |
| `UI_setting_clock_tooltip` | Clock Display | Shows the clock in the hangar. | Revista<br><sub>antes: Show the Gameface clock in the hangar</sub> |
| `UI_setting_customClockText_tooltip` | Clock format (restart required) | Clock text with time codes such as %H hours, %M minutes, %A weekday, %d day, %b month and %Y year. Simple <font> and <textformat> tags are allowed. A JSON list of formats can also be used. | Nova |
| `UI_setting_fieldMail_tooltip` | Field Mail | Shows Field Mail. Turn it off to hide it. | Revista<br><sub>antes: Show/hide Field Mail.</sub> |
| `UI_setting_hideBtnCounters_tooltip` | Disable tooltips | Hides the tooltips of the hangar, header and footer buttons. | Nova |
| `UI_setting_lootBoxesWidget_tooltip` | Lootbox Widget | Shows the loot box widget in the hangar. Turn it off to hide it. | Revista<br><sub>antes: Show/hide lootbox widget in hangar</sub> |
| `UI_setting_lowAmmoPercentage_tooltip` | Low Ammo Percentage | Ammunition level, as a percentage of capacity, below which the vehicle counts as low on ammo. | Revista<br><sub>antes: Ammo threshold used to mark a vehicle as ready or low on ammo.</sub> |
| `UI_setting_premiumTime_tooltip` | Show Premium account expiry | Shows the expiry date and time of your Premium account under the Premium button. | Nova |
| `UI_setting_showAchievementPopups_tooltip` | Achievement Popups | Shows pop-ups for new achievements. Turn it off to hide them. | Revista<br><sub>antes: Show/hide Achievement Popups.</sub> |
| `UI_setting_showAchievementRewardWindow_tooltip` | Achievement Reward Window | Shows the full-screen achievement reward window. Turn it off to hide it. | Revista<br><sub>antes: Show/hide fullscreen achievement reward window.</sub> |
| `UI_setting_showBattleCount_tooltip` | Battle Counter | Shows the session battle counter. Turn it off to hide it. | Revista<br><sub>antes: Show/hide the battle count display</sub> |
| `UI_setting_showBattlePassWidget_tooltip` | Battle Pass Widget | Shows the Battle Pass widget and its hangar notifications. Turn it off to hide them. | Revista<br><sub>antes: Show/hide Battle Pass widget in hangar.</sub> |
| `UI_setting_showButtonCounters_tooltip` | Button Counters | Shows the counters on hangar buttons. Turn it off to hide them. | Revista<br><sub>antes: Show/hide notification counters on buttons</sub> |
| `UI_setting_showButton_tooltip` | Statistics Button | Shows the session statistics button. Turn it off to hide it. | Revista<br><sub>antes: Show/hide the session statistics button</sub> |
| `UI_setting_showBuyPremiumButton_tooltip` | Show Premium account button | Shows the Premium account button in the hangar header. | Nova |
| `UI_setting_showDailyQuestWidget_tooltip` | Daily Missions | Shows the daily missions widget in the hangar. Turn it off to hide it. | Revista<br><sub>antes: Show/hide daily mission widget in hangar</sub> |
| `UI_setting_showEventBanner_tooltip` | Event Banners | Shows event banners in the hangar. Turn it off to hide them. | Revista<br><sub>antes: Show/hide event banners in hangar</sub> |
| `UI_setting_showEventTournamentWidget_tooltip` | Tournament Widget | Shows the tournament widget in the hangar. Turn it off to hide it. | Revista<br><sub>antes: Show/hide tournament banner widget in hangar.</sub> |
| `UI_setting_showGeneralChatButton_tooltip` | General Chat | Shows the General chat button. Turn it off to hide it. | Revista<br><sub>antes: Show/hide the General Chat button</sub> |
| `UI_setting_showHangarPrestigeWidget_tooltip` | Hangar Prestige Display | Shows the elite (prestige) level in the hangar. Turn it off to hide it. | Revista<br><sub>antes: Show/hide elite level widget in hangar</sub> |
| `UI_setting_showPopUpMessages_tooltip` | Popup Notifications | Shows pop-up notifications in the hangar. Turn it off to hide them. | Revista<br><sub>antes: Show/hide popup notification messages</sub> |
| `UI_setting_showPremiumShopButton_tooltip` | Show Premium Shop | Shows the Premium Shop button in the hangar header. | Nova |
| `UI_setting_showProfilePrestigeWidget_tooltip` | Profile Prestige Display | Shows the elite (prestige) level in the service record. Turn it off to hide it. | Revista<br><sub>antes: Show/hide elite level widget in profile</sub> |
| `UI_setting_showProgressiveDecalsWindow_tooltip` | Progressive Decals | Shows the progressive decal notification windows. Turn it off to hide them. | Revista<br><sub>antes: Show/hide progressive decal notifications</sub> |
| `UI_setting_showPromoPremVehicle_tooltip` | Premium Vehicle Preview | Shows the Premium vehicle promotion in the hangar. Turn it off to hide it. | Revista<br><sub>antes: Show/hide premium vehicle previews in hangar</sub> |
| `UI_setting_showRankedBattleResults_tooltip` | Ranked Battle Results | Shows the Ranked Battles results window. Turn it off to hide it. | Revista<br><sub>antes: Show/hide ranked battle results window</sub> |
| `UI_setting_showReferralButton_tooltip` | Show referral program | Shows the referral program button. | Nova |
| `UI_setting_showUnreadCounter_tooltip` | Notification Counter | Shows the unread notification counter. Turn it off to hide it. | Revista<br><sub>antes: Show/hide unread notification counters</sub> |
| `UI_setting_showWotPlusButton_tooltip` | Show WoT Plus button | Shows the WoT Plus button in the hangar header. | Nova |
| `UI_setting_showXpToUnlockVeh_tooltip` | Vehicle XP Requirements | Shows the XP needed to research a vehicle in its tooltip. | Revista<br><sub>antes: Show required XP to unlock vehicles</sub> |

## high_caliber_progress

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_backGroundEnabled_tooltip` | Show panel background | Shows the panel background. The opacity is set separately. | Nova |
| `UI_tooltip_accentColor` | Accent color | Color used for the progress bar while the target is still reachable. | Nova |
| `UI_tooltip_background_alpha` | Background opacity | Opacity of the panel background, in percent. | Nova |
| `UI_tooltip_mainGun_dynamic` | Dynamic target | Raises the target when another eligible player deals more damage than the base target, as the award requires. | Nova |
| `UI_tooltip_scale` | Panel scale | Size of the panel compared with its normal size. | Nova |
| `UI_tooltip_showPercentage` | Show percentage | Shows the progress as a percentage. | Nova |
| `UI_tooltip_showProgress` | Progress bar | Shows the progress bar. | Nova |
| `UI_tooltip_showSecondary` | Show description | Shows the second line with the remaining damage or the reason the award is not available. | Nova |
| `UI_tooltip_textLock` | Lock panel position | Prevents moving the panel. When unlocked, show the cursor (Ctrl) and drag the panel; the position is saved. | Nova |
| `UI_tooltip_textPosition_x` | X | Horizontal position of the panel, in UI units, from the screen edge it is anchored to. Dragging the panel updates this value. | Nova |
| `UI_tooltip_textPosition_y` | Y | Vertical position of the panel, in UI units, from the screen edge it is anchored to. Dragging the panel updates this value. | Nova |

## minimap_enhancements

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_button_tooltip` | Zoom Button | Hold this key to show the alternative (enlarged) minimap. | Revista<br><sub>antes: Hot key for zoom.</sub> |
| `UI_setting_changeColorCircles_tooltip` | Change Color Circles | Uses the colors below for the view range circles on the minimap. | Revista<br><sub>antes: When enabled, you can change the color of the circles on the minimap.</sub> |
| `UI_setting_colorDrawCircle_tooltip` | Draw Range Circle | Color of the draw range circle. | Nova |
| `UI_setting_colorMaxViewCircle_tooltip` | Max. View Range Circle | Color of the maximum view range circle. | Nova |
| `UI_setting_colorMinSpottingCircle_tooltip` | Min. Spotting Range Circle | Color of the minimum spotting range circle. | Nova |
| `UI_setting_colorViewCircle_tooltip` | View Range Circle | Color of your current view range circle. | Nova |
| `UI_setting_lastPositionDuration_tooltip` | Last position duration (0: until seen again) | How long a last known position stays on the minimap, in seconds. 0 keeps it until the vehicle is seen again. | Revista<br><sub>antes: How long to show last known positions (in seconds)</sub> |
| `UI_setting_permanentMinimapDeath_tooltip` | Permanent Minimap Death | Keeps destroyed vehicles on the minimap for the rest of the battle. | Revista<br><sub>antes: Always show the destroyed on the map</sub> |
| `UI_setting_showLastPositions_tooltip` | Show Last Known Positions | Shows where enemy vehicles were last seen after they disappear from view. | Revista<br><sub>antes: Display the last known positions of enemy vehicles</sub> |
| `UI_setting_showNames_tooltip` | Show Names | Shows the names of destroyed vehicles on the minimap. | Revista<br><sub>antes: Display the names of destroyed tanks</sub> |
| `UI_setting_showVehicleTypes_tooltip` | Show Vehicle Types | Shows vehicle type icons on the minimap. | Revista<br><sub>antes: Display vehicle type icons on the minimap</sub> |
| `UI_setting_viewRadius_tooltip` | Real View | Draws the view range circle with your vehicle's real view range instead of the game's 445 m limit. | Revista<br><sub>antes: Remove the limitation of the circle of vision 445m</sub> |
| `UI_setting_yaw_tooltip` | Show Hover Angles | Shows the turret traverse limits on the minimap for every vehicle that has them, not only SPGs. | Revista<br><sub>antes: Show Hover Angles on all vehicles where they are</sub> |
| `UI_setting_zoomFactorMax_tooltip` | Maximum Zoom Factor | Upper limit for the alternative minimap size (1.0–3.0). | Revista<br><sub>antes: Maximum zoom level for the minimap (1.0-3.0)</sub> |
| `UI_setting_zoomFactor_tooltip` | Zoom scale | Size of the alternative minimap compared with the normal one. | Nova |
| `UI_tooltip_alpha` | Label opacity; Vehicle icon opacity (+8) | Opacity, in percent. | Nova |
| `UI_tooltip_alternativeAlly` | Alternative ally format | Label format for allies on the alternative minimap. | Nova |
| `UI_tooltip_alternativeAlpha` | Alternative map opacity | Opacity of the alternative minimap, in percent. | Nova |
| `UI_tooltip_alternativeEnabled` | Enable alternative presentation | Lets the minimap key switch to an alternative, enlarged minimap. | Nova |
| `UI_tooltip_alternativeEnemy` | Alternative enemy format | Label format for enemies on the alternative minimap. | Nova |
| `UI_tooltip_alternativeSquad` | Alternative platoon format | Label format for platoon members on the alternative minimap. | Nova |
| `UI_tooltip_artilleryAim_enabled` | Artillery aim on minimap | Shows the SPG aiming point on the minimap. | Nova |
| `UI_tooltip_artilleryAim_scale` | Artillery aim scale (%) | Size of the SPG aiming point. | Nova |
| `UI_tooltip_artilleryAim_src` | Artillery aim style | Image used for the SPG aiming point. | Nova |
| `UI_tooltip_avoidOverlap` | Reduce overlapping names | Shortens names when labels would overlap. | Nova |
| `UI_tooltip_circles_mode` | Draw range / Visibility; Maximum spotting range / Visibility (+3) | When this circle is shown. | Nova |
| `UI_tooltip_compactLength` | Shortened name length | Number of characters kept when a name is shortened. | Nova |
| `UI_tooltip_customColors` | Custom label colors | Uses the label colors below instead of the game colors. | Nova |
| `UI_tooltip_customStyle` | Custom line colors | Uses the line colors and opacities below. | Nova |
| `UI_tooltip_dash` | Dash length (0: continuous); Draw range / Dash length (0: continuous) (+4) | Length of each dash, in pixels. 0 draws a continuous line. | Nova |
| `UI_tooltip_deadAlpha` | Destroyed vehicle icon opacity | Opacity of the icons of destroyed vehicles, in percent. | Nova |
| `UI_tooltip_deadColor` | Destroyed label color | Label color for destroyed vehicles. | Nova |
| `UI_tooltip_deadScale` | Destroyed vehicle icon scale | Size of the icons of destroyed vehicles. | Nova |
| `UI_tooltip_desaturate` | Lost vehicle color intensity | How strongly the icons at last known positions fade towards grey or a dull team color, in percent. | Nova |
| `UI_tooltip_direction` | Camera direction line | Shows or hides the camera direction line. Client setting keeps the game option. | Nova |
| `UI_tooltip_directionAlpha` | Camera direction line opacity | Opacity of the camera direction line, in percent. | Nova |
| `UI_tooltip_directionColor` | Direction line color | Color of the camera direction line. | Nova |
| `UI_tooltip_extraCircles` | Extra circles (JSON, up to 8) | Additional circles as a JSON list of up to 8 objects with radius (m), color, alpha, thickness, dash, gap, vehicleClass (all, lightTank, mediumTank, heavyTank, AT-SPG, SPG) and an optional vehicle name. | Nova |
| `UI_tooltip_fade` | Fade last-known markers | Fades last known position markers as time passes. | Nova |
| `UI_tooltip_fontSize` | Label font size; HP font size (+1) | Font size, in pixels. | Nova |
| `UI_tooltip_gap` | Dash spacing; Draw range / Dash spacing (+4) | Space between dashes, in pixels. | Nova |
| `UI_tooltip_geometry` | Custom line geometry (requires custom style) | Uses the line length below. Requires custom line colors. | Nova |
| `UI_tooltip_health_height` | HP bar height | Height of the HP bar, in pixels. | Nova |
| `UI_tooltip_health_mode` | HP display | How the HP is shown: value, percentage or bar. | Nova |
| `UI_tooltip_health_visibility` | HP visibility | When the vehicle HP is shown on the minimap. | Nova |
| `UI_tooltip_health_width` | HP bar width | Width of the HP bar, in pixels. | Nova |
| `UI_tooltip_hull` | Hull direction line | Shows a line in the direction of your vehicle's hull. | Nova |
| `UI_tooltip_hullColor` | Hull line color | Color of the hull direction line. | Nova |
| `UI_tooltip_icon` | Vehicle icon at the last position (instead of a dot) | Shows the vehicle icon at the last known position instead of a dot. | Nova |
| `UI_tooltip_icons_scale` | Vehicle icon scale | Size of the vehicle icons on the minimap. | Nova |
| `UI_tooltip_labels_align` | Label alignment | Alignment of the labels relative to the vehicle icon. | Nova |
| `UI_tooltip_labels_ally` | Ally format (empty: use normal) | Label format for allies. Leave it empty to use the normal format. | Nova |
| `UI_tooltip_labels_allyColor` | Ally label color | Label color for allies. | Nova |
| `UI_tooltip_labels_alternative` | Alternative label | Label shown for vehicles on the alternative minimap. | Nova |
| `UI_tooltip_labels_dead` | Destroyed label | Label shown for destroyed vehicles. | Nova |
| `UI_tooltip_labels_enabled` | Custom labels | Replaces the minimap vehicle labels with the formats below. | Nova |
| `UI_tooltip_labels_enemy` | Enemy format (empty: use normal) | Label format for enemies. Leave it empty to use the normal format. | Nova |
| `UI_tooltip_labels_enemyColor` | Enemy label color | Label color for enemies. | Nova |
| `UI_tooltip_labels_lost` | Last known position label | Label shown at the last known position of a vehicle. | Nova |
| `UI_tooltip_labels_normal` | Normal label | Label shown for vehicles on the normal minimap. Uses the same macros as the team panels. | Nova |
| `UI_tooltip_labels_shadow` | Label shadow | Adds a shadow to the labels. | Nova |
| `UI_tooltip_labels_squad` | Platoon format (empty: use normal) | Label format for platoon members. Leave it empty to use the normal format. | Nova |
| `UI_tooltip_labels_squadColor` | Platoon label color | Label color for platoon members. | Nova |
| `UI_tooltip_lines_length` | Line length (m) | Length of the direction lines, in metres. | Nova |
| `UI_tooltip_lostMarker_allyColor` | Last position color: ally | Color of last known positions of allies. | Nova |
| `UI_tooltip_lostMarker_enemyColor` | Last position color: enemy | Color of last known positions of enemies. | Nova |
| `UI_tooltip_lostMarker_squadColor` | Last position color: squad | Color of last known positions of platoon members. | Nova |
| `UI_tooltip_lostMarker_style` | Last position style | Color of last known position markers: a dull team color or grey. | Nova |
| `UI_tooltip_lostScale` | Lost vehicle icon scale | Size of the icons at last known positions. | Nova |
| `UI_tooltip_mapSize_color` | Map dimensions color | Color of the map dimensions text. | Nova |
| `UI_tooltip_mapSize_enabled` | Show map dimensions | Shows the map dimensions next to the minimap. | Nova |
| `UI_tooltip_mapSize_format` | Map dimensions format | Text of the map dimensions. Macros: {{width}} and {{height}} in metres. | Nova |
| `UI_tooltip_marks` | Distance marks every (m, 0: off) | Adds a distance mark on the lines every set number of metres. 0 turns the marks off. | Nova |
| `UI_tooltip_minimumAlpha` | Minimum last-known opacity | Lowest opacity a fading marker reaches, in percent. | Nova |
| `UI_tooltip_nearby_color` | Nearby highlight color | Color used to highlight nearby enemies. | Nova |
| `UI_tooltip_nearby_distance` | Nearby distance (m) | Fixed distance used when the range is set to Fixed distance, in metres. | Nova |
| `UI_tooltip_nearby_enabled` | Highlight nearby enemies | Highlights enemy vehicles within the selected range. | Nova |
| `UI_tooltip_nearby_range` | Nearby range | Distance used to decide which enemies are nearby. | Nova |
| `UI_tooltip_normalAlpha` | Normal map opacity | Opacity of the normal minimap, in percent. | Nova |
| `UI_tooltip_presentation_backgroundAlpha` | Map background opacity | Opacity of the map image behind the icons, in percent. | Nova |
| `UI_tooltip_presentation_center` | Center alternative map | Moves the alternative minimap to the centre of the screen. | Nova |
| `UI_tooltip_presentation_zoom` | Enlarge alternative map | Shows the alternative minimap larger than the normal one. Not used in Frontline. | Nova |
| `UI_tooltip_sector` | Gun traverse sector | Shows or hides the gun traverse sector. Client setting keeps the game option. | Nova |
| `UI_tooltip_sectorColor` | Sector line color | Color of the gun traverse sector lines. | Nova |
| `UI_tooltip_selfAlpha` | Own arrow opacity | Opacity of your own vehicle arrow, in percent. | Nova |
| `UI_tooltip_selfColor` | Own arrow color | Color of your own vehicle arrow. | Nova |
| `UI_tooltip_selfScale` | Own arrow scale | Size of your own vehicle arrow. | Nova |
| `UI_tooltip_shell_color` | Maximum shell range / Color | Color of the maximum shell range circle. | Nova |
| `UI_tooltip_showSeconds` | Seconds since last detection | Shows the seconds since the vehicle was last seen. | Nova |
| `UI_tooltip_sizeIndex` | Alternative map size (0-5) | Size step of the alternative minimap, from 0 (smallest) to 5 (largest). | Nova |
| `UI_tooltip_teamColors` | Team colors by state (alive/dead) | Colors the labels by team and by state (alive or destroyed). | Nova |
| `UI_tooltip_teamKillerColor` | Team killer color | Label color for team killers. | Nova |
| `UI_tooltip_thickness` | Stroke thickness; Draw range / Stroke thickness (+4) | Line thickness, in pixels. | Nova |
| `UI_tooltip_triangleAlpha` | Camera direction triangle opacity | Opacity of the camera direction triangle, in percent. | Nova |
| `UI_tooltip_x` | Label horizontal offset; HP horizontal offset (+1) | Horizontal offset, in pixels. | Nova |
| `UI_tooltip_y` | Label vertical offset; HP vertical offset (+1) | Vertical offset, in pixels. | Nova |

## penetration_indicator

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_displayOnAllies_tooltip` | Display On Allies | Also shows the armour and penetration indicator when aiming at allied vehicles. | Nova |

## profile_ratings

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_colorReceivedDamage_tooltip` | Color received damage | Colors the average damage received using the limits below. | Nova |
| `UI_setting_colorScale_tooltip` | Color palette | Color table used for the service record values. | Nova |
| `UI_setting_colorSurvival_tooltip` | Color survival rate | Colors the survival rate using the limits below. | Nova |
| `UI_setting_receivedDamageThresholds_tooltip` | Received damage limits (% of vehicle HP) | Five increasing limits for the average damage received, as a percentage of the vehicle's HP (0–500%), separated by commas. Use a dot for decimals. | Revista<br><sub>antes: Enter five increasing limits separated by commas. Survival: 0–100%; received damage: 0–500% of vehicle HP. Use a dot for decimals.</sub> |
| `UI_setting_showPlayerWN8_tooltip` | Show player WN8 | Adds the player's WN8 to the service record overview. | Nova |
| `UI_setting_showUnavailableWN8_tooltip` | Show -- when WN8 data is missing | Shows -- when WN8 cannot be calculated. Turn it off to hide the field instead. | Nova |
| `UI_setting_showVehicleWN8_tooltip` | Show vehicle WN8 | Adds the WN8 of each vehicle to the vehicle list and vehicle details. WN8 is calculated from random battles only. | Nova |
| `UI_setting_statisticsColors_tooltip` | Color statistics | Colors the values on the service record statistics page. | Nova |
| `UI_setting_summaryColors_tooltip` | Color overview | Colors the values on the service record overview page. | Nova |
| `UI_setting_survivalThresholds_tooltip` | Survival limits (%) | Five increasing limits for the survival rate, separated by commas, from 0 to 100%. Use a dot for decimals. | Revista<br><sub>antes: Enter five increasing limits separated by commas. Survival: 0–100%; received damage: 0–500% of vehicle HP. Use a dot for decimals.</sub> |
| `UI_setting_vehicleColors_tooltip` | Color vehicles | Colors the values in the service record vehicle list. | Nova |

## repair_controls

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_buttonChassis_tooltip` | Button: Restore Chassis | Repairs a destroyed track or wheel with the repair kit. | Nova |
| `UI_setting_buttonRepair_tooltip` | Button: Smart Repair | Uses the enabled actions below, in order: fire, devices, crew, stun and chassis. | Nova |
| `UI_setting_extinguishFire_tooltip` | Extinguish fire | Smart Repair puts out a fire with the fire extinguisher. | Nova |
| `UI_setting_healCrew_tooltip` | Heal crew | Smart Repair heals injured crew members in the configured priority order. | Nova |
| `UI_setting_removeStun_tooltip` | Remove stun | Smart Repair removes stun with the first aid kit. | Nova |
| `UI_setting_repairDevices_tooltip` | Repair devices | Smart Repair repairs damaged modules in the configured priority order. | Nova |
| `UI_setting_restoreChassis_tooltip` | Restore chassis | Smart Repair also repairs a destroyed track or wheel. | Nova |
| `UI_setting_useGoldKits_tooltip` | Use large consumables | Uses large repair kits, first aid kits and fire extinguishers when they are equipped. | Nova |

## server_turret_sync

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_activateMessage_tooltip` | Show Activation Message | Shows a message a few seconds after the battle starts, confirming the mod is active. | Revista<br><sub>antes: Show Activation Message in battle</sub> |
| `UI_setting_serverTurret_tooltip` | Server Turret | Moves the turret and gun to the server's aiming angles. Requires the server reticle to be enabled in the game settings. | Revista<br><sub>antes: Move Turret to Server Aim coordinates (need enabled Server Sight in game settings)</sub> |

## shell_flight_time

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_spgOnly_tooltip` | Just for SPG? | Shows the timer only when you drive an SPG. | Revista<br><sub>antes: If checked, then the timer will be visible only for SPG.</sub> |
| `UI_setting_template_tooltip` | Template | Text of the timer. Macros: %(flightTime).1fs shell flight time, %(distance)dm distance to the aiming point. | Revista<br><sub>antes: Macros '%(flightTime).1fs', %(distance)dm</sub> |
| `UI_setting_x_tooltip` | Position X | Horizontal offset of the timer from the crosshair, in pixels. Negative values move it left. | Nova |
| `UI_setting_y_tooltip` | Position Y | Vertical offset of the timer from the crosshair, in pixels. Negative values move it up. | Nova |

## sixth_sense_alert

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_defaultIconName_tooltip` | Default Icon Name | Included icon shown when you are spotted. | Revista<br><sub>antes: Select an embedded image.</sub> |
| `UI_setting_defaultIcon_tooltip` | Default Icon | Uses one of the icons included with the mod. Turn it off to use your own image. | Revista<br><sub>antes: Use embedded image.</sub> |
| `UI_setting_delay_tooltip` | Delay | Pause between the parts of a message that is too long for one chat message, in milliseconds. | Revista<br><sub>antes: Text message remains on screen for this amount of seconds before fading out.</sub> |
| `UI_setting_helpMessage_tooltip` | Help Message | Sends the "Help!" command to your team when you are spotted. | Revista<br><sub>antes: Send for chat (Help me) message automatically.</sub> |
| `UI_setting_iconSize_tooltip` | Image size | Size of the icon, in pixels (up to 180). | Revista<br><sub>antes: In pixels (max 180)</sub> |
| `UI_setting_lampShowTime_tooltip` | Lamp Show Time | Length of the countdown, in seconds. With Radio Interception it is 1.5 seconds shorter. The countdown is an estimate, not the exact end of spotting. | Revista<br><sub>antes: The countdown is an estimate; it does not indicate the exact end of enemy spotting.</sub> |
| `UI_setting_playTickSound_tooltip` | Play Tick Sound | Plays the game's countdown ticking while you are spotted. It replaces the custom detection sound. | Revista<br><sub>antes: Play tick sound.</sub> |
| `UI_setting_showTimerGraphicsColor_tooltip` | Graphics color. | Color of the countdown circle. | Revista<br><sub>antes: Color of the graphic circle.</sub> |
| `UI_setting_showTimerGraphicsRadius_tooltip` | Radius of the graphic circle. | Radius of the countdown circle, in pixels. | Revista<br><sub>antes: Size of the timer circle in pixels.</sub> |
| `UI_setting_showTimerGraphics_tooltip` | Show Timer Graphics. | Shows the countdown as a circle around the icon. | Revista<br><sub>antes: Show graphical timer circle.</sub> |
| `UI_setting_showTimer_tooltip` | Show Timer | Shows a countdown under the icon while you are spotted. | Revista<br><sub>antes: Show countdown timer when spotted.</sub> |
| `UI_setting_sixthSenseSound_tooltip` | Detection sound | Sound played when you are spotted, if the custom sound is enabled. | Nova |
| `UI_setting_spottedMessage_tooltip` | Spotted | Sends a message to the team chat when you are spotted, once per map square. | Revista<br><sub>antes: Enable spotted text in battle.</sub> |
| `UI_setting_spottedText_tooltip` | Text Format | Chat message sent when you are spotted. Macro: %(pos)s map square. | Revista<br><sub>antes: Use macros to edit the message (macro:'%(pos)s').</sub> |
| `UI_setting_userIcon_tooltip` | Custom image path | Your own PNG or JPEG image in mods/configs/driftkings/, used when the included icon is turned off. If it cannot be loaded, the included fallback icon is shown. | Revista<br><sub>antes: Custom PNG/JPEG image under mods/configs/driftkings/. Used when the embedded image is disabled.</sub> |
| `UI_setting_userSound_tooltip` | User Sound | Plays the detection sound selected below instead of the game's sound. | Revista<br><sub>antes: Enable custom sound when spotted.</sub> |

## sniper_camera

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_disableCamAfterShotLatency_tooltip` | Disable Cam After Shot Latency | Delay before returning to arcade view after the shot, in seconds. | Revista<br><sub>antes: Delay automatic shutdown of the camera.</sub> |
| `UI_setting_disableCamAfterShotSkipClip_tooltip` | Disable Cam After Shot Skip Clip | Stays in sniper view on vehicles with a magazine (clip) gun. | Revista<br><sub>antes: Do not exit if magazine loading system.</sub> |
| `UI_setting_disableCamAfterShot_tooltip` | Disable Cam After Shot | Returns to arcade view after you fire in sniper view. | Revista<br><sub>antes: Disable sniper mode after the shot.</sub> |
| `UI_setting_noBinoculars_tooltip` | Disable Binoculars. | Removes the dark binocular frame in sniper view. | Revista<br><sub>antes: Remove the blackout in sniper mode.</sub> |
| `UI_setting_noFlashBang_tooltip` | Disable Red Flash. | Removes the red screen flash when your vehicle is hit. | Revista<br><sub>antes: Remove red flash when taking damage.</sub> |
| `UI_setting_noShockWave_tooltip` | Shock Wave | Removes the camera shake when your vehicle is hit. | Revista<br><sub>antes: Remove camera shaking when hit by tank.</sub> |
| `UI_setting_noSniperDynamic_tooltip` | Sniper Dynamic | Turns off the dynamic camera (camera movement while firing and driving) in sniper view. | Revista<br><sub>antes: Disable dynamic camera in sniper mode.</sub> |
| `UI_setting_zoomSteps_steps_tooltip` | Zoom levels (JSON list) | At least four different zoom values of 2 or more, as a JSON list, for example [4, 6, 8, 12, 16, 25, 30]. Applied in the next battle. | Revista<br><sub>antes: Enter at least four unique numbers of 2 or more, for example [4, 6, 8, 12, 16, 25, 30]. Applied next battle.</sub> |
| `UI_tooltip_zoomSteps_enabled` | Custom zoom levels | Replaces the game's sniper zoom levels with the list below. | Nova |

## sound_bank_loader

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_IOPoolSize_tooltip` | IOPoolSize | Size of the sound file reading pool in the engine configuration. Changes require a game restart. | Nova |
| `UI_setting_debug_tooltip` | debug | Writes detailed sound bank information to game.log. | Nova |
| `UI_setting_defaultPool_tooltip` | defaultPool | Size of the default sound memory pool in the engine configuration. Changes require a game restart. | Nova |
| `UI_setting_lowEnginePool_tooltip` | lowEnginePool | Size of the low-level sound engine pool in the engine configuration. Changes require a game restart. | Nova |
| `UI_setting_max_voices_tooltip` | max_voices | Maximum number of sounds played at the same time. Changes require a game restart. | Nova |
| `UI_setting_memoryLimit_tooltip` | memoryLimit | Sound memory limit written to the game's engine configuration. Changes require a game restart. | Nova |
| `UI_setting_streamingPool_tooltip` | streamingPool | Size of the sound streaming pool in the engine configuration. Changes require a game restart. | Nova |

## target_distance

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_anchorHorizontalOffset_tooltip` | Horizontal Offset | Horizontal offset of the marker from its anchor point, in pixels. | Revista<br><sub>antes: Adjusts the horizontal position of the marker</sub> |
| `UI_setting_anchorPosition_tooltip` | Anchor Position | Point of the vehicle the marker is attached to. | Revista<br><sub>antes: Defines where the marker will be positioned relative to the vehicle</sub> |
| `UI_setting_anchorVerticalOffset_tooltip` | Vertical Offset | Vertical offset of the marker from its anchor point, in pixels. | Revista<br><sub>antes: Adjusts the vertical position of the marker</sub> |
| `UI_setting_decimalPrecision_tooltip` | Decimal Precision | Number of decimal places in the distance. | Revista<br><sub>antes: Defines how many decimal places will be displayed in the distance</sub> |
| `UI_setting_displayMode_tooltip` | Display Mode | When the distance markers are shown: always, or only while Alt is held. | Revista<br><sub>antes: Defines when the distance marker will be displayed</sub> |
| `UI_setting_drawTextShadow_tooltip` | Text Shadow | Adds a shadow to the text to make it easier to read. | Revista<br><sub>antes: Adds shadow to the text to improve visibility</sub> |
| `UI_setting_lockPositionOffsets_tooltip` | Lock Position Offsets | Prevents moving the markers in battle. When unlocked, hold Ctrl and drag a marker with the left mouse button while markers are shown. | Revista<br><sub>antes: Prevents changes to marker positions during gameplay</sub> |
| `UI_setting_markerTarget_tooltip` | Marker Targets | Which vehicles get a distance marker. | Revista<br><sub>antes: Defines which vehicles will receive the distance marker</sub> |
| `UI_setting_textAlpha_tooltip` | Text Transparency | Opacity of the distance text (0 transparent, 1 opaque). | Revista<br><sub>antes: Adjusts the transparency of the marker text</sub> |
| `UI_setting_textColor_tooltip` | Text Color | Color of the distance text. | Revista<br><sub>antes: Sets the text color of the marker</sub> |
| `UI_setting_textSize_tooltip` | Text Size | Font size of the distance text. | Revista<br><sub>antes: Adjusts the font size of the marker</sub> |

## target_information

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_aliveOnly_tooltip` | Alive Only | Shows information only for vehicles that are not destroyed. | Revista<br><sub>antes: Show only for alive players.</sub> |
| `UI_setting_altKey_tooltip` | Alt. Key | Hold this key to show information about your own vehicle. | Revista<br><sub>antes: Key for self vehicle information display.</sub> |
| `UI_setting_backgroundAlpha_tooltip` | Background Opacity | Opacity of the background (0 transparent, 1 opaque). | Revista<br><sub>antes: Opacity of the background panel (0-1)</sub> |
| `UI_setting_backgroundEnabled_tooltip` | Enable Background | Shows a background behind the text. | Revista<br><sub>antes: Show a background behind the text</sub> |
| `UI_setting_delay_tooltip` | Delay | How long the panel stays visible after you stop aiming at the vehicle, in seconds. 0 hides it immediately. | Revista<br><sub>antes: Hide panel delay (in seconds)</sub> |
| `UI_setting_showFor_tooltip` | Show For | Which vehicles show the panel: all, allies only or enemies only. | Revista<br><sub>antes: • Ally - Just show to 'ALLY' players tanks. • Enemy - Just show to 'ENEMY' players tanks. • All - Show to 'ALL' players tanks.</sub> |
| `UI_setting_templatePreset_tooltip` | Template Preset | Predefined layout of the information. The Full preset can be edited in the JSON configuration. | Revista<br><sub>antes: Choose a predefined template for the information display</sub> |
| `UI_setting_textLock_tooltip` | Disable text mouse dragging | Prevents moving the panel with the mouse. When unlocked, drag it while the cursor is visible. | Revista<br><sub>antes: This setting controls whether you are able to move text window with a mouse or not.</sub> |

## team_panels

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_tooltip_altMode` | Panel mode while holding ALT | Panel mode shown while ALT is held. Game default keeps the game behaviour. | Nova |
| `UI_tooltip_badgeAlpha` | badgeAlpha (+2) | Opacity of player badges, in percent. | Nova |
| `UI_tooltip_badgeOffsetX` | badgeOffsetXLeft; badgeOffsetXRight (+6) | Moves the player badge horizontally, in pixels. | Nova |
| `UI_tooltip_badgeWidth` | badgeWidth (+2) | Width reserved for the player badge, in pixels. | Nova |
| `UI_tooltip_bindToIcon` | Anchor to vehicle icon (+2) | Positions this element from the vehicle icon instead of the screen edge. | Nova |
| `UI_tooltip_clockFormat` | clockFormat | Clock shown on the loading screen, with time codes such as %H:%M. Leave it empty to hide it. | Nova |
| `UI_tooltip_colorScale` | colorScale | Color table used for ratings in the team panels. | Nova |
| `UI_tooltip_darkenNotReadyIcon` | darkenNotReadyIcon | Keeps the darker icon of players who have not loaded yet. Turn it off to show every icon at full brightness. | Nova |
| `UI_tooltip_diagnostics` | Performance diagnostics in log | Writes timing information for the team panels to game.log. Use it only to investigate performance problems. | Nova |
| `UI_tooltip_expandAreaWidth` | expandAreaWidth (+2) | Width of the area that expands the panel when the mouse is over it, in pixels. | Nova |
| `UI_tooltip_extraFields` | extraFieldsLeft; extraFieldsRight (+10) | Additional text or image fields for this side, as a JSON list of field definitions. | Nova |
| `UI_tooltip_extraFields_height` | height | Vertical spacing between players when the layout is vertical, in pixels. | Nova |
| `UI_tooltip_extraFields_width` | width | Horizontal spacing between players when the layout is horizontal, in pixels. | Nova |
| `UI_tooltip_extraFields_x` | x | Horizontal position of these fields, in pixels. | Nova |
| `UI_tooltip_extraFields_y` | y | Vertical position of these fields, in pixels. | Nova |
| `UI_tooltip_fixedPosition` | fixedPosition (+3) | Keeps each player in the same row for the whole battle instead of following the game order. | Nova |
| `UI_tooltip_formatLeftFrags` | formatLeftFrags | Frags format for the left team (allies). | Nova |
| `UI_tooltip_formatLeftNick` | formatLeftNick | Player name format for the left team (allies). Accepts macros such as {{name}}, {{clan}} and {{r}}. | Nova |
| `UI_tooltip_formatLeftVehicle` | formatLeftVehicle | Vehicle name format for the left team (allies). Accepts macros such as {{vehicle}}. | Nova |
| `UI_tooltip_formatRightFrags` | formatRightFrags | Frags format for the right team (enemies). | Nova |
| `UI_tooltip_formatRightNick` | formatRightNick | Player name format for the right team (enemies). Accepts macros such as {{name}}, {{clan}} and {{r}}. | Nova |
| `UI_tooltip_formatRightVehicle` | formatRightVehicle | Vehicle name format for the right team (enemies). Accepts macros such as {{vehicle}}. | Nova |
| `UI_tooltip_formats` | formats | Fields shown when the panel is hidden, as a JSON list of field definitions. | Nova |
| `UI_tooltip_fragsFieldOffsetX` | fragsFieldOffsetXLeft; fragsFieldOffsetXRight | Moves the frags field horizontally, in pixels. | Nova |
| `UI_tooltip_fragsFieldShowBorder` | fragsFieldShowBorder | Draws a border around the frags field to help adjust the layout. | Nova |
| `UI_tooltip_fragsFieldWidth` | fragsFieldWidthLeft; fragsFieldWidthRight | Width of the frags field, in pixels. | Nova |
| `UI_tooltip_fragsFormat` | fragsFormatLeft; fragsFormatRight (+6) | Frags text. Accepts macros and <font> tags. | Nova |
| `UI_tooltip_fragsOffsetX` | fragsOffsetXLeft; fragsOffsetXRight (+6) | Moves the frags horizontally, in pixels. | Nova |
| `UI_tooltip_fragsShadow` | fragsShadowLeft; fragsShadowRight (+6) | Shadow of the frags as JSON (distance, angle, color, alpha, blur, strength), or null to keep the game shadow. | Nova |
| `UI_tooltip_fragsWidth` | fragsWidth (+2) | Width of the frags, in pixels. | Nova |
| `UI_tooltip_hpKey` | Key to show HP | Hold this key to show the HP when the visibility is set to show while the key is held. | Nova |
| `UI_tooltip_hpVisibility` | HP visibility | When the vehicle HP is shown in the team panels. | Nova |
| `UI_tooltip_hp_format` | hp.format | HP text. Accepts macros such as {{hp}}, {{hp-max}} and {{hp-ratio}}. | Nova |
| `UI_tooltip_iconAlpha` | Vehicle icon opacity | Opacity of the vehicle icons in the team panels, in percent. | Nova |
| `UI_tooltip_inviteIndicatorAlpha` | inviteIndicatorAlpha | Opacity of the platoon invitation indicator, in percent. | Nova |
| `UI_tooltip_inviteIndicatorX` | inviteIndicatorX | Horizontal position of the platoon invitation indicator, in pixels. | Nova |
| `UI_tooltip_inviteIndicatorY` | inviteIndicatorY | Vertical position of the platoon invitation indicator, in pixels. | Nova |
| `UI_tooltip_layout` | layout | How players are stacked when the panel is hidden: vertical or horizontal. | Nova |
| `UI_tooltip_loading_enabled` | Enabled | Applies these settings to the battle loading screen. | Nova |
| `UI_tooltip_nameFieldOffsetX` | nameFieldOffsetXLeft; nameFieldOffsetXRight (+2) | Moves the player name field horizontally, in pixels. | Nova |
| `UI_tooltip_nameFieldShowBorder` | nameFieldShowBorder | Draws a border around the player name field to help adjust the layout. | Nova |
| `UI_tooltip_nameFieldWidth` | nameFieldWidthLeft; nameFieldWidthRight | Width of the player name field, in pixels. | Nova |
| `UI_tooltip_nameFieldWidthDelta` | nameFieldWidthDeltaLeft; nameFieldWidthDeltaRight | Makes the player name field wider (positive) or narrower (negative) than the game width, in pixels. | Nova |
| `UI_tooltip_nickFormat` | nickFormatLeft; nickFormatRight (+6) | Player name text. Accepts macros such as {{name}}, {{clan}} and {{r}}, and <font> tags. | Nova |
| `UI_tooltip_nickMaxWidth` | nickMaxWidth (+2) | Maximum width of the player name, in pixels. | Nova |
| `UI_tooltip_nickMinWidth` | nickMinWidth (+2) | Minimum width of the player name, in pixels. | Nova |
| `UI_tooltip_nickOffsetX` | nickOffsetXLeft; nickOffsetXRight (+6) | Moves the player name horizontally, in pixels. | Nova |
| `UI_tooltip_nickShadow` | nickShadowLeft; nickShadowRight (+6) | Shadow of the player name as JSON (distance, angle, color, alpha, blur, strength), or null to keep the game shadow. | Nova |
| `UI_tooltip_playersPanel_alpha` | Panel background opacity | Opacity of the team panel background, in percent. | Nova |
| `UI_tooltip_playersPanel_enabled` | Enabled | Applies these settings to the team panels at the sides of the screen. | Nova |
| `UI_tooltip_prestigeOffsetX` | prestigeOffsetXLeft; prestigeOffsetXRight (+6) | Moves the elite (prestige) level horizontally, in pixels. | Nova |
| `UI_tooltip_profiles_enabled` | Enabled (+3) | Uses the custom layout in this panel mode. | Nova |
| `UI_tooltip_rating` | Rating macro r | Rating returned by the {{r}} macro and its colors. | Nova |
| `UI_tooltip_removeHealthPoints` | Hide native HP bars | Hides the game's HP bars in the team panels. | Nova |
| `UI_tooltip_removePanelsModeSwitcher` | removePanelsModeSwitcher | Hides the buttons that switch the team panel mode. | Nova |
| `UI_tooltip_removePlayerStatusIcon` | Hide player status icons | Hides player status icons. | Nova |
| `UI_tooltip_removePrestigeLevel` | Hide elite levels | Hides the elite (prestige) levels. | Nova |
| `UI_tooltip_removeRankBadgeIcon` | Hide badges | Hides player badges. | Nova |
| `UI_tooltip_removeSelectedBackground` | Hide selected player background | Hides the highlight behind the selected player. | Nova |
| `UI_tooltip_removeSpottedIndicator` | Replace native spotted indicator (+2) | Hides the game's spotted indicator so the custom spotted marker is used instead. | Nova |
| `UI_tooltip_removeSquadIcon` | Hide platoon icons (+4) | Hides platoon icons. | Nova |
| `UI_tooltip_removeTesterIcon` | Hide tester icons | Hides tester icons. | Nova |
| `UI_tooltip_removeVehicleLevel` | Hide vehicle tiers | Hides vehicle tiers. | Nova |
| `UI_tooltip_removeVehicleTypeIcon` | Hide vehicle type icons | Hides vehicle type icons. | Nova |
| `UI_tooltip_shadow_alpha` | Panel background opacity | Opacity of the shadow, in percent. | Nova |
| `UI_tooltip_shadow_angle` | hp.shadow.angle | Direction of the shadow, in degrees. | Nova |
| `UI_tooltip_shadow_blur` | hp.shadow.blur | Blur of the shadow. | Nova |
| `UI_tooltip_shadow_color` | Color | Color of the shadow. | Nova |
| `UI_tooltip_shadow_distance` | hp.shadow.distance | Distance of the shadow from the text, in pixels. | Nova |
| `UI_tooltip_shadow_enabled` | Enabled | Adds a shadow to the HP text. | Nova |
| `UI_tooltip_shadow_strength` | hp.shadow.strength | Strength of the shadow. | Nova |
| `UI_tooltip_showUnavailable` | showUnavailable (+1) | Keeps the custom layout for players without statistics. Turn it off to show the game layout for them. | Nova |
| `UI_tooltip_spottedEnabled` | spottedEnabled | Shows whether each enemy is spotted, lost or never seen in the team panels. | Nova |
| `UI_tooltip_spottedIndicatorAlpha` | spottedIndicatorAlpha (+2) | Opacity of the game's spotted indicator, in percent. | Nova |
| `UI_tooltip_spottedIndicatorOffsetX` | spottedIndicatorOffsetX (+2) | Moves the game's spotted indicator horizontally, in pixels. | Nova |
| `UI_tooltip_spottedIndicatorOffsetY` | spottedIndicatorOffsetY (+2) | Moves the game's spotted indicator vertically, in pixels. | Nova |
| `UI_tooltip_squadIconAlpha` | squadIconAlpha (+2) | Opacity of the platoon icon, in percent. | Nova |
| `UI_tooltip_squadIconOffsetX` | Left platoon icon: X offset; Right platoon icon: X offset (+2) | Moves the platoon icon horizontally, in pixels. | Nova |
| `UI_tooltip_standardFields` | standardFields (+2) | Game fields shown in this mode and their order, as a JSON list, for example ["frags", "badge", "nick", "vehicle"]. | Nova |
| `UI_tooltip_startMode` | Initial panel mode | Panel mode set when the battle starts. Game default keeps the game behaviour. | Nova |
| `UI_tooltip_statsEnabled` | statsEnabled | Loads player statistics for the rating macros in the panels, the loading screen and the statistics screen. | Nova |
| `UI_tooltip_tab_enabled` | Enabled | Applies these settings to the statistics screen (TAB). | Nova |
| `UI_tooltip_templates_enabled` | Enabled | Shows this element. | Nova |
| `UI_tooltip_templates_height` | enemySpottedMarker.height; hpBar.height (+1) | Height of this element, in pixels. | Nova |
| `UI_tooltip_templates_src` | enemySpottedMarker.src; hpBar.src (+1) | Image path of this element, for example gui/maps/driftkings/.... | Nova |
| `UI_tooltip_templates_width` | enemySpottedMarker.width; hp.width (+2) | Width of this element, in pixels. | Nova |
| `UI_tooltip_templates_x` | enemySpottedMarker.x; hp.x (+2) | Horizontal position of this element, in pixels. | Nova |
| `UI_tooltip_templates_y` | enemySpottedMarker.y; hp.y (+2) | Vertical position of this element, in pixels. | Nova |
| `UI_tooltip_textFormat_align` | hp.textFormat.align | Text alignment: left, center or right. | Nova |
| `UI_tooltip_textFormat_color` | Color | Text color. | Nova |
| `UI_tooltip_textFormat_font` | hp.textFormat.font | Font name, for example $FieldFont. | Nova |
| `UI_tooltip_textFormat_size` | hp.textFormat.size | Font size. | Nova |
| `UI_tooltip_vehicleFieldOffsetX` | vehicleFieldOffsetXLeft; vehicleFieldOffsetXRight (+2) | Moves the vehicle name field horizontally, in pixels. | Nova |
| `UI_tooltip_vehicleFieldShowBorder` | vehicleFieldShowBorder | Draws a border around the vehicle name field to help adjust the layout. | Nova |
| `UI_tooltip_vehicleFieldWidth` | vehicleFieldWidthLeft; vehicleFieldWidthRight | Width of the vehicle name field, in pixels. | Nova |
| `UI_tooltip_vehicleFieldWidthDelta` | vehicleFieldWidthDeltaLeft; vehicleFieldWidthDeltaRight | Makes the vehicle name field wider (positive) or narrower (negative) than the game width, in pixels. | Nova |
| `UI_tooltip_vehicleFormat` | vehicleFormatLeft; vehicleFormatRight (+6) | Vehicle name text. Accepts macros such as {{vehicle}} and <font> tags. | Nova |
| `UI_tooltip_vehicleIconAlpha` | Vehicle icon opacity | Opacity of the vehicle icons, in percent. | Nova |
| `UI_tooltip_vehicleIconOffsetX` | Left vehicle icon: X offset; Right vehicle icon: X offset (+10) | Moves the vehicle icon horizontally, in pixels. | Nova |
| `UI_tooltip_vehicleLevelAlpha` | vehicleLevelAlpha (+2) | Opacity of the vehicle tier, in percent. | Nova |
| `UI_tooltip_vehicleLevelOffsetX` | vehicleLevelOffsetXLeft; vehicleLevelOffsetXRight (+6) | Moves the vehicle tier horizontally, in pixels. | Nova |
| `UI_tooltip_vehicleOffsetX` | vehicleOffsetXLeft; vehicleOffsetXRight (+6) | Moves the vehicle name horizontally, in pixels. | Nova |
| `UI_tooltip_vehicleShadow` | vehicleShadowLeft; vehicleShadowRight (+6) | Shadow of the vehicle name as JSON (distance, angle, color, alpha, blur, strength), or null to keep the game shadow. | Nova |
| `UI_tooltip_vehicleWidth` | vehicleWidth (+2) | Width of the vehicle name, in pixels. | Nova |

## tech_tree_marks_of_excellence

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_badgeOffsetX_tooltip` | Position X (left / right) | Moves the mark information horizontally. Negative values move it left. | Revista<br><sub>antes: Negative: left. Positive: right.</sub> |
| `UI_setting_badgeOffsetY_tooltip` | Position Y (up / down) | Moves the mark information vertically. Negative values move it up. | Revista<br><sub>antes: Negative: up. Positive: down.</sub> |
| `UI_setting_colorRating_tooltip` | Color table | Color table used for marks in the tech tree. | Revista<br><sub>antes: Color scale for marks of excellence.</sub> |
| `UI_setting_showInTechTreeMarkOfGunPercent_tooltip` | TechTree: show MoE % | Shows the current mark percentage. | Nova |
| `UI_setting_showInTechTreeMarkOfGunTankNameColored_tooltip` | TechTree: MoE colorize vehicle name | Colors the vehicle name according to its mark percentage. | Nova |
| `UI_setting_showInTechTreeMastery_tooltip` | TechTree: show Mastery | Shows the Mastery Badge earned on the vehicle. | Nova |
| `UI_setting_showInTechTree_tooltip` | TechTree: enabled | Shows mark information on vehicles in the tech tree. | Nova |

## third_person_zoom

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_max_tooltip` | (arcade, artillery and postmortem cameras) | Largest camera distance from the vehicle, in metres. | Revista<br><sub>antes: Maximum camera distance from vehicle</sub> |
| `UI_setting_min_tooltip` | (arcade, artillery and postmortem cameras) | Smallest camera distance from the vehicle, in metres. | Revista<br><sub>antes: Minimum camera distance from vehicle</sub> |
| `UI_setting_scrollSensitivity_tooltip` | (arcade, artillery and postmortem cameras) | How far each step of the mouse wheel moves the camera. | Revista<br><sub>antes: Adjust mouse wheel zoom sensitivity</sub> |
| `UI_setting_startDeadDist_tooltip` | (arcade, artillery and postmortem cameras) | Camera distance when the battle starts and after your vehicle is destroyed, in metres. | Revista<br><sub>antes: Initial exterior camera distance in metres, including the post-destruction camera.</sub> |
| `UI_tooltip_useClientDefaults` | Strategic artillery: Use native client values; Alternative artillery: Use native client values | Uses the game's own values for this camera and ignores the values above. | Nova |

## vehicle_carousel

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_colorRating_tooltip` | Color table | Color table used for statistics in the carousel. | Nova |
| `UI_setting_showIcons_tooltip` | Show icons | Shows the images in the custom carousel fields. Turn it off to show only their text. | Nova |
| `UI_tooltip_backgroundAlpha` | Background opacity | Opacity of the carousel background, in percent. | Nova |
| `UI_tooltip_carousel_height` | Standard layout: Height; Compact layout: Height | Height of each slot, in pixels. | Nova |
| `UI_tooltip_carousel_width` | Standard layout: Width; Compact layout: Width | Width of each slot, in pixels. | Nova |
| `UI_tooltip_cellType` | Layout | Slot layout of the carousel. Automatic follows the game layout. | Nova |
| `UI_tooltip_edgeFadeAlpha` | Edge fade opacity | Opacity of the fade at both ends of the carousel, in percent. | Nova |
| `UI_tooltip_enableLockBackground` | Show unavailable vehicle background | Shows the background of vehicles that cannot be used right now. | Nova |
| `UI_tooltip_extraFields_align` | 2: Alignment; 4: Alignment (+5) | Horizontal alignment of the text. | Nova |
| `UI_tooltip_extraFields_alpha` | 1: Opacity; 3: Opacity (+4) | Opacity of the field, in percent. | Nova |
| `UI_tooltip_extraFields_bgColor` | 13: Background color; 1: Background color | Background color of the field. | Nova |
| `UI_tooltip_extraFields_color` | — | Text color of the field. | Nova |
| `UI_tooltip_extraFields_enabled` | 14: Enabled; 2: Enabled (+2) | Shows this custom field. | Nova |
| `UI_tooltip_extraFields_fontSize` | — | Font size of the field. | Nova |
| `UI_tooltip_extraFields_format` | 1: Text template; 2: Text template (+13) | Text of the field. Macros such as {{wn8}}, {{battles}}, {{winRate}} and {{avgDamage}}; colors with {{c:wn8}}. Missing statistics show --. | Nova |
| `UI_tooltip_extraFields_height` | 11: Height; 13: Height (+3) | Height of the field, in pixels. | Nova |
| `UI_tooltip_extraFields_iconSize` | — | Size of the icons in the field, in pixels. | Nova |
| `UI_tooltip_extraFields_layer` | 13: Display layer; 14: Display layer (+1) | Shows the field behind or in front of the slot contents. | Nova |
| `UI_tooltip_extraFields_src` | 2: Image resource path | Image shown in the field, from gui/maps/driftkings/ or mods/configs/driftkings/. | Nova |
| `UI_tooltip_extraFields_width` | 11: Width; 13: Width (+3) | Width of the field, in pixels. | Nova |
| `UI_tooltip_extraFields_x` | 1: Horizontal position; 2: Horizontal position (+16) | Horizontal position of the field inside the slot, in pixels. | Nova |
| `UI_tooltip_extraFields_y` | 1: Vertical position; 2: Vertical position (+16) | Vertical position of the field inside the slot, in pixels. | Nova |
| `UI_tooltip_fields_alpha` | National flag: Opacity; Vehicle image: Opacity (+24) | Opacity of the element, in percent. | Nova |
| `UI_tooltip_fields_dx` | National flag: Horizontal offset; Vehicle image: Horizontal offset (+24) | Moves the element horizontally, in pixels. | Nova |
| `UI_tooltip_fields_dy` | National flag: Vertical offset; Vehicle image: Vertical offset (+24) | Moves the element vertically, in pixels. | Nova |
| `UI_tooltip_fields_enabled` | Show National flag; Show Vehicle image (+24) | Shows this element of the slot. Turning it off also hides the elements inside it. | Nova |
| `UI_tooltip_fields_scale` | National flag: Scale; Vehicle image: Scale (+24) | Size of the element compared with its normal size. | Nova |
| `UI_tooltip_filters_enabled` | Filter: Vehicle parameters; Filter: Favourite vehicles (+3) | Shows this filter button above the carousel. | Nova |
| `UI_tooltip_gap` | Standard layout: Spacing between slots; Compact layout: Spacing between slots | Space between slots, in pixels. | Nova |
| `UI_tooltip_hideBuySlot` | Hide garage slot purchase | Hides the slot for buying a garage slot. | Nova |
| `UI_tooltip_hideBuyTank` | Hide vehicle purchase slot | Hides the slot for buying a vehicle. | Nova |
| `UI_tooltip_hideRestoreTank` | Hide vehicle recovery slot | Hides the slot for restoring a vehicle. | Nova |
| `UI_tooltip_horizontal` | Filter spacing: Horizontal | Horizontal space between filter buttons, in pixels. | Nova |
| `UI_tooltip_nationsOrder` | Nation order (comma-separated) | Nation order used when sorting by nation, separated by commas, for example ussr, germany, usa. | Nova |
| `UI_tooltip_rows` | Rows (0 = game default) | Number of carousel rows. 0 keeps the game setting. | Nova |
| `UI_tooltip_scrollingSpeed` | Scrolling speed | Scrolling speed of the carousel. | Nova |
| `UI_tooltip_showTotalSlots` | Show total garage slots | Shows the total number of garage slots. | Nova |
| `UI_tooltip_showUsedSlots` | Show occupied garage slots | Shows the number of occupied garage slots. | Nova |
| `UI_tooltip_slotBackgroundAlpha` | Slot background opacity | Opacity of the slot backgrounds, in percent. | Nova |
| `UI_tooltip_slotBorderAlpha` | Slot border opacity | Opacity of the slot borders, in percent. | Nova |
| `UI_tooltip_slotSelectedBorderAlpha` | Selected slot border opacity | Opacity of the border of the selected vehicle, in percent. | Nova |
| `UI_tooltip_sortingCriteria` | Sorting (comma-separated; - = descending) | Sort order, separated by commas. Prefix a criterion with - to sort descending. Criteria: nation, type, level, premium, battles, winRate, markOfMastery, damageRating, marksOnGun, battlePassPoints, wn8, avgDamage. | Nova |
| `UI_tooltip_suppressCarouselTooltips` | Hide carousel tooltips | Hides the tooltips of the carousel slots. | Nova |
| `UI_tooltip_typesOrder` | Vehicle type order (comma-separated) | Vehicle type order used when sorting by type: lightTank, mediumTank, heavyTank, AT-SPG, SPG. | Nova |
| `UI_tooltip_vertical` | Filter spacing: Vertical | Vertical space between filter buttons, in pixels. | Nova |

## vehicle_health

| Chave | Controlo(s) | Descrição | Estado |
|---|---|---|---|
| `UI_setting_x_tooltip` | Position X | Horizontal offset of the health bar from the crosshair, in pixels. Negative values move it left. | Nova |
| `UI_setting_y_tooltip` | Position Y | Vertical offset of the health bar from the crosshair, in pixels. Negative values move it up. | Nova |
