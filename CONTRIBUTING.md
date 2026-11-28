# Contributing to Driftkings SettingsLab

Thank you for helping. This guide covers the rules for code and resources. The architecture, build, validation and release processes are in [docs/AI_CONTEXT.md](docs/AI_CONTEXT.md), which is also the reference for AI assistants.

## Branches

- `develop` receives features, improvements and CT development. Open pull requests into `develop`.
- `main` holds stable releases and their hotfixes. Do not open feature pull requests against it.
- Keep changes focused: one concern per pull request.

## Code rules

- **Client scripts run on Python 2.7.** Code must be valid on Python 2.7 and Python 3: no f-strings, no type hints, no `nonlocal`, no keyword-only arguments. The Python 2.7 AST parse and runtime suite run in CI.
- **Imports** are alphabetical in three groups separated by blank lines: standard library, game libraries, then Driftkings modules. Check with `python -m isort --settings-path mod/res/scripts/client --check-only mod/res/scripts/client`.
- **Logging:** use `logging`, never `print`. Import `get_logger` from `driftkings.logger` and declare `LOG = get_logger('Driftkings.<Area>')`. Call `LOG.exception(...)` inside `except` blocks so the traceback reaches the game log.
- **Gameface JavaScript is ES5.** Lint with `npm --prefix build_tools/javascript run lint`.
- **Paths are lowercase `driftkings`** for packages, directories, `coui://` URLs and native resource IDs. Match the case exactly: CI runs on Linux, where `Driftkings` and `driftkings` are different paths.
- **Do not reintroduce** per-language Python modules, copies of translations in frontend scripts, or hard-coded realm preferences.

## Translations

Translations are UTF-8 `.yml` files under `mod/res/mods/driftkings/text/`, one per language. Use the flat format:

```yaml
# Component text: component.translation_key
high_caliber_progress.UI_description: "High Caliber progress"
# Nested dictionaries use further dots.
penetration_indicator.UI_colors.green: "#60CB00"
# Settings panel text: panel.translation_key
panel.title: "Driftkings settings"
```

Use double-quoted values with JSON escapes (`\n`, `\"`, `\\`). Comments go on their own lines. Duplicate keys are rejected. Keep the English file complete; other languages fall back to English.

## Gameface resources

- Name each panel folder after its Python presentation module, for example `battle_performance`. Shared frontend helpers live in `shared/`.
- Register layouts, scripts, styles and their Python owners in `interface_catalog.py`, and include their assets in `build_data/components.json`.
- After changing the UI catalogue, run `python build_tools/generate_ui_catalog.py --write` and then `python build_tools/validate_build_data.py`.

## Adding a component

1. Create the module under `battle/`, `lobby/` or `components/` with `init()` (and `fini()` if it holds state).
2. Keep calculations in a pure module under `core/` when possible.
3. Add its defaults JSON, settings definition, constants and translations.
4. Register its entry point and assets in `build_data/components.json`, keep `component_list.py` aligned, and register any presentation in `interface_catalog.py`. Then run `python build_tools/validate_build_data.py`.
5. Add tests for pure logic.

## Testing

```powershell
python -B tests/run_python.py --suite runtime
python -B tests/run_python.py --suite build
npm --prefix build_tools/javascript test
```

Run only the suites that a change affects. Focused tests for a single component are preferred. Tests must not depend on a game client, a network connection or a proprietary file.

## Pull requests

- Describe what changed and how you verified it (tests, replay, live battle).
- Include the relevant `game.log` lines when fixing a bug, with personal information removed.
- Code adapted from other mods must keep its credit and its GPL-3.0 licence (see [licence](licence)).
- Do not commit generated build output, local toolchain settings, private keys or credentials.

## Removed features

Remove Fog is an optional, default-OFF feature: `core/fog_package.py` (controller), `installer/source/fogpackage.cs` (native helper, built by `fog_package_helper`), its setting, texts and tests (`tests/runtime/core/test_fog_*.py`, `tests/runtime/settings/test_fog_reload_integration.py`, `tests/build/test_optional_fog_contract.py`). Its atmospheric leaves are not yet established as independent of gameplay visibility, so the feature generates nothing until they are; do not add a leaf without that evidence. Public distribution requires Fair Play confirmation first.

## Security

See [SECURITY.md](SECURITY.md) for how to report vulnerabilities. Never publish signing keys or credentials.
