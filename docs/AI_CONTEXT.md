# Driftkings SettingsLab – AI context

Authoritative technical context for AI development assistants (Claude Code, Codex, ChatGPT and others). Read this file before any substantial investigation, development, validation or release task. Do not re-investigate facts recorded here unless a change makes them stale.

## 1. Project identity

- **Purpose:** an interface modpack for World of Tanks: battle, hangar and aiming enhancements, vehicle markers and one settings panel.
- **Repository:** `https://github.com/dkruben/Driftkings_SettingsLab` (GPL-3.0). Local workspace: `E:\Wot_Mods_\Drift_Kings_ModPack\Driftkings_SettingsLab`.
- **Technologies:** client runtime in Python 2.7; build tooling in Python 3; Flash/ActionScript 3 libraries; Gameface UI in ES5 JavaScript (tests with Node 20); installer in Inno Setup 6.7.1 with a small C# helper.
- **Public release:** **0.1.7 stable** for World of Tanks **2.4.2.0**. Published compatibility: **EU and NA validated**; ASIA and CN not validated for 0.1.7.
- **Development:** the current unpublished test candidate is `0.1.8-rc.1`. It is not a publication candidate.

## 2. Approved architecture

- One shared Wargaming codebase, with realm-independent compilation, installation, validation and publication.
- One primary compiler: `build_tools/compiler.py`.
- One independent installer: `build_tools/build_installer.py`, with Inno Setup scripts in `installer/setup/`.
- One unified run workspace: `build/runs/<run-id>/`.
- Two permanent branches: `main` and `develop`. Optional beta publication.
- Universal WOTMOD whenever compatibility is demonstrated.
- Exclusions: LESTA, RU and PT_RU are outside the project scope.

**No production realm is the exclusive or preferred reference.** EU #1000, NA #999, ASIA #998 and CN #997 are production realms with equal standing. CT (#995, #996) is a development and testing environment, not a public requirement. `na999` is the configured target that was used for the recent validations. It is not an architectural dependency. The same validation could have been performed on another compatible production client.

Known contradictions in the implementation are listed in section 9.

## 3. Git strategy

- `main`: stable releases, hotfixes, nanopatches and micropatches.
- `develop`: major improvements, new features and CT development.
- Temporary branches only when genuinely necessary. No unnecessary worktrees.
- No evidence-only commits. Do not add commits that exist only to record a validation.
- Published tags and release artifacts are immutable. Never modify a published release.

## 4. Entry points

All commands run from the repository root.

| Task | Command | Notes |
| --- | --- | --- |
| Development WOTMOD | `python -B build_tools/compiler.py --mode dev --target na999` | Add `--version X` for a package-only override. Writes only `build/runs/<run>/`. Development output is WOTMOD only. |
| Release staging candidate | `python -B build_tools/compiler.py --mode release --target na999 --channel stable` | The tracked version must already match `build_data/release.json`. Output stays STAGING in the run. |
| Read-only plan | append `--plan` to any build command | Compiles nothing and writes nothing. |
| Installer | `python -B build_tools/build_installer.py --artifacts build/runs/<run>/output --compile --attach-to-release` | Adds the Setup and its WGMods ZIP to the staging output. Refused once the candidate is frozen. |
| Freeze and promote | sign, then `python -B build_tools/compiler.py --promote-run build/runs/<run>` | Promotion copies the frozen run once into `build/releases/`. It refuses unsigned or unstamped candidates. |
| Retention | `python -B build_tools/compiler.py --retain-runs` (preview) and `--retain-runs --apply` | Never apply without reviewing the preview. |
| Offline signing | `python -B build_tools/sign_release.py <folder> --key <private-key-file>` | The private key is never stored in the repository. |
| Direct stable publication | `build_tools/promote_release.py prepare / build / check / publish --stable X.Y.Z` | `build` takes no record. `check` and `publish` take `--record`. Full digests bind the approval. |
| Optional beta publication | `build_tools/promote_release.py build / check / publish --beta X.Y.Z-beta.N` | Same gates as direct. Not required for stable. |
| Artifact tests | `python -B tests/run_python.py --suite artifacts --wotmod <path-to-WOTMOD>` | Explicit path. |
| Build tests | `python -B tests/run_python.py --suite build` | About 555 tests. |
| Runtime tests | `python -B tests/run_python.py --suite runtime` | About 787 tests. |

**Compatibility aliases still accepted:** `--mode debug` (same as `dev`, WOTMOD only), `debug.cmd` and `release.cmd` (wrappers around `build_tools/run_build.cmd`), `--isolated-output` (accepted; every build already uses the run layout).

**Retired:** the `beta_version` gate input (use `route` and `version`), the `build/experiments` layout and the release-time installer directories.

## 5. Dependencies and toolchain

- **Target configuration:** `build_data/build_config.json`. Targets: `na999`, `eu1000`, `ct995`, `ct996`. Production pins are in `reference.production_clients` (build, revision and snapshot): NA 999 (2.4.2.5523), EU 1000 (2.4.2.5524), ASIA 998 (2.4.2.5526), CN 997 (2.4.2.5525). CT builds: 995 and 996.
- **Canonical sources:** the local snapshot stores are `Driftkings_WoT_Sources/wot_src_NA` (2.4.2.5523) and `Driftkings_WoT_Sources/wot_src_CT` (2.4.2.0 Common Test #996). Do not modify them.
- **Local toolchain:** `build_data/toolchain.local.json` (git-ignored). Path precedence: CLI argument, then `DK_*` environment variable, then the `targets` section for the selected target, then the local default, then discovery.
- **Required tools:** Python 2.7 (for the compile worker), Flex SDK (`mxmlc`), Java 8, the Adobe Animate `playerglobal.swc`, a C# compiler (Roslyn preferred), Inno Setup 6.7.1 and Node 20.
- **Reference handling:** only eight reviewed Python reference files may be compared after CRLF-to-LF normalization. Bare CR is refused, and every other byte is compared exactly. Binary resources, SWF, SWC, WOTMOD, patch files and signed manifests are compared by raw SHA-256.
- **Known limitation:** `WoT_Tools/wot-src-EU` is snapshot 2.4.1.5514, not the EU pin 2.4.2.5524. The EU profile is an alias of the NA profile (see section 9), and it requires an explicit reference override.
- **Machine-specific:** drive letters, game folders and tool paths. These are not architecture.
- **Never put private keys, credentials, tokens or secrets in the repository or in any document.**

## 6. Build architecture

```
build/
  runs/<run-id>/            run-owned workspace (the only place for new build output)
    workspace/              intermediates, worker jobs, installer input and Setup output
    output/                 WOTMOD, distribution, manifests, checksums
    evidence/               build report, state, logs, installer evidence
  releases/<channel>/<ver>/ canonical frozen candidates (promotion target)
  cache/                    genuinely needed caches (for example Flash inputs)
```

Other folders under `build/` are historical: `backups/`, `candidates/`, `diagnostics/`, `reference/` and older runs. Do not delete them without owner approval.

**Run workspace:** each run has its own folder. Its workspace is not shared with other runs. Its evidence is kept with its output.

**Development output:** WOTMOD and evidence only. No distribution, no installer, no release metadata.

**Release output:** the distribution ZIP, the manifest and modpack metadata, `SHA256SUMS.txt`, the Setup and its WGMods ZIP when attached, and the build report.

**Installer workspace:** `workspace/installer/input`, `workspace/installer/output`, and `evidence/installer/` with the Inno Setup log and verification record.

**Atomic promotion:** a run is copied once into `build/releases/`, staged first and then moved into place. A release that already exists is refused unless it is byte-identical.

**Frozen candidate protection:** a candidate is STAGING while it has no stamp and no signature, and it may change while staging. It is FROZEN once `.promotion-build.json` or `release.json.sig` exists. A frozen candidate is never changed, and only promotion copies it.

**Retention:** successful development runs keep their WOTMOD and evidence for the three newest per target; their workspace is removed. Failed runs keep evidence for 14 days. Release runs, runs marked `evidence/RETAIN`, unknown or historical layouts, active runs and referenced runs are protected. Preview first.

**Removed in the Phase 6.3 cleanup (verified SHA-256 duplicates or regenerable):** `build/unified/`, `build/staging/`, `build/gameface/`, `build/flash/`, `build/native/`, `build/installer_input/` and the `build/debug/beta/0.1.8-beta.1` mirror. The `package.output`, `package.debug_root` and `python.staging_root` configuration keys were removed.

**Retired global writes (do not reintroduce):** `build/debug/`, `build/unified/`, `build/staging/`, `build/flash/`, `build/gameface/`, `build/native/` (as copies), `build/previous/`, `build/experiments/`, `build/installer/`, `build/installer_input/`.

**Logical identifiers that look like paths:** generator outputs such as `build/flash/...` in `build_config.json` and the `components.json` sources are catalog identifiers. The files themselves live in the run workspace. Do not remove them because they resemble old paths.

## 7. Release lifecycle

1. Prepare and commit the intended version (`release.json` and the runtime version file).
2. Compile the unsigned staging candidate in `build/runs/<run>/output`.
3. Generate and verify the WOTMOD and distribution.
4. Attach the Setup and generate the WGMods Setup ZIP.
5. Verify the complete distribution and finalize the checksum list.
6. Sign: `release.json.sig` covers the manifest, and `SHA256SUMS.txt.sig` covers the complete inventory. Both use the project's own signature module, with the offline key.
7. Stamp the verified candidate (this is the last write, and it is outside the inventory).
8. Record verification and approval evidence.
9. Atomically promote the frozen candidate into `build/releases/`.
10. Publish exactly those bytes through the protected `stable-release` environment.
11. Verify the remote asset digests.

**Signatures are not Authenticode.** The Setup executable is not Authenticode-signed, and no commercial code-signing is used.

**Manifest schema:** the runtime manifest rejects unknown fields. `release.json` must not gain new keys. The Setup ZIP is covered by `SHA256SUMS.txt`, which is covered by the detached inventory signature.

**Embedded defaults archive:** `Driftkings-defaults.zip` is required inside the distribution. The shipped updater reads it there. The standalone public defaults asset is kept for the published 0.1.7 only; new candidates do not publish it.

**Approval bindings:** approvals bind the complete SHA-256 of the inventory and of the validation record. Abbreviated digests are display and lookup values only. Historical abbreviated titles (`0.1.7-beta.2`) are accepted for historical verification only.

**Protected environment:** the approval environment `stable-release` must keep its required reviewers. Direct stable publication has no waiver.

**Direct stable and beta:** stable does not need a published beta. Beta publication is optional. A beta and a stable with different versions are distinct artifacts, and a signed beta is never renamed into a stable.

**Never rebuild or repackage a frozen candidate during publication.** Publication only verifies and uploads exact bytes.

## 8. Validation knowledge

Status: **PASS**, **PARTIAL**, **NOT TESTED**, **NOT APPLICABLE**.

| Item | Status | Scope and commit | Limitation |
| --- | --- | --- | --- |
| Build suite | PASS | Current tree after `ead3fbbb` (about 555 tests, 2 skipped) | Historical skips need unavailable references. |
| Runtime suite | PASS | Current tree (787 tests) | Source tests; not a client run. |
| Client identities | PASS | NA #999 (2664941) and EU #1000 (2664941) | The CT client is installed at `C:\Games\World_of_Tanks_CT` (#996). |
| NA and EU consumed-resource equivalence | PASS | Source comparison of 13 Gameface resources, 8 SWCs and 1 vehicle-marker SWF | Equivalence of sources is not runtime validation. |
| Reviewed Python reference equivalence | PASS | Eight reviewed files, LF and CRLF only | Other files must match raw bytes. |
| Real NA development WOTMOD | PASS | `0.1.8-beta.2`, SHA-256 `68220ffa…cbca4` | Built before the installer fix. |
| Real release staging distribution | PASS | `0.1.8-rc.1`, WOTMOD `07b5a545…8f33a`, dirty source (temporary version edit) | Unsigned, unpublished, test-only. |
| Real Inno Setup compile | PASS | Inno Setup 6.7.1, Setup `488817ac…1dca96c`, WGMods ZIP `0d94fcbb…09dbb` | The compile ran before the destination correction. |
| WGMods ZIP verification | PASS | One executable, exact SHA-256 match | Only the test candidate. |
| Published 0.1.7 updater compatibility | PASS | Shipped updater modules run under Python 2.7 on the published 0.1.7 and the new distribution | Rollback not exercised. |
| NA runtime (owner checklist) | PASS | `0.1.8-rc.1` on NA #999; game log shows startup, hangar, battle, replay and shutdown; no SettingsLab exception | Native launcher and settings open/close are confirmed by the owner, not by log lines. |
| Installer destination safety | PASS (source tests) | `fix(installer)` commit `ead3fbbb`: 21 static tests | The Pascal code is **not compiled**. |
| Corrected installer executable | NOT TESTED | — | Needs an authorised compile and an isolated run. |
| Isolated install and uninstall | NOT TESTED | — | Only in an isolated Windows environment. |
| Full updater run and rollback | NOT TESTED | — | Needs an isolated client copy. |
| Real GitHub promotion gate | NOT TESTED | — | Requires owner dispatch. |
| Historical 0.1.7 artifacts | PARTIAL | Two artifact-suite checks skip (missing historical references) | Restore references to run them. |

**Live client state (incident):** on 26 November 2026 the Setup installed the `0.1.8-rc.1` test WOTMOD into the live NA client (`mods\2.4.2.0\driftkings.wotmod`), appended `mods\configs\driftkings\installer\unins001.*`, and created a current-user uninstall entry. The owner has **not** authorised restoration or cleanup. Do not change this state without explicit owner authorisation.

**Validation policy:** rerun a check only after a relevant code change, changed inputs, changed client resources, a changed contract, a regression, a specific technical reason, or an owner request. Prefer focused tests for a single component. Historical validation is evidence, not a guarantee.

## 9. Realm-independence notes

These are recorded so that future work does not treat them as intended design:

- `build_config.json` declares `production_profiles.EU.alias_of = NA`. The EU reference profile therefore depends on NA's reviewed pins. It should be a peer profile.
- Scope is candidate-specific: any production realm (EU, NA, ASIA, CN) may be marked OUT OF SCOPE by one release record, with owner approval, for that release only. Every region must still be accounted for, and an out-of-scope region is never verified compatibility. No realm has permanent priority.
- The EU reference snapshot in `toolchain.local.json` is the wrong version (see section 5).
- `validate_build_data.py` and `vehicle_markers_patch.py` keep a `995` fallback for the historical native lock that has no `clientBuild` field. This is a legacy contract, kept on purpose.

## 10. Pending work and component status

### Remove Fog

**Status:** functionally restored and accepted for the development candidate `0.1.8-beta.1`. The behaviour is the one reviewed in v0.1.6. Remove Fog is not part of the public 0.1.7 release and must not be advertised until a version that contains it is publicly released.

**Accepted development candidate:** version `0.1.8-beta.1`, target `ct996` (historical build evidence, not a production-realm requirement), mode `dev`, WOTMOD `build/runs/20261126T041020Z-e956d6e1/output/driftkings.wotmod`, SHA-256 `613447ace5747052559ddb7c74da48f23c344ffa163b0bd207de9970b1a8abd5`.

**Validation evidence (two kinds, kept separate):**

- *Owner-reported runtime validation (manual, in game):* the owner reports that all 12 manual points passed: fresh profile defaults OFF; no auxiliary package before explicit activation; manual activation works; package generation and installation after client exit work; the expected historical graphical effect is restored; the player preference persists; manual deactivation works; owned auxiliary package removal works; original fog behaviour is restored; reset restores OFF; the Portuguese settings descriptions were verified; and no related `game.log` errors were reported. These are the owner's observations; the repository holds no game logs or screenshots of them.
- *Automated test evidence (this repository):* runtime `core` group 222 pass; runtime `settings` group 113 pass; build contracts (fog contract, production readiness, own-window catalogue, installer destination and discovery, CT binaries) 55 pass. The helper binary carries the six historical leaf names, and its SHA-256 matches `helper.json`. These tests check structure and contracts; they do not measure in-game behaviour.

#### Owner correspondence (verbatim)

Original WGMods moderation feedback, supplied by the project owner:

> Please expand the listing and settings explanations to cover these behaviors clearly:
>
> * Fog removal is enabled in the supplied defaults and generates a separate Driftkings.RemoveFog.wotmod after the client exits. Explain how users disable it.
> * Clan reward collection also automatically unlocks progression stages using Tour of Duty coins and is enabled by default. Distinguish this from free reward collection and from credits/gold. Automatic Tour of Duty coin spending is accepted; please explain that behavior clearly.
> * Explain that the account manager stores protected credentials locally, that analytics is optional, and that the updater uses Windows helpers to install after client exit. Keep this information visible before users enable or use the corresponding features.
>
> The bundled executables were statically decompiled and inspected. No source-code upload is requested.

New explicit confirmation from Wargaming moderation, supplied by the project owner:

> Hello,
>
> Thank you for reaching out to confirm before implementing the change.
>
> Yes, restoring the optional Remove Fog feature with the exact same behavior reviewed in v0.1.6 remains acceptable under our current Fair Play policy, provided it remains disabled by default and requires explicit opt-in from the player.
>
> Please note that your upcoming update will still undergo our standard moderation review upon submission to ensure no unintended gameplay advantages have been introduced.
>
> Best regards

#### What the confirmation covers

- **Covered:** restoration of the exact historical behaviour reviewed in v0.1.6, provided the feature is disabled by default and requires explicit player opt-in.
- **Not covered:** expanded functionality, any new resource modification, and any exemption of the upcoming release from standard moderation review.
- **Mandatory conditions:** OFF by default; explicit player opt-in; no automatic activation on first installation, through installation profiles, or through ambiguous legacy configurations; previously recorded explicit player choices are preserved; reset to defaults restores OFF; disabling removes the owned auxiliary package after client exit; the restart requirement is shown to the player.
- **Standard moderation review still required** for the upcoming release submission.

#### Historical reference (verified in the repository)

- Tag `v0.1.6` (commit `cfa1ed4b`) contains the reviewed implementation. The published `driftkings.wotmod` (`bc392604…`) contains `core/fog_package.py` and `res/gui/driftkings/fog/Driftkings.FogPackage.exe` (`dd11d7c9…`). The published defaults set `removeFog` to `true`; that default was changed to OFF by `1e194db1`, which the confirmation requires.
- Exact transformation (`installer/source/fogpackage.cs`): boolean leaves `Fog/enable`, `VolumetricFog/enabled`, `VolumetricFog/enableGameplay` are replaced by an empty payload; density leaves `Fog/deferred/density`, `Fog/simplifiedDeferred/density`, `Fog/forward/density` are replaced by four zero bytes. These six leaves are the whole transformation. The same rewrite logic is in the `v0.1.6` helper and in the recovery reference `6ac1d7e7`. A test (`tests/build/test_optional_fog_contract.py`) asserts the lists.
- Local engine-side evidence (`WoT_Tools/wot-src-EU`, read-only): the leaves are data in `res/spaces/*/environments/*/environment.xml`. `VolumetricFog/enableGameplay` is `false` in 97 of 98 environment files and `true` in one. No client script reads these keys. The gameplay meaning of each leaf is therefore not established by local evidence; the moderation confirmation is what authorises the historical behaviour.

#### Implemented behaviour

- The Settings panel shows the Remove Fog control. It is OFF by default (`battle_preferences.json`, `default_values.py`).
- Turning it on writes an explicit choice to `mods/configs/driftkings/cache/fog/choice.json`. Legacy profile values never enable it; ambiguous states hold automatic action.
- The helper builds `Driftkings.RemoveFog.wotmod` locally from the game's map packages while the client runs, and installs it only after the client exits. A restart is requested only with the player's consent (`coordinated_restart`).
- Turning it off, or resetting to defaults, removes the owned package after client exit. A recovery copy is kept under `cache/fog/recovery/`.
- Ownership: the package is accepted only if its `meta.xml` id is `driftkings.removefog`. The helper records the installed path and SHA-256 in `cache/fog/owned.txt`.
- Uninstall (Inno Setup `CurUninstallStepChanged`, not compiled): removes only the recorded package, only inside `{app}\mods\`, only if the file name is `Driftkings.RemoveFog.wotmod` and its SHA-256 matches the record. Recovery copies and the cache folder are left in place.

#### Remaining limitations

- The Setup executable and the installer cleanup are not compiled or executed. The uninstall cleanup is covered by a static contract test only.
- Non-English moderation texts were written by the project and need native review.
- Standard WGMods moderation review is required before public distribution of any version containing Remove Fog. The official WGMods listing URL has not been supplied and must not be invented.

#### Phase 8 conclusions (functional regression inventory, owner decisions)

- **No additional unintended functional losses were identified** between v0.1.6, v0.1.7 and develop. The component registry (35 entries in `component_list.py`) and the settings definitions are unchanged apart from the Remove Fog restoration and the Tour Coin consent switch (default OFF).
- **Remove Fog has been recovered and validated.** The owner completed the manual runtime validation; see the Remove Fog section above.
- **Halloween TAB removal was intentional and owner-approved.** The Halloween TAB ally rating colours were removed because Halloween is a seasonal game mode. It is not restored, and its Fair Play status is not being investigated.
- **Seasonal features do not require permanent maintenance.** Seasonal game modes are addressed only when relevant to an active event and explicitly requested by the owner.
- **Architecture:** the native Gameface architecture is preserved. OpenWG and ModsListAPI are not restored. Battle cards are hosted in the owned window, and the settings open from the hangar footer launcher.
- **Documentation correction:** the README's "open Driftkings settings from the mods list" instruction was obsolete and now points to the hangar footer launcher.
- **Deferred to the upcoming visual correction phase:** battle card placement relative to the native HUD, and the appearance of the settings header image (`header_tank.jpeg`, removed in v0.1.7).
- **Phase 8 is complete.** No runtime code, compilation, automated test or push was performed in this phase.


#### Account Manager security review (Phase 9, complete, owner-accepted, 2026-11-26)

Method: code reading of `components/account_manager.py`, `core/accounts.py`, `gameface/lobby/account_manager.py`, `common/utils/filesystem.py`, the existing lobby tests, and the decompiled client's own use of `BigWorld.wg_cpdata` (`WoT_Tools/wot-src-EU`: `gui/login/Preferences.py`, `helpers/local_cache.py`). No real account file, password or credential was accessed; tests use synthetic values only.

**Verified storage behaviour**

- The file `accounts.manager` is `wg_cpdata(base64(zlib(JSON)))`. Each record's `email` and `password` are additionally passed through `wg_cpdata` individually (`core/accounts.py`, `save`). Writes therefore never produce a plaintext account file.
- Reading: `wg_ucpdata` is tried first. If it fails, the file is parsed as plain JSON, and only the exception type name is logged (debug level). If that also fails, `read_error` is set and every write is blocked, so the existing file is preserved.
- The fallback affects reading only. No code path writes plaintext. Writes are guarded by `read_error` and roll back the in-memory list if the file write fails.
- Strength of `wg_cpdata`: the engine's implementation is not in the local references. The game uses the same call for its own login preferences (`cryptLoginInfo`) and cache files, which indicates a protection layer, not an authenticated encryption scheme. Its strength and key scope are **unverified**. The UI text therefore says "protected with the game client's credential protection. This is not a guarantee of encryption."
- Logs: no code logs an e-mail or password. Exception messages in the Gameface handler are replaced with a generic label, and the `LOG.exception` traceback names the failing step only (`gameface/lobby/account_manager.py`).
- Analytics: the analytics modules do not reference the account store or its fields.
- Gameface: the password leaves the store only on an explicit "reveal" request, and is then carried in that window's view-model payload until cancel, save or close. The payload stays in the client process.
- Migration: no conversion of existing files is performed. Records are read as stored and rewritten, protected, on the next successful save. A failed read never overwrites the file.
- Deletion: a delete rewrites the file without the record through `atomicWrite`. `replace_file` removes the `.previous` backup after a successful replace, so no backup of the deleted record remains. This does not guarantee physical erasure on the disk.

**Findings and severity**

| # | Finding | Severity | Practical impact |
|---|---|---|---|
| 1 | Protection strength of `wg_cpdata` unverified | Medium (unknown) | If the layer is weak, a local user with access to the preferences folder could recover the stored passwords. The wording makes no encryption claim. |
| 2 | Plain-JSON fallback accepted silently at read time | Low | Only a file that was never written by the protected path reaches this branch. Its records are used as stored, and the next save protects them. No plaintext is written by Driftkings. |
| 3 | Revealed password stays in the window payload until cancel, save or close | Low | In-process only; requested by the player. |
| 4 | Deletion does not guarantee physical erasure | Low | Standard filesystem behaviour. |

No finding shows a plaintext write, a credential in logs, or a transmission of credentials to analytics or a third party.

**Corrections**

- No runtime code was changed. None of the findings requires a correction that is small and clearly justified. Removing the fallback would make any legacy file unreadable, and the repository does not show whether such files exist.
- Tests added (`tests/runtime/lobby/test_account_manager.py`, class `AccountStorageSecurityTests`): protected writes go only through the protection function; a plain-JSON read is not rewritten as plaintext; deletion removes only the chosen record and leaves no backup.

**Owner decisions needed (not implemented)**

- Whether to migrate a fallback-read file to the protected format immediately, and whether to tell the player when that happens. This needs new text in 18 catalogues and a startup write.
- Whether to tell the player when protected storage is unavailable at read time, not only at save time.

**Owner decisions (accepted 2026-11-26):** preserve the current Account Manager implementation; preserve the native `BigWorld.wg_cpdata` protection; preserve the legacy JSON read fallback; no automatic migration on startup; no Windows DPAPI; no additional executables or dependencies; no redesign of credential storage. No claim of verified cryptographic strength is made.

**Verified in this review:** the legacy JSON fallback is read-only, and nothing is written in plaintext. No plaintext write path was identified. No credential is logged or transmitted to analytics. Failures are safe: a read failure blocks writes and preserves the original file, and a save failure rolls back the in-memory records. Focused lobby runtime suite: 125 tests passed, including the three synthetic-credential contracts added in this phase.

**Remaining limitations (not confirmed vulnerabilities):**

- The protection strength of `wg_cpdata` has not been verified in the engine; this is the main residual risk.
- The fallback has no documented origin in this repository, so its legacy use is unknown.
- Physical erasure on delete is not guaranteed.

### Settings panel multilingual font rendering (Phase 10.1)

**Status:** resolved for the reported symptom. The owner reported 10 of 10 manual visual validation points passed on development candidate `0.1.8-beta.4`, target `ct996`, mode `dev`, WOTMOD `build/runs/20261126T051702Z-e07b53bf/output/driftkings.wotmod`, SHA-256 `718160359d5558d011f2e924397d49294b8db6daf55df8f5e46ac9a73e0c36f1`. Thai passed visual validation with no additional Thai font.

**Original issue:** in the settings panel, language options were invisible and some interface text was missing for Japanese, Korean, Simplified and Traditional Chinese, and Thai.

**Failed approaches (do not repeat without a specific technical reason):**

- Adding Windows system fonts (Tahoma, Leelawadee UI, Microsoft YaHei and similar) to the font stack. No effect.
- Selecting the font only by setting the document language and removing the local Warhelios `@font-face` rules. No effect.

**Working solution:**

- The five native Wargaming font files are registered explicitly under distinct DK-prefixed families in `mod/res/gui/gameface/mods/driftkings/settings_window/css/panel.css`:
  - `DKWarhelios`: `coui://gui/gameface/fonts/Warhelios-Regular.ttf` (400) and `Warhelios-Bold.ttf` (700).
  - `DKWarheliosJA`: `WarheliosJA-Medium.ttf` (400) and `WarheliosJA-Bold.ttf` (700).
  - `DKWarheliosKO`: `WarheliosKO-Medium.ttf` and `WarheliosKO-Bold.ttf`.
  - `DKWarheliosZHCN`: `WarheliosZHCN-Medium.ttf` and `WarheliosZHCN-Bold.ttf`.
  - `DKWarheliosZHTW`: `WarheliosZHTW-Medium.ttf` and `WarheliosZHTW-Bold.ttf`.
- The files come from `res/packages/gui-part1.pkg` to `gui-part4.pkg` under `gui/gameface/fonts/`. Read-only inspection established their presence; do not bundle any external font.
- Whole-panel text is selected by `html[lang=ja|ko|zh_cn|zh_tw]` rules in `panel.css`. `app.js` sets the document `lang` attribute from the schema language.
- Each language dropdown option, and the selected value, is given its own language's family by `DK.languageFamily` in `core.js`, through `controls.js`. This works independently of the document language.
- Thai has no Thai-specific native font. Base `DKWarhelios` is used for Thai and was accepted by the owner.
- `zh_tw.yml` had simplified-only characters in nine values, which the Traditional font cannot draw. They were replaced with Traditional forms. Keys are unchanged. This was a character-map correction, not a full terminology review.

**Evidence, kept separate:**

- *Owner-reported runtime observation (manual, in game, on `0.1.8-beta.4`):* 10 of 10 validation points passed.
- *Source contracts (automated):* static tests in `tests/runtime/settings/test_locale_resources.py` (`SettingsFontFallbackTests`) check the registered files, families, language mapping and absence of the diagnostic overlay. Locale validation tests cover catalogue fallback and language selection. Frontend settings suites pass and ESLint is clean on the changed scripts.
- *Cleaned source after diagnostic removal:* the temporary `FONT_DIAGNOSTIC` overlay was removed after validation. The cleaned source has **not** been compiled into a WOTMOD and manually validated as a new artifact. Record this distinction.
- *Unverified internal engine behaviour:* how the Gameface engine maps `html[lang=…]` to the native variants was not established. The mechanism is accepted on runtime evidence only.
- *Not verified:* exhaustive glyph coverage of every catalogue string, and native translation review of the 18 catalogues.

**Diagnostic:** a temporary in-panel overlay (`FONT_DIAGNOSTIC`) existed only in `0.1.8-beta.4`. Do not reintroduce it in production code; add a separate temporary diagnostic only for a new, specific investigation.

### Battle loading table layout (Phase 10.2: complete with documented limitations)

**Status:** closed with documented limitations, after owner runtime validation of the final development candidate `0.1.8-beta.15`, target `na1010` (NA #1010, client revision `2671446`, reference snapshot `2.4.2.5537`). WOTMOD `build/runs/20261127T215612Z-762d2a26/output/driftkings.wotmod`, SHA-256 `1b0b5803603cdd5b6504121b03e49fbbb1a99a3e4031ba5d4a2bdbb1c02a1d55`. No visual or functional change is authorised within this phase.

**Evidence kinds (kept separate):**

- *Static source contracts:* `tests/runtime/battle/test_loading_layout.py` checks that the renderer source keeps the agreed structure (occupied-bounds placement, shared cursor, named header bindings, background host, TAB isolation, state-only writes). They do not execute ActionScript.
- *Arithmetic-model tests:* the same file replays selected column and band arithmetic with plain numbers. They confirm arithmetic, not rendering.
- *Compilation:* `battle_flash` compiled without errors for `0.1.8-beta.15`.
- *Automated regression suites (this repository, `0.1.8-beta.15`):* runtime 923 passed; build 574 passed and 2 skipped; artifact suite passed with its 2 existing skips; configuration validator exit 0.
- *Owner-reported runtime validation (manual, NA #1010, in game):* normal beta.15 loading without visual regressions: PASS. Independent extra fields: PASS. Intentional overlay extra fields: PASS. Disabled configurable native elements: PASS. Native interface restoration: PASS. TAB statistic form: PASS. 1920×1080: WAIVED BY OWNER, NOT VERIFIED. Frontline: WAIVED BY OWNER, NOT VERIFIED. Reported failures: 0. Waivers apply to this phase only and do not replace future release validation.

**Dynamic column architecture.** `flash_source/battle/src/driftkings/battle/components/ratings/tablerenderer.as` lays out each side as one cursor walk outward from the shared contour anchor. Present columns (prestige, class, vehicle text, nick, badges, squads) take their shared width plus one gap; disabled columns take no space. Widths come from the effective configuration and formatted content, and are cached with the widths. Every native element is placed by its occupied bounds, not its origin, so mirrored native components are handled. All writes go through `nativestate` (`setValue`, `base`, `restore`), so no offset accumulates. Asynchronous rating statistics use a high-water reservation estimated from the configured format; the estimate is never displayed.

**Extra fields.** A field lying fully inside the contour span is an *intentional overlay*: it keeps its configured position and reserves nothing. A field outside the contour reserves a horizontal band only if it vertically intersects at least one row of its side; the table then expands outward. A field partly over the contour edge is *ambiguous*: it keeps its configured position, is counted in diagnostics as a conflict during development, and is reserved only if it intersects a row. No field is moved, no configuration is rewritten, and no setting was added. Validated by owner runtime (independent and overlay: PASS).

**Native header bindings.** Team headers (`team1Text` ally, `team2Text` enemy) are found by a bounded search of the owner's ancestors. Header icons are bound by explicit name: ally `leftSquad` and `leftTank`; enemy `rightSquad` and `rightTank`. They move with their header by the same delta, from base positions. A missing name is skipped and nothing else is moved. The enemy binding was confirmed by the 21:47 runtime log (`rightTank` and `rightSquad` moved with the enemy header). The ally icon movement was not confirmed by a logged sibling listing, so it is not independently verified.

**Adaptive background.** Two gradient Shapes (one per side) are inserted directly above the native table background in its parent, so they sit below the headers and icons and above the native artwork. Core opacity 65%, outer fade 24 px outside the occupied content, inner fade limited to half the centre gap. The background follows the exterior edge (including independent extra fields) and covers the header row. Redraws happen only when the geometry key changes. The colour is not sampled from native artwork.

**Viewport fallback.** Overflow is measured against the stage limits. If the normal gutter overflows a side, that side is recomputed with a 2 px gutter; the result is deterministic and reversible. No font shrinking, no truncation, and no statistic is hidden. Oversized arbitrary configurations are not guaranteed to fit every viewport; overflow is reported in `layoutOverflow`.

**Native restoration.** `ratingscreens.as` calls `state.restore()` and `tables.restoreBackground()` when the loading view has no rows. Background Shapes are removed from their parent, and cached header and icon references are dropped at the same point.

**Accepted cosmetic limitations.** The native own-player highlight (`selfBgAlly{N}`) keeps its original 325 px width and is not extended to the expanded row; the sprite cannot be widened safely without scaling its artwork. The background colour is not sampled from Wargaming artwork. Header tank icons follow their header; this layout was accepted without separate review.

**Diagnostics removed.** The temporary `loadinggeometry.as` diagnostic, its header-sibling and row-child probes, its test file and its diagnostic-only assertions were removed after runtime evidence was collected. No diagnostic code or string remains in the battle source or the artifact.

### Crew Management: native Barracks progression (Phase 10.3.1)

**Status:** owner visual validation PASS on NA #1010 for the final candidate `0.1.8-beta.19`, WOTMOD `build/runs/20261127T232938Z-8ac57c01/output/driftkings.wotmod`, SHA-256 `50aba250e70c7a7611b104bdd27a55af27ce560cd55e8487926d5f46d0aac655`. Owner-confirmed: XP cyan, estimated battles green, neutral separator, insufficient-history indicator, "Choose a perk" green, both values on one line, portrait unobstructed, native card dimensions preserved, values consistent with the crew tooltip, no overlap with hover actions. Functional checks not confirmed by the owner: individual configuration toggles, restoration when disabled, search, filters, sorting, card reuse and scrolling. Languages other than the tested one and other realms are not verified.

**Native integration.** The progression is written into the native Barracks card's information container (`Content_base_*`, the container that renders the `additionalContent` position after the skills row). The former absolute overlay (`top:86rem`, 65% black background) is removed. The card keeps its 300×247rem size, its 122rem portrait and its grid. The script (`mod/res/gui/gameface/mods/driftkings/crew_details/details.js`) finds the card through the native `data-dk-barracks-*` attributes added by the NA #1010 Barracks bridge patch.

**Single-line semantic presentation.** Each visible value is one segment, using the existing semantic classes: XP `#00FFFF`, estimated battles `#28F09C`, separator and unavailable indicator `#8C8C7E`, ready and complete `#28F09C`. A missing estimate is a neutral dash, never zero. The full wording stays in the native tooltip. Segments are built with `createElement` and `textContent` only; no `innerHTML`.

**Final rendering approach.** A horizontal flex row (`display:flex; flex-direction:row; flex-wrap:nowrap; white-space:pre`) with independent non-shrinking flex children, the pattern of the existing vehicle carousel fields. The container width is fixed at 200rem; `text-overflow` is not used because it does not apply to a flex container. The box keeps `pointer-events:none`.

**Preserved calculations.** XP and estimated-battle calculations, the progression payload (`lines`, `kinds`), configuration keys and defaults, localization, and the NA #1010 bridge manifest are unchanged. The protected calculation sources (`crew_progression_model.py`, `crew_details.py`, `core/crew_progression.py`, `lobby/crew_progression.py`) are byte-identical to the committed baseline. Any future change to them needs the recorded owner revision flow in `tests/support/baselines.py`.

**Historical reference.** Spoter Crew Extended v6.04 was used as a visual and behavioural reference only (semantic colours; the native skill-cost API). No Spoter code, hooks, dependencies or premium adjustments were imported.

**Lesson (beta.17 and beta.18).** Synthetic DOM tests check the script's logic and the stylesheet text only. They do not establish Gameface layout compatibility. Beta.17 (spans in a block line) and beta.18 (explicit inline spans) passed the synthetic tests and failed in game: only the first value was visible. Only the owner's in-game validation established the flex correction. Future layout changes need runtime validation before they are described as working.

**Known documentation note.** A comment inside `details.js` still describes the line as "inline segments". The rendering is the flex row above. The comment was kept unchanged so the validated artifact remains identical to the source.

### SettingsLab final preview simplification (Phase 10.3.2, owner-accepted)

**Status:** owner approved development candidate `0.1.8-beta.22` on NA #1010. The final SettingsLab design is accepted and no further visual changes are planned. The owner's individual runtime results are not recorded here. WOTMOD `build/runs/20261128T010304Z-933b1943/output/driftkings.wotmod`, SHA-256 `db7d1754bee11c3e883b4eef2a9295270e5181d9ffbc612c2ec9f41fb7f9615c`.

**Owner decision.** Only the Minimap and Vehicle Markers keep a standalone Live Preview. The HUD, carousel and hangar standalone previews, their controls, placeholders and informational messages are removed (`settings_window/js/hud.js` and `test_live_preview.js` deleted; `carousel.js` reduced to the macro evaluator).

**Retained inline previews.** Rich-text formatting, macro and Battle Performance/Results formatting, Vehicle Health style thumbnails (one fixed 79% demonstration sample, `HEALTH_SAMPLE` in `controls.js`) and carousel inline field examples. `richtext.js` was not redesigned.

**Horizontal formatting correction.** Each logical line is a flex row (`display:flex; flex-direction:row; flex-wrap:nowrap; white-space:pre`) with non-shrinking inline segments, so mixed-colour values such as WN8/EFF/DIFF stay on one line. Explicit breaks (`<br>`, `<br/>`, newline characters) are kept.

**Sample macros.** `{wnx}`, `{xwn8}` and `{c:wnx}` resolve in the sample preview (covered by `test_rich_text_preview.js`); unsupported macros are marked, not silently dropped.

**Development warning.** The construction banner (`panel.constructionNotice`), its element, its reserved space and its CSS are removed.

**Localization.** Obsolete preview and banner keys (`panel.constructionNotice`, `panel.hud.*`, `panel.live.disabled|nonVisual|alt`) are removed from all 18 catalogues. Catalogue parity passes with zero untranslated keys (`build_tools/validate_locales.py`).

**Narrowly approved native catalogue revision.** Removing `hud.js` changes the settings-window script list, so the `DriftkingsModSettings` entry differs from the native baselines of `native_crew`, `native_carousel` and `native_marks`. The owner authorised exactly this entry. `tests/fixtures/native_baselines.json` records `approved_catalog_revisions` with the historical hash `8b39688a…` and the approved hash `394ec57b…`. `changed_catalog_entries` in `tests/support/baselines.py` skips an entry only when both hashes match exactly. Historical hashes are never replaced, and there is no wildcard or automatic approval. `tests/build/test_own_window_catalog.py` now expects 334 packaged assets instead of 335, because `hud.js` is no longer packaged. Negative checks on temporary fixtures confirmed that the exact approved revision passes and that a different current hash, a mismatched historical hash, an altered baseline and an unrelated modified entry are all reported.

**Sizes (tracked files against `df8427a1`).** 34 files: 147 lines added, 933 removed. The new rich-text regression test `tests/frontend/settings/test_rich_text_preview.js` adds 78 lines. Localization accounts for 162 removed lines (9 per catalogue).

**Validation.** Frontend 32 suites passed; ESLint 0 warnings; localization parity passed with 0 untranslated; build suite 574 tests passed with 2 pre-existing skips; artifacts suite 9 tests passed with 2 pre-existing skips.

**Synthetic versus Gameface validation.** The frontend suites use a synthetic DOM (`tests/support/frontend/dom_fixture.js`, Node `vm`). They check structure, logic and stylesheet text. They do not establish Gameface layout. The horizontal-row correction and the removal of the banner were validated only by the owner's in-game testing of candidate beta.22.

**Remaining limitations.** The Python presenter still emits a `carouselPreview` payload (`settings/panel/presenter.py`) and a runtime test covers it. The JavaScript no longer reads it. Removing it would change Python sources and require a rebuild, so it is retained. The 1920×1080 and Frontline checks stay owner-waived from Phase 10.2.

### Other pending work

- Corrected installer compilation and isolated executable validation.
- Isolated install and uninstall validation, and full updater and rollback validation in an isolated client copy.
- Real promotion-gate validation, only when the owner authorises a dispatch.
- Restoration of the live NA client, only when the owner authorises it.
- Owner decision on legacy directories with unique material: `build/debug/beta/0.1.7-beta.2` (unreferenced WOTMOD `f1735c37…`), `build/previous/` (WOTMOD `7b64e5e0…`, see `CT_COMPATIBILITY.md`), `build/installer/` (0.1.7-beta.2 Setup `a490ab1a…`), `build/experiments/`.
- Correction of existing visual defects, with focused and impact-proportional validation.
- Account Manager: no further work is planned. The native `wg_cpdata` protection strength remains an unverified limitation (see the Phase 9 review above).
- Native review of the translated moderation descriptions in all 18 catalogues.
- Standard WGMods moderation review before public distribution, and the official WGMods listing URL (not supplied).

## 11. Safety rules for AI assistants

Do not:

- modify an installed game client, or launch or terminate a live game, without explicit owner authorisation;
- run an installer or uninstaller on the development host;
- modify the Windows registry, uninstall records, antivirus settings or repository protections;
- access private signing keys, credentials or tokens;
- publish, sign or replace a release, or modify `main`, without authorisation;
- delete unique evidence or unknown files, or run destructive cleanup;
- invent compatibility claims or treat a historical realm selection as permanent;
- rebuild published artifacts or reintroduce retired global mirrors.

For executable installer tests, use an isolated Windows environment with its own registry and drives, and drive it from PowerShell with argument arrays. Git Bash rewrites `/` switches (`/VERYSILENT` became a Git path). Never test the installer against a folder on a host that has a live client, because discovery scans every fixed drive and the registry.
