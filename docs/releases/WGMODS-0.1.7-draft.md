# WGMods draft for 0.1.7

**Status: draft, not published.** Candidate `0.1.7-beta.2` for World of Tanks 2.4.2.0. Public stable remains 0.1.6 and public beta remains 0.1.7-beta.1 until a separate, approved promotion. Character counts below were measured with spaces (Python `len()` on the UTF-8 text, excluding the heading line).

Owner-confirmed status: this is an update of a mod already approved by Wargaming through WGMods, and the moderator-requested corrections were already implemented. This submission does not claim a new approval.

---

## 1. Mod description

<!-- MAX 3000 characters -->

Driftkings SettingsLab adds configurable interface options to World of Tanks: hangar clock, vehicle carousel statistics, Marks of Excellence, crew progression and tooltips, profile ratings, tech tree marks, battle results, battle HUD cards, vehicle markers and an account-management panel. A Settings Panel opens from a launcher in the hangar footer.

Version 0.1.7 is a standalone release. Its interface is built on native Gameface integrations inside Driftkings. The distribution no longer requires, and no longer ships, the external OpenWG Gameface and ModsListAPI packages. Existing third-party mods that use those libraries are not removed and keep working.

Changes in this version:
- Hangar footer launcher, with updated launcher and account icons.
- Native Gameface integration for the hangar clock, Marks of Excellence, crew progression, carousel statistics and post-battle efficiency.
- Battle HUD cards share one owned window per battle HUD.
- Health frames above the native consumables panel, and updated battle-marks presentation.
- A notice when an e-mail address is already saved on another server, and explicit confirmation before Tour Coin purchases.
- Updated minimap enhancements and launcher hover behaviour.
- Remove Fog is available again as an optional Settings Panel option, off by default. It is enabled or disabled only by an explicit user choice, which is kept across sessions.

Your personal settings in `mods/configs/driftkings` are kept on upgrade. The in-game updater verifies the signed manifest and package hash before it stages an update.

Supported game version: World of Tanks 2.4.2.0. Runtime coverage is described in the release notes; regional support is stated there, not here.

---

## 2. Installation instructions

<!-- MAX 1000 characters -->

Close World of Tanks before installing. Run the Setup file or extract the ZIP into the game folder, keeping the `mods/2.4.2.0` structure. Keep your existing `mods/configs/driftkings` directory on upgrade; do not replace it with defaults. No other mod packages are required. Remove Fog is off by default. Enabling it in the Settings Panel installs a separate package after you close the game; disabling it removes that package. An older `Driftkings.RemoveFog.wotmod` is never reinstalled; with the option off, it is removed once after the game closes, with a recovery copy kept in the configuration folder.

---

## 3. Information for moderators

<!-- MAX 1000 characters -->

Update of a mod already approved by Wargaming; the moderator corrections were implemented before this submission (owner-confirmed). This is not a first-time review and does not claim a new approval. Standalone migration: OpenWG Gameface and ModsListAPI are removed from the distribution and from the mandatory dependencies; the interface uses native Gameface resources packaged with the mod. Remove Fog is restored as an optional, default-OFF setting that changes only on an explicit user choice. Runtime validation status is listed in the release notes and may still be pending for some regions.

---

## 4. English changelog (0.1.6 to 0.1.7)

- Standalone: no mandatory OpenWG Gameface or ModsListAPI package; native Gameface integrations for the hangar clock, Marks of Excellence, crew progression, carousel statistics and post-battle efficiency.
- Hangar footer launcher, with updated launcher and account icons.
- Battle HUD cards share one owned window per HUD; health frames above the consumables panel.
- Updated battle-marks presentation.
- Cross-server saved-email notice and explicit consent for Tour Coin purchases.
- Updated minimap enhancements and launcher hover behaviour.
- Remove Fog restored as an optional, default-OFF setting (explicit choice only; legacy values do not enable it).
- Supported game version: World of Tanks 2.4.2.0.

---

## Character counts

| Section | Limit | Characters |
| --- | --- | --- |
| Mod description | 3000 | 1756 |
| Installation instructions | 1000 | 610 |
| Information for moderators | 1000 | 601 |

## Related records

- Readiness and verdicts: [0.1.7-beta.2-phase3-readiness.md](0.1.7-beta.2-phase3-readiness.md)
- Candidate validation record: [0.1.7-beta.2-validation.md](0.1.7-beta.2-validation.md)
