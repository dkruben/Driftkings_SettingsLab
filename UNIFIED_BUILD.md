# Unified Driftkings laboratory

All changes and outputs are local to Driftkings_SettingsLab. The original project
and the game installation are not modified by the commands below.

## Package and structure

`build/unified/Driftkings.wotmod` contains 33 components and has one automatic
entry point: `gui/mods/mod_Driftkings.pyc`. Internal components live in
`Driftkings/battle`, `Driftkings/lobby` and `Driftkings/components`, without the
`mod_` prefix. Definitions in `build_data/components` generate `Driftkings/component_list.py`.
The sole release version is `VERSION` in `Driftkings/__init__.py`; the builder
and all component configuration instances use it. Individual package manifests,
release ZIP tooling and automatic per-component version hooks have been retired.
ColorMessages, CreditCalc, ServerReticle, SystemColor, TotalLog and
VehicleExperience remain excluded because their sources were removed.

Core imports declarations, registers views, starts services and initializes
components. It owns keyboard dispatch, managed callbacks, component hooks,
application contexts and settings. Hooks become active when their component
starts. Deactivated wrappers forward the original implementation so wrappers
installed by other mods are preserved. Shutdown runs component cleanup and then
services in reverse order. A component that fails during initialization has its
hooks disabled and its cleanup invoked immediately, once. Cleanup failures are
logged without blocking the remaining components. The startup log reports the
number actually initialized. Runtime hot reload is intentionally not supported.

Login/lobby transitions are delivered through `onContextEntered` and
`onContextLeft`. The battle event hub supplies shared battle lifecycle and
vehicle events. Feature-specific game hooks remain where they implement actual
behavior; they are declared through the Core hook manager. Existing direct
BigWorld timers and backend-specific resources retain their component cleanup.
The managed callback service additionally cancels its battle callbacks on exit.

See [SOURCE_LAYOUT.md](docs/SOURCE_LAYOUT.md) for configuration and presentation ownership.

## Interface

`DriftkingsBattle.swf` contains seven battle components: OwnHealth, FlightTimer,
DispersionTimer, ArmorCalculator, Minimap, SixthSense and the PlayerPanelPro API.
Core registers and loads the shared battle root. The old PlayersPanelAPI Python
module is a compatibility import forwarding to `Driftkings/views/battle/players_panel`.

Account windows and rating screens use the central window catalog. Settings
retain their own window, available through ModList and F10. Loading/TAB screens,
account windows and DistanceMarker keep the Flash entry points appropriate to
their UI contexts. Seven active AS3 projects are compiled. Old AS3 projects remain
as reference sources but are excluded from the active build and package.

Settings do not require ModSettingsAPI. Existing template definitions and i18n
remain supported. Battle overlays and Gameface now use the owned Driftkings UI bridge.
ModList remains the integration for opening the settings window. ModsListAPI
1.7.9 requires OpenWG Gameface 1.1.6; both packages in `res/wotmods/` must be
installed. Driftkings shares its global Gameface entry point and resource IDs,
while keeping its own feature loader, battle Flash and settings window. The
build rejects conflicting resources across these packages.

## Configuration

Python defaults live in `Driftkings/settings/settings_data.py`. The loader
reads `mods/configs/Driftkings/load.json` (`{"loadConfig": "default"}`), then one JSON
per component inside that profile. CarouselStats and PlayerPanelPro retain their
split JSON files in `carousel_stats/` and `player_panel_pro/` subdirectories.
The owned settings window edits the same files and offers profile selection and
cloning. Profile changes apply after restarting the game; edits to individual
options retain their existing update behavior.

The default profile imports previous settings once, preserving old documents.
Missing options use Python defaults; unknown custom keys are retained. Invalid
JSON or known option types are reported instead of overwritten. Atomic writes,
backups and interrupted-publication recovery remain supported. Translations,
accounts and statistics caches stay outside profiles. The wotmod creates missing
configuration files at runtime. All menus live in `settings/templates.py`;
`Driftkings/i18n/` holds one bundled catalog per language, with unified optional
JSON overrides in `mods/configs/Driftkings/i18n/`. See [configuration details](docs/CONFIGURATION.md).

## Build and verification

Run from this directory:

```
python -m unittest discover -s build_tools/tests
python build_tools/build_lab.py --flash
```

The builder uses SourceTree's embedded Python 2.7 (`--hg` overrides its location).
It first runs a real Python 2.7 hook smoke test, compiles Python and active Flash,
and creates the unified wotmod directly from enabled manifests and local assets.
It rejects missing resources, conflicting paths, old automatic mod entries and
bytecode from another Python version. No component archives are used as build
inputs and no files are deployed. Flash tool paths accept the DK_* environment
variables documented in `build_tools/build_flash.py`.

Outputs: `build/lab-compile.log`, `build/flash/results.json`,
`build/unified/components.json` and `build/unified/Driftkings.wotmod`.

Local verification covers persistence, input routing, view registration, panel
updates, lifecycle isolation, callbacks and packaging. The Python 2.7 smoke test
also covers partial handlers, static/class methods, properties and deactivation.
Compilation and mocked tests do not establish compatibility with a running WoT
client. In-game validation is still required: login, settings through ModList/F10,
lobby/battle transitions, loading/TAB, HP/spotted updates, respawns, results,
repeated battles and event battle modes. Review game.log during those checks.

See `docs/UI_BRIDGE.md` for the native Flash/Gameface integration and validation limits.

DispersionCircle is enabled again in its package manifest. The current package
contains 33 components; DispersionTimer remains included.
