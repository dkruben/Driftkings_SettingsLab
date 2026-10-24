# Driftkings

Modpack for Wargaming World of Tanks: battle overlays, hangar improvements and an integrated settings panel.

## Downloads

[Windows installer](https://github.com/dkruben/Driftkings_SettingsLab/releases/download/v0.1.2/Driftkings-0.1.2-WoT-2.4.1.0-Setup.exe) · **[Download the stable release](https://github.com/dkruben/Driftkings_SettingsLab/releases/tag/v0.1.2)** · [All releases](https://github.com/dkruben/Driftkings_SettingsLab/releases)

Current version: **0.1.2**, for **WoT 2.4.1.0**. Stable release.

## Included mods and functions

The names below match the settings labels. The module column identifies the corresponding Python file, without the `.py` extension. Components can be enabled or configured individually; availability depends on the vehicle, battle mode and selected options.

### Battle interface and statistics

| Mod | Module | Function |
| --- | --- | --- |
| Team panels and battle loading | `team_panels` | Customizes player panels, the team statistics screen and battle-loading information, including player ratings. |
| Battle performance | `battle_performance` | Calculates battle efficiency ratings such as WN8, EFF and XTE. Adds configurable macro text to the native results information line, with automatic UI sizing, spacing and vertical separators. |
| Battle statistics | `battle_statistics` | Compares team statistics and displays an estimated team-strength comparison. Estimates are not a guarantee of the battle outcome. |
| Marks of Excellence in battle | `battle_marks_of_excellence` | Displays estimated gun-mark progress and combined damage during battle in a movable Gameface panel. |
| High Caliber progress | `high_caliber_progress` | Tracks damage, the current High Caliber target, remaining damage and eligibility in a Gameface panel. Reaching the displayed target does not guarantee the server award. |
| Vehicle health | `vehicle_health` | Displays the player's vehicle health with configurable text and positioning. |
| Target information | `target_information` | Shows configurable information about the targeted vehicle. |
| Target distance | `target_distance` | Displays the distance to the current target. |
| Minimap enhancements | `minimap_enhancements` | Customizes minimap labels, circles, lines and vehicle information. |
| Spotted and assist notifications | `enemy_spotting_status` | Displays notifications for detected vehicles and spotting, tracking or stun assistance, with configurable text, colors and sound. |
| Sixth Sense alert | `sixth_sense_alert` | Customizes the Sixth Sense alert, including its icon, sound and timing. |
| Battle damage log | `game_log_manager` | Filters native damage-log event types and optionally swaps the top and bottom log positions. |
| Battle preferences | `battle_preferences` | Groups battle presentation and convenience options, including the clock, hints, notifications and other native interface controls. |

### Camera, aiming and controls

| Mod | Module | Function |
| --- | --- | --- |
| Third-person camera zoom | `third_person_zoom` | Adjusts third-person zoom steps, limits and camera behavior. |
| Sniper camera | `sniper_camera` | Customizes sniper-camera zoom and related camera options. |
| Gun traverse limits | `gun_traverse_limits` | Displays the gun's aiming-angle limits. |
| Aiming reticles | `aiming_reticles` | Customizes aiming-circle size and client/server reticle presentation. |
| Aiming countdown | `aiming_countdown` | Displays the estimated remaining aiming time. |
| Shell flight time | `shell_flight_time` | Displays the estimated shell travel time to the aiming point. |
| Armour penetration indicator | `penetration_indicator` | Displays armour and penetration information for the aimed surface. |
| Artillery blast radius | `artillery_blast_radius` | Visualizes the shell blast radius for supported artillery aiming modes. |
| Server turret synchronization | `server_turret_sync` | Synchronizes turret presentation with server aiming data. |
| Autoaim target indicator | `autoaim_target_indicator` | Highlights the native autoaim target with a configurable indicator color. |
| Repair controls | `repair_controls` | Provides configurable shortcuts and priorities for repairs, crew treatment and fire extinguishing using available consumables. |

### Hangar and utilities

| Mod | Module | Function |
| --- | --- | --- |
| Vehicle carousel | `vehicle_carousel` | Customizes carousel layout, filters and vehicle statistics. |
| Marks of Excellence in the hangar | `hangar_marks_of_excellence` | Shows gun-mark information and progress for the selected vehicle in a Gameface panel. |
| Marks of Excellence in the tech tree | `tech_tree_marks_of_excellence` | Adds gun-mark information to supported tech-tree vehicle displays. |
| Crew management | `crew_management` | Supports automatic crew return and adds crew details, progression, remaining XP and estimated battles in supported crew screens and tooltips. |
| Service record ratings | `profile_ratings` | Colors native overview, statistics and vehicle profiles; shows player/vehicle WN8, with independent switches, palettes and editable survival/received-damage limits. |
| Hangar preferences | `hangar_preferences` | Configures the hangar clock, header buttons, widgets, notifications and other garage convenience options. |
| AccountManager | `account_manager` | Provides the account-management interface, controlled through Hangar preferences. |
| Clan reward collection | `clan_reward_collection` | Collects eligible clan rewards automatically when the option is enabled. |
| Sound bank loader | `sound_bank_loader` | Loads the mod's custom sound banks. |

The integrated settings window (`settings_window`) provides controls, profiles, themes and update settings, including stable/beta channels. Gameface folders and native resource files use the corresponding presentation-module names under `mod/res/gui/gameface/mods/driftkings/` and `mod/res/gui/gen_resources/`.

The archived `hangar_efficiency` panel is inactive and is not compiled or included in the modpack.

## Installation

For guided setup, download `Driftkings-0.1.2-WoT-2.4.1.0-Setup.exe` from the stable release. Select a supported Wargaming game installation; the installer verifies its root, realm and game version.

1. Close World of Tanks.
2. Download `Driftkings-0.1.2-WoT-2.4.1.0.zip` from the release assets.
3. Extract its `mods` folder into the game installation, merging folders. It includes Driftkings and the required ModsListAPI and OpenWG Gameface packages under `mods/2.4.1.0/`.
4. For a new installation, extract the separate `Driftkings-defaults.zip` into the game installation. Preserve existing `mods/configs/driftkings` settings when updating.
5. Start the game and open Driftkings settings through the mods list.

The defaults are the author's selected mod configurations. Existing personal JSON files take precedence. The in-game updater preserves those configurations; missing settings use packaged defaults.

An optional Windows installer is built from the same compiler output. Its 29 component choices change JSON configuration only, never the installed WOTMOD/dependency set. Existing profiles are preserved on reinstall. Explicit `/RESETCONFIG=1` backs up configurations before resetting them. Branding and component previews are optional and can be added later.

The installer creates user-media folders `mods/configs/driftkings/sixthsense/` (default custom icon: `SixthSenseIcon.png`) and `mods/configs/driftkings/images/`, with short READMEs. Uninstall preserves these folders and their contents. Images accept packaged `gui/maps/driftkings/...` resources or custom files in `mods/configs/driftkings/...`; select the paths in the mod settings. These user files are not optional installer payloads.

## Compatibility

Designed for Wargaming World of Tanks **EU, NA and ASIA** clients, for **WoT 2.4.1.0**. All included features have been tested in-game and confirmed working across these regions, including live battles, replays, Gameface panel dragging and the in-game updater. Mir Tankov/RU is outside scope.

Version 0.1.2 is the stable release, with in-game validation completed for the panels and automatic-update installation.

## Anonymous statistics (optional)

Driftkings can send anonymous usage statistics to Google Analytics. It is **off by default** and is enabled in **Settings → Anonymous statistics**. When on, it sends a random installation ID, the mod and game versions, the realm, a heartbeat while the game is open and the type and source location (file, line, function) of errors logged by the mod. It never sends player names, accounts, error messages or file paths. Turning the switch off stops all sending and deletes the installation ID (`mods/configs/driftkings/analytics_id`). Replays are not counted. Builds without a configured Measurement ID and API secret in `core/analytics.py` do not send anything, even with the switch on.

## Languages

Settings translations: Czech, German, English, Spanish, French, Hungarian, Italian, Japanese, Korean, Polish, Portuguese, Russian, Thai, Turkish, Ukrainian, Vietnamese, Simplified Chinese and Traditional Chinese. Translation corrections are welcome. Bundled translations are editable UTF-8 `.yml` files in `mod/res/mods/driftkings/text/`; see [contributing.md](contributing.md#translation-resources) for the format and JSON override paths.

## Build from source

This repository contains the compiler, runtime sources, defaults and required resource inputs. Generated packages, Python bytecode, caches and local tests are excluded from Git. Download compiled packages from Releases.

On Windows, configure Python 3.10+, Python 2.7, Java/Flex, playerglobal and game SWCs, the .NET C# compiler. Game and reference directories are external read-only inputs.

```powershell
python build_tools/compiler.py --plan
python build_tools/validate_build_data.py
.\debug.cmd
.\release.cmd
```

Set `version` and `channel` in `build_data/release.json`, for example `"version": "0.1.3-beta.1", "channel": "beta"` or `"version": "0.1.2", "channel": "stable"`. The compiler validates their agreement and synchronizes `VERSION` in the original Python source after prerequisite validation. The installer takes its version from the completed build. An explicit `--version` also updates the JSON and Python source; `--channel` validates the selected version. `--plan` never writes files. For temporary older-version updater tests, use `--version ... --keep-source-version` to leave both originals unchanged. A version change modifies the Git checkout: commit it and rebuild before signing and publishing, so the release records a clean source revision. Version numbers are never incremented automatically.

Check portable logic with `python -m unittest discover -s tests/settings_panel -p 'test_*.py'` and `python -m unittest discover -s tests/core -p 'test_*.py'`; both suites also run on Python 2.7. Run `node tests/settings_panel/test_gameface.js` for the Gameface state tests. Install development dependencies with `npm ci --ignore-scripts`, then run `npm run lint` to enforce ES5 syntax and basic JavaScript checks. These tools run on Node 20.19+; client scripts remain ES5.

Edit defaults in `res/configs/driftkings/default/`, then run `python build_tools/generate_defaults.py --write` to regenerate the Python fallback. For intentional changes to the default values, also refresh the recorded snapshot with `python build_tools/generate_defaults.py --write --refresh-snapshot`. Use `python build_tools/generate_defaults.py --check` to check synchronization without writing files; never edit `settings/default_values.py` by hand.

The current build contract uses the (EU, NA) installation as its resource source and an EU source reference. Local tool paths belong in ignored `build_data/toolchain.local.json`. Builds compile Python 2.7 to standard bytecode without obfuscation, Flash and native helpers, generate the carousel integration and verify the packages. Outputs go to `build/`; compilation does not install or publish them.

To compile the Windows installer and include it in the release inventory and checksums:

```powershell
python build_tools/build_installer.py --artifacts build/releases/stable/0.1.2 --compile --attach-to-release
```

Sign `release.json` after preparing all release assets, then publish with `build_tools/publish_release.py`. The installer is uploaded with the other verified assets.

To update an existing published release, first edit and save its release notes on GitHub, commit the intended code and source version, then run:

```powershell
python build_tools/update_release.py --key release-signing.key --publish
```

This imports those notes into the signed changelog, rebuilds the mod and installer, verifies the assets and replaces the existing release files. It also moves the remote release tag to the compiled source commit. Omit `--publish` to build and sign locally without changing GitHub. Notes must fit the panel contract: 50 nonempty lines, 500 characters per line and 16 KiB total UTF-8. The private key stays local. Replacing files under the same version does not trigger an automatic update for clients already running that version; editing GitHub notes alone does not change the signed changelog.

| Directory | Contents |
| --- | --- |
| `mod/res` | Runtime Python, Gameface and packaged resource inputs |
| `flash_source` | ActionScript sources and compilation libraries |
| `installer/source` | Native helper sources |
| `build_data` | Build contracts, components, targets and release metadata |
| `build_tools` | Compiler, validators and release tooling |
| `res` | Canonical defaults, dependencies and resource sources |

## Image paths

Overlay images and custom Sixth Sense icons accept `gui/maps/driftkings/...` resources or user files in `mods/configs/driftkings/...`, including their fixed SWF-relative forms. `img://` prefixes remain supported. Move custom images from other folders into `mods/configs/driftkings/` and update their configuration paths. External URLs, absolute paths and directory traversal are rejected; overlays use their configured alternative image, and Sixth Sense uses its embedded fallback icon when loading fails.

## Support and credits

[Join the Driftkings Discord community](https://discord.gg/GJcy4x7SP).

[Report an issue](https://github.com/dkruben/Driftkings_SettingsLab/issues) with the mod version, game version/realm, reproduction steps and relevant `game.log` excerpts. Remove personal information before sharing logs.

Dependencies: ModsListAPI by poliroid and OpenWG Gameface.
