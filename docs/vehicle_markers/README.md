# Integrated vehicle markers

The Flash runtime lives in `driftkings/flash/battle/vehicle_markers`, with
functional helpers in `driftkings/core/vehicle_markers`, and is owned by
`battle.vehicle_markers`. It incorporates the independently tested VM_TEST 0.0.14
implementation. VM_TEST is not a build or runtime dependency.

The build reads `battleVehicleMarkersApp.swf` from the game package identified in
`native-lock.json`, verifies its SHA-256, patches the native methods and appends
the helper ABC with a unique name after the native ABC. Embedded font resources
and their class bindings are copied with collision-free character IDs. A different native movie
requires reviewing the patch and lock before building. RABCDAsm's `abcexport`,
`rabcdasm`, `rabcasm` and `abcreplace` are required; set `DK_RABCDASM_HOME`,
`rabcdasm_home` in `build_data/toolchain.local.json`, or `--rabcdasm-home`.

`DriftkingsVehicleMarkersFlash.as` is the facade whose static entry points the patched
native movie calls. Its helpers live in `driftkings/vehiclemarkers` (`VMState`, `VMText`,
`VMDamage`, `VMHealthBar`, `VMIcons`) and compile into the same single helper ABC; the
marker movie keeps its own colour and shadow code rather than sharing classes with the
battle SWF.

Configurable ActionScript text fields allow shared-library, device and embedded font
lookup with `embedFonts = false`. Keep `$FieldFont` and `$TitleFont` as client aliases.
The real symbol fonts are included in both Flash movies and Gameface; configured names,
Unicode and HTML entities are preserved. Font resources, credits and coverage limits are
listed in [Fontes e caracteres](../FONTES.md).

Configuration lives in the active profile's `vehicle_markers` directory and
uses a structured five-file marker layout, without XMQP: `markers.json` plus
`markersAliveNormal.json`, `markersAliveExtended.json`, `markersDeadNormal.json`
and `markersDeadExtended.json`. Transactions preserve the five files together.

`markers.json` holds the switch (`enabled`), `debug`, `colorRating`,
`ratingType`, `turretMarkers`, `colors` and, as in `markers.xc`, the wiring of
each team, state and mode to a block of a state file:

```json
{"markers": {"enabled": true,
  "ally": {"alive": {"normal": "${markersAliveNormal.json:ally}", "extended": "${markersAliveExtended.json:ally}"},
           "dead": {"normal": "${markersDeadNormal.json:ally}", "extended": "${markersDeadExtended.json:ally}"}}}}
```

Each state file has local `def` templates and complete `ally` and `enemy`
blocks: `vehicleIcon`, `healthBar`, `damageText`, `damageTextPlayer`,
`damageTextSquadman`, `vehicleDist`, `contourIcon`, `levelIcon`, `actionMarker`,
`hoverMarker` (with `glow`), `vehicleStatusMarker`, `damageIndicator` and
`textFields`. Fields and templates reference definitions with `"${def.name}"` or
`{"$ref": {"path": "def.name"}}`. Geometry uses fixed boxes: text fields are 140x100
boxes anchored at `x` by `align`, damage text 200x100 boxes, the distance a
100x100 box, the class icon moves its container by `x`/`y` plus `offsetX`/
`offsetY` (`maxScale` is unused in this schema), and the damage indicator text sits at
`x + 14`, `y - 14`. `{{position}}` is the vehicle's place in its team list from
the first roster and `{{battletype}}` is empty in random battles. The entity `&#x115;` is preserved and drawn using the configured font's own glyph map.

`core/vehicle_markers/schema.py` converts the files to the runtime profiles; the
editor uses the same mapping in `vehicle_markers_model.js`. The earlier
seven-file layout is converted once: its general switches and colours are kept,
the layouts start from these defaults, and the old files remain as `.v2.bak`.
The native marker settings getter resolves visibility per vehicle, so destroyed
allies and enemies can differ even though the client exposes a shared dead
settings group. Icon geometry is restored before native updates to avoid
carrying offsets across ALT, death or observer changes.

`markers.json` selects the shared `colorRating` palette. Marker team colors use
its `system` table, percentage HP uses `hp_ratio`, and floating damage uses its
`damage` ownership colors. The runtime and sample use the same resolved tables;
HP thresholds follow the shared strict upper-bound comparison and last-band
fallback. Explicit marker color overrides remain supported and take priority.

Ratings use the existing shared statistics cache and worker, including when the
roster itself is hidden. The statistics switch and minimum battle count still
apply. `ratingType` selects `wn8`, `wnx` or `eff` for `{{r}}` and `{{c:xr}}`;
the individual metrics and colors are also available. `{{xr}}` is the normalized
normalized rating where the statistics module provides one (WN8/EFF); no normalized WNX
value is invented. Anonymized or unavailable statistics remain unavailable.

The EU-profile alive normal layout uses a coloured `!` in `XVMSymbol`, and ALT shows the
selected rating. Both `xvm` and `XVMSymbol` use the original symbol font in the runtime
and the editor. `&#x115;` retains its original glyph. Existing custom field arrays are preserved: use **Add rating** in the
editor to insert the normal or ALT preset in any of the eight contexts.

Text fields support structured `name`, `textFormat` (font, size, color, bold,
italic), `{{stat-available?100|0}}` opacity, fallbacks such as `{{r|--}}`, and basic
numeric formatting (`{{r%d}}`, `{{winrate%.1f}}`). A compatible ALT example is:

```json
{"name":"Rating", "enabled":true, "x":-100, "y":-115, "width":200, "height":25,
 "alpha":100, "align":"center", "format":"{{r}}",
 "textFormat":{"font":"$FieldFont", "size":13, "color":"{{c:xr}}", "bold":false, "italic":false}}
```

Marker statistics travel as a separate packet over the existing native settings
entry point, intercepted before it can replace native settings. Refreshes only
update text and formatting, preserving health-bar trails and damage animation.
Ratings reuse the shared statistics worker and cache. Account WNX uses the
existing WNX calculator with random-only vehicle counters and assistance; missing
expected values or incomplete battle/assistance coverage produce no rating.
The random vehicle counters are documented in the
[Wargaming API reference](https://developers.wargaming.net/reference/eu/wot/tanks/stats/).

The hangar settings editor uses a native T32 shop image and an HTML marker sample.
WG's `MarkerSettings.as` in the pinned 2.4.1 source uses a T32 sample with level 8
and 1550 maximum HP; the editor follows that approach. It adds editable text,
normal/ALT, team and alive/destroyed selectors, HP presets, shared-template editing and a raw JSON view. Damage settings remain editable; the redesigned sample does not simulate damage animation.
The sample renders sanitized Flash-style HTML. It approximates Flash rendering;
native icon artwork and font metrics must still be checked in-game.

Drafts use the existing settings session: Apply/Save publishes them, and Cancel
discards them. Marker settings are available in the hangar and apply next battle.
Only regular random and training managers receive custom presentation. Unknown
modes and KillCam keep native settings. Do not install the standalone VM_TEST
WOTMOD alongside this package: both replace the same native Flash resource.

Validation inherited from VM_TEST includes normal/ALT, damage ownership, replays,
real battles, observed-vehicle changes after death and special-mode fallback.
The integrated settings editor requires its own in-game visual acceptance test.

## Damage authors and explosion messages

Every damage context can override `sources.player`, `sources.squad` and
`sources.other`. These inherit the common context style and can independently
set visibility, `format`, `blowupMessage`, font, position, opacity, duration, rise,
colors and maximum simultaneous numbers. Counts are capped separately by author;
one author's animation does not evict another's. For example, under
`damageText.enemy.alive.normal`:

```json
{"sources":{"player":{"x":-80,"duration":2.5,"rise":60},
            "squad":{"format":"Squad: -{{dmg}}","duration":1.5},
            "other":{"enabled":false}}}
```

`blowupMessage` is used only for the native `explosion` damage type or negative
health signal, not an ordinary hit reaching zero HP. Killing hits use the
destroyed context. `{{i18n:blownUp}}` (or the legacy `{{l10n:blownUp}}`) is localized by Driftkings; damage messages
also accept `{{dmg}}`, `{{dmg-ratio}}`, `{{dmg-kind}}`, `{{dmg-source}}` and
`{{c:dmg}}`. The editor selects the author and can simulate an ammo-rack explosion.

## Distance and conditions

`{{distance}}` / `{{dist}}` return rounded meters from the attached live vehicle
(or the avatar position while observing) to the current target entity. There is
no last-known-position fallback: `{{distance|--}} m` displays missing data safely.
When a distance macro is used, updates run at 0.2-second intervals; statistics
loads remain throttled to once per second. The editor includes an **Add distance**
preset and a distance slider.

Text, font colors and field opacity support nested conditionals, `!`, `&&`, `||`
(AND before OR), and `<`, `<=`, `>`, `>=`, `==`, `!=`. Conditions use the known
macros, numeric/Boolean literals and quoted strings. They do not evaluate code,
arithmetic, attributes or function calls. Examples:

```json
{"alpha":"{{enemy&&hp-ratio<25?100|0}}",
 "format":"{{alive&&distance<=500?{{vehicle}} ({{distance}} m)|}}",
 "textFormat":{"color":"{{squad?#FFB964|{{c:team}}}}"}}
```

Flags include `alive`, `dead`, `ally`, `enemy`, `player`, `squad`, `anonym` and
`stat-available`; `vtype` uses LT/MT/HT/TD/SPG. Numeric comparisons with unavailable data
return false. Opacity results are clamped to 0..100, with invalid numeric results
hidden. The sample exposes player/platoon/anonymization flags, HP, team, state and
statistics availability for checking these conditions.


### Remaining native marker controls (without XMQP)

Health bars accept `fill.alpha` independently of `alpha`, and
`gradient: {"enabled": true, "color": "{{c:hp}}", "angle": 0}`. The primary
`color` is the first gradient endpoint. The damage trail accepts `{{c:dmg}}`;
it snapshots the event author's colour even when floating damage is disabled.
Current defaults use flat filling; `fill.alpha` controls the configured fill opacity. Replay seeks clear event snapshots.

The scoped `icons` tree also accepts `actionMarker`, `hoverMarker`,
`vehicleStatusMarker`, `damageIndicator`, `damageIndicatorText`, and
`hitExplosion`. Each uses enabled/x/y/scale/alpha/deadAlpha. Positions default
to native coordinates; opacity multiplies through a filter so native show/hide
and animation alpha remain under the game's control. The preview's sample
indicator symbols illustrate geometry and opacity rather than native artwork.

`{{turret}}` displays the configurable `turretMarkers.highVulnerability`,
`lowVulnerability`, or `unknown` string for a visible stock turret. The flags
`{{stock-turret}}` and `{{turret-vulnerability}}` support conditions. Classification
compares stock/top turret health and available gun prices from client resources;
unknown data is never treated as a top or stock turret. Equal-health alternate
turrets and top turrets have no vulnerability symbol. No external service is used.

Each state file can contain reusable objects under `def`. Its fields
can use `{"$ref":{"path":"def.example"},"x":20}` to inherit a definition and
override properties, or `${def.example}` for a whole value. Resolution is local,
bounded, rejects cycles/missing paths, and never rewrites saved references.
The editor can save the selected field as a named template, add linked copies,
and edit templates in their own tab. Template names use letters, digits, `_`, `-`.
External file-reference syntax and XMQP are deliberately unsupported.

These additions compile against the pinned EU 2.4.1 movie. Native event animation,
stock/top turret variants and edited templates still require replay acceptance.

## Property scrolling and current defaults

The structured property column has a fixed 470 UI-unit viewport and its own scrollbar through `DK.dom.scrollbar`. Wheel events stay in that column; dragging reaches the final property. The scrollbar refreshes after tab/group changes and resize, hides when content fits, and removes deferred updates and resize listeners on disposal.

The beta 0.1.3-beta.2 defaults follow the EU profile: normal-mode distance fields are disabled, level and contour icons are enabled, and the normal rating template uses `XVMSymbol` with custom `!` text. Preserve the editable font name and original glyphs through the adapter boundary. Fixed colours use `#RRGGBB`; ActionScript uses the existing numeric conversion helpers.

Run `npm --prefix build_tools/javascript test` for the preview/editor and Python/JavaScript adapter mapping, and the Core suite for geometry, references, aliases and damage policies. See the [contribution guide](../../CONTRIBUTING.md) and [current status](../STATUS.md). Paths in this guide are relative to the repository root or the `driftkings` client package as indicated.

## Naming and source attribution

The project palette is named **Driftkings**, retaining index 1 and the existing thresholds/colours. New macros use `{{stat-available}}`; the old macro spelling is accepted only for profile compatibility. Source code lives in `core/vehicle_markers/schema.py`, not a provider-named module.

The layout and rating-scale references were originally adapted from XVM's `default_wg` configuration. This attribution is retained; the `xvm` and `XVMSymbol` font names also remain valid. Provider URLs and external-mod detection identifiers are unchanged where required for interoperability.
