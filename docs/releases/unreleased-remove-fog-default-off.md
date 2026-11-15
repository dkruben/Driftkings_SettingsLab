# Unreleased: Remove fog is off by default

Status: **unreleased.** No version number, release, tag or download link is assigned by this note. It has not been approved by Wargaming.

## What changes

- **Remove fog is off by default** (`battle_preferences.removeFog = false`). A new installation does not create or install `Driftkings.RemoveFog.wotmod`.
- **Manual activation is kept.** You can still turn Remove fog on in the settings panel. The separate package is built from the maps of your installed client and is installed after the game is closed.
- **Turning it off** removes the Driftkings package after the game is closed. The main `driftkings.wotmod` is not changed.

## Existing installations

- An explicit `removeFog` value in your profile (`true` or `false`) is kept as it is.
- A profile with no `removeFog` entry that has the Driftkings package installed for your client is migrated to `true`, so the package is not removed unexpectedly. Only that one entry is written; the other settings are kept.
- A profile with no entry and no package stays off.
- Packages for another client folder or realm are never treated as your preference.
- If the state cannot be determined safely, nothing is written and no install or removal is scheduled. Change the option yourself to apply a choice.
- Nothing is deleted automatically during the migration.

## Fair Play

Removing fog changes what is visible in battle. The feature stays available for players who accept that risk, but it has not been approved by Wargaming. Read the current Fair Play policy before enabling it.

## Upgrade notes

- Your installed packages are not changed by the upgrade itself.
- If you want to remove a package that is already installed, turn the option off and close the game.
