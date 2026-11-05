# Driftkings Modpack

A customizable World of Tanks modpack with advanced battle statistics, modern interface enhancements, aiming tools, vehicle markers and integrated settings.

[![Latest Stable: 0.1.6](https://img.shields.io/badge/Latest_Stable-0.1.6-blue)](https://github.com/dkruben/Driftkings_SettingsLab/releases/tag/v0.1.6)
[![World of Tanks: 2.4.1.1](https://img.shields.io/badge/World_of_Tanks-2.4.1.1-red)](https://worldoftanks.eu/)
[![Regions: EU / NA / ASIA](https://img.shields.io/badge/Regions-EU%20%2F%20NA%20%2F%20ASIA-blue)](#compatibility--languages)
[![Python 2.7](https://img.shields.io/badge/Python-2.7-orange)](https://www.python.org/downloads/release/python-2718/)
[![GitHub Release](https://img.shields.io/github/v/release/dkruben/Driftkings_SettingsLab?label=GitHub%20Release)](https://github.com/dkruben/Driftkings_SettingsLab/releases/latest)
[![Discord](https://img.shields.io/badge/Discord-Community-5865F2)](https://discord.gg/k2Stjv5fS5)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-green)](licence)

Built for the Wargaming **EU, NA and ASIA** clients. Enable the components you want and customize them through one settings panel, with profiles and previews for markers, the minimap, HUD and vehicle carousel.

[Downloads](#downloads) · [What's new](#whats-new-in-v016) · [Features](#features) · [Installation](#installation) · [Settings & updates](#settings-profiles--updates) · [Contributing](#development--contributions) · [Support](#support-credits--license)

## Downloads

**[v0.1.6 is the current stable release](https://github.com/dkruben/Driftkings_SettingsLab/releases/tag/v0.1.6)** for World of Tanks **2.4.1.1**.

| Download | Purpose |
| --- | --- |
| **[Windows installer](https://github.com/dkruben/Driftkings_SettingsLab/releases/download/v0.1.6/Driftkings-0.1.6-WoT-2.4.1.1-Setup.exe)** | Guided installation, component selection and required dependencies. |
| **[Manual installation ZIP](https://github.com/dkruben/Driftkings_SettingsLab/releases/download/v0.1.6/Driftkings-0.1.6-WoT-2.4.1.1.zip)** | Modpack and dependencies for manual installation. |
| [Default configurations](https://github.com/dkruben/Driftkings_SettingsLab/releases/download/v0.1.6/Driftkings-defaults.zip) | Initial settings for a new installation; preserve existing profiles when updating. |
| [SHA-256 checksums](https://github.com/dkruben/Driftkings_SettingsLab/releases/download/v0.1.6/SHA256SUMS.txt) | Verify downloaded files against the published checksums. |

[All releases and changelogs](https://github.com/dkruben/Driftkings_SettingsLab/releases) include previous stable versions and optional beta releases. Use assets from the same release when installing manually.

## Beta 0.1.7-beta.1

Beta preparation for the World of Tanks 2.4.1.1 micro-update: updated carousel and vehicle-marker build resources, refreshed Flash libraries, optimized images and custom minimap support restricted to Random Battles and 7x7/Onslaught. Other modes retain the native minimap. The project owner confirmed the local EU test build in game; NA and ASIA have not been revalidated in game for this beta. Stable downloads above remain at 0.1.6 until the beta is published and validated.

## What's New in v0.1.6

Version 0.1.6 brings the improvements of the approved 0.1.6-beta.1 into the stable channel, preserving personal profiles and settings.

- **Parallel player statistics:** vehicle-statistics requests run in parallel, and each account is delivered as it answers.
- **Progressive results:** delivered statistics are applied in small batches across frames, reducing work concentrated in a single frame.
- **Player-panel optimizations:** battle events and delivered statistics trigger updates; only changed rows are sent to Flash. The loading-screen clock runs inside Flash.
- **Native side-panel integration:** in standard battles, the panel follows the game's own row redraws. Other modes and panels replaced by another mod retain the fallback renderer.
- **Leaner combat overlays:** gun traverse limits, the autoaim indicator and target information send only changed values to Flash.

The source beta was functionally validated on **EU, NA and ASIA**, including real Random Battle and Frontline battles, replays, installation, updates and configuration persistence. These results are documented declarations by the project owner; the [approved validation record](docs/releases/0.1.6-beta.1-validation.md) distinguishes confirmed checks from features not individually tested.

Earlier measurements used **EU replays**, CapFrameX and the mod's diagnostics: the player-statistics batch stall fell from about 200 ms to about 11 ms, and side-panel processing in a random replay fell from about 5.4 ms to 0.6–1.4 ms per pass. These measurements describe those scenarios, rather than performance measured across all three regions. See the [measurement context and implementation history](docs/STATUS.md).

## Features

Components can be enabled and configured individually. Availability depends on the vehicle, battle mode and selected options.

### Battle & statistics

| Feature | What it does |
| --- | --- |
| Team panels and battle loading | Custom player panels, battle-loading information and team statistics, including player ratings. |
| Vehicle markers | Editable text, ratings, health bars, floating damage and icons, with team/state/ALT layouts and a tank preview. |
| Battle performance | WNX, WN8, EFF and XTE calculations, with configurable battle text and native results information. |
| Battle statistics | Team-statistics comparisons and estimated relative strength. |
| Marks of Excellence | Estimated gun-mark progress and combined damage in a movable battle panel. |
| High Caliber progress | Damage, target, remaining damage and eligibility in a movable panel. |
| Vehicle health | Configurable own-vehicle health display. |
| Target information and distance | Information about the targeted vehicle and its distance. |
| Minimap enhancements | Vehicle labels, last positions, HP, circles, direction lines and map-size captions. |
| Spotted and assist notifications | Configurable messages, colours and sounds for detection and spotting, tracking or stun assistance. |
| Sixth Sense | Custom icon, sound and alert timing. |
| Battle damage log | Event filters and optional swapping of the native top/bottom logs. |
| Battle preferences | Hints, notifications, fog and other native interface options. |

### Camera, aiming & controls

| Feature | What it does |
| --- | --- |
| Third-person and sniper cameras | Configurable zoom steps, limits and camera behaviour. |
| Gun traverse limits | Displays the gun's aiming-angle limits. |
| Aiming reticles | Reticle size and client/server aiming-circle presentation. |
| Aiming countdown | Estimated remaining aiming time. |
| Shell flight time | Estimated shell travel time to the aiming point. |
| Armour penetration indicator | Armour and penetration information for the aimed surface. |
| Artillery blast radius | Shell blast-radius display in supported artillery aiming modes. |
| Server turret synchronization | Turret presentation synchronized with server aiming data. |
| Autoaim target indicator | Configurable highlight for the native autoaim target. |
| Repair controls | Shortcuts and priorities for repairs, crew treatment and fire extinguishing. |

### Hangar & utilities

| Feature | What it does |
| --- | --- |
| Vehicle carousel | Card layouts, filters, sorting and vehicle statistics. |
| Hangar and tech-tree Marks of Excellence | Gun-mark information for the selected vehicle and supported tech-tree displays. |
| Crew management | Automatic crew return, progression, remaining XP and estimated battles in supported crew screens. |
| Service record ratings | Player/vehicle WN8 and configurable rating colours in native service-record screens. |
| Hangar preferences | Header buttons, widgets, notifications and garage options. |
| General settings and clock | Editable hangar clock fields with time/date text, background images, positioning and shadows. |
| Account manager | Account-management interface with its own General settings page: a switch for the login-screen button and **Manage accounts** in the hangar. |
| Clan reward collection | Automatic collection of eligible clan rewards when enabled. |
| Sound bank loader | Loads the mod's packaged sound banks. |

Ratings and progress displays are estimates; they do not guarantee a battle result, server award or gun-mark increase. Vehicle-marker customization applies to supported regular modes; special modes retain native markers. XMQP is not included.

Feature guides: [vehicle markers](docs/vehicle_markers/README.md) · [vehicle carousel](docs/vehicle_carousel/README.md) · [template macros](docs/macros/README.md) · [fonts](docs/fonts/README.md) · [custom Sixth Sense icons](docs/sixthsense_icons/README.md).

## Installation

### Windows installer

1. Close World of Tanks.
2. Download the installer for v0.1.6 and pick your language.
3. Read what's new, then select your game installation.
4. Choose **Recommended**, **Complete** or **Custom** and pick the components you want enabled; each one shows a preview.
5. Start the game and open **Driftkings settings** through the mods list.

The installer checks the game version and region, installs the required dependencies and keeps existing profiles when reinstalling. To choose the components again, select **Reset to defaults and choose the components again** on the folder page; your current settings are backed up first.

### Manual installation

1. Close World of Tanks and download the ZIP for v0.1.6.
2. Extract its `mods` folder into the game installation, merging folders.
3. For a new installation, download `Driftkings-defaults.zip` from the **same release** and extract it into the game installation.
4. Start the game and open Driftkings settings through the mods list.

**Upgrading from the old configuration layout:** back up your personal images and sounds, then remove the old `mods/configs/driftkings` folder before the first launch of version 0.1.3. Configure the mod again in the hangar. Older settings and caches are no longer imported automatically.

**Updating an existing installation:** keep personal settings under `mods/configs/driftkings/`. Extract the defaults archive for a new installation; do not overwrite current profiles with defaults during a normal update. The manual ZIP includes the required ModsListAPI and OpenWG Gameface packages.

To verify a downloaded file on Windows, compare `Get-FileHash -Algorithm SHA256 -LiteralPath '<downloaded-file>'` with its entry in the published `SHA256SUMS.txt`.

## Settings, profiles & updates

The integrated settings panel includes **profiles, themes, UI scale, translations and update channels**. Marker changes can be checked in the tank preview before applying them.

Default configurations are based on the author's EU profile, except vehicle markers, which now follow the reference layout. Personal JSON settings take precedence, and the updater preserves them. Settings remain under `mods/configs/driftkings/<profile>/`.

Use the **stable** update channel for stable releases. Select **Beta** only if you want prerelease updates. The updater authenticates the signed manifest, verifies the package size and SHA-256, and applies the update after restarting. See [release integrity and security](SECURITY.md).

For custom media, use `mods/configs/driftkings/images/` and `mods/configs/driftkings/sixthsense/`. The default custom Sixth Sense icon is `SixthSenseIcon.png`. Packaged `gui/maps/driftkings/...` image paths are also supported. Select the paths in settings; uninstall preserves your media folders.

### Ratings and palettes

Choose from **NoobMeter, Driftkings, WoT-Life and Tomato.gg** palettes. WNX includes assistance damage for your own battle, results and carousel vehicles; missing data displays `--`. Expected values refresh daily in the hangar and retain the last valid cache if a download fails.

The EU battle overlay defaults to **WN8, EFF and DIFF**. Add `{wnx}` and `{c:wnx}` to battle/results text, or `{{v.wnx}}` and `{{v.c:wnx}}` to carousel fields, to display WNX. Carousel sorting by WNX is also available.

### Optional anonymous statistics

Anonymous usage statistics are **off by default**. You can enable them in settings. When enabled, the mod sends a random installation ID, mod/game versions, region, activity heartbeats and error-location metadata to Google Analytics. It does not send player names, account details, error messages or full filesystem paths. Disabling the option stops sending and deletes the installation ID. Replays are not counted.

## Compatibility & languages

| Area | Support |
| --- | --- |
| Game | Wargaming World of Tanks **2.4.1.1** |
| Regions | **EU, NA and ASIA**; Mir Tankov/RU is outside the project's scope. |
| Client runtime | Python 2.7, ActionScript 3 / Scaleform and ES5 JavaScript / Gameface. |
| Dependencies | ModsListAPI by poliroid and OpenWG Gameface, included in the release distribution. |

**18 interface languages:** Czech, German, English, Spanish, French, Hungarian, Italian, Japanese, Korean, Polish, Portuguese, Russian, Thai, Turkish, Ukrainian, Vietnamese, Simplified Chinese and Traditional Chinese.

English is the fallback. Regional Spanish and Portuguese variants reuse the existing catalogs. See the [language guide](docs/i18n/README.md) for aliases and coverage. Translation corrections and native-speaker terminology reviews are welcome.

Special modes may retain native markers or omit Gameface HUD elements when the game's battle page does not provide that HUD. See the feature guides for limitations.

## Release history & changelog

- **[v0.1.6 — current stable](https://github.com/dkruben/Driftkings_SettingsLab/releases/tag/v0.1.6):** statistics, player-panel and overlay optimizations described above.
- **[v0.1.5](https://github.com/dkruben/Driftkings_SettingsLab/releases/tag/v0.1.5):** consolidated the four 0.1.5 betas, including the Classic target card, Gameface HUD, expanded team-panel support, account management and settings improvements.
- **[v0.1.4](https://github.com/dkruben/Driftkings_SettingsLab/releases/tag/v0.1.4):** account-manager fixes, self-contained fonts, minimap/player-panel corrections and shared configuration contracts.
- [Complete release history](https://github.com/dkruben/Driftkings_SettingsLab/releases) · [release and promotion process](docs/releases/README.md) · [project status and historical validation](docs/STATUS.md).

**Older custom profiles:** version 0.1.5 retired the `xvm`/`XVMSymbol` font aliases, `{{xvm-stat}}` and carousel `{{v.c_...}}` macros. Use `dkm`, `{{stat-available}}` and `{{v.c:...}}` instead. Aiming texts support `{name}` fields such as `{timer:.1f}`; older `%(name)s` templates remain supported. See the [macro reference](docs/macros/README.md).

## Development & contributions

Runtime code targets **Python 2.7**, **ActionScript 3** and **ES5 JavaScript**. Build and validation tools run on **Python 3**. The published stable source is on `main`; `develop` is the development branch. Stable preparation uses a release branch and a reviewed merge commit.

Start with [CONTRIBUTING.md](CONTRIBUTING.md) for environment setup, architecture, tests, translations and release instructions. The [documentation index](docs/STATUS.md#guias-mantidos) links to feature guides and technical references. Contributions can cover fixes, configuration examples, translations, documentation and reproducible bug reports.

Stable releases promoted through the current process are rebuilt and signed from an approved beta and carry `promotion.json` for traceability. Functional acceptance is recorded separately from automated CI and package checks.

## Support, credits & license

[Join Discord](https://discord.gg/k2Stjv5fS5) · [Report an issue](https://github.com/dkruben/Driftkings_SettingsLab/issues) · [Browse releases](https://github.com/dkruben/Driftkings_SettingsLab/releases)

Include the mod version, full game version, region, steps to reproduce and relevant `game.log` excerpts when reporting a problem. Remove personal information before sharing logs. For security reports, follow [SECURITY.md](SECURITY.md).

Thanks to **poliroid** for ModsListAPI and the **OpenWG Gameface** project for the interface dependency.

Licensed under the [GNU General Public License v3.0](licence).
