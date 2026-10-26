# Documentation status

Updated: 26 October 2026. Commands and source paths in these guides are relative to the repository root unless explicitly stated otherwise.

## Release baseline

- Beta: [0.1.3-beta.2](https://github.com/dkruben/Driftkings_SettingsLab/releases/tag/v0.1.3-beta.2), built from `aec3da8` with 11 verified assets and an Ed25519-signed updater manifest.
- Stable: [0.1.2](https://github.com/dkruben/Driftkings_SettingsLab/releases/tag/v0.1.2).
- Game target: WoT `2.4.1.0`, Wargaming EU/NA/ASIA. Build source: configured NA installation; source reference: EU `2.4.1.5498`.
- Canonical defaults: author's EU profile, including clock fields, panel positions, carousel and marker layouts. Settings-window scale: 140%; opacity: 94%. Existing personal configuration takes precedence.

## Verified checks

The release passed [GitHub Actions](https://github.com/dkruben/Driftkings_SettingsLab/actions/runs/40394556691), Python 2.7 package verification and the installer build. The baseline contains 413 Core and 27 settings-panel tests on Python 2.7/3, 33 installer tests on Python 3, and the Gameface regression suites. Eighteen language catalogues contain 1491 component keys and 170 panel keys, with no unapproved English-only values reported by the validator.

The all-pages settings test opens and applies every current feature definition with unchanged values. Marker tests cover property scrolling, font aliases, invalid references, sample toggles and limits. Source defaults and the generated Python fallback are synchronized. These checks do not establish pixel-perfect rendering in the client: the latest marker, font and layout changes still need visual acceptance in game.

## Documentation policy

The [README](../README.md) and [contribution guide](../CONTRIBUTING.md) live at the repository root. Feature guides and historical reports live under `docs/`. The Git ignore rules include Markdown only; local JSON/CSV snapshots, study scripts and generated outputs remain excluded. Third-party dependencies and generated build trees keep their own files and are not project documentation.

Dated reviews retain their original evidence, line references, counts and conclusions. Update notes distinguish historical findings from the current implementation. No new source audit or statistical study is implied by reorganizing a report. Research prototypes under `wn8-study/` are not additional production ratings; reproduction requires the original local scripts and data.

## Current implementation changes

- The clock is configured under General settings, in `main.json` through `clock.enabled` and `clock.formats`.
- HangarEfficiency is removed. Use vehicle carousel statistics, service-record ratings or the relevant Marks of Excellence panel.
- Vehicle markers use the structured five-file layout without XMQP, team/state/ALT contexts and an editable tank sample. The property column has its own scrollbar.
- ActionScript fields use the client font library. Marker `xvm`/`XVMSymbol` aliases resolve to `$FieldFont`; legacy private glyphs map to a supported bullet. Fixed colours use `#RRGGBB` with existing numeric converters.
- WN8 uses random-battle statistics; WNX uses its own assistance-aware calculation and expected values. The EU battle overlay defaults to WN8, EFF and DIFF; WNX remains configurable.

For current commands and release procedures, use [CONTRIBUTING.md](../CONTRIBUTING.md). For feature guides and historical reports, use the [project overview](../README.md).

## Naming changes after beta.2

The source branch uses descriptive marker/statistics module names and the **Driftkings** palette at index 1. New templates use `stat-available`; installed profiles and statistics caches retain read compatibility. Original font names, provider URLs, integration IDs and upstream credits are preserved. These source changes do not replace the already-published beta.2 assets.

## Colour format after beta.2

Colour settings and defaults use `#RRGGBB`. Legacy numeric prefixes and bare hex strings are no longer accepted. Native APIs still receive numeric RGB/ARGB values through the existing converters. The settings panel saves hash-prefixed strings directly; HTML templates do not prepend another hash. Tests cover rejection of legacy strings and unchanged open/apply behaviour for the corrected defaults.

## Python Gameface architecture after beta.2

The development branch centralizes Python Gameface adapters under `driftkings/gameface`, with shared `core.py`, `payloads.py`, `registry.py`, and separate `batalha`/`hangar` packages. The 14 interface contracts still come from `interface_catalog.py`; native resource IDs and visual assets are preserved. Scaleform remains under `views`; functional calculations and data collection remain in the feature modules. See the [migration inventory and execution log](PLANO_GAMEFACE.md). Client acceptance checks remain pending; this refactor does not replace the published beta.2.

Gameface refactor validation: 429 Core tests on Python 2.7/3, 27 settings tests on both runtimes, 33 installer tests, JavaScript/lint and the native debug build passed. [Source CI passed for c7189f8](https://github.com/dkruben/Driftkings_SettingsLab/actions/runs/40421997019). The build validates 301 Python modules; visual assets and all non-Python catalogue fields are unchanged.
