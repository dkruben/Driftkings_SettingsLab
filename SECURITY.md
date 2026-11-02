# Security policy

## Supported versions

| Version | Channel | Supported |
| --- | --- | --- |
| 0.1.5-beta.3 | Beta | Yes |
| 0.1.4 | Stable | Yes |
| Older releases | — | No; update first |

Both supported versions target World of Tanks 2.4.1.1 on the Wargaming EU, NA and ASIA clients.

## Reporting a vulnerability

Please do not open a public issue for a security problem.

1. **Preferred:** use [Report a vulnerability](https://github.com/dkruben/Driftkings_SettingsLab/security/advisories/new) on GitHub to send a private advisory.
2. **Alternative:** ask the author for a private conversation on the [Driftkings Discord](https://discord.gg/k2Stjv5fS5), without posting details in public channels.

Include the mod version, game version and region, the steps to reproduce and the impact you expect. Remove account names, passwords, tokens and other personal data from logs before sharing them. You will get an acknowledgement as soon as possible; fixes are released through the normal beta and stable channels.

## Signed updates

The in-game updater only installs releases whose `release.json` manifest carries a valid Ed25519 signature from a key built into the mod. The manifest pins the package size and SHA-256, and the download is checked against both before installation. A release without a valid signature is rejected. Clients older than this check must update once manually to receive it.
