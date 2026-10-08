# PlayerPanelPro — reconstrução v2

Implementação Python/ActionScript nova para PlayersPanel, battleLoading (incluindo dicas)
e statisticForm/TAB. Referências: `WoT_Tools/xvm-master/release/configs/default_wg`,
`release/doc/macros.txt`, `release/doc/extra-field.txt` e os fontes Python/AS3 do cliente EU
`v.2.4.0.2 #966` (`.version_name`: `2.4.0.5473`).

## Configuração

Nove JSON em `mods/configs/Driftkings/<perfil>/player_panel_pro/`:

- `general.json`: versão do esquema, ativação, estatísticas, rating e escala de cores;
- `playersPanel.json`: opções globais e `templates` dos campos partilhados;
- `panelNone.json`, `panelShort.json`, `panelMedium.json`, `panelMedium2.json`, `panelLarge.json`;
- `battleLoading.json`, partilhado pelo loading normal e pelo loading com dicas;
- `statisticForm.json` para TAB.

Os nomes e valores padrão vêm dos XC WG. O importador de desenvolvimento é
`build_tools/import_xvm_panels.py <pasta-xvm-master>`; o jogo só lê JSON, sem XC,
XFW ou serviços XVM. Referências usam `{"ref":"hp"}` e aceitam overrides ao lado de `ref`.
Os formatos e a geometria têm uma única representação, sem os antigos `playerNameFull`,
`playerNameCut`, `layout.leftNick` ou `textFields` paralelos.

O esquema é `schemaVersion: 2`. Na primeira leitura de configurações v1, o módulo guarda
cada JSON anterior como `.json.v1` e cria os defaults novos, preservando rating,
escala de cores e opções de pedidos de estatísticas. Os ficheiros inválidos não são
sobrescritos. A escrita dos nove documentos usa um journal com recuperação.

O painel visual expõe as opções escalares e ambos os lados, incluindo seleção visual
de cores constantes nos templates. `standardFields`, listas de campos extra e sombras
nulas são editados como JSON; propriedades dos templates são apresentadas individualmente.
Não existem controlos duplicados para o mesmo formato.

## Painéis

`standardFields` seleciona e ordena `frags`, `badge`, `nick`, `vehicle`, `prestige`.
Por defeito short mostra abates; medium mostra abates, insígnia e nome; medium2
mostra abates e veículo; large segue a definição WG. Os formatos de nomes também
podem ser usados em short ao acrescentar `nick` à lista.

São aplicados os formatos, sombras, larguras, limites mínimo/máximo do nome,
offsets, transparências, pelotão, nível do veículo e indicador de deteção.
`expandAreaWidth` define a faixa lateral de expansão com o rato. `fixedPosition`
conserva a ordem inicialmente recebida para cada equipa; novos IDs são acrescentados.
A ordem nativa de loading/TAB não é alterada. `startMode` e `altMode` não gravam
preferências do cliente. `none` suporta campos em disposição vertical/horizontal.

Campos extra suportam texto/HTML/macros, imagens `src`, fundos, bordas, dimensões,
alinhamentos, rotação/escala, formato de texto e sombras. `bindToIcon` ancora ao ícone.
A ordem da lista determina as camadas. `hotKeyCode`, `onHold` e `visibleOnHotKey`
controlam cada campo. O preset Driftkings usa o HP permanente original: texturas
`hp_alive_l.png`/`hp_alive_r.png`, fundo `hp_bg.png` e valor atual/máximo em branco.
Os templates são desenhados pela ordem fundo, barra, texto. As posições antigas foram
convertidas para as âncoras espelhadas do renderer atual. A deteção usa as quatro
imagens originais de 22 px (`neverSeen`, `spotted`, `lost`, `dead`).
No painel visual, em Geral, **Visibilidade do HP** permite escolher sempre visível,
enquanto a tecla estiver premida ou nunca visível. **Tecla para mostrar o HP** permite
capturar outra tecla ou combinação; por defeito aceita ALT esquerdo ou direito.
Em `general.json`, estas opções são `hpVisibility` (`always`, `hold`, `never`) e
`hpKey` (por defeito `[[56, 184]]`). Grupos exigem uma tecla de cada grupo; os códigos
dentro do mesmo grupo são alternativas. O seletor controla fundo, barra e texto
em conjunto e substitui condições de tecla antigas nesses templates.
`hpEnabled` é mantido para compatibilidade; o painel visual sincroniza-o ao mudar
o modo. `spottedEnabled` continua independente da visibilidade do HP.

O preset define `startMode: "medium2"`: o cliente mantém o painel grande durante
a contagem e chama `setInitialMode()` ao entrar em batalha. A partir desse momento,
as mudanças manuais continuam disponíveis. As barras nativas são ocultadas através
de `removeHealthPoints: true` para não duplicar o HP personalizado.

O HP e a deteção ficam no modelo por ID de veículo. Mudar de painel não elimina os
dados; sair da visão conserva o último HP conhecido; morte coloca HP a zero; um
novo veículo/reaparecimento não herda a morte do veículo anterior.

## Loading e TAB

Formatos Nick/Vehicle independentes; TAB também permite Frags. Usam os nomes XC
`nameFieldOffsetXLeft/Right`, `nameFieldWidth...`, `vehicleField...`, `fragsField...`
e opções de ícones. Os offsets do lado direito seguem o sinal do XVM, não o sinal
absoluto da configuração anterior. Campos extra usam o mesmo motor do painel.
O relógio de loading aceita `H`, `i`, `s` e texto literal; não é um interpretador
completo de todas as diretivas PHP de data.

As coleções nativas são associadas à ordem recebida pelo controlador do cliente,
com identificação por nome exato quando disponível. O Flash guarda os valores
que altera e restaura-os ao desligar, respeitando alterações posteriores do cliente.

## Macros

O parser novo suporta condicionais aninhadas, comparações, formato `%`, sufixos `~`,
valores alternativos `|`, `{{.caminho.de.config}}` e `{{l10n:ID}}`. Valores de nomes
são escapados uma vez para HTML. Exemplos:

```
{{name%.{{anonym?10|12}}s~..}}
{{r%4d|----}}  {{winrate%2d~%|--%}}  {{tdv%3.01f|-.-}}
{{alive?{{ready?#FF|#80}}|#00}}
{{hp-ratio:70}}
```

Dados implementados: identidade/clã, veículo/nome curto/ID/nação/classe/nível,
premium/especial, aliado/jogador/anonimização, vivo/pronto, HP, deteção, abates,
pelotão, seleção, contactos/mute/chatban quando fornecidos pelo controlador,
badge/battle-pass quando presentes, modo e larguras dos painéis e prefixo `my-`.
WN8, eficiência, WGR, vitórias percentuais, batalhas, estatísticas de veículo e
escalas normalizadas disponíveis vêm do serviço comum do Core. As cores continuam
a usar a escala escolhida em `general.json`. `xvm-stat` significa dados disponíveis
no Core, não ligação ao serviço XVM.

Uma macro sem dado disponível produz vazio ou o fallback explícito; nunca inventa
estatísticas. XMQP, clan icons, flags e marcadores de utilizador XVM foram excluídos.
Valores exclusivos dos serviços XVM, WTR/xTE/XTDB sem dados no Core, tiers de matchmaking,
comentários privados, funções arbitrárias `py:` e traduções de IDs não mapeados não têm
paridade completa. O fallback permite configurações portáveis; uma macro reconhecida
pelo parser não implica que a sua fonte de dados exista.

Fontes `mono`/`xvm` foram adaptadas à fonte nativa; anonimização usa `*` e deteção usa
as imagens de círculos do pacote. Textos/cores específicos das secções globais XVM
`texts`, `colors` e extensões Python de terceiros não são importados automaticamente.

## Arquitetura

- `battle/players_panel.py`: proprietário das configurações e ciclo de vida;
- `core/panel_model.py`: roster, HP, deteção, ordem e contexto dos macros;
- `core/panel_macros.py`: parser de expressões sem execução arbitrária;
- `views/battle/player_ratings.py`: eventos nativos e ponte DAAPI;
- `views/battle/panel_gameface.py`: ponte para o TAB Gameface e loading White Tiger;
- `RatingScreens.as`: descoberta dos componentes nativos e ciclo de desenho;
- `PanelRenderer.as`, `TableRenderer.as`, `ExtraFields.as`, `NativeState.as`: apresentação.

A antiga PlayersPanelAPI, o shim e o adaptador de formatos v1 foram retirados do código
ativo. Cópias anteriores estão nos ZIP de segurança locais em `build/`.
O serviço comum de estatísticas do Core mantém-se partilhado pelos restantes módulos.

## Validação

Testes automatizados cobrem macros, identidade, ausência de estatísticas, HP/deteção,
respawn, ordem fixa, delegação dos métodos nativos, cancelamento de callbacks, seleção
de modo, JSON, backups, validação e rollback. O Flash é compilado contra os SWC locais.

A compilação não substitui a validação no cliente. Testar replay/batalha: os cinco
modos; passar o rato dentro/fora da área; ALT; TAB; loading normal/dicas; morte e
reaparecimento; desligar e voltar a ligar; escalas/cores; mudança de resolução.
Verificar `Roster v2 Flash ready` e `Roster v2: bindings=...` no game.log.
No TAB Gameface, verificar `Gameface roster attached: tab`; `table rows=0` no
diagnóstico Flash é normal nesse ecrã. O adaptador usa a coluna fixa do nome,
trechos de texto numa única linha flex e a fonte nativa para `$FieldFont`.
Os offsets dos ícones preservam a orientação original e são repostos ao desativar.
`node build_tools/tests/roster_gameface_test.js` verifica formatos aninhados,
cores, alpha, larguras/âncoras, offsets sem acumulação e reposição do estado nativo.
Também verifica a reutilização de linhas e alterações do DOM; `--poll-only`
repete os cenários sem `MutationObserver`, validando o mecanismo alternativo.

As interfaces nativas distintas de eventos precisam de validação em cada modo.
O TAB Gameface suporta formatos de nome/veículo/abates, opções de ícones e campos
extra de texto/imagem/fundo/borda, com posição, alinhamento, alpha, escala e rotação.
`ref`, macros e teclas dos campos extra são resolvidos pelo mesmo Python do Flash.
Imagens usam caminhos locais `img://gui/...` ou `coui://gui/...`. Sombras usam CSS;
filtros avançados do Scaleform não têm correspondência exata no Gameface.
O loading Gameface do White Tiger mantém o adaptador de formatos de texto; não é
um ecrã Flash nem reproduz todas as opções geométricas de um XC.
O pacote é preparado em `build/unified/Driftkings.wotmod`, sem instalação automática.

## Atualizações e diagnóstico

O contexto estatístico e os formatos são reutilizados por jogador. Mudanças de HP,
deteção, estatísticas, identidade, ordem e veículo invalidam o contexto necessário;
macros `my-*` podem legitimamente invalidar outros jogadores. Teclas de movimento
não invalidam formatos, salvo quando configuradas como teclas de um campo.
O protocolo Flash envia linhas alteradas e a ordem atual, preservando as restantes.
Propriedades nativas mantêm os valores aplicados entre ciclos e são repostas quando
deixam de ser usadas; offsets partem sempre da base nativa, evitando acumulação.
Há uma verificação leve de geometria a 10 Hz e descoberta de componentes a 1 Hz.
As referências às linhas são renovadas ao mudar de modo ou os filhos da lista.
Cada linha Flash mantém o seu próprio estado nativo e campos extra. Se os dados,
textos, referências e geometria rápida não mudaram, reutiliza o desenho sem percorrer
os filtros nem reaplicar as propriedades. A auditoria das restantes propriedades
corre a 1 Hz, distribuída pelas linhas; deteta também campos extra removidos pelo
cliente. Uma alteração da largura máxima dos nomes atualiza a equipa afetada.
Fechar/desativar o painel ou remover uma linha repõe o estado nativo e liberta os
campos extra; reabrir ou reaparecer reconstrói apenas o necessário.

O Flash comunica os ecrãs visíveis; o Gameface usa `_onShown`/`_onHidden` e o estado
inicial nativo. Os dados da batalha continuam atualizados, mas os formatos de ecrãs
fechados são calculados apenas quando voltam a ser necessários.

Em `general.json`, `performance.diagnostics: true` ativa resumos a cada cinco
segundos: `Performance Python` (média/máximo em ms, linhas resolvidas/enviadas),
`Performance Flash` (desenho e pesquisas) e `Performance Gameface` no `game.log`.
O TAB Gameface envia os tempos pelo comando `onPerformance` do seu próprio modelo
para o logger Python, sem depender da consola JavaScript. Usa `performance.now()`
quando disponível (com fallback para `Date.now()`). O resumo inclui `calls`, média,
máximo, duração da janela e `rows` (soma das linhas processadas, não jogadores únicos).
`reason=interval` indica uma janela de cerca de cinco segundos; `hidden`/`dispose`
identificam o resumo parcial ao fechar/remover a vista. Fechado, não acumula amostras.
`rowsDrawn` e `rowsReused` distinguem linhas reaplicadas e reutilizadas; `searches`
conta pesquisas da lista nativa. As referências são renovadas quando o DOM nativo
muda, com uma auditoria a cada cinco segundos. Se `MutationObserver` não estiver
disponível, a descoberta usa uma verificação por segundo. Alterações aos nossos
overlays não provocam uma nova pesquisa dos componentes nativos.
O TAB conserva texto, estilos e campos extra por jogador. Cada verificação de
layout lê primeiro as posições e estilos nativos, partilhando leituras dos
antecessores e copiando os valores dos estilos, e só depois aplica as linhas alteradas.
As leituras limitam-se às propriedades necessárias: os antecessores contribuem
opacidade/visibilidade e os campos com texto contribuem fontes e posições.
Campos vazios ou ocultos não exigem retângulos; posições da linha e do ícone são
lidas quando existem campos extra. Os estilos de ícones são preparados apenas
para linhas que precisam de reaplicação, ainda antes das escritas. A verificação
periódica continua a detetar mudanças de posição, fonte e visibilidade mesmo sem
notificação do observador.
Os overlays novos são preparados fora do DOM e inseridos em conjunto quando
`DocumentFragment` está disponível. Formatos vazios apenas ocultam o campo nativo;
texto simples não passa pelo parser HTML. Mudanças de resolução,
posição, opacidade, fontes, identidade ou componentes também invalidam a linha.
Linhas removidas, desativadas ou ocultas libertam os overlays e repõem os estilos;
a reposição preserva alterações de estilo feitas posteriormente pelo cliente.
Ao fechar o TAB através do modelo, os overlays são retirados do DOM e os estilos
nativos repostos, mas os textos já preparados são conservados para a reabertura.
Na reabertura, posições, estilos e dados são novamente verificados. A remoção do
modelo ou da vista liberta também essa cache; não há desenho enquanto o TAB está fechado.
A construção de linhas novas é dividida em grupos de até seis por execução,
continuando no próximo `requestAnimationFrame` (ou num temporizador de 16 ms se
essa API não existir). As linhas pendentes conservam o conteúdo nativo até serem
preparadas. Fechar ou remover a vista cancela a continuação; cada grupo usa os
dados e componentes atuais. Linhas já preparadas continuam a atualizar normalmente
e a reabertura reutiliza os seus elementos sem esta divisão.
Os grupos adicionais contam como chamadas de `renderTab` no diagnóstico. Por isso,
na abertura, comparar o máximo por chamada e não apenas a média da janela; esta
medição não representa o tempo total até todas as linhas estarem preparadas.
Desativar o diagnóstico descarta a janela pendente. A medição cobre o trabalho
síncrono de `renderTab`, incluindo consultas/alterações ao DOM; não mede a pintura
posterior do Gameface, a GPU ou o tempo completo de um frame do jogo.
No Python, cada jogador conserva também os formatos resolvidos de loading, TAB
e perfis do painel já apresentados. Alternar a visibilidade seleciona esses
resultados sem voltar a resolver macros se as dependências e as teclas relevantes
não mudaram. Cada resultado regista os macros efetivamente avaliados, incluindo
condições, nomes dinâmicos, referências a formatos e valores de substituição.
`hp-ratio` depende de `hp` e `hp-max`; a disponibilidade depende de `xvm-stat`.
Alterações a valores não usados, incluindo `my-*`, não invalidam esse resultado.
Uma condição alterada volta a avaliar o formato e regista as dependências do novo
ramo. A configuração, a arena e o lado do jogador também são verificados; ecrãs
ocultos só são resolvidos quando voltam a ser necessários.
Jogadores removidos e o fim da batalha libertam os respetivos resultados. O contador
Python `resolved` conta jogadores com formatos efetivamente resolvidos nessa
janela, não as linhas reconstruídas apenas para selecionar outro ecrã.
Com diagnóstico ativo, `invalidations` lista até oito causas mais frequentes
por janela, por exemplo `hp:1,my-hp:3`. Os números contam formatos recalculados
por causa, não jogadores únicos; um formato pode ter várias causas. `cold` indica
um resultado ainda não preparado, `hotkeys` alterações às teclas relevantes e
`side` uma troca de equipa. Só são registados nomes de macros, nunca os seus valores.
As larguras `pp.widthLeft`/`pp.widthRight` conservam a última medição válida de
cada lado enquanto o painel lateral está oculto ou sem linhas associadas.
Ocultar o painel ao abrir TAB não publica zeros nem invalida essas macros.
Ao reaparecer, as larguras são novamente medidas, incluindo reduções de largura;
o modo `none` continua a publicar zero quando efetivamente apresentado. A
reposição/destruição do renderer limpa as medições.
O resumo Flash separa médias por ciclo em `search`, `panel`, `table` e `cleanup`,
e conta `rowsDrawn`/`rowsReused` durante a janela de cinco segundos. `panel` inclui
a verificação e aplicação das linhas; `cleanup` mede a reposição de linhas/ecrãs
que deixaram de ser usados. Comparar o mesmo replay, modo e intervalo, com o TAB
fechado e depois aberto; não comparar o arranque com um trecho estável.
A opção também aparece no separador Geral. Desativar após recolher a medição.
Os tempos são do trabalho do mod, não uma medição do FPS global do jogo.

`py -3 build_tools/test_panel_flash.py` executa o ActionScript de produção no AIR
local com 30 linhas simuladas: reutilização, HP individual, colunas partilhadas,
atualizações nativas, modos, resolução, remoção/reabertura e auditoria de filtros.
Este teste verifica comportamento; o custo real no Scaleform exige medição no jogo.

A validação indica o JSON e o caminho da opção para referências inexistentes e
geometria/opacidade inválidas. Macros desconhecidos, expressões incompletas e
referências de configuração inexistentes produzem avisos `Configuration:` no log,
sem apagar formatos personalizados que contenham valores de fallback.
