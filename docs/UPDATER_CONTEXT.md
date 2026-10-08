# Updater — Fase 6: integração com os contextos

UpdaterService, já gerido pelo Core, passa a possuir o Installer. Continua a receber
onContextEntered/onContextLeft pelo Contexts existente. Não há outro serviço,
entry point, subscrição de appLoader, implementação de restart ou alteração da UI.

## Política de segurança

`context.py` contém InstallContext, uma consulta read-only. Exige simultaneamente:

* o contexto entregue pelo Core e appLoader.getSpaceID() iguais a LOBBY;
* player conhecido, BattleCapabilities.is_in_battle() exatamente False e
  current_mode() igual a hangar;
* BattleReplay.isPlaying()/isLoading() exatamente False, mesmo sem arena;
* IHangarSpace.inited/spaceInited/isModelLoaded exatamente True.

Login, waiting, battle loading, battle, replay, contexto divergente, player ausente,
hangar incompleto, retorno desconhecido ou exceção bloqueiam o agendamento.
BattleCapabilities, os seus cálculos e hooks permanecem intactos.

As APIs foram confirmadas na referência EU 2.4.0.2: skeletons/gui/app_loader.py,
BattleReplay.py, skeletons/gui/shared/utils/__init__.py e
gui/shared/utils/HangarSpace.py. A extração inclui o contrato e a implementação
das propriedades do hangar. .version_name continua diferente de sources/version.xml;
não foi usado como versão do diretório de mods.

A disponibilidade observável é atualizada pelos contextos e por eventos existentes
do hangar (criação/destruição, mudança de veículo e fim de refresh). Essas subscrições
são removidas em stop. Não existe polling em repouso. A política é consultada novamente
no início da ação e imediatamente antes do lançamento; metadata de UI não autoriza instalação.

## Ação explícita e confirmação

`schedule_install()` é a ação backend para a Fase 7. Nunca é chamada automaticamente
por entrada no lobby, download, recuperação de staging ou abertura de Settings.
Reutiliza Installer.schedule ou, havendo ticket próprio, Installer.resume.
A validação de versão/canal/compatibilidade/hash do Installer mantém-se obrigatória.

READY significa validado. INSTALLING significa preparação do helper, sem alterar o
WOTMOD ativo. Só result.json com schema 1, helperPid correspondente ao processo lançado
e status prepared leva a RESTART_REQUIRED e installScheduled=True. installedVersion
continua VERSION; agendamento não é instalação concluída.

State acrescenta canInstall, installBlocked e installScheduled, apenas runtime.
Presenter e observadores existentes continuam a transportar o snapshot; não foram
adicionados botões, traduções ou ações de restart nesta fase.

Usa CallbackService existente: 250 ms durante preparação, deadline de 15 segundos;
após confirmação, verifica a saúde do helper uma vez por segundo enquanto essa operação
estiver ativa. Outra verificação/download/agendamento é bloqueada. Não há callbacks em
repouso, polling por frame ou callbacks de geração anterior a afetar uma operação nova.

Timeout, contexto inseguro antes da confirmação, resultado inválido/antigo ou helper
terminado produzem ERROR; não fingem sucesso. Um cancel.install fixo na pasta própria
solicita cancelamento cooperativo. O helper verifica-o enquanto espera e antes de aplicar.
Retoma explícita remove apenas esse marker validado, depois de o helper anterior terminar.

## Encerramento, retoma e preservação

stop remove callbacks/subscrições e cancela preparação ainda não confirmada. Um
agendamento confirmado sobrevive ao encerramento normal do Core: o helper deve
continuar a esperar pelo fim do processo WoT. Sair do lobby ou entrar posteriormente
em batalha não provoca instalação: a substituição só ocorre com o processo encerrado,
e outro processo WorldOfTanks ativo volta a bloqueá-la.

Se o mesmo serviço for iniciado novamente, acompanha o helper já confirmado sem lançar
outro processo. Preferências de canal futuras não redirecionam a transação com consentimento.

No arranque e na alteração de canal sem operação ativa, recupera READY válido através
do Installer, sem instalar nem lançar o helper. Staging inválido ou falha de disco são
registados e não impedem boot. Não altera configs, migrações, perfis ou persistência de valores.

## Limites desta fase

Não foi executado o helper na instalação real do jogo. Os testes de contexto usam
fixtures das APIs; os testes Windows executam o helper numa instalação fictícia sob build/.
A coordenação de restart com WGC continua sem prova: o serviço não invoca restart.
A Fase 7 deve apresentar ações com esse limite, reutilizando o fluxo existente quando
a coordenação estiver demonstrada. Não há deployment, PJOrion ou publicação.

## Validação — 2026-10-08

* Suite Python completa: 649/649; 21 testes específicos de política/lifecycle e
  27 testes do installer, incluindo cancelamento cooperativo nativo.
* Python 2.7.18: seis smoke, também sobre os .pyc compilados de context/installer.
* Settings Gameface, Hangar/TechTree, Gameface dependencies e UI bridge: passaram.
* Contratos Python/Flash: nove componentes. Localização: 12 catálogos, zero erros.
* Build debug: 33 componentes, 391 entradas e 244 módulos Python 2.7.
* Package: CRC/identidade/bytecode válidos; zero problemas na inspeção.
* git diff --check: sem erros de whitespace.

Artefacto local: build/unified/Driftkings.wotmod, versão 0.1.0, WoT EU 2.4.0.2,
6 652 426 bytes. SHA-256:
`7b3aa43f1a5cdaffa5c5b1a2b062bead559817d389b1a5a3aa04a3d866d6758f`.
Este é um build debug sem PJOrion, não um manifest de release.
