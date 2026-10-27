# Documentation status

Updated: 27 October 2026. Commands and source paths in these guides are relative to the repository root unless explicitly stated otherwise.

## Release baseline

- Beta: [0.1.3-beta.2](https://github.com/dkruben/Driftkings_SettingsLab/releases/tag/v0.1.3-beta.2), built from `aec3da8` with 11 verified assets and an Ed25519-signed updater manifest.
- Stable: [0.1.3](https://github.com/dkruben/Driftkings_SettingsLab/releases/tag/v0.1.3), targeting WoT 2.4.1.1; release preparation and publication recorded in [PLANO_STABLE_0_1_3.md](PLANO_STABLE_0_1_3.md).
- Game target: WoT `2.4.1.1`, Wargaming EU/NA/ASIA. Build source: configured NA installation; source reference: EU `2.4.1.5504`.
- Canonical defaults: author's EU profile, including clock fields, panel positions, carousel and marker layouts. Settings-window scale: 140%; opacity: 94%. Existing personal configuration takes precedence.

## Verified checks

Current validation baseline: 443 Core and 27 settings-panel tests on Python 2.7/3, 36 installer/build tests on Python 3, Gameface regression suites and ESLint. Eighteen language catalogues contain 1491 component keys and 243 panel keys. The native build compiles 313 Python modules and verifies the full modpack; release-specific CI, installer and signature results are recorded in the stable plan.

The all-pages settings test opens and applies every current feature definition with unchanged values. Marker tests cover property scrolling, font aliases, invalid references, sample toggles and limits. Source defaults and the generated Python fallback are synchronized. These checks do not establish pixel-perfect rendering in the client: the latest marker, font and layout changes still need visual acceptance in game.

## Documentation policy

The [README](../README.md) and [contribution guide](../CONTRIBUTING.md) live at the repository root. Feature guides and historical reports live under `docs/`. The Git ignore rules include Markdown only; local JSON/CSV snapshots, study scripts and generated outputs remain excluded. Third-party dependencies and generated build trees keep their own files and are not project documentation.

Dated reviews retain their original evidence, line references, counts and conclusions. Update notes distinguish historical findings from the current implementation. No new source audit or statistical study is implied by reorganizing a report. Research prototypes under `wn8-study/` are not additional production ratings; reproduction requires the original local scripts and data.

## Current implementation changes

- The clock is configured under General settings, in `main.json` through `clock.enabled` and `clock.formats`.
- HangarEfficiency is removed. Use vehicle carousel statistics, service-record ratings or the relevant Marks of Excellence panel.
- Vehicle markers use the structured five-file layout without XMQP, team/state/ALT contexts and an editable tank sample. The property column has its own scrollbar.
- ActionScript fields use the client font library. Marker `xvm`/`XVMSymbol` aliases resolve to `$FieldFont`; legacy private glyphs map to a supported bullet. Fixed colours use `#RRGGBB` with existing numeric converters.
- WN8 uses random-battle statistics; WNX uses its own assistance-aware calculation and expected values. The EU battle overlay defaults to WN8, EFF and DIFF; WNX remains configurable.

For current commands and release procedures, use [CONTRIBUTING.md](../CONTRIBUTING.md). For feature guides and historical reports, use the [project overview](../README.md).

## Naming changes after beta.2

The source branch uses descriptive marker/statistics module names and the **Driftkings** palette at index 1. New templates use `stat-available`; installed profiles and statistics caches retain read compatibility. Original font names, provider URLs, integration IDs and upstream credits are preserved. These source changes do not replace the already-published beta.2 assets.

## Colour format after beta.2

Colour settings and defaults use `#RRGGBB`. Legacy numeric prefixes and bare hex strings are no longer accepted. Native APIs still receive numeric RGB/ARGB values through the existing converters. The settings panel saves hash-prefixed strings directly; HTML templates do not prepend another hash. Tests cover rejection of legacy strings and unchanged open/apply behaviour for the corrected defaults.

## Python Gameface architecture after beta.2

The development branch centralizes Python Gameface adapters under `driftkings/gameface`, with shared `core.py`, `payloads.py`, `registry.py`, and separate `batalha`/`hangar` packages. The 14 interface contracts still come from `interface_catalog.py`; native resource IDs and visual assets are preserved. Scaleform is now centralized under `flash`; functional calculations and data collection remain in the feature modules. See the [migration inventory and execution log](PLANO_GAMEFACE.md). Client acceptance checks remain pending; this refactor does not replace the published beta.2.

Gameface refactor validation: 429 Core tests on Python 2.7/3, 27 settings tests on both runtimes, 33 installer tests, JavaScript/lint and the native debug build passed. [Source CI passed for c7189f8](https://github.com/dkruben/Driftkings_SettingsLab/actions/runs/40421997019). The build validates 301 Python modules; visual assets and all non-Python catalogue fields are unchanged.

## Python Flash/Scaleform architecture after beta.2

The development branch centralizes Flash views, DAAPI metas and native presentation bridges under `driftkings/flash`. `flash/battle/registry.py` registers the native battle package and preserves the ten aliases from `interface_catalog.py`; `flash/core.py` owns the existing overlay scene. Shared HUD state, functional calculations and data collection remain outside the presentation layer. The Gameface package and AS3/SWF assets are unchanged. The [local plan](PLANO_FLASH.md) records the inventory, per-step commits, validation and client acceptance checks. No measured FPS improvement or new published release is implied.

Flash refactor validation: 441 Core tests and 27 settings tests on Python 2.7/3, 33 installer tests, JavaScript/lint, catalogue/defaults/locales checks and the native WOTMOD build passed (317 Python modules). [Source CI passed for 56138ce](https://github.com/dkruben/Driftkings_SettingsLab/actions/runs/40424997042). Native client acceptance and comparative performance measurements remain pending.

## EU replay log corrections — 27 October 2026

The battle clock no longer accesses unsupported Scaleform sharpness/thickness properties; MainGun and marks cards explicitly declare and use the native Warhelios regular/bold fonts. Replay calibration skips flat/inverted curves and uses the existing approximation without modifying installed caches or live-battle calculations. See the [EU log analysis](EU_LOG_2026-10-27.md) for evidence, 444 Core tests on both Python runtimes, native build results and pending client checks.

## Settings panel functional report

The [settings panel report](RELATORIO_PAINEL_CONFIGURACAO.md), in Portuguese, inventories navigation, editing/save behaviour, controls, previews, both profile mechanisms, updater/restart actions, battle restrictions, the 34 component definitions and all 23 backend actions. It documents the current implementation detail that Apply also persists values, with links to the source modules.

## Fontes e símbolos — 27 outubro 2026

Correção `4d1b961` com [CI aprovado](https://github.com/dkruben/Driftkings_SettingsLab/actions/runs/40541534633): fontes de símbolos reais incorporadas nos dois SWF e disponibilizadas ao Gameface; adaptadores preservam Unicode, nomes de fontes e entidades HTML. Plano e validação em [PLANO_FONTES.md](PLANO_FONTES.md); recursos e limites em [FONTES.md](FONTES.md). Requer confirmação visual no cliente.

## Painel redesenhado — 27 outubro 2026

Integrada a interface do autor em `1a5b021`/`ddbf608`, com [CI aprovado](https://github.com/dkruben/Driftkings_SettingsLab/actions/runs/40561989621), preservando o seletor de espectro original, fontes e contrato Python. As 35 páginas/1104 controlos são testadas com schemas reais e os 18 catálogos incluem 243 chaves de painel. Novas amostras: minimapa, HUD, texto e carrossel. [Plano e registo](PLANO_PAINEL_CONFIGURACOES.md); [relatório funcional atualizado](RELATORIO_PAINEL_CONFIGURACAO.md). Validação gráfica em jogo pendente: Computer Use/browser indisponíveis nesta sessão.

## Limpeza de fontes e artefactos — 27 outubro 2026

Retirados quatro módulos Python sem consumidor runtime, oito mapas Gameface não empacotados, o SWF antigo substituído pelo gerador e caches/saídas antigas de Wwise/installer. O aviso isolado do HangarEfficiency retirado foi consolidado neste estado. Mantidos os recursos ativos, fontes de áudio e estudos citados nos relatórios. [Inventário e validação](PLANO_LIMPEZA.md). O plano passa de 317 para 313 módulos Python, sem alterações às seleções de assets, defaults ou dependências.

Validação da limpeza: 443 testes core em Python 2.7/3, testes frontend e 36 testes de instalação aprovados; 313 bytecodes, SWF de batalha e três auxiliares recompilados isoladamente. A build completa requer rever o alvo de jogo, pois as instalações EU/NA já estão em 2.4.1.1 e o projeto continua em 2.4.1.0.

Limpeza enviada em `7be22a2`, com [CI aprovado](https://github.com/dkruben/Driftkings_SettingsLab/actions/runs/40564708020). O plano documenta a remoção dos temporários da própria verificação.

## Atualização da referência e alvo — 27 outubro 2026

A atualização em WoT_Tools disponibilizou a referência EU 2.4.1.5504. Alvo de desenvolvimento atualizado para WoT 2.4.1.1, oito SWC sincronizados e contrato/hashes dos marcadores revistos em EU e NA. Os três patches Gameface mantêm operações e bytes de origem; metadados atualizados para NA #987. A build completa voltou a passar, resolvendo o bloqueio registado na limpeza. [Plano e evidência](PLANO_ATUALIZACAO_2_4_1_1.md). As releases publicadas continuam a visar 2.4.1.0; sem alteração de tag, publicação ou instalação EU. Aceitação visual em jogo pendente.

Atualização do alvo enviada em `e019622`, com [CI aprovado](https://github.com/dkruben/Driftkings_SettingsLab/actions/runs/40567140916). WOTMOD/ZIP de desenvolvimento regenerados para 2.4.1.1; hashes e verificações no plano.
