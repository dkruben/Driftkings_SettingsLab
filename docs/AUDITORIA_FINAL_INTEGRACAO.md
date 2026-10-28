# Fase 6 — Auditoria Final de Integração, Compatibilidade e Estabilidade

- Projeto: `dkruben/Driftkings_SettingsLab`
- Branch: `develop`
- Data: `2026-10-28`
- Base de comparação: `9ebc163661ab0e04d8be65dbc119b8184a3f3ddc`
- Estado da entrega: alterações locais, sem commit nem push.

## A. Resumo executivo

**Classificação: apto para validação funcional.**

A integração das cinco fases foi revista contra a base Git indicada. Foi identificada e corrigida uma regressão pequena da Fase 1. Não ficaram regressões bloqueantes novas confirmadas por inspeção.

Esta conclusão **não significa que o modpack esteja pronto para distribuição**. A análise estática não substitui a execução no cliente World of Tanks.

## B. Âmbito

Foram revistos os 20 ficheiros de código alterados nas Fases 1–5: 13 Python, cinco JavaScript e dois AS3. Foram também consultadas as dependências necessárias de inicialização, configurações, estatísticas e ciclo de vida.

### Ficheiros Python

Caminhos relativos a `mod/res/scripts/client/driftkings/`:

- `core/player_ratings.py`
- `core/panel_macros.py`
- `core/battle_events.py`
- `core/callbacks.py`
- `settings/service.py`
- `settings/panel/session.py`
- `settings/panel/registry.py`
- `flash/battle/messages.py`
- `flash/battle/minimap_plugins.py`
- `flash/battle/vehicle_markers/ratings.py`
- `gameface/battle/panel_gameface.py`
- `gameface/lobby/settings_window.py`
- `gameface/lobby/vehicle_carousel.py`

### Ficheiros JavaScript

Caminhos relativos a `mod/res/gui/gameface/mods/driftkings/settings_window/js/`:

- `app.js`
- `bridge.js`
- `carousel.js`
- `layer.js`
- `minimap.js`

### Ficheiros ActionScript 3

Caminhos relativos a `flash_source/battle/src/driftkings/battle/components/minimap/`:

- `minimaplines.as`
- `vehiclelabels.as`

### Alterações da Fase 6 e limites da análise

Apenas `core/player_ratings.py` foi modificado nesta fase. Os restantes 19 ficheiros permaneceram intactos, conforme comparação de hashes.

A base Git estava disponível e correspondia ao HEAD. O Markdown preexistente do plano foi separado do âmbito da auditoria de código. Não foram descartadas nem substituídas alterações locais.

Não foram consultados, criados ou executados testes, nem executados o WoT ou scripts de inicialização do cliente. Não foram compilados SWFs. Este relatório foi guardado posteriormente por pedido explícito do utilizador.

## C. Compatibilidade

| Área | Verificação e resultado |
| --- | --- |
| Python 2.7 | 313 módulos de produção passaram na análise sintática, sem importar ou executar os módulos da aplicação |
| JavaScript ES5 | 12 scripts relacionados passaram na análise sintática e de referências |
| ActionScript 3 | Assinaturas, referências, delimitadores e substituições revistas por inspeção; sem compilação |
| Imports | Não foram identificados novos ciclos de importação imediata no grafo de 312 módulos do pacote; imports dinâmicos e dependentes do WG não foram executados |
| Contratos públicos | Assinaturas existentes, classes, constantes, propriedades dos ViewModels e comandos preservados |
| Flash e Gameface | Mantidos os contratos dos payloads e as propriedades `schema` e `state`, bem como o comando `onAction` |
| JSON e recursos | Sem alterações a configurações JSON, valores predefinidos, SWFs ou SWCs |
| Estatísticas | Fórmulas e caminhos de pedidos, retries e expiração comparados com a base, sem alterações funcionais identificadas |

Não foram encontrados nomes indefinidos pelos verificadores utilizados. Estes resultados não constituem garantia de compatibilidade funcional no cliente WoT.

## D. Problema confirmado e corrigido

### D1. Encaminhamento das cores contornava o método público

- **Gravidade:** média.
- **Classificação:** regressão confirmada no código da Fase 1.
- **Localização:** `core/player_ratings.py`, método `Statistics.applyPlayer()`, chamadas finais de cores a partir da linha 647 na versão auditada.
- **Causa:** as chamadas a `self.getColor()` tinham sido substituídas por chamadas diretas ao helper privado `_rating_color()`.
- **Consequência:** eventuais overrides do método público `Statistics.getColor()` deixavam de intercetar aquelas cores.
- **Correção aplicada:** restauradas as quatro chamadas públicas, mantendo a resolução das cores depois de as métricas atingirem os valores finais. Removida a variável local de escala que deixou de ser utilizada.
- **Contratos:** sem alterações de assinaturas, fórmulas, campos ou formatos.
- **Validação no cliente:** confirmar cores e interceção por outros mods que utilizem esse método.

Com a implementação padrão e estatísticas válidas:

| Operação em `applyPlayer()` | Antes das fases | Após a correção da Fase 6 |
| --- | --- | --- |
| Cálculos de cores | Oito | Quatro |
| Consultas às configurações | Nove | Cinco |

A contagem anterior da Fase 1 de uma consulta às configurações deixa de se aplicar após esta correção de compatibilidade. As contagens resultam de inspeção do código e não representam medições de CPU ou FPS.

## E. Revisão das cinco fases

| Fase | Resultado da revisão |
| --- | --- |
| 1 — Estatísticas | Pesquisa de `tdv` coerente com os dados JSON suportados, incluindo templates aninhados e tabulações escapadas. Fórmulas preservadas; corrigido o encaminhamento das cores |
| 2 — Configurações | Pré-validação, cópias defensivas e persistência continuam coerentes com a semântica existente. Apply continua a guardar. Não foram acrescentados bloqueios de dependências dinâmicas |
| 3 — Gameface | Schema e estado continuam coordenados; updater publica independentemente da consolidação. Mensagens, segredos ocultados, previews temporárias e encerramento mantêm os respetivos caminhos |
| 4 — Batalha | Contextos dinâmicos continuam dentro do ciclo por veículo. A projeção partilhada limita-se à mesma operação; ordem por view, geometria e frequências preservadas |
| 5 — Ciclo de vida | Subscrições parciais têm limpeza, carrossel desliga o serviço subscrito e mensagens pertencem à arena original. O registo anterior é retirado antes de executar um callback, permitindo reagendamento legítimo |

O grupo adicional `driftkings.flash.battle.*` abrange atualmente mensagens de batalha e a verificação de libertação da tecla do minimapa. Não foram identificados callbacks de lobby abrangidos por esse prefixo.

Os caminhos de bootstrap, hangar, entrada em batalha, batalha ativa, morte/espectador, saída, batalhas consecutivas e replay foram revistos por inspeção. Não foram executados no cliente.

## F. Riscos pendentes

### Históricos, sem agravamento identificado pelas fases

| Gravidade | Localização | Causa e consequência | Proposta e validação necessária |
| --- | --- | --- | --- |
| Alta | `settings/panel/session.py`, `EditSession.apply()`, linha 83 na versão auditada | Falhas específicas de componentes ou efeitos externos ainda podem deixar módulos parcialmente aplicados; não existe rollback global | Definir preparação sem efeitos externos antes de uma transação mais ampla; validar falhas durante Apply/Save |
| Alta | `settings/panel/registry.py`, `ModRegistry.save()`, linha 389 | Gravações pública e secreta são separadas e podem ficar parcialmente concluídas | Estudar publicação conjunta recuperável; validar falhas de gravação |
| Alta | `settings/panel/registry.py`, `ModRegistry.apply_values()`, chamada a `external_apply` na linha 374 | A normalização externa pode deixar os valores apresentados e guardados pelo painel desfasados dos valores reais | Estabelecer leitura explícita dos valores normalizados; validar perfis e normalizações específicas |
| Média | `core/player_ratings.py`, assinatura de `_appliedCache` na linha 736 | A assinatura não inclui `minBattlesToShow` nem a revisão das tabelas. Baixar o limite pode não repor estatísticas anteriormente filtradas até nova aplicação/reset | Rever a invalidação separadamente; validar alterações do limite e atualização de referências. A política não foi alterada |

Estas localizações correspondem à versão auditada e podem mudar com edições posteriores. Os riscos não foram corrigidos nesta fase porque são históricos e exigem decisões ou validação fora do âmbito autorizado.

### Riscos fundamentados das alterações e hipóteses por validar

- **Fase 2 — risco de integração com extensões externas:** módulos que criem dependências através de callbacks anteriores precisam de validar a pré-validação antecipada. Não foi identificado esse uso nos módulos próprios revistos. A possibilidade não foi tratada como defeito reproduzido no WoT.
- **Fase 5 — comportamento nativo:** cancelamento de callbacks, destruição de views e substituição da arena em replay permanecem dependentes do cliente WG. É necessário confirmar que o trabalho legítimo continua a ser reagendado e que operações antigas não atingem a arena seguinte.
- **Outros mods:** a ordem de instalação dos hooks e o comportamento de terceiros continuam a exigir validação. Não foram removidas cadeias de hooks de outros mods.

## G. Checklist manual futura no WoT

Os cenários abaixo **não foram executados**. Esta checklist é apenas um guia de validação manual futura, não um ficheiro de testes executáveis.

- [ ] Entrada, saída e batalhas consecutivas, sem mensagens ou callbacks da arena anterior.
- [ ] Morte, transição para espectador e mudança de veículo observado.
- [ ] Replay: arranque, avanço, recuo, mudança de veículo e encerramento.
- [ ] Spotting, últimas posições e veículos destruídos.
- [ ] Zoom, resolução, escala, círculos, linhas e etiquetas do minimapa.
- [ ] Vehicle Markers: estados normal/Alt, vida, textos, estatísticas e cores.
- [ ] Player Panels: ordem dos jogadores, nomes, anonimização e visibilidade.
- [ ] Estatísticas locais, externas, indisponíveis e respetivas cores.
- [ ] Alteração do limite mínimo de batalhas e comportamento da cache.
- [ ] Configurações e perfis, incluindo criação, importação e exportação.
- [ ] Apply/Save/Cancel/Discard/Reset/Undo e preservação de alterações pendentes.
- [ ] Troca de idioma e captura de teclas.
- [ ] Updater: progresso, cancelamento, estados intermédios e mensagens de erro.
- [ ] Encerramento rápido e reabertura do painel.
- [ ] Falhas parciais de inicialização, gravação e criação de views.
- [ ] Ocultação de valores secretos nos payloads da interface.
- [ ] Compatibilidade com outros mods, incluindo ordem dos hooks e overrides de `Statistics.getColor()`.

## H. Conclusão

O código está **apto para iniciar validação funcional**, com os riscos acima identificados e uma regressão corrigida nesta auditoria.

Não foi identificado um problema novo de integração bloqueante que tenha permanecido sem correção por inspeção. Não se conclui, por isso, que o modpack esteja pronto para distribuição: a execução efetiva dos cenários no cliente WoT continua pendente.

Todas as alterações permanecem locais, sem commit nem push. Não foram iniciadas novas fases.
