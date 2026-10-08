# MinimapPlugins 2.0

Implementacao no SettingsLab, integrada no Core e no Flash unificado
DriftkingsBattle. Nao depende do ModSettingsAPI.

## Onde configurar

ModList / F10 -> MinimapPlugins, em duas colunas, com seletores visuais de cor,
listas de visibilidade e campos de formato. A configuracao ativa fica em
`mods/configs/Driftkings/<perfil>/minimap_plugins/`, com o perfil escolhido
em `load.json`. Os exemplos ficam em `res/configs/Driftkings/default/minimap_plugins/`:

- `minimap.json`: ativacao, icones, apresentacao, dimensoes e mira PNG.
- `minimap_labels.json`: etiquetas, HP e ultima deteccao.
- `minimap_circles.json`: circulos normais e adicionais.
- `minimap_lines.json`: direcao, limites do canhao e estilo.

O antigo `minimap_plugins.json` e importado automaticamente e preservado como
copia de referencia. Depois da migracao, editar os novos ficheiros. As gravacoes
conjuntas usam um diario de recuperacao para impedir configuracoes parcialmente
atualizadas. As opcoes do painel aplicam-se na batalha seguinte.
Na primeira utilizacao de `default`, importa a antiga seccao `components.MinimapPlugins`.

As opcoes anteriores sao preservadas. A antiga opacidade `alpha` e importada
para os quatro circulos na primeira leitura do esquema antigo. Depois, cada
circulo tem a sua propria opacidade. As quatro cores existentes permanecem.

## Etiquetas

`labels` permite ativar/ocultar etiquetas, escolher tamanho (8-24) e opacidade.
Os formatos `normal`, `alternative`, `dead` e `lost` sao independentes.
Exemplo:

```json
"labels": {
  "enabled": true,
  "normal": "{{vehicle}}",
  "alternative": "{{vehicle}} - {{name%.16s}}",
  "dead": "X {{vehicle}}",
  "lost": "? {{vehicle}}",
  "fontSize": 10,
  "alpha": 100
}
```

Macros locais: `vehicle` (nome apresentado pelo cliente), `name` (jogador),
`level`, `type`, `state` (alive/lost/dead), `hp`, `maxHp`, `hpPercent` e
`lostSeconds`. Os valores de HP desconhecidos usam `--`. `%.16s` limita o texto a 16 caracteres,
incluindo os dois pontos finais de truncagem. Texto simples, sem HTML ou macros
remotas de estatisticas. As cores das etiquetas seguem a equipa e o modo daltonico por defeito.
`customColors` permite substitui-las com `allyColor`, `enemyColor`, `squadColor`
e `deadColor`. `x`, `y`, `align` e `shadow` controlam o posicionamento e a sombra.
Os formatos `ally`, `enemy`, `squad` e `alternativeAlly`/`alternativeEnemy`/
`alternativeSquad`, quando vazios, herdam `normal`/`alternative`.

`avoidOverlap` e opcional: no mapa normal, abrevia nomes com `compactLength` e
oculta os que continuam sobrepostos, dando prioridade ao pelotao e aos inimigos.
Ao ampliar com a tecla, mostra novamente os nomes completos. A comparacao de
posicoes usa o ciclo visual existente de 250 ms; nao ha formatacao por frame.

A visibilidade nativa dos nomes ainda se aplica: ativa os nomes de veiculo no
minimapa nas definicoes do jogo para os ver permanentemente. `showNames` controla
os nomes dos destruidos; `showVehicleTypes` controla os icones dos veiculos.
A apresentacao de destruidos e ultimas posicoes continua dependente das opcoes
respetivas. `lost` e aplicado a posicoes guardadas pelo modulo, sem obter novas
posicoes de adversarios ocultos.

## Circulos e linhas

`circles.draw`, `maxView`, `proximity` e `view` aceitam:

- `mode`: client (seguir o jogo), on (mostrar), off (ocultar).
- `alpha`: 0-100, independente para cada circulo.

Os raios de desenho e detecao sao obtidos do modo de batalha, em vez de valores
fixos de 565/445/50 metros. `viewRadius` permite desenhar o alcance de visao real;
isto nao altera as regras de detecao do jogo. `changeColorCircles` escolhe entre
as quatro cores configuradas e as cores nativas, sem desativar a opacidade.

`lines.direction` e `lines.sector` usam client/on/off. `customStyle` ativa as
cores `directionColor`, `sectorColor` e a opacidade `alpha`. Sao as linhas nativas
de direcao da camara e de limites do canhao; o modulo nao inventa limites para
veiculos que nao os tenham. `yaw` estende a apresentacao a veiculos com limites
reais, alem das artilharias. Por defeito, comprimento, tracejado e espessura seguem o cliente.
`lines.geometry` (com `customStyle`) permite alterar `length`, `thickness`,
`dash` e `gap`. O comprimento e medido nas unidades locais do minimapa; nao em
metros do terreno. `dash: 0` significa linha continua. O angulo e a visibilidade
continuam a seguir a camara e os limites reais do canhao.

Cada circulo normal aceita `thickness`, `dash` e `gap`. `extraCircles` aceita ate
oito circulos em metros, filtrados por `vehicleClass` (`all`, `lightTank`,
`mediumTank`, `heavyTank`, `AT-SPG`, `SPG`). Exemplo:

```json
"extraCircles": [
  {"radius": 100, "color": "FFFFFF", "alpha": 60,
   "thickness": 1, "dash": 5, "gap": 4, "vehicleClass": "SPG"}
]
```

O painel inclui um editor JSON para esta lista; as restantes opcoes tem
controlos individuais, incluindo seletores visuais de cor.

## Apresentacao alternativa

Mantem premida a tecla configurada em `button` (Ctrl esquerdo por defeito).
`presentation` permite ativar a alternativa, ampliar ou apenas mudar etiquetas,
centrar ou manter no canto inferior direito, escolher tamanho 0-5 e opacidades
normal/alternativa. `zoomFactor` define a escala; `zoomFactorMax` limita-a.
O zoom tambem e limitado pelo espaco disponivel no ecra.

Ao largar a tecla, abrir as definicoes ou terminar a vista, o estado ampliado
e libertado. O Flash restaura tamanho, posicao, escala, ordem e estilos ao sair.
O mapa segmentado Epic/Frontline conserva o posicionamento nativo: nesse modo
nao se aplica ampliacao/centralizacao. As outras funcoes dependem dos plugins
nativos disponiveis no modo, cujas subclasses sao preservadas.

## Icones, fundo, HP e dimensoes

`icons.scale` e `icons.alpha` alteram apenas os icones dos veiculos. `selfScale`,
`selfAlpha` e `selfColor` personalizam a propria seta.
`presentation.backgroundAlpha` altera apenas a imagem do terreno; os antigos
`normalAlpha`/`alternativeAlpha` continuam a controlar o conjunto, preservando
as preferencias existentes.

`health.visibility`: `never`, `key` (a mesma tecla do minimapa) ou `always`.
`health.mode`: `value`, `percent` ou `bar`. `x`, `y`, `fontSize`, `width` e
`height` ajustam o texto/barra. Os eventos de HP do cliente atualizam apenas o
veiculo alterado. Nao se assume HP cheio para inimigos ainda desconhecidos;
guarda-se o ultimo valor recebido e limpa-se o estado no respawn/troca de tanque.

`lostMarker.showSeconds` acrescenta o tempo desde a perda de deteccao;
`fade` reduz a opacidade ate `minimumAlpha` durante `lastPositionDuration`.
O contador atualiza uma vez por segundo, apenas para posicoes perdidas.

`mapSize.enabled` mostra as dimensoes reais recebidas do modo de batalha.
Pode ajustar `x`, `y`, `fontSize`, `color` e `format` (`{{width}} x {{height}} m`).

## Ciclo de vida e compatibilidade

As ultimas posicoes expiram apos `lastPositionDuration` (0-300 segundos; zero
expira no proximo ciclo). A deteccao de novo do veiculo cancela a expiracao.
Os temporizadores sao cancelados ao terminar a batalha. A formatacao e atualizada
quando muda a apresentacao, a deteccao ou os dados do veiculo.

Com XVM detetado, o modulo nao substitui os plugins nem aplica estilos. Modos
com implementacoes nao derivadas dos plugins comuns mantem a sua implementacao.
Nao foram adicionados marcadores de informacao que o cliente nao tenha recebido.

## Validacao

### Mira de artilharia

`artilleryAim` carrega o PNG MinimapAim do XVM no centro da camara de artilharia
fornecido pelo cliente. A imagem e incluida no pacote com a licenca e atribuicao
do XVM, sem exigir a instalacao desse mod. Aparece apenas enquanto
a entrada nativa da camara estrategica estiver ativa; acompanha a sua posicao
sem consultar coordenadas de veiculos em Python.

Opcoes no painel de configuracao e em `minimap_plugins/minimap.json`:
`enabled` (true), `scale` (50, entre 10 e 200%),
`src` (`gui/maps/Driftkings/Minimap/MinimapAim.png`) e
`alpha` (100, entre 0 e 100%). O tamanho e a orientacao da mira permanecem
estaveis ao ampliar ou rodar o mapa. As cores sao as da imagem; o antigo
parametro `color` e descartado ao ler a configuracao. O PNG e carregado uma vez
por caminho, centralizado pelas suas dimensoes reais e libertado ao desativar.
Se nao for encontrado, a mira fica oculta e e emitido um diagnostico no log.
Usa o ciclo de apresentacao existente para
encontrar a entrada; a atualizacao por frame verifica apenas a visibilidade e
a transformacao dessa entrada. Remove os callbacks ao desativar ou sair.

O teste AIR `test_panel_flash.py --suite minimap` verifica transformacoes,
visibilidade e limpeza. A confirmacao visual exige um replay com artilharia.

Testes automatizados: formatos UTF-8, estados, truncagem, valores invalidos,
raios especificos do modo, ausencia de circulos duplicados, encadeamento das
subclasses de eventos, linhas, expiracao e reaparicao, desativacao e callbacks.
Compilacao Python 2.7 e Flash contra os SWCs locais.

Ainda requer teste dentro do jogo: nomes normais/alternativos, Ctrl e F10,
cores e opacidades, perda de deteccao, destruicao, respawn, resolucao, modo
Epic e regresso a garagem. A compilacao nao comprova a apresentacao visual.
