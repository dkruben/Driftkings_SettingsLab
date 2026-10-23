# Contributing to Driftkings

This guide explains how the code is organised and how to make a change safely. For building and installing, see the [README](readme.md).

## Ground rules

- **Client scripts run on Python 2.7** (the World of Tanks client). Write code that is valid on both 2.7 and 3: no f-strings, no type hints, no `nonlocal`, no keyword-only arguments. CI parses every client source with Python 2.7.
- **Gameface JavaScript is ES5.** `npm run lint` enforces this.
- **Use `logging`, never `print`.** Import `get_logger` from `driftkings.logger` and declare `LOG = get_logger('Driftkings.<Area>')`. The shared factory preserves client-owned handlers and output. Use `LOG.exception(...)` inside `except` blocks so the traceback reaches the game log.
- **Do not swallow exceptions silently.** Catch the narrowest exception type, and either log it or explain in a comment why ignoring it is correct.
- Prefer **pure, engine-free modules** for logic (see `core/gun_stats.py`, `core/carousel*.py`, `core/high_caliber.py`). They can be tested without the game.
- Regenerate `settings/default_values.py` with the defaults tool and `shared/bootstrap.js` with the UI catalogue tool. The compiler generates the packaged `component_list.py` from enabled manifests; keep the checked-in component list aligned with those manifests.

## Branches and release channels

- `develop` is the development branch for beta versions. Requests referring to a beta mean work on `develop`.
- `main` is the stable release branch. Prepare stable releases there after integrating the validated changes from `develop`.
- Before editing, check the current branch and switch to the branch for the requested channel. Keep the release version and channel in `build_data/release.json` consistent with the release being prepared.

## Repository layout

| Path | Contents |
| --- | --- |
| `mod/res/scripts/client/driftkings` | Runtime Python (the mod itself) |
| `mod/res/scripts/client/gui/mods/mod_driftkings.py` | Game client entry point |
| `mod/res/gui/gameface/mods/driftkings` | Gameface HTML, CSS and ES5 JavaScript |
| `mod/res/gui/gen_resources/driftkings.*.json` | Native Gameface layout declarations |
| `res/configs/driftkings/default` | Canonical default settings (JSON) |
| `flash_source` | ActionScript sources for the battle SWFs |
| `installer` | Windows installer script and the native C# helper |
| `build_data`, `build_tools` | Build contracts, validators, compiler and release tooling |
| `tests` | Portable tests (`core`, `settings_panel`, `installer`) |

Inside the client package:

- `core/` – composition, lifecycle, hooks, keyboard, callbacks, updater, and pure logic helpers.
- `settings/` – settings service, profiles, store, panel (presenter, controls, sections) and `definitions/`.
- `battle/`, `lobby/`, `components/` – the feature components.
- `views/` – Scaleform/Gameface presentation for those components.
- `common/` – shared utilities (colours, config reading, monkeypatching helpers).
- `i18n/` – translation loaders and optional JSON override support; bundled language text lives in `mod/res/mods/driftkings/text/`.

## Architecture

### Core and services

`core/__init__.py` composes the mod explicitly:

1. **Services** are declared as `ServiceSpec(name, factory, requires, phase)`. A service starts only when all the services it `requires` are `active`; otherwise it is marked `blocked`. Factories hold import *paths*, so no engine module is touched until the service really starts. Services are stopped in reverse order.
2. **Components** are the modules listed in `component_list.py` (for example `battle.target_information`). Core imports each one, which *declares* its hooks, then starts the `interface` services, then calls the module's `init()`. A component can declare `REQUIRES_SERVICES`, and optionally `getBattleViews()` / `getWindowViews()`. `fini()` is called on shutdown.
3. A component that fails to import or initialise is **disabled and logged** (`LOG.exception`), and its settings are disabled; it must never take the rest of the mod down.

### Hooks

Patching game code goes through `core/hooks.py`, never directly through ad-hoc monkeypatching:

```python
from driftkings.core.hooks import override, overrideMethod, on_event

@overrideMethod(PlayerAvatar, 'onEnterWorld')
def onEnterWorld(original, avatar, *args, **kwargs):
    result = original(avatar, *args, **kwargs)
    ...
    return result
```

Hooks are declared at import time and **owned by their component**. They are only installed while the owner is active; when it is inactive the wrapper simply delegates to the original function. Always call `original`, and keep handlers small and defensive.

### Settings

- Defaults live as JSON under `res/configs/driftkings/default/`. After editing them run `python build_tools/generate_defaults.py --write` (and `--refresh-snapshot` for intentional default changes). CI runs `--check`.
- A component's settings class lives in `settings/definitions/<area>/<name>.py` and extends `SectionDefinition`. Read values through `settings_service.getComponentDict(config)` and react to changes with `affects(changes, ...)`.
- Names and menu text come from `mod/res/mods/driftkings/text/<code>.yml`. Add and translate new keys in **all 18 languages**, preserving formatting placeholders, then run `python build_tools/validate_locales.py`. English is the runtime fallback; CI requires complete translations.

### Translation resources

Translations are UTF-8 `.yml` resources, loaded through the game VFS (`ResMgr`) and cached per language. They are packaged under `res/mods/driftkings/text/`, rather than compiled into Python bytecode. No YAML library is required. The same parser is used by runtime, validators and installer generation.

Use the supported flat string format:

```yaml
# Component text: component.translation_key
high_caliber_progress.UI_description: "High Caliber progress"
# Nested component dictionaries use additional dots.
penetration_indicator.UI_colors.green: "#60CB00"
# Settings panel text: panel.translation_key (dots remain part of the panel key).
panel.title: "Driftkings settings"
```

Use double-quoted values with JSON escapes: `\n` for a newline, `\"` for a quote and `\\` for a literal backslash. Keep HTML, macros and intentional whitespace inside the quotes. The reader also accepts simple unquoted text and YAML single-quoted strings, but it does not implement full YAML nesting, tags, anchors or multiline blocks. Comments go on their own lines. Duplicate or conflicting keys are rejected.

Existing user overrides remain JSON: `mods/configs/driftkings/i18n/<code>.json` for component sections and `mods/configs/driftkings/locales/<code>.json` for panel strings. The English fallback, language aliases and migration of older component overrides remain available. Do not reintroduce per-language Python modules or copy translations into frontend scripts.

### Gameface resources and naming

Use lowercase `driftkings` for package and directory paths, including Python imports, `coui://` URLs and native resource IDs. Match the spelling and case exactly: CI runs on Linux, where `Driftkings` and `driftkings` are different paths. The game entry point is `gui/mods/mod_driftkings.py`.

Name each Gameface panel folder after its Python presentation module, for example `battle_performance`, `settings_window` or `high_caliber_gameface`. Resource declaration files follow `driftkings.<module>.json`. Layouts owned by the same presentation module can share one folder and declaration file: `hangar_preferences` contains the clock and header-options layouts. Shared frontend helpers live in `shared/`.

Register layouts, scripts, styles and Python owners in `interface_catalog.py`, and include their assets in `build_data/components.json`. Update the matching native declarations under `mod/res/gui/gen_resources/` and any retained resource maps under `mod/res/mods/configs/res_map/`. Existing feature aliases are separate from paths; a folder rename does not require changing them.

After changing the UI catalogue, regenerate and validate:

```bash
python build_tools/generate_ui_catalog.py --write
python build_tools/validate_build_data.py
```

Keep custom text and macros configurable. Use the native UI scale for Gameface layouts; for the results information line, preserve native font sizing across resolution classes and support the configured spacing and separators.

## Adding a component

1. Create the module under `battle/`, `lobby/` or `components/` with `init()` (and `fini()` if it holds state).
2. Declare its hooks with the decorators above; keep calculations in a pure module under `core/` when possible.
3. Add its defaults JSON, settings definition, constants and translations.
4. Register its entry point and assets in `build_data/components.json`, keep `component_list.py` aligned, and register any presentation in `interface_catalog.py`. Regenerate the UI catalogue if needed, then run `python build_tools/validate_build_data.py`.
5. Add tests for any pure logic.

## Testing

Run these before opening a pull request. They cover the main local checks; the complete sequence is defined in `.github/workflows/`:

```bash
python -m unittest discover -s tests/core -p 'test_*.py'
python -m unittest discover -s tests/settings_panel -p 'test_*.py'
python -m unittest discover -s tests/installer -p 'test_*.py'
python build_tools/validate_build_data.py
python build_tools/validate_locales.py
python build_tools/generate_defaults.py --check
python build_tools/generate_ui_catalog.py
python build_tools/build_installer.py
python -m pip install pyflakes
python build_tools/check_undefined_names.py
npm ci --ignore-scripts
npm run lint
npm test
node tests/settings_panel/test_settings_window.js
node tests/settings_panel/test_ratings.js
```

`tests/core` and `tests/settings_panel` also run on Python 2.7 in CI; if you have Docker you can reproduce that with the `python:2.7` image. Tests load real production modules through `tests/core/support.py` with the engine stubbed at the import boundary, so avoid importing `BigWorld`, `gui.*` or `Avatar` from code you want to test.

The current modpack has been tested in-game on Wargaming EU, NA and ASIA, including live battles, replays, Gameface panels and the in-game updater. For each new change, verify the affected behaviour in the target client and state the client version, realm and mode in the pull request. Portable tests complement that verification.

## Signing releases

The updater authenticates `release.json` with an Ed25519 signature. **Signature verification is active:** `TRUSTED_KEYS` in `core/updater/signature.py` already contains a trusted public key. Published release manifests must be signed with a corresponding private key.

1. Use the existing trusted signing key for releases. Only when provisioning a new key, run `python build_tools/sign_release.py --generate release-signing.key` and add its public key to `TRUSTED_KEYS`. Keep private keys offline, outside the repository and CI, and back them up.
2. For each release, after the build: `python build_tools/sign_release.py <version-folder> --key release-signing.key`. This writes `release.json.sig`, and `publish_release.py` verifies it and uploads it with the other assets.
3. To rotate a key, ship a release that lists both the old and the new public keys before retiring the old one.

Clients that predate this feature do not verify signatures; they must update once to get the check.

## Pull requests

- Keep changes focused; one concern per pull request.
- Describe what changed and how you verified it (tests, replay, live battle).
- Include `game.log` excerpts when fixing a bug, with personal information removed.
- Code adapted from other mods must keep its credit and licence (the project is GPL-3.0; see `licence`).
