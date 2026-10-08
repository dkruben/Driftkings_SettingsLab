# Beta.6: coordinated updater restart

The real beta.5 test reached verified staging and a matching prepared helper
acknowledgement. At 22:14:59 the Settings restart path requested an immediate
WGC/engine restart. The native receipt then reported `gameAlreadyRunning`, and
the installed package remained the corrected 0.1.0 base. The result establishes
that another WoT process blocked replacement; it does not identify which launcher
created that process.

## Behavior

For updater restart only, Settings saves preferences, claims validated restart
consent, closes its window and calls the normal `BigWorld.quit()` API. It does
not request an immediate engine/WGC restart. Ordinary Settings restart still
uses its existing `WGC.notifyRestart()` and `BigWorld.restartGame()` path.

Consent is an exclusively created, flushed `restart.install` marker containing
only schema, parent PID and helper PID. The live prepared acknowledgement is
rechecked before writing. The native helper validates exact fields and both PIDs
after the validated parent exits, then consumes the marker. No paths, command
lines, URLs or executable names are accepted from the marker. Rearming an owned
interrupted transaction clears stale consent. Client shutdown failure revokes
consent; inability to revoke cancels the helper rather than leaving relaunch armed.

The helper retains all existing package/backup/hash validation, global NoGame
checks, rollback and atomic replacement behavior. It reopens only after a verified
successful install and a flushed terminal receipt, releasing transaction and
parent handles first. The executable is the validated parent image, with no
arguments and no shell, and the working directory is its game root. Scheduling
alone does not authorize reopening. Cancellation, invalid consent, installation
failure or rollback never reopen the client automatically. On installation
failure, open the game manually to inspect the result. If installation succeeds
but reopening fails, the receipt stays `installed` with `restartLaunchFailed`.

No other game process is killed. Any other running WoT still blocks replacement.
If an external launcher or the user independently opens the game too early, the
helper continues to fail closed. This change controls the project's own restart
request; it does not disable external launchers.

## Compatibility and validation

Existing manifest, ticket, receipt, user configuration and settings-value formats
remain unchanged. The new restart marker is optional. Receipt validation remains
in the beta.5 background jobs; the marker is small local binary-mode JSON with
exclusive creation. No new service or dependency is introduced. PT/EN updater
dialog text describes the coordinated restart.

Native fixtures under local `build/` observe the actual executable reopening and
assert the new package SHA-256 and terminal `installed` receipt are already
visible before that process starts. They also assert zero arguments, the owned
game root working directory, one-shot consent, no reopening without consent,
stale/wrong PID rejection, command-field rejection, cancellation and failure.
Controller tests cover ordinary restart, updater quit, duplicate requests and
preference/shutdown exceptions. Python 2.7 smoke covers the consent marker.

Real-client installation remains a separate manual test. Install the newly built
0.1.0 base first so the running client and its bundled helper both contain this
fix. With WoT and any old helper closed, move the previous beta.5 `download-*`
operation outside `cache/update` before the new test; its verified helper belongs
to the previous build and is deliberately not silently replaced. Select beta,
check/download beta.6, request installation and confirm restart. Let the helper
reopen the game. Then check loaded VERSION, native receipt and installed SHA-256.
Local preparation and publication do not deploy anything into the game.

## Validated local artifacts

- Python: 713/713 tests, including 21 native installer tests.
- Python 2.7 smoke: 12/12 on source, compiled base and compiled beta.6.
- Settings Gameface, Hangar updates, Gameface dependency and UI bridge: passed.
- Python/Flash: nine contracts passed; i18n: 12 catalogs, zero errors.
- Package: 33 components, 394 entries, 247 Python 2.7 modules; inspection and
  source contracts passed. `git diff --check` passed.
- Base 0.1.0: 6703937 bytes; SHA-256
  `237c42c85d1cf5d5e6b4c7bc6a31076a1bfe00fb80a970353d287bf93897aa3a`.
- Beta.6: 6703951 bytes; SHA-256
  `101bca74231833f8cffa2d5fe5cc8501ab72663ee0406c21d78056d7f09706e4`.

Base: `build/updater-test-base/Driftkings.wotmod`. Beta, manifest and checksum:
`build/release/`. Successful native fixtures establish local transaction/relaunch
ordering; they do not certify launcher authentication or real-game installation.
