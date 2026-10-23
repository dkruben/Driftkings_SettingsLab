# Auditoria de código — 23 de outubro de 2026

Base: `develop`, commit `5d82d09`. Auditoria sem alterações funcionais ou remoção de ficheiros.

## Resultado

As verificações automáticas passam, mas foram reproduzidos erros no caminho de fallback/cache dos valores WN8. Estes devem ser corrigidos antes da próxima beta. Há também lacunas no CI, testes intermitentes e recursos antigos que podem ser retirados do código ativo.

Não foi executado o cliente do jogo nesta auditoria. A confirmação anterior de testes em jogo pertence à versão estável; não demonstra os cenários de dados incompletos reproduzidos abaixo. A análise estática e os testes não garantem a ausência de outros defeitos.

## Cobertura e verificações

- Inventário dos 762 ficheiros versionados e pesquisa de marcadores de conflito, TODO/FIXME, definições Python repetidas, ficheiros idênticos, imports e recursos fora do plano de empacotamento.
- Python 3: 306 testes de core, 27 de settings e 30 de instalador, todos aprovados.
- Python 2.7: 306 testes de core e 27 de settings aprovados; os 265 módulos do cliente foram analisados pelo parser.
- Todos os ficheiros `tests/settings_panel/test_*.js` executados, incluindo os que não entram em `npm test`; aprovados.
- Lint ES5 aprovado; 32 ficheiros JavaScript e 77 documentos JSON analisados sem erros de sintaxe.
- Build data, 18 idiomas, defaults e catálogo UI aprovados; zero nomes indefinidos pelo verificador do projeto.
- Validação das patches contra os pacotes locais do jogo aprovada (`validate_build_data.py --check-game`).
- Revisão dirigida dos hooks/lifecycle, estatísticas, configurações, transporte/instalação do atualizador, transações nativas, ferramentas de build/publicação e workflows.
- O CI da revisão estável `e3ff2f1` terminou com sucesso. Foi consultado também um job anterior que falhou num teste intermitente.

## Problemas confirmados

### A01 — Alta: cache WN8 guarda valores vazios e não recupera após o download

Local: `mod/res/scripts/client/driftkings/core/player_ratings.py:297–336`.

`getExpectedWn8()` pode guardar `{}` quando existem veículos do tier/classe, mas ainda não há dados de referência válidos. A consulta seguinte devolve esse dicionário imediatamente. A chegada de dados em `stats/vehinfo.py` não invalida `_wn8Cache`.

Reprodução com os módulos reais e os stubs existentes dos testes:

1. Consultar um veículo de tier 8/heavyTank sem expected values: resultado `{}`.
2. Acrescentar expected values válidos ao veículo: a consulta continua a devolver `{}`.
3. Calcular WN8 com esse veículo: `KeyError: 'expFrag'`.

Impacto: estatísticas de jogadores podem deixar de ser aplicadas; valores aproximados também podem permanecer desatualizados durante a sessão. `applyPlayerStats()` captura o erro por jogador, pelo que esta reprodução não demonstra um crash global do jogo.

Correção proposta: não guardar resultados incompletos; devolver indisponível quando não houver amostras válidas; invalidar/versionar a cache quando os expected values forem carregados ou atualizados. Cobrir a transição sem dados → dados disponíveis.

### A02 — Alta: média WN8 divide também pelos veículos sem dados

Local: `mod/res/scripts/client/driftkings/core/player_ratings.py:312–334`.

Os contadores `values[2]` e `values[3]` são incrementados antes de verificar `_expectedFromVehicleData()`. Os numeradores só acumulam dados válidos, mas o divisor inclui os veículos rejeitados.

Reprodução: dois veículos do mesmo tier/classe, um sem expected values e outro com `expDamage=1000`, produzem `expDamage=500`. Os restantes valores de referência também ficam reduzidos para metade.

Impacto: classificação WN8 distorcida para veículos que usam a aproximação. Não é uma alteração à fórmula WN8; é um erro na seleção/contagem das amostras.

Correção proposta: contar apenas veículos que contribuíram efetivamente para cada soma, com teste de amostras mistas e de ausência de amostras válidas.

### A03 — Média: validação superficial permite substituir cache válida por dados inúteis

Local: `mod/res/scripts/client/driftkings/stats/vehinfo.py:43–57,181–185`.

`valid_wn8()` só exige uma lista `data` não vazia. `_scale_documents()` usa `any()`, aceitando um documento misto com uma escala válida e outras inválidas.

Reproduções:

- `valid_wn8({'data': [{}]})` devolve `True`.
- `loadJsonData()` aceita esse documento e substitui o ficheiro WN8 anterior por `{"data":[{}]}`.
- `valid_xvm_scales({'xwn8':[1,2], 'xeff':'invalid'})` devolve `True`.

Impacto: a promessa de preservar a última cache utilizável não cobre estas respostas estruturalmente inválidas. No arranque seguinte podem faltar dados que antes estavam disponíveis.

Correção proposta: validar os campos efetivamente consumidos e os limites numéricos antes de publicar. Definir uma política explícita para documentos parcialmente válidos: filtrar/mesclar entradas válidas ou rejeitar o documento, preservando a cache anterior. Evitar exigir que todos os metadados remotos sejam escalas.

### A04 — Alta para o fluxo beta: `develop` não tem CI automático

Local: `.github/workflows/python-package.yml:3–7`.

Os eventos `push` e `pull_request` só incluem `main` e `master`. O fluxo agora documentado usa `develop`; um push para esse branch ou PR dirigido a ele não executa este workflow.

Correção proposta: incluir `develop` nos dois filtros. Manter ou retirar `master` conforme a política pretendida. Esta alteração não publica releases nem envia mensagens.

### A05 — Média: teste de estatísticas tem uma corrida entre threads

Local: `tests/core/test_player_panel.py:69–97`; thread iniciada em `core/player_ratings.py:678–681`.

O teste substitui o worker por uma função que acrescenta elementos a uma lista, mas mantém uma thread real. As asserções seguintes verificam essa lista imediatamente, sem `join`, evento ou executor determinístico.

Há uma falha real registada no [job 39882832972](https://github.com/dkruben/Driftkings_SettingsLab/actions/runs/39882832972): Python 2.7, `test_answered_accounts_are_not_fetched_again_without_the_cache`, linha 97, `AssertionError: 1 != 2`. A revisão estável seguinte passou; os testes locais desta auditoria também passaram. Não houve alteração deste teste entre esses dois commits.

Correção proposta: usar um executor síncrono controlado para o teste de decisões de retry; testar concorrência separadamente com sincronização explícita. Não acrescentar sleeps arbitrários.

### A06 — Média: o comando padrão não executa todos os testes JavaScript

Local: `package.json:6`, `tests/settings_panel/test_gameface.js:2–6`, `.github/workflows/python-package.yml:64–65`.

`npm test` e o CI só executam o agregador `test_gameface.js`. Esse agregador inclui cinco suites, mas não inclui `test_settings_window.js` nem `test_ratings.js`. Ambas passaram quando executadas explicitamente nesta auditoria.

Impacto: regressões cobertas exclusivamente por esses testes podem passar pelo CI.

Correção proposta: criar um único runner que execute todas as suites e usá-lo no CI e nas instruções locais, sem executar duas vezes as suites já importadas pelo agregador.

## Robustez e manutenção

### A07 — Média: pedidos de estatísticas sem limite total de resposta e sem fecho explícito

Local: `mod/res/scripts/client/driftkings/core/player_ratings.py:234`.

`urllib2.urlopen(...).read()` lê a resposta inteira sem teto de tamanho ou deadline total e sem `closing()`/`finally`. O timeout de socket não equivale a um limite de tempo de toda a transferência. O código corre num worker, o que evita bloquear diretamente a UI, mas não limita memória ou duração total do worker.

Correção proposta: reutilizar o padrão de leitura limitada já existente em `stats/vehinfo.py`, fechar explicitamente a resposta e preservar os mecanismos de generation/retry. Trata-se de uma lacuna confirmada no código; não foi simulado um servidor remoto lento nesta auditoria.

### A08 — Baixa: exceções do relógio perdem o traceback

Local: `mod/res/scripts/client/driftkings/views/hangar/hangar_preferences.py:69–70,125–126,138–139`.

Estes `except Exception` usam `LOG.error()` sem `exc_info`, contrariando a regra de diagnóstico em `contributing.md`. Não confundir com o erro de recurso inexistente na linha 135, que não está num handler de exceção.

Correção proposta: `LOG.exception()` nos três handlers; conservar o fallback que esconde o painel quando necessário.

### A09 — Baixa: imports realmente sem utilização

Imports avaliados pelo pyflakes, pesquisa de consumidores e testes de compatibilidade:

- Corre��o da auditoria: `core/updater/__init__.py` conserva `logging`, `os`, `threading`, `time`. O teste `test_public_service_and_dependency_exports_remain_available` exige esses exports p�blicos; n�o s�o candidatos a remo��o.
- `battle/battle_preferences.py`: `events`, `on_event`.
- `build_tools/compiler.py`: `hashlib`.

Os outros avisos de imports em `__init__.py`, `game_constants.py` e `settings/__init__.py` incluem reexports públicos. Não remover em massa. Os avisos de `unicode`, `long`, `StandardError`, etc. no pyflakes Python 3 correspondem a nomes válidos de Python 2.7 e não são defeitos confirmados.

### A10 — Preparação da próxima beta ainda usa identidade da estável

Local: `build_data/release.json:3–4` e `mod/res/scripts/client/driftkings/__init__.py:2`.

`develop` ainda contém `0.1.2`/`stable`. Isto é o estado herdado da release, não um erro da versão publicada. Antes de gerar a próxima beta, definir uma versão posterior, por exemplo `0.1.3-beta.1`, canal `beta`, e atualizar as notas para as mudanças efetivas. Não reutilizar `0.1.2` para artefactos beta: clientes já nessa versão não receberiam uma atualização de mesma versão.

## Limpeza de ficheiros e pastas

### Candidatos confirmados fora do pacote atual

- `mod/res/gui/gameface/mods/driftkings/hangar_efficiency/`: três ficheiros do painel arquivado; o README confirma que está inativo e o plano de build não os seleciona. Remover do código ativo ou conservar apenas no histórico Git.
- `mod/res/mods/configs/res_map/driftkingshangarefficiency.json`: aponta para esse painel inativo e não entra no plano de build.
- `mod/res/gui/flash/driftkingsbattle.swf`: binário versionado que não é usado pelo plano atual; o asset efetivo vem de `build/flash/driftkingsbattle.swf`, gerado a partir de ActionScript. Remover a cópia em `mod/res` depois de confirmar que nenhum fluxo manual externo depende dela.

### Candidatos que exigem decisão de compatibilidade

Os outros oito JSON de `mod/res/mods/configs/res_map/` não entram no pacote atual. A documentação ainda refere mapas retidos e podem servir de referência para integração legada. Verificar consumidores externos antes de remover a pasta inteira. O nome `driftkingsbattleefficiency.json` aponta para o painel ativo `battle_performance`; o nome antigo, por si só, não prova que o conteúdo esteja obsoleto.

### Não remover como se fossem lixo

- `common/utils/events/lobby_view.py` e `login_view.py` têm conteúdo idêntico, mas criam instâncias de eventos distintas e são importados separadamente. Não deduplicar instâncias.
- Pares `bottom.png`/`bottom_limit.png` e `top.png`/`top_limit.png` em `gui/aimingangles/6/` são idênticos; os nomes fazem parte dos caminhos de recursos. Só consolidar após atualizar os consumidores.
- `__pycache__`, `.pyc`, `node_modules` e `build` são saídas/dependências locais ignoradas, não código obsoleto versionado. `build/releases` contém também os artefactos estáveis assinados; uma limpeza global apagaria esses ficheiros locais.
- A chave privada local está ignorada pelo Git. Não foi aberta, copiada ou incluída neste relatório. A orientação existente recomenda guardá-la fora do repositório.

## Possíveis conflitos entre funcionalidades

- `aiming_reticles` e `server_turret_sync` interceptam `VehicleGunRotator.setShotPosition`. O segundo altera o parâmetro `forceValueRefresh` que o primeiro usa para decidir o caminho. Não foi comprovada uma falha; acrescentar um teste combinado e verificar ambos ativos/inativos em jogo.
- `battle_marks_of_excellence` e `hangar_marks_of_excellence` interceptam `MarkOnGunAchievement.getUserCondition` e ambos podem devolver texto sem chamar o próximo hook. Com ambos ativos, o hook exterior com dados disponíveis determina o tooltip. Definir/documentar a precedência pretendida e testar os quatro estados das opções. Isto é uma sobreposição real, não prova de comportamento incorreto.
- As duas interceções de `RandomHangar._getChildComponents` preservam o resultado anterior: uma acrescenta o relógio e a outra remove a entrada de lootboxes. Não encontrei substituição direta de um resultado pelo outro neste caminho.

## Ordem sugerida

1. Corrigir A01–A03 com regressões dos cenários reproduzidos.
2. Ativar CI em `develop`, estabilizar A05 e unificar a execução JavaScript.
3. Limitar os pedidos da API e melhorar o logging; retirar os imports sem uso.
4. Retirar o painel arquivado e avaliar os recursos antigos sem apagar os artefactos publicados.
5. Preparar a identidade da próxima beta, compilar e validar em jogo as combinações de hooks afetadas.

Nenhuma correção funcional, remoção, commit ou push foi feito durante esta auditoria.
