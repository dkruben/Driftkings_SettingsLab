# Release validation and promotion

This is the human guide for the release gates. The full technical reference is [docs/AI_CONTEXT.md](../AI_CONTEXT.md), section 7. Commands run from the repository root.

## Principles

- **A stable is built from its own committed version.** Promotion never renames a beta. The stable is compiled again, has its own artifact names and manifest, and receives a new signature.
- **A beta is optional.** A stable can be published directly. A beta-backed stable is used when a beta was published and tested. The two routes are distinct artifacts when their versions differ.
- **Compilation, signing and publication are local steps.** The build needs the game client, and the signing key stays offline. Only the read-only gate runs on GitHub.
- **Approvals bind complete digests.** The approval names the complete SHA-256 of the inventory (`SHA256SUMS.txt`) and of the validation record. Abbreviated digests are for display only.
- **Each regional result is evidence for that region only.** A region is never claimed compatible by another region's result, nor by matching version numbers.
- **Traceability goes in `promotion.json`.** The updater rejects unknown fields, so `release.json` carries no extra keys.

## Validation records

A validation record is a plain-text file with fixed rules. It records what a person checked on a candidate, using `PASS`, `FAIL`, `NOT TESTED` or `NOT APPLICABLE`. The tools never fill in results.

- Beta records live at `docs/releases/<beta-version>-validation.md`. Create one with `python build_tools/validation_record.py new <beta> --commit <sha> --package-sha256 <sha>` and check it with `validation_record.py check <beta>`. The [template](validation-template.md) shows the structure.
- Direct stable records are supplied to the gate as a file (`--record`) and bind to the stable version, the artifact commit and the package digest.
- Any production realm (EU, NA, ASIA or CN) can be marked `OUT OF SCOPE` by one release record, with owner approval, for that release only. Every region must still be accounted for, and an out-of-scope region is never claimed as verified. No realm has permanent priority.

The evaluation refuses a record when the decision is not `APPROVED`, the approver or date is missing, the commit or version does not match, a blocking check is not passed, a `BLOCKER` issue is open, or an automatic check has no evidence.

## Direct stable (no beta)

1. `python build_tools/promote_release.py prepare --stable <X.Y.Z>` sets `release.json` and `VERSION`. Commit and push; CI runs on that commit.
2. `python build_tools/promote_release.py build --stable <X.Y.Z> --target <target>` compiles, attaches the installer and the WGMods archive, signs, stamps and promotes. It takes no record, because the record binds the finished package.
3. Write the validation record for the stable, bound to the artifact commit and the package digest.
4. `python build_tools/promote_release.py check --stable <X.Y.Z> --record <file> --record-digest <full-sha256> --commit <sha> --digest <full-sha256>` runs the read-only gate.
5. Request the approval with the `promotion-gate.yml` workflow, route `direct`, the complete digests and the record file. The approval happens in the protected `stable-release` environment, and it has no waiver.
6. `python build_tools/promote_release.py publish --stable <X.Y.Z> --record <file> --target <target>` previews the assets. Then `--confirm v<X.Y.Z>@<digest>` publishes exactly those bytes, and the remote asset digests are verified.

## Beta-backed stable (optional)

1. Publish and test the beta as a prerelease, and record its validation.
2. Prepare, build, check and publish with `--beta <beta>` in place of `--stable`. The stable commit must differ from the approved beta only in permitted metadata; the tool compares the two.
3. Approve through the gate with route `beta`. The approval binds the complete artifacts digest.

## Frozen candidates

A candidate is **STAGING** while it can still change, for example while an installer is attached. It becomes **FROZEN** once it is stamped or signed. A frozen candidate is never edited, rebuilt or repackaged. Publication only verifies and uploads its bytes.

## Historical releases

Releases published before this process (for example 0.1.7, built through `0.1.7-beta.2`) keep their original records and checksums. They remain valid under their own contract.
