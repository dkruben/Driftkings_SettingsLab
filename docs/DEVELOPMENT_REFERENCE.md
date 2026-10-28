# Development References

Verified on **28 October 2026** against the local reference folders, the installed NA client's `version.xml`, and [`build_data/build_config.json`](../build_data/build_config.json).

This guide identifies the sources used to develop Driftkings SettingsLab. These paths describe the maintainer's Windows workspace; they are not bundled with this repository. Other developers may store them elsewhere. The build contract is authoritative for the reference selected by the compiler.

## Reference locations

Local tools root: `E:/Wot_Mods_/Drift_Kings_ModPack/WoT_Tools`.

| Reference | Folder under the tools root | Purpose |
| --- | --- | --- |
| WoT SRC EU | `wot-src-EU/` | Current production reference for Python APIs, signatures, events, models, battle modes and Scaleform code; selected by the build contract. |
| WoT SRC CT | `wot-src-CT/` | Common Test snapshot for comparison. Check its version before treating it as newer than production. |
| XVM | `xvm-master/` | Implementation examples for cameras, crew, carousel, minimap, configuration and component lifecycle. |
| ModsList | `ModList/` | Mods-panel API and UI integration, including WULF resources and dependencies. |
| OpenWG Gameface | `GameFace/` | Resource registration, UI injection and JavaScript integration. |

The full ModsList path is `E:/Wot_Mods_/Drift_Kings_ModPack/WoT_Tools/ModList`. Preserve the actual folder spellings: `ModList` and `GameFace`.

The `Atualizados/` directory also exists under the tools root, but was empty when checked. It is not an additional verified source copy.

## Verified versions and source priority

| Item | Verified value | Evidence |
| --- | --- | --- |
| EU SRC snapshot | `2.4.1.5504` | `wot-src-EU/.version_name` |
| EU source client | `v.2.4.1.1 #989`, realm `EU` | `wot-src-EU/sources/version.xml` |
| CT SRC snapshot | `2.4.1.5466` | `wot-src-CT/.version_name` |
| CT source client | `v.2.4.1.0 Common Test #960`, realm `CT` | `wot-src-CT/sources/version.xml` |
| Build game target | `2.4.1.1` | Build contract, `game.version` |
| Configured game root | `D:/Games/World_of_Tanks_NA` | Build contract, `game.root` |
| Installed NA client | `v.2.4.1.1 #987`, realm `NA` | Installed client's `version.xml` |
| Supported realms | `EU`, `NA`, `ASIA` | Build contract, `game.supported_realms` |
| Selected source | `WoT_Tools/wot-src-EU`, snapshot `2.4.1.5504` | Build contract, `reference` |
| Reference policy | `read_only: true` | Build contract; this declares the intended access policy, not filesystem permissions |

The snapshot number and the game installation version are different identifiers. The EU reference and the installed NA client also have different build numbers. Verify changed APIs and behavior against the target client; these labels do not prove identical implementations.

Use the configured EU source as the starting point. The current CT snapshot is older than the EU snapshot and targets `2.4.1.0`; its name does not establish that its APIs belong to the current production client.

If additional reference copies are created, compare versions, revisions and relevant files. Do not silently switch the compiler to another copy or edit the reference sources to make a build pass.

## Where to look

### WoT client sources

The following paths were confirmed under both `wot-src-EU/` and `wot-src-CT/`:

| Path | What to inspect |
| --- | --- |
| `sources/` | Python implementations: original classes, method signatures, return values, events and call order. |
| `sources-as3/` | Available ActionScript classes and Scaleform contracts. Coverage can be incomplete, especially for extensions. |
| `_stubs/` | API-analysis helpers; confirm behavior in the available implementation and the game. |
| `.version_name` | Snapshot identifier. |
| `README.md` | Extraction details and reference context. |

Before changing a hook, find the original method and inspect its lifecycle, arguments, return value and callers. Confirm the affected mode: lobby, normal battle, replay, training/Topography or a special event. A successful import alone does not establish mode support.

### XVM

These starting points were confirmed under `xvm-master/`:

| Area | Paths |
| --- | --- |
| Camera and zoom | `src/xvm_battle_camera/` |
| Crew and tooltips | `src/xvm_crew/`, `src/xvm_tooltips/` |
| Lobby and carousel | `src/xvm_tankcarousel/`, `src/xvm_hangar/`, `src/xvm_techtree/` |
| Battle, minimap and replay | `src/xvm_battle/`, `src/xvm_battle_minimap/`, `src/xvm_battle_replay/` |
| Distributed configuration examples | `release/` |

Trace each configuration field to the code that consumes it. XVM is an implementation reference, not Driftkings' configuration specification. Preserve Driftkings defaults and presentation, and check dependencies, client compatibility, licensing and credits before incorporating external code or assets.

### ModsList

Start with `ModList/README.md`, then inspect `python/`, `resources/` and `as3/`. These paths were confirmed locally.

The packaged dependency is `res/wotmods/me.poliroid.modslistapi_1.8.0.wotmod`. Its SHA-256 matches the value in the build contract. A method present in the reference checkout may still differ from the packaged implementation; a matching package hash does not establish source-checkout equivalence.

### OpenWG Gameface

Start with `GameFace/README.md`, `python/openwg_gameface.py`, `resources/`, `as3/` and `tests/`. These paths were confirmed locally.

The packaged dependency is `res/wotmods/net.openwg.gameface_1.2.2.wotmod`. Its SHA-256 matches the build contract. Match the relevant source revision to that package before adopting an API.

The local README and Python implementation confirm that WG uses native `gui/gen_resources/*.json` registration from client 2.4.1. The older `on_ready`, `res_id_by_key`, `res_ids_by_mask` and `ModDynAccessor` APIs are deprecated placeholders on WG; `gf_mod_inject`, `ModInjectModel` and the JavaScript helpers remain supported by that reference implementation. Do not assume Lesta-specific paths or behavior apply to EU, NA or ASIA.

Gameface's DOM/CSS support is not identical to a desktop browser. The NA client log showed that `style.getPropertyPriority` is unavailable. Keep adapters compatible with the actual client and validate visual changes in game; browser-style test doubles alone do not prove API support.

## Workflow for a game update

1. Record the target game version, build and realm, SRC `.version_name` values, and revisions of the external libraries being consulted.
2. Compare the methods, events, enums, WULF/Gameface models and Flash classes used by Driftkings, including removed symbols and changed signatures.
3. Verify affected battle modes and follow the original component lifecycle, including cleanup when vehicles, modes or battles change.
4. Consult equivalent reference implementations where useful, preserving Driftkings defaults and tracing settings to their consumers.
5. Check ModsList/Gameface dependencies and Flash SDK/library compatibility before deliberately updating build contracts. Changing only a version number is insufficient.
6. Run the appropriate source checks and tests. Client Python remains compatible with Python 2.7 and client JavaScript with ES5. Regenerate defaults and UI catalogs through the project tools when required.
7. Compile and validate in the target client. Inspect `game.log`, battle entry/exit, vehicle/mode changes and component unloading. Stub-based tests do not replace in-game validation.

Run these JavaScript commands from the repository root:

```sh
npm --prefix build_tools/javascript ci --ignore-scripts
npm --prefix build_tools/javascript run lint
npm --prefix build_tools/javascript test
```

The npm manifests and local dependencies are in `build_tools/javascript/`; the scripts keep lint and test execution rooted at the repository directory. The ESLint configuration remains at the repository root.

For the complete validation sequence, use [`CONTRIBUTING.md`](../CONTRIBUTING.md) and [the CI workflow](../.github/workflows/python-package.yml). The build inputs can be checked with:

```sh
python build_tools/validate_build_data.py
```

See [`STATUS.md`](STATUS.md) for the project documentation index.

## Repository and packaging boundaries

Reference folders are development inputs, not additional runtime dependencies. Do not copy complete SRC snapshots, external repositories or local research snapshots into `mod/` or publish them as part of this guide.

Project Markdown documentation lives in `docs/`, with `README.md` and `CONTRIBUTING.md` at the repository root. Documentation is not part of the mod packages. Runtime dependencies are explicitly declared in the build contract; imported code and assets must retain their required licenses and credits.

Other repositories, including `dkruben/WOT_SRC`, may use a different extraction layout. Their current structure was not checked in this review; do not infer it from the local folder layout above.

## Maintaining this guide

Update this guide when verified local paths or reference contents change. Change the compiler's build contract only when intentionally changing its selected reference, target or dependencies. Updating an optional comparison checkout alone is not a reason to switch the build reference.

Evidence used in this review:

- Local folders and `.version_name` files under the tools root.
- EU/CT `sources/version.xml` and the installed NA client's `version.xml`.
- Local ModsList/Gameface README files and `GameFace/python/openwg_gameface.py`.
- [`build_config.json`](../build_data/build_config.json) and SHA-256 checks of both packaged UI dependencies.
- [`package.json`](../build_tools/javascript/package.json), npm scripts and the CI workflow.

[`FONTES_DESENVOLVIMENTO.md`](FONTES_DESENVOLVIMENTO.md) is the older Portuguese companion guide; dated statements there should be checked against the current contract and this verification.
