# Security policy

## Supported versions

| Version | Channel | Supported |
| --- | --- | --- |
| 0.1.7-beta.1 | Beta in preparation | Pending publication |
| 0.1.6 | Stable | Yes |
| 0.1.6-beta.1 | Archived beta | Update to stable 0.1.6 |
| Older releases | — | No; update first |

Stable 0.1.6 and the new beta target World of Tanks 2.4.1.1 on Wargaming EU, NA and ASIA. The historical 0.1.6-beta.1 validation covers all three regions; it does not establish validation of the new beta. The project owner confirmed the new locally installed EU test build; the published release package requires its own validation record before stable promotion.

## Reporting a vulnerability

Please do not open a public issue for a security problem.

1. **Preferred:** use [Report a vulnerability](https://github.com/dkruben/Driftkings_SettingsLab/security/advisories/new) on GitHub to send a private advisory.
2. **Alternative:** ask the author for a private conversation on the [Driftkings Discord](https://discord.gg/k2Stjv5fS5), without posting details in public channels.

Include the mod version, game version and region, the steps to reproduce and the impact you expect. Remove account names, passwords, tokens and other personal data from logs before sharing them. You will get an acknowledgement as soon as possible; fixes are released through the normal beta and stable channels.

## Signed updates

The in-game updater only installs releases whose `release.json` manifest carries a valid Ed25519 signature from a key built into the mod. The manifest pins the package size and SHA-256, and the download is checked against both before installation. A release without a valid signature is rejected. Clients older than this check must update once manually to receive it.

Stable releases promoted through this process are rebuilt and signed anew from an approved beta, and carry a `promotion.json` asset naming the source commit, the beta and the validation record. Stable `0.1.5` and older predate it; see [docs/releases/README.md](docs/releases/README.md).
