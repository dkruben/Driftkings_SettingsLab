# Plano de Trabalho — Driftkings SettingsLab

- Projeto: `dkruben/Driftkings_SettingsLab`
- Branch: `develop`
- Referência da análise: commit `9ebc163661ab`
- Objetivo: eliminar processamento redundante, melhorar a robustez e otimizar o desempenho sem alterar o comportamento dos mods.
- Última atualização: `2026-10-28`.
- Estado: Fases 01–06 concluídas e revistas estaticamente; validação funcional completa no cliente WoT pendente.
- Entrega: commit `202f476`, enviado para `origin/develop` por instrução explícita do autor.

O plano está organizado em seis fases independentes. Cada fase deverá ser concluída e revista antes de avançar para a seguinte.

## 1. Visão geral

| Fase | Área | Prioridade | Objetivo | Estado |
| --- | --- | --- | --- | --- |
| 01 | Player Ratings e estatísticas | Alta | Eliminar operações redundantes e otimizar acesso aos dados | Implementada; revisão estática concluída |
| 02 | Sistema de configurações | Alta | Melhorar validação, persistência e consistência das alterações | Implementada; revisão estática concluída |
| 03 | Comunicação Gameface | Média | Reduzir serializações e atualizações desnecessárias | Implementada; revisão estática concluída |
| 04 | Desempenho durante a batalha | Alta | Rever Vehicle Markers, Player Panels e minimapa | Implementada; revisão estática concluída |
| 05 | Hooks, eventos e ciclo de vida | Média | Auditar registos, subscrições e limpeza de recursos | Implementada; revisão estática concluída |
| 06 | Revisão de integração | Alta | Verificar contratos, compatibilidade e alterações acumuladas | Concluída; ver auditoria final |

## 2. Trabalhos por fase

| Fase | Intervenção prevista | Critério de conclusão |
| --- | --- | --- |
| 01 | Substituir pesquisas de `tdv` baseadas em serialização JSON por percurso da configuração, reduzir consultas repetidas e analisar cache | Sem alteração do resultado das estatísticas |
| 02 | Validar alterações antes de aplicar, rever rollback e diferenças entre Apply/Save/Discard | Sem estados inconsistentes introduzidos |
| 03 | Comparar publicação de estados Gameface, payloads e renderização | Contratos Python–JS preservados |
| 04 | Identificar atualizações gráficas repetidas e cálculos sem alterações dos dados | Redução demonstrável de operações redundantes |
| 05 | Inspecionar instalação de hooks, subscrições e callbacks | Sem novos registos duplicados ou recursos pendentes |
| 06 | Rever imports, compatibilidade Python 2.7, contratos e JSON | Sem regressões identificadas na revisão estática |

## 3. Regras de execução

Para proteger o funcionamento do modpack, o Codex deve respeitar estas condições durante todas as fases:

- Não consultar, modificar, criar ou executar testes.
- Não consultar nem modificar documentação durante as fases. Atualizar este plano apenas por pedido explícito do utilizador, como nesta atualização.
- Preservar Python 2.7, ActionScript 3 e as APIs do cliente WoT.
- Não alterar funcionalidades, configurações existentes, nomes públicos ou formatos JSON.
- Não introduzir novas dependências externas.
- Não remover mecanismos de compatibilidade com outros mods sem uma justificação concreta.
- Não efetuar commits nem pushes automaticamente.
- Trabalhar numa fase de cada vez, com alterações pequenas e reversíveis.
- Distinguir melhorias verificáveis por inspeção de ganhos de FPS que necessitam de medição no jogo.

## 4. Registo das fases executadas

As conclusões abaixo resultam de inspeção e verificações estáticas. Não representam validação funcional no WoT nem medições de CPU, memória ou FPS.

### Fase 01 — Player Ratings e estatísticas

**Ficheiros modificados**, relativos a `mod/res/scripts/client/driftkings/`:

- `core/player_ratings.py`
- `core/panel_macros.py`

**Trabalho realizado:**

- Substituídas duas serializações completas usadas para procurar `tdv` por uma função partilhada que percorre chaves, valores e templates aninhados, incluindo o caso legado das tabulações escapadas pelo JSON.
- Reutilizadas configurações locais na seleção da cache e na aplicação das cores.
- Adiada a resolução das cores até as métricas terem os valores finais.
- Reutilizada a lista serializada dos campos dos pedidos por região e removidas cópias dispensáveis no fallback WN8.
- Mantidas as fórmulas, a política de expiração, as tentativas e os pedidos externos.
- Analisados também `core/analytics.py`, `core/panel_model.py` e `stats/vehinfo.py`, sem alterações.

**Verificação:** sintaxe Python 2.7, referências, assinaturas existentes e campos de saída. Nenhum nome indefinido encontrado.

**Contagem por inspeção:** com estatísticas válidas, `applyPlayer()` passa de oito para quatro cálculos de cores e de nove para cinco consultas às configurações, após a Fase 06 preservar as quatro chamadas públicas a `Statistics.getColor()`.

### Fase 02 — Sistema de configurações

**Ficheiros modificados**, relativos a `mod/res/scripts/client/driftkings/`:

- `settings/service.py`
- `settings/panel/session.py`
- `settings/panel/registry.py`

**Trabalho realizado:**

- Introduzida validação prévia de uma cópia independente dos drafts: dependências, controlos estaticamente desativados, tipos e limites são verificados antes da primeira publicação.
- Mantida a validação na publicação, porque callbacks anteriores podem alterar o registo.
- Reutilizado o candidato preparado por `SettingsService.apply()`, reduzindo de duas para uma as construções completas desse candidato.
- Os acessos individuais por `ModHandle` copiam apenas o valor solicitado, preservando a proteção contra mutações.
- Evitadas a recriação da lista de controlos durante a gravação e a construção do fallback de caminhos quando já existe `changes.paths`.
- Mantidas as cópias defensivas necessárias ao undo, às notificações e à reversão em memória.

**Semântica preservada:** o botão Apply continua a chamar `session.save()`; módulos com `external_apply` mantêm o comportamento de persistência existente. Não foi introduzida uma transação global nem prometido rollback completo.

**Verificação:** sintaxe Python 2.7 em 13 módulos revistos, imports, assinaturas e contratos. Nenhum nome indefinido encontrado.

### Fase 03 — Comunicação Gameface

**Ficheiros modificados:**

- `mod/res/scripts/client/driftkings/gameface/lobby/settings_window.py`
- `mod/res/gui/gameface/mods/driftkings/settings_window/js/app.js`
- `mod/res/gui/gameface/mods/driftkings/settings_window/js/bridge.js`
- `mod/res/gui/gameface/mods/driftkings/settings_window/js/carousel.js`
- `mod/res/gui/gameface/mods/driftkings/settings_window/js/layer.js`
- `mod/res/gui/gameface/mods/driftkings/settings_window/js/minimap.js`

**Trabalho realizado:**

- Consolidadas no fim da ação as notificações síncronas de estrutura. As notificações do updater permanecem imediatas para preservar estados intermédios e erros.
- Publicadas apenas propriedades cujo JSON mudou. A cache de conteúdo enviado só é atualizada depois de a transação terminar com sucesso.
- Eliminada a renderização duplicada quando schema e estado mudam juntos; alterações apenas ao schema reutilizam o último estado válido.
- Evitados redesenhos das previews do carrossel e minimapa para entradas idênticas. Previews temporárias e redesenhos explícitos continuam a ser respeitados.
- Cancelados timers de redesenho de páginas removidas e de foco de diálogos fechados.
- Protegida a continuação de ações contra views entretanto destruídas.

**Verificação:** sintaxe Python 2.7 e JavaScript ES5, nomes indefinidos, assinaturas e exports. Mantidos `schema`, `state`, `onAction`, a ocultação de segredos e os formatos JSON. Os ficheiros das Fases 01 e 02 permaneceram intactos.

**Limite:** notificações independentes continuam a reconstruir e serializar o estado para uma comparação segura; não foi introduzida uma cache geral do estado do painel.

### Fase 04 — Desempenho durante a batalha

**Ficheiros modificados:**

- `mod/res/scripts/client/driftkings/flash/battle/vehicle_markers/ratings.py`
- `mod/res/scripts/client/driftkings/flash/battle/minimap_plugins.py`
- `mod/res/scripts/client/driftkings/gameface/battle/panel_gameface.py`
- `flash_source/battle/src/driftkings/battle/components/minimap/minimaplines.as`
- `flash_source/battle/src/driftkings/battle/components/minimap/vehiclelabels.as`

**Caminhos identificados e preservados:**

- Marcadores: tick de 0,2 segundos com distância, ou 1 segundo sem distância; contexto dinâmico continua a ser calculado por veículo.
- Player Panels: callback Python de 0,25 segundos e eventos adicionais. O Flash recebe `ENTER_FRAME`, com limitação do trabalho quando não há alterações.
- Minimapa: eventos de veículos e timer Flash de 250 ms. A frequência dos métodos nativos dos marcadores depende do cliente e não foi assumida como sendo por frame.

**Trabalho realizado e contagens por inspeção:**

| Operação | Antes | Depois |
| --- | --- | --- |
| Consulta de `enabled()` e do limite mínimo nos marcadores, por tick com N veículos | N chamadas de cada | Uma chamada de cada |
| Acesso às configurações por etiqueta do minimapa | 3–7 consultas, conforme o estado | Uma consulta |
| Projeção das linhas para V views Gameface ativas | V construções | Uma construção por operação |
| Seno/cosseno por transformação de linha do minimapa | Quatro chamadas | Duas chamadas |
| Lista temporária de etiquetas no início da atualização AS3 | Uma nova lista | Lista privada esvaziada e reutilizada |

**Cache e memória:** não foram introduzidas caches persistentes. A projeção Gameface é partilhada apenas dentro da mesma operação e volta a ser criada na atualização seguinte. As invalidações, a ordem por view, os agendamentos e os caminhos de encerramento existentes foram preservados.

**Verificação:** análise sintática Python 2.7 em 33 módulos, JavaScript ES5 e referências nos três scripts do painel Gameface de batalha. As duas alterações AS3 foram revistas por inspeção, incluindo assinaturas, delimitadores e listeners; não houve compilação nem alteração de recursos SWF. Os ficheiros das fases anteriores permaneceram intactos.

### Fase 05 — Hooks, eventos e ciclo de vida

**Ficheiros modificados**, relativos a `mod/res/scripts/client/driftkings/`:

- `core/callbacks.py`
- `core/battle_events.py`
- `flash/battle/messages.py`
- `gameface/lobby/vehicle_carousel.py`

**Auditoria realizada:**

- Inventariados 157 módulos Python e revistos os caminhos centrais de declaração, ativação e desativação de hooks, eventos, callbacks, teclado e contextos.
- Revistos os proprietários e a limpeza de recursos Flash/Gameface, incluindo loaders, tweens e scripts de interface.
- Confirmada a preservação da identidade dos hooks por proprietário, da instalação única e dos wrappers desativáveis que encaminham a chamada original.
- Mantida a gestão partilhada de `BattleEvents`: as subscrições não são desligadas enquanto existirem consumidores.

**Defeitos confirmados e correções:**

| Problema | Correção implementada |
| --- | --- |
| A primeira subscrição de sessão ficava ligada se a segunda falhasse | Remoção da subscrição já adquirida antes de propagar a exceção |
| O serviço de callbacks mantinha o estado de arranque após falha na aquisição dos eventos | Limpeza da subscrição e da referência aos eventos, permitindo nova tentativa coerente |
| O controlador do carrossel não protegia arranques e encerramentos repetidos | `start()`/`stop()` idempotentes; remoção no serviço exato que recebeu a subscrição; notificações ignoradas após paragem |
| As mensagens Flash diferidas não estavam associadas à arena original nem ao serviço central | Agendamento centralizado e verificação da identidade da arena antes da entrega ou de nova tentativa |
| A limpeza de fim de batalha não abrangia callbacks de adaptadores Flash de batalha | Cancelamento também dos proprietários `driftkings.flash.battle.*`, preservando callbacks de lobby e da aplicação |

**Reforço defensivo:** o callable de um callback verifica se o registo ainda está pendente antes de executar o método. A ocorrência efetiva de chamadas tardias pelo backend WG após cancelamento não foi reproduzida; essa proteção foi revista por inspeção.

**Compatibilidade e limites:**

- Mantidas as assinaturas públicas, as chamadas originais WG e os contratos dos ViewModels.
- Mantido o intervalo de 0,5 segundos das tentativas de mensagens e os restantes intervalos de atualização.
- Não removidos wrappers dos métodos WG nem introduzido outro gestor global de hooks.
- Nenhuma alteração adicional a AS3, JavaScript ou SWFs nesta fase.
- Confirmado por comparação de hashes que os 16 ficheiros alterados nas Fases 01–04 permaneceram intactos durante a Fase 05.

**Verificação:** sintaxe Python 2.7 nos 157 módulos inventariados, nomes indefinidos, imports, assinaturas, cadeias de hooks e diferenças do código. Nenhum nome indefinido encontrado. Não foram consultados, criados ou executados testes.

## 5. Questões pendentes e validação no cliente

| Origem | Questão | Estado / proposta |
| --- | --- | --- |
| Fase 01 | A assinatura de `_appliedCache` não inclui `minBattlesToShow` nem a revisão das tabelas | Política mantida; rever separadamente as condições de invalidação antes de acrescentar cache de métricas |
| Fase 02 | Callbacks, validações específicas e `external_apply` ainda podem falhar depois de outros módulos publicarem alterações | A validação prévia reduz o risco, mas não torna a aplicação globalmente transacional; definir preparação sem efeitos externos antes de uma intervenção mais ampla |
| Fase 02 | Gravação separada dos ficheiros público e de segredos | Pode ficar parcialmente concluída; estudar transação conjunta sem alterar silenciosamente Save ou os formatos existentes |
| Fase 02 | Normalização por `external_apply` pode deixar o painel com valores diferentes dos efetivamente aplicados | Definir um contrato explícito de leitura dos valores normalizados antes de corrigir o adaptador |
| Fase 03 | Reconstrução integral do estado em notificações independentes | Mantida para evitar valores desatualizados; qualquer cache adicional precisa de invalidação demonstrável |
| Fase 05 | Ordem de instalação de hooks de terceiros e falhas nativas na remoção de subscrições | Exigem validação no cliente; não foram alteradas cadeias pertencentes a outros mods |
| Fase 05 | Comportamento do backend WG perante callbacks já cancelados e falhas parciais de arranque | Proteções revistas estaticamente; ocorrência e recuperação efetivas ainda por validar no WoT |
| Fases 01–06 | Compatibilidade funcional no WoT e resultados de desempenho | Pendente; sem medições quantitativas de CPU, memória ou FPS |

A validação futura no cliente deve abranger Apply/Save/Cancel/Discard/Reset/Undo, perfis, troca de idioma, captura de teclas, erros do updater, encerramento rápido da janela, morte, observação, replay, spotting e interação com outros mods. As falhas de gravação e de callbacks também continuam por validar.

Para a Fase 05, ficam explicitamente pendentes entrada e saída de batalha, transição para espectador, troca de veículo observado, avanço e recuo em replay, batalhas consecutivas, arranques incompletos e encerramento com callbacks pendentes. A revisão estática não constitui garantia de funcionamento destes cenários no cliente.

## 6. Fase 06 e próximos passos

A revisão final preservou os contratos públicos e corrigiu a passagem indevida por cima de `Statistics.getColor()`. O [relatório completo](AUDITORIA_FINAL_INTEGRACAO.md) apresenta os ficheiros, verificações estáticas, riscos e checklist manual. As seis fases foram enviadas no commit `202f476`.

Os replays NA observados em 28/10 não apresentaram exceções Python ou JavaScript registadas; isto não substitui a validação completa de configurações, lobby, ciclo de vida e compatibilidade com outros mods. Manter as pendências da auditoria e medir no cliente antes de atribuir ganhos de CPU, memória ou FPS.
