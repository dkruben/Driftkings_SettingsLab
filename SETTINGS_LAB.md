# Driftkings Settings Lab

## Current prototype

ModsListAPI remains the hangar entry point: select Driftkings.
F10 also opens the window. The independent Scaleform UI lists registered mods,
with paginated controls derived from their existing createTemplate() methods.
Checkboxes, option lists, numeric values, colors, text, hotkeys and block settings
are supported. The visual controls include color selection, dropdown lists and column layouts.
Save applies only the selected mod; unsaved drafts survive switching mods and are
discarded when the window closes. Defaults affect exposed settings only.
Mods without templates expose simple top-level values; nested visual settings
remain in their existing JSON files. Existing translations supply field labels.

The Core registration path no longer imports or patches ModSettingsAPI.
Config-backed mod hotkeys are suspended while the own window is open.
Archive manifests include ModsListAPI and Driftkings.ui instead of ModSettingsAPI.

## Verification and remaining runtime work

Registry tests cover validation, defaults, drafts, flat/grouped hotkeys, custom
field retention, template and block callbacks. Flash and Python 2.7 are compiled.
Still requires game testing: ModsList entry, all mod pages, window focus, modifier
key capture, save/reload and lobby/battle transitions. No deployment performed.

Only this isolated workspace is modified. The unified package is built locally at build/unified/Driftkings.wotmod.
