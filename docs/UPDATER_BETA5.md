# Beta.5: updater responsiveness and native diagnostics

The beta.4 client log showed synchronous filesystem validation during installation
and restart, including a reported 5589 ms client-thread stall. WoT's embedded
Python 2.7 lacks `_ctypes`, so receipt checks invoke fixed hidden PowerShell/.NET
operations. Repeating these checks on the client thread blocked rendering.
The native receipt only reported `installValidationError`; it did not establish
whether WGC reopened the game or another validation failed.

## Change

`UpdaterService` now owns bounded `FileWork` jobs for recovery, previous-result
inspection, installation preparation, receipt validation and notification receipts.
Existing Core callbacks deliver results on the client thread. Workers never call
BigWorld, ResMgr, Settings state, context policy or restart APIs. Helper resources
are captured through ResMgr on the client thread before preparation. This adds no
parallel Core service and changes no gameplay modules or Settings UI.

Preparation retains existing size/hash, package, ticket and helper validations,
but intercepts native launch until delivery. The client then rechecks context,
file/parent identities, the ticket and the small helper hash before launching.
Cancellation or shutdown discards only newly created preparation files; staged
packages and user configurations are preserved. Cancellation after launch still
requires the matching native acknowledgement and process exit.

Restart uses a background-validated receipt with a maximum age of five seconds.
The receipt must match the helper PID and original ticket and differ from the
pre-launch receipt. File and parent signatures are compared before/after validation,
at delivery and at each restart request. Signature comparison is a change guard,
not a replacement for validation. Context, helper liveness and one-shot restart
consent are still checked on the client thread. Native package validation and the
existing process-exit gate remain authoritative for actual replacement.

## Diagnostics

The native result schema remains unchanged. Fixed error codes distinguish
`gameAlreadyRunning`, `installedPackageChanged`, `backupMismatch`,
`stagedPackageMismatch`, `copiedPackageMismatch`, `finalPackageMismatch`,
`packageIdentityMismatch`, `ownedPathMissing`, `reparsePathRejected`,
`pathNotLocal`, `installAccessDenied`, `installSharingViolation`,
`installIOError` and `processInspectionFailed`. Other validation failures retain
`installValidationError`. No filesystem paths or exception messages enter receipts.
The updater logs native rejection codes and previous-result error codes.

Any running WoT instance still blocks replacement. No WGC coordination, process
termination or retry while the game is running has been introduced.

## Local validation and runtime follow-up

New regression tests cover callback responsiveness during slow IO, bounded jobs,
late cleanup after shutdown, main-thread-only game resources/context, cancellation,
changed files, expired receipt proof, and the real native helper acknowledgement
and cancellation flow. Python 2.7 smoke also exercises worker delivery.

Builds remain in `build/`. The corrected 0.1.0 base is for a manual in-client
0.1.0-to-beta.5 test; beta.5 is the release candidate. This does not constitute
evidence of successful installation in the real game. Validate check/download,
READY, prepared acknowledgement, responsive rendering, restart, native result,
loaded VERSION and the installed package SHA-256. If installation fails, inspect
the new native error code before changing restart behavior.

Validated local checks: 698/698 Python tests, including all 15 native installer
tests and 13 new asynchronous regression tests. Python 2.7 smoke passed 11/11
on source, compiled base and compiled beta.5. Settings Gameface, Hangar updates,
Gameface dependency and UI bridge tests passed; nine Python/Flash contracts and
12 translation catalogs passed. Package inspection verified 247 Python 2.7
modules and source contracts. `git diff --check` passed. Native tests use owned
fixtures under `build/` and do not modify the actual game installation.

Local candidate artifacts (not deployed):

- Base 0.1.0: 6700002 bytes, SHA-256
  `f8de38814f4f99f13a4ba7439101121691a353cb777b946a992bb96afd2ec4c4`.
- Beta.5: 6700016 bytes, SHA-256
  `fca595f9e7e3acb9958585adfa0cda4904264d1ec2614c6dabf65af9f2f79165`.
- Manifest and checksum: `build/release/release.json` and
  `build/release/Driftkings.wotmod.sha256`.
