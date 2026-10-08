# Driftkings Mods for World of Tanks

Battle tools, hangar improvements and interface customization for the **World of Tanks EU client**.

![WoT EU target](https://img.shields.io/badge/WoT_EU-2.4.0.1-bb3535)
![Client runtime](https://img.shields.io/badge/Python-2.7.18-3776AB)
![UI](https://img.shields.io/badge/UI-Scaleform_%2B_Gameface-6554C0)

[Installation](#installation) · [Mod catalog](#mod-catalog) · [Development](#development) · [Support](#support)

This repository contains the Python sources, ActionScript projects, Gameface assets, configurations and build tooling for the Driftkings mod collection. All active components are distributed in one Driftkings.wotmod package.

## Compatibility

| Component | Repository target |
| --- | --- |
| Game client | World of Tanks **EU 2.4.0.1** |
| Reference source dump | **2.4.0.5450** |
| Client scripts | Python **2.7.18** |
| Interface | Scaleform / ActionScript 3 and Gameface / HTML, CSS, JavaScript |
| Localization | **11 EU client languages** |

The version and local build paths are defined in [build_config.json](build_data/build_config.json). Build validation checks source syntax, resources and package contents; behavior inside the game must also be tested against the target client.

## Installation

Build with `release.cmd`. The only output package is
`build/unified/Driftkings.wotmod`. With the game closed, install it in
`mods/<game-version>/` alongside ModsListAPI 1.7.9 and its required OpenWG Gameface 1.1.6 dependency.
Keep your existing `mods/configs/Driftkings/` settings. Do not install previous
individual Driftkings packages alongside the unified package.

The build commands only produce local files; they never install into the game.

## Mod catalog

The package contains 33 internal components. Their resource definitions live in
[`build_data/components`](build_data/components); these are not separate releases.

| Component | Purpose |
| --- | --- |
| `AimingAngles` | Shows gun elevation and depression limits. |
| `ArcadeZoom` | Adds extra zoom control in arcade mode. |
| `ArmorCalculator` | Displays effective armor and penetration assistance. |
| `ArtySplash` | Shows HE splash and stun range. |
| `AutoAimOptimize` | Improves auto-aim against targets behind obstacles. |
| `BattleOptions` | Hides and tweaks multiple battle UI elements. |
| `BattleStat` | Adds extra battle statistics. |
| `DispersionCircle` | Replaces the standard aiming info circle with a dispersion circle. |
| `DispersionTimer` | Shows the real gun dispersion time. |
| `DistanceMarker` | Displays distance to enemy targets. |
| `FlightTimer` | Shows shell flight time. |
| `InfoPanel` | Clean battle vehicle panel with seven layouts, translucent background and base technical statistics. |
| `MainGun` | Displays Main Gun progress in battle. |
| `MarksOnGunBattle` | Shows Marks of Excellence progress in battle. |
| `MinimapPlugins` | Adds names, destroyed vehicles, and extra minimap tools. |
| `OwnHealth` | Displays the player's HP. |
| `PlayerPanelPro` | Player panel HP, detection status and ratings, with independent loading and TAB formats. |
| `RepairExtended` | Adds quick repair and crew healing helpers. |
| `SafeShot` | Blocks shots that would damage allies. |
| `ServerTurretExtended` | Adds server turret sync, wheel auto-speed, and stop-to-fire behavior. |
| `SixthSense` | Adds a custom Sixth Sense icon, sounds, and battle message. |
| `SpottedExtendedLight` | Shows detection and spotting-damage messages above the minimap. |
| `ZoomExtended` | Adds configurable extended zoom. |
| `AccountManager` | Quick account switching for login management. |
| `BanksLoader` | Loads and manages custom sound-bank resources. |
| `BattleEfficiency` | Displays battle efficiency during and after a match. |
| `LogsSwapper` | Reorders the damage log for XVM-style layouts. |
| `AutoClaimClan` | Automatically claims clan-related rewards. |
| `CarouselStats` | Configurable Gameface carousel statistics, macros, icons and Core rating colors. [Configuration guide](res/gui/gameface/mods/Driftkings/CarouselStats/README.md). |
| `CrewSettings` | Adds crew return and related crew helpers. |
| `HangarOptions` | Hangar tweaks, auto-login and a Gameface clock with five styles, position and size controls. |
| `MarksOnGunHangar` | Gameface hangar card with MoE objectives, observed progress, mastery icons, WN8 and win rate. Its calculations are included in the main Python module; no separate progress module or SWF is packaged. |
| `MarksOnGunTechTree` | Shows MoE percentages and mastery badges in the EU Gameface tech tree. |

The package version is declared once as `VERSION` in
[`Driftkings/__init__.py`](source/scripts/client/Driftkings/__init__.py).
The builder reads it for `meta.xml`; shared services and component settings use
that same value. There are no individual component release versions.

## Configuration and localization

Repository defaults live in [`res/configs/Driftkings`](res/configs/Driftkings):

```text
load.json                      # {"loadConfig": "default"}
default/                       # selected configuration profile
    own_health.json
    minimap_plugins/             # minimap.json, minimap_labels.json, minimap_circles.json, minimap_lines.json
    carousel_stats/             # 3 layout files, plus optional example presets
    player_panel_pro/           # 8 screen/panel files
i18n/<language>.json            # optional unified translation overrides (runtime)
```

Installed settings live in `mods/configs/Driftkings/`. Python creates missing
files and migrates existing settings into `default` on first use. To preserve
installed customizations, let the wotmod perform that migration before copying
example JSON files. Profiles can be selected or cloned in the owned settings
window; changing profile takes effect after restarting the game.
See [configuration details](docs/CONFIGURATION.md).

Python values are centralized in `settings/settings_data.py`, with all menus in
`settings/templates.py`. Bundled translations live in `Driftkings/i18n/`, one
Python catalog per language; old per-component catalogs are imported once into
the unified JSON overrides.

The client language list is recorded in [locales.json](build_data/locales.json):

| Code | Language | Code | Language |
| --- | --- | --- | --- |
| `cs` | Czech | `it` | Italian |
| `de` | German | `pl` | Polish |
| `en` | English | `ru` | Russian |
| `es` | Spanish | `tr` | Turkish |
| `fr` | French | `uk` | Ukrainian |
| `hu` | Hungarian | | |

All **44 catalog groups** include these languages. Catalog coverage also includes retained configurations for inactive modules. Translations still need native-speaker terminology review. Newly added MinimapPlugins keys use English fallback where translations are missing.

Configuration defaults live in `source/scripts/client/Driftkings/settings/`.
The obsolete synchronizer for standalone `gui/mods/mod_*.py` sources was removed.
Validate settings behavior and translations locally with:

```powershell
python -m unittest discover -s build_tools/tests
python build_tools/localize_configs.py --check
```

`localize_configs.py --translate` regenerates translated catalogs online. It sends UI text fragments to the translation service and caches intermediate results in `build/localization/`.

## Development

### Repository layout

| Path | Contents |
| --- | --- |
| [`source/scripts/client`](source/scripts/client) | Python client modules and shared libraries |
| [`flash_source`](flash_source/README.md) | One battle source tree, three active projects, shared utilities and client libraries |
| [`res/flash`](res/flash) | Published SWFs grouped by the same contexts |
| [`flash_source/shared/swc`](flash_source/shared/swc) | EU client SWC libraries and their hash manifest |
| [`res/gui/gameface/mods/Driftkings`](res/gui/gameface/mods/Driftkings) | Editable Gameface HTML, CSS and JavaScript |
| [`res/mods/configs/res_map`](res/mods/configs/res_map) | Gameface resource registration |
| [`res/configs/Driftkings`](res/configs/Driftkings) | Default settings and localization catalogs |
| [`res/wotmods`](res/wotmods) | Bundled third-party API dependencies |
| [`build_data`](build_data) | Build settings and package manifests |
| [`build_tools`](build_tools) | Compilation, packaging and validation tools |
| `build/` | Generated packages, compiler output and local reports |

### Build and validation

Run `debug.cmd` or `release.cmd`. Both commands validate the settings and translations,
compile Flash and Python, and produce **one local package** at
`build/unified/Driftkings.wotmod`. They never deploy into the game.

Requirements: Python 3 (`python` on PATH, or `DK_PYTHON3`), PowerShell, Java/Flex,
and SourceTree's embedded Python 2.7 host. To override that host, invoke
`python build_tools/build_lab.py --flash --hg <path-to-hg.exe>` directly.
The Flash compiler supports `DK_FLEX_HOME`, `DK_MXMLC_JAR`, `DK_PLAYERGLOBAL` and `DK_JAVA`.

The CI workflow checks unit tests, translations, JSON resources, Python 2.7 syntax
and Gameface JavaScript. Gameplay still requires testing in the client.
See [UNIFIED_BUILD.md](UNIFIED_BUILD.md) and [source layout](docs/SOURCE_LAYOUT.md).

Run `Verificar-Atualizacoes.cmd` to check the upstream versions of wot-src EU,
ModList and GameFace against the references in `WoT_Tools`, without installing
or replacing files. See [TOOL_UPDATES.md](TOOL_UPDATES.md) for terminal options.

### UI dependencies

`res/wotmods` contains ModsListAPI 1.7.9 and its required OpenWG Gameface 1.1.6
dependency. Install both with Driftkings for client 2.4.0.2. OpenWG owns the global
Gameface injection and shared resource IDs; Driftkings owns its script lifecycle,
battle Flash and settings window. Gambiter and ModsSettingsAPI are not required.
See [the UI bridge](docs/UI_BRIDGE.md).

## Support

For a bug report, include the game version, mod name, steps to reproduce and the relevant excerpt from **`game.log`**. A screenshot is useful for visual issues.

- [Open an issue](https://github.com/dkruben/Driftkings_Mods_Hide/issues)
- Email: [driftkingsmods@gmail.com](mailto:driftkingsmods@gmail.com)
- Support development: [Patreon](https://www.patreon.com/driftkings_mods/)

## License and credits

License documents: [English](LICENSE_EN.md) · [Português](LICENSE_PT.md).

Thanks to **Izebrg (Renat Iliev)**, **Poliroid (Andrii Andrushchyshyn)**, **PolyacovYury**, **Spoter (Peter Rastorguev)** and **CH4MPi (Alexander Kuznetsov)** for their original work and contributions.
