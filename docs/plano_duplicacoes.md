# Duplicação de código — revisão e plano

> Atualização de contexto — 26/10/2026: As cinco etapas documentadas abaixo foram integradas. O projeto reutiliza os auxiliares numéricos, ciclo de vida dos painéis, conversor Flash/HTML, controlo de configurações e primitivas de ficheiros. Também partilha `common/utils/compat.py` e auxiliares AS3 de cor/sombra/HUD. As cores fixas usam `#RRGGBB`. Os resultados antigos são históricos; não foi repetida uma pesquisa global de duplicações nesta atualização. Ver o [estado atual](STATUS.md) e o [guia de contribuição](CONTRIBUTING.md).

Âmbito: Python cliente, ferramentas de build, JavaScript Gameface e fontes ActionScript. Comparação estrutural de funções Python e blocos de texto, seguida de revisão dos candidatos. Traduções, código gerado e tabelas de dados não foram tratados como duplicação de lógica.

## 1. Conversão numérica — primeira prioridade

- core/marks_calculator.py: safe_number(value, default=0.0)
- lobby/hangar_marks_of_excellence.py: finite(value, default=0.0)
- views/marks_model.py: finite(value, default=None)
- lobby/vehicle_carousel.py: number(value, default=None), equivalente com variáveis e ordem das exceções diferentes.

Extrair uma função pura para common/utils/numbers.py. Preservar os valores padrão de cada consumidor com aliases ou wrappers. Testar None, strings numéricas, booleanos, NaN, infinito e overflow. Não confundir esta conversão com stats/vehinfo.finite_number, que valida um tipo numérico sem converter strings.

## 2. Estrutura comum do HUD Gameface

views/battle/battle_marks_of_excellence.py e views/battle/high_caliber_gameface.py repetem criação de ViewModel/ViewComponent, ligação a RandomHUDView, visibilidade, cursor, referências fracas, publicação de payload e descarregamento. setVisible é idêntico.

Extrair apenas o ciclo de vida partilhado para um adaptador base de batalha. O projeto já tem views/hangar/common.py para o hangar; não usar diretamente a base do hangar em batalha. Manter cálculo, conteúdo dos modelos, comandos e gravação de posição em cada funcionalidade. Testar descarregamento, Ctrl/cursor, mudança de HUD e reinício de batalha.

## 3. Conversão segura de texto Flash para HTML

BattleEfficiency/results.js e RatingPlayers/ratings.js têm copyText com um bloco comum. A versão dos jogadores suporta também face, alpha, size=0 e unidades rem em certos contextos.

Criar um renderizador ES5 partilhado com opções explícitas. Preservar as diferenças de opções por consumidor e a filtragem de elementos e atributos. Rever também o renderizador próprio do relógio antes de o incluir: o relógio suporta textformat/tab e tem regras diferentes.

## 4. Paragem e atualização dos controladores de hangar

lobby/hangar_preferences.py e lobby/tech_tree_marks_of_excellence.py repetem stop do callback. Há semelhança com os controladores já existentes em views/hangar/common.py.

Avaliar reutilização do controlador existente. A função repetida tem apenas quatro linhas: não criar uma hierarquia nova só para eliminar este bloco. Validar a ordem de cancelamento e a possibilidade de reativação.

## 5. JSON, hashes e ficheiros — revisão separada

Há helpers semelhantes em common/utils/filesystem.py, settings/store.py, core/updater e build_tools. O leitor do updater impõe limites e valida ficheiros; o validador da build rejeita chaves JSON duplicadas; write_new usa criação exclusiva; atomicWrite substitui com recuperação. Não são intercambiáveis.

Reutilizar as primitivas adequadas após documentar os contratos, sem unificar validadores de segurança apenas pelo nome. O runtime é Python 2.7; build_tools usa Python 3 e não deve ser importado pelo cliente.

## O que manter separado

- _component(): resolve módulos distintos e evita imports circulares; repetição curta intencional.
- Declarações de eventos/hooks: padrões semelhantes para ciclos de vida diferentes.
- Dicionários enviados como JSON: estrutura pública, não converter automaticamente em namedtuple.
- Índices de escalas, dados de cores e traduções: dados semelhantes não são necessariamente lógica duplicada.
- ActionScript: a pesquisa de blocos não encontrou nesta passagem outro candidato longo idêntico entre ficheiros; não constitui prova de ausência de duplicação semântica.

## Execução proposta

1. Números: extração pequena com teste de equivalência.
2. Adaptador base de batalha: testes de ciclo de vida e validação no jogo.
3. Renderização Flash/HTML: testes Node, ES5 e comparação visual.
4. Controladores de hangar: reutilizar apenas se reduzir a complexidade.
5. I/O e updater: tratar em etapa própria com testes de falha.

Esta revisão não altera código de produção nem contém commit/push.

## Estado da etapa 1

Conversão extraída para common/utils/numbers.py. Mantidos nomes públicos e defaults de cada consumidor. Comparação com as quatro funções anteriores: 144 verificações equivalentes, incluindo fallbacks personalizados. Etapas 2 a 5 por iniciar.

## Estado da etapa 2

Base BattleCardAdapter criada em views/battle/common.py. Marcas e MainGun reutilizam instalação, child ViewModel/ViewComponent, eventos de cursor/visibilidade, propriedade do filho, publicação e descarregamento. Cada funcionalidade mantém regras de posição, ativação e construção dos dados. A autoria dos hooks continua no módulo da funcionalidade. Validação no jogo pendente.

## Estado da etapa 3

Conversor ES5 extraído para shared/flash_text.js, com opções por consumidor. BattleEfficiency mantém apenas cor e tamanho em px; RatingPlayers mantém fonte, alpha, size=0 e unidades dinâmicas. Catálogo e bootstrap atualizados pelo gerador; asset incluído no contrato de build. Testes Node integrados em test_gameface.js; equivalência com os conversores anteriores confirmada em quatro contextos. Relógio preservado por ter semântica distinta. Validação visual no jogo pendente.

## Estado da etapa 4

A repetição dos controladores de hangar era a subscrição do sinal de configurações, não cancelamento de callbacks. Ciclo start/stop partilhado em core/settings_controller.py, usado pelas opções do hangar, árvore tecnológica e relógio através da base HangarController existente. Mantidos os handlers específicos, o estado active, a subscrição por secção e a ordem de atualização do relógio. Testes cobrem chamadas repetidas, stop antes de start e reativação.

## Estado da etapa 5 e publicação

Primitivas de publicação/recuperação centralizadas em common/utils/filesystem.py, mantendo os imports públicos de settings/store.py. Hash do instalador usa a primitiva comum; inventory.py mantém o hashing autónomo por também ser carregado sem pacote pelo build. Escrita da cache de tripulação passou a publicação recuperável. Leitores JSON estritos e validadores de caminhos do updater permanecem separados.

Beta 0.1.2-beta.5 publicada com instalador e manifesto assinado. Commit b6afb5c; CI remoto 39368442484 passou. Testes locais: 111 core em Python 2.7/3, 25 painel em ambas as versões, 22 instalador, Node e ESLint. Validação no jogo e instalação real continuam por confirmar.
