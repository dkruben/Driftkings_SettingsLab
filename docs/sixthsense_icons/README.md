# Packaged Sixth Sense icons

Source folder: `mod/res/gui/maps/icons/sixthsense/`.

Use valid PNG images named `<number>.png` (for example `10.png`). The settings panel uses the numeric filename as the icon ID. Declare added images in `build_data/components.json` and keep them below the updater inventory's `MAX_FILE` limit.

Users can instead select `mods/configs/driftkings/sixthsense/SixthSenseIcon.png` through the existing custom-icon setting. Installer previews belong in `installer/setup/assets/previews/` and do not change the game payload.

Updated for beta 0.1.3-beta.2. Paths are relative to the repository root. Validate added media with `python build_tools/validate_build_data.py` and `python build_tools/build_installer.py`. See the [contribution guide](../../CONTRIBUTING.md) and [current status](../STATUS.md).
