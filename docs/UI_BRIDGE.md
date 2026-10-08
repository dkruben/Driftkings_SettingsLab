# Owned UI bridge

The battle_observer reference registers AS3 components with the native battle
page, associates Python components through Scaleform settings, and calls Flash
methods through DAAPI. Driftkings uses the same native game facilities with its
own implementations; no battle_observer code or runtime is required.

## Battle

`core/overlay.py` holds texts, panels, images and their latest properties.
`views/battle/overlay.py` registers `DriftkingsOverlay` through the shared battle
view service. Its AS3 implementation is compiled into `DriftkingsBattle.swf`.
The transport exposes `as_reset`, `as_create`, `as_update` and `as_remove`;
`onElementMoved` returns drag coordinates to Python and existing settings stores.

The scene sends a snapshot when Flash becomes ready or is recreated. Children
are restored after their parents. Deleting a parent deletes its subtree. A
disposed view cannot detach a newer view or save stale drag coordinates.
Resize alignment, bounds, HTML labels, image fallback, backgrounds, shadows,
visibility, stacking and numeric animations are handled inside our SWF.
Animation and image listeners are removed when their elements are disposed.

Migrated consumers: AimingAngles, BattleEfficiency, BattleOptions, BattleStat,
InfoPanel, MainGun and MarksOnGunBattle. Existing visual configuration keys
remain supported. Other native Flash components keep their existing adapters.

## Gameface

`ui/gameface.py` adds a `DriftkingsUI` child model to each participating Wulf model.
It carries the feature name and owned CSS/JS asset lists. The bootstrap discovers
these models through the client's `subViews`, loads scripts in order, avoids
duplicate loads and invokes the feature's disposal function on removal.

Driftkings uses OpenWG Gameface 1.1.6, which is also required by ModsListAPI 1.7.9
on the current 2.4.0.1 client. `attach_assets` retains the owned `DriftkingsUI`
metadata and registers only `shared/bootstrap.js` through `gf_mod_inject`.
The owned bootstrap continues to load feature scripts in order and clean them up.
Each parent model reserves three properties: payload, DriftkingsUI and ModInjectModel.

OpenWG owns `gui/gameface/js/index.js` and builds the resource map using all mods'
declarations. `resource_id` resolves the shared IDs through `res_id_by_key`;
Driftkings no longer ships a competing index, resource map or fixed ID registry.
`build_ui_resources.py` validates our six layout declarations and writes a report.
A map change can cause OpenWG to request one game restart on this client.

Compatibility reference: [OpenWG Gameface 1.1.6 source](https://gitlab.com/openwg/wot.gameface/-/blob/v1.1.6/python/openwg_gameface.py).
This integration targets client 2.4.0.1; later client versions may change resource registration.

## Dependencies and verification

Install these three packages together:

- `Driftkings.wotmod` from `build/unified/`.
- `me.poliroid.modslistapi_1.7.9.wotmod` from `res/wotmods/`.
- `net.openwg.gameface_1.1.6.wotmod` from `res/wotmods/`.

The previous advice to remove OpenWG was incorrect: ModsListAPI requires it.
Gambiter GUIFlash and ModsSettingsAPI remain retired. Our battle Flash components
and settings window remain implemented by Driftkings. No game installation is
modified by the builder. Build and audit compare resource paths and contents
against the two required packages, rejecting conflicts before publication.

Run the Python unit suite, `node build_tools/tests/ui_bridge_test.js`, the carousel
JavaScript tests, `node build_tools/tests/gameface_dependency_test.js`, and `python build_tools/build_lab.py --flash`. Compilation and
mocked tests cover the transport, lifecycle, loader and packaging; actual visual
positioning, drag input, transitions, respawns and event battles still require
in-client testing.
