# DriftKings updater beta controlada

Esta preparação muda a fonte única VERSION de 0.1.0 para 0.1.1-beta.1 e mostra
DriftKings seguido dessa versão na metadata da página da Settings. Não altera a
lógica do updater, Installer, helper, restart, componentes ou persistência.

O commit inclui as Fases 2–7 previamente aprovadas, os respetivos testes e relatórios.
A remoção preexistente de res/icones_foco_variantes.zip fica fora do commit.
O SWF gerado DriftkingsBattle.swf também fica fora do commit desta preparação;
não houve alteração nos fontes de batalha.
As fixtures do Installer usam VERSION no package anterior e no ticket; a expectativa
installedVersion do serviço acompanha VERSION. As verificações continuam iguais.

## Changelog

- Updater end-to-end beta test
- Safe staging and SHA-256 verification
- Installer/helper restart validation

## Build de teste sem PJOrion

Com o jogo fechado, executar `build_tools/run_build.ps1 -Mode release`.
O pipeline unificado atual aceita Mode mas usa a mesma compilação Python 2.7 para
ambos os modos; não existe uma compilação distinta otimizada release. Não se altera
o conceito de build nesta fase. PJOrion não é executado. O output canónico é
build/unified/Driftkings.wotmod; os três assets finais são copiados para build/release/.
Essa cópia é byte a byte e o SHA-256 é calculado sobre o asset final.

Cliente alvo: EU 2.4.0.2, conforme sources/version.xml (#966).
O marcador de extração .version_name indica 2.4.0.5473; não é usado como versão
do cliente no manifest. Identidade: driftkings.unified. Entry point único:
res/scripts/client/gui/mods/mod_Driftkings.pyc.

## Publicação posterior — exige confirmação explícita

Ainda não executar os comandos seguintes. Primeiro rever branch, commit, tag e
working tree. A tag anotada deve apontar para o commit da preparação beta.

```powershell
git push origin main
git push origin v0.1.1-beta.1
gh release create v0.1.1-beta.1 build/release/Driftkings.wotmod build/release/release.json build/release/Driftkings.wotmod.sha256 --repo dkruben/Driftkings_SettingsLab --verify-tag --prerelease --latest=false --title "DriftKings 0.1.1-beta.1" --notes-file build/release/release-notes.md
```

Em alternativa, GitHub → Releases → Draft a new release → selecionar a tag
v0.1.1-beta.1; título DriftKings 0.1.1-beta.1; copiar o changelog; anexar os três
assets de build/release/; marcar prerelease e desmarcar Latest antes de publicar.

O download no release.json usa a URL oficial prevista para esta tag e asset. Não
significa que o asset já esteja publicado. Depois de publicar, confirmar que
browser_download_url do asset é exatamente esse URL e descarregar novamente os
assets para comparar tamanho, SHA-256 e conteúdo do manifest.

## Teste real

Manter a instalação local em 0.1.0 até ao teste do updater; não instalar a beta à mão.
Na Settings selecionar updateChannel = beta e Procurar atualizações. Confirmar
0.1.1-beta.1 disponível, compatible = true, changelog literal e a sequência:

AVAILABLE → DOWNLOADING → VERIFYING → READY → INSTALLING → RESTART_REQUIRED
→ restart → installed.

No novo arranque, confirmar a metadata DriftKings 0.1.1-beta.1, VERSION carregada,
hash do package e resultado validado. Seguir também a checklist de UPDATER_UI.md,
incluindo cancelamento, Mais tarde e o caso WGC arrancar antes da instalação.
O restart via WGC ainda não está certificado no cliente. Esta preparação não faz
deployment, push, publicação ou alterações na instalação do jogo.

## Resultado desta preparação

- Python: 676/676; inclui os testes do updater e helper nativo.
- Settings Gameface, Hangar/TechTree, dependências e UI bridge: passaram.
- Python 2.7 smoke: 7/7 sobre fontes e 7/7 sobre módulos compilados da beta.
- Contratos Python/Flash: 9; i18n: 12 catálogos, zero erros.
- CRC, identidade, versão, entry point, recursos e 245 módulos Python 2.7: válidos.
- git diff --check: passou.

Asset final: build/release/Driftkings.wotmod, 6 677 296 bytes.
SHA-256: e4aa1a21ecaf19a082ffedd17dde30fe8b6fb0dfc0c24180ad3fd648570e0ee1.
Relatório completo de package: build/final-validation/package-report.json.
Lista de ficheiros do commit: build/release/commit-files.txt.

Conteúdo de build/release/release.json (UTF-8 sem BOM):

```json
{
  "schema": 1,
  "version": "0.1.1-beta.1",
  "channel": "beta",
  "gameVersion": "2.4.0.2",
  "file": "Driftkings.wotmod",
  "size": 6677296,
  "sha256": "e4aa1a21ecaf19a082ffedd17dde30fe8b6fb0dfc0c24180ad3fd648570e0ee1",
  "download": "https://github.com/dkruben/Driftkings_SettingsLab/releases/download/v0.1.1-beta.1/Driftkings.wotmod",
  "changelog": [
    "Updater end-to-end beta test",
    "Safe staging and SHA-256 verification",
    "Installer/helper restart validation"
  ]
}
```
