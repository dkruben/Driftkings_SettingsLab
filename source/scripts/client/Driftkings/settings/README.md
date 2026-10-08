# Configurações e constantes

Seguimos a separação usada pelo Battle Observer:

- `../_constants.py`: identificadores, nomes das secções JSON, chaves principais
  das opções e aliases Flash. Não importa o cliente nem as configurações.
- `settings_data.py`: valores predefinidos, atalhos e regras de aplicação.
- `loader.py`: leitura e gravação por módulo e perfil.
- `lifecycle.py`: inicialização e abertura/fecho do painel do próprio pacote.
- `service.py`: acesso comum, aplicação e notificações de alterações.
- `dependencies.py`: resolução das dependências entre controlos.
- `templates/base.py`: inicialização e construção comum dos menus.
- `templates/battle/`, `templates/lobby/` e `templates/components/`:
  apresentação das opções de cada módulo, separada do código de jogo.
- `template_schema.py`: declarações de controlos e campos internos.
- `panel/`: interface Gameface, validação dos controlos e sessões de edição.

Por exemplo, `OWN_HEALTH.ID` identifica o módulo e as traduções, enquanto
`OWN_HEALTH.NAME` identifica o ficheiro `own_health.json`. Os valores de ambas
as constantes preservam os identificadores anteriores.

As predefinições e os templates usam `GLOBAL.ENABLED`, `OWN_HEALTH.COLORS`,
etc. As opções internas de estruturas complexas, como os formatos XVM, mantêm
as suas próprias chaves. Alterar o nome de uma constante Python não muda o
formato JSON; alterar o seu valor exige avaliar a migração dos ficheiros.

`BATTLE_ALIASES` contém os nomes usados pelo registo Python dos componentes.
Esses valores têm de coincidir com a fábrica em `DriftkingsBattle.as`.

O catálogo de configurações não ativa módulos: essa responsabilidade continua
no carregador e em `component_list.py`. Os templates mantêm a ordem, os limites,
as duas colunas e as pré-visualizações atuais; não inferimos limites numéricos
apenas a partir do tipo de um valor.

Cada componente importa diretamente o seu template. Os `__init__.py` destas
pastas não importam nem registam menus. Por exemplo, `battle/own_health.py`
usa `settings/templates/battle/own_health.py`, sem carregar o template do
sexto sentido nem a sua dependência de `ResMgr`. Os nomes das pastas seguem
a organização do código do pacote; os IDs públicos e os JSON mantêm-se.

## Serviço e notificações

`service.py` fornece `getSetting`, `setSetting`, `getComponentDict` e acesso à
configuração pelo alias Flash. Aceita constantes como `OWN_HEALTH`, IDs, nomes
das secções e o objeto proprietário. Caminhos internos usam tuplos como `('panel', 'x')`.

O editor valida os controlos antes de chamar `settings_service.apply`. O serviço
elimina alterações sem efeito e entrega ao `onApplySettings` do módulo apenas
as secções alteradas, com os dicionários internos completos. Os módulos mantêm
a sua validação e gravação, incluindo os JSON repartidos em vários ficheiros.

Depois da gravação, o serviço emite apenas
`onModSettingsChanged(nome_da_seccao, alteracoes)`. Os componentes podem
implementar esse método ou subscrever o evento, filtrando por módulo e por
chaves. `REFRESH_KEYS` limita as opções que acionam o método do componente.
O serviço desliga o método anterior quando o proprietário é substituído.
Um erro na apresentação é registado e não desfaz uma gravação bem-sucedida.
As vistas temporárias ligam/desligam os destinatários em `_populate` e
`_dispose`; o OwnHealth usa esse percurso.

Nas vistas Flash que derivam de `BattleMeta`, `getSettings()` consulta este
serviço usando o ID da vista. ArmorCalculator, DispersionTimer, FlightTimer,
OwnHealth e SixthSense partilham essa implementação. A leitura devolve o
dicionário atual, mesmo que tenha sido substituído; não importa o módulo de
jogo nem guarda uma cópia das configurações. O SixthSense ainda consulta o
módulo para as mensagens e os estados de deteção específicos do jogo.

Esta separação não altera as regras de aplicação: opções que exigem a próxima
batalha continuam a ser identificadas dessa forma pelo painel.

## Definições declarativas

Os 31 menus usam o construtor comum de `template_schema.py`. Quinze definem
`COLUMNS` com declarações `control`, `slider`, `options` e `hotkey`; os outros
16 fornecem duas colunas através de `getControlColumns`, gerando os campos
que dependem da configuração, traduções ou recursos do cliente. O construtor
comum prepara o cabeçalho e constrói os controlos para cada apresentação.
Também as colunas dinâmicas devolvem declarações: não chamam diretamente o
TemplateBuilder. Cores, imagens e metadados de pré-visualização usam a mesma via.

Os limites e a ordem são explícitos. A função `field` centraliza os caminhos
internos, limites e listas dos campos do minimapa, carrossel e PlayerPanelPro.
Os geradores preservam as regras específicas, macros e pré-visualizações.
AccountManager e BanksLoader completam as 33 secções de configurações, mas não
têm um menu neste painel.

`HANDLER_VALUES`, em `_constants.py`, declara as relações entre interruptores e
opções dependentes. O Gameface avalia essas relações durante a edição, antes
de guardar. Relações que não pertencem ao bloco apresentado são ignoradas.

As relações podem depender de `true`, `false` ou de valores de uma lista; o
adaptador converte estes últimos para os índices apresentados pelo Gameface.
Secções internas com um interruptor `enabled` controlam os respetivos campos,
incluindo perfis personalizados, sem desativar campos de outras secções.

## Proprietários e compatibilidade

Os consumidores de jogo e Flash leem pelo serviço. O acesso direto a `data`
fica na infraestrutura e nos proprietários para carregar, validar e gravar.
`apply(..., persist=False)` serve alterações temporárias de batalha: conserva
as referências aos dicionários, publica alterações e não escreve em disco.
As alterações persistentes continuam a passar pela validação do proprietário;
não se deve modificar o dicionário antes de chamar `apply` ou `setSetting`.

O ciclo do painel usa `onPanelOpened` e `onPanelClosed`. Foram removidos os
objetos de ligação ao ModSettingsAPI, os adaptadores de blocos sem consumidores
e as subclasses de componentes que apenas encaminhavam notificações.
As classes com validação, migração, cache ou estado de jogo continuam necessárias.
`TemplateAdapter` converte os controlos para o nosso Gameface; o prefixo interno
`legacy.` dos IDs foi preservado para manter as preferências do painel.

Os formatos JSON, IDs públicos, idiomas, sliders, duas colunas, pré-visualizações,
edição em batalha e regras de reinício mantêm-se. A migração deve ser validada
no jogo abrindo o painel no hangar e numa batalha, aplicando alterações e
confirmando a persistência depois de reiniciar.

## Atualizações seletivas

O evento mantém as secções alteradas completas, mas `SettingsChanges.paths`
identifica os caminhos que mudaram. `affects(changes, ('carousel', 'rows'))`
permite distinguir a alteração das linhas de uma mudança de transparência.
Os destinatários continuam a poder tratar o conteúdo como um dicionário.
A reabertura do painel também publica alterações feitas nos JSON através de
`settings_service.reload`, sem gravar novamente e sem notificar se nada mudou.

PlayerPanelPro preserva as caches dos ecrãs e perfis não afetados. Mudanças de
estatísticas, escala de cores ou limites de apresentação invalidam os contextos
necessários; mudar de arena limpa as caches. O Carousel só atualiza os modelos
nativos de linhas e nações quando essas opções mudam. Os cartões Gameface do
carrossel e das marcas reutilizam os dados do veículo nas alterações de posição,
transparência e estilo; voltar de um estado oculto força nova leitura.

O DispersionCircle mantém o estado calculado em `ReticleState`, separado do
proprietário das configurações. A preferência Beta continua a decidir se as
duas miras são mostradas. A chave histórica `showClientAndServerReticle` permanece
compatível no JSON, mas já não é alterada nem usada como estado durante o jogo.

As dependências do minimapa incluem cores personalizadas, compactação,
desvanecimento, geometria das linhas, apresentação alternativa e o modo de HP.
Títulos dinâmicos e o editor dos círculos adicionais usam declarações comuns.


AutoAimOptimize, SafeShot e SpottedExtendedLight também usam um proprietário
`Settings()` sem lógica de batalha. Os controladores `AutoAimController`,
`SafeShotController` e `SpottedLightController` guardam os alvos, o estado da
tecla, os veículos destruídos e os textos temporários. Consultam o serviço com
o proprietário, pelo que alterações às opções continuam a ser lidas nos eventos
seguintes. Os hooks e a limpeza de batalha apontam para estes controladores;
os IDs, JSON e traduções mantêm-se.

O MinimapPlugins usa `MinimapController` para o estado da apresentação alternativa,
a tecla e as notificações seletivas. A subscrição do teclado existe apenas enquanto
há vistas do minimapa ativas; a última vista limpa o estado ao fechar. A validação
e a migração dos JSON pertencem a `MinimapPluginsSettings`, junto do template.
Recriar uma vista mantém a apresentação alternativa das restantes. O controlador
consulta as opções atuais através do serviço e desliga a subscrição de alterações
quando o módulo termina.

O AimingAngles mantém as coordenadas e a animação em `AimingAnglesController`;
o adaptador visual lê as opções no serviço através de `config`. A criação e a
remoção dos elementos são idempotentes. A morte, o reaparecimento, a abertura
do mapa tático e o fim de batalha cancelam a animação pendente. O ArcadeZoom
guarda a preparação das câmaras em `CameraConfigState`, sem acrescentar estado
ao proprietário `Settings()`. Os formatos JSON e as regras de aplicação das
opções mantêm-se.

ZoomExtended e ArtySplash usam proprietários `Settings()` sem estado de batalha.
`ZoomController` guarda o avatar, as subscrições e as mudanças de câmara pendentes;
limpa-os ao terminar a batalha e ao descarregar o módulo. As opções que exigem
reinício continuam com a mesma regra. O caminho de zoom por distância foi removido
porque a antiga flag interna nunca era ativada; a chave JSON `dynamicZoom` permanece
compatível, sem acrescentar uma funcionalidade que antes não estava operacional.
`ArtySplashController` recebe o proprietário das opções, conserva os modelos e o
estado das teclas, e evita criar modelos repetidos na mesma batalha. A compatibilidade
do atributo de escala pertence agora à inicialização deste controlador.

O PlayerPanelPro mantém o carregamento e a publicação dos JSON divididos em
`PlayerPanelProSettings`. O módulo de batalha apenas liga este proprietário ao
serviço de estatísticas e a `RatingViews`. As notificações pertencem a `RatingViews`,
que subscreve ao iniciar e desliga ao parar; alterações de apresentação preservam
a cache de estatísticas e mudanças de escala invalidam as cores calculadas.
As opções de desempenho das estatísticas são lidas pelo serviço comum, sem o
antigo adaptador `internal_conf`. A gravação continua a validar e publicar antes
de alterar os dados em memória e de emitir o evento de alterações.

O MarksOnGunBattle guarda o histórico estatístico em `MarksBattleCache`, separado
do proprietário das opções. Mantém o diretório central e o ficheiro
`MarksOnGunBattle_stats.json`, incluindo a leitura dos registos antigos. Abrir o
menu já não relê nem regrava esta cache. A normalização da posição e das dimensões
do painel pertence a `MarksOnGunBattleSettings`; os cálculos continuam em `Worker`.
A lista de símbolos coloridos sem consumidores foi removida, juntamente com a
notificação que apenas a recalculava. As cores usadas pelo painel continuam a
consultar a escala configurada.

O MarksOnGunHangar também usa `Settings()` sem preparação visual. A conversão dos
controlos antigos `positionX` e `positionY` pertence a `MarksOnGunHangarSettings`.
O adaptador Gameface constrói as opções visuais a partir das preferências atuais,
sem as modificar. O controlador subscreve as alterações do seu componente em
`start()` e desliga em `stop()`. Mantém os filtros por opção e a reutilização dos
dados do veículo nas alterações de posição e aspeto; o histórico conserva o seu
armazenamento separado.

O CarouselStats concentra a leitura, validação e gravação dos três JSON em
`CarouselStatsSettings`, incluindo as listas de ordenação editadas no menu.
A preparação visual pertence ao adaptador Gameface e lê as linhas nativas e os
lugares disponíveis sem alterar as preferências. `CarouselController` recebe as
notificações diretamente, subscrevendo em `start()` e desligando em `stop()`.
Mantém as atualizações seletivas dos modelos nativos, a cache dos dossiers e a
reutilização do conteúdo dos veículos nas alterações de apresentação.

O AutoClaimClan usa um proprietário `Settings()` e um controlador separado para
os dados do clã e os pedidos de recompensas. O controlador subscreve apenas a
opção `enabled` do seu componente enquanto está no hangar e desliga todas as
subscrições ao sair. A reentrada lê a preferência atual. As regras de recolha,
os níveis ignorados e a proteção contra pedidos de recompensas simultâneos
mantêm-se no controlador.

O BanksLoader usa `BanksLoaderController` para verificar os bancos, acumular as
alterações e gerir o diálogo de reinício. O proprietário `Settings()` conserva
apenas opções e traduções; carregar as configurações não executa a verificação
dos ficheiros de áudio. A verificação ocorre no arranque do controlador, antes
da subscrição dos eventos. Arranque e paragem não duplicam subscrições. Só pode
existir um diálogo de reinício pendente e uma resposta de uma execução anterior
é ignorada depois de parar o controlador, mesmo que este já tenha reiniciado.

O MainGun separa as notificações de conteúdo das de apresentação. O controlador
de batalha liga e desliga a sua subscrição em `start()`/`stop()` e só recalcula
o conteúdo quando mudam a ativação, o formato ou as opções da medalha. A vista
gere posição, bloqueio e opacidade do fundo diretamente, sem recalcular danos
nem tornar visível um painel oculto. A destruição remove também a subscrição
da vista. O painel continua arrastável quando desbloqueado, sem moldura.

No InfoPanel, o controlador recebe apenas alterações que afetam o conteúdo e
desliga a subscrição ao terminar. A vista subscreve durante a batalha e trata
posição, fundo, sombra e estilo. Alterar o estilo reaplica a formatação ao texto
guardado, sem recalcular macros nem acumular etiquetas HTML. Alterações visuais
e de conteúdo não reiniciam o temporizador de ocultação após retirar a mira.
O fim da batalha limpa o texto guardado e a subscrição visual.

No BattleStat, o controlador subscreve as alterações em `start()` e desliga em
`stop()`. Só alterações à ativação, ao formato ou à escala de cores renovam o
conteúdo; a vista trata posição e bloqueio separadamente. O temporizador de
0,3 segundos mantém-se, mas texto e visibilidade só são enviados ao Flash quando
mudam. A cena conserva o estado para reconstruir o Flash e um envio recusado
pode ser repetido. A destruição da vista remove também a sua subscrição.

No BattleEfficiency, o controlador liga e desliga a subscrição com o módulo.
Alterar o formato ou a escala de cores reapresenta os valores guardados em
batalha, sem repetir os cálculos estatísticos. As janelas de resultados abertas
só são atualizadas pelas opções que lhes dizem respeito. A vista gere posição,
bloqueio e sombra e evita envios de texto e visibilidade sem alterações. O fim
da batalha oculta o painel e limpa os dados mesmo quando o módulo foi desativado;
essa limpeza mantém a subscrição necessária para a batalha seguinte.

No MarksOnGunTechTree, `TechTreeController` liga e desliga as notificações com o
módulo. Cada vista aberta conserva os valores brutos dos dossiers em memória;
alterações visuais reutilizam esses valores e aplicam a escala de cores atual.
As notificações nativas da árvore invalidam os registos, mesmo com os indicadores
desligados; a leitura ocorre quando são necessários. Uma nova vista começa sem
dados guardados. Dossiers indisponíveis
podem ser tentados novamente sem bloquear os restantes veículos. O Gameface só
recebe um novo payload quando o conteúdo muda; transações falhadas podem repetir
o envio. Esta cache é exclusiva da vista e não cria ficheiros em disco.

No HangarOptions, as notificações do Battle Pass pertencem ao controlador do
módulo e as do relógio ao `ClockController`. Ambos subscrevem no arranque e
desligam ao terminar. Uma falha no serviço do Battle Pass não bloqueia a
atualização do relógio. A vista usa `publish_card` para evitar envios iguais,
oculta-se quando o controlador termina e remove o estado de visibilidade ao
fechar. O limite de munições é lido diretamente das configurações, sem copiar
valores para a classe nativa `Vehicle`; o módulo desativado e os erros usam a
propriedade original do jogo.

No DispersionCircle, `ReticleState` só aplica opções e subscreve notificações em
`start()`. Guarda os valores nativos existentes nesse momento e restaura o tamanho
mínimo e o registo de marcadores em `stop()`. Cada alteração atualiza apenas o
grupo afetado: escala, tamanho mínimo, marcadores duplos, aspeto ou opção SPG.
O dicionário visual mantém a identidade usada pelas vistas. A espera pela
sincronização das definições do cliente tem uma única subscrição, removida ao
terminar ou desligar a mira dupla. A preferência persistente `useServerAim`
mantém o comportamento anterior; esta migração não a repõe. As opções continuam
identificadas no painel como aplicáveis na próxima batalha.
