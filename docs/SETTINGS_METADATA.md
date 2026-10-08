# Settings presentation metadata — phases 2–5

This is an additive presentation contract. It does not change configuration JSON,
control IDs, validation, apply policies, profiles or persistence.

## Optional control metadata

```json
{
  "id": "field_example",
  "type": "slider",
  "metadata": {
    "sourceType": "NumericStepper",
    "applyTiming": "battle"
  }
}
```

Both fields and the metadata object itself are optional:

| Field | Contract | Current use |
| --- | --- | --- |
| `sourceType` | Text naming the original template control | Selects NumericStepper and small RadioButtonGroup renderers; preserves public type |
| `applyTiming` | `live`, `battle`, `view`, `restart` | A localized visual badge; no new application logic |

The adapter supplies `applyTiming` from the existing `application_timing(component,
path)` policy. Native declarations without a known timing omit it; the UI does not
invent an immediate or restart policy. Existing descriptions and timing tooltips
remain available. Unknown renderer hints are ignored by the UI. Python rejects
unknown metadata keys so unsupported capabilities are not silently advertised.

Old schemas with only `id`, `type`, labels and value attributes remain valid.
`metadata` is omitted for controls that have none. Renderers continue to dispatch
on the existing `type`; ColorChoice, RadioButtonGroup and NumericStepper retain
their current adapters. Phases 4 and 5 extend the UI without changing those public types.

## Categories and statuses

The existing Registry `category` field carries a standard key (`general`, `battle`,
`hangar`, `system`) or a custom string/translation dictionary. The Presenter keeps
the existing schema shape. Standard categories are translated in the renderer;
custom categories retain their labels. Missing/empty categories fall back to
General. Groups follow that standard order, then custom categories in registration
order; mods retain the Registry ordering inside each group.

The TemplateAdapter derives category from the settings class module:
`templates.battle` → Battle, `templates.lobby` → Hangar,
`templates.components` → General. ProfileSettings and the framework page use
System. Authors may override the template default with optional `SETTINGS_CATEGORY`.
Existing special sound categories are retained. There is no hardcoded mod list.

Sidebar and header use `state.status[id].status` and `enabled`, existing
`restartRequired`, and schema `dependencies`. Missing dependency and error states
are warnings, not new disable/activation rules. A new optional boolean
`state.status[id].restartRequired` maps the adapter's original restart key to its
public panel ID. The original top-level array remains unchanged. Absent state
status is displayed as unknown, not as a proven active component.

## Schema invalidation

At declaration time:

```python
mod.add_slider('scale', min_value=80, max_value=140, default=100,
               metadata={'applyTiming': 'battle'})
```

After registration:

```python
mod.set_control_metadata('scale', {'applyTiming': 'view'})
mod.set_category('hangar')
```

These methods validate and copy metadata, compare against the old value, then use
the existing Registry `_notify_structure()` to increment `revision` and notify the
open window. Equal updates do nothing. Passing `{}` removes control metadata;
passing `None` to category restores the General fallback. Use these methods rather
than mutating control metadata or mod category directly after publication.

SettingsView already caches by `(registry.revision, api.language)`. A metadata or
category change rebuilds and sends schema once; subsequent edits send state only.
The same Presenter and EditSession survive a schema update, including draft values
and undo history. Category grouping and its DOM are built on schema changes only;
state changes patch existing nodes. No persistence method is involved.

## Scope and validation

Only the settings shell, optional metadata, category grouping and status/timing
presentation change. MarksOnGun modules/assets, hooks, CompatibilityManager,
SettingsService, EditSession, JSON stores and build concept are unchanged.

Checks include legacy-schema rendering, mixed categories and search, all existing
widget tests, state-only DOM identity, metadata invalidation in an open WULF view,
draft/history retention, legacy color-format preservation, Python 2.7 smoke checks
and Python/Flash contracts. Visual behavior in the actual game still requires
runtime review; a minimal DOM test cannot certify Gameface layout.

Validated locally on 2026-10-08:

- 481 Python tests: 478 passed, with the same two defaults mismatches and BOM
  test error recorded in the earlier project review; no new failing tests.
- The integrated Gameface UI test, real OpenWG 1.1.6 bootstrap test and shared
  asset bridge test passed.
- Python 2.7 smoke checks, nine Python/Flash contracts and twelve translation
  catalogs passed.
- Browser previews were inspected at 1920×1080, 2560×1440, 3440×1440,
  3840×2160 and a narrow 1000×600 viewport. These use demonstration Registry
  data, a browser bridge stand-in and Arial in place of the game's font;
  they are not game screenshots. Files are in `build/review/settings-shell-*.png`.
- No game deployment or final package build was performed in these phases.


## Optional alpha and hotkey contracts (phases 4 and 5)

Native color declarations may supply:

```python
metadata={'allowAlpha': True, 'alphaScale': 'normalized', 'alphaKey': 'opacity'}
```

`allowAlpha` defaults to false. `alphaScale` defaults to `percent`; supported values
are `percent` (0–100), `normalized` (0–1), and `byte` (0–255, rounded at the boundary).
`alphaKey` names an existing numeric control in the same mod. No field is inferred,
created or migrated. A template may use `metadata.alphaPath` instead, naming the
existing numeric `varName`; TemplateAdapter resolves it into the schema's `alphaKey`.
The adapter's persistence and original color-prefix preservation are unchanged.
Without a valid association the renderer remains an opaque legacy ColorChoice.

The picker sends `{action: 'set', mod, key, value, alpha}` only on Apply, with alpha
converted to the physical scale. Presenter validates both targets and their disabled
states before changing drafts. Existing `EditSession.set` supplies snapshots; Presenter
retains only the first snapshot for this logical operation, preserving previous history
and its 50-entry limit. Failure restores that existing snapshot and previous history.
EditSession itself is unchanged. Cancel/Escape never send this payload; no-op Apply
creates no history entry. The eventual existing Apply publishes both fields together.

`allowModifierOnly: true` explicitly permits modifier-only hotkey capture. Its default
is false. Existing stored combinations remain valid, and capture still uses the existing
native keyboard/mouse service. Escape cancels capture.

All metadata changes still use `set_control_metadata`, which increments the existing
Registry revision and notifies open views only when the metadata actually changes.
No settings value, dirty state or persistence revision is introduced for UI metadata.

## UI implementation and validation (phases 4 and 5)

`colors.js` contains pure format and alpha conversion helpers. `modal.js` owns only UI
lifetime/focus, including the existing profile, installed-mod and confirmation dialogs.
Widgets handle their own keys; TextInput retains native cursor navigation. Disabled
controls are removed from tab order and restored when enabled.

The color spectrum uses Canvas feature detection, drawn once per opening. Missing or
failing Canvas uses CSS gradients with the same mathematical mouse/keyboard sampler.
Both follow the supplied black–hue–white spectrum reference. Arbitrary RGB values remain
editable through HEX; opening or cancelling never changes the original color. Its cursor
position is approximate for RGB values outside the spectrum's black/hue and hue/white
edges. Only an explicit spectrum interaction samples a new color. Drag updates cursor,
HEX and previews, never the backend or spectrum bitmap.

Validation includes prefixes/lowercase/invalid input, alpha conversion at 0/50/85/100,
Canvas rendering once, CSS fallback, local drag, modal Tab/Shift+Tab, Cancel/Escape/focus
return, widget keys and native text cursor, modifier-only opt-in, legacy schema, atomic
undo at the history limit, rejected/disabled alpha and rollback after a failed second set.
Browser preview: `build/review/color-picker.png` (standalone UI fixture, not the game).
Gameface runtime behavior still needs an in-game check; no deployment or final build ran.


Final phase 4/5 checks on 2026-10-08: 488 Python tests, 485 passing; the same
three pre-existing failures remain. Integrated settings UI, real OpenWG bootstrap,
shared bridge, Python 2.7 smoke and all nine Python/Flash contracts passed.
