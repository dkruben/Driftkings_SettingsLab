# Isolated settings development workspace

Work only in this workspace. Do not edit the original Driftkings_Mods_Hide project.
Do not install packages into the game or modify the game installation unless the
user explicitly requests that deployment. Build outputs belong in local build/.
Inspect release scripts for deployment paths before running them.
Preserve configuration formats and i18n where practical.
Develop the independent settings manager in Core/Inject, starting with PlayerPanelPro.
Replace ModSettingsAPI progressively, only removing dependencies when ready.

## Local game and API references

Use E:/Wot_Mods_/Drift_Kings_ModPack/WoT_Tools as the reference tools directory.
Game sources are in wot-src-EU/sources; check sources/version.xml for the client
version and compare wot-src-EU/.version_name, which can differ during updates.
GameFace, ModList and modssettingsapi references are in their
respective sibling directories. Treat these as read-only references.
Check extraction completeness before relying on missing files or comparing APIs.
Select dependency versions compatible with the target client, not merely the
highest version present. Keep project changes inside this SettingsLab workspace.
