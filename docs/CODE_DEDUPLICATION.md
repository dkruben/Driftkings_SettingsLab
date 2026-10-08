# Limpeza de duplicações — 2026-10-06

A revisão abrangeu o código Python dos componentes e das bibliotecas, os projetos
Flash e o JavaScript do Gameface. Os formatos de configuração foram preservados.

## Implementações partilhadas

- `source/scripts/client/Driftkings/settings/store.py`: leitura de objetos JSON,
  substituição de ficheiros e publicação recuperável de vários documentos.
  PlayerPanelPro, minimapa e carrossel usam `JsonDocuments`. O painel de
  configurações reutiliza a substituição/recuperação de ficheiros, mantendo a sua
  política de cópias de segurança e proteção dos dados privados.
- `source/scripts/client/Driftkings/views/hangar/common.py`: controlador comum do
  carrossel, marcas e relógio. Carrossel e marcas partilham também a instalação
  dos eventos Gameface, preservando a ativação independente de cada componente.
- `source/scripts/client/Driftkings/views/battle/label.py`: criação, posição,
  sombra e libertação das caixas de texto de BattleEfficiency e BattleStat.
  Cada módulo conserva os seus formatos de texto e nomes de opções.
- `flash_source/shared/as3/driftkings/utils/`: alinhamento, estilos, campos de
  texto, cores, animação e eventos de animação. Substitui 25 ficheiros locais por
  seis classes partilhadas. OwnHealth, FlightTimer e DispersionTimer usam também
  o mesmo cálculo de posição, incluindo o arredondamento original do centro.

O carrossel passa a recuperar o conjunto completo de documentos se uma gravação
falhar a meio, usando o mecanismo comum já necessário no painel e no minimapa.

## Código retirado

- `SixthSenseTimer`, sem chamadas: a implementação ativa do Sexto Sentido conserva
  o seu temporizador e a reprodução de áudio.
- Sete projetos Flash antigos, substituídos pelo pacote unificado:
  ArmorCalculator, DispersionTimer, DriftkingsPlayersPanelAPI, FlightTimer,
  Minimap, OwnHealth e SixthSense.
- As cópias foram guardadas em `build/legacy-flash-sources/` e
  `build/legacy-flash-utilities/`, fora da compilação e do pacote final.

## Repetições mantidas deliberadamente

Não foram fundidos contratos abstratos, pequenos adaptadores de eventos do jogo,
validadores específicos, formatos de texto nem gestores de cache com ciclos de
vida diferentes. Os recursos de HangarEfficiency continuam temporariamente
inativos, conforme o seu README; não foram reativados. TotalLog mantém a sua
fonte específica inativa para eventual recuperação.

Esta revisão reduz duplicações concretas; não significa que toda a semelhança
entre módulos deva desaparecer. O ganho de FPS não foi medido nesta tarefa.

## Validação

- 318 testes Python, incluindo gravação interrompida, recuperação após reinício,
  rejeição de transações inválidas, isolamento dos controladores e libertação
  dos eventos das caixas de texto.
- Teste AIR `SharedUtilsTest`: alinhamentos, cores, HTML com quebras de linha,
  estilos e animações independentes.
- Compilação dos três SWF ativos e verificações/compilação em Python 2.7.
- Pacote local único: `build/unified/Driftkings.wotmod`.

Não foi feita instalação no jogo. A confirmação visual em hangar e replay fica
para o teste do pacote no cliente.
