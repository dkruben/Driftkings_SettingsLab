# WGMods draft for 0.1.7

**Status: draft, not published.** Candidate `0.1.7-beta.2` for World of Tanks 2.4.2.0. Public stable remains 0.1.6 and public beta remains 0.1.7-beta.1 until a separate, approved promotion. Character counts below were measured with spaces (Python `len()` on the UTF-8 text, excluding the heading line).

Owner-confirmed status: this is an update of a mod already approved by Wargaming through WGMods, and the moderator-requested corrections were already implemented. This submission does not claim a new approval.

---

## 1. Mod description

<!-- MAX 3000 characters -->

Driftkings SettingsLab adds configurable interface options to World of Tanks: hangar clock, vehicle carousel statistics, Marks of Excellence, crew progression and tooltips, profile ratings, tech tree marks, battle results, battle HUD cards, vehicle markers and an account-management panel. A Settings Panel opens from a launcher in the hangar footer.

Version 0.1.7 is a standalone release. Its interface is built on native Gameface integrations inside Driftkings. The distribution no longer requires, and no longer ships, the external OpenWG Gameface and ModsListAPI packages. Existing third-party mods that use those libraries are not removed and keep working.

Changes in this version:
- Added a hangar footer launcher, with updated launcher and account icons.
- Native Gameface integration for the hangar clock, Marks of Excellence, crew progression, carousel statistics and post-battle efficiency.
- Battle HUD cards share one owned window per battle HUD.
- Updated battle-marks presentation.
- A notice when an e-mail address is already saved on another server, and explicit confirmation before Tour Coin purchases.
- Updated the minimap enhancements panel and launcher hover behaviour, relative to 0.1.7-beta.1.

Your personal settings in `mods/configs/driftkings` are kept on upgrade. The in-game updater verifies the signed manifest and package hash before it stages an update.

Supported game version: World of Tanks 2.4.2.0. Runtime coverage is described in the release notes; regional support is stated there, not here.

---

## 2. Installation instructions

<!-- MAX 1000 characters -->

Close World of Tanks before installing. Run the Setup file or extract the ZIP into the game folder, keeping the `mods/2.4.2.0` structure. Keep your existing `mods/configs/driftkings` directory on upgrade; do not replace it with defaults. No other mod packages are required. If an older `Driftkings.RemoveFog.wotmod` is present in `mods/2.4.2.0`, delete it manually: this release does not remove it.

---

## 3. Information for moderators

<!-- MAX 1000 characters -->

Update of a mod already approved by Wargaming; the moderator corrections were implemented before this submission (owner-confirmed). This is not a first-time review and does not claim a new approval. Standalone migration: OpenWG Gameface and ModsListAPI are removed from the distribution and from the mandatory dependencies; the interface uses native Gameface resources packaged with the mod. Runtime validation status is listed in the release notes and may still be pending for some regions.

---

## 4. English changelog (0.1.6 to 0.1.7)

- Standalone: no mandatory OpenWG Gameface or ModsListAPI package; native Gameface integrations for the hangar clock, Marks of Excellence, crew progression, carousel statistics and post-battle efficiency.
- Added a hangar footer launcher, with updated launcher and account icons.
- Battle HUD cards share one owned window per HUD.
- Updated battle-marks presentation.
- Added a cross-server saved-email notice and explicit consent for Tour Coin purchases.
- Updated the minimap enhancements panel and launcher hover behaviour, relative to 0.1.7-beta.1.
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
