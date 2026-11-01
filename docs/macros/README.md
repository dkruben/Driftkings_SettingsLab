# Macro reference

Updated on 2026-11-01 from the `develop` sources. Every module has its own macro engine, so the syntax and the available names depend on where the template is used. Paths are relative to `mod/res/scripts/client/driftkings/` unless stated otherwise. Colour macros always return a complete `#RRGGBB` value: write `color='{{c:wn8}}'`, never `color='#{{c:wn8}}'`.

| Where | Syntax | Engine |
| --- | --- | --- |
| Team panels, loading screen, TAB | `{{name}}` with formats, conditions and fallbacks | `core/panel_macros.py`, values from `core/panel_model.py` |
| Vehicle markers | `{{name}}` with `&&`/`\|\|` conditions | `core/vehicle_markers/expressions.py`, names in `core/vehicle_markers/fields.py` |
| Vehicle carousel | `{{v.name}}` or `{{name}}`, `{{v.c:name}}`, `{{icon:name}}` | `core/carousel.py`, values from `lobby/vehicle_carousel.py` |
| Battle efficiency and battle results | `{name}`, `{c:name}` | `components/battle_performance.py` |
| Team strength | `{name}` | `battle/battle_statistics.py` |
| Spotting and assistance notifications | `{name}` (Python `str.format`) | `battle/enemy_spotting_status.py` |
| Target information | `{{name}}`, `{{i18n:KEY}}` | `battle/target_information.py` |
| Aiming countdown, shell flight time, penetration indicator | `{name}`, `{name:d}`, `{name:.1f}` | `gameface/battle/reticle_texts.py` |
| Sixth Sense | `%(pos)s` | `battle/sixth_sense_alert.py` |
| Minimap labels and map size | `{{name}}`, `{{name%.Ns}}` | `core/minimap.py` |
| Clocks | `%H`, `%M`, … or `H:i:s` | `gameface/mods/driftkings/main/clock.js`, `flash/battle/debug_panel.py`, `loadingclock.as` |

## Team panels, loading screen and TAB

### Syntax

| Form | Meaning |
| --- | --- |
| `{{key}}` | Value; empty when missing. |
| `{{key\|fallback}}` | Fallback text (may contain macros) when the value is missing or empty. |
| `{{key%spec}}` | printf format: `[-+0 ]?` width up to three digits, optional `.precision` up to three digits, then `s`, `d` or `f`. Example: `{{winrate%2d}}`, `{{name%.12s}}`. |
| `{{key~suffix}}` | Appends `suffix` when the value exists. With `%…s` the suffix is added only if the text was cut, so `{{name%.12s~…}}` marks truncated names. |
| `{{test?yes\|no}}` | Condition. `test` is a key (true unless empty, `0`, `false`) or a comparison with `=`, `==`, `!=`, `>`, `<`, `>=`, `<=`. Numbers compare numerically. |
| `{{my-key}}` | The same value for the player's own vehicle, e.g. `{{my-wn8}}`. |
| `{{.path.to.option}}` | Reads a value from the team-panel configuration; nested macros in it are expanded. |
| `{{i18n:KEY}}` | Driftkings translation. `{{l10n:KEY}}` is the legacy spelling. |
| `{{hp-ratio}}`, `{{hp-ratio:WIDTH}}` | Current HP as a width in pixels (default 100, maximum 4000). |
| `{{c:key}}`, `{{a:key}}` | Colour (`#RRGGBB`) and alpha (100 with data, 0 without) of a statistic. |

Macros can be nested (up to 24 levels). The settings panel reports unknown names with `settings/panel_validation.py`.

### Player and vehicle

| Macro | Value |
| --- | --- |
| `name`, `nick`, `clan`, `clannb` | Player name; name plus `[CLAN]`; `[CLAN]`; clan tag without brackets. |
| `vehicle` | Vehicle name: **short** in the TAB and side panels, **full** on the loading screen. |
| `vehicle-short`, `vehiclename` | Short name everywhere; internal name (`usa-A12_T32`). |
| `veh-id` | Vehicle entity ID. |
| `level`, `rlevel` | Tier as a number and as a Roman numeral. |
| `vtype`, `vtype-key`, `vtype-l` | `LT`/`MT`/`HT`/`TD`/`SPG` (the first two are equal); class tag (`heavyTank`). |
| `nation` | Nation key (`usa`). |
| `premium`, `special` | `premium` / `special`, or empty. |
| `hp`, `hp-max` | Current and maximum HP (0 when destroyed). |
| `frags` | Kills in this battle. |
| `squad-num` | Platoon number. |
| `rankBadgeId`, `bp-stage`, `hasBadges` | Selected badge, Battle Pass stage, `true` when any player shows a badge. |
| `region`, `battletype-key`, `colorblind` | Realm, arena GUI type, colour-blind mode. |
| `pp.mode`, `pp.widthLeft`, `pp.widthRight` | Native panel mode index and column widths. |

### State flags

Each flag holds its own name when true and is empty otherwise, so it works directly in conditions such as `{{alive?…|…}}`.

`alive`, `ally`, `player` (`pl`), `anonym`, `ready`, `squad` (`sq`), `selected` (`sel`), `tk`, `friend`, `ignored`, `muted`, `chatban`, `spotted` (`spotted`/`lost`), `stat-available` (`stat`), `stat-color` (`stat`, also set in event modes where the numbers are hidden).

`sys-color-key` is `player`, `ally` or `enemy`. `c:system` is `#FFDD33`, `#96FF00` or `#F50800`. `c:spotted` is `#FFBB00` when spotted, otherwise `#D9D9D9`; `a:spotted` is 100 when the spotted indicator applies.

### Statistics

| Macro | Value |
| --- | --- |
| `wn8`, `wnx`, `eff`, `wgr` | Account ratings (WNX may be missing when expected values or assistance are incomplete). |
| `xwn8`, `xeff` | Ratings on the 0–100 X scale. |
| `winrate`, `battles` | Account random-battle win rate and battle count. |
| `kb` | Battles in thousands as a number (`{{kb%.1f}}k`). |
| `t-battles`, `t-winrate` | Battles and win rate on this vehicle (also `t_battles`, `t_winrate`). |
| `t-kb`, `t-hb` | Vehicle battles in thousands / hundreds. |
| `tdv` | Average damage on this vehicle divided by its maximum HP. |
| `spg_battles`, `spg_percent`, `mark_of_mastery` | SPG battles and share, mastery badge on this vehicle. |
| `r`, `xr`, `r_size` | Rating selected in the settings, its X-scale value, suggested field width. |

Colours and alphas exist for `wn8`, `eff`, `wgr`, `winrate`, `xwn8`, `xeff`, `battles`, `t-battles`, `t-winrate`, `tdv`, `r`, `xr` and `kb` (for example `{{c:r}}`, `{{a:wn8}}`). Without statistics the colour is `#AAAAAA` and the alpha 0. In event modes the numbers are hidden but the colours remain.

## Vehicle markers

Names are validated against a fixed list; any other name is rejected when the configuration is saved.

| Group | Macros |
| --- | --- |
| Vehicle and player | `vehicle`, `name`, `nick`, `clan`, `level`, `vtype`, `position` (place in the team list), `battletype` (empty in random battles) |
| Health | `hp`, `maxHp`, `hp-max`, `hpPercent`, `hp-ratio`, `c:hp` |
| Statistics | `r`, `xr`, `wn8`, `wnx`, `eff`, `xwn8`, `xeff`, `wgr`, `winrate`, `battles`, `kb`, `stat-available`, `a:r` |
| Colours | `c:team`, `c:system`, and `c:` plus each statistic above |
| Flags | `alive`, `dead`, `ally`, `enemy`, `player`, `squad`, `anonym` |
| Distance and turret | `distance`, `dist` (rounded metres, empty without a live vehicle), `turret`, `stock-turret`, `turret-vulnerability` |
| Damage messages only | `dmg`, `c:dmg`, `dmg-ratio`, `dmg-kind`, `dmg-source`, `i18n:blownUp` (legacy `l10n:blownUp`, `blownUp`) |

Conditions accept `&&` and `||`, comparisons, fallbacks and basic formats: `{{alive&&distance<=500?{{vehicle}} ({{distance}} m)|}}`, `{{r|--}}`, `{{winrate%.1f}}`. See the [marker guide](../vehicle_markers/README.md) for examples.

## Vehicle carousel

### Syntax

`{{v.key}}` and `{{key}}` are equivalent. Supported: `{{key%2d}}`, `{{key%.1f}}`, `{{key:.1f}}`, `{{key:d}}`, `{{key~suffix}}`, `{{key|fallback}}`, `{{key?yes|no}}`, `{{key==value?yes|no}}`, `{{key!=value?yes|no}}`. Missing values display `--` unless a fallback is given. Nested macros such as `{{v.tfb?{{v.wn8expd%d}}|}}` work.

### Values

| Macro (aliases) | Value |
| --- | --- |
| `vehicle` (`name`), `level` (`tier`), `nation`, `type`, `premium` | Short name, tier, nation, class tag, premium flag. |
| `battles` (`t_battles`) | Random battles on the vehicle. |
| `winRate` (`winrate`), `hitRate` (`hitsRatio`) | Win rate and hit rate in %. |
| `avgDamage` (`tdb`), `avgFrags` (`tfb`), `avgSpotted` | Average damage, kills, spots. |
| `avgReceived`, `avgAssist`, `avgBlocked`, `avgStun` | Average received, assisted, blocked and stun damage. |
| `avgCapture`, `avgDefence` | Average capture and defence points. |
| `damageRatio`, `damageHP` | Damage dealt / received; average damage / maximum HP. |
| `wn8expd`, `wn8effd` | WN8 expected damage; average damage / expected damage. |
| `wn8`, `eff`, `xwn8`, `xeff`, `wnx` | Ratings on this vehicle. |
| `marks` (`damageRating`), `marksOnGun` | Mark-of-excellence percentage (tier V+), marks earned. |
| `mastery` (`markOfMastery`) | Mastery badge 0–4. |
| `battletiermin`, `battletiermax` | Battle tier range. |
| `classColor` | Class colour (`#RRGGBB`). |

`{{v.c:key}}` colours any of these with the carousel palette (`c:winrate`, `c:tdb`, `c:wn8effd`, `c:damageRating`, …). `{{v.c:type}}` is the class colour and is also the name of the card background image (`gui/maps/driftkings/carroucel/{{v.c:type}}.svg`). The old `{{v.c_key}}` form was removed on 2026-11-01.

### Icons

`{{icon:damage}}`, `{{icon:assist}}`, `{{icon:blocked}}`, `{{icon:wins}}`, `{{icon:battles}}` (native library icons), `{{icon:marksOnGun}}` (marks of the vehicle's nation, or the zero-marks image) and `{{icon:mastery}}` (mastery badge, `--` without one).

## Battle efficiency and battle results

Single braces.

| Macro | Value |
| --- | --- |
| `{frags}`, `{damage}`, `{spotted}`, `{defence}`, `{capture}` | Battle counters (efficiency text only). |
| `{wn8}`, `{xwn8}`, `{eff}`, `{xeff}`, `{xte}` | Battle ratings. |
| `{wnx}` | Battle WNX, `--` when unavailable. |
| `{dmg}`, `{diff}` | Damage and difference from expected damage. |
| `{wn8effd}` | Damage / expected damage, two decimals. |

Each has a colour `{c:…}` (`{c:wn8}`, `{c:diff}`, `{c:wn8effd}`, …). Battle results also accept `{c:x}`, the X-scale colour. `{mapName}` and `{battleType}` are removed from result templates because the native header already shows them.

## Other battle texts

| Module | Macros |
| --- | --- |
| Team strength | `{header}`, `{allyChance}`, `{enemyChance}` (already coloured), `{compareSign}` |
| Spotting and assistance | `{icons}`, `{names}`, `{vehicles}`, `{icons_names}`, `{icons_vehicles}`, `{full}`, `{damage}` |
| Aiming countdown | `{timer:.1f}` seconds, `{percent:d}`, `{color}` |
| Shell flight time | `{flightTime:.1f}`, `{distance:d}` |
| Penetration indicator | `{color}`, `{message}`, `{countedArmor:d}`, `{piercingPower:d}`, `{piercingReserve:d}`, `{caliber:d}`, `{noDamage}`, `{ricochet}` |
| Sixth Sense | `%(pos)s` map square |

The reticle texts use Python format fields: `:d` drops decimals and `:.1f` keeps one. An unknown name displays `macros not found`. Templates written before 2026-11-01 with `%(name)s` are still read; a template is treated as the old form when it contains `%(`.

### Target information

`{{i18n:KEY}}` reads a module translation; `{{i18n:KEY:arg1:arg2}}` fills `{}` placeholders in it.

| Group | Macros |
| --- | --- |
| Vehicle | `vehicle_name`, `vehicle_system_name`, `icon_system_name`, `vehicle_type`, `nation`, `level`, `rlevel`, `nick_name`, `marks_on_gun`, `vehicle_max_health`, `vehicle_weight`, `max_ammo` |
| Armour | `armor_hull_front`, `armor_hull_side`, `armor_hull_back`, `armor_turret_front`, `armor_turret_side`, `armor_turret_back` |
| Gun | `gun_name`, `gun_reload`, `gun_reload_with_crew`, `gun_reload_equip`, `gun_dpm`, `gun_dpm_equip`, `gun_clip`, `gun_clip_reload`, `gun_burst`, `gun_burst_reload`, `gun_aiming_time`, `gun_accuracy`, `angle_pitch_up`, `angle_pitch_down`, `angle_pitch_left`, `angle_pitch_right` |
| Shells (1–3) | `shell_name_N`, `shell_type_N`, `shell_damage_N`, `shell_power_N` |
| Mobility | `speed_forward`, `speed_backward`, `engine_name`, `engine_power`, `engine_power_density`, `chassis_max_weight`, `chassis_rotation_speed`, `hull_speed_turn`, `turret_name`, `turret_speed_turn` |
| Vision and camouflage | `vision_radius`, `radio_name`, `radio_radius`, `invis_stand`, `invis_stand_shot`, `invis_move`, `invis_move_shot` |
| Artillery stun | `stun_radius`, `stun_duration_min`, `stun_duration_max` |
| Player's own vehicle | `pl_vehicle_weight`, `pl_vision_radius`, `pl_gun_reload`, `pl_gun_reload_equip`, `pl_gun_dpm`, `pl_gun_dpm_equip`, `pl_gun_aiming_time` |

## Minimap

Vehicle labels (normal, alternative, ally/enemy/squad, lost and dead variants): `{{vehicle}}`, `{{name}}`, `{{level}}`, `{{type}}`, `{{state}}`, `{{hp}}`, `{{maxHp}}`, `{{hpPercent}}`, `{{lostSeconds}}`. Each accepts a length limit such as `{{name%.16s}}`. The map-size caption uses `{{width}}` and `{{height}}`; the cell-size caption uses `{{cellsize}}`.

## Clocks

| Clock | Format |
| --- | --- |
| Hangar clock (General settings) | `%H`, `%I`, `%M`, `%S`, `%d`, `%m`, `%Y`, `%y`, `%A`, `%a`, `%B`, `%b`, `%p`, `%%`. Adding `u` or `l` to a name forces upper/lower case: `%Au`, `%bl`. |
| Battle clock (battle options) | Python `strftime` directives such as `%H:%M:%S`. |
| Loading-screen clock (team panels) | Letters `H`, `i`, `s` (hour, minute, second); `\` escapes the next character. Default `H:i:s`. |

## Known gaps

These were found while compiling this reference; none was changed.

- **Team panels:** `wnx` is passed to the templates but has no `{{c:wnx}}`/`{{a:wnx}}`, and the settings validator reports `{{wnx}}` as unknown. `tdb`, `tfb`, `tsb`, `xwgr` and `xwr` are accepted by the validator (and `tdb`/`tfb`/`tsb` get colour slots) but no code fills them, so they are always empty.
- **`{{kb}}`:** the panels and markers use battles ÷ 1000 as a number, so the 0.1.5-beta.2 fix ("below 1000 show the battle count") only changes the internal statistics value and not what `{{kb}}` displays.
- **Validator coverage:** `mark_of_mastery`, `spg_battles`, `spg_percent` and the underscore spellings `t_battles`/`t_winrate` reach the templates but are not in the validator's list, so the panel reports them as unknown.
