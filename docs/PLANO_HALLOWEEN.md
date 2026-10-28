# Plano — modo Halloween (painel de jogadores, TAB e carregamento)

## Âmbito

- Modo Halloween: `ARENA_BONUS_TYPE` `HALLOWEEN=101`, `HALLOWEEN_MEDIUM=102`, `HALLOWEEN_HARD=103`, injetados pela extensão `halloween` (`halloween_common/halloween_constants.py`, `ConstInjector`).
- Estado atual do mod (branch `feature/halloween-mode-adapters`):
  - `core/battle_capabilities.py` devolve o modo `halloween` (antes era `special`). O Halloween continua a ser um modo de evento para `is_special()` e `is_event_mode()`.
  - `core/mode_adapters.py` declara o que cada modo suporta. Só existem `random` (comportamento anterior) e `halloween`. Os modos sem adaptador ficam com as vistas nativas intactas.
  - No Halloween, o roster do mod tem só aliados, ordenados no mod como o `HWSortKey` nativo (equipa, vivos primeiro, classe, nome do veículo, nome do jogador). As entidades do modo (bots, bosses, `accountDBID` 0) ficam como linhas sem estatísticas. Os perfis short/medium/large do painel clássico não são usados.
  - O painel e o carregamento do Halloween **não são desenhados** (adaptador com `panel=False`, `loading=False`). Ver "Painel" abaixo.
  - O TAB do Halloween recebe uma **tabela separada** com os aliados e as estatísticas numéricas (opção B abaixo, adaptador com `tab='halloween'` e `event_numbers=True`). Os outros modos de evento continuam só com cores.

## Versão da referência

- Cliente dos logs: NA `2.4.1.1 #987`.
- Referência local `WoT_Tools/wot-src-EU/sources/version.xml`: EU `v.2.4.1.1 #989` (branch `v2.4.1`). As builds diferem (`#987` vs `#989`); nada do que segue foi confirmado no cliente NA.
- O ficheiro `docs/PLANO_ATUALIZACAO_2_4_1_1.md` indicado para confirmar a versão não existe neste repositório nem em `WoT_Tools`. A versão foi lida do `version.xml` da referência e do histórico em `WoT_Tools/Notas_Atualizacoes/wot-src-EU.md`.
- A pasta `sources-as3` da referência não inclui o AS3 do `HWPlayersPanel` (nem de outro componente Flash do Halloween).

## Estrutura nativa encontrada (EU #989)

| Ecrã | Classe | Tecnologia | Notas |
| --- | --- | --- | --- |
| Painel | `halloween.gui.scaleform.daapi.view.battle.players_panel.HWPlayersPanel` (alias `hwPlayersPanel`) | Scaleform | Herda de `HWPlayersPanelMeta`, que herda do `PlayersPanel` clássico. Por isso os hooks do mod em `PlayersPanel` (`as_setPanelModeS`, `setInitialMode`, `tryToSetPanelModeByMouse`, `updateVehicleHealth`) também disparam no Halloween. Só aliados com `accountDBID > 0`; usa `as_setPlayerPanelInfoS`, `as_setPlayerPanelHpS`, `as_setPlayerDeadS`, `as_setPostmortemS`. |
| Troca de estatísticas | `halloween...stats_exchange.HWStatisticsDataController` | Scaleform | Ordena com `HWSortKey` e esvazia o lado inimigo (`HWEnemySortedIDsComposer.addSortIDs` não faz nada). |
| TAB | `halloween.gui.impl.battle.full_stats.TabScreen` em `FullEventStatsWindow` | Gameface | Layout `R.views.halloween.mono.battle.tab_screen`, `FullStatsViewModel` (título, tarefa, dificuldade, anomalias). As linhas dos jogadores estão no filho `TeamStats` (`R.aliases.halloween.shared.TeamStats`, `EventStatsViewModel.team`). Janela `WINDOW_FULLSCREEN`, modal, camada `OVERLAY`. Aberta por `page.py` com `__showBattlePageGFComponent`. |
| Carregamento | `halloween...halloween_battle_loading.HalloweenBattleLoadingWindow` | Gameface | Só progresso (`EventLoadingViewModel.currentProgress`); não tem lista de jogadores. |

## Painel

O Flash do mod (`ratingscreens.as` / `viewbindings.as`) liga-se a qualquer objeto com `listLeft` e `listRight`. Como o `HWPlayersPanel` herda do painel clássico, era encontrado e o mod desenhava por cima dos nomes nativos. Os modos `medium2` e `large` dos logs vinham dos hooks do painel clássico.

Sem o AS3 do `HWPlayersPanel` não há forma segura de alinhar as linhas. Por isso o adaptador `halloween` tem `panel=False`: o payload Flash vai com `enabled=False`, o Flash do mod restaura o estado nativo e os hooks de modo só passam a chamada ao original. O roster (só aliados, ordenado, sem estatísticas para `accountDBID` 0) já é calculado e testado; ativar o painel exige primeiro validar o alinhamento em jogo.

## TAB

### Implementação atual (opção B)

- `GamefaceLoading` anexa o filho `DriftkingsRatingPlayers` ao `TabView` clássico só quando o adaptador tem `tab='classic'`, e ao `TabScreen` do Halloween só quando tem `tab='halloween'`.
- O mod nunca importa a extensão. O hook do `TabScreen` só é instalado depois de o `page.py` do Halloween ter carregado `halloween.gui.impl.battle.full_stats` (`GamefaceLoading.watch`, chamado em cada tick). Se o TAB for aberto antes desse primeiro tick, essa janela fica sem tabela até ser recriada.
- O payload `hwTab` tem uma linha por aliado (`summary`): nome, clã, veículo, vivo, próprio, rating configurado, % de vitórias e batalhas, com as cores da escala. Respeita o interruptor do TAB nas definições. Não lê o modelo nativo (o `TabScreen` não tem `playerList`).
- `panel_gameface/halloween_tab.js` cria um único `div.dk-hw-tab` em `document.body` (posição absoluta, `left: 24rem`, `top: 160rem`, sem eventos de rato). Só usa `textContent` e nunca altera os elementos nativos. As entidades sem estatísticas mostram `—`, e os mortos ficam a 50% de opacidade.
- Não há settings novas nem texto traduzível. O único cabeçalho é o nome do rating (por exemplo `WN8`).
- Testes: `tests/core/test_halloween_tab.py` (hooks e payload) e `tests/settings_panel/test_halloween_tab.js` (formatação, cores, texto seguro e nó próprio).

### Opções avaliadas

### Opção A — camada por cima do `TabScreen`

Anexar um filho Gameface ao `TabScreen` (como hoje no `TabView`), com JS que posiciona os campos do mod sobre as linhas do `TeamStats`.

- Ganho: aparece e desaparece com o TAB nativo, sem gerir a visibilidade nem a camada.
- Riscos:
  - O layout `halloween.mono.battle.tab_screen` e o DOM do `TeamStats` não estão na referência local. Os seletores e as posições teriam de ser descobertos em jogo e podem mudar a cada evento.
  - O `TeamStats` é um `ViewImpl` filho com o seu próprio modelo (`team`, `EventStatsTeamMemberModel`), não o `playerList` com `getAllies()/getEnemies()` que `GamefaceLoading.update` usa. A ordem teria de vir do modelo `team` ou do roster do mod.
  - `supports_gameface_overlay` exige um módulo `gui.impl.battle.*`, e o `TabScreen` está em `halloween.gui.impl.battle.full_stats`. Seria preciso alargar essa verificação só para esta classe.
  - Hook numa classe de extensão: se o evento acabar ou o módulo mudar de nome, o import falha (tem de ficar opcional, como o `TabView`).
  - A janela é modal e de ecrã inteiro: um erro no JS do filho afeta o TAB inteiro do jogador.

### Opção B — painel separado

Uma vista própria do mod (Flash ou Gameface) mostrada enquanto o TAB do Halloween está aberto, ao lado ou por baixo do conteúdo nativo, sem escrever no `TabScreen`.

- Ganho: não depende do DOM nativo; o roster do mod (só aliados, ordem própria) pode ser usado tal como está.
- Riscos:
  - A `FullEventStatsWindow` está na camada `OVERLAY`, é modal e de ecrã inteiro. Uma vista Flash fica por baixo. Uma janela Gameface própria tem de ficar acima dela sem roubar o foco nem o input.
  - Visibilidade: é preciso seguir a abertura e o fecho da janela (hook em `FullEventStatsWindow` ou nos eventos de `page.py`) e esconder o painel quando o TAB fecha.
  - Duplica informação do `TeamStats`, e a posição livre pode tapar elementos nativos em resoluções diferentes.

### Decisão

Foi implementada a opção B, alojada como filho do `TabScreen`. Assim abre e fecha com o TAB, na mesma camada, sem foco próprio e sem tocar no DOM nativo. A opção A só vale a pena depois de inspecionar o `TabScreen` em jogo (estrutura e classes CSS) no cliente NA.

## Por validar em jogo

- O painel nativo do Halloween fica sem texto do mod por cima e sem mudanças de modo (`medium2`/`large`).
- O log mostra `Team panels: mode=halloween supported=tab`, `Gameface roster watching halloween.gui.impl.battle.full_stats.TabScreen` e, ao abrir o TAB, `Gameface roster attached: tab (halloween)`.
- No TAB do Halloween, a tabela aparece à esquerda sem tapar conteúdo nativo (posição, tamanho da letra, contraste), com números e cores para os 5 jogadores e `—` para os bots. Fecha com o TAB.
- O carregamento do Halloween fica igual ao nativo.
- O random fica igual ao anterior (painel, carregamento e TAB).
- Os outros modos (comp7, frontline, treino, eventos) ficam com as vistas nativas, sem o roster do mod.
