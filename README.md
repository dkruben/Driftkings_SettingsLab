[![WoT Version](https://img.shields.io/badge/WoT-2.4.1.1-red.svg)](https://worldoftanks.eu/)
[![Python 2.7.18](https://img.shields.io/badge/Python-2.7.18-orange.svg)](https://www.python.org/downloads/release/python-2718/)
[![Visual Studio Code](https://img.shields.io/badge/Visual%20Studio%20Code-blue.svg)](https://code.visualstudio.com/)
[![Discord](https://img.shields.io/badge/Discord-green.svg)](https://discord.gg/k2Stjv5fS5)
[![Beta 0.1.5-beta.4](https://img.shields.io/badge/Beta-0.1.5--beta.4-purple.svg)](https://github.com/dkruben/Driftkings_SettingsLab/releases/tag/v0.1.5-beta.4)
[![Stable 0.1.4](https://img.shields.io/badge/Stable-0.1.4-blue.svg)](https://github.com/dkruben/Driftkings_SettingsLab/releases/tag/v0.1.4)

# Driftkings Modpack

A configurable modpack for **Wargaming World of Tanks**, with battle statistics, vehicle markers, aiming tools, hangar improvements and an integrated settings panel.

Built for **WoT 2.4.1.1** on **EU, NA and ASIA**.

> **Settings panel under construction:** the panel passed visual acceptance in the EU game client, but layouts and live previews may still change between versions.

## Downloads

| Release | Windows installer | Manual installation |
| --- | --- | --- |
| **[Stable 0.1.4](https://github.com/dkruben/Driftkings_SettingsLab/releases/tag/v0.1.4)** | [Download Setup.exe](https://github.com/dkruben/Driftkings_SettingsLab/releases/download/v0.1.4/Driftkings-0.1.4-WoT-2.4.1.1-Setup.exe) | [Download ZIP](https://github.com/dkruben/Driftkings_SettingsLab/releases/download/v0.1.4/Driftkings-0.1.4-WoT-2.4.1.1.zip) |
| **[Beta 0.1.5-beta.4](https://github.com/dkruben/Driftkings_SettingsLab/releases/tag/v0.1.5-beta.4)** | [Download Setup.exe](https://github.com/dkruben/Driftkings_SettingsLab/releases/download/v0.1.5-beta.4/Driftkings-0.1.5-beta.4-WoT-2.4.1.1-Setup.exe) | [Download ZIP](https://github.com/dkruben/Driftkings_SettingsLab/releases/download/v0.1.5-beta.4/Driftkings-0.1.5-beta.4-WoT-2.4.1.1.zip) |

Stable **0.1.4** and beta **0.1.5-beta.4** both target WoT **2.4.1.1**. The 0.1.5 betas retire legacy font and macro names, including the `{{v.c_...}}` carousel colour macro; check custom profiles before installing them.

[All releases and changelogs](https://github.com/dkruben/Driftkings_SettingsLab/releases). Each release includes the defaults archive, required dependencies, signed updater manifest and SHA-256 checksums.

### What's new in 0.1.5-beta.4

- **Target card:** each row is on its own line again. The former card is back as the **Classic** preset, now the default, with the vehicle picture, reload with equipment and aligned armour and shell tables, translated into every language. Profiles that still had that card unchanged switch to Classic automatically; edited cards and other presets are kept.
- **Shell types:** AP, APCR, HE, HEAT and HESH in all 18 languages.
- **Frontline:** player statistics now appear on the loading screen and in the TAB, shrinking to fit the narrower columns.
- **Settings panel:** new header image and a GitHub button.
- **Fixes:** Sixth Sense alerts with `%` in the text and the first alert of each battle; battle marks card dragging; decimal target weights; Gameface CSS and font warnings.
- **Logs:** `game.log` names the mod and game versions at startup; updater and account manager failures are logged, never with account data.

### Earlier in 0.1.5-beta.3

- **Carousel colour macro:** `{{v.c_...}}` no longer works. Use `{{v.c:...}}`, for example `{{v.c:winrate}}`; the default settings already do.
- **Account manager page:** a General settings page turns the login-screen button on or off, and **Manage accounts** opens the manager in the hangar to add, edit or delete accounts.
- **Aiming texts:** the aiming countdown, shell flight time and penetration templates use `{name}` fields such as `{timer:.1f}`; older `%(name)s` templates keep working.
- **Battle:** the target card uses Gameface, native team panels work in Frontline, Black Signal and Stronghold, and manual reload uses the native command.
- **Marks of excellence:** a single achievement tooltip in the service record, controlled by Hangar marks.

See [the macro reference](docs/macros/README.md) for every template macro.

### Earlier in 0.1.5-beta.1

- **Legacy names removed:** the `xvm` and `XVMSymbol` font aliases and the `{{xvm-stat}}` macro no longer work. Use `dkm` and `{{stat-available}}` in custom profiles; the default settings already do.
- **Validated in game:** `dkm` fonts in markers, team panels and the carousel, and rating colours on Halloween TAB player names (NA 2.4.1.1).
- **Release tooling:** stricter signing and tag protection, and builds that work with EU, NA and ASIA clients.

### What's new in 0.1.4

- **Account Manager:** corrected intermittent clipping and Escape handling; saved passwords can be explicitly revealed, with a visible checkbox state.
- **Self-contained fonts:** embedded Flash fonts and Gameface resources preserve `dkm` and existing aliases, without OpenWG Common or its additional native modules.
- **Battle fixes:** corrected minimap sector direction, improved player-panel discovery and added native Halloween TAB colour integration, later accepted in game (NA 2.4.1.1, 2026-10-30).
- **Shared contracts:** consolidated constants and numeric/colour helpers while preserving personal settings, defaults and JSON formats.
- **Regression coverage:** reorganised Python and frontend suites, added account lifecycle and compiled-font checks, and updated CI.

## Installation

### Windows installer

1. Close World of Tanks.
2. Download the installer for your chosen release and pick your language.
3. Read what's new, then select your game installation.
4. Choose **Recommended**, **Complete** or **Custom** and pick the components you want enabled; each one shows a preview.
5. Start the game and open **Driftkings settings** through the mods list.

The installer checks the game version and region, installs the required dependencies and keeps existing profiles when reinstalling. To choose the components again, select **Reset to defaults and choose the components again** on the folder page; your current settings are backed up first.

### Manual installation

1. Close World of Tanks and download the ZIP for your chosen release.
2. Extract its `mods` folder into the game installation, merging folders.
3. For a new installation, download `Driftkings-defaults.zip` from the **same release** and extract it into the game installation.
4. Start the game and open Driftkings settings through the mods list.

**Upgrading from the old configuration layout:** back up your personal images and sounds, then remove the old `mods/configs/driftkings` folder before the first launch of version 0.1.3. Configure the mod again in the hangar. Older settings and caches are no longer imported automatically.

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
| Account manager | Account-management interface with its own General settings page: a switch for the login-screen button and **Manage accounts** in the hangar. |
| Clan reward collection | Automatic collection of eligible clan rewards when enabled. |
| Sound bank loader | Loads the mod's packaged sound banks. |

Ratings and progress displays are estimates; they do not guarantee a battle result, server award or gun-mark increase. Vehicle-marker customization applies to supported regular modes; special modes retain native markers. XMQP is not included.

## Settings and updates

The integrated settings panel includes **profiles, themes, UI scale, translations and update channels**. Marker changes can be checked in the tank preview before applying them.

Default configurations are based on the author's EU profile, except vehicle markers, which now follow the reference layout. Personal JSON settings take precedence, and the updater preserves them. Settings remain under `mods/configs/driftkings/<profile>/`.

To receive beta updates, select the **Beta** update channel in Driftkings settings. The `develop` branch carries beta development; `main` carries the stable version.

For custom media, use `mods/configs/driftkings/images/` and `mods/configs/driftkings/sixthsense/`. The default custom Sixth Sense icon is `SixthSenseIcon.png`. Packaged `gui/maps/driftkings/...` image paths are also supported. Select the paths in settings; uninstall preserves your media folders.

### Ratings and palettes

Choose from **NoobMeter, Driftkings, WoT-Life and Tomato.gg** palettes. WNX includes assistance damage for your own battle, results and carousel vehicles; missing data displays `--`. Expected values refresh daily in the hangar and retain the last valid cache if a download fails.

The EU battle overlay defaults to **WN8, EFF and DIFF**. Add `{wnx}` and `{c:wnx}` to battle/results text, or `{{v.wnx}}` and `{{v.c:wnx}}` to carousel fields, to display WNX. Carousel sorting by WNX is also available.

### Languages

**18 languages:** Czech, German, English, Spanish, French, Hungarian, Italian, Japanese, Korean, Polish, Portuguese, Russian, Thai, Turkish, Ukrainian, Vietnamese, Simplified Chinese and Traditional Chinese.

English is the fallback language. Translation corrections are welcome.

### Optional anonymous statistics

Anonymous usage statistics are **off by default**. You can enable them in settings. When enabled, the mod sends a random installation ID, mod/game versions, region, activity heartbeats and error-location metadata to Google Analytics. It does not send player names, account details, error messages or full filesystem paths. Disabling the option stops sending and deletes the installation ID. Replays are not counted.

## Compatibility

Supports Wargaming **EU, NA and ASIA** clients for **WoT 2.4.1.1**. Mir Tankov/RU is outside the project's scope.

The stable release has prior in-game validation. Each beta passes package verification and GitHub Actions, including Python 2/3 and Gameface tests, and is tested on the EU client before publication.

## Development

The project uses **Python 2.7**, **ActionScript 3** and **ES5 JavaScript** for Gameface. Build and validation tools run on Python 3.

The redesigned settings panel (since `0.1.3`) includes option details, change review and minimap/HUD/carousel previews, while retaining the original spectrum colour picker. Published release checks are recorded in the [release history](https://github.com/dkruben/Driftkings_SettingsLab/releases); in-game acceptance is recorded in [docs/STATUS.md](docs/STATUS.md).

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, architecture, tests, translations and release instructions. Feature guides and historical reviews are available in [`docs/`](docs/).

## Support and credits

[Join Discord](https://discord.gg/k2Stjv5fS5) · [Report an issue](https://github.com/dkruben/Driftkings_SettingsLab/issues) · [Browse releases](https://github.com/dkruben/Driftkings_SettingsLab/releases)

When reporting a problem, include the mod version, game version, region, reproduction steps and relevant `game.log` excerpts. Remove personal information before sharing logs.

Dependencies: **ModsListAPI** by poliroid and **OpenWG Gameface**.

Licensed under [GPL-3.0](licence).
