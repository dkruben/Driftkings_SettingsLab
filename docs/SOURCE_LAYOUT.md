# Organizacao dos modulos, configuracoes e apresentacao

Reorganizacao inspirada na separacao do battle_observer. A implementacao e os
ficheiros dos jogadores continuam a ser os do Driftkings; nao foram copiados
componentes ou configuracoes daquele projeto.

```text
source/scripts/client/Driftkings/
  battle/                  logica, estado e ciclo de vida de batalha
  lobby/                   logica, estado e ciclo de vida da garagem
  components/              componentes transversais e registo
  core/                    servicos e calculos partilhados
  settings/
    settings_data.py       valores, atalhos e acesso partilhado dos 33 componentes
    panel/                 interface interna, sessões de edição e apresentação dos controlos
    templates.py           todos os menus e inicializacao comum
    loader.py              perfis e migracao dos JSON
    registry.py            registo e validacao da janela de configuracoes
    store.py               persistencia comum
  i18n/                    um catalogo por idioma e carregador comum
  views/
    battle/                adaptadores Flash e apresentacao de batalha
      meta/                contratos Python -> Flash
    hangar/                janelas, resultados e apresentacao Gameface
    shared/                janela de configuracoes

flash_source/
  battle/                  projetos AS3 de batalha
  hangar/                  projetos AS3 de garagem/login
  shared/                  janela de configuracoes e bibliotecas SWC

res/flash/
  battle/                  SWF compilados de batalha
  hangar/                  SWF compilados de garagem/login
  shared/                  SWF partilhados
```

## Responsabilidades

Os 33 componentes partilham settings_data.py e templates.py. Os IDs sao
explicitos e independentes do nome do ficheiro compilado. Os controllers herdam
os adaptadores de menu e mantem os callbacks que afetam o jogo. Os valores e as
traducoes foram retirados das antigas pastas settings/battle, hangar e shared.
Os catalogos ficam exclusivamente em i18n, um por idioma.

As vistas usam a configuracao e o estado vivos do componente. Quando e necessario
aceder a esse estado, o adaptador resolve o modulo apenas durante a chamada,
evita imports circulares na inicializacao e nao copia referencias que ficam
obsoletas, como a vista de OwnHealth ou os controllers da garagem.

Os hooks de comportamento permanecem nos controllers. Os hooks de apresentacao
extraidos, como os resultados Flash e widgets da garagem, sao registados por
imports explicitos dos adaptadores `*_hooks.py`; esses imports nao devem ser
removidos como se fossem imports sem uso.

A API publica Driftkings.ui continua disponivel. Os contratos de batalha
foram agrupados em `views/battle/meta`, e a janela de configuracoes fica em
`views/hangar/settings_window.py` (Gameface, também em batalha, com backend em `settings/panel/`). Os servicos comuns de injecao continuam no
pacote Driftkings.ui.

## Configuracoes e recursos instalados

Os perfis mantem os JSON e nomes das opcoes. Traducoes passam para uma pasta
i18n comum, com importacao dos catalogos individuais anteriores.
O Core usa load.json e JSON por componente/perfil; PlayerPanelPro e CarouselStats mantem os
seus documentos separados. Os JSON de distribuicao permanecem em res/configs.

Dentro do wotmod, os SWF continuam em `res/gui/flash/`, com os nomes esperados
pelo cliente. A separacao batalha/garagem aplica-se ao projeto e aos inputs do
build. Os URLs dos recursos Gameface tambem nao mudam.

Os projetos AS3 antigos continuam como referencia, sem serem ativados por esta
reorganizacao. So os sete projetos ativos sao compilados. DispersionCircle
esta novamente ativo e o pacote contem 33 componentes e um unico mod_ de
entrada, mod_Driftkings.

## Acrescentar um componente

1. Acrescentar valores em settings/settings_data.py, o menu em settings/templates.py
   e os textos na seccao correspondente de cada catalogo i18n.
2. Colocar eventos, calculos e estado no modulo de jogo correspondente.
3. Colocar vistas e contratos Flash em views, no contexto respetivo.
4. Colocar AS3 em flash_source e mapear o SWF agrupado no manifesto para o caminho
   publico res/gui/flash. Os ficheiros Python de settings/views sao incluidos
   automaticamente pelo empacotador.
5. Compilar com `python build_tools/build_lab.py --flash`.

## Verificacao

A comparacao de AST confirmou 68 metodos de configuracao sem alteracoes e 35
classes/funcoes de vistas com a mesma logica apos a ligacao ao estado do modulo.
A suite inclui verificacao de imports locais, caminhos AS3/SWF, registo dos hooks
e inicializacao segura de OwnHealth, alem dos testes funcionais existentes.
Compilacao Python 2.7 e Flash concluida. Nao foi feita instalacao nem teste no jogo.

## Shared libraries

All Python infrastructure now belongs to the `Driftkings` namespace:
- `common`: shared configuration infrastructure and utility functions.
- `stats`: statistics and vehicle data.
- `ui`: interface bridge and shared visual helpers.
- `core`: component lifecycle, hooks and orchestration.

The former top-level library packages are no longer shipped. Existing statistics
cache directories are reused when present; new installations use `Stats/cache`.

## Unified release

`Driftkings/__init__.py` owns the single `VERSION`. Internal resource definitions
are in `build_data/components`; only `build/unified/Driftkings.wotmod` is built.
Previous distribution files are archived under `build/retired-single-package`.
