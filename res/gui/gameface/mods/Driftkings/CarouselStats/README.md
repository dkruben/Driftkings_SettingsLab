# CarouselStats (Gameface)

Per-vehicle **own-player random-battle statistics** on the EU 2.4.0.1 hangar carousel. No SWF is required. Each native card is matched by its compact descriptor (`vehicleCard-<intCD>`), including recycled cards and double-row layouts. This integration must be checked inside the client after installation.

## Configuration

Open CarouselStats in the mod settings menu, or edit `mods/configs/Driftkings/CarouselStats/CarouselStats.json`. Four independent fields are available. Each has:

| Setting suffix | Meaning |
| --- | --- |
| `Enabled` | Show or hide this field |
| `Format` | Text with macros, for example `WN8 {{wn8}}` |
| `Icon` | Icon macro or local game resource path; empty hides the icon |
| `X`, `Y` | Offset from the card's top-left, in game UI units |
| `FontSize`, `IconSize` | Text and icon size |
| `Color` | `#RRGGBB` or a color macro such as `{{c:wn8}}` |

Prefixes are `slot1` through `slot4`. Global `showIcons` hides all field icons. `colorRating` selects the existing DriftkingsCore table: **0 NoobMeter, 1 XVM, 2 WotLabs**. No color thresholds are duplicated in this mod. Fields are clipped to the card; reduce offsets or font sizes if content does not fit the selected carousel layout.

```json
{
    "slot1Enabled": true,
    "slot1Format": "WN8 {{wn8}} / X {{xwn8}}",
    "slot1Color": "{{c:wn8}}",
    "slot1Icon": "",
    "slot1X": 4,
    "slot1Y": 4,
    "slot1FontSize": 12,
    "slot1IconSize": 14
}
```

This is an example field, not a replacement for the entire configuration file.

## Value macros

| Macro | Value |
| --- | --- |
| `{{battles}}` | Random battles in this vehicle |
| `{{winRate}}` | Win percentage, without the `%` suffix |
| `{{hitRate}}` | Hits / shots fired × 100, without the `%` suffix; a hit does not necessarily penetrate or cause damage |
| `{{avgDamage}}` | Average damage caused |
| `{{avgReceived}}` | Average damage received |
| `{{damageRatio}}` | Damage caused / damage received |
| `{{damageHP}}` | Average damage / vehicle's current maximum HP |
| `{{avgAssist}}` | Assistance average reported by the game's dossier |
| `{{avgBlocked}}` | Average damage blocked by armor |
| `{{avgStun}}` | Average stun assistance |
| `{{avgFrags}}` | Average destroyed vehicles |
| `{{avgSpotted}}` | Average enemies spotted |
| `{{avgCapture}}`, `{{avgDefence}}` | Average capture / defence points |
| `{{eff}}` | Classic Efficiency Rating calculated for this vehicle |
| `{{wn8}}` | WN8 calculated for this vehicle |
| `{{xeff}}`, `{{xwn8}}` | Corresponding XVM scale, using DriftkingsStats |
| `{{marks}}` | Marks percentage, tier V+ |
| `{{mastery}}` | Best mastery class: 0 none, 1 III, 2 II, 3 I, 4 Ace |

Use `{{avgFrags:.1f}}` to request one decimal, `:.0f` through `:.3f` for zero to three decimals, or `:d` for an integer. Values are plain text, not HTML. Missing data, unknown macros, missing WN8 expected values and zero denominators display `--`; absent statistics are never presented as a zero rating.

WN8 uses the per-vehicle expected values already loaded by DriftkingsStats (`wn8exp.json`). EFF uses this vehicle's tier and random-battle averages in the classic formula:

```text
damage * 10 / (tier + 2) * (0.23 + 0.02 * tier)
+ frags * 250 + spotted * 150
+ log(capture + 1) / log(1.732) * 150 + defence * 150
```

These are vehicle ratings, not account-wide ratings. The HP ratio uses the tank's current configuration, not historical HP from each battle. Mastery and marks are achievement records; the other counters use the random-battle dossier.

## Colors and icons

Supported color macros: `{{c:wn8}}`, `{{c:eff}}`, `{{c:xwn8}}`, `{{c:xeff}}`, `{{c:winRate}}`, `{{c:avgDamage}}`, `{{c:marks}}`, `{{c:damageRatio}}`, `{{c:damageHP}}`. They use the Core's `wn8`, `eff`, `x`, `winrate`, `tdb`, `mog`, `damageRatio` and `damageHP` categories. Missing values use gray. Metrics without a Core category can use a fixed color.

Native game icon macros: `{{icon:damage}}`, `{{icon:assist}}`, `{{icon:blocked}}`, `{{icon:wins}}`, `{{icon:battles}}`, `{{icon:mastery}}`.

A custom icon can use `gui/maps/icons/MyIcons/damage.png` or `coui://gui/maps/icons/MyIcons/damage.png`. The resource must already exist in the client or be supplied by a resource mod. Web URLs and executable URLs are not loaded. Missing images are hidden.

## Implementation and validation

- Python: `source/scripts/client/gui/mods/mod_CarouselStats.py`.
- Visuals: `carousel.js` and `carousel.css` in this directory.
- Resource map: `res/mods/configs/res_map/DriftkingsCarouselStats.json`.
- Dependencies: the unified Driftkings package and ModsListAPI.
- Only visible card IDs are requested, with a limit of 120 per request. Dossiers are cached and invalidated on item-cache synchronization or account changes. No other-player statistics are requested by this module.
- Layers do not intercept clicks. Model callbacks, observers and injected layers are removed when the view is disposed.

In-client checks still required: scrolling, one through four carousel rows, filters, resizing, switching game modes, post-battle updates, and coexistence with other carousel mods. `rows: 0` retains automatic selection. The native client model stays at one/two; the bridge groups virtualized cards and handles keyboard navigation using the effective count (up to four).

Win-rate color bands in the Core: below 46%, 46–48%, 48–52%, 52–56%, 56–60%, and 60–100%. These are project defaults using each selected table's existing X-scale colors. Upper bounds are exclusive, except the final band includes 100%.

Damage-ratio and damage/HP color bands are independent Core categories, both defaulting to below 0.50, 0.50–0.75, 0.75–1.00, 1.00–1.50, 1.50–2.00 and 2.00+. Each uses the selected table's existing X-scale palette. These are project defaults. A field has one color: use separate fields for separately colored ratios. The default fourth field is colored by `{{c:damageRatio}}`.
