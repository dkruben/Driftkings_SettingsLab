# Estado do projeto e da documentação

Atualizado em 30 de outubro de 2026. Os caminhos e comandos partem da raiz do repositório.

## Como retomar o trabalho

1. Ler este documento para conhecer o estado e as pendências; depois [CONTRIBUTING](../CONTRIBUTING.md) para arquitetura, contratos, verificações e build, e [Development References](DEVELOPMENT_REFERENCE.md) para as fontes externas.
2. Executar `git status --short`, `git branch --show-current` e `git log -5 --oneline`. Confirmar alterações locais antes de editar; este documento é um retrato datado, não substitui o Git.
3. Consultar `build_data/release.json` para versão/canal/changelog e `build_data/build_config.json` para cliente, referência, dependências e empacotamento. Abrir o guia da funcionalidade afetada através do índice abaixo.
4. Distinguir alteração de código, build local, instalação no jogo e publicação no GitHub. Uma dessas operações não implica as restantes; seguir o âmbito do pedido atual.

## Referência atual

- Branch de desenvolvimento: `develop`; `main` é a branch stable.
- Versão de desenvolvimento: `0.1.4-beta.2`. O código posterior ao tag não atualiza automaticamente os assets publicados; não reconstruir nem mover tags existentes para incluir novas alterações.
- Último commit funcional registado nesta revisão: `88930b6` (Account Manager), enviado para `develop`. O commit anterior `4d40588` removeu OpenWG Common.
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
| Preferências do lobby | [Guia](hangar_preferences/README.md) |
| Fontes e caracteres | [Fontes](FONTES.md) |
| Traduções | [Guia i18n](i18n/README.md) |
| Áudio e Sexto Sentido | [Bancos](audioww/README.md) e [ícones](sixthsense_icons/README.md) |
| Referências locais de desenvolvimento | [Development References](DEVELOPMENT_REFERENCE.md); [guia português histórico](FONTES_DESENVOLVIMENTO.md) |
| Otimização e pendências | [Auditoria final](AUDITORIA_FINAL_INTEGRACAO.md) |

Os adaptadores atuais usam `gameface/battle`, `gameface/lobby`, `flash/battle` e `flash/lobby`; os contratos ativos estão em `interface_catalog.py`. Os planos de migração concluídos e os estudos antigos foram retirados de `docs`. Os dados locais dos estudos foram preservados em `../Driftkings_SettingsLab_docs_backup_20261028/`; os relatórios versionados continuam recuperáveis no histórico Git. As pendências da otimização permanecem na auditoria final.

## Comportamentos e limites a preservar

- Configurações de cor usam `#RRGGBB`; as APIs nativas recebem números através dos conversores existentes.
- Preservar fontes, Unicode, aliases de fontes e identificadores externos necessários à compatibilidade.
- Marcadores distinguem equipa, estado vivo/destruído e modo normal/ALT. O editor inclui modelos partilhados e secção de rating.
- A preview do carrossel usa dois veículos fictícios; deve representar a geometria nativa horizontal e aplicar as mesmas regras de campos, macros e cores do renderer.
- O carrossel dispõe de um ícone para zero marcas. Um perfil que oculte o campo através da opacidade pode continuar a escondê-lo.
- O dano efetuado e o esperado têm macros de cor independentes; o separador pode ter a sua própria cor.
- Apply também persiste valores, conforme o contrato atual do painel. Os riscos de aplicação parcial, gravação de segredos e invalidação de estatísticas estão na auditoria final.
- As correções históricas do replay retiraram acessos TextField não suportados do relógio, declararam fontes nativas dos cartões e rejeitaram curvas de calibração planas/invertidas.

## Alterações e validação de 29 de outubro

- **Fontes:** OpenWG Common e o pacote Python `driftkings.fonts` foram retirados. As fontes são incorporadas/registadas nos dois SWF e carregadas por `@font-face` no Gameface; preservar `dkm`, aliases existentes e fontes nativas. OpenWG Gameface permanece como dependência separada, juntamente com ModsList.
- **Desempenho:** o utilizador confirmou fontes funcionais e ausência de lag observado no NA após a remoção do Common. Não existe comparação A/B válida que quantifique FPS ou prove a causa da quebra anterior. Não reintroduzir Common apenas para registar as fontes já incorporadas.
- **Marcadores e estatísticas:** defaults seguem o layout de referência sem XMQP; distância integrada desativada por defeito para manter o módulo independente «Distância ao alvo». A descoberta das vistas dos Player Panels continua ativa durante transições sem linhas. Preservar perfis pessoais; a configuração instalada pode diferir dos defaults.
- **Account Manager:** janela modal com área completa do cliente e centragem CSS, foco e captura de Esc; campo de palavra-passe guardada mascarado, revelação apenas a pedido e manutenção do valor ao guardar sem o alterar. Vistos desenhados em CSS sem depender de um glifo da fonte. O utilizador confirmou funcionamento no cliente NA `2.4.1.1 #987`.
- **Verificações desta correção:** build debug beta compilou 314 módulos Python 2.7; suites Gameface, sete testes de contas e validação dos contratos de build passaram. A build foi instalada no NA com backup do WOTMOD anterior. Não se afirma uma nova execução integral do CI nem publicação de release por essa instalação.

### Pendências e limites atuais

- O painel de configurações continua em construção; a validação do Account Manager não valida todas as páginas, previews, perfis e falhas de gravação.
- A aceitação visual das cores dos nomes no TAB Halloween continua indicada como pendente no changelog. Não a considerar concluída com base nos testes portáveis.
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

Os testes completos, as 14 suites frontend, os defaults e o catálogo UI passaram. Repetições com significado diferente, algoritmos de paleta distintos, regras de segurança de caminhos, recursos gerados e espelhos Python/JS/AS3 dos contratos não foram unidos por semelhança textual. Os grupos WG usados por uma única implementação permanecem locais. A revisão não acrescenta dependências nem muda configurações instaladas; estas alterações ainda não foram compiladas/validadas no cliente.

## Build e instalação local

Os comandos e requisitos estão em [CONTRIBUTING — Local build and client installation](../CONTRIBUTING.md#local-build-and-client-installation). O cliente configurado é `D:/Games/World_of_Tanks_NA`; confirmar o contrato e `version.xml` antes de instalar. O log é `<game-root>/game.log`.

As instalações recentes guardaram backups em `build/local-backups/`, fora dos pacotes e do Git. Os ficheiros gerados pelo Common foram movidos para backup, não apagados definitivamente. Preservar as configurações pessoais em `<game-root>/mods/configs/driftkings` e não divulgar contas, palavras-passe, tokens ou logs completos sem ocultar os dados pessoais.

## Limpeza do projeto

Foram retirados 14 relatórios e planos antigos de revisão, correção e publicação, substituídos pelos guias atuais e pela auditoria final. O conteúdo original continua recuperável no histórico Git. Foram também retirados bytecodes, caches, saídas de build regeneráveis e o replay de teste local de WoT 2.4.1.0. Ao todo, 1 704 ficheiros (incluindo 1 582 bytecodes), cerca de 72,9 MiB, foram movidos para `../Driftkings_SettingsLab_cleanup_20261028/`, com manifesto para recuperação. Uma pasta vazia adicional foi retirada. A revisão automática bloqueou a eliminação em lote; foi usada esta alternativa reversível.

Os testes versionados continuam a visar módulos existentes e são usados pelo CI; foram mantidos. As dependências locais, preferências do editor, fontes, configurações, chave de assinatura e backups de perfis foram preservados. Esta limpeza não executa testes nem compila ou instala o mod.

## Verificação histórica da preparação da beta 0.1.4-beta.2

Registo da preparação de 28 de outubro; os números abaixo não representam uma nova execução sobre todos os commits posteriores. Metadados e changelog preparados em `build_data/release.json`, com `VERSION` e downloads alinhados. Antes da compilação passaram 449 testes Core e 27 testes do painel em Python 2.7 e Python 3, 36 testes do instalador em Python 3, suites JavaScript, ESLint, traduções, defaults, catálogo UI e contratos de build. Foram atualizadas apenas as dependências simuladas de três fixtures que ainda representavam os contratos anteriores do carrossel, eventos WG e constantes das secções. O aviso de painel em construção permanece.
