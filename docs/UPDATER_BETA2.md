# DriftKings 0.1.1-beta.2

Corrige a falha ao seguir redirects HTTPS no Python 2.7 do WoT:
TypeError: super() argument 1 must be type, not classobj.
HTTPSRedirects chama explicitamente HTTPRedirectHandler.redirect_request, pois
urllib2 usa classes de estilo antigo. Mantém validação HTTPS/hosts antes do redirect,
verificação de certificados, limites de download e toda a lógica de instalação.
Acrescenta logging da exceção original e um teste de redirects no smoke Python 2.7.

VERSION muda exclusivamente em source/scripts/client/Driftkings/__init__.py:
0.1.1-beta.1 → 0.1.1-beta.2. A Settings apresenta essa mesma versão.
Não há alterações em componentes, Installer/helper, restart, configs ou PJOrion.
O SWF gerado e a remoção anterior do ZIP ficam fora do commit.

Build de teste: entrada release existente, sem PJOrion. O pipeline unificado atual
usa a mesma compilação para debug/release, conforme documentado em UPDATER_BETA.md.
Assets finais em build/release/: Driftkings.wotmod, release.json e checksum SHA-256.
Cliente EU 2.4.0.2; identidade driftkings.unified; entry point mod_Driftkings.pyc.
A beta.1 publicada permanece intacta. A beta.2 é prerelease, nunca Latest stable.

## Substituir a beta.1 em READY

READY preserva o download entre arranques e bloqueia novas pesquisas. Mudar de
Stable para Beta recupera novamente esse staging: não elimina a beta.1.
Antes de retomar o teste, com WoT fechado e sem helper ativo, identificar pelo
release.json a pasta download-* da beta.1 na cache do updater. Mover apenas essa
pasta para um backup fora da cache, preservando todos os ficheiros de diagnóstico.
Não apagar configurações ou packages instalados e não alterar tickets/resultados.
Se já houver instalação preparada, cancelar pelo fluxo existente e aguardar
confirmação antes de qualquer manutenção manual da cache.

Depois abrir WoT com a base corrigida 0.1.0, escolher Beta e procurar atualizações.
Confirmar latestVersion 0.1.1-beta.2, compatible=true. Descarregar, verificar READY,
preparar helper, confirmar RESTART_REQUIRED e só então reiniciar pelo diálogo.
No novo arranque, validar resultado, VERSION carregada e SHA-256 do package.
O fluxo real WoT/WGC permanece em teste até haver confirmação pós-restart.

## Validação do artefacto

- Suite Python: 677/677, incluindo testes nativos de instalação/rollback.
- Smoke Python 2.7: 8/8 sobre fontes e sobre bytecode da beta.2.
- Settings Gameface, Hangar/TechTree, dependências e UI bridge: passaram.
- Contratos Python/Flash: 9; i18n: 12 catálogos sem erros; diff --check passou.
- CRC, recursos, identidade e entry point válidos; 245 módulos Python 2.7
  validados e respetivos fontes analisados, defaults/imports passivos corretos.

WOTMOD: 6 677 528 bytes.
SHA-256: 9963d1e27e4d03823a7d8e93fa6e1879bdda3f4cec149325bb99336419158c02.
Manifest schema 1, canal beta, gameVersion 2.4.0.2, download oficial:
https://github.com/dkruben/Driftkings_SettingsLab/releases/download/v0.1.1-beta.2/Driftkings.wotmod

No cliente de teste, a pasta identificada da beta.1 é:
C:/Games/World_of_Tanks_EU/mods/configs/Driftkings/cache/update/download-pmxaq_.
Continha apenas release.json e Driftkings.wotmod.ready; não havia helper ativo.
Manutenção dessa pasta exige jogo fechado e reconfirmação de que nenhuma instalação
foi entretanto preparada. O package e configs do jogo não foram alterados nesta preparação.
