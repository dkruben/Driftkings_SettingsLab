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

All project Markdown files live under `docs/`, including the [README](README.md), [contribution guide](CONTRIBUTING.md) and feature guides. The Git ignore rules include Markdown only; local JSON/CSV snapshots, study scripts and generated outputs remain excluded. Third-party dependencies and generated build trees keep their own files and are not project documentation.

Dated reviews retain their original evidence, line references, counts and conclusions. Update notes distinguish historical findings from the current implementation. No new source audit or statistical study is implied by reorganizing a report. Research prototypes under `wn8-study/` are not additional production ratings; reproduction requires the original local scripts and data.

## Current implementation changes

- The clock is configured under General settings, in `main.json` through `clock.enabled` and `clock.formats`.
- HangarEfficiency is removed. Use vehicle carousel statistics, service-record ratings or the relevant Marks of Excellence panel.
- Vehicle markers use the five-file XVM-style layout without XMQP, team/state/ALT contexts and an editable tank sample. The property column has its own scrollbar.
- ActionScript fields use the client font library. Marker `xvm`/`XVMSymbol` aliases resolve to `$FieldFont`; legacy private glyphs map to a supported bullet. Fixed colours use `#RRGGBB` with existing numeric converters.
- WN8 uses random-battle statistics; WNX uses its own assistance-aware calculation and expected values. The EU battle overlay defaults to WN8, EFF and DIFF; WNX remains configurable.

For current commands and release procedures, use [CONTRIBUTING.md](CONTRIBUTING.md). For feature guides and historical reports, use the [documentation index](README.md#documentation).
