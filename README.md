[![WoT Version](https://img.shields.io/badge/WoT-2.4.1.1-red.svg)](https://worldoftanks.eu/)
[![Python 2.7.18](https://img.shields.io/badge/Python-2.7.18-orange.svg)](https://www.python.org/downloads/release/python-2718/)
[![Visual Studio Code](https://img.shields.io/badge/Visual%20Studio%20Code-blue.svg)](https://code.visualstudio.com/)
[![Discord](https://img.shields.io/badge/Discord-green.svg)](https://discord.gg/GJcy4x7SP)
[![Beta 0.1.3-beta.2](https://img.shields.io/badge/Beta-0.1.3--beta.2-purple.svg)](https://github.com/dkruben/Driftkings_SettingsLab/releases/tag/v0.1.3-beta.2)
[![Stable 0.1.2](https://img.shields.io/badge/Stable-0.1.2-blue.svg)](https://github.com/dkruben/Driftkings_SettingsLab/releases/tag/v0.1.2)

# Driftkings Modpack

A configurable modpack for **Wargaming World of Tanks**, with battle statistics, vehicle markers, aiming tools, hangar improvements and an integrated settings panel.

Built for **WoT 2.4.1.1** on **EU, NA and ASIA**.

## Downloads

| Release | Windows installer | Manual installation |
| --- | --- | --- |
| **[Beta 0.1.3-beta.2](https://github.com/dkruben/Driftkings_SettingsLab/releases/tag/v0.1.3-beta.2)** | [Download Setup.exe](https://github.com/dkruben/Driftkings_SettingsLab/releases/download/v0.1.3-beta.2/Driftkings-0.1.3-beta.2-WoT-2.4.1.0-Setup.exe) | [Download ZIP](https://github.com/dkruben/Driftkings_SettingsLab/releases/download/v0.1.3-beta.2/Driftkings-0.1.3-beta.2-WoT-2.4.1.0.zip) |
| **[Stable 0.1.2](https://github.com/dkruben/Driftkings_SettingsLab/releases/tag/v0.1.2)** | [Download Setup.exe](https://github.com/dkruben/Driftkings_SettingsLab/releases/download/v0.1.2/Driftkings-0.1.2-WoT-2.4.1.0-Setup.exe) | [Download ZIP](https://github.com/dkruben/Driftkings_SettingsLab/releases/download/v0.1.2/Driftkings-0.1.2-WoT-2.4.1.0.zip) |

The published downloads above target WoT **2.4.1.0**. The `develop` branch now builds for **2.4.1.1**; this update has not replaced any published release.

[All releases and changelogs](https://github.com/dkruben/Driftkings_SettingsLab/releases). Each release includes the defaults archive, required dependencies, signed updater manifest and SHA-256 checksums.

### What's new in the beta

- **Vehicle markers:** separate layouts for allies/enemies, alive/destroyed vehicles and normal/ALT views; configurable text, ratings, health bars, icons and floating damage.
- **Live tank preview:** edit marker fields, simulate damage and check team colours, HP and visibility. The property column has its own scrollbar.
- **Updated defaults:** the author's EU profile for the clock, panel positions, carousel, minimap and markers. Settings-window scale starts at 140%, with 94% opacity.
- **Font and editor fixes:** corrected native font handling, marker font aliases, colour inputs, slider limits and reference errors.

## Installation

### Windows installer

1. Close World of Tanks.
2. Download the installer for your chosen release.
3. Select your game installation and the components you want enabled.
4. Start the game and open **Driftkings settings** through the mods list.

The installer checks the game version and region, installs the required dependencies and preserves existing profiles when reinstalling.

### Manual installation

1. Close World of Tanks and download the ZIP for your chosen release.
2. Extract its `mods` folder into the game installation, merging folders.
3. For a new installation, download `Driftkings-defaults.zip` from the **same release** and extract it into the game installation.
4. Start the game and open Driftkings settings through the mods list.

**Upgrading from the old configuration layout:** back up your personal images and sounds, then remove the old `mods/configs/driftkings` folder before the first launch of the 0.1.3 beta series. Configure the mod again in the hangar. Older settings and caches are no longer imported automatically.

## Included features

Components can be enabled and configured individually. Availability depends on the vehicle, battle mode and selected options.

### Battle interface and statistics

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

### Camera, aiming and controls

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

### Hangar and utilities

| Feature | What it does |
| --- | --- |
| Vehicle carousel | Card layouts, filters, sorting and vehicle statistics. |
| Hangar and tech-tree Marks of Excellence | Gun-mark information for the selected vehicle and supported tech-tree displays. |
| Crew management | Automatic crew return, progression, remaining XP and estimated battles in supported crew screens. |
| Service record ratings | Player/vehicle WN8 and configurable rating colours in native service-record screens. |
| Hangar preferences | Header buttons, widgets, notifications and garage options. |
| General settings and clock | Editable hangar clock fields with time/date text, background images, positioning and shadows. |
| AccountManager | Account-management interface, controlled through Hangar preferences. |
| Clan reward collection | Automatic collection of eligible clan rewards when enabled. |
| Sound bank loader | Loads the mod's packaged sound banks. |

Ratings and progress displays are estimates; they do not guarantee a battle result, server award or gun-mark increase. Vehicle-marker customization applies to supported regular modes; special modes retain native markers. XMQP is not included.

## Settings and updates

The integrated settings panel includes **profiles, themes, UI scale, translations and update channels**. Marker changes can be checked in the tank preview before applying them.

Default configurations are based on the author's EU profile. Personal JSON settings take precedence, and the updater preserves them. Settings remain under `mods/configs/driftkings/<profile>/`.

To receive beta updates, select the **Beta** update channel in Driftkings settings. The `develop` branch carries beta development; `main` carries the stable version.

For custom media, use `mods/configs/driftkings/images/` and `mods/configs/driftkings/sixthsense/`. The default custom Sixth Sense icon is `SixthSenseIcon.png`. Packaged `gui/maps/driftkings/...` image paths are also supported. Select the paths in settings; uninstall preserves your media folders.

### Ratings and palettes

Choose from **NoobMeter, Driftkings, WoT-Life and Tomato.gg** palettes. WNX includes assistance damage for your own battle, results and carousel vehicles; missing data displays `--`. Expected values refresh daily in the hangar and retain the last valid cache if a download fails.

The EU battle overlay defaults to **WN8, EFF and DIFF**. Add `{wnx}` and `{c:wnx}` to battle/results text, or `{{v.wnx}}` and `{{v.c_wnx}}` to carousel fields, to display WNX. Carousel sorting by WNX is also available.

### Languages

**18 languages:** Czech, German, English, Spanish, French, Hungarian, Italian, Japanese, Korean, Polish, Portuguese, Russian, Thai, Turkish, Ukrainian, Vietnamese, Simplified Chinese and Traditional Chinese.

English is the fallback language. Translation corrections are welcome.

### Optional anonymous statistics

Anonymous usage statistics are **off by default**. You can enable them in settings. When enabled, the mod sends a random installation ID, mod/game versions, region, activity heartbeats and error-location metadata to Google Analytics. It does not send player names, account details, error messages or full filesystem paths. Disabling the option stops sending and deletes the installation ID. Replays are not counted.

## Compatibility

Supports Wargaming **EU, NA and ASIA** clients for **WoT 2.4.1.1**. Mir Tankov/RU is outside the project's scope.

The stable release has prior in-game validation. Beta 0.1.3-beta.2 passed package verification and GitHub Actions, including Python 2/3 and Gameface tests. Its latest marker, font and layout changes still need visual confirmation in game.

## Development

The project uses **Python 2.7**, **ActionScript 3** and **ES5 JavaScript** for Gameface. Build and validation tools run on Python 3.

The `develop` branch includes the redesigned settings panel, with option details, change review and minimap/HUD/carousel previews. It retains the original spectrum colour picker. This interface is a development build awaiting in-game visual acceptance; it is not a replacement of the published beta assets. See the [integration plan](docs/PLANO_PAINEL_CONFIGURACOES.md).

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, architecture, tests, translations and release instructions. Feature guides and historical reviews are available in [`docs/`](docs/).

## Support and credits

[Join Discord](https://discord.gg/GJcy4x7SP) · [Report an issue](https://github.com/dkruben/Driftkings_SettingsLab/issues) · [Browse releases](https://github.com/dkruben/Driftkings_SettingsLab/releases)

When reporting a problem, include the mod version, game version, region, reproduction steps and relevant `game.log` excerpts. Remove personal information before sharing logs.

Dependencies: **ModsListAPI** by poliroid and **OpenWG Gameface**.

Licensed under [GPL-3.0](licence).
