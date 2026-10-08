# Fase 10 — gate final e teste real da beta protegida

Build gate Bitdefender: **NO_ALERT**, confirmação humana explícita para
09/10/2026 00:42:10–00:47:30 Europe/Lisbon. Registo independente em
`build/obfuscation/real-beta/bitdefender-build-gate.json`.

Candidato preservado sem rebuild: `build/beta/0.1.2-beta.1/Driftkings.wotmod`,
6 773 910 bytes, SHA-256
`3fcefee6b47c1abba2897ed2bacfcddec3640f9d2241489ac1b250c1030893d3`.
Manifest schema 1 / beta / 2.4.0.2 e sidecar verificados novamente antes de publicação.

Commit/registo da source aprovada, tag anotada `v0.1.2-beta.1` e prerelease
são autorizados nesta etapa. Apenas WOTMOD, sidecar SHA-256 e release.json serão
assets públicos. Relatórios, logs, baseline e cache ficam em build/ ignorado.

O SWF modificado já foi utilizado no package validado e será registado no commit
para reproduzir os recursos. A remoção preexistente de
`res/icones_foco_variantes.zip`, sem ligação ao package, permanece fora deste commit.
Nenhum byte funcional da source foi alterado após gerar o candidato.

A instalação inicial observada é 0.1.1-beta.6: POC ativa e package original
renomeado para `.wotmod_`. Antes do teste do updater deve existir uma única cópia
ativa com nome `Driftkings.wotmod`. Não instalar manualmente a nova beta.

**FASE 10: BLOCKED — teste real pendente.** Publicação/upload/verificação remota
e resultados reais serão registados no relatório próprio em
`build/obfuscation/real-beta/`. Não confundir gates offline com install/restart,
novo boot, Marks em batalha e confirmação humana Bitdefender no cliente.

OPEN SECURITY HARDENING permanece: primeira extração WindowsFiles antes da
validação nativa completa dos ancestrais da cache. Rever antes de stable;
não resolvido nesta beta. Fase 11 não iniciada.
