# Regional languages

The catalogs are UTF-8 `.yml` resources in `mod/res/mods/driftkings/text/<code>.yml`,
packaged under `res/mods/driftkings/text/` and loaded through the game VFS. The
format is described in [contribution guide](../../CONTRIBUTING.md#translation-resources).

Each catalog holds the component text (`<component>.<key>`) and the settings panel
text (`panel.<key>`). The loaders are `driftkings/i18n/resources.py` (resources),
`driftkings/i18n/__init__.py` (components) and `driftkings/i18n/panel.py` (panel).
User overrides remain JSON: `mods/configs/driftkings/i18n/<code>.json` for component
sections and `mods/configs/driftkings/locales/<code>.json` for panel strings.

Component section names use the canonical settings names, such as
`third_person_zoom` and `sixth_sense_alert`. Older override files and section
names are no longer imported or converted.

Language codes are resolved by `driftkings/locale_support.py`. `build_data/locales.json`
records the regional language lists, source, translation method and coverage.

The Wargaming portal selectors list:

- EU: Czech, German, English, Spanish, French, Hungarian, Italian, Polish,
  Russian, Turkish and Ukrainian.
- NA: English, Latin American Spanish and Brazilian Portuguese.
- ASIA: English, Japanese, Korean, Thai, Vietnamese, Simplified Chinese
  (Singapore) and Traditional Chinese.

These are portal language lists, not a guarantee that each regional client
distributes every corresponding language pack. Spanish and Portuguese regional
variants reuse the existing `es` and `pt` catalogs. `zh-SG` resolves to `zh_cn`;
`zh-TW` and `zh-HK` resolve to `zh_tw`. The Chinese scripts stay separate.

All 18 catalogs contain the same 1491 component keys and 170 panel keys as
`en.yml` (validated 26/10/2026). Missing entries and prose still in English were
completed with machine translation. Existing localized text was preserved. New
translations need native-speaker review; complete key coverage is not a
linguistic quality rating.

`python build_tools/validate_locales.py` checks exact key coverage, value types,
nonempty strings, formatting macros, HTML and colors. It also reports values that are still
an English phrase (`untranslated`); `tests/installer/test_locales.py` keeps that at zero,
except for names listed in `ENGLISH_NAMES`. The compiler runs this
validation before building. Add new English keys to every catalog in the same
change. Names and identifiers may legitimately be identical across languages.
The loader retains the English fallback and user JSON overrides.
