# CarouselStats: perfis inspirados no XVM

Implementacao propria para o carrossel Gameface EU. Referencias consultadas:
https://github.com/modxvm/XVM/tree/master/release/configs/default_wg
(carousel.xc, carouselNormal.xc e carouselSmall.xc).

## Configuracao

As opcoes ficam em `mods/configs/Driftkings/<perfil>/carousel_stats/`:

- `carousel.json`: opcoes gerais, escala colorRating, filtros e ordenacao.
- `carouselNormal.json`: fields e extraFields do perfil normal.
- `carouselSmall.json`: fields e extraFields do perfil compacto.

O perfil e escolhido em `load.json`. Na primeira utilizacao de `default`, os
tres JSON da antiga pasta `CarouselStats/` sao importados sem alterar os originais.
Os tres JSON sao criados automaticamente quando faltam. Os exemplos distribuiveis
estao em `res/configs/Driftkings/default/carousel_stats/`. Nao existem includes nem ficheiros
.xc. A antiga seccao CarouselStats de Driftkings.json e o antigo CarouselStats.json
ja nao sao lidos; as configuracoes slot1 a slot4 foram removidas.

O perfil normal apresenta WN8, percentagem de vitorias e dano medio; o compacto
apresenta WN8 e percentagem de vitorias. Ambos permitem personalizar os campos.
O painel ModList/F10 edita os mesmos JSON, com normal e compacto em duas colunas.
Os ficheiros alterados mantem uma copia .bak. Cada ficheiro e gravado atomicamente;
uma interrupcao entre gravacoes pode deixar perfis de momentos diferentes.
Um JSON invalido e preservado e o erro e registado, sem substituir pelo padrao.
Reinicia o cliente depois de editares os JSON externamente; as alteracoes pelo
painel sao aplicadas diretamente.

- `cellType`: default segue o cliente; normal usa uma linha; small usa duas.
- `rows`: 0 segue cellType; 1 ou 2 forcam as linhas nativas.
  A preferencia do jogo nao e gravada no servidor.
- Cada perfil tem:
- `width` / `height`: dimensoes reais da celula e referencia das coordenadas dos campos extra.
  `gap` define o intervalo entre celulas (0..40). A virtualizacao nativa usa
  a mesma largura, mantendo os alvos de clique associados ao veiculo.
- `fields`: flag, tankIcon, tankType, level, xp, tankName, info, favorite,
  progressionPoints. Cada um aceita enabled, dx, dy, alpha (0..100), scale.
- `extraFields`: ate 64 campos por perfil; a lista ja nao esta limitada a quatro.
  Podem ser acrescentados ou removidos no JSON. As propriedades presentes sao
  editaveis no painel: enabled, format, color, bgColor, src, x, y, width, height,
  fontSize, iconSize, alpha, align (left/center/right), layer (substrate/top).
  `shadow` aceita enabled, color, alpha, blur e distance no JSON.
- Cores fixas usam o seletor visual; expressoes de cor usam um campo de texto.
  As cores fixas aceitam #RRGGBB, 0xRRGGBB ou RRGGBB.

## Macros

Mantem as macros anteriores: wn8, eff, xwn8, xeff, battles, winRate, avgDamage,
avgAssist, avgBlocked, avgStun, avgFrags, avgSpotted, damageRatio, damageHP,
hitRate, marks, mastery. Acrescenta vehicle, level e premium.

Aceita o prefixo v. e os aliases name, tier, tdb, winrate, t_battles e damageRating.
Cores: {{c:wn8}}, {{v.c_winrate}}. Imagens: {{icon:damage}}, {{icon:assist}},
{{icon:blocked}}, {{icon:wins}}, {{icon:battles}}, {{icon:mastery}}.

Formatacao: {{winRate:.1f}}, {{v.tdb%d}}, {{v.winrate%2d~%|--%}}.
O sufixo segue ~ e o valor alternativo segue |. Expressoes nao suportadas
mostram --. Condicoes simples e aninhadas sao aceites, por exemplo
{{premium?#FFD700|#C8C8B5}}. Referencias ${...}, includes .xc e macros
XVM externas nao estao incluidos.

O formato de texto aceita b, i, u, br e font com color, size, face, alpha.
As imagens usam src separado: caminhos locais gui/, img://gui/ ou coui://gui/.
Nao carrega imagens remotas nem recursos xvm:// que nao pertencem ao pacote.

## Limites e verificacao

Integracao na garagem RandomHangar Gameface ja usada pelo CarouselStats.
Nao foi alargada nesta alteracao aos hangares de eventos. O cliente suporta
uma ou duas linhas; mais linhas nao estao implementadas.
As cores usam as escalas Driftkings, sem precisar de XVM instalado.

Testar no cliente: normal/compacto/auto, mudanca entre uma e duas linhas,
selecionar e deslocar veiculos, textos e imagens, cores, salvar/reabrir,
desativar o mod e regressar de batalha. Os testes locais nao substituem esta
validacao Gameface.

## Opcoes gerais adicionais

- Transparencias: backgroundAlpha, slotBackgroundAlpha, slotBorderAlpha,
  slotSelectedBorderAlpha e edgeFadeAlpha (0..100). O fundo geral e uma
  camada propria; a aparencia nao e uma copia pixel a pixel do Flash XVM.
- scrollingSpeed: multiplicador de 0.1 a 10.
- hideBuyTank, hideBuySlot, hideRestoreTank: retiram os respetivos cartoes
  da lista nativa, sem deixar espacos vazios.
- showTotalSlots, showUsedSlots: acrescentam contagens aos cartoes de compra.
- enableLockBackground e suppressCarouselTooltips.
- filters: params, bonus, favorite, elite, premium, cada um com enabled.
  Ocultar um filtro nao limpa uma selecao ja guardada pelo jogador.
- filtersPadding: horizontal e vertical (0..40).
- nations_order, types_order: listas; entradas restantes seguem no fim.
- sorting_criteria: nation, type, level, premium, battles, winRate,
  markOfMastery, damageRating, marksOnGun, battlePassPoints, wn8, avgDamage.
  Prefixo - inverte a ordem. Favoritos ficam primeiro e valores indisponiveis
  ficam no fim. Lista vazia mantem a ordenacao do cliente.
  xte, xtdb, wtr e maxBattleTier nao estao implementados e sao rejeitados.
  Estatisticas sao locais, sem pedidos adicionais a API para ordenar.

## Exemplo compacto DriftKings

`res/configs/Driftkings/default/carousel_stats/presets/carouselSmallDriftKings.json`
inspira-se na configuracao antiga fornecida: 160x35, fundo escuro, mestria,
nome dourado para premium e percentagem de vitorias com a escala escolhida.
Para experimentar, copia o conteudo para carouselSmall.json e escolhe small.
Os perfis existentes e a selecao colorRating sao preservados.

## Compatibilidade do recurso nativo

O build le o bundle Gameface do cliente instalado e valida 15 pontos de
integracao antes de gerar uma copia adaptada dentro do wotmod. Os hooks
mantem os controlos e a selecao nativos, incluindo ao desativar a funcionalidade.
Uma atualizacao do jogo pode exigir atualizar estes pontos e recompilar.
Outro mod que substitua o mesmo bundle da garagem pode entrar em conflito.
O build nao instala ficheiros nem altera os recursos do jogo.

Testes locais: Python 2.7, suite Python e testes Node de renderizacao,
ordenacao, filtros, geometria, deslocacao e desativacao. A validacao visual
na garagem e em diferentes resolucoes ainda tem de ser feita no jogo.
