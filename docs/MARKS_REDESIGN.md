# MarksOnGun — audit and phases 8–11

## Audit: calculation ownership and equivalence

The Battle/Hangar/TechTree presentation adapters were compared with their underlying
components, templates, stats/vehinfo.py and existing MoE helpers before implementation.
They do not share one interchangeable prediction model.

| Concern | Battle | Hangar / TechTree | Decision |
| --- | --- | --- | --- |
| Damage percentage | Starting dossier/cache percent, then current-battle estimate | Dossier damageRating / 100; TechTree clamps to 0–100 | Keep acquisition and percentage policies |
| Combined damage | Current damage + max(radio,track,stun) | Average damage + max(track,radio,stun), converted to int | Share addition/max only, preserve input order and caller conversion |
| Integer target rounding | int(ceil(value)) | Same operation | Extract ceil_damage |
| Tens rounding | int(ceil(ceil(value/10.0))*10) | Same operation | Extract ceil_damage_tens verbatim |
| Threshold search | Incremental 0.1 loop, cap 30000, threshold <100.001 | Similar loop, plus guards for zero percent/damage and safe defaults | Do not merge the guarded/unguarded routines |
| Next-percent tables | floor(percent)+1, levels 20/40/55/65/85/95/100, adjustments | Similar table but different invalid-input protection | Keep each implementation |
| Battle forecast | EMA k=2/101 and interpolation between two cached samples | Not the Hangar goal forecast | Unchanged |
| Hangar goal | Not used by Battle forecast | Proportional EMA * threshold / percent rounded to tens; eligibility tier V and retained awards | Unchanged |
| Next Battle target | Existing getColor/levels/damages selection, including half-percent option | Hangar goal selection and dossier EMA approximation | Do not unify |
| Delta | Estimated Battle percent minus starting percent, presentation only | History trend over configured observed-battle period, rounded to two decimals | Preserve distinct meanings |
| History | Existing account/vehicle cache, sample dates | Existing snapshot store, battle counter rules, 21 samples and period trend | Neither history format nor acquisition changed |
| Vehicle/session | Attached battle vehicle public marks, events and worker state | Current vehicle/dossier, random-mode stats; TechTree own dossier cache | Keep all data sources |
| External stats | Existing data sources | vehinfo supplies metadata/WN8/XVM/XTE expected values; not a interchangeable MoE forecast | No external calculation/data change |

The pure `core/marks_calculator.py` imports only math. It holds only the three proven
operations. Equivalence tests ran before replacing calls and include every hundredth
from 0 to 100, requested boundaries, near-integer/ten boundaries, and damage/assist
cases. Numeric types/tie ordering are preserved. The repeated candidate percentage
clamps have differing invalid-input semantics, so no broad clamp was extracted.

No historical cache, callback, hook, data acquisition, view, settings or WoT object
was moved into the calculator. Percentage forecast rounding and formulas are unchanged.

## Visual stack and final presentation

Battle is the existing owned Scaleform/DAAPI overlay label. No active Wulf battle
view/resource was confirmed for this HUD, so no speculative Gameface transport was
introduced. `OverlayElement` recognizes optional `marks` presentation data and uses
`MarksCard`; otherwise it continues rendering the exact legacy label/custom format.
The same transport, dragging, alignment, visibility and scale lifecycle remain.
Legacy text is still supplied, including fallback for a previously compiled SWF.

Python's `views/marks_model.py` formats already-calculated data and supplies signed
symbols, strings, progress ratio, target states and color tokens. AS draws fields,
bar/milestones/cursor and displays those values. It performs no MoE forecast or target
calculation. Uncertain estimates show -- and an unknown delta rather than a fabricated
percentage. Modern payload updates are deduplicated in the existing presentation adapter.

- Compact: stars, estimated MoE percent and signed delta, milestones, combined/target.
- Normal: the same core hierarchy with a combined-damage caption.
- Detailed: additionally starting/current MoE, direct damage, largest assist and the
  existing 65/85/95 targets. 100% remains a possible additional target, never a fourth star.

Hangar remains the existing Gameface card and live controller. It shows percent/delta,
star awards/progress, milestone bar, achieved status, EMA/goal estimate, period history
and existing stats. At >=95% (or an already earned third mark), the header says the third
mark is achieved instead of describing 95% as the next goal. Displayed stars reuse the
existing goal semantics: max(retained awards, thresholds reached), capped at three.
The stored earnedMarks value is not changed. Compact uses the original compactMode and
hides supporting details/stats; no second toggle is introduced. Vehicle changes patch
fields and preserve the card DOM. The delta's title states the observed period; it is
not mislabeled as a single-battle forecast/result.

TechTree remains its existing Gameface integration/node badges. Changes are limited to
font/spacing, subtle background/border, a star indicator and percent styling. Dossier
queries, cache, colored-name option, payload and hooks remain unchanged.

Shared color tokens live in `shared/marks_tokens.css`; equivalent numeric tokens are
supplied to AS by the Python presentation model. Literal CSS declarations provide a
fallback where CSS custom properties are unavailable. Background rgba(18,21,24,.75),
border white .10, text #E8E4DA, muted #969BA3, positive #67C56A, negative #E05454 and
accent #D98219 are used. Existing palette/custom card colors continue to be respected;
only shipped visual defaults were harmonized, without migrating user configs.

## Additive configuration

Battle `displayMode` uses the existing numeric dropdown convention:
0 Legacy, 1 Compact, 2 Normal, 3 Detailed. Default is 0. Existing UI preset indices
0–11, battleMessage and battleMessageAlt remain unchanged. Optional booleans showMarks,
showDelta, showDamage, showProgress and showTargets default True and apply only to the
modern presentation. Scale reuses battleMessageSizeInPercent; opacity reuses panel.alpha.
No parallel setting/service or new persistence is introduced. All 12 language catalogs
retain existing content and add matching keys; new labels are English fallbacks with
Portuguese translations in the Portuguese catalog.

Hangar reuses compactMode, card, panel, existing colors and APPLY_TIMING=LIVE.
Its shipped card defaults use the shared tokens. No user config is automatically
converted, and no settings/persistence/APPLY_TIMING implementation changed.

## Files

Added: core/marks_calculator.py; views/marks_model.py; overlay/MarksCard.as;
Gameface shared/marks_tokens.css; tests/test_marks_equivalence.py; this report.

Extended: battle/gun_marks.py; lobby/gun_marks.py; views/battle/gun_marks.py;
views/hangar/gun_marks.py and gun_marks_tree.py (shared style loading only);
overlay/OverlayElement.as; Gameface MarksOnGunHangar and MarksOnGunTechTree assets;
settings/settings_data.py; settings/templates/battle/gun_marks.py; both shipped Battle
and Hangar Marks default JSON files; twelve existing i18n catalogs; hangar_updates_test.js;
flash/HudVisibilityTest.as. Lobby/Hangar goal/history and TechTree acquisition are unchanged.

EditSession, SettingsService, persistence code, CompatibilityManager, BattleCapabilities,
Core, stats/vehinfo.py, build scripts/concept and unrelated hooks were not changed.
Earlier approved changes remain in the workspace.

## Validation and artifacts

Equivalence/presentation tests cover percentages/thresholds/rounding, 0–3 marks,
positive/negative/zero/unknown deltas, target below/reached/above, missing data, retained
awards, vehicle switch, legacy defaults, 12 presets and stable modern payloads.
Gameface tests exercise compact switching, achieved status, stars, vehicle patching,
unchanged-payload/no-DOM-work behavior and existing disposal/recreation.
AIR tests compile and run the actual AS renderer, verify reusable fields, fallback
custom text, four viewport anchors and existing UI scale. This is a local test build,
not the final mod build and not a published/replaced game SWF.

Local artifacts in build/review:
- marks-battle.png: capture of the actual AS renderer in AIR;
- marks-1920x1080.png, marks-2560x1440.png, marks-3440x1440.png, marks-3840x2160.png:
  browser fixtures using the production Hangar/TechTree scripts and UI scaling;
- marks-hangar-tree.html: interactive browser fixture.

These are local previews, not client screenshots. Real client/replay validation remains
necessary before publishing the new SWF or selecting a different Battle transport.
No final build or deployment was run.


Final validation on 2026-10-08: 519 Python tests, 516 passing, with the same two
pre-existing JSON/default mismatches and BOM-related test error. All ten new Marks
Python tests passed. Integrated Settings and Hangar/TechTree Gameface tests passed;
AIR HUD suite passed 35 assertions; existing Python 2.7 smoke, dedicated Marks
Python 2.7 smoke and all nine Python/Flash contracts passed. Diff whitespace checks
passed. Previews were inspected at all four requested resolutions.
