# Organização do Flash

A batalha utiliza uma única biblioteca: `DriftkingsBattle.swf`. O cliente carrega-a
através de `BATTLE_REQUIRED_LIBRARIES`, como no Battle Observer. A biblioteca
regista uma fábrica de componentes na página nativa; não abre uma janela própria.

```text
flash_source/
  battle/
    projects/DriftkingsBattle.as3proj
    src/
      DriftkingsBattle.as
      driftkings/battle/
        base/                    # ciclo de vida e visibilidade
        components/
          armor_calculator/
          dispersion_timer/
          distance_marker/
          flight_timer/
          health/
          minimap/
          overlay/
          ratings/               # jogadores, loading e TAB Flash
          sixth_sense/
  hangar/                        # interfaces atuais em Gameface
  shared/
    as3/driftkings/utils/         # texto, cores, coordenadas e animações
    swc/                         # dependências externas do cliente
```

## Ligação ao Python

Cada módulo declara `getBattleViews()` com `(alias, classe, configuração)`.
O Core publica esse catálogo no pacote `Driftkings.views.battle`, acrescentado a
`g_overrideScaleFormViewsConfig.battlePackages`, como no Battle Observer.

O cliente chama `getViewSettings()` para registar `ComponentSettings` e
`getBusinessHandlers()` para criar o `BattleViewHandler`, derivado de
`PackageBusinessHandler`. Este escuta os eventos `LOAD_VIEW` das páginas de
batalha, localiza a página pelo alias e chama
`view.flashObject.as_DriftkingsCreate(aliases)`. As tentativas são limitadas a 80,
a intervalos de 100 ms, e canceladas quando o handler termina. O PlayerPanelPro
passa a enviar os dados pelo componente criado pelo cliente, sem outro carregador.

O cliente controla o registo/desregisto das classes Python, o ciclo de vida do
handler e a destruição dos componentes. Uma página nova recebe novas instâncias.

O componente de ratings é criado com a página nativa, ainda durante o loading. Mantém os
transportes incrementais e as interfaces Gameface existentes. O DistanceMarker
fornece dados através de um componente DAAPI da mesma biblioteca; a conversão de
coordenadas compensa a escala e a posição da página nativa.

## Compilação e validação

`py -3 build_tools/build_flash.py --publish` compila para `build/flash/` e atualiza
`res/flash/battle/DriftkingsBattle.swf`. As bibliotecas SWC são externas e não são
incorporadas no SWF. `py -3 build_tools/build_lab.py --flash` gera o pacote local.
Nenhum destes comandos instala o pacote no jogo.

Os testes Python cobrem registo, repetição, troca de página e transporte dos dados.
Os testes AIR usam as mesmas fontes: `build_tools/test_panel_flash.py --suite
panel|hud|minimap|utils`. A validação final no cliente exige testar loading, TAB,
DistanceMarker (incluindo Ctrl+arrastar), mudança de resolução e um segundo replay.

## Arquivo

`build/flash-archive-unified/` guarda os dois antigos projetos/SWF independentes e
o carregador Python substituído. As limpezas anteriores estão em
`build/flash-archive-20261006/`, `build/legacy-flash-sources/` e
`build/legacy-flash-utilities/`. Estes ficheiros não entram na compilação nem no
pacote. Não são versões ativas; recuperá-los exige atualizar os caminhos.

## Contratos meta

`source/scripts/client/Driftkings/meta/battle/` define os nove contratos Python/AS:
metodos de envio, verificacao DAAPI e callbacks implementados pelos controladores.
`views/battle/` mantem os eventos e a apresentacao; os modulos de batalha mantem
a logica de jogo. Os imports sao explicitos.

A base `HudMeta` liga a visibilidade do HUD durante `_populate` e desliga durante
`_dispose`. A pagina nativa e responsavel pela destruicao, sem uma segunda
subscricao ao fim da batalha. `PlayersPanelMeta` usa apenas `ComponentMeta`,
para manter o TAB disponivel quando o HUD fica oculto.

`py -3 build_tools/check_flash_contracts.py` verifica os metodos de envio e o
numero de argumentos contra as fontes AS, e exige implementacao dos callbacks.
Esta verificacao corre antes da compilacao pelo `build_lab.py`. Os contratos
anteriores estao arquivados em `build/meta-archive/`, fora do pacote.
