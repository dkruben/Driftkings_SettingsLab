# Runtime context — phases 6 and 7

These layers query loaded runtime objects. They do not start services, subscribe to
signals, schedule callbacks, hook components, apply settings or persist anything.

## CompatibilityManager

`Driftkings.core.mod_compatibility` exports a singleton and the read-only methods
`is_installed`, `status`, `has_possible_conflict`, `has_confirmed_conflict`, and
`warnings_for`. A manager can receive a module mapping for isolated tests.

Concrete signals checked against the read-only WoT_Tools references:

| Integration | Observed signal |
| --- | --- |
| XVM | Loaded `xvm_main`, `xvm_battle`, or `xvm_battle_minimap` modules |
| Battle Observer | Loaded `gui.mods.mod_armagomen_battle_observer` or `armagomen.battle_observer` |
| ModsListAPI | Loaded `gui.modsListApi` and non-null `g_modsListApi` |
| OpenWG Gameface | Loaded `openwg_gameface` with callable `gf_mod_inject` and `res_id_by_key` |

No external integration is imported to detect it. No file name, folder, old config
string or package found on disk is treated as a loaded installation. ABSENT means
not observed in this runtime, rather than a complete disk inventory. UNKNOWN covers
unrecognized names, failed/partial module entries, and incomplete API modules.

`status(name)` reports integration presence: ABSENT/PRESENT/UNKNOWN.
`conflict_status(feature, integration)` additionally reports POSSIBLE_CONFLICT or
CONFIRMED_CONFLICT. Presence is not confirmation of overlapping functionality.
XVM confirmation requires `owg_module_loaded() is True` and a loaded config getter
returning true for `playersPanel.enabled` or `minimap.enabled`. Known false suppresses
the warning for that feature; missing/raising/unknown evidence remains possible.
CONFIRMED_CONFLICT means confirmed active overlapping functionality, not proof of a
runtime error or incompatibility. The UI consistently describes potential interference.

Initial feature mappings are PlayerPanelPro, MinimapPlugins and MarksOnGunBattle.
Battle Observer and MarksOnGun mappings remain possible warnings: this version does
not infer active per-feature instances. ModsListAPI/OpenWG are not feature conflicts.
All warning payloads are fresh dictionaries, never references to external config.

Presenter state adds `compatibilityWarnings: {mod_id: [warning, ...]}`. Legacy IDs map
through the existing `restart_key`, including nested settings pages. Each warning has
`code`, `level`, `text`, `integration`, `component`, and `status`. The header patches
plain text with English/Portuguese localization. No schema revision is necessary for
these runtime observations; they are refreshed on existing state publications. There
is no timer or new lifecycle subscription. Dependency status is unchanged.

## BattleCapabilities

`Driftkings.core.battle_capabilities` exports its read-only singleton methods:
`current_mode`, `is_random`, `is_comp7`, `is_frontline`, `is_replay`, `is_event`,
`is_white_tiger`, `is_special`, `is_spg`, `is_in_battle`, `supports_gameface_overlay`.
Tests can supply callable player/session providers and a module mapping.

Existing contracts reused:

- `BigWorld.player()` and player arena presence;
- `Account.PlayerAccount` for positively identifying hangar instead of assuming that
  every partially loaded avatar without an arena is in the hangar;
- `IBattleSessionProvider.arenaVisitor` and its bonus type / GUI visitor;
- GUI visitor `isRandomBattle`, `isEventBattle`, `isEpicBattle`;
- current `ARENA_BONUS_TYPE` enums/ranges, including Comp7 variants and Frontline;
- `BattleReplay.isPlaying/isLoading`, matching the existing common replay helper
  without importing that broad utility module and its additional dependencies;
- `getArenaDP().getVehicleInfo().isSPG()`, the same query as BattleMeta.

Replay is orthogonal to the underlying mode. `special` describes a recognized bonus
outside the explicitly named modes. Missing player, destroyed objects, missing APIs,
unknown bonus, missing arena and incomplete context return `unknown`/False. A valid
PlayerAccount gives `hangar`. All game-object attribute access and method calls are
exception guarded; no game module is needed to import these layers.

White Tiger is deliberately not equated with EVENT_BATTLES. The inspected EU visitor
has no dedicated White Tiger method/enum. If a runtime extension supplies
`gui.isWhiteTigerBattle()` or `ARENA_BONUS_TYPE.WHITE_TIGER`, those explicit signals are
recognized. Otherwise this query returns False; the battle may still be classified as
event. No extension is imported or initialized to discover it.

`supports_gameface_overlay(view=None, resource_key=None)` is a conservative query for
a specific supplied view/resource, not a promise of universal overlay support. True
requires a recognized current battle context, an actual Wulf View with LOADED status
and live proxy, a client `gui.impl.battle.*` class in its inheritance chain, callable
OpenWG injection, and a positive resolved resource ID matching that view's layoutID.
Missing evidence, a lobby/custom unrecognized view, disposed/loading view, absent
resource, or missing API returns False. It does not create, attach, or modify a view.

Contexts and BattleViews continue to own lifecycle/registration. The new queries have
no callers in battle components yet. No supportedModes metadata is needed in this phase.
Logs occur only when an observed presence/conflict/mode changes, never per unchanged query.

## Reference and scope

Target reference: EU sources/version.xml v2.4.0.2 #966; .version_name 2.4.0.5473.
The different markers were retained. Existing extraction audit established client and
common source roots. Relevant arena visitor, constants, Wulf View/ViewStatus, XVM
module initialization/config reader, Battle Observer entry/Core and ModsListAPI import
were inspected directly. An absent extension-specific API is not evidence that the
mode can never exist in a later runtime.

Files added: core/mod_compatibility.py, core/battle_capabilities.py,
build_tools/tests/test_runtime_context.py, and this document.
Files extended: settings/panel/presenter.py, locales/en.py and pt.py,
DKModSettings/js/app.js, css/main.css, and the integrated settings JS test.
Previously approved phases 2–5 changes remain in the workspace.
MarksOnGun/calculator, layouts, EditSession, SettingsService, persistence, picker,
component hooks and build/deployment scripts were not changed in phases 6–7.

Tests cover absent/present/unknown integrations, failing read/import evidence,
presence versus confirmation, possible/confirmed warnings, disabled XVM features,
read-only Presenter warnings, warning header patches, all requested battle contexts,
partial/shutdown objects, conservative overlay checks and log suppression.


Validation on 2026-10-08: 21 new runtime-context tests passed; full suite 509 tests,
506 passing, with the same two distributed-default mismatches and BOM-related test
error from the initial review. Integrated Gameface settings tests, Python 2.7 existing
smoke plus direct imports/queries of both new layers, and all nine Python/Flash
contracts passed. `git diff --check` passed. No final build or deployment ran.
