# Hangar clock and preferences

The clock is configured in **General settings**, stored in `mods/configs/driftkings/<profile>/main.json`. Hangar preferences still control hangar header buttons and widgets; they do not own the clock settings.

## Clock configuration

- `enabled` is the General section switch; `clock.enabled` switches the clock itself.
- `clock.formats` is a list of fields. Each field accepts `x`, `y`, `width`, `height`, `screenHAlign`, `format`, `textFormat` and `shadow`.
- `format` contains the supported Flash-style HTML, time/date directives or a background image. `textFormat` supplies alignment and colour; `shadow` supplies visibility, colour, opacity, blur, angle, distance and strength.
- The settings panel exposes each field in its own tab. Apply/Save uses the normal editing session. The EU-profile default contains a background-image field and a separate time/day/date field.

Legacy `clockStyle`, `clockX`, `clockY`, `clockScale`, `clockSeconds`, `clock24Hour` and single-format options are not current controls. Older configuration folders are not imported automatically.

## Sources and lifecycle

Repository paths:

- `mod/res/scripts/client/driftkings/components/main.py`: General component.
- `mod/res/scripts/client/driftkings/settings/definitions/components/main.py`: field declarations and normalization.
- `mod/res/scripts/client/driftkings/views/hangar/hangar_preferences.py`: hangar presentation.
- `mod/res/gui/gameface/mods/driftkings/main/clock.js`: clock rendering.
- `res/configs/driftkings/default/main.json`: canonical defaults.

The clock follows hangar visibility. Its text is laid out line by line to support negative leading, matching the supported Flash formatting. Custom images use packaged `gui/maps/driftkings/...` paths or the permitted `mods/configs/driftkings/...` media folders.

Run the clock-text, settings and Gameface suites from the repository root. Check placement, negative leading, visibility transitions and custom-image paths in the target client. See the [contribution guide](../CONTRIBUTING.md) and [current status](../STATUS.md).
