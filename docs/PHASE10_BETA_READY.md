# Fase 10 — beta protegida 0.1.2-beta.1

Estado: **FASE 10 READY FOR REAL BETA TEST.** Todos os gates técnicos passaram; teste real no WoT ainda não executado.

Build normal: `python -B build_tools/build_lab.py --release`. Sem fallback em claro; nenhum deployment, push, tag ou upload. Fase 11 não iniciada.

## Entrega

1. **PJOrion:** 1.3.5.501; seis ficheiros originais e configuração inalterados, hashes verificados contra baseline e POC. CLI `--protect-bytecode-file=<staging absoluto> /exit`, apenas bytecode compilado em staging isolado.
2. **Profile:** SAFE, allowlist fixa de três módulos; nenhum módulo adicional protegido.
3. **Módulos e hashes SHA-256:**

| Módulo | Input | Output |
|---|---|---|
| `Driftkings/core/marks_calculator.pyc` | `974a734472071762afe6130cefa403c9b6b446e3c099fb4504f70177002cea54` | `474b4111c10f141a7c37f567c6304f75b15a2706ba8eb08c6e0ad7ab06a05f39` |
| `Driftkings/core/updater/versioning.pyc` | `6280ec875368a1cbe9592f4965d3d0dbbf726bd5368e58b17e5e46682bf7d197` | `152cc59a805c0f9d8cc82377c39d618be0c44ea859572cc48375c3f5bbcfb6eb` |
| `Driftkings/core/updater/manifest.pyc` | `5ca70d145e143089e9475878ad36e3625087fafa13e66266adc7478a8f0391c5` | `2b730b5732ef11e243388dadb1300ac28e652a45d8077950ea8419d039dc1e7b` |

4. **Baseline/hash provenance:** branch `main`, commit `3c9a4639c3ffbd109f71b5637defb92ab9c96794`, VERSION `0.1.2-beta.1`. Working tree completo, helpers pré-build, fontes, ferramentas e Python arquivados em `build/obfuscation/resume-20261008-234210/baseline.json`. Todos os hashes funcionais permanecem iguais após build/suite.
5. **Python 2.7.18 x64:** staging e package PASS, relatórios finais presentes. 15 contratos Version/Manifest, 12 smokes updater, 33 componentes, Settings registration e 20 090 comparações numéricas + quatro testes Marks por execução.
6. **Python 2.7.15 x86 (Hg SourceTree):** mesmos gates PASS, relatórios finais e paths reais `.pyc` protegidos comprovados; exit code isolado não foi usado como evidência.
7. **Package diff:** controlo A da mesma source vs B protegido: exatamente os três módulos da tabela diferem. Nenhuma alteração de helpers, recursos, outros bytecodes ou metadata. Beta local é byte a byte igual ao WOTMOD final usado nos smokes de package.
8. **WindowsFiles:** helper presente, metadata schema/size/SHA coerentes; helper SHA `9a544c53c35e40c5da9450f2b046578995f69ff87c50dc90bbbe3728472cd5ce`. READY/V/R reais (35 V + 1 R em cada smoke de package). `windows_files.pyc` igual ao controlo; fonte Python e C# inalteradas; sem PS/cmd/.ps1/.bat em recursos.
9. **Installer:** helper package SHA `48485ef6b6af553a8ff728c875c7359d0cff75927101d360f5e06befb7890eef`, size 19 968; metadata e bytes iguais ao controlo. `build_unified.py` validou build-report/helper/source antes de empacotar. A suite nativa recompila depois o helper local (PE/MVID não determinísticos), resultando em SHA local diferente, sem alterar a beta. Essa diferença está explicitamente registada em `final-inspection.json`; o report local posterior não foi falsificado como report histórico. Nenhum helper remoto ou alteração funcional.
10. **Inspeção:** CRC PASS; identity `driftkings.unified`; VERSION `0.1.2-beta.1`; 396 entradas únicas; 247 pycs com magic Python 2.7; entrypoint único; 50 assets Gameface, SWF/resources/helpers presentes; zero source `.py`.
11. **Testes:** suite completa 745 total / 744 PASS / 0 FAIL / 0 ERROR / 1 skip Python 2 específico (já validado no runtime Py2 na Fase 10.3). Updater 178/178, Results 14/14, Installer 36/36, path security 15/15, Marks/Settings/hangar incluídos. Nove suites JavaScript PASS, nove contratos Python/Flash PASS, 12 catálogos i18n/35 secções com keys inglesas preservadas PASS; `git diff --check` PASS. Suite observada: zero PowerShell, cmd ou shell=True.
12. **Bitdefender:** NO_ALERT confirmado explicitamente pelo utilizador para 09/10/2026 00:42:10–00:47:30 Lisboa; registo próprio em `build/obfuscation/real-beta/bitdefender-build-gate.json`. Nenhum probe novo, exclusão ou alteração de proteção. Não repetir automaticamente se surgir alerta.
13. **WOTMOD:** `build/beta/0.1.2-beta.1/Driftkings.wotmod`.
14. **Tamanho final:** 6 773 910 bytes.
15. **SHA-256 final:** `3fcefee6b47c1abba2897ed2bacfcddec3640f9d2241489ac1b250c1030893d3`.
16. **release.json:** `build/beta/0.1.2-beta.1/release.json`, schema 1, beta, gameVersion 2.4.0.2, tamanho/hash finais verificados. URL futura de release ainda não publicada. Pasta beta contém apenas WOTMOD, SHA-256 e release.json; relatórios internos não são assets públicos.
17. **OPEN SECURITY HARDENING:** primeira extração do WindowsFiles helper precede validação nativa completa dos ancestrais da cache. Finding aprovado preservado e não corrigido neste build. ReplaceFileW mantém os limites já documentados, sem promessa de rollback universal.
18. **Decisão:** FASE 10 READY FOR REAL BETA TEST. Teste real da beta/updater continua pendente e não está implicitamente aprovado pela validação offline.

## Mudanças nesta retoma

`obfuscation_runtime.py`: setup dos recursos WindowsFiles nos testes, bytes reais do package, observação READY/V/R e contratos VERSION/ordering. `build_safe_beta.py`: changelog factual. `windows_files_regression_suite.py`: output isolado dos resultados sem substituir evidência anterior. Nenhuma source funcional, allowlist, profile, CLI PJOrion ou helper C# alterados.

## Evidência local

- `build/obfuscation/report.json` e `resume-release.log`.
- `build/obfuscation/safe/runtime-*.json`, `marks-*.json`: staging/package nos dois runtimes, hashes e paths carregados.
- `build/obfuscation/safe/final-inspection.json`, `ui-validation.json`, `source-regression/source.json` e `.log`.
- As alterações preexistentes do working tree, incluindo SWF e zip removido, foram preservadas. A release oficial beta.6 mantém o hash inicial.
