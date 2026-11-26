# Driftkings SettingsLab

**A customizable interface modpack for World of Tanks**: battle statistics, hangar enhancements, aiming tools, vehicle markers and one integrated settings panel.

[![Latest release](https://img.shields.io/github/v/release/dkruben/Driftkings_SettingsLab?label=Latest%20release)](https://github.com/dkruben/Driftkings_SettingsLab/releases/latest)
[![World of Tanks 2.4.2.0](https://img.shields.io/badge/World_of_Tanks-2.4.2.0-red)](https://worldoftanks.eu/)
[![Discord](https://img.shields.io/badge/Discord-Community-5865F2)](https://discord.gg/k2Stjv5fS5)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-green)](licence)

---

## Download

| | |
| --- | --- |
| **Latest release** | **Driftkings 0.1.7** for World of Tanks **2.4.2.0** |
| Release page | [github.com/dkruben/Driftkings_SettingsLab/releases](https://github.com/dkruben/Driftkings_SettingsLab/releases) |
| Community | [Discord](https://discord.gg/k2Stjv5fS5) |

Download every file from the same release. Keep the `SHA256SUMS.txt` file to verify your downloads.

## What it offers

Enable only the components you want. Each one can be configured from a single settings panel, with profiles and live previews.

- **Battle** – custom player panels and team statistics, vehicle markers, performance ratings (WN8, EFF, WNX and others), Marks of Excellence and High Caliber progress, vehicle health, minimap enhancements, spotted and assist notifications, Sixth Sense alerts and a battle log.
- **Aiming & camera** – third-person and sniper camera options, gun traverse limits, aiming reticles and countdown, shell flight time, armour-penetration indicator, artillery blast radius, server turret synchronization, autoaim target highlight and repair shortcuts.
- **Hangar** – vehicle carousel with statistics, crew management, Marks of Excellence in the hangar and tech tree, service-record ratings, hangar preferences, an editable hangar clock and an account manager.
- **Utilities** – a footer launcher that opens the settings panel from the hangar, an optional clan-reward collector, and a sound-bank loader.

Ratings and progress figures are estimates. They do not predict battle results, awards or gun-mark progress. Vehicle-marker customization applies to regular battle modes; special modes keep the native markers.

## Compatibility

Driftkings is a standalone package: it needs no other mod and includes its own interface layer.

| Area | Status |
| --- | --- |
| Game version | World of Tanks **2.4.2.0** |
| Production realms the project supports | **EU, NA, ASIA and CN** |
| Realms validated for **0.1.7** | **EU** and **NA** |
| Not validated for 0.1.7 | ASIA and CN |
| Other regions | Not supported |

Support for a realm is confirmed release by release. A matching game version alone does not guarantee that a realm is validated for a given Driftkings release.

## Installation

Close World of Tanks before you install or update.

### Option 1 – Windows installer (recommended)

1. Download `Driftkings-0.1.7-WoT-2.4.2.0-Setup.exe` from the release page and run it.
2. Choose your language and confirm the game folder (the one that contains `version.xml`).
3. Pick **Recommended**, **Complete** or **Custom** and choose the components to enable.
4. Start the game and open **Driftkings settings** from the mods list.

The installer keeps your existing settings when you reinstall. To choose the components again, select **Reset to defaults and choose the components again** on the folder page; your current settings are backed up first.

### Option 2 – Manual installation

1. Download `Driftkings-0.1.7-WoT-2.4.2.0.zip`.
2. Extract its `mods` folder into the game folder and merge it with the existing one.
3. For a new installation only, also download `Driftkings-defaults.zip` from the same release and extract it into the game folder. Do not do this when updating; your settings live in `mods/configs/driftkings`.
4. Start the game and open **Driftkings settings** from the mods list.

### Updating

The in-game updater downloads the signed update, checks its signature, size and SHA-256 before applying it, and applies it after the game has closed. Your settings under `mods/configs/driftkings` are kept.

## Settings, profiles and updates

The settings panel includes profiles, themes, UI scale, translations and update channels. Marker changes can be previewed on a tank before you apply them. Select the **stable** channel for public releases, or **beta** to receive prerelease updates.

Custom images and sounds go in `mods/configs/driftkings/images/` and `mods/configs/driftkings/sixthsense/`. Uninstalling keeps these folders.

### Anonymous statistics (optional)

Anonymous usage statistics are **off by default**. When you turn them on, the mod sends a random installation ID, the mod and game versions, the region and the error types to Google Analytics. It never sends player names, account details or error messages. Turning the option off stops sending and deletes the installation ID.

## Languages

In-game text is available in 18 languages: Chinese (Simplified and Traditional), Czech, German, English, Spanish, French, Hungarian, Italian, Japanese, Korean, Polish, Portuguese, Russian, Thai, Turkish, Ukrainian and Vietnamese. English is the fallback. Translation corrections are welcome on [Discord](https://discord.gg/k2Stjv5fS5).

## What's new in 0.1.7

- A footer launcher in the hangar, with updated icons.
- Native Gameface integration for the hangar clock, Marks of Excellence, crew progression, carousel statistics and post-battle efficiency.
- Battle HUD cards share one window per battle HUD.
- Updated Marks of Excellence presentation in battle.
- A notice when your e-mail address is already saved on another server, and explicit confirmation before Tour Coin purchases.
- Updated minimap enhancements panel and launcher hover behaviour.

## Support and issues

- Questions and help: [Discord](https://discord.gg/k2Stjv5fS5).
- Bugs and feature requests: open an issue on [GitHub](https://github.com/dkruben/Driftkings_SettingsLab/issues). Include your game version, realm, the Driftkings version and, if possible, the relevant lines from `game.log`.
- Security concerns: see [SECURITY.md](SECURITY.md).

## Fair play

Driftkings is an interface modpack. Wargaming decides what is permitted in World of Tanks. Check the current rules and terms before you use any mod, and keep the options you enable within them.

## Credits and license

Driftkings SettingsLab is released under the **GNU General Public License v3.0**; see [licence](licence). Contributors are listed in the project's commit history. Thanks to the Driftkings community for testing and feedback.

World of Tanks is a trademark of Wargaming.net. This project is not affiliated with or endorsed by Wargaming.net.
