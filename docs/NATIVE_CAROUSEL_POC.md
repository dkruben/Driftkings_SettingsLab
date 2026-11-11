# Fase 3E.2 — Native Carousel Plugin PoC

Baseline `501aec366fa3ef51e895a745cf9735ccf5a1db38`, branch `feature/wot-2.4.2-ct`, alvo CT 2.4.2.0 Common Test #995. **IMPLEMENTAÇÃO EXPERIMENTAL INSTALADA — PRIMEIRA VALIDAÇÃO VISUAL CT CONFIRMADA; APTO PARA COMMIT LOCAL, SEM AUTORIZAÇÃO DE COMMIT.** Nenhum PASS automático equivale a validação visual/funcional no CT.

## Âmbito e contratos

Apenas DriftkingsCarouselStats passa a quarto plugin nativo: 4 nativos, 16 OpenWG, 2 janelas próprias. Relógio, marcas, progressão, CrewDetails, launcher, cálculos, configurações, patches e dependências externas preservados. Nenhum commit/push ou Fase 3F autorizado.

`native_payload_model(feature, commands=())` mantém duas propriedades (payload e DriftkingsUI), reserva len(commands) e declara comandos Wulf via _addCommand. Sem attach_assets. payload_model permanece igual. Os três plugins existentes continuam com zero comandos; teste compara o resultado real da factory anterior e atual.

CarouselModel usa apenas onRequestVehicles. Argumento permanece `{ids: "123,456,789"}`: dicionário/string, limite2048caracteres, primeiros120tokens, isdigit, conversão, deduplicação e ordenação. IDs são descritores compactos de veículos, não IDs de tripulantes. Retorno Python None; dados chegam por payload posterior. Sem requestId/RPC/Promise de resposta. Guarda inicial em requestVehicles recusa pedidos antes da ativação/após finalização, sem mudar pedidos válidos. View, eventos, controller, cache, cálculos e publicação transacional preservados.

## Descriptor e identidade

URL física: `coui://gui/gameface/mods/driftkings/mono/driftkings/vehicle_carousel/carousel_plugin.js`.
Identidade SDK: `driftkings/vehicle_carousel/carousel_plugin.js`, distinta das três anteriores. Alias de recurso `mods/driftkings/vehicle_carousel/model`. Descriptor UserMissionsPluginModel no UserMissionsPresenter; alias ocupado não é substituído. Remoção exige a instância e URL publicadas; lifecycle original preservado. Sem dependências SDK entre plugins.

## Frontend, ownership e falhas

Entrypoint default.plugin sem efeitos de DOM na avaliação. init/destroy idempotentes; estados created/initializing/ready/failed/destroying/destroyed. Estado do modelo separado: waiting/bound/unavailable. Ready não exige cartões visíveis/modelo disponível, mas exige recursos e API prontos.

Carga sequencial: carousel_native.js → carousel_layout.js → carousel.js. Links próprios de fonts.css e carousel.css. Timeout10s cobre recursos/engine, não dados dos veículos. Imagens, model.html, declaração Wulf e helpers preservados no pacote.

Geração exclusiva __dkCarouselLoad. Helpers publicam DKCarouselNative/DKCarouselLayout apenas para uma geração válida; renderer publica __dkCarouselStats. Referências capturadas permitem limpar o owner antigo mesmo após substituição do global, sem apagar owner alheio. Globals retirados por identidade de geração; CSS e nós retirados por referências próprias, sem limpeza global do DOM.

Destroy invalida geração/dados, cancela timers, desliga observer/listeners/subscrições e tenta todas as limpezas apesar de falhas diagnosticadas. Montagens retiram camadas próprias e restauram estilos apenas se ainda correspondem aos valores aplicados. Cleanup de montagem parcial tenta libertar alterações já realizadas. Cálculos/layout visual e ordenação não foram redesenhados.

Scripts clássicos pedidos não são fisicamente canceláveis. O pedido pendente conserva callbacks de retirement e bloqueia nova geração até load/error. Execução tardia observa geração cancelada e não publica owners/reativa o renderer. Se nunca terminar, a funcionalidade permanece indisponível nesse documento; sem retry automático prometido. Falhas recuperáveis resolvem init com componente vazio válido, diagnosticando failed. Erro do próprio import antes do entrypoint executar continua limitação do loader CT.

## Progressão e tooltips

dk-carousel-config mantém nome e ausência de payload, após configuração/ordenação e durante descarte. Listener nativo do documento é preservado. O carrossel não cria/remove/substitui __dkCrewProgression nem chama stop/clear no controller partilhado. getRow(tankmanId), serialização e CrewDetails permanecem intactos.

## Fontes e patches protegidos

Fontes técnicas principais: `E:/Wot_Mods_/Drift_Kings_ModPack/Driftkings_WoT_Sources/wot_src_CT`, extração CT#995 descompilada/formatada; não tratada como fonte oficial original. Comandos fundamentados em ViewModel._addCommand, Command, EventsHandler, VehicleInventoryPresenter e VehicleFiltersDataProvider.

O compilador existente valida literalmente reference_root/.version_name contra2.4.2.5516. A extração nova declara2.4.2.0 Common Test; não foi modificada. Exclusivamente para este gate do compilador usa-se a referência CT anterior `E:/Wot_Mods_/Drift_Kings_ModPack/WoT_Tools/wot-src-CT`, que declara2.4.2.5516. O compilador não lê outras fontes desse parâmetro; os recursos originais para patches vêm dos pacotes do cliente CT em leitura. Não se alterou build_config.json nem toolchain.local.json.

Patches carousel_2.4.2_ct.json (24operações) e crew_tooltip_2.4.2_ct.json (3operações) intactos. Outputs exigidos:
- main: `0ad03065a96418af626a78b8ee2f8954fbc1accb899f5f328e9946cf0518eec3`.
- tooltips: `190534383748a3daac3d8097a15d6436174dbcf12648540cb1f06aa0eef9a498`.
Sem patch adicional de carga, index.js global ou modificação do loader oficial.

## Validação local e limites

Testes específicos: modelo sem/com comando; comparação com factory da baseline; binding/retirada, validação exata, deduplicação, payload posterior e descriptor por instância. Frontend executa os quatro entrypoints/renderers reais em DOM simulado nas24ordens. Exercita cada recurso ausente, renderer sem owner, CSS, engine rejeitado, subscrição/observer/comando/getter, criação/append/montagem parcial, timeout, retirement dos três scripts, modelo ausente/substituído, reciclagem/remoção de cartões, cleanup com exceções, globals substituídos, evento sem payload e falhas independentes de crew/carrossel. O modelo de contrato demonstra também quatro identidades e a retenção de um import rejeitado; a limpeza manual do harness não é apresentada como recuperação do loader. Isto não é o loader/Gameface real do CT.

Testes de catálogo protegem cálculos, controller, hooks, três plugins, CrewDetails, launcher, CSS/model.html e patches. Expectativas17→16 referem-se exclusivamente ao transporte migrado; comparação histórica da Fase3C agora permite crew e carousel como as únicas diferenças. Testes de artefactos comparam novo pacote com Fase3D preservada, verificando também os hashes dos patches e imagens.

## Build experimental

Saída isolada: `build/debug/beta/0.1.8-beta.3/`. Fonte permanece0.1.8-beta.1, com --keep-source-version. Build3D beta.2 e backup3C não são substituídos. Build debug concluída e verificada localmente na Fase 3E.2; detalhes históricos abaixo. A instalação posterior da Fase 3E.3 e a sessão do utilizador da Fase 3E.4 estão registadas a seguir.

## Rollback preparado — não executado

Retirar apenas descriptor/entrypoint CarouselStats; repor payload_model com onRequestVehicles e transporte OpenWG no catálogo; regenerar bootstrap pelo comando oficial; retirar inventário/lint novos; reverter adaptações dos três scripts e expectativas específicas. Reverter extensão opcional da factory apenas de forma localizada, preservando os três consumidores sem comandos. Não restaurar ficheiros partilhados indiscriminadamente.

Para eventual recuperação no CT: autorização separada e substituição exclusiva do pacote por build3D preservada, após hashes. Nunca reinstalar toda a suite nem alterar perfis/configurações. Build3D `7c50836f5f53eaf97a8c3a63433cc71e6889089b4d50b8fd98770888477ad89c`; backup3C `09b70a3b4a48194514393fa1f7cae1b7281a42434d1cbae9b78ce064cf4c9bec`.

## Instalação controlada — Fase 3E.3

Instalação autorizada da beta.3 concluída no CT 2.4.2.0 Common Test #995. A versão foi confirmada em `C:/Games/World_of_Tanks_CT/version.xml`, por substituição de fonte expressamente autorizada; o ficheiro não foi modificado e não foi criado `.version_name`. Entre 712 ficheiros inventariados antes/depois, apenas `mods/2.4.2.0 Common Test/driftkings.wotmod` foi substituído. OpenWG, ModsListAPI, configurações, perfis e restantes mods preservados. O CT não foi iniciado pela instalação.

Relatório: `build/diagnostics/phase3e3/20261109T195257156673Z/installation-report.json`. Origem local e pacote instalado: SHA-256 `f0ff0cde074b25e0ee5d3f3c0647c870d01a85e6c8dfb8ed5b17bdf0709259a8`.

Backup independente da Fase 3D: `build/backups/ct-phase3e3-install-20261109T195257156673Z/fase3d-7c50836f5f53eaf97a8c3a63433cc71e6889089b4d50b8fd98770888477ad89c.wotmod`; SHA-256 `7c50836f5f53eaf97a8c3a63433cc71e6889089b4d50b8fd98770888477ad89c`. Backup verificado; rollback não executado.

## Primeira sessão CT — Fase 3E.4

Sessão do utilizador em 09/11/2026, aproximadamente 20:01:09–20:03:21, analisada no `game.log` existente. Driftkings 0.1.8-beta.3 carregou; startup às 20:01:35.292 com serviços ativos e `failures=[]`. Quatro descriptors nativos registados às 20:02:01.943–944; RandomHangar carregou e o cliente chegou a HANGAR READY às 20:02:06.312. Não foram identificados tracebacks Python nessa sessão. Encerramento com `Scaleform Memory arenas are empty` às 20:03:17.617.

**PASS — confirmação visual manual do utilizador:** carrossel, estatísticas e campos adicionais apresentados normalmente, sem anomalias visuais reportadas durante a sessão. Este PASS tem esse âmbito limitado.

Registo de descriptors não comprova isoladamente a execução individual de `init()`. Entrypoint carregado, binding do modelo, chamada de onRequestVehicles, publicação de payload, renderer pronto e `destroy()` individual não são demonstrados diretamente pelos logs disponíveis. Ausência de traceback não equivale a aprovação funcional de todos os percursos.

## Checklist CT — evidência parcial e cenários pendentes

Observados: startup, registo dos quatro descriptors, garagem pronta e encerramento; apresentação do carrossel/estatísticas/campos adicionais confirmada manualmente. Os testes automáticos históricos da Fase 3E.2 e as 24 ordens em DOM simulado permanecem evidência local, não sequências executadas no jogo.

Permanecem sem prova abrangente nesta beta: todas as combinações de linhas 1–4, perfis normal/pequeno, filtros/pesquisa/ordenação; scroll/pedidos visíveis; troca rápida de veículo; opções; todas as transições de modo; tooltips de veículo/tripulação; reentrada; ciclos garagem → batalha → garagem; regressão completa de relógio/hidePrestige, marcas, progressão, CrewDetails e launcher/definições. Fault injection no CT real e execução individual de destroy() dos quatro plugins não foram comprovados. Não se declara ausência absoluta de fugas de memória.

## Scaleform

Fase3D.1 permanece em observação: uma ocorrência original Lobby=true/Battle=false, três sessões seguintes com arenas vazias, causa não determinada, sem associação demonstrada ao carrossel e sem profiling completo. Nenhuma alteração foi introduzida para corrigir esse aviso; não se declara ausência absoluta de fugas. A primeira sessão beta.3 também encerrou com arenas vazias; isso não demonstra resolução definitiva. Avisos TextureManager surgiram antes e depois do carregamento Driftkings; partículas BZ-75 antes; transparent_white_2x2.dds durante a garagem; BW::MouseCursor no encerramento. Não existe causalidade demonstrada com Driftkings/carrossel. O aviso DeviceCallback/BW::MouseCursor é distinto do Scaleform. Congestionamento e filas de tarefas também não têm causalidade atribuída ao mod.

## Resultado histórico da implementação — Fase 3E.2, 2026-11-09

**Gate histórico da Fase 3E.2: APTA PARA INSTALAÇÃO CONTROLADA NO CT.** Naquela fase ainda não havia instalação ou validação CT. A instalação e a confirmação visual posteriores estão registadas acima. Os resultados da tabela seguinte são históricos; não foram executados novos testes ou builds nas Fases 3E.5/3E.6. Sem commit/push.

| Verificação | Resultado final |
|---|---|
| Python 3 | 869 PASS |
| Python 2.7 | 678 PASS |
| Frontend | 26 suites PASS |
| Artefactos reais | 6 PASS |
| Lint | PASS, zero avisos |
| Catálogo | 4 nativos / 16 OpenWG / 2 janelas próprias |
| Build data | 39 manifests, 307 módulos, 318 assets, 54 defaults, 2 dependências |
| Locales | 18, zero não traduzidos |
| Defaults / nomes indefinidos / diff check | PASS |

Evidência local ignorada: `build/diagnostics/phase3e2/20261109T155134Z/`. `baseline.json` regista hashes anteriores à edição e dos pacotes protegidos. `final/` contém validações completas; após o teste adicional de descarte reentrante, `verified/` contém novo snapshot, frontend/lint, build/artefactos e nova execução integral Python 3/2.7. Snapshot verificado: `2f3422a0eba9d7215aedaf34297af310f683ba49153ad87648d106364704af23`. Os comandos, timestamps UTC, exit codes e hashes de logs estão em results.json de cada execução. Depois do snapshot verificado foram atualizados os três documentos e acrescentados dois cenários ao teste frontend: quatro identidades através do modelo de loader e import rejeitado/remoção bloqueada. A suite frontend completa foi repetida com PASS; hash do teste e log constam de verified/frontend-contract-final.json. Código funcional e testes Python mantêm os hashes verificados; o manifesto final separa estas alterações.

Um teste adicional demonstrou que a API antiga podia voltar a indicar ready após um descarte provocado dentro de onRequestVehicles. Guardas após chamadas reentrantes e antes de marcar prontidão corrigem esse percurso; teste de regressão aprovado. Não alterou argumentos ou cálculos.

Artefacto final: `build/debug/beta/0.1.8-beta.3/driftkings.wotmod`.
- Debug, canal beta, não publicável; fonte permanece0.1.8-beta.1.
- Tamanho: **13609962 bytes**.
- Entradas: **626** (mais um entrypoint, nenhuma entrada removida).
- SHA-256: `f0ff0cde074b25e0ee5d3f3c0647c870d01a85e6c8dfb8ed5b17bdf0709259a8`.
- Manifesto de build: `build/debug/beta/0.1.8-beta.3/build-report.json`, **779 inputs**, todos verificáveis por hash.
- Os hashes main/tooltips acima permanecem exatos.
- Imagens, fontes, três plugins anteriores e CrewDetails preservados.

Diferenças de recompilação explicitadas: os307.pyc recebem o timestamp da baseline atual; excluindo o cabeçalho Python2.7, apenas os corpos de __init__ (versão experimental), gameface/core, adaptador do carrossel e interface_catalog diferem. Nos SWF driftkingsbattle/driftkingspanels só muda o campo de timestamp de compilação do tag ProductInfo; todos os demais tags, incluindo código e recursos, são equivalentes. Teste de artefactos cobre esta comparação sem modificar os SWF. Não se afirma identidade binária integral de ficheiros recompilados.

Build3D beta.2 local preservada, backup independente da instalação 3D e backup3C mantêm os hashes anteriores; o pacote atualmente instalado é a beta.3. A build experimental foi regenerada após a correção de reentrada; apenas o SHA-256 final acima identifica o pacote aprovado automaticamente. Outputs anteriores de diagnóstico não são candidatos à instalação.

Gate histórico 3E.2: testes locais, contratos, recursos protegidos, rollback preparado e pacote verificado permitiram solicitar instalação controlada. Não demonstram todos os percursos do loader real, cancelamento físico de scripts, ausência absoluta de fugas ou conclusão da investigação Scaleform. A checklist CT tem a evidência parcial e as pendências discriminadas acima.

## Correção documental e preparação — Fase 3E.6

A auditoria 3E.5 confirmou o âmbito dos 24 caminhos, os contratos, a evidência automática histórica, a build/backup e a primeira confirmação visual; identificou como correção necessária o estado documental desatualizado. A Fase 3E.6 atualiza exclusivamente este documento, CT_COMPATIBILITY.md e STATUS.md. Os 21 caminhos não documentais devem manter os hashes do snapshot 3E.5, coincidentes com o manifesto final 3E.2. Sem novos testes, builds, instalação, rollback ou operações Git de escrita.

**APTO PARA COMMIT LOCAL**, sujeito à verificação final de integridade e a autorização expressa posterior. Esta decisão não aprova os cenários CT pendentes, não encerra a investigação Scaleform e não autoriza staging, commit, push, release ou migração adicional.
