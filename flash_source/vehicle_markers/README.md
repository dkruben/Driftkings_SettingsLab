# Integrated vehicle markers

The runtime lives in `driftkings/core/vehicle_markers` and is owned by
`battle.vehicle_markers`. It incorporates the independently tested VM_TEST 0.0.14
implementation. VM_TEST is not a build or runtime dependency.

The build reads `battleVehicleMarkersApp.swf` from the game package identified in
`native-lock.json`, verifies its SHA-256, patches the native methods and appends
the helper ABC with a unique name after the native ABC. A different native movie
requires reviewing the patch and lock before building. RABCDAsm's `abcexport`,
`rabcdasm`, `rabcasm` and `abcreplace` are required; set `DK_RABCDASM_HOME`,
`rabcdasm_home` in `build_data/toolchain.local.json`, or `--rabcdasm-home`.

Configuration lives in the active profile's `vehicle_markers` directory:
`general.json`, `markers.json`, `fields.json`, `colors.json`, `healthbar.json`,
`damage.json` and `icons.json`. Transactions preserve the seven files together.

`general.json` selects the shared `colorRating` palette. Marker team colors use
its `system` table, percentage HP uses `hp_ratio`, and floating damage uses its
`damage` ownership colors. The runtime and sample use the same resolved tables;
HP thresholds follow the shared strict upper-bound comparison and last-band
fallback. Explicit marker color overrides remain supported and take priority.

The hangar settings editor uses a native T32 shop image and an HTML marker sample.
WG's `MarkerSettings.as` in the pinned 2.4.1 source uses a T32 sample with level 8
and 1550 maximum HP; the editor follows that approach. It adds editable text,
normal/ALT and team selectors, HP and colorblind previews, and simulated damage.
The sample renders sanitized Flash-style HTML. It approximates Flash rendering;
native icon artwork and font metrics must still be checked in-game.

Drafts use the existing settings session: Apply/Save publishes them, and Cancel
discards them. Marker settings are available in the hangar and apply next battle.
Only regular random and training managers receive custom presentation. Unknown
modes and KillCam keep native settings. Do not install the standalone VM_TEST
WOTMOD alongside this package: both replace the same native Flash resource.

Validation inherited from VM_TEST includes normal/ALT, damage ownership, replays,
real battles, observed-vehicle changes after death and special-mode fallback.
The integrated settings editor requires its own in-game visual acceptance test.
