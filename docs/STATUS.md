# Estado do projeto e da documentação

Atualizado em 2026-10-30. Os caminhos e comandos partem da raiz do repositório.

## Como retomar o trabalho

1. Ler este documento para conhecer o estado e as pendências; depois [CONTRIBUTING](../CONTRIBUTING.md) para arquitetura, contratos, verificações e build, e [Development References](DEVELOPMENT_REFERENCE.md) para as fontes externas.
2. Executar `git status --short`, `git branch --show-current` e `git log -5 --oneline`. Confirmar alterações locais antes de editar; este documento é um retrato datado, não substitui o Git.
3. Consultar `build_data/release.json` para versão/canal/changelog e `build_data/build_config.json` para cliente, referência, dependências e empacotamento. Abrir o guia da funcionalidade afetada através do índice abaixo.
4. Distinguir alteração de código, build local, instalação no jogo e publicação no GitHub. Uma dessas operações não implica as restantes; seguir o âmbito do pedido atual.

## Referência atual

- Branch de desenvolvimento: `develop`; `main` é a branch stable.
- Versão stable publicada: `0.1.4` (latest). Beta publicada: `0.1.5-beta.1` (prerelease, tag no commit `3176085`). O código posterior ao tag não atualiza automaticamente os assets publicados; não reconstruir nem mover tags existentes para incluir novas alterações.
- Último commit funcional de integração: `dbbe7dd` (testes, constantes e utilidades), enviado para `develop` e integrado em `main` para stable 0.1.4. `88930b6` contém as correções do Account Manager; `4d40588` removeu OpenWG Common.
- Alvo do cliente: WoT `2.4.1.1`, Wargaming EU/NA/ASIA; contratos e ferramentas em `build_data/` e `build_tools/`.
- As versões publicadas e os downloads estão no [README](../README.md). O histórico de publicação permanece nas releases e no Git.
- O painel de configurações continua em construção. A ausência de erros num replay não valida todas as páginas, previews ou operações de gravação.
- As seis fases de otimização foram revistas e enviadas no commit `202f476`. A auditoria estática não demonstra ganhos quantitativos de FPS.

## Guias mantidos

| Área | Documento |
| --- | --- |
| Instalação, funcionalidades e downloads | [README](../README.md) |
| Desenvolvimento, verificações e publicação | [CONTRIBUTING](../CONTRIBUTING.md) |
| Painel de configurações | [Relatório funcional](RELATORIO_PAINEL_CONFIGURACAO.md) |
| Marcadores dos veículos | [Guia dos marcadores](vehicle_markers/README.md) |
| Carrossel | [Guia do carrossel](vehicle_carousel/README.md) |
| Modo Halloween | [Halloween mode](halloween/README.md) |
| Preferências do lobby | [Guia](hangar_preferences/README.md) |
| Fontes e caracteres | [Fonts and characters](fonts/README.md) |
| Traduções | [Guia i18n](i18n/README.md) |
| Áudio e Sexto Sentido | [Bancos](audioww/README.md) e [ícones](sixthsense_icons/README.md) |
| Referências locais de desenvolvimento | [Development References](DEVELOPMENT_REFERENCE.md) |
| Otimização e pendências | [Auditoria final](AUDITORIA_FINAL_INTEGRACAO.md) |

Os adaptadores atuais usam `gameface/battle`, `gameface/lobby`, `flash/battle` e `flash/lobby`; os contratos ativos estão em `interface_catalog.py`. Os planos de migração concluídos e os estudos antigos foram retirados de `docs`. Os dados locais dos estudos foram preservados em `../Driftkings_SettingsLab_docs_backup_20261028/`; os relatórios versionados continuam recuperáveis no histórico Git. As pendências da otimização permanecem na auditoria final.

### Convenções da documentação

- Guias técnicos de funcionalidades ficam em inglês, cada um em `docs/<área>/README.md`; os guias transversais (`DEVELOPMENT_REFERENCE.md`, `CONTRIBUTING.md`) também estão em inglês.
- Relatórios de estado, auditoria e funcionamento do painel ficam em português, em `docs/` com nome em maiúsculas: este documento, `AUDITORIA_FINAL_INTEGRACAO.md` e `RELATORIO_PAINEL_CONFIGURACAO.md`.
- As datas usam o formato ISO `AAAA-MM-DD` quando indicam a revisão de um documento.
- Planos concluídos passam a guia da funcionalidade ou são retirados; o histórico Git conserva as versões anteriores. Em 2026-10-30, `FONTES.md` passou a `fonts/README.md`, `PLANO_HALLOWEEN.md` passou a `halloween/README.md` e `FONTES_DESENVOLVIMENTO.md` foi retirado.

## Comportamentos e limites a preservar

- Configurações de cor usam `#RRGGBB`; as APIs nativas recebem números através dos conversores existentes.
- Preservar fontes, Unicode, aliases de fontes e identificadores externos necessários à compatibilidade.
- Marcadores distinguem equipa, estado vivo/destruído e modo normal/ALT. O editor inclui modelos partilhados e secção de rating.
- A preview do carrossel usa dois veículos fictícios; deve representar a geometria nativa horizontal e aplicar as mesmas regras de campos, macros e cores do renderer.
- O carrossel dispõe de um ícone para zero marcas. Um perfil que oculte o campo através da opacidade pode continuar a escondê-lo.
- O dano efetuado e o esperado têm macros de cor independentes; o separador pode ter a sua própria cor.
- Apply também persiste valores, conforme o contrato atual do painel. Os riscos de aplicação parcial, gravação de segredos e invalidação de estatísticas estão na auditoria final.
- As correções históricas do replay retiraram acessos TextField não suportados do relógio, declararam fontes nativas dos cartões e rejeitaram curvas de calibração planas/invertidas.

## Vida do veículo migrada para Gameface — 2026-10-30

A barra de pontos de vida passou de Flash (`ownhealthui.as`) para uma vista Gameface própria, filha da HUD nativa (`RandomHUDView`), com a arte Driftkings em `gameface/mods/driftkings/vehicle_health/` (moldura, emblema e logótipo; enchimento, riscas e texto desenhados em CSS). A cor segue `avgColor`; a posição usa `x`/`y`/`alignX`/`alignY` e a barra pode ser arrastada em batalha com Ctrl. O AS3, a vista DAAPI, o meta e o alias Flash foram retirados; o registo Flash passa a ter nove contratos e os defaults deixam de ter `colors`.

As páginas de batalha que não carregam a HUD Gameface (Halloween e Fort Rush, segundo `VIEW_BATTLE_PAGE_CONFIG_BY_ARENA_GUI_TYPE` e as extensões da referência EU) deixam de mostrar a barra. O utilizador validou no cliente EU a posição inicial, a atualização com dano e o arrasto.

## Beta 0.1.5-beta.1 publicada — 2026-10-30

A [release v0.1.5-beta.1](https://github.com/dkruben/Driftkings_SettingsLab/releases/tag/v0.1.5-beta.1) está publicada como prerelease; a stable 0.1.4 continua marcada como latest. O tag aponta para `3176085e251a37835eff0369fedcff0b0de9ad1a`, cujo CI passou antes do upload.

A build release foi feita a partir da árvore limpa nesse commit, com verificação do pacote em Python 2.7, instalador Inno Setup e os três testes opcionais sobre o WOTMOD. O manifesto foi assinado com a chave existente. Os 11 assets enviados coincidem em tamanho e SHA-256 com o inventário local; o manifesto e a assinatura descarregados da release pública passaram na verificação da chave de confiança. O anúncio automático no Discord correu sem erros. A publicação não instalou a beta nos clientes.

O changelog assinala como incompatíveis com perfis personalizados a remoção dos aliases de fonte `xvm`/`XVMSymbol` e do macro `{{xvm-stat}}`; os perfis devem usar `dkm` e `{{stat-available}}`.

## Validação no jogo de 2026-10-30

O utilizador testou no cliente NA `2.4.1.1 #987` a build de desenvolvimento posterior à stable 0.1.4 (commits `682580f` a `91cf708`) e confirmou funcionamento em:

- fontes `dkm` nos marcadores, painéis de equipa e carrossel, depois da remoção dos aliases antigos;
- painéis de equipa e ecrã de carregamento com `{{stat-available}}`, nos perfis pessoais convertidos a partir do nome antigo (backup em `build/local-backups/`);
- cores dos nomes nativos no TAB Halloween segundo o rating configurado.

O utilizador indica comportamento igual nos clientes EU e ASIA da mesma versão; não foi registado um teste separado nesses clientes. A validação não abrange as restantes pendências abaixo.

### Build limpa de `a7eda3a` instalada no NA

A build debug `0.1.5-beta.1` de `a7eda3a` (imports ordenados, builds reproduzíveis e helpers C# compilados com Roslyn `/deterministic`) foi instalada no NA com backup em `build/local-backups/wotmod-20261030T021346/`. O `game.log` regista três arranques com 35 componentes e 13 serviços ativos, `failures=[]`, sem tracebacks nem avisos/erros do Driftkings.

- **Nevoeiro:** o helper compilado com Roslyn desligou e voltou a ligar o nevoeiro com reinício coordenado (`2.4.1.1:ok:off` e `2.4.1.1:ok:on`).
- **Halloween:** batalha completa com `mode=halloween`, TAB anexado e regresso ao hangar; o utilizador confirmou todas as verificações do [guia Halloween](halloween/README.md#in-game-acceptance).
- **Por confirmar:** o `UpdateInstaller.exe` (só corre quando houver uma versão mais recente para instalar) e o `WindowsFiles.exe` (não usado nesta sessão).

## Alterações e validação de 29 de outubro

- **Fontes:** OpenWG Common e o pacote Python `driftkings.fonts` foram retirados. As fontes são incorporadas/registadas nos dois SWF e carregadas por `@font-face` no Gameface; preservar `dkm`, `DriftkingsFont` e as fontes nativas; os aliases antigos foram retirados em 2026-10-30. OpenWG Gameface permanece como dependência separada, juntamente com ModsList.
- **Desempenho:** o utilizador confirmou fontes funcionais e ausência de lag observado no NA após a remoção do Common. Não existe comparação A/B válida que quantifique FPS ou prove a causa da quebra anterior. Não reintroduzir Common apenas para registar as fontes já incorporadas.
- **Marcadores e estatísticas:** defaults seguem o layout de referência sem XMQP; distância integrada desativada por defeito para manter o módulo independente «Distância ao alvo». A descoberta das vistas dos Player Panels continua ativa durante transições sem linhas. Preservar perfis pessoais; a configuração instalada pode diferir dos defaults.
- **Account Manager:** janela modal com área completa do cliente e centragem CSS, foco e captura de Esc; campo de palavra-passe guardada mascarado, revelação apenas a pedido e manutenção do valor ao guardar sem o alterar. Vistos desenhados em CSS sem depender de um glifo da fonte. O utilizador confirmou funcionamento no cliente NA `2.4.1.1 #987`.
- **Verificações desta correção:** build debug beta compilou 314 módulos Python 2.7; suites Gameface, sete testes de contas e validação dos contratos de build passaram. A build foi instalada no NA com backup do WOTMOD anterior. Não se afirma uma nova execução integral do CI nem publicação de release por essa instalação.

### Pendências e limites atuais

- O painel de configurações continua em construção; a validação do Account Manager não valida todas as páginas, previews, perfis e falhas de gravação.
- O modo Halloween foi aceite no jogo em 2026-10-30 (NA `2.4.1.1 #987`): TAB, painel, carregamento, log e restantes modos; ver o [guia Halloween](halloween/README.md#in-game-acceptance).
- Os helpers `UpdateInstaller.exe` e `WindowsFiles.exe`, agora compilados com Roslyn, ainda não foram exercitados no jogo.
- Medições comparáveis de FPS/CPU/memória e a matriz completa de modos/replay/estados dos marcadores continuam por realizar; não atribuir ganhos quantitativos sem medição.
- Os riscos históricos de aplicação/gravação parcial, normalização externa e invalidação de estatísticas permanecem na [auditoria final](AUDITORIA_FINAL_INTEGRACAO.md). Essa auditoria é datada: a frase final «sem commit nem push» descreve o momento da auditoria, anterior à integração `202f476`.

## Organização dos testes

A reorganização local preservou os 560 métodos Python originais e as 14 suites JavaScript. Os testes de runtime estão em `tests/runtime/{core,settings,battle,lobby,integration}`, os do frontend em `tests/frontend/{settings,battle,lobby}` e os das ferramentas em `tests/build`. Os auxiliares partilhados foram retirados dos ficheiros `test_*` para `tests/support`; os dados sintéticos ficam em `tests/fixtures`.

Foram acrescentados casos de persistência, revelação de palavra-passe, edição ativa, encerramento e callbacks do Account Manager, além da equivalência da pesquisa recursiva `tdv` com o contrato anterior. O teste DOM das contas usa agora o mesmo nó simulado do painel, incluindo substituição de filhos por `textContent`, e verifica modelos tardios e edições sucessivas. A suite opcional `tests/artifacts` verifica os nomes das fontes e o glifo de rating nos SWF do WOTMOD realmente compilado.

Validação local final: **542 testes runtime em Python 2.7**, **580 testes runtime/build em Python 3**, **14 suites frontend** e **3 testes opcionais sobre o WOTMOD compilado**, todos sem falhas. São 23 métodos Python novos, incluindo os três de artefactos e as verificações das utilidades reutilizadas, além dos 560 preservados. Passaram também ESLint, defaults, catálogo UI, traduções e contratos de build. As mensagens de erro provocadas pelos testes negativos são esperadas e não representam falhas da execução.

Comandos e limites de validação: [CONTRIBUTING — Testing](../CONTRIBUTING.md#testing). O CI foi atualizado para os novos executores. Esta reorganização integra a preparação da stable 0.1.4; consultar o Git e os checks do commit publicado para o estado do envio e do CI. Não altera funcionalidades do mod nem instala uma nova build.

## Reutilização e limpeza de utilidades

`hexToDecimal` é partilhado pela borda da arena e pelas cores dos veículos no registo de serviço. `create_range` resolve os enums opcionais de Grande Calibre e estatísticas de batalha; os acessos de artilharia e informações do alvo reutilizam `getPlayer`/`getEntity`. Os contratos específicos de HSL, cores de oito dígitos, macros com funções, replay e callbacks geridos foram preservados.

De `common/utils/game.py` foram removidos `BigWorld_callback`, `refreshCurrentVehicle`, `Sound` e `VKEY_ALT`/`VKEY_CONTROL`/`VKEY_SHIFT`, sem consumidores no projeto; `checkKeys` permanece em uso. Foram retirados também 54 imports sobrantes dos testes após a reorganização. Esta limpeza não altera configurações ou perfis instalados e não implica instalação no jogo.

## Constantes partilhadas e duplicações

A revisão do runtime Python, ferramentas, frontend e Flash identificou contratos repetidos entre validação e apresentação. Foram centralizados em `_constants.py` os modos/ratings/visibilidade dos Player Panels, campos e opções comuns do minimapa, switches/opacidade/filtros/limites das células do carrossel, ratings dos marcadores, campos esperados de WN8 e numerais romanos. Os aliases públicos existentes mantêm os seus valores, incluindo o limite XI do macro romano dos Player Panels e XII das informações do alvo; não se uniformizaram esses intervalos distintos. A comparação com o inventário anterior confirmou todos os valores públicos de `_constants.py`.

`game_constants.py` reexporta os objetos nativos partilhados `CTRL_MODE_NAME`, `GUN_MARKER_TYPE` e `ARENA_PERIOD`, sem copiar valores WG para `_constants.py`. As funções numéricas idênticas de WNX e rating dos marcadores reutilizam `common/utils/numbers.nonnegative_number`, preservando os nomes `number` e `numeric`. Booleanos, negativos e não finitos continuam indisponíveis; `finite_number` conserva o seu contrato anterior.

Os testes completos, as 14 suites frontend, os defaults e o catálogo UI passaram. Repetições com significado diferente, algoritmos de paleta distintos, regras de segurança de caminhos, recursos gerados e espelhos Python/JS/AS3 dos contratos não foram unidos por semelhança textual. Os grupos WG usados por uma única implementação permanecem locais. A revisão não acrescenta dependências nem muda configurações instaladas; estas alterações foram compiladas na stable 0.1.4; a validação funcional completa no cliente continua pendente.

## Build e instalação local

Os comandos e requisitos estão em [CONTRIBUTING — Local build and client installation](../CONTRIBUTING.md#local-build-and-client-installation). O cliente local é `D:/Games/World_of_Tanks_NA`, definido em `build_data/toolchain.local.json` (`game_root`, fora do Git). A build aceita clientes EU, NA ou ASIA da versão do contrato; confirmar `version.xml` antes de instalar. O log é `<game-root>/game.log`.

As instalações recentes guardaram backups em `build/local-backups/`, fora dos pacotes e do Git. Os ficheiros gerados pelo Common foram movidos para backup, não apagados definitivamente. Preservar as configurações pessoais em `<game-root>/mods/configs/driftkings` e não divulgar contas, palavras-passe, tokens ou logs completos sem ocultar os dados pessoais.

## Limpeza do projeto

Foram retirados 14 relatórios e planos antigos de revisão, correção e publicação, substituídos pelos guias atuais e pela auditoria final. O conteúdo original continua recuperável no histórico Git. Foram também retirados bytecodes, caches, saídas de build regeneráveis e o replay de teste local de WoT 2.4.1.0. Ao todo, 1 704 ficheiros (incluindo 1 582 bytecodes), cerca de 72,9 MiB, foram movidos para `../Driftkings_SettingsLab_cleanup_20261028/`, com manifesto para recuperação. Uma pasta vazia adicional foi retirada. A revisão automática bloqueou a eliminação em lote; foi usada esta alternativa reversível.

Os testes versionados continuam a visar módulos existentes e são usados pelo CI; foram mantidos. As dependências locais, preferências do editor, fontes, configurações, chave de assinatura e backups de perfis foram preservados. Esta limpeza não executa testes nem compila ou instala o mod.

## Verificação histórica da preparação da beta 0.1.4-beta.2

Registo da preparação de 28 de outubro; os números abaixo não representam uma nova execução sobre todos os commits posteriores. Metadados e changelog preparados em `build_data/release.json`, com `VERSION` e downloads alinhados. Antes da compilação passaram 449 testes Core e 27 testes do painel em Python 2.7 e Python 3, 36 testes do instalador em Python 3, suites JavaScript, ESLint, traduções, defaults, catálogo UI e contratos de build. Foram atualizadas apenas as dependências simuladas de três fixtures que ainda representavam os contratos anteriores do carrossel, eventos WG e constantes das secções. O aviso de painel em construção permanece.

## Stable 0.1.4 publicada — 30 de outubro

A [release v0.1.4](https://github.com/dkruben/Driftkings_SettingsLab/releases/tag/v0.1.4) está pública e marcada como latest stable. Integra a `develop` em `main`, mantendo o aviso de painel em construção. O tag aponta para `0ee483d351cbc6fb6043224bfd974522f3ce9d53`; o [CI desse commit](https://github.com/dkruben/Driftkings_SettingsLab/actions/runs/40978795023) passou em todas as etapas.

A build release compilou 314 módulos Python 2.7 e gerou os SWF e helpers nativos. O instalador foi compilado e o manifesto assinado com a chave existente. Foram publicados 11 assets; nomes, tamanhos e SHA-256 foram comparados com o inventário local. O manifesto e a assinatura descarregados da release passaram na verificação da chave pública de confiança. Os três testes opcionais sobre o WOTMOD compilado passaram. A publicação não instalou a stable nos clientes EU/NA.

O CI anterior da `develop` expôs uma corrida no teste de encerramento de analytics. O teste passou a aguardar a thread de teste antes de contar novos envios após desativação; o código de analytics não foi alterado. A correção integra o commit da release. Commits posteriores de documentação não mudam o tag nem os assets publicados. Antes de outra publicação, atribuir uma nova versão e alinhar versão runtime, canal, changelog e links.
