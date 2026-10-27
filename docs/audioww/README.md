# Packaged Wwise banks

Source folder: `mod/res/audioww/`.

Add matching `<name>.bnk` and `<name>.xml` files to that source folder. The XML must list `<name>.bnk` in `<loadBanks><bank><name>…</name></bank></loadBanks>`. Declare both files in `build_data/components.json`; the sound bank loader discovers the packaged XML. Keep each file below the updater inventory's `MAX_FILE` limit.

The installer changes JSON settings only; it never installs optional loose sound banks. `res/sound_bank_wwise` is the source Wwise project, not distribution content.

Updated for beta 0.1.3-beta.2. Paths are relative to the repository root. Validate added media with `python build_tools/validate_build_data.py` and `python build_tools/build_installer.py`. See the [contribution guide](../../CONTRIBUTING.md) and [current status](../STATUS.md).

Keep the authoring WAV, WWU and WPROJ files. Wwise regenerates `.cache/`, `GeneratedSoundBanks/`, validation caches and `Wwise.dat`; these outputs are ignored and are not build inputs. Packaged banks under `mod/res/audioww/` remain the distribution source.
