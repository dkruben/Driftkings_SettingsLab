# Updater — Fase 5: installer, staging e rollback

Esta fase implementa apenas o mecanismo. O serviço e a UI da Fase 4 continuam
a terminar em READY. A criação do Installer, a política de contexto real e os
callbacks/botões ficam para as Fases 6 e 7. Não há instalação automática nem novo serviço.

Este parágrafo regista o âmbito original da Fase 5. A integração posterior do serviço
e dos contextos está descrita em [UPDATER_CONTEXT.md](UPDATER_CONTEXT.md).

## Ficheiros

* `source/scripts/client/Driftkings/core/updater/installer.py`: revalidação,
  descoberta de READY anteriores, preparação e retoma explícitas.
* `source/updater/Installer.cs`: helper Windows próprio, offline, sem restart.
* `build_tools/build_updater_helper.py`: compilação C# e hashes locais em build/updater.
* `build_tools/build_lab.py`, `build_tools/build_unified.py`: compilação e packaging;
  rejeitam helper desatualizado face ao source ou com hash divergente.
* `build_tools/tests/test_updater_installer.py`, `test_updater_smoke.py`: testes.

## Agendamento e confirmação

Installer é um módulo interno sem lifecycle/hooks. schedule/resume exigem uma
função de segurança cujo resultado seja exatamente True, antes da preparação e
imediatamente antes do lançamento. Na Fase 6 essa função consultará os contextos
e BattleCapabilities existentes. False, None e informação incompleta bloqueiam.

O READY deve estar diretamente em
`mods/configs/Driftkings/cache/update/download-*/Driftkings.wotmod.ready`.
Manifest, canal, SemVer, compatibilidade, tamanho, SHA-256 e conteúdo do package
são novamente verificados. A versão deve ser superior à instalada. O package
instalado deve ter a identidade e versão esperadas. Configs não são migradas.

O helper é exportado de um recurso do package local, com hash validado. Não é
descarregado nem definido pelo manifest remoto. É lançado com argumentos em lista,
shell=False e CREATE_NO_WINDOW; recebe apenas staging e PID do processo chamador.
O ticket local contém schema, gameVersion, version, size, sha256, installedVersion,
installedSize e installedSha256. Rejeita campos desconhecidos, comandos e destinos.

O helper deduz a instalação pela imagem do pai `win64/WorldOfTanks.exe` ou
`win32/WorldOfTanks.exe`. Atua exclusivamente em `mods/<gameVersion>/Driftkings.wotmod`.
Rejeita UNC e todos os reparse points nos ficheiros/ancestrais, incluindo junctions
que o Python 2.7 nem sempre consegue detetar.

Abre o handle do pai antes de confirmar prepared e mantém lock exclusivo de cache
e handle de leitura do READY, impedindo escrita/remoção desse staging durante a espera.
Só instala após o handle do pai sinalizar encerramento. Outro WorldOfTanks ativo
bloqueia a instalação. Outra operação não obtém o lock nem altera o resultado.
install.lock permanece na cache; o lock do sistema é libertado quando o helper termina.

schedule=True significa lançamento, não confirmação/instalação. result.json contém
schema, status, error e helperPid. A integração futura deve correlacionar helperPid
com o processo lançado e esperar prepared antes de confirmar agendamento. Falta de
resultado nunca significa sucesso. Se o pai sair antes da abertura do handle, falha
sem modificar o package.

## Atomicidade, rollback e recuperação

Depois da espera, repete paths e hash do instalado. Mudança externa desde a preparação
bloqueia a substituição. Copia o READY para `Driftkings.wotmod.new` no diretório de destino,
faz flush e confirma o hash. File.Replace(new, target, old) substitui atomicamente o
ficheiro completo e preserva o anterior em `.old`. Confirma o hash final e regista
installed antes de remover o backup. Falha de cleanup conserva o backup.

Falha após replace restaura o backup validado por File.Replace. Se outro cliente já
arrancou ou o Windows impedir a restauração, mantém backup/ticket para recuperação.
Nunca apaga o destino nem copia bytes para ele. A verificação de processos reduz a
corrida com WGC, mas não é um lock do launcher: restart automático não está comprovado
como coordenado com o helper. Esta fase não altera nem invoca o restart flow.

resume reutiliza o ticket original e confirma o helper contra o recurso local.
Na mesma transação, `.old` com hash/identidade válidos é restaurado se o destino divergir.
Se o destino já corresponder ao hash novo, conclui apenas cleanup. Backup desconhecido
é preservado e causa erro. `.new` pendente não é sobrescrito e requer recuperação futura.

recover_ready é descoberta read-only, limitada a 100 entradas da cache, escolhe a
maior versão válida e ignora parcial/corrompido ou resultado installed. Não elimina
configs, perfis, overrides nem ficheiros de outras operações.

## Build e limites

Runtime: Windows com .NET Framework 4.5+. Build: csc.exe do Framework v4 local.
Nenhuma dependência é instalada automaticamente. build/updater/build-report.json
relaciona hashes do source/helper. Executável e helper.json entram como recursos
do WOTMOD; source e relatório ficam fora.

Os ensaios nativos compilam um processo fictício WorldOfTanks.exe sob build/ e
executam o helper real numa instalação fictícia. Cobrem espera, sucesso, hash,
PID indevido, concorrência, outro processo ativo, alteração externa, junction,
destino bloqueado, campos arbitrários, recovery de backup e falha injetada após
File.Replace com rollback real. O contrato local também corre em Python 2.7.

Isso não prova jobs do launcher, disponibilidade do .NET noutros PCs ou execução
do helper dentro do WoT; esses ensaios dependem da integração seguinte. Não houve
deployment, PJOrion nem publicação.

## Validação — 2026-10-08

* Suite Python: 625/625, incluindo 25 testes do installer (12 de contratos Python,
  13 com executáveis/transações Windows) e cinco smoke portáveis.
* Python 2.7.18: cinco smoke verdes, também com installer importado dos .pyc do build.
* Settings Gameface, Hangar/TechTree, Gameface dependencies e UI bridge: passaram.
* Contratos Python/Flash: nove componentes; localização: 12 catálogos sem erros.
* Build debug local: 33 componentes, 390 entradas, 243 módulos Python 2.7.
* Inspeção do package: CRC, identidade, recursos e bytecode válidos; zero problemas.
* git diff --check: sem erros de whitespace.

Artefacto: `build/unified/Driftkings.wotmod`, versão 0.1.0, WoT EU 2.4.0.2,
6 640 901 bytes. SHA-256:
`ba02096f27f1a3fd1db2ffc98367ede39d4aaf835b6766d4fab83b8982f01068`.
Este hash identifica o build debug local, sem PJOrion; não é um manifest de release.
