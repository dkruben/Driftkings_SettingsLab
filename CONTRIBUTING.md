# Contributing to Driftkings

This guide explains how the code is organised and how to make a change safely. For building and installing, see the [README](README.md). Run all commands below from the repository root. The README and contribution guide live at the repository root; other Markdown documentation lives under `docs/`; repository paths in code spans are relative to the repository root.

## Ground rules

- **Client scripts run on Python 2.7** (the World of Tanks client). Write code that is valid on both 2.7 and 3: no f-strings, no type hints, no `nonlocal`, no keyword-only arguments. CI parses every client source with Python 2.7.
- **Keep Python imports alphabetical in three groups**, separated by a blank line: Python standard libraries, game libraries, then Driftkings modules. Keep conditional and local imports in their existing execution scope. Run `python -m isort mod/res/scripts/client` to apply the client configuration, or add `--check-only` to check it.
- **Gameface JavaScript is ES5.** `npm run lint` enforces this.
- Vehicle markers build from a SHA-256-pinned native movie. Configure RABCDAsm with
  `DK_RABCDASM_HOME` or `--rabcdasm-home`; see the [vehicle marker guide](docs/vehicle_markers/README.md).
- **Use `logging`, never `print`.** Import `get_logger` from `driftkings.logger` and declare `LOG = get_logger('Driftkings.<Area>')`. The shared factory preserves client-owned handlers and output. Use `LOG.exception(...)` inside `except` blocks so the traceback reaches the game log.
- **Do not swallow exceptions silently.** Catch the narrowest exception type, and either log it or explain in a comment why ignoring it is correct.
- Prefer **pure, engine-free modules** for logic (see `core/gun_stats.py`, `core/carousel*.py`, `core/high_caliber.py`). They can be tested without the game.
- Regenerate `settings/default_values.py` with the defaults tool and `shared/bootstrap.js` with the UI catalogue tool. The compiler generates the packaged `component_list.py` from enabled manifests; keep the checked-in component list aligned with those manifests.
- Write fixed colours as `#RRGGBB`. Reuse `colorutils.parse`, `nativestate.color` or `VMState.rgb` where ActionScript needs a numeric colour. Keep bit masks and format-compatibility parsers separate from colour literals.
- Colour settings require the `#` prefix. Legacy numeric prefixes and bare hex strings are rejected; do not restore prefix-preserving save logic or automatic conversion of old colour strings. Keep actual native numeric colours as numbers at the API boundary. HTML templates consume the complete colour value, including `#`, so do not add a second prefix.
- Owned ActionScript text fields use `embedFonts = true` with the client's `$FieldFont`/`$TitleFont` aliases. Fields copied from native text retain its font settings. The marker adapters map `xvm` and `XVMSymbol` to the client font in both Python and Gameface; keep their mappings equivalent.

## Branches and release channels

- `develop` is the development branch for beta versions. Requests referring to a beta mean work on `develop`.
- `main` is the stable release branch. Prepare stable releases there after integrating the validated changes from `develop`.
- Before editing, check the current branch and switch to the branch for the requested channel. Keep the release version and channel in `build_data/release.json` consistent with the release being prepared.
- Published versions: beta `0.1.3-beta.2` and stable `0.1.2`, targeting WoT `2.4.1.0`. Source reference: EU `2.4.1.5498`. A new release needs a new version; do not move or rebuild an existing tag for a documentation-only change.

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
| `docs` | Project overview, contribution guide, feature guides and dated audit reports; research data/scripts remain local |

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

The beta defaults follow the author's active EU profile. The settings window starts at 140% scale and 94% opacity. Preserve personal profiles when applying updates; a default change is not permission to overwrite installed settings, caches or media. Update the canonical JSON, generated Python fallback and defaults snapshot together.

When changing a settings declaration, verify that it opens and applies without changes through `SettingsRegistry`. `test_current_defaults_open_and_apply_through_every_settings_page` checks this for every current feature definition, including nested JSON and hotkeys. For the marker editor, also check the property scrollbar, wheel propagation, tab/group changes and resize; reuse `DK.dom.scrollbar` and dispose resize listeners and deferred updates.

### Colour resources

Colour resources live in `mod/res/mods/driftkings/colors/`: `shared.json` holds the shared team, vehicle-type, team-HP and damage colours; `noobmeter.json`, `driftkings.json`, `wotlife.json` and `tomato.json` hold the individual statistical palettes. Each file uses `def` for named colours and `colors` for tables. Whole-value strings such as `"${def.colorRating.very_bad}"` reference definitions within that same file. This adapts the XVM [colours configuration](https://gitlab.com/xvm/xvm/-/blob/master/release/configs/default_wg/colors.xc) to strict JSON; it does not implement XC comments, file includes or arbitrary expressions. Keep each `value`/`color` entry on one line.

The game loads these bundled resources once through `ResMgr`; standalone tools read the same JSON from disk. The ordered `palettes` list in `shared.json` supplies the palette names and filenames to the loader and settings selectors. Preserve the existing indices (NoobMeter, Driftkings, WoT-Life, Tomato.gg), threshold order and numeric types. To add a palette, create another JSON file with the same structure and append its entry to `palettes`. Shared tables are merged automatically and must not be repeated or overridden by individual palettes. Adding a statistical rating such as WNX also requires its metric data and calculation; adding a colour file alone does not implement that rating. Rebuild and restart the client to apply changes.

`relativePerformance` is a Driftkings scale, not an official WN8 rating. Its exclusive upper bounds are 0.5, 0.75, 1.0, 1.5 and 2.0, followed by a final catch-all band. Battle efficiency keeps `{diff}` as damage dealt minus WN8 expected damage, while `{c:diff}` uses damage dealt divided by WN8 expected damage on this scale, both in battle and in results. Missing or non-positive expected damage uses the palette's no-data colour. The separate `diff` table remains the sign-based scale for other statistical comparisons.

The palette files include `sources` documenting upstream references and remaining adaptations. NoobMeter, Driftkings and WoT-Life can contain local threshold/colour customizations; those source links do not certify an exact upstream copy. The current local values are preserved. WoT-Life occupies index 2, formerly WoTLabs, so existing index-2 selections remain valid. The original NoobMeter win-rate thresholds were not verified. Other inherited metrics remain Driftkings adaptations. The Driftkings WN8/EFF/WTR thresholds are a fixed snapshot of `xvmscales-wg.json` dated 2026-10-24; indices 16, 33, 52, 75 and 92 give the exclusive raw boundaries for its integer X-scale colour bands. Its configured win-rate threshold is 63.49.

`wn8effd` is damage dealt divided by WN8 expected damage. All palettes map the shared damage-efficiency limits (0.5, 0.7, 0.9, 1.2, 1.9, final band) to their own colours. The carousel already supports `{{v.wn8effd}}` and `{{v.c_wn8effd}}`. Battle efficiency and battle results also support `{wn8effd}` (two decimal places) and `{c:wn8effd}`. For example, `<font color='{c:wn8effd}'>{wn8effd}</font>` displays `1.50` for 150% of expected damage. Missing or invalid expected damage displays `--` in the no-data colour. Existing format defaults and DIFF behaviour are retained.

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

Existing user overrides remain JSON: `mods/configs/driftkings/i18n/<code>.json` for component sections and `mods/configs/driftkings/locales/<code>.json` for panel strings. The English fallback and language aliases remain available. Older component override folders are not imported. Do not reintroduce per-language Python modules or copy translations into frontend scripts.

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
```

`npm test` runs all current Gameface regression suites, including the settings window and ratings helpers.

`tests/core` and `tests/settings_panel` also run on Python 2.7 in CI; if you have Docker you can reproduce that with the `python:2.7` image. Tests load real production modules through `tests/core/support.py` with the engine stubbed at the import boundary, so avoid importing `BigWorld`, `gui.*` or `Avatar` from code you want to test.

The stable release has prior in-game validation; beta `0.1.3-beta.2` passed package verification and GitHub Actions. Its latest marker/font/layout changes still need visual confirmation in game. For each new change, verify the affected behaviour in the target client and state the client version, realm and mode in the pull request. Portable tests complement that verification.

The release baseline has 413 Core tests and 27 settings-panel tests on both Python 2.7 and Python 3, plus 33 installer tests on Python 3 and the Gameface regression suites. Counts describe this baseline, not a fixed requirement for later changes.

## Signing releases

The updater authenticates `release.json` with an Ed25519 signature. **Signature verification is active:** `TRUSTED_KEYS` in `core/updater/signature.py` already contains a trusted public key. Published release manifests must be signed with a corresponding private key.

1. Use the existing trusted signing key for releases. Only when provisioning a new key, run `python build_tools/sign_release.py --generate release-signing.key` and add its public key to `TRUSTED_KEYS`. Keep private keys offline, outside the repository and CI, and back them up.
2. For each release, after the build: `python build_tools/sign_release.py <version-folder> --key release-signing.key`. This writes `release.json.sig`, and `publish_release.py` verifies it and uploads it with the other assets.
3. To rotate a key, ship a release that lists both the old and the new public keys before retiring the old one.

Clients that predate this feature do not verify signatures; they must update once to get the check.

### Build and publish a new beta

1. Update `build_data/release.json`, the runtime `VERSION` and the README version/download links. Record the changes in the changelog. Commit and push to `develop`, then build from a clean checkout.
2. Run `python build_tools/compiler.py --mode release --channel beta`. This compiles and verifies the package without installing or publishing it.
3. Compile and attach the installer: `python build_tools/build_installer.py --artifacts build/releases/beta/<version> --compile --attach-to-release`. Inno Setup 6.7.1+ is required.
4. Sign with `python build_tools/sign_release.py build/releases/beta/<version> --key <private-key-file>` and preview with `python build_tools/publish_release.py build/releases/beta/<version>`.
5. After GitHub Actions passes for the built commit, add `--publish` to create a draft with the verified assets. Check the uploaded filenames, sizes and SHA-256 digests against the local inventory, then publish it as a prerelease. `--publish --live` publishes directly when that is the intended workflow.
6. Verify the public manifest/signature and tag commit. Keep the stable release as GitHub's latest stable release. Documentation edits after publication do not require replacing release assets.

The publisher rejects dirty builds or a checkout that differs from the recorded source revision. A release includes the installer, distribution ZIP, defaults, dependencies, WOTMOD, modpack manifest, signed updater manifest, build report and checksums. Never publish the private signing seed.

## Pull requests

- Keep changes focused; one concern per pull request.
- Describe what changed and how you verified it (tests, replay, live battle).
- Include `game.log` excerpts when fixing a bug, with personal information removed.
- Code adapted from other mods must keep its credit and licence (the project is GPL-3.0; see [licence](licence)).

### WNX and Tomato.gg

The fourth palette, `Tomato.gg`, uses the 100-point WN8/WNX/win-rate reference and continuous HSL interpolation published at https://tomato.gg/wnx (snapshot 2026-10-25). Its other reference metrics are average tier, damage, frags, damage ratio and K/D. Existing palettes reuse their own WN8 colour bands for a WNX value; the WNX number is calculated separately and is never a renamed WN8 number. Locally customized NoobMeter/Driftkings/WoT-Life thresholds are retained; historical source links do not certify those local adjustments.

`core/wnx.py` calculates WNX from direct damage, kills, spots and assistance. Assistance is weighted by 0.67. The single-vehicle function follows the page's executable calculator rounding (round the scaled raw value, then multiply by 1.65); its overall helper follows the separately published overall formula (multiply by 1.65, then round). Presenters round the single-vehicle result to a whole display value. Overall totals must use battle-weighted expected values per matched vehicle, not an average of individual tank ratings.

Battle efficiency and battle results support `{wnx}` and `{c:wnx}`. The carousel supports `{{wnx}}`, `{{c:wnx}}`, `{{v.wnx}}`, `{{v.c_wnx}}`, and the `wnx` sorting criterion. Live assistance includes personal assist and stun damage; results use the matching native fields. The carousel reads the native vehicle dossier assistance and its recorded battle denominator. Missing assistance or expected values gives no rating and displays `--`; it must not silently become zero. WNX is available for the player's own battle/results and own vehicle carousel. Service-record/player-panel WN8 is retained; adding WNX there needs its own per-tank account collection and display work.

The existing statistics worker refreshes the public https://tomato.gg/wnx page under the same daily hangar-only policy as other statistical references, stores normalized JSON as `wnxexp.json`, and applies it on the client thread. The parser extracts numeric fields only and never executes downloaded JavaScript. A malformed, partial or changed page is rejected; the last valid cache remains available. Without a valid cache, WNX displays `--` until a download succeeds. No Tomato API key is required. The colour reference is a shipped snapshot, not an automatic live colour-scale update.

Tests include golden outputs generated from the publisher's executable JavaScript calculator and HSL colour functions, plus native battle/results, vehicle dossier and cache-preservation coverage. The EU-profile battle overlay defaults to WN8, EFF and DIFF; WNX remains available through its macros. Existing custom templates are preserved.

The minimap `mapSize` caption uses HTML in `format` (including font size and colour), percentage `alpha`, `offsetX`/`offsetY` relative to the native map origin, and fixed `width`/`height` in pixels. Its `shadow` object accepts `enabled`, `distance`, `angle`, `color`, percentage `alpha`, `blur` and `strength`. Negative offsets are supported. Legacy `fontSize`/`color` and `x`/`y` are converted on load. Macros `{{width}}`, `{{height}}` and `{{cellsize}}` still expand in the HTML.

The minimap checks the native colorblind flag on its refresh and uses the native enemy text
scheme for enemy names/HP and lost-position tint when enabled. Normal and destroyed colours
keep their configured behaviour. Roster templates expose `{{colorblind}}` (boolean), usable
inside conditions; toggling the game option invalidates the affected cached outputs.
An alternative HP image can be selected, for example:
`img://gui/maps/driftkings/playerpanelpro/hp/hp_alive_{{ally?l|{{colorblind?r_cb|r}}}}.png`.
The shipped `hp_alive_r_cb.png` is selected only for enemy rows in colorblind mode.
The normal left/right images remain selected otherwise. The author supplied all three
HP textures at 72 x 24 pixels; the current EU-profile default displays the HP image at 24 pixels high. Its configured position and dimensions remain editable.

## Project naming and compatibility

Use descriptive internal names: `core/vehicle_markers/schema.py` for marker layouts, `stats/ratings.py` for normalized ratings and `colors/driftkings.json` for palette index 1. Keep numeric palette indices and all existing colour thresholds unchanged when renaming a palette.

New templates use `{{stat-available}}`. `core/legacy_names.py` retains the old macro and cache filename only as read aliases for installed profiles. The Python renderer, settings validator, ActionScript markers and Gameface sample must continue accepting those legacy templates. New cache downloads use `ratingScales.json`; an existing legacy cache remains readable with its validation and refresh timestamps.

External service URLs, third-party module detection paths, source attribution and the `xvm`/`XVMSymbol` font names keep their original spelling. They are compatibility or provenance identifiers, not names for Driftkings components. Do not create old-name wrapper modules or duplicate palette assets.
