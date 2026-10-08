# Updater — Fase 7: UI, restart existente e resultado pós-restart

## Âmbito e ficheiros

Alterações desta fase:

* `core/updater/__init__.py`: ações explícitas, prova de prepared, cancelamento,
  razão de restart, notificações e consumo de resultados no arranque.
* `core/updater/state.py`: canRestart, cancellingInstall, restartDeferred e
  lastInstallResult; campos apenas runtime.
* `core/updater/results.py`: novo módulo interno de leitura/validação de receipts;
  não é serviço, helper, transporte ou mecanismo de instalação/restart.
* `settings/panel/presenter.py`: delegação das novas ações ao UpdaterService e
  razão updater no diálogo de restart já existente.
* `views/hangar/settings_window.py`: passa essa razão ao método restart existente,
  que revalida/obtém a autorização do serviço antes de executar o fluxo habitual.
* `settings/panel/locales/en.py`, `pt.py`: textos completos com o fallback existente.
* `res/gui/gameface/mods/Driftkings/DKModSettings/js/app.js`: secção Updates e diálogo.
* Testes: `test_updater_results.py`, `test_updater_context.py`,
  `test_updater_installer.py`, `test_updater_smoke.py`, `test_dk_settings_view.py`
  e `dk_settings_gameface_test.js`.

Os paths Python acima são relativos a `source/scripts/client/Driftkings/`;
os testes ficam em `build_tools/tests/`.

Installer Python/C#, política de contexto, transporte/download, manifest/versioning/
checker, Core lifecycle, BattleCapabilities, CompatibilityManager, SettingsService,
Marks, ColorPicker, perfis e build concept não foram alterados nesta fase.

## Ações e estados

| Estado | UI e ação |
| --- | --- |
| IDLE | Por verificar, ou atualizado após check concluído |
| CHECKING | A procurar; ações concorrentes bloqueadas |
| AVAILABLE | Atualizar agora inicia download da release compatível |
| DOWNLOADING | Percentagem real em bytes; cancelar download |
| VERIFYING | Verificação textual, sem percentagem inventada |
| READY | Atualizar agora prepara a instalação se canInstall e compatible |
| INSTALLING | A preparar instalação; cancelar; sem botão de restart |
| RESTART_REQUIRED | Prepared confirmado; restart, mais tarde e cancelamento |
| ERROR | Mensagem não fatal; eventual nova preparação apenas com READY válido |

AVAILABLE e READY partilham a legenda Atualizar agora, mas a primeira ação apenas
descarrega; a segunda chama schedule_install. Não há agendamento automático ao
terminar download, entrar no Hangar, recuperar staging ou abrir Settings.

installBlocked mostra texto contextual para batalha, replay, Hangar incompleto ou
estado desconhecido, sem modal de erro. Enquanto há operação ativa, check/download/
schedule concorrentes e mudança de canal durante preparação são bloqueados na UI.
Depois de prepared, o canal pode referir-se às próximas verificações; não muda o ticket.
O changelog continua a usar textContent. Os botões nunca chamam Installer.

## Prova de prepared e geração

Antes do lançamento, regista a assinatura do resultado anterior, se existir.
Depois do lançamento, captura o ticket validado. Só arma quando o resultado tem
os quatro campos esperados, schema 1 inteiro, helperPid inteiro igual ao processo
lançado, status prepared, ticket igual ao capturado e resposta posterior ao lançamento.
A assinatura inclui conteúdo, timestamps, tamanho e identidade do ficheiro local;
protege também retoma com ticket igual e PID reutilizado. Callback de geração antiga
não afeta a operação atual. Contexto inseguro durante preparação cancela-a.

Uma resposta antiga ou incompleta não produz installScheduled. Durante preparação
mantém deadline de 15 segundos. Uma indisponibilidade transitória de leitura do
result.json durante substituição no Windows é repetida por callbacks existentes,
num intervalo limitado; nunca é interpretada como confirmação.

## Restart e Mais tarde

O botão Reiniciar agora abre o diálogo já existente, com texto específico do updater.
Presenter exige prepared atual e ausência de edits por guardar. Ao confirmar,
SettingsController.restart(reason='updater') usa o seu fluxo habitual:
close, savePreferences, WGC.notifyRestart e BigWorld.restartGame.
O updater não chama BigWorld.restartGame e não há restart.py ou outro fluxo.

O controller mantém a verificação de lobby/arena e pede claim_restart ao serviço,
que reconsulta a política existente, ticket, resultado atual, PID, vida do helper e
cancelamento. Uma razão updater só pode consumir uma claim uma vez. Cancelamento,
helper morto, contexto inseguro, ticket alterado ou resultado antigo impedem restart.

Mais tarde fecha apenas o diálogo de updater, mantém a janela e o helper, não remove
staging e preserva installScheduled. A secção continua a mostrar prepared, sem reabrir
modal automaticamente. Fechar/reabrir Settings conserva o serviço e reconstrói a UI
pelo snapshot; listeners da janela são removidos no disposal.

## Cancelamento cooperativo

cancel_install chama apenas o cancel do Installer existente, que cria cancel.install
na operação atual. Não mata o processo. Enquanto aguarda, mostra a confirmação pendente
e desativa restart. Só resultado cancelled do PID atual, resposta nova e exit code 3
confirmam cancelamento. Revalida o READY antes de regressar a READY; staging/canal
inelegível volta a AVAILABLE, sem oferecer instalação desse artefacto. O cancelamento
confirmado continua a ser apresentado como cancelado, sem o confundir com falha.
Marca lastInstallResult.cancelled sem alterar installedVersion.
Timeout ou saída sem confirmação não são apresentados como cancelamento concluído.

## Resultado no arranque seguinte

Results inspeciona até 100 entradas da cache própria, apenas download-* com result.json
e ticket/manifest conhecidos e válidos. Não interpreta comandos/destinos remotos.
Rejeita JSON duplicado, schema/bools inválidos, campos desconhecidos, paths externos
e reparse points, incluindo junctions Windows verificadas também em Python 2.7.

Os nomes nativos installed, rolledBack, cancelled e error são normalizados para
installed, rolled_back, cancelled e failed no snapshot. Prepared/installing de uma
sessão anterior são incompletos, não sucesso.

installed exige package presente, identidade DriftKings, versão do ticket, tamanho,
SHA-256 e VERSION carregada no novo processo iguais. Rollback/cancelamento exigem
o package anterior validado. Backup desconhecido ou .new pendente impedem sucesso.
Nada é inferido só por presença de backup, helper ausente ou mudança de versão.

Notificações discretas usam SystemMessages apenas no Hangar seguro: available uma vez
por sessão/versão; resultado uma vez por operação. lastInstallResult reconstrói o texto
na Settings. notified.json, na cache da própria operação, marca o resultado consumido
e é substituído atomicamente para novo resultado de uma retoma. Esse é o cleanup
controlado desta fase: ticket, result, READY e backups ficam para diagnóstico/recuperação.
Não se apagam packages, executáveis, configurações ou perfis para limpar uma notificação.
Erros técnicos são registados em Driftkings.Updater e não impedem o arranque.

## Limites e confirmação de âmbito

WGC continua sem certificação no cliente. A UI e o diálogo indicam que um novo WoT
demasiado cedo bloqueia a instalação. Não se contorna esse bloqueio e não se promete
que restart automático aplique a atualização. O helper mantém a espera pelo fim do
processo e a recusa enquanto existir outro WorldOfTanks.

Não houve execução contra a instalação real, deployment, PJOrion, GitHub Release
ou publicação. Os testes nativos usam pastas/processos fictícios em build/. O novo
teste do serviço usa o helper real; só substitui o PID chamador, pois o runner é Python,
e confirma prepared, restart_ready, cancelamento e preservação do package antigo.

## Checklist para teste real posterior

1. Abrir WoT sem update; confirmar arranque e Settings normais.
2. Preparar manifest/assets de teste controlados num endpoint permitido, com versão
   superior, gameVersion correta e hash real. Não publicar nesta fase nem desativar TLS.
3. Detetar update; confirmar notificação única e changelog literal.
4. Fazer download real; verificar percentagem em bytes e VERIFYING.
5. Confirmar READY sem helper preparado ou restart disponível.
6. Regressar ao Hangar; aguardar o carregamento completo.
7. Clicar Atualizar agora; observar INSTALLING, sem restart prematuro.
8. Confirmar result.json schema 1, PID correto, status prepared e ticket atual.
9. Confirmar RESTART_REQUIRED e as três ações.
10. Escolher Mais tarde; continuar a jogar e confirmar helper/state preservados.
11. Fechar/reabrir Settings; confirmar snapshot e ausência de modal repetido.
12. Cancelar; aguardar cancelled/exit 3 e verificar package antigo intacto.
13. Repetir download/preparação ou retomar READY; verificar resposta nova do helper.
14. Confirmar bloqueios durante battle loading, batalha, replay e Hangar incompleto.
15. Reiniciar agora pelo diálogo existente; observar WGC sem assumir sucesso.
16. Se WGC arrancar cedo, confirmar instalação bloqueada e staging recuperável.
17. No novo arranque, verificar result.json e hash/identidade/versão no disco.
18. Confirmar VERSION efetivamente carregada e mensagem correta do resultado.
19. Reabrir Settings: resultado reconstruído; não repetir notificação consumida.
20. Rever game.log e result.json; testar failure/rollback/cancel sem apagar diagnóstico.

## Validação final — 2026-10-08

- Suite Python completa: 676/676, incluindo instalação e rollback nativos.
- Settings Gameface, Hangar/TechTree, dependências Gameface e UI bridge: passaram.
- Smoke Python 2.7 sobre código compilado: 7/7.
- Contratos Python/Flash: 9 testes passaram; 12 catálogos i18n sem erros.
- Package: CRC e recursos válidos; 245 módulos Python 2.7 e respetivos fontes
  validados, incluindo defaults e imports passivos.
- git diff --check: passou.

Build debug local: build/unified/Driftkings.wotmod, versão 0.1.0, cliente EU 2.4.0.2.
Contém 33 componentes, 392 entradas e 6 677 241 bytes.

SHA-256:
`142bc16742e9e8d3698bb5370b52edbc413ff55e09ecc2a89b5ccd92efe0a8a2`

O restart real via WGC requer a checklist acima; não foi certificado pelos testes
automatizados. Não houve deployment, ofuscação PJOrion ou publicação.
