# Halloween mode (player panel, TAB and loading)

Moved from `docs/PLANO_HALLOWEEN.md`, translated and condensed on 2026-10-30; the full option analysis remains in the Git history.

Integrated in `develop` and stable 0.1.4 (originally `feature/halloween-mode-adapters`). All in-game checks were accepted on 2026-10-30 (NA `2.4.1.1 #987`); see [In-game acceptance](#in-game-acceptance).

## Scope

- Halloween mode: `ARENA_BONUS_TYPE` `HALLOWEEN=101`, `HALLOWEEN_MEDIUM=102`, `HALLOWEEN_HARD=103`, injected by the `halloween` extension (`halloween_common/halloween_constants.py`, `ConstInjector`).
- `core/battle_capabilities.py` returns the `halloween` mode (formerly `special`). Halloween is still an event mode for `is_special()` and `is_event_mode()`.
- `core/mode_adapters.py` declares what each mode supports. Only `random` (previous behaviour) and `halloween` exist; modes without an adapter keep their native views intact.
- In Halloween the mod roster contains allies only, sorted like the native `HWSortKey` (team, alive first, class, vehicle name, player name). Mode entities (bots, bosses, `accountDBID` 0) are rows without statistics. The short/medium/large profiles of the classic panel are not used.
- The Halloween panel and loading screen are **not drawn** (adapter with `panel=False`, `loading=False`).
- The Halloween TAB only colours the allies' native names by the configured rating (`tab='halloween'`, `event_numbers=True`). The former extra table in the upper-left corner was removed.

## Reference version

- Client in the logs: NA `2.4.1.1 #987`.
- Local reference `WoT_Tools/wot-src-EU/sources/version.xml`: EU `v.2.4.1.1 #989` (branch `v2.4.1`). The builds differ (`#987` vs `#989`); nothing below was confirmed against the NA client sources.
- The reference `sources-as3` folder does not include the AS3 for `HWPlayersPanel` or any other Halloween Flash component.

## Native structure (EU #989)

| Screen | Class | Technology | Notes |
| --- | --- | --- | --- |
| Panel | `halloween.gui.scaleform.daapi.view.battle.players_panel.HWPlayersPanel` (alias `hwPlayersPanel`) | Scaleform | Inherits from `HWPlayersPanelMeta`, which inherits from the classic `PlayersPanel`, so the mod's `PlayersPanel` hooks (`as_setPanelModeS`, `setInitialMode`, `tryToSetPanelModeByMouse`, `updateVehicleHealth`) also fire in Halloween. Allies with `accountDBID > 0` only; uses `as_setPlayerPanelInfoS`, `as_setPlayerPanelHpS`, `as_setPlayerDeadS`, `as_setPostmortemS`. |
| Statistics exchange | `halloween...stats_exchange.HWStatisticsDataController` | Scaleform | Sorts with `HWSortKey` and empties the enemy side (`HWEnemySortedIDsComposer.addSortIDs` does nothing). |
| TAB | `halloween.gui.impl.battle.full_stats.TabScreen` in `FullEventStatsWindow` | Gameface | Layout `R.views.halloween.mono.battle.tab_screen`, `FullStatsViewModel` (title, task, difficulty, anomalies). Player rows live in the `TeamStats` child (`R.aliases.halloween.shared.TeamStats`, `EventStatsViewModel.team`). `WINDOW_FULLSCREEN`, modal, `OVERLAY` layer, opened by `page.py` through `__showBattlePageGFComponent`. |
| Loading | `halloween...halloween_battle_loading.HalloweenBattleLoadingWindow` | Gameface | Progress only (`EventLoadingViewModel.currentProgress`); no player list. |

## Panel

The mod's Flash (`ratingscreens.as` / `viewbindings.as`) binds to any object with `listLeft` and `listRight`. Because `HWPlayersPanel` inherits from the classic panel, it was found and the mod drew over the native names; the `medium2` and `large` modes in the logs came from the classic panel hooks.

Without the `HWPlayersPanel` AS3 there is no safe way to align the rows, so the `halloween` adapter has `panel=False`: the Flash payload is sent with `enabled=False`, the mod's Flash restores the native state and the mode hooks only pass the call to the original. The roster (allies only, sorted, no statistics for `accountDBID` 0) is already computed and tested; enabling the panel first requires validating the alignment in game.

## TAB

- `GamefaceLoading` attaches the `DriftkingsRatingPlayers` child to the classic `TabView` only when the adapter has `tab='classic'`, and to the Halloween `TabScreen` only when it has `tab='halloween'`.
- The mod never imports the extension. The `TabScreen` hook is installed only after Halloween's `page.py` has loaded `halloween.gui.impl.battle.full_stats` (`GamefaceLoading.watch`, called every tick). Late hooks keep the component owner captured at start-up; a test with the real registry checks activation, visibility, finalization and deactivation. If the TAB opens before that first tick, that window stays without colours until it is recreated.
- The `hwTab` payload has one row per ally (`summary`): name, clan, vehicle, alive, own, configured rating, win rate and battles, with the scale colours. It respects the TAB switch in the settings and does not read the native model (`TabScreen` has no `playerList`).
- `panel_gameface/halloween_tab.js` colours only the native names by exact, unique match (`PlayerInfo_base__tabWindow_` / `PlayerInfo_userName_`, checked in the NA 2.4.1.1 bundle). It uses `style.color` and restores the original value when no longer needed. It reuses the existing timer to follow row recreation without rewriting unchanged colours. It creates no elements and does not change names, damage, kills or anomalies.
- No new settings, headers or translatable text were added.
- Tests: `tests/runtime/battle/test_halloween_tab.py` (hooks and payload) and `tests/frontend/battle/test_halloween_tab.js` (no extra panel, name matching, colour changes, row recreation and restoration of native styles).

### Options considered

- **A — layer over `TabScreen`:** position the mod's fields over the `TeamStats` rows. Rejected for now: the layout and `TeamStats` DOM are not in the local reference, `TeamStats` has its own `team` model instead of `playerList`, `supports_gameface_overlay` would need widening for an extension module, and a JavaScript error would affect the whole modal TAB.
- **B — separate panel:** a mod view shown while the TAB is open. Hosted as a child of `TabScreen`, so it opens and closes with the TAB in the same layer, without its own focus and without touching the native DOM. This was implemented and later reduced to colouring the native names.

Option A is only worth revisiting after inspecting the `TabScreen` structure and CSS classes in the NA client.

## Gameface CSS compatibility

The NA log of 28 October 2026 showed `TypeError: style.getPropertyPriority is not a function`, which stopped the table from being created. The code now uses `style.color`, and the priority API is only queried when it exists. The JavaScript regression covers a style object without `getPropertyPriority`, `getPropertyValue`, `setProperty` or `removeProperty`.

## In-game acceptance

2026-10-30, NA `2.4.1.1 #987`. The maintainer confirmed every check below in game; the log of the development build from `a7eda3a` (0.1.5-beta.1) records a complete Halloween battle with no Driftkings warnings, errors or tracebacks. EU and ASIA clients of the same version are reported to behave the same, without a separately recorded test.

- The native Halloween TAB names receive the configured rating colours; no extra panel appears, names without statistics stay intact, event data (damage, kills, anomalies) is unchanged, and original colours return when the TAB closes or is disabled.
- The native Halloween panel shows no mod text on top and no mode changes (`medium2`/`large`).
- The log shows `mode=halloween`, `Team panels: mode=halloween supported=tab`, `Gameface roster watching halloween.gui.impl.battle.full_stats.TabScreen` and, when the TAB opens, `Gameface roster attached: tab (halloween)`. Statistics-dependent features (marks of excellence, battle statistics, High Caliber) stay disabled with `requires_statistics_battle`, and markers keep the native `HalloweenMarkersManager` presentation.
- The Halloween loading screen matches the native one.
- Random battles are unchanged (panel, loading and TAB).
- Other modes (comp7, frontline, training, events) keep their native views without the mod roster.

The two `minWidth` warnings logged by `coui://halloween/.../lib.js` on the battle results screen come from the native event UI, not from the mod.
