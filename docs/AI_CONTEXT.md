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
- Corrected: ASIA and CN are project-scope realms. `validation_record.py` lets one release record mark them OUT OF SCOPE for that release only; EU and NA can never be marked out of scope.
- The EU reference snapshot in `toolchain.local.json` is the wrong version (see section 5).
- `validate_build_data.py` and `vehicle_markers_patch.py` keep a `995` fallback for the historical native lock that has no `clientBuild` field. This is a legacy contract, kept on purpose.

## 10. Pending work

- Corrected installer compilation and isolated executable validation.
- Full updater execution and rollback validation in an isolated client copy.
- Real promotion-gate validation, when the owner authorises a dispatch.
- Restoration of the live NA client, once the owner authorises it.
- Owner decision on the remaining legacy directories that hold unique material: `build/debug/beta/0.1.7-beta.2` (unreferenced WOTMOD `f1735c37…`), `build/previous/` (WOTMOD `7b64e5e0…`, documented in `CT_COMPATIBILITY.md`), `build/installer/` (0.1.7-beta.2 Setup `a490ab1a…`) and `build/experiments/` (isolated experiments; some fog-related strings).
- Recovery of the previous Remove Fog implementation. **Not implemented.** It needs a current Wargaming Fair Play review before any distribution.

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
