# Compatibilidade com WoT Common Test

Revisão e adaptação de 2026-11-05, na branch `feature/wot-2.4.2-ct`, criada da base `832d3263` (`0.1.7-beta.1`). Os contratos desta branch apontam exclusivamente para CT; `develop`, `main`, os pacotes publicados e `toolchain.local.json` não foram alterados. A versão local CT é `0.1.8-beta.1`, sem publicação.

## Fases 3E.2–3E.6 — Native Carousel PoC — 2026-11-09

**APTO PARA COMMIT LOCAL — INSTALAÇÃO CONTROLADA CONCLUÍDA E PRIMEIRA CONFIRMAÇÃO VISUAL CT REGISTADA; COMMIT NÃO AUTORIZADO.** Fase 3E.2: implementação experimental concluída. CarouselStats passa a quarto plugin nativo independente, com onRequestVehicles preservado; 16 consumidores continuam OpenWG e duas janelas próprias. Factory nativa recebe comandos opcionais; três plugins anteriores mantêm zero comandos e fontes protegidas. Backend funcional, patches, CrewDetails, launcher e dependências preservados.

Resultados históricos da Fase 3E.2: 869 testes Python 3, 678 Python 2.7, 26 suites frontend, seis testes de artefactos, lint e validadores PASS. As 24 ordens dos quatro plugins foram simuladas, não observadas no CT. Snapshot/logs em `build/diagnostics/phase3e2/20261109T155134Z/verified/`. Build debug beta `0.1.8-beta.3`, fonte 0.1.8-beta.1, 626 entradas, 13609962 bytes, SHA-256 `f0ff0cde074b25e0ee5d3f3c0647c870d01a85e6c8dfb8ed5b17bdf0709259a8`. Nenhum teste ou build novo executado na correção documental 3E.6.

Fase 3E.3: instalação controlada da beta.3 concluída, com integridade verificada. Entre 712 ficheiros do CT, apenas driftkings.wotmod foi substituído; OpenWG, ModsListAPI, perfis e configurações preservados. Versão CT #995 confirmada por version.xml, conforme substituição de fonte expressamente autorizada; sem criar .version_name. Relatório: `build/diagnostics/phase3e3/20261109T195257156673Z/installation-report.json`. Backup independente 3D em `build/backups/ct-phase3e3-install-20261109T195257156673Z/`, SHA-256 `7c50836f5f53eaf97a8c3a63433cc71e6889089b4d50b8fd98770888477ad89c`; rollback não executado.

Fase 3E.4: primeira sessão CT do utilizador em 09/11/2026, aproximadamente 20:01:09–20:03:21. Beta.3 carregada, serviços ativos e sem failures declaradas, quatro descriptors nativos registados, garagem carregada/HANGAR READY, sem tracebacks Python identificados e encerramento com `Scaleform Memory arenas are empty`. **PASS — confirmação visual manual do utilizador:** carrossel, estatísticas e campos adicionais apresentados normalmente. Registo de descriptors não comprova isoladamente init(); chamadas internas, payload e destroy() individual não estão demonstrados diretamente nos logs.

Sem prova abrangente nesta beta: todas as combinações de linhas/filtros/ordenações, todas as transições de modo, ciclos garagem → batalha → garagem, fault injection no CT real e destroy() individual. Não se declara ausência absoluta de fugas. Aviso Scaleform anterior continua em observação, causa não determinada e sem resolução definitiva; TextureManager, BZ-75 e DeviceCallback/BW::MouseCursor não têm causalidade demonstrada com Driftkings. MouseCursor é distinto do Scaleform.

Fase 3E.5 identificou a desatualização documental; Fase 3E.6 corrige apenas os três documentos autorizados e verifica a integridade dos 21 caminhos não documentais. **APTO PARA COMMIT LOCAL**, sujeito à verificação final e autorização expressa posterior. Sem staging, commit, push, release, nova instalação ou migração adicional nesta fase. [Contratos, evidências, limitações, checklist e rollback](NATIVE_CAROUSEL_POC.md). Secções seguintes são checkpoints históricos.

## Fase 3D.3 — apto para commit local, memória em observação — 2026-11-09

**APTO PARA COMMIT LOCAL**, sem staging/commit autorizado nesta execução. Nova execução: 864 testes Python 3, 675 Python 2.7, 25 suites frontend, cinco testes de artefactos, lint e validadores PASS, todos com exit code 0. Snapshot `2bf769feb61120aa1ae64e2e7a0842cafe63061cbb6a6d29639049b8d3326ea6` liga comandos/logs aos hashes atuais de origem e testes; hashes antes/depois dos testes idênticos. Evidência local ignorada em `build/diagnostics/phase3d3/20261109T131245Z/`; apenas os três documentos da Fase 3D foram posteriormente atualizados. 20 caminhos previstos, staging vazio, branch/HEAD e worktrees preservados; build/backup com hashes autorizados.

A investigação 3D.1 encontrou três sessões posteriores com arenas vazias: A com tooltips de Natal (identificação do utilizador); B com tentativa incompleta por falta de jogadores, sem batalha efetiva ou três ciclos adicionais; C com interações da tripulação, sem prova no log de todos os passos/restauração das opções. Uma ocorrência original de `Memory arena contains allocations. Lobby = true, Battle = false`, sem objetos/tamanhos/owners identificados; sem associação causal demonstrada à progressão e sem prova de ausência absoluta de fugas. **Risco residual EM OBSERVAÇÃO, causa não determinada.** Os oito cenários funcionais anteriores continuam PASS por confirmação separada do utilizador. A enumeração da sessão original foi corrigida para **oito grupos de registo**, com o último confirmado nas linhas 5494–5496 do excerto preservado.

Import rejeitado/promises retidas pelo loader continuam limitação conhecida; telemetria individual JS é insuficiente, cenário B complementar permanece pendente e profiling completo não foi realizado. Não são regressões automaticamente demonstradas nem bloqueios concretos identificados. Sem código/testes/catálogo/packaging alterados, build, instalação, arranque do CT, rollback, commit/push ou Fase 3E. [Rastreabilidade, resultados, cenários e riscos](NATIVE_CREW_PROGRESSION_POC.md#fase-3d3--rastreabilidade-e-encerramento-documental--2026-11-09). Secções seguintes são checkpoints históricos.

## Fase 3D — validação funcional e pendência técnica — 2026-11-09

Build Native Crew Progression instalada no CT #995: `7c50836f5f53eaf97a8c3a63433cc71e6889089b4d50b8fd98770888477ad89c`; oito cenários funcionais confirmados pelo autor. Três nativos e 17 OpenWG, mantendo ambas as dependências externas. Auditoria da sessão 11:59:17–12:28:14 e novas suites aprovadas (864 Python 3, 675 Python 2.7, 25 frontend, cinco artefactos). **Auditoria técnica pendente:** alocações Scaleform Lobby no encerramento, sem origem identificada; não é regressão causal comprovada do plugin. Sem telemetria individual JS de destroy ou medições de memória. Backup Fase 3C verificado, sem rollback, alteração de código, commit/push ou Fase 3E. [Relatório e limites](NATIVE_CREW_PROGRESSION_POC.md#auditoria-final-de-logs-e-lifecycle--2026-11-09). O encerramento Fase 3C seguinte é histórico.

## Encerramento Fase 3C — 2026-11-09

**Fase 3C concluída e validada no CT #995 no âmbito confirmado pelo autor.** Relógio e marcas da garagem usam plugins nativos independentes; os outros 18 consumidores continuam OpenWG e ambas as dependências de distribuição são preservadas. Confirmação inclui coexistência, hidePrestige, ativação/desativação, veículos, três ciclos sem duplicação e launcher. Log da build instalada identifica os dois registos backend e encerramento; não expõe init/destroy JS. Testes finais: 860 Python 3, 673 Python 2.7, 23 suites frontend, quatro artefactos e validadores aprovados. Pacote local/instalado `09b70a3b4a48194514393fa1f7cae1b7281a42434d1cbae9b78ce064cf4c9bec`, backup Fase 3A verificado. Sem nova instalação/build, push, release ou Fase 3D. Escalas/resoluções adicionais e memória não foram individualmente medidas. [Evidências e rollback](NATIVE_HANGAR_MARKS_POC.md#auditoria-final-e-encerramento--2026-11-09). O estado da Fase 3A abaixo é histórico.

## PoC Fase 3A — 2026-11-09

Relógio com arranque pelo loader nativo de plugins da garagem CT; os outros 19 consumidores ficam no OpenWG. Gate fundamentado nas fontes e bundles CT; testes automáticos e build aprovados. **Fase 3A concluída e validada no CT #995 no âmbito da checklist confirmada pelo autor, incluindo posição/escala, prestígio, três ciclos e regressões. Telemetria JS direta de destroy não observada; limites documentados no guia.** SHA-256 do PoC: `d08148935218a1fd9ee697e31f3e686928b4ac16bfc8e7d39a906b30d6eb3d14`. A aprovação da Fase 2 abaixo não abrange este PoC. [Contratos e rollback](NATIVE_CLOCK_POC.md).

## Encerramento Fase 2 — 2026-11-09

**Fase 2 — Validada funcionalmente no CT 2.4.2.0 sem ModsListAPI.** Confirmação do autor inclui botão, hover, abertura, X, Esc, atalho, regresso ao hangar e ausência de duplicações. O log sem ModsList confirma serviços ativos, `failures=[]` e `disabled={}`. ModsList restaurado após o teste. OpenWG continua utilizado; os dois pacotes mantêm-se no contrato de distribuição. Outros modos/escalas e futuras versões WoT requerem revalidação. [Registo completo](NATIVE_FOOTER_LAUNCHER.md#encerramento-formal-da-fase-2--2026-11-09). As pendências anteriores abaixo são históricas; sem implementação da Fase 3.

## Confirmação funcional do launcher — 2026-11-09

O autor confirmou em jogo a apresentação e o funcionamento do launcher da Fase 2. Revisão do log CT: arranque sem falhas/componentes desativados e sem erros identificados do launcher. Foram observados erros de partículas e dos SVG sociais do painel, sem atribuição ao launcher. ModsList e OpenWG estavam presentes; cenários sem ModsList, outros modos e escalas continuam por confirmar individualmente. Ver [registo detalhado](NATIVE_FOOTER_LAUNCHER.md#confirmação-do-autor-e-revisão-do-log--2026-11-09). A pendência na secção de implementação seguinte é histórica.

## Launcher CT — Fase 2 — 2026-11-09

O launcher próprio substitui o registo ativo Driftkings na ModsList, mantendo OpenWG e os dois pacotes na distribuição. Usa `_initChildren`, `setChildView` e a âncora DOM do footer CT; os modos com override próprio são tratados separadamente. **IMPLEMENTADO — VALIDAÇÃO EM JOGO PENDENTE.** O ciclo de versões local permanece inalterado. Ver [guia e rollback](NATIVE_FOOTER_LAUNCHER.md). Esta alteração não está abrangida pela aprovação anterior do CT.

## Ponto de controlo — 2026-11-09

O autor autorizou commit e push da barra de vida integrada antes da futura migração das dependências. Os três estilos adicionais e a preservação dos estilos/perfis anteriores estão descritos em [AMMO_HEALTH.md](AMMO_HEALTH.md). A aprovação CT de 2026-11-06 não valida esta nova apresentação; o teste visual em batalha continua pendente. O ciclo de versão CT permanece inalterado. ModsListAPI e OpenWG Gameface continuam dependências atuais; a sua substituição ainda não foi implementada.

## Correções implementadas e build de teste

- Arranque explicitamente permitido no realm CT; a normalização reconhece o rótulo `Common Test` sem aceitar sufixos arbitrários.
- Atualizador de produção desativado no runtime CT para evitar a instalação futura de pacotes de produção nesse cliente.
- Contratos, locales, bibliotecas SWC e lock dos marcadores alinhados com CT `2.4.2.5516`/`2.4.2.0`.
- Patches CT guardados em `build_data/patches/*_2.4.2_ct.json`; os patches de produção permanecem preservados. Carrossel e tooltip têm as âncoras e aliases das funções importadas remapeados; os exports de observable, action, optional, array, string e object foram verificados no bundle lib do CT.
- O patch ABC existente aplica-se ao filme CT e preserva o código nativo, incluindo `updateHpGlow`; não foi necessário substituir a lógica do marcador.

Compilar sem mudar os caminhos de produção guardados em `toolchain.local.json`:

```powershell
python -B build_tools/compiler.py --mode debug --channel beta --game-root C:/Games/World_of_Tanks_CT --reference-root E:/Wot_Mods_/Drift_Kings_ModPack/WoT_Tools/wot-src-CT
```

Saída: `build/debug/beta/0.1.8-beta.1/driftkings.wotmod`. Não instalar em EU/NA/ASIA. A build não foi instalada no CT nesta etapa.

Validação: compilação CT completa, contratos Gameface contra pacotes CT, análise de escopo sem novas referências JavaScript indefinidas, 657 testes runtime em Python 3 e Python 2.7, 181 testes build e 18 suites frontend. Passaram também lint, imports e nomes indefinidos. Os três testes sobre os SWF/fontes do pacote compilado passaram. Estes resultados não substituem validação visual/funcional no CT; serviços e estatísticas de contas CT também precisam dessa confirmação.

## Referências verificadas

| Referência | Snapshot | Cliente |
| --- | --- | --- |
| EU selecionada para produção | `2.4.1.5514` | `2.4.1.1 #993`, realm EU |
| CT para comparação | `2.4.2.5516` | `2.4.2.0 Common Test #995`, realm CT |

As fontes foram lidas em `WoT_Tools/wot-src-EU` e `WoT_Tools/wot-src-CT`. O cliente CT foi localizado em `C:/Games/World_of_Tanks_CT`; o seu `version.xml` confirma `2.4.2.0 Common Test #995`, realm CT, client `2655094`, overrides `2649229`. Os quatro pacotes GUI estão disponíveis. A extração de fontes não contém o dist Gameface; os pacotes instalados fornecem os recursos originais para a adaptação.

## Impactos identificados antes da adaptação

- **Arranque bloqueado:** `gui/mods/mod_driftkings.py` só aceita EU, NA e ASIA. O mod atual desativa-se no realm CT. Uma adaptação de teste deve tratar explicitamente CT sem o confundir com uma região de produção; os serviços de conta, estatísticas e atualização também devem ser revistos antes de permitir o arranque.
- **Contrato de build:** alvo `2.4.1.1`, referência EU e realms de produção não aceitam o cliente CT. Os hashes dos três patches Gameface, o SWF dos marcadores e as bibliotecas SWC têm de ser verificados contra o CT; não basta alterar a versão.
- **Marcadores:** `VehicleMarker.as` acrescenta `HP_GLOW_NAME` e `updateHpGlow()`, chamado após atualizar o hover. O brilho acompanha a visibilidade e posição do HP nativo. Confirmar a interação com barras/textos personalizados; preservar essa atualização. `VehicleMarkersManager.as` não mudou na comparação.
- **Página de batalha:** `BaseBattlePage.as` posiciona mensagens de erro segundo a mira e passa a escutar `CROSSHAIR_LAYOUT_CHANGE`; deixa de chamar `dualGunPanel.updateStage` naquele bloco. Revalidar sobreposições e alterações de resolução/mira.
- **Câmara estratégica:** nova compensação do pivot pela inclinação. Os hooks do mod delegam no método original; não foi identificada mudança direta de assinatura nos pontos consultados. A geometria dos limites de rotação e o zoom exigem teste no CT.
- **Temporizadores:** novos argumentos opcionais `isRestored`, deduplicação de efeitos e remoção de `hasActiveTimer` nas classes consultadas. O hook atual do mod usa `TimersPanel.__playStunSoundIfNeed`, não os métodos removidos; não foi identificada quebra direta nesse hook.
- **Carrossel:** removidos `_getVehicleTypesFilter` e `_getVehicleLevelsFilter` de `VehicleFiltersDataProvider`; a referência passa a usar as constantes diretamente. O mod não usa esses dois métodos e mantém hooks em `__updateModel` e `_finalize`. O bundle Gameface continua por validar.
- **Battle Pass e TAB:** alterações internas no cálculo de tempo/capítulos e na atualização de informação de veículo. Os hooks e modelos consumidos devem ser revalidados com o cliente; alteração de ficheiro por si só não prova quebra.

## Comparação dos pacotes CT com os patches de produção

| Recurso | SHA-256 CT | Compatibilidade dos pontos de substituição atuais |
| --- | --- | --- |
| Carrossel/hangar | `7e28391b4c51daa555b04d103a4031f7734b8d0728df03f7b73b47fa781873e5` | 18 de 23 operações não encontram o texto esperado; precisa de remapeamento |
| Quartéis | `d4784c9c6f1b66452dad287e89ffad84e142309a75599c3866498d16e3f0162a` | Recurso igual à produção; único ponto presente |
| Tooltips de tripulação | `a7cb133ce2d0495bd8b9cc29794755c55bc6e694f36e6d257b17fc4b6a4967dd` | 1 de 3 operações não encontra o texto esperado |
| SWF nativo dos marcadores | `34d92354f1c755313b99fd4e268bb78dc130ece24797a271aece5f0a7346537e` | Hash diferente da produção; revisão do patch ABC necessária |

Os resultados medem correspondências textuais das operações, não falhas observadas em jogo. A ausência de uma âncora pode resultar de renomeação de variáveis na minificação ou de uma alteração estrutural; é preciso distinguir as duas antes de adaptar. Os pacotes do cliente foram apenas lidos.

## Inventário e limites

Foram identificados 202 módulos em instruções Python `from ... import ...` do runtime, excluindo imports Driftkings e relativos. Entre os módulos resolvidos na extração EU, nenhum desapareceu na CT e 17 têm conteúdo diferente. Este inventário não cobre todos os imports dinâmicos, símbolos de extensões nem todos os caminhos de importação possíveis e não prova compatibilidade de execução.

As 18 classes ActionScript explicitamente importadas com namespace `net.*` foram comparadas onde disponíveis; `BaseBattlePage` mudou. A análise separada dos marcadores encontrou a alteração acima. As classes `PlayersPanelListItem` e `PlayersPanelListLeft` disponíveis para random, ranked e epicRandom mantêm o conteúdo. Os linkage classes `*UI` não estão disponíveis como ficheiros próprios na extração, pelo que os símbolos dos filmes ainda precisam de verificação.

## Validação pendente no CT

Instalar a build de teste com backup dos ficheiros existentes e testar login/hangar, contas, estatísticas, carrossel, quartéis/tooltips, marcadores normal/ALT/vivos/destruídos, mira/câmara, painéis, mensagens e minimapa por modo. Confirmar no `game.log` que os componentes e hooks iniciam e descarregam corretamente. Não atribuir compatibilidade completa ao CT com base apenas em compilação e testes portáteis.

## Correções após leitura do game.log — 2026-11-06

Cliente movido para `C:/Games/World_of_Tanks_CT`. O log contém uma sessão em F: e outra em C:, com arranque `failures=[]`/`disabled={}`. O pacote instalado corresponde à build local 0.1.8-beta.1; isto não constitui aprovação completa do CT.

Foram corrigidos dois pontos na build de teste local `0.1.8-beta.2` (versão apenas no pacote, sem alterar os metadados de release):

- Remoção do nevoeiro: o runtime Python e o helper C# resolvem o destino a partir de `paths.xml`, aceitando apenas a versão canónica ou a mesma versão com sufixo ` Common Test`. No CT o destino correto é `mods/2.4.2.0 Common Test`, não `mods/2.4.2.0`. Caminhos desconhecidos, ambíguos e diretórios inexistentes são rejeitados. Sem paths.xml mantém-se o destino numérico de produção. O protocolo de pedidos/resultados continua a usar a versão canónica; não foram apagados caches, resultados anteriores nem pastas do cliente.
- Gráfico das marcas: os segmentos passam a usar rotações em graus; o Gameface rejeitava `rotate(0rad)` no log. As coordenadas e comprimentos dos segmentos são preservados.

Verificação: 174 testes core em Python 3 e Python 2.7, 18 suites frontend, lint ES5, nomes indefinidos, contratos contra o CT em C: e compilação debug completa aprovados. Um probe compilado com o C# real confirmou o destino CT instalado, produção e rejeição de caminhos ambíguos/traversal, sem aplicar operações no cliente. A regressão do gráfico verifica segmentos horizontais, ascendentes e descendentes. Falta confirmar no jogo o gráfico e aplicar a opção de nevoeiro, fechar o cliente para o helper concluir e voltar a abrir para verificar o resultado.

Sem instalação, commit, push ou publicação destas correções. O painel redesenhado mantém-se na branch separada.

## Painel aprovado integrado no CT — 2026-11-06

Por autorização do autor, foram trazidos apenas os oito ficheiros do painel aprovados no commit `6c4bed01` de `feature/settings-header`: cabeçalho, duas imagens, SVG do gestor de contas, testes e guia. As correções CT locais foram preservadas. Não houve cherry-pick/commit/merge nem alteração das referências das outras branches.

A build debug CT mantém o mesmo número de teste `0.1.8-beta.2`, através do override já usado com `--keep-source-version`; os metadados versionados `0.1.8-beta.1` não foram incrementados. A regra de manter o número foi pedida apenas para este ciclo de teste CT e não altera as regras de novas versões/publicações nas restantes branches. O WOTMOD anterior sem o novo painel foi guardado em backup local antes da recompilação. Lint ES5, 19 suites frontend, contratos CT e catálogo UI aprovados; confirmar o painel no CT em jogo. Sem instalação ou publicação.

## Aprovação do CT e autorização de envio — 2026-11-06

O autor declarou a build CT `0.1.8-beta.2`, incluindo as correções de nevoeiro/gráfico e o painel atualizado, testada e aprovada em jogo, e autorizou commit e push na branch `feature/wot-2.4.2-ct`. A declaração não é uma nova matriz individual de testes por tema/modo nem validação de regiões de produção. As referências históricas a pendências nas secções anteriores descrevem as etapas anteriores à aprovação.

O número do pacote testado permanece `0.1.8-beta.2`; `build_data/release.json` e `VERSION` permanecem `0.1.8-beta.1`, conforme o ciclo local com override documentado. Não há publicação CT nem incremento de versão autorizado nesta etapa. Produção e a branch independente do cabeçalho não são alteradas por este envio.

SHA-256 do pacote local aprovado: `714e08cf625f981596e765d91ef12cede2fe9184af68ca46aeaa1d4d02d0c8f9`.
