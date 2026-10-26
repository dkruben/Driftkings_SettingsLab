# Vehicle carousel (Gameface)

Source folder: `mod/res/gui/gameface/mods/driftkings/vehicle_carousel/`.

Configurable own-player random-battle statistics for the Wargaming 2.4.1.0 carousel.

## Configuration

Use the Vehicle carousel settings, or the active profile at
`mods/configs/driftkings/<profile>/vehicle_carousel/`:

- `carousel.json`: enable switch, rows, layout, filters, sorting and appearance.
- `carouselnormal.json`: normal-layout native fields and custom fields.
- `carouselsmall.json`: compact-layout native fields and custom fields.

`cellType: normal` or `small` selects that profile regardless of row count.
`default` follows the native card layout. Normal and compact options are independent.

## Native fields

Supported fields accept `enabled`, `alpha` (0–100), `dx`, `dy` and `scale`.
Disabling a field hides its descendants too. Disabling the mod restores native styles.

| Key | Native equivalent |
| --- | --- |
| `flag` | National flag |
| `tankIcon` | Vehicle image |
| `tankName` | Vehicle name |
| `tankType` | Vehicle type icon |
| `level` | Vehicle tier |
| `xp` | XP bonus text and background |
| `info` | Vehicle status text |
| `infoImg` | Vehicle status icon |
| `rentInfo` | Rental time/battles/wins counter |
| `favorite` | Favourite indicator |
| `progressionPoints` | Battle Pass points |
| `crystalsIcon` | Bonds earning indicator |
| `coreBorder` | Special-vehicle Battle Pass highlight |

Legacy fields `clanLock`, `price`, `actionPrice`, `infoBuy`, `crystalsBorder`
and `stats` are preserved in existing JSON, but have no independent equivalent in
this integration and are not exposed as controls. Native Flash `textFormat` and
`shadow` properties on standard fields are not applied.

## Custom fields

Each profile accepts up to 64 `extraFields`, with `enabled`, `format`, `src`, `x`,
`y`, `width`, `height`, `fontSize`, `iconSize`, `alpha`, `align`, `layer` and `shadow`.
Formatting templates use a restricted text parser. Example:
`<font color="{{c:wn8}}">{{wn8}}</font>`.

Macros include `battles`, `winRate`, `hitRate`, `avgDamage`, `avgReceived`,
`avgAssist`, `avgBlocked`, `avgStun`, `avgFrags`, `avgSpotted`, `avgCapture`,
`avgDefence`, `damageRatio`, `damageHP`, `eff`, `wn8`, `wnx`, `xeff`, `xwn8`, `marks`
and `mastery`. Missing statistics display `--`. `{{avgDamage:.1f}}` selects one
decimal. Compatible `{{v.tdb}}` and related aliases are also supported.

Built-in PNGs use lowercase paths under `gui/maps/driftkings/carroucel/`.
Python reads these through ResMgr and delivers image data, including names with `#`.
Native icons may use `coui://gui/maps/icons/...`.

Dossier synchronization invalidates the statistics cache even without an active
hangar card. Loading a new card also clears cached statistics. Validate updates
in-game by completing a battle and returning to the hangar.

## Current defaults and validation

The 0.1.3-beta.2 defaults follow the author's EU profile. Normal cards use separate icon and text fields, configurable font aliases and per-field opacity. `{{v.wnx}}` / `{{v.c_wnx}}` and sorting by `wnx` are supported; incomplete assistance or expected-value data displays `--`.

After editing the JSON, regenerate the fallback and snapshot with `python build_tools/generate_defaults.py --write --refresh-snapshot`. Run `npm test` for native-field restoration, fixed-width alignment and font-alias regression coverage. Complete a battle and return to the hangar to verify live dossier updates.

See the [contribution guide](../../CONTRIBUTING.md) and [current status](../STATUS.md).
