## Summary

<!-- What changes and why. Keep one concern per pull request. -->

## In-game validation

CONTRIBUTING.md asks every change to be verified in the target client. Say where it was tested:

- **Client version:** <!-- e.g. 2.4.1.1 #989 -->
- **Region:** <!-- EU / NA / ASIA -->
- **Mode:** <!-- e.g. random battle, replay, hangar, Halloween -->
- **What was checked:**

If it was not tested in game, say so and why.

## Checks

- [ ] `python -B tests/run_python.py --suite runtime`
- [ ] `python -B tests/run_python.py --suite build`
- [ ] `python build_tools/validate_locales.py`
- [ ] `python build_tools/generate_defaults.py --check`
- [ ] `python build_tools/check_undefined_names.py`
- [ ] `npm --prefix build_tools/javascript run lint && npm --prefix build_tools/javascript test`
- [ ] New interface text is in the YAML catalogues for all 18 languages
