# Estado do projeto e da documentação

Atualizado em 2026-11-09. Os caminhos e comandos partem da raiz do repositório.

## Fase 3D.3 — apto para commit local, memória em observação — 2026-11-09

**APTO PARA COMMIT LOCAL**, sem staging/commit autorizado nesta execução. Nova execução: 864 testes Python 3, 675 Python 2.7, 25 suites frontend, cinco testes de artefactos, lint e validadores PASS, todos com exit code 0. Snapshot `2bf769feb61120aa1ae64e2e7a0842cafe63061cbb6a6d29639049b8d3326ea6` liga comandos/logs aos hashes atuais de origem e testes; hashes antes/depois dos testes idênticos. Evidência local ignorada em `build/diagnostics/phase3d3/20261109T131245Z/`; apenas os três documentos da Fase 3D foram posteriormente atualizados. 20 caminhos previstos, staging vazio, branch/HEAD e worktrees preservados; build/backup com hashes autorizados.

A investigação 3D.1 encontrou três sessões posteriores com arenas vazias: A com tooltips de Natal (identificação do utilizador); B com tentativa incompleta por falta de jogadores, sem batalha efetiva ou três ciclos adicionais; C com interações da tripulação, sem prova no log de todos os passos/restauração das opções. Uma ocorrência original de `Memory arena contains allocations. Lobby = true, Battle = false`, sem objetos/tamanhos/owners identificados; sem associação causal demonstrada à progressão e sem prova de ausência absoluta de fugas. **Risco residual EM OBSERVAÇÃO, causa não determinada.** Os oito cenários funcionais anteriores continuam PASS por confirmação separada do utilizador. A enumeração da sessão original foi corrigida para **oito grupos de registo**, com o último confirmado nas linhas 5494–5496 do excerto preservado.

Import rejeitado/promises retidas pelo loader continuam limitação conhecida; telemetria individual JS é insuficiente, cenário B complementar permanece pendente e profiling completo não foi realizado. Não são regressões automaticamente demonstradas nem bloqueios concretos identificados. Sem código/testes/catálogo/packaging alterados, build, instalação, arranque do CT, rollback, commit/push ou Fase 3E. [Rastreabilidade, resultados, cenários e riscos](NATIVE_CREW_PROGRESSION_POC.md#fase-3d3--rastreabilidade-e-encerramento-documental--2026-11-09). Secções seguintes são checkpoints históricos.

## Fase 3D — funcionalmente validada, auditoria técnica pendente — 2026-11-09

O autor confirmou os oito cenários funcionais, incluindo tooltips/XP/batalhas, veículos, opções, CrewDetails/carrossel, relógio/hidePrestige/marcas, três ciclos e launcher. Sessão Fase 3D identificada em game.log: 11:59:17–12:28:14, serviços active, failures=[] e disabled={}, oito grupos de registos backend (contagem corrigida na Fase 3D.3) dos três plugins. Sem diagnósticos de falha do bridge identificados; telemetria JS individual de init/destroy ausente. No encerramento surgiu ERROR Scaleform “Memory arena contains allocations. Lobby = true, Battle = false”, sem owner no relatório e sem atribuição causal à progressão. Por isso: **FASE 3D FUNCIONALMENTE VALIDADA — AUDITORIA TÉCNICA PENDENTE**. Testes repetidos: 864 Python 3, 675 Python 2.7, 25 suites frontend, cinco artefactos e validadores PASS; hash local/instalado e backup íntegros. Apenas documentação alterada nesta auditoria, sem código, build, instalação, rollback, commit, push ou Fase 3E. [Evidências e pendência de teardown](NATIVE_CREW_PROGRESSION_POC.md#auditoria-final-de-logs-e-lifecycle--2026-11-09). Checkpoints abaixo são históricos.

## Fase 3D experimental implementada — validação CT pendente — 2026-11-09

Instalação controlada posteriormente autorizada e concluída às 11:55:42 UTC no CT #995 encerrado. Hash instalado `7c50836f5f53eaf97a8c3a63433cc71e6889089b4d50b8fd98770888477ad89c`; backup independente da Fase 3C verificado antes/depois. Comparação integral de 706 ficheiros confirma apenas driftkings.wotmod alterado, com OpenWG/ModsListAPI preservados. Três entrypoints presentes no pacote. Jogo não iniciado, sem código/build/commit/push novos. Validação funcional pelo autor continua pendente. [Relatório de instalação e backup](NATIVE_CREW_PROGRESSION_POC.md#instalação-controlada-autorizada--2026-11-09). O parágrafo seguinte regista o estado anterior à instalação.

**FASE 3D IMPLEMENTADA — VALIDAÇÃO CT PENDENTE.** Apenas CrewProgression passa a terceiro plugin nativo; getRow, evento sem payload e passagem JSON aos tooltips preservados. Controlador/registo partilhados com CrewDetails mantidos, sem alterar carrossel, patches, relógio ou marcas. Catálogo: duas janelas próprias, três nativos e 17 OpenWG; dependências mantidas. Testes: 864 Python 3, 675 runtime Python 2.7, 25 suites frontend e cinco artefactos; lint e validadores PASS. Build debug CT 0.1.8-beta.2 (fonte 0.1.8-beta.1), SHA-256 `7c50836f5f53eaf97a8c3a63433cc71e6889089b4d50b8fd98770888477ad89c`. Não instalada: o CT mantém a build validada da Fase 3C, preservada também em build/reference. Sem commit/push. [Contratos, testes, limites e rollback](NATIVE_CREW_PROGRESSION_POC.md). Checkpoints abaixo mantêm o estado histórico.

## Fase 3C encerrada e validada — 2026-11-09

**FASE 3C CONCLUÍDA E VALIDADA no CT #995, no âmbito confirmado pelo autor.** Confirmados coexistência relógio/marcas, hidePrestige, troca repetida de veículos, três ciclos sem duplicações e launcher; ativação/desativação já confirmada. Sessão 11:02:53–11:09:32 identificada após instalação, serviços active, failures=[] e disabled={}, três pares de registos nativos e nenhum erro novo relevante dos plugins identificado. Telemetria JS de init/destroy ausente; matriz visual de múltiplas escalas e memória não medida. Testes repetidos: 860 Python 3, 673 Python 2.7, 23 suites frontend, quatro artefactos e validadores PASS. Hash local/instalado e backup reconfirmados. Consolidação em commit local `feat(gameface): add native hangar marks plugin`, sem push. Sem nova build, instalação, correção de código ou Fase 3D. Dois nativos e 18 OpenWG; sem independência global. [Auditoria, classificação e limites](NATIVE_HANGAR_MARKS_POC.md#auditoria-final-e-encerramento--2026-11-09). Checkpoints abaixo são históricos.

## Fase 3C — funcionamento confirmado pelo autor no CT — 2026-11-09

O autor confirmou “Está a funcionar bem e sem problemas” após testar a build instalada da Fase 3C. Confirmou também que ativar/desativar as marcas funciona, retirando o relato inicial em contrário; nenhuma correção de código foi feita durante essa investigação. Hash instalado reconfirmado: `09b70a3b4a48194514393fa1f7cae1b7281a42434d1cbae9b78ce064cf4c9bec`. Confirmação funcional no âmbito relatado, sem atribuir testes individuais ou três ciclos não explicitados e sem nova análise de logs. Sem commit/push ou alterações de código. [Confirmação e limites](NATIVE_HANGAR_MARKS_POC.md#confirmação-funcional-do-autor--2026-11-09). Checkpoints abaixo são históricos.

## Fase 3C experimental implementada — validação CT pendente — 2026-11-09

Instalação controlada posteriormente autorizada e concluída às 11:02 UTC: apenas `driftkings.wotmod` substituído no CT encerrado, hash instalado `09b70a3b4a48194514393fa1f7cae1b7281a42434d1cbae9b78ce064cf4c9bec`. Backup Fase 3A verificado; inventário integral de 706 ficheiros confirma uma única alteração. Jogo não iniciado. Sem alterações de código, commit ou push. Validação funcional pelo autor continua pendente. [Relatório e backup](NATIVE_HANGAR_MARKS_POC.md#instalação-controlada-autorizada--2026-11-09). O parágrafo seguinte regista o estado anterior à instalação.

**FASE 3C IMPLEMENTADA — VALIDAÇÃO CT PENDENTE.** Apenas as marcas da garagem passam a plugin nativo independente; relógio original preservado. Catálogo: duas janelas próprias, dois nativos, 18 OpenWG. Testes: 860 Python 3, 673 runtime Python 2.7, 23 suites frontend e quatro de artefactos; lint e validadores aprovados. Fault injection é isolada, sem execução do loader real. Build debug CT 0.1.8-beta.2 (fonte 0.1.8-beta.1), SHA-256 `09b70a3b4a48194514393fa1f7cae1b7281a42434d1cbae9b78ce064cf4c9bec`. Não instalada; CT mantém a build validada da Fase 3A. Sem commit/push. [Arquitetura, evidências, limites e rollback](NATIVE_HANGAR_MARKS_POC.md). Registos abaixo permanecem históricos.

## Fase 3A encerrada e validada — 2026-11-09

**FASE 3A CONCLUÍDA E VALIDADA no CT #995.** O autor respondeu afirmativamente à checklist final de formatos/posição/escala/ativação, alternância de prestígio, três ciclos sem duplicação e regressões do launcher/restantes módulos. Testes finais já aprovados e código inalterado desde essa verificação. CT fechado, hash do PoC e backup confirmados; sessão adicional encerrada às 05:54:41 com serviços sem falhas e sem erros identificados do relógio/lifecycle, mantendo apenas os erros conhecidos de partículas. Ausência de telemetria JS explícita permanece documentada. [Encerramento e âmbito](NATIVE_CLOCK_POC.md#encerramento-após-respostas-à-checklist--2026-11-09). Commit local autorizado, sem push. OpenWG continua necessário para os outros 19 consumidores; sem Fase 3B. Pendências abaixo são históricas.

## Encerramento Fase 3A condicionado — 2026-11-09

**FASE 3A IMPLEMENTADA — VALIDAÇÃO PENDENTE.** Auditoria limitada ao relógio aprovada, testes finais repetidos (856 Python 3, 672 Python 2.7, 21 suites frontend e três de artefactos). Build instalada e backup confirmados por hash. Log após encerramento CT sem falhas identificadas do plugin, com três registos nativos; não comprova três ciclos completos nem telemetria de destroy. Checklist adicional enviada ao autor para formatos/escala, alternância repetida de prestígio, ciclos e regressões nesta build. Commit suspenso enquanto critérios essenciais permanecem pendentes; staging vazio, sem alterações de código nesta verificação. [Resultados e limites](NATIVE_CLOCK_POC.md#verificação-final-condicionada--2026-11-09). Sem Fase 3B.

## Relógio e hidePrestige confirmados pelo autor — 2026-11-09

O autor confirmou apresentação/atualização do relógio e ocultação/reposição do prestígio no PoC instalado. A confirmação complementa o log de registo do plugin nativo e a separação dos transportes no código. OpenWG permanece instalado para os outros 19 consumidores; não há declaração de runtime global sem OpenWG. Outros formatos, escalas, modos e descarte/transições continuam por confirmar individualmente. [Âmbito da confirmação](NATIVE_CLOCK_POC.md#confirmação-funcional-do-autor--2026-11-09). Sem commit/push ou Fase 3B.

## Primeira leitura do log Fase 3A — 2026-11-09

PoC inicia com serviços ativos, `failures=[]`, `disabled={}` e registo Python do plugin nativo confirmado às 05:44:36. Sem erros identificados do plugin no snapshot; erros de partículas conhecidos separados. A mensagem de arranque JS não aparece no log consultado, portanto a execução frontend e hidePrestige não estão confirmados apenas pelo log. CT ainda aberto; descarte e validação visual pendentes. [Evidência e limites](NATIVE_CLOCK_POC.md#primeira-leitura-do-log-do-poc--2026-11-09).

## PoC Fase 3A instalado para teste — 2026-11-09

Instalação do relógio nativo autorizada e concluída apenas no CT, hash `d08148935218a1fd9ee697e31f3e686928b4ac16bfc8e7d39a906b30d6eb3d14`, com backup verificado da Fase 2. Perfis e dependências preservados. CT não iniciado pelo agente; validação em jogo pendente. [Registo e recuperação](NATIVE_CLOCK_POC.md#instalação-autorizada-no-ct--2026-11-09). Os estados de não instalação abaixo são históricos.

## Fase 3A — PoC do relógio nativo — 2026-11-09

Gate aprovado por contratos CT: loader nativo de plugins da garagem com import de módulo, init/destroy e mapa UserMissionsPluginModel. PoC implementado apenas para o relógio; renderer/CSS/HTML e hidePrestige preservados, 19 consumidores continuam OpenWG. 856 testes Python 3, 672 runtime Python 2.7, 21 suites frontend e três testes de artefactos aprovados; build debug CT concluída. **Validação real pendente; não instalado, sem commit/push.** O CT mantém o pacote da Fase 2. Ver [evidências, riscos e rollback](NATIVE_CLOCK_POC.md). OpenWG e os dois pacotes da distribuição permanecem.

## Fase 2 encerrada — 2026-11-09

**Fase 2 — Validada funcionalmente no CT 2.4.2.0 sem ModsListAPI.** O autor confirmou botão/hover, abertura, X, Esc, atalho, regresso ao hangar e ausência de duplicações. A sessão sem ModsList já analisada confirma serviços ativos e ausência de falhas identificadas do launcher. Pacote ModsList restaurado e hash confirmado. OpenWG continua utilizado e ambos os pacotes permanecem no contrato de distribuição; futuras versões requerem revalidação. Ver [encerramento e evidências](NATIVE_FOOTER_LAUNCHER.md#encerramento-formal-da-fase-2--2026-11-09). As pendências nas secções seguintes são históricas. Commit local autorizado, sem push; Fase 3 apenas em investigação read-only.

## Fase 2.5 — arranque sem ModsList confirmado no log — 2026-11-09

Isolamento reversível concluído; sessão CT 04:52–04:53 carregou OpenWG e Driftkings sem ModsList, com serviços ativos, `failures=[]` e `disabled={}`, sem erros identificados do launcher. Confirmação manual dos controlos nesse cenário ainda pendente. ModsList restaurado após encerramento do CT, com hash confirmado e cópia de recuperação preservada. Erros de partículas e SVG sociais registados separadamente. Ver [registo detalhado](NATIVE_FOOTER_LAUNCHER.md#fase-25--sessão-sem-modslist-e-recuperação--2026-11-09). Sem alterações de código ou Fase 3.

## Launcher confirmado no CT pelo autor — 2026-11-09

O autor confirmou o funcionamento visual e funcional do launcher instalado. O log da sessão CT #995 regista serviços ativos, `failures=[]` e `disabled={}`, sem erros identificados do launcher ou tracebacks. Há erros de partículas BZ-75 e de SVG dos ícones YouTube/GitHub do painel, registados separadamente. Ambas as bibliotecas externas estavam presentes; os restantes cenários de coexistência e a matriz de modos/escalas não foram declarados como testados. Ver [evidência e âmbito](NATIVE_FOOTER_LAUNCHER.md#confirmação-do-autor-e-revisão-do-log--2026-11-09). As pendências abaixo descrevem checkpoints anteriores. Sem commit, push ou Fase 3.

## Instalação do launcher no CT — 2026-11-09

Instalação autorizada e concluída apenas no cliente CT, com backup verificado do pacote anterior e confirmação do SHA-256 instalado. Perfis e bibliotecas externas preservados. O cliente não foi iniciado e a validação visual continua pendente. Ver [registo de instalação e recuperação](NATIVE_FOOTER_LAUNCHER.md#instalação-autorizada--2026-11-09).

## Native Footer Launcher — Fase 2 — 2026-11-09

Implementação local na branch CT: botão próprio no footer através de filho Wulf e adaptador DOM localizado, reutilizando o OpenWG e bootstrap existentes. Registo ativo Driftkings na ModsList removido; atalho, janela, contextos e perfis preservados. Ambos os pacotes externos continuam na distribuição. **IMPLEMENTADO — VALIDAÇÃO EM JOGO PENDENTE.** Ver [contratos, testes e rollback](NATIVE_FOOTER_LAUNCHER.md). Sem instalação, commit, push ou início da Fase 3.

## Ponto de controlo antes da autonomia das dependências — 2026-11-09

O autor autorizou commit e push das alterações locais da barra de vida na branch CT antes de iniciar qualquer migração. A documentação deve acompanhar as alterações futuras. ModsListAPI e OpenWG Gameface continuam obrigatórios no pacote atual; o botão próprio e a ponte interna foram apenas analisados, sem implementação. A validação visual da barra integrada permanece pendente. Ver [guia da barra integrada](AMMO_HEALTH.md) e [compatibilidade CT](CT_COMPATIBILITY.md).

## Barra de vida no painel de munições — 2026-11-07

Implementação local no CT: três opções adicionais no estilo da vida do veículo (Painel de munições — Minimalista / Clássica WoT / Driftkings), preservando os cinco índices anteriores e o estilo guardado. A nova apresentação usa um componente Flash filho do painel nativo de consumíveis, largura `basePanelWidth`, moldura de 26 px e intervalo de 8 px. Valores de vida e cores reutilizam o tracker atual. O Gameface flutuante é ocultado nestes três estilos. Ver [guia da barra integrada](AMMO_HEALTH.md) para âmbito e validação. O teste visual em batalha está pendente; não confundir com a aprovação CT anterior. Versões mantidas, outras branches intactas.

## Aprovação local do CT — 2026-11-06

O autor aprovou em jogo a build local `0.1.8-beta.2`, com o painel aprovado em `6c4bed01` e as correções de nevoeiro e rotação do gráfico, autorizando commit e push da branch `feature/wot-2.4.2-ct`. O ciclo CT mantém o número do pacote e os metadados versionados sem incremento, conforme [registo CT](CT_COMPATIBILITY.md). As secções anteriores de preparação abaixo são históricas; não representam uma publicação CT ou promoção da produção.

## Adaptação Common Test — 2026-11-05

Trabalho local em `feature/wot-2.4.2-ct`, base `832d3263`, versão `0.1.8-beta.1`. Esta branch aponta para CT `2.4.2.0 #995` / SRC `2.4.2.5516`; as secções de produção abaixo são histórico da preparação anterior. Build CT compilada com patches Gameface específicos e bibliotecas/filme nativo CT; arranque permitido em CT e atualizador de produção desativado nesse realm. Ver [compatibilidade CT](CT_COMPATIBILITY.md) para comandos, verificações e testes em jogo pendentes. Sem instalação, commit, push ou publicação desta adaptação.

## Preparação da beta 0.1.7-beta.1 — 2026-11-05

A beta seguinte integra a microatualização, as cinco imagens otimizadas e a restrição do minimapa a aleatórias/Comp7. `build_data/release.json`, `VERSION` e o teste de arranque estão alinhados em `0.1.7-beta.1`/`beta`. O autor confirmou todos os testes da build local instalada no EU nesta conversa; não foi declarada uma nova validação NA/ASIA. Essa build debug não substitui a identificação e validação do pacote release para promoção a stable.

A stable publicada atual é `0.1.6` (confirmada no GitHub). As secções antigas abaixo sobre preparação da stable são históricas. A referência de compilação continua EU `2.4.1.5514`; CT será trabalho posterior. Verificações desta preparação: 834 testes Python 3 (runtime/build), 654 testes runtime Python 2.7 e 18 suites frontend aprovados; lint, imports, nomes, traduções, defaults, catálogo UI e contratos aprovados.

## Como retomar o trabalho

1. Ler este documento para conhecer o estado e as pendências; depois [CONTRIBUTING](../CONTRIBUTING.md) para arquitetura, contratos, verificações e build, e [Development References](DEVELOPMENT_REFERENCE.md) para as fontes externas.
2. Executar `git status --short`, `git branch --show-current` e `git log -5 --oneline`. Confirmar alterações locais antes de editar; este documento é um retrato datado, não substitui o Git.
3. Consultar `build_data/release.json` para versão/canal/changelog e `build_data/build_config.json` para cliente, referência, dependências e empacotamento. Abrir o guia da funcionalidade afetada através do índice abaixo.
4. Distinguir alteração de código, build local, instalação no jogo e publicação no GitHub. Uma dessas operações não implica as restantes; seguir o âmbito do pedido atual.

## Referência atual

- Branch de desenvolvimento: `develop`, com a beta `0.1.7-beta.1` em preparação; `main` mantém a stable publicada `0.1.6`.
- Versão stable publicada: `0.1.6` (latest). Beta publicada anterior: `0.1.6-beta.1`; os assets `0.1.7-beta.1` serão compilados do novo commit em `develop`. O código posterior a um tag não altera os assets já publicados.
- Base desta preparação: `4cf49575` em `develop`. As integrações anteriores mencionadas nas secções datadas são histórico, não o HEAD atual.
- Alvo do cliente: WoT `2.4.1.1`, Wargaming EU/NA/ASIA; contratos e ferramentas em `build_data/` e `build_tools/`.
- As versões publicadas e os downloads estão no [README](../README.md). O histórico de publicação permanece nas releases e no Git.
- A beta `0.1.6-beta.1` foi aprovada funcionalmente por Ruben Gameiro Lopes Gonçalves em 2026-11-05, com testes declarados de 2026-11-04 em EU, NA e ASIA. Os 18 bloqueantes estão PASS nas três regiões; 57 células PASS e 36 NOT TESTED no [registo oficial](releases/0.1.6-beta.1-validation.md). O painel e os perfis têm persistência confirmada; detalhes históricos sobre construção/aceitação visual do painel permanecem nas secções datadas abaixo. A aprovação funcional não é uma nova medição de desempenho.
- As seis fases de otimização foram revistas e enviadas no commit `202f476`. A auditoria estática não demonstra ganhos quantitativos de FPS; as medições em jogo de 2026-11-03 estão na secção correspondente.

## Restrição do minimapa por modo — 2026-11-05

O minimapa do mod passa a funcionar apenas em batalhas aleatórias (incluindo as variantes reconhecidas pelo cliente) e 7x7/Comp7. Nos restantes modos, incluindo eventos, Frontline, Stronghold e modos desconhecidos, ficam os plugins e a apresentação nativos. A restrição usa a política central de batalha tanto na substituição dos plugins como na ativação da apresentação Flash; não altera as preferências gravadas. Validação visual desta alteração em jogo pendente.

## Compatibilidade da microatualização — 2026-11-05

A referência de produção passou de EU `2.4.1.5504` para `2.4.1.5514` (cliente `2.4.1.1 #993`; NA instalado `#992`). Foram alinhados o contrato de build, os hashes de entrada/saída do patch do carrossel, o lock do SWF nativo dos marcadores e as oito bibliotecas SWC exportadas da referência EU. Os 23 pontos de inserção do carrossel e os métodos/campos usados pelo patch dos marcadores foram verificados; não foi necessário alterar a lógica dos patches. Os recursos dos quartéis e tooltips da tripulação mantêm os hashes anteriores.

As cinco imagens otimizadas pelo autor foram preservadas: ícones de contas a 128×128 (apresentação controlada por CSS), barras HP a 72×24 com transparência. Redução total aproximada de 4,62 MiB nos PNG de origem; sem alteração dos caminhos ou configurações.

Validação local: contratos Gameface aprovados nos clientes EU e NA, 180 testes de build aprovados e compilação debug completa com os novos recursos. A build de ensaio usa `0.1.7-beta.1` apenas no pacote, através de `--keep-source-version`; a versão/canal de release no repositório permanecem intactos. O autor confirmou o aspeto visual do mod anteriormente instalado após a atualização; essa confirmação não valida em jogo esta nova build. Sem instalação, assinatura, publicação, commit ou push. A referência CT não foi selecionada para compilação.

## Preparação local da stable 0.1.6 — 2026-11-05

`prepare` atualizou apenas a versão/canal em `build_data/release.json` e o literal `VERSION` para `0.1.6`/`stable`. Changelog, README, SECURITY, exemplo de reporte e expectativas de arranque foram preparados sem mudanças funcionais. Não há links de download para assets 0.1.6 inexistentes; stable 0.1.5 e beta 0.1.6-beta.1 continuam as versões publicadas.

A beta aprovada permanece no commit `22a19317a19b0969351ed1514ec63d3d7f4831f2`, com os registos e artefactos preservados. A stable terá de ser recompilada e assinada após PR, merge commit em `main`, CI verde e `promote_release.py check` aprovado; o hash da beta não é reutilizado como hash da stable. Commit/push, PR, merge, build, gate e publicação aguardam autorizações posteriores.

## Guias mantidos

| Área | Documento |
| --- | --- |
| Instalação, funcionalidades e downloads | [README](../README.md) |
| Desenvolvimento, verificações e publicação | [CONTRIBUTING](../CONTRIBUTING.md) |
| Validação e promoção de beta a stable | [Releases](releases/README.md) |
| Painel de configurações | [Relatório funcional](RELATORIO_PAINEL_CONFIGURACAO.md) |
| Marcadores dos veículos | [Guia dos marcadores](vehicle_markers/README.md) |
| Carrossel | [Guia do carrossel](vehicle_carousel/README.md) |
| Modo Halloween | [Halloween mode](halloween/README.md) |
| Preferências do lobby | [Guia](hangar_preferences/README.md) |
| Fontes e caracteres | [Fonts and characters](fonts/README.md) |
| Traduções | [Guia i18n](i18n/README.md) |
| Macros de todos os módulos | [Macro reference](macros/README.md) |
| Áudio e Sexto Sentido | [Bancos](audioww/README.md) e [ícones](sixthsense_icons/README.md) |
| Referências locais de desenvolvimento | [Development References](DEVELOPMENT_REFERENCE.md) |
| Otimização e pendências | [Auditoria final](AUDITORIA_FINAL_INTEGRACAO.md) |
| Exceções genéricas silenciosas | [Relatório](RELATORIO_EXCECOES.md) |
| Eventos falsos nas estatísticas anónimas | [Proposta](RELATORIO_ANALYTICS.md) |

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

## Promoção de beta a stable — 2026-11-04

A publicação passa a ter registo de validação, promoção rastreável e bloqueios para o que falhou na 0.1.6-beta.1: `publish_release.py --publish` recusa commits sem CI verde, duplicados do mesmo tag e versões stable. A stable sai de `build_tools/promote_release.py`, que exige um registo aprovado em `docs/releases/`, e o workflow `promotion-gate.yml` faz as verificações em modo de leitura. O processo está em [Releases](releases/README.md).

O registo da `0.1.6-beta.1` tem as linhas automáticas verificadas e as linhas em jogo por preencher, com a decisão `PENDING`; a beta ainda não pode ser promovida.

**Configuração do GitHub.** `promotion-gate.yml` está disponível em `main` e `develop`, e lança-se a partir de `main`. O ambiente `stable-release` está criado e protegido, com `dkruben` como revisor obrigatório, restrição a `main` e `can_admins_bypass` a `false`. Os três rulesets estão ativos e sem lista de bypass: `protect-release-tags` (`26562419`), `protect-develop` (`26562657`) e `protect-main` (`26563825`). `main` passa a receber alterações só por pull request, e a promoção exige merge commit.

**Validado.** O teste negativo do gate passou na [execução 41880158173](https://github.com/dkruben/Driftkings_SettingsLab/actions/runs/41880158173): `identity` rejeitou a combinação sintética, o título trouxe o digest, a aprovação não correu e não houve tags, releases nem notificações Discord. A primeira execução, sem aspas em `run-name`, tinha mostrado que o digest se perdia como comentário YAML; corrigido em `c7bbcc4`. Depois de uma edição do ambiente na interface ter removido a regra de revisores, a regra foi reposta pela API.

**Pendente.** A validação em jogo, a primeira aprovação real no ambiente, o primeiro PR para `main`, a primeira build por `promote_release.py` e a promoção da 0.1.6.

A auditoria final corrigiu seis problemas: um teste que ficaria vermelho ao aprovar o registo, caminhos locais no `build-report.json` publicado, aprovação sem ligação aos artefactos, dispensa da revisão sobre um ambiente protegido, pastas aceites sem instalador ou sem passar por `build`, e testes que não detetavam a remoção de bloqueios. As releases já publicadas mantêm os caminhos locais no `build-report.json`.

## Desempenho em batalha e beta 0.1.6-beta.1 — 2026-11-03

**Medição.** No cliente EU, com a CapFrameX (gravações de 20 s nos mesmos momentos de replays) e os diagnósticos do mod (`Debug` no painel e `team_panels.performance.diagnostics`), os mods custavam ~8,5% no FPS médio e ~16% no 1% low num replay da Linha da Frente. Retirar o `RemoveFog` ou o `res_mods` não mudou os números; retirar o `driftkings.wotmod` recuperou ~70% da perda no 1% low. Os diagnósticos apontaram as paragens da aplicação das estatísticas (até 200 ms), o `gun_traverse_limits` e o painel das equipas, que numa aleatória gastava ~5,4 ms por passagem em Flash, 10 vezes por segundo.

**Correções em `develop`:**

- `3a410b4`: as contas entregues aplicam-se no máximo 3 ms por frame (`applyDeferred`); a paragem máxima passou de ~200 ms para ~11 ms.
- `73104b9`: `OverlayScene.update` só envia ao Flash as propriedades alteradas (marcadores de ângulo, indicador do autoaim, informação do alvo).
- `4c10b66`: o relógio do ecrã de carregamento passou para o Flash (o payload deixava de ser igual a cada segundo); o tick Python do painel passou de 0,25 s a 1 s, com as estatísticas a avisar o painel no fim de cada lote. Medido: 5 ticks por 5 s em vez de 20, reenvios só com alterações.
- `4ab8855`: `rowlookup` indexa as linhas uma vez por payload em vez de ~2700 regex por passagem; o painel passou de ~5,4 ms a ~2,1 ms por passagem.
- `eea95cb` e `d1973a2`: `driftkingspanels.swf` (só código, 1,5 KB) define as classes de ligação do painel lateral clássico com os nomes nativos; as linhas avisam os redesenhos através de `panelhook`, ficam marcadas com o `vehicleID` e o painel só é percorrido com dados novos, alterações ou a verificação de 1 s. Medido: ~0,6–1,4 ms por passagem e ~6 vezes menos verificações. Ranked, Linha da Frente e Fort Rush reutilizam os mesmos nomes com outras bases, por isso a biblioteca só é acrescentada por batalha à página clássica (`BattleEntry._getRequiredLibraries`); validado num replay aleatório (classes carregadas, 30 linhas) e da Linha da Frente (não carregadas).

**Decisões.** O TAB (`FullStats`) fica com o método anterior: substituí-lo obrigava a copiar código privado da WG (`createItemHolder` e a configuração das abas de `FullStatsUI`) e só custa enquanto está aberto. O `ifc_addons` (polarfox) serviu de referência: os SWF só de código são legíveis; o Python (PjOrion) e o Gameface (JS encriptado) não foram contornados. Os scripts locais de teste de FPS ficam fora do repositório.

**Beta 0.1.6-beta.1.** Versão e canal em `driftkings/__init__.py`, `build_data/release.json`, README (badge, downloads e novidades), SECURITY.md, o exemplo do formulário de bug e o fixture de `test_core_startup.py`; o CONTRIBUTING descreve o `driftkingspanels.swf` e a regra da página clássica. O CI falhou no `b6f03f1` pela ordem de um import (isort), corrigida em `22a1931`. A build release foi refeita a partir da árvore limpa em `22a1931`, com o CI verde, instalador Inno Setup e os três testes sobre o WOTMOD, e o manifesto foi assinado com a chave existente. Os 11 assets do rascunho coincidiram em nome, tamanho e SHA-256 com a build local; o manifesto e a assinatura descarregados da release pública são iguais aos locais e os links de download do README respondem. A [release v0.1.6-beta.1](https://github.com/dkruben/Driftkings_SettingsLab/releases/tag/v0.1.6-beta.1) está publicada como prerelease; a stable 0.1.5 continua latest. Um rascunho anterior com o mesmo tag e alvo `b6f03f1` foi apagado sem ser publicado.

## Beta 0.1.5-beta.4 publicada e stable 0.1.5 em preparação — 2026-11-02

A build release da beta.4 foi feita a partir da árvore limpa em `080658e`, com o CI verde, instalador Inno Setup e os três testes opcionais sobre o WOTMOD. O manifesto foi assinado com a chave existente. Os 11 assets do rascunho coincidem em nome, tamanho e SHA-256 com a build local; o manifesto e a assinatura descarregados da release pública passaram na verificação da chave de confiança. A [release v0.1.5-beta.4](https://github.com/dkruben/Driftkings_SettingsLab/releases/tag/v0.1.5-beta.4) está publicada como prerelease; a stable 0.1.4 continua marcada como latest.

A stable `0.1.5` junta as quatro betas 0.1.5 com o mesmo código da beta.4: versão `0.1.5`, canal `stable`, changelog consolidado (incluindo as alterações incompatíveis das betas), README, SECURITY.md, o exemplo do formulário de bug e o fixture de `test_core_startup.py`. O rascunho foi verificado (11 assets iguais à build local em nome, tamanho e SHA-256, manifesto e assinatura descarregados válidos) e depois publicado como latest, com o tag `v0.1.5` no commit `550b800`, cujo CI passou. Os links de download do README para a 0.1.5 e para a beta.4 respondem.

## Preparação da beta 0.1.5-beta.4 — 2026-11-02

Na branch `release/0.1.5-beta.4`, a versão passou a `0.1.5-beta.4` em `driftkings/__init__.py`, `build_data/release.json`, README (badge, downloads e novidades), SECURITY.md, o exemplo do formulário de bug e o fixture de `test_core_startup.py`. O changelog resume as alterações desde o tag `v0.1.5-beta.3` (`d1dbfe3`): cartão do alvo com linhas separadas e modelo Clássico por omissão, siglas das munições nas 18 línguas, cabeçalho e botão GitHub do painel, correções do Sexto Sentido, do arrasto das marcas e dos pesos, avisos Gameface de CSS e fontes, e registos novos do updater e do gestor de contas. A release **ainda não foi compilada, assinada nem publicada**; os links de download do README apontam para o tag `v0.1.5-beta.4`, que ainda não existe. A stable 0.1.4 não muda.

**Frontline (2026-11-02):** o roster nunca aparecia no Frontline, apesar do suporte entrar na beta.3 sem validação no jogo. Um diagnóstico temporário (branch `debug/frontline-diagnostics`, não integrada) mostrou que as tabelas são símbolos da biblioteca com outros nomes em runtime, `FrontlineFullStatsTableUI` (TAB) e `FrontlineStatsTableUI` (carregamento), e que os padrões do mod exigiam os nomes das classes AS3 (`FrontlineFullStatsTable`, `FrontlineBattleStatsTable`). `viewbindings.as` passou a reconhecê-las pelas listas `team1PlayerList`/`team2PlayerList`. Validado pelo utilizador no cliente EU: carregamento com 36 linhas desenhadas e TAB com 20 a 40, sem rejeições nem erros. As colunas do Frontline são mais estreitas do que as do TAB clássico, por isso os nomes longos com estatísticas ficavam cortados: `extrafields.drawText` ganhou a opção `fit`, usada só pelo Frontline, que reduz o texto até 65% para caber, mantendo o alinhamento. Validado pelo utilizador no EU (TAB "A minha frente" e "Todas as frentes"), sem erros do Driftkings no log; o único aviso foi a API de estatísticas da Wargaming indisponível (504).

O utilizador testou uma build debug da `0.1.5-beta.4` no cliente EU `2.4.1.1 #989` e aprovou-a: um replay e o hangar. O `game.log` regista `Driftkings 0.1.5-beta.4 for World of Tanks 2.4.1.1`, `failures=[]`, o cartão do alvo carregado em Gameface e nenhum aviso, erro ou traceback do Driftkings nem avisos de CSS ou fontes do Gameface; os restantes avisos são do jogo. O utilizador confirmou no ecrã o cartão Clássico, as siglas das munições e o cabeçalho do painel.

## Cartão do alvo, cabeçalho do painel e validações — 2026-11-02

- **Cartão do alvo:** o Gameface descarta texto só com espaços entre etiquetas, por isso a quebra de linha entre as linhas do cartão perdia-se e o cartão aparecia numa só linha. `shared/flash_lines.js` converte as quebras em `<span data-dk-br>` antes de analisar o HTML nos textos ricos; o teste dos textos de ecrã passou a descartar esse texto como o Gameface.
- **Siglas das munições:** as 18 línguas tinham traduções automáticas das siglas como palavras comuns (HE como o pronome «ele», APCR como «TAEG», HEAT como «calor»). Todas usam agora AP, APCR, HE, HEAT e HESH.
- **Modelo Clássico:** o cartão antigo (imagem do veículo, recarga com equipamento e tabelas alinhadas de blindagem e munições) voltou como modelo 7, `classic`, agora o padrão, com legendas traduzidas (`card_type` e `card_damage` novos nas 18 línguas). Cópias guardadas do cartão português retirado passam para o Clássico; os IDs dos modelos existentes não mudam. A configuração do EU foi mudada para o modelo 7, com cópia de segurança. O utilizador validou o cartão Clássico no cliente EU.
- **Painel:** cabeçalho de 80rem com a imagem `header_tank.jpeg` (2800×160), ícones sociais brancos e botão GitHub que abre o repositório (`REPOSITORY` do updater).
- **Validações confirmadas pelo utilizador:** Halloween, gestor de contas, cartão das marcas no hangar, tooltip das marcas, macro do carrossel `{{v.c:…}}`, textos da mira em Gameface e macros `{nome}`, aceitação visual do painel e os helpers `UpdateInstaller.exe`/`WindowsFiles.exe`.
- **Verificações:** 608 testes Python, 18 suites frontend e validação dos contratos de build sem falhas. Commits `20af06d`, `6192862` e `b25b9e0` enviados para `develop`; não há nova release.

## CSS Gameface sem declarações rejeitadas — 2026-11-01

O `game.log` do EU mostrava 256 avisos `alignItems ... baseline` de `shared/flash_lines.js` (células com `<tab>` da Informação do alvo) e avisos de CSS ao abrir hangar, painel, árvore e batalha. O Gameface ignora `align-items: baseline`, `display: inline-block`/`inline-flex`, bordas `dashed` e os seletores `:empty`/`:disabled`. Passaram a `flex-end`, `flex` e `solid`; os elementos vazios do painel (dependência da opção, changelog e nota das atualizações, título de diálogo) escondem-se via `DK.show` e os botões +/− desativados usam a classe `is-disabled`. Validado no cliente EU com a build debug: hangar, painel de configurações, árvore tecnológica e replay sem avisos de CSS do mod. Os restantes avisos (`hangar_camera_manager` ao sair do hangar de Halloween, `NaN%` na barra da árvore) são do jogo.

## Beta 0.1.5-beta.3 publicada — 2026-11-01

O utilizador testou a build debug no cliente EU `2.4.1.1 #989` e aprovou-a. A [release v0.1.5-beta.3](https://github.com/dkruben/Driftkings_SettingsLab/releases/tag/v0.1.5-beta.3) está publicada como prerelease; a stable 0.1.4 continua marcada como latest. `develop` e `main` avançaram em fast-forward para `d1dbfe3`, onde está o tag; o CI desse commit passou antes do upload.

A build release foi feita a partir da árvore limpa (304 módulos Python 2.7, SWF e helpers), com instalador Inno Setup e os três testes opcionais sobre o WOTMOD. O manifesto foi assinado com a chave existente. Os 11 assets publicados coincidem em nome, tamanho e SHA-256 com a build local; o manifesto e a assinatura descarregados da release pública passaram na verificação da chave de confiança. O anúncio automático no Discord correu sem erros. O changelog assinala como incompatível com perfis personalizados a remoção de `{{v.c_…}}` no carrossel.

## Gestor de contas com página própria no painel — 2026-11-01

O Account Manager deixou de ler a opção `accountManager.enabled` das Opções do hangar e passou a ter a sua secção `account_manager` (`settings/definitions/components/account_manager.py`, categoria Geral) e o ficheiro `default/account_manager.json`. O interruptor do cabeçalho liga ou desliga o botão do gestor no ecrã de login (momento de aplicação imediato). A página tem um botão "Gerir contas" que abre a janela atual do gestor no hangar (`AccountsManagerController.openManager`), onde se adicionam, editam e apagam contas; "Entrar" fica desativado fora do ecrã de login. Título e textos novos nas 18 línguas. Os perfis antigos mantêm `accountManager` em `hangar_preferences.json` sem efeito; quem o tinha desativado à mão volta a ter o gestor ativo. Validado pelo utilizador no cliente EU (confirmado em 2026-11-02).

## Revisão de `common/utils` — 2026-11-01

Reutilização onde o comportamento é idêntico: `SettingsStore.write` e o armazenamento do painel usam `atomicWrite`; `core/crew_progression` usa `nonnegative_number`; `core/diagnostics` e `core/carousel.bounded` usam `finite_number`; `core/keycodes`, `core/panel_macros`, `core/minimap` e `stats/vehinfo` usam `compat` em vez de definirem `text_type`/`integer_types`. Retirados por não terem uso: o alias `recoverFile` (os quatro chamadores usam `recover_file`) e as tabelas `noob_meter_colors`, `driftkings_colors`, `wot_life_colors`, `vehicle_type_colors` e `total_hp_colors` de `color_rating_data` (o teste de tabelas partilhadas passou a ler `color_tables`). `getPlayer()`, `getTarget()` e `getEntity()` de `wgutils`, que só devolviam `BigWorld.player()`, `BigWorld.target()` e `BigWorld.entity()`, também saíram: os módulos que os usavam chamam o `BigWorld` diretamente e os testes fazem stub do `BigWorld`.

Ficaram de fora de propósito: `core/updater/*` e `core/locale_catalog.py`, que as ferramentas de build carregam isoladamente e não podem importar `driftkings.common`; e as verificações `isnan`/`isinf` que validam e rejeitam valores, que não equivalem a `finite_number`.

## Leituras de dossiers centralizadas — 2026-11-01

`common/utils/achievement_dossiers.py` passou a `common/utils/dossiers.py` e reúne as leituras repetidas dos dossiers dos veículos: `total_record` (bloco TOTAL: `marksOnGun`, `movingAvgDamage`…), `damage_rating` (percentagem de marca), `mastery_achievement`/`mastery_rank` (mestria 0–4, sem confundir `NO_LVL` com Ás), `average_assists` (rastos, rádio e atordoamento por batalha) e `wnx_assistance`. As marcas no hangar, em batalha e na árvore tecnológica e o carrossel usam estas funções; os valores calculados não mudam. Os testes de módulos executados com `game_source` recebem os helpers reais através de `support.dossiers()`.

A tooltip das marcas no registo de serviço (`MarkOnGunAchievement.getUserCondition`) era substituída pelos dois módulos de marcas, e o que ganhava dependia da ordem de arranque. Ficou só a do hangar (mais completa: mestria, WN8, vitórias e alvos opcionais). Saíram das marcas em batalha o override, a opção `showInStatistic`, o seu controlo e as traduções `UI_setting_showInStatistic_*` e `UI_tooltips`; a opção do hangar controla a tooltip. Perfis antigos mantêm a chave sem efeito. Validado pelo utilizador no cliente EU (confirmado em 2026-11-02).

## Textos da mira com macros `{nome}` — 2026-11-01

A contagem de pontaria, o tempo de voo e o indicador de penetração usam agora campos de formatação Python: `{timer:.1f}`, `{percent:d}`, `{color}`, `{countedArmor:d}`, etc. (`fill_template` em `gameface/battle/reticle_texts.py`). `:d` trunca decimais como o antigo `%d`; um nome desconhecido mostra `macros not found`. Os templates antigos com `%(nome)s` continuam a ser lidos quando contêm `%(`. Defaults, dicas das 18 línguas, testes e o [guia das macros](macros/README.md) usam a forma nova. Os perfis instalados no EU e no NA foram convertidos, com backup em `build/local-backups/reticle-braces-*`. Validado pelo utilizador no cliente EU com a build da beta.3 (confirmado em 2026-11-02).

## Macro de cor `{{v.c_…}}` retirada do carrossel — 2026-11-01

O carrossel deixou de aceitar a forma antiga `{{v.c_métrica}}` (e `{{v.c_type}}`); a única sintaxe de cor é `{{c:métrica}}`/`{{v.c:métrica}}`, que devolve `#RRGGBB`. Uma macro antiga passa a ser lida como campo desconhecido e mostra `--`. Os defaults, a pré-visualização, os testes e os guias usam `{{v.c:…}}`. Foram também retirados de `Statistics.applyPlayer()` os campos `c_wn8`, `c_battles`, `c_winrate` e `c_tBattles`, que nenhum renderizador lia; `Statistics.getColor()` mantém-se como API pública, mas não controla as cores apresentadas (os painéis e marcadores usam `getStatisticColor`). Alteração incompatível com perfis personalizados, assinalada no changelog da beta.3. Os perfis instalados nos clientes EU e NA (`default/vehicle_carousel/`) já usam `{{v.c:…}}`. Validado pelo utilizador no cliente EU (confirmado em 2026-11-02).

## Eficiência e força das equipas migradas para Gameface — 2026-10-31

O texto de eficiência em batalha (`battle_performance`: WN8, WNX, EFF, XTE, DIFF) e o da força das equipas (`battle_statistics`) deixaram o overlay Flash (`CachedBattleLabel` em `flash/battle/`) e passaram a duas vistas Gameface filhas da HUD nativa, com o renderizador partilhado `shared/screen_text.js`/`.css` e os adaptadores em `gameface/battle/screen_texts.py`. Os cálculos continuam nos componentes. A conversão dos templates Flash foi extraída para `shared/flash_lines.js`, também usado pelos textos da mira; nos textos de ecrã aplica ainda `face` e `alpha` de `<font>`.

As definições mantêm-se: a posição (`position` e `textPosition`) tem a mesma semântica do overlay (`x`/`y` em unidades da interface a partir do canto `alignX`/`alignY`, por omissão esquerda/topo), por isso os valores guardados passam sem conversão. `textStyle`/`textFormat` dão a fonte base (`$TitleFont` → Warhelios Bold, `$FieldFont` → Warhelios Regular, outras faces só se carregadas), o tamanho, a cor, o negrito/itálico e o alinhamento; `textShadow` vira `text-shadow` com a mesma normalização de `alpha`/`strength` do overlay; `textPosition.alpha` dá a opacidade. `textLock` continua a bloquear o arrasto com Ctrl e passou a ter controlo no painel das estatísticas. O arrasto grava a posição ancorada ao canto mais próximo. A posição por omissão da força das equipas passou de x −58/y 2 para x −3/y 32 (topo à direita), porque a etiqueta nativa "Mapa Com Eventos Aleatórios" a tapava; perfis já guardados mantêm a sua posição. `background` das estatísticas não era aplicado pelo overlay e continua sem efeito. O overlay Flash mantém-se para a informação do alvo, os limites do canhão e a mira automática. As páginas sem HUD Gameface (Halloween e Fort Rush) deixam de mostrar estes textos. Validado num replay no cliente EU: os dois textos aparecem, o arrasto com Ctrl grava a posição e o log não tem erros.

## Textos junto à mira migrados para Gameface — 2026-10-30

A contagem de pontaria, o tempo de voo do projétil e o indicador de penetração passaram de Flash (`dispersiontimerui.as`, `flighttimerui.as`, `armorcalculatorui.as` e a base `crosshairdisplayable.as`) para três vistas Gameface filhas da HUD nativa (`RandomHUDView`), com um renderizador partilhado (`shared/reticle_text.js` e `.css`) e os adaptadores em `gameface/battle/reticle_texts.py`. Como no Flash, cada texto fica na posição da mira mais o desvio `x`/`y` do módulo (`position.x`/`position.y` na penetração), em unidades da interface; na vista estratégica a âncora é o centro do ecrã. Os templates Flash (cor, tamanho, `b`/`i`/`u`, `br`) são convertidos em linhas de texto.

Em batalha, com Ctrl, cada texto pode ser arrastado e o novo desvio é gravado nas definições do próprio módulo. As vistas DAAPI, os metas, o `CrosshairMeta` e os aliases Flash foram retirados; o registo Flash passa a ter seis contratos. As páginas sem HUD Gameface (Halloween e Fort Rush) deixam de mostrar estes textos. Validado pelo utilizador no cliente EU (confirmado em 2026-11-02).

## Marcas do hangar junto à coluna de missões — 2026-10-30

O painel livre e arrastável das marcas no hangar foi substituído por um cartão compacto colocado por baixo da coluna nativa de missões (`HangarScreen_userMissions_*`, o widget `HangarWidget` de `mono/hangar/main`), com a mesma largura e o estilo das linhas de missão. O cartão mostra o ícone de marca da nação, a marca consolidada com a cor do colorrating escolhido e as estrelas. "Ver mais" abre à esquerda um painel lateral com o resto (veículo, barra com 65/85/95%, EMA, objetivo, histórico e estatísticas); fecha com o ×, Esc ou um clique fora.

O cartão não entra na árvore React do jogo: a coluna é posicionada pelas suas próprias animações, por isso o cartão mede-a e é recolocado enquanto está visível. Sem a coluna fica junto à margem direita. Saíram as definições `panel`, `card`, `compactMode`, `textLock` e `gameface.scale`, e os textos correspondentes; os perfis antigos mantêm essas chaves sem efeito. Validado pelo utilizador no cliente EU (confirmado em 2026-11-02).

As fontes Warhelios do cliente não têm estrelas, setas, triângulos nem ✓; esses símbolos passaram a imagens (`shared/assets/star*.png`) ou formas CSS nos painéis de marcas, na janela de definições e no gestor de contas.

## Vida do veículo migrada para Gameface — 2026-10-30

A barra de pontos de vida passou de Flash (`ownhealthui.as`) para uma vista Gameface própria, filha da HUD nativa (`RandomHUDView`), com a arte Driftkings em `gameface/mods/driftkings/vehicle_health/` (moldura, emblema e logótipo; enchimento, riscas e texto desenhados em CSS). A cor segue `avgColor`; a posição usa `x`/`y`/`alignX`/`alignY` e a barra pode ser arrastada em batalha com Ctrl. O AS3, a vista DAAPI, o meta e o alias Flash foram retirados; o registo Flash passou então a ter nove contratos e os defaults deixam de ter `colors`.

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
- **Helpers:** o `UpdateInstaller.exe` e o `WindowsFiles.exe` não foram exercitados nesta sessão; o utilizador confirmou-os depois no jogo (2026-11-02).

## Alterações e validação de 29 de outubro

- **Fontes:** OpenWG Common e o pacote Python `driftkings.fonts` foram retirados. As fontes são incorporadas/registadas nos dois SWF e carregadas por `@font-face` no Gameface; preservar `dkm`, `DriftkingsFont` e as fontes nativas; os aliases antigos foram retirados em 2026-10-30. OpenWG Gameface permanece como dependência separada, juntamente com ModsList.
- **Desempenho:** o utilizador confirmou fontes funcionais e ausência de lag observado no NA após a remoção do Common. Não existe comparação A/B válida que quantifique FPS ou prove a causa da quebra anterior. Não reintroduzir Common apenas para registar as fontes já incorporadas.
- **Marcadores e estatísticas:** defaults seguem o layout de referência sem XMQP; distância integrada desativada por defeito para manter o módulo independente «Distância ao alvo». A descoberta das vistas dos Player Panels continua ativa durante transições sem linhas. Preservar perfis pessoais; a configuração instalada pode diferir dos defaults.
- **Account Manager:** janela modal com área completa do cliente e centragem CSS, foco e captura de Esc; campo de palavra-passe guardada mascarado, revelação apenas a pedido e manutenção do valor ao guardar sem o alterar. Vistos desenhados em CSS sem depender de um glifo da fonte. O utilizador confirmou funcionamento no cliente NA `2.4.1.1 #987`.
- **Verificações desta correção:** build debug beta compilou 314 módulos Python 2.7; suites Gameface, sete testes de contas e validação dos contratos de build passaram. A build foi instalada no NA com backup do WOTMOD anterior. Não se afirma uma nova execução integral do CI nem publicação de release por essa instalação.

### Pendências e limites atuais

- O painel de configurações continua em construção; a aceitação visual no EU (2026-11-02) não cobre todas as falhas de gravação nem perfis externos.
- O modo Halloween foi aceite no jogo em 2026-10-30 (NA `2.4.1.1 #987`): TAB, painel, carregamento, log e restantes modos; ver o [guia Halloween](halloween/README.md#in-game-acceptance).
- Os helpers `UpdateInstaller.exe` e `WindowsFiles.exe`, compilados com Roslyn, foram confirmados no jogo pelo utilizador (2026-11-02).
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

Os comandos e requisitos estão em [CONTRIBUTING — Local build and client installation](../CONTRIBUTING.md#local-build-and-client-installation). Os testes decorrem nos clientes EU (`D:/Games/World_of_Tanks_EU`) e NA (`D:/Games/World_of_Tanks_NA`); o cliente de destino da instalação é o `game_root` de `build_data/toolchain.local.json` (fora do Git), atualmente o EU. A build aceita clientes EU, NA ou ASIA da versão do contrato; confirmar `version.xml` antes de instalar. O log é `<game-root>/game.log`.

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
