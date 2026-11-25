# Driftkings SettingsLab — Progresso da reorganização

Para o estado atual da candidata de produção e os checkpoints desta fase, ver o [registo v0.1.7-beta.2](../releases/0.1.7-beta.2-readiness.md). Os checkpoints datados abaixo mantêm os resultados e as versões originais.

Criado em 2026-11-11, Europe/Lisbon. Referência normativa:
[plano diretor](DRIFTKINGS_REORGANIZATION_MASTER_PLAN.md).

> Estado atual — 2026-11-15: consultar a secção 43 para os commits C1–C6 já
> criados e a preparação de C7. As entradas anteriores são registos datados;
> contagens Git, gates pendentes e runtime nelas descritos pertencem à respetiva
> execução. C7 não foi criado; integração em `develop` permanece pendente.

Este ficheiro controla fases, decisões, bloqueios e aprovações. Não autoriza execução.
A redação inicial autorizou apenas os dois documentos Markdown. Em 2026-11-11,
o responsável autorizou a preservação integral e a worktree isolada da Fase 0.
A Fase 0 foi aceite expressamente pelo responsável e está `COMPLETE`.
A auditoria da Fase 1 foi aceite expressamente e está `COMPLETE` enquanto análise.
A auditoria da Fase 2 foi aceite e está `COMPLETE` enquanto análise.
A auditoria arquitetural da Fase 3 e a Opção B foram aceites pelo responsável.
A Fase 3 está `COMPLETE` no âmbito local: `FASE 3 — COMPLETE (LOCAL VALIDATION)`.
G1, G2 e G3 estão `COMPLETE` ao nível dos testes locais; validação CT pendente.
G4: `COMPLETE`, sem implementação; Opção A aceite, manter as factories atuais.
G5: `COMPLETE`, sem implementação; `OPTION A — KEEP EXISTING SHARED HELPERS`.
G6: `COMPLETE` no âmbito local autorizado; resolução runtime CT pendente.
G7 aceite localmente com a aceitação da Fase 3; todas as pendências CT permanecem.
Fase 4: auditoria e F4-G1a/G1b/G2 aceites localmente; F4-G3
`COMPLETE (LOCAL AUDIT)`; F4-G3.1 `COMPLETE (LOCAL CHARACTERIZATION)`;
F4-G3.2/G3.3 `COMPLETE (LOCAL VALIDATION)`; F4-G5 consolidado.
`FASE 4 — COMPLETE (LOCAL VALIDATION; CT PENDING)`.
Seis renomeações AS3, verificação binária e correções B/C1 concluídas localmente.
Fase 5 `COMPLETE (LOCAL VALIDATION; CT PENDING)`; F5-G3 aceite e F5-G4 consolidado.
Fase 6 `COMPLETE (LOCAL VALIDATION; CT PENDING)`; F6-G1.1 aceite como diagnóstico parcial; F6-G2 `PASS`; F6-G3 `PASS`; F6-G4 `PASS` (estático e isolado; runtime pendente); F6-G5 e F6-G5.1 `PASS` (acorn instalado; três baselines aprovados; build experimental por autorizar).
Fase 7 `IN_PROGRESS`; F7-G1.1 build/instalação PASS; F7-G2 funcional confirmado pelo utilizador.
F7-G3 aceite expressamente pelo responsável no pedido F7-G4A; C1–C6 criados localmente. C7 em preparação documental; integração pendente (secção 43).

## 1. Contexto confirmado e limites da confirmação

| Item | Registo nesta redação |
|---|---|
| Repositório | `dkruben/Driftkings_SettingsLab` |
| Branch | `feature/wot-2.4.2-ct` |
| HEAD | `bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3` |
| Working tree antes da documentação | 44 caminhos pendentes, listados abaixo |
| Staging | Vazio |
| Beta.9 | Pacote produzido e instalado com SHA-256 idêntico |
| SHA-256 beta.9 | `22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9` |
| Catálogo | 20 nativos / 0 OpenWG / 2 janelas próprias do lobby |
| HUD | 9 cartões/modelos independentes; uma janela Wulf/Gameface partilhada |
| Build, auditoria e instalação | Aprovação técnica documentada nos registos beta.9 existentes |
| Runtime CT beta.9 | Pendente; nenhuma aprovação presumida |
| Teste sem OpenWG | Pendente; nenhuma dependência desativada por esta redação |
| Servidor CT | Indisponibilidade comunicada; disponibilidade não sondada nesta tarefa |
| Divergências do contexto indicado | Nenhuma material identificada na conferência mínima |

Pacote: `build/experiments/20261111T115234Z-1d26e1e9/output/driftkings.wotmod`.
Instalado: `C:/Games/World_of_Tanks_CT/mods/2.4.2.0 Common Test/driftkings.wotmod`.
Registos: `diagnostics/install-record.json`, `package-audit.json` e
`packaged-contracts.log` dentro desse experimento. Não pressupor que artefactos
ignorados pelo Git sejam transportados para outra máquina ou worktree.

A regressão anterior teve uma expectativa sazonal desatualizada nas execuções
completas de 936 testes Python 3 (um ignorado) e 691 Python 2.7. A expectativa foi
corrigida e o ficheiro passou nos oito testes em ambos; não houve segunda regressão
completa. O registo também indica 29 suites frontend e verificações estáticas aprovadas.
Os dez contratos direcionados do pacote beta.9 passaram. Nenhum teste foi reexecutado
para redigir este plano, e nada disto equivale a `CT RUNTIME PASS`.

A conferência desta documentação não substitui o inventário recuperável e a estratégia
de isolamento a aprovar na Fase 0. O Git pode mudar entre sessões.

## 2. Quadro de fases

| Fase | Objetivo | Estado | Autorização de análise | Autorização de implementação | Próxima condição |
|---|---|---|---|---|---|
| 0 | Baseline e preservação | `COMPLETE` | Concedida no pedido Fase 0 — Baseline Analysis | Estratégia C limitada autorizada e baseline aceite expressamente | Aceitação registada na secção 10 |
| 1 | Inventário e nomenclatura global | `COMPLETE` | Auditoria aceite expressamente no pedido Fase 1 — Encerramento documental / Fase 2 | Não concedida; apenas mapa conceptual aceite | Implementação distribuída por futuras fases e autorizações delimitadas |
| 2 | Auditoria e organização dos assets | `COMPLETE` | Auditoria aceite no pedido Fase 3 | Não concedida; orientação conceptual apenas | Intervenções físicas continuam dependentes de autorização específica |
| 3 | Reorganização Gameface/Wulf | `COMPLETE` (LOCAL VALIDATION) | Auditoria e G1–G7 aceites localmente | Âmbitos autorizados concluídos | Host/R/input/lifecycle/independência CT pendentes para Fase 7 |
| 4 | Reorganização Flash/Scaleform | `COMPLETE` (LOCAL VALIDATION; CT PENDING) | Auditoria e caracterização aceites | G1a/G1b/G2/G3.2/G3.3 aceites localmente; consolidação G5 autorizada | Riscos conhecidos diferidos para Fase 7; Fase 5 depende de nova autorização |
| 5 | Botão Driftkings e FooterLauncher | `COMPLETE` (LOCAL VALIDATION; CT PENDING) | F5-G1 aceite; F5-G2 aprovado visualmente | F5-G3 aceite localmente; consolidação F5-G4 autorizada | SVG/filtros/footer e abertura runtime pendentes para Fase7; Fase6 não iniciada |
| 6 | Compatibilidade internacional | `COMPLETE (LOCAL VALIDATION; CT PENDING)` | F6-G1.1 diagnóstico parcial aceite | F6-G2 preflight CT autorizado | F6-G2 PASS; F6-G3 PASS estático/isolado (carrossel e tooltip CT996); F6-G4 PASS estático/isolado (SWF marcadores CT996); runtime pendente; F6-G5.1 PASS: acorn instalado, três baselines aprovados, toolchain pronta; Fase 6 concluída localmente, CT pendente; outras regiões fora do âmbito |
| 7 | Validação e consolidação | `IN_PROGRESS` | F7-G3 aceite; F7-G4A e preparação documental C7 autorizadas | C1–C6 criados com autorizações individuais; beta.10 e runtime históricos preservados | C7 ainda não criado; criação, integração em develop e publicação exigem autorização própria; ver secção 43 |

Estados permitidos: `PENDING`, `IN_ANALYSIS`, `AWAITING_APPROVAL`,
`APPROVED_FOR_IMPLEMENTATION`, `IN_PROGRESS`, `VALIDATION_PENDING`, `BLOCKED`,
`COMPLETE`, `REJECTED`. Significados e fluxo encontram-se no plano diretor.
`COMPLETE` exige critérios cumpridos e confirmação expressa do responsável.
Um relatório técnico PASS não aprova a fase nem permite avançar automaticamente.

## 3. Registo de decisões

| ID | Data | Fase | Assunto | Proposta | Decisão/evidência | Impacto | Estado de implementação |
|---|---|---|---|---|---|---|---|
| D-001 | 2026-11-11 | Transversal | Âmbito desta sessão | Criar plano e progresso | Responsável autorizou somente os dois Markdown no pedido «Criar o plano diretor de reorganização — documentação apenas» | Nenhuma implementação autorizada | Documentação produzida; aceitação do responsável pendente |
| D-002 | 2026-11-11 | Transversal | Gates de execução | Uma fase de cada vez; análise separada de implementação | Regra explícita do mesmo pedido | PASS não é autorização; exigir decisão seguinte | Regra documentada; nenhuma fase iniciada |
| D-003 | 2026-11-11 | 1 | Nomes HUD candidatos | Avaliar candidatos descritos no plano | Não há mapeamento definitivo aprovado | Evitar renomeações e mudanças de configurações por estética | Não implementado |
| D-004 | 2026-11-11 | 2 | Destino Sixth Sense | Avaliar `gui/icons/driftkings/sixth_sense/` | Proposta do responsável sujeita ao carregador real | IDs numéricos e persistência exigem mapeamento | Não implementado |
| D-005 | 2026-11-11 | 3 | Janela HUD | Preservar janela única e modelos independentes | Requisito explícito do responsável | Nenhuma proposta de nove janelas ou transporte paralelo | Restrição registada; sem alteração |
| D-006 | 2026-11-11 | 5 | SVG e exclusividade | Visual aprovado antes da integração; acesso ModsListAPI funcional oculta botão nativo | Requisito explícito; desenho e implementação ainda não aprovados | Não afetar outros mods nem ocultar ModsListAPI globalmente | Não implementado |

Novas entradas devem conter data, fase, assunto, proposta, decisão literal ou referência,
evidência, impacto e estado. Não converter pedidos de análise em aprovações de implementação.
Não inventar datas, autorizações ou resultados runtime de sessões anteriores.

## 4. Decisões pendentes e bloqueios potenciais

| ID | Fase | Decisão ou condição em falta | Evidência atual | Condição de desbloqueio |
|---|---|---|---|---|
| P-001 | 0 | Estratégia de branch/worktree e preservação integral | Estratégia C implementada, verificada e aceite expressamente | Resolvido; evidências na secção 9 e aceitação na secção 10 |
| P-002 | 1 | Nomes definitivos e eventuais incompatibilidades | Convenções e nomes funcionais aceites na secção 11 | Implementação exige mapas exatos e autorização própria; não inclui transições de configurações |
| P-003 | 2 | IDs Sixth Sense e resolução do novo caminho | README atual declara nomes numéricos como IDs de seleção | Inventário, mapa ID/configuração e teste do carregador |
| P-004 | 3 | Ordem dos patches lifecycle e separação de helpers | Achados estáticos registados no plano | Caracterização e proposta por patch; confirmação runtime quando exigida |
| P-005 | 3 | Composição estática vs. alternativa do host | Composição estática gerada é a referência | Benefício demonstrado e aprovação; sem loader paralelo por defeito |
| P-006 | 5 | SVG final e prova de acesso ModsListAPI | Nenhum SVG criado; visible atual não verifica acesso funcional | Aprovação visual e contrato funcional demonstrado |
| P-007 | 6 | Snapshots e perfis EU/NA/ASIA/CN/CT | Só CT #995 confirmado nesta redação | Documentos e hashes da versão alvo; evidência por superfície |
| P-008 | 7 | Runtime e isolamento sem OpenWG | CT indisponível segundo o responsável; testes pendentes | Disponibilidade e autorização própria; nunca marcar PASS por inferência |
| P-009 | 7 | Consolidação Git e eventual release | Nenhum commit/publicação autorizado | Confirmação do responsável por operação e âmbito |

Estes itens não colocam automaticamente todas as fases em `BLOCKED`.
Quando uma fase estiver autorizada e o pré-requisito se tornar impeditivo,
registar o bloqueio concreto, o impacto e a condição de desbloqueio nessa fase.

## 5. Ficha a preencher em cada execução futura

Copiar/preencher a ficha apenas para a fase efetivamente autorizada; não abrir fases
seguintes por iniciativa própria.

```text
Fase e subetapa:
Estado antes / depois:
Data e responsável:
Objetivo e âmbito:
Ficheiros envolvidos:
Pré-requisitos e estado real de Git/artefactos:
Riscos e contratos protegidos:
Autorização de análise (referência exata):
Proposta apresentada e decisão:
Alterações autorizadas (incluindo limites):
Build/instalação/commit autorizados separadamente? Referências:
Critérios de aceitação:
Testes exigidos / executados / não disponíveis:
Resultados e evidências:
Divergências e bloqueios:
Procedimento de rollback e verificação:
Relatório final e pendências:
Confirmação do responsável:
Autorização seguinte: nenhuma, salvo referência explícita:
```

## 6. Histórico de autorizações e execução

| Data | Evento | Resultado | Aprovação |
|---|---|---|---|
| 2026-11-11 | Leitura do pedido e conferência mínima do contexto | Branch/HEAD, 44 caminhos, staging, catálogo e hashes beta.9 compatíveis | Permitido apenas para redigir o plano |
| 2026-11-11 | Criação do plano diretor e deste registo | Oito fases documentadas em `PENDING`; nenhuma implementada | Autorizada documentação; aceitação final ainda pendente |

O registo inicial acima é histórico. A autorização posterior da Fase 0 e os seus
resultados estão na secção 9. Não há autorização de renomeação, movimentação de
assets de produção, build, instalação, remoção de dependência ou commit.

## 7. Snapshot dos 44 caminhos anteriores à documentação

Este snapshot é referência de conferência, não um inventário permanente nem uma
autorização para alterar os caminhos. `M`: modificado; `D`: removido na working tree;
`??`: não rastreado. As remoções já existiam antes deste plano.

| Estado | Caminho |
|---|---|
| M | `build_data/build_config.json` |
| M | `build_data/components.json` |
| M | `build_tools/generate_ui_catalog.py` |
| D | `mod/res/gui/gameface/mods/driftkings/panel_gameface/halloween_tab.js` |
| M | `mod/res/gui/gameface/mods/driftkings/panel_gameface/ratings.js` |
| M | `mod/res/gui/gameface/mods/driftkings/shared/bootstrap.js` |
| M | `mod/res/scripts/client/driftkings/core/mode_adapters.py` |
| M | `mod/res/scripts/client/driftkings/flash/battle/player_ratings.py` |
| M | `mod/res/scripts/client/driftkings/gameface/battle/panel_gameface.py` |
| M | `mod/res/scripts/client/driftkings/gameface/core.py` |
| M | `mod/res/scripts/client/driftkings/interface_catalog.py` |
| M | `tests/build/test_native_carousel_catalog.py` |
| M | `tests/build/test_native_clock_catalog.py` |
| M | `tests/build/test_native_crew_catalog.py` |
| M | `tests/build/test_native_hangar_marks_catalog.py` |
| M | `tests/build/test_native_results_source.py` |
| M | `tests/build/test_own_window_catalog.py` |
| D | `tests/frontend/battle/test_halloween_tab.js` |
| M | `tests/frontend/battle/test_own_battle_window.js` |
| D | `tests/runtime/battle/test_halloween_tab.py` |
| M | `tests/runtime/battle/test_halloween_panel.py` |
| M | `tests/runtime/battle/test_mode_adapters.py` |
| M | `tests/runtime/battle/test_own_battle_window.py` |
| M | `tests/runtime/battle/test_team_rosters.py` |
| M | `tests/runtime/lobby/test_native_carousel.py` |
| M | `tests/runtime/lobby/test_native_clock.py` |
| M | `tests/runtime/lobby/test_native_crew_runtime.py` |
| M | `tests/support/__init__.py` |
| M | `tests/support/rosters.py` |
| ?? | `build_data/patches/native_document_crewdetails_0_2.4.2_ct.json` |
| ?? | `build_data/patches/native_document_crewdetails_1_2.4.2_ct.json` |
| ?? | `build_data/patches/native_document_crewdetails_2_2.4.2_ct.json` |
| ?? | `build_data/patches/native_document_crewdetails_3_2.4.2_ct.json` |
| ?? | `build_data/patches/native_document_footerlauncher_0_2.4.2_ct.json` |
| ?? | `build_data/patches/native_document_hangarheaderoptions_0_2.4.2_ct.json` |
| ?? | `build_data/patches/native_document_marksonguntechtree_0_2.4.2_ct.json` |
| ?? | `build_data/patches/native_document_profileratings_0_2.4.2_ct.json` |
| ?? | `build_data/patches/native_document_ratingplayers_0_2.4.2_ct.json` |
| ?? | `docs/openwg-native-migration.md` |
| ?? | `tests/build/test_native_document_catalog.py` |
| ?? | `tests/frontend/battle/test_native_rating_tab.js` |
| ?? | `tests/frontend/lobby/test_native_documents.js` |
| ?? | `tests/runtime/battle/test_native_rating_tab.py` |
| ?? | `tests/runtime/lobby/test_native_documents.py` |

Resultado esperado desta tarefa documental: esses 44 caminhos intactos, mais apenas
os dois ficheiros em `docs/plans/`, sem staging ou commits. O Git pode resumir a pasta
untracked numa linha; usar `--untracked-files=all` para contar os dois documentos.

## 8. Próxima ação

Aguardar aceitação da auditoria F4-G3, registada na secção 26.
Não implementar correções nem iniciar F4-G4/G5/Fase 5. CT reservado à Fase 7.
A Opção B continua um alvo aprovado, sem autorização para reorganizar o host.

## 9. Fase 0 — Preservação e isolamento executados

Data: 2026-11-11, Europe/Lisbon. Estado: `VALIDATION_PENDING`.
Autorização: pedido «FASE 0 — Preservação integral e criação de worktree isolada»,
com a decisão literal «implementação limitada da estratégia C, aprovada após a análise da baseline».
Âmbito autorizado: snapshot externo verificável, bundle Git, dados privados protegidos,
branch/worktree, transporte fiel da baseline e atualização documental só nesta worktree.
Não foram autorizados commits, builds, instalações ou início da Fase 1.

### Baseline e evidências

- Original: `E:/Wot_Mods_/Drift_Kings_ModPack/Driftkings_SettingsLab`.
- Branch original: `feature/wot-2.4.2-ct`; HEAD `bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3`.
- Upstream conhecido: `origin/feature/wot-2.4.2-ct`, 0 atrás / 3 à frente; sem fetch.
- 46 caminhos: 26 modificados, 3 removidos e 17 untracked; staging vazio.
- Preservação: `E:/Wot_Mods_/Drift_Kings_ModPack/Driftkings_Preservation/phase0-20261111T214846Z-10b23615`.
- Snapshot: 8.787 ficheiros, 674.601.743 bytes; inclui fontes, ignorados, todos os
  experimentos/backups, evidências, `build/unified`, `build/previous` e `build/debug`.
- `git/history.bundle`: todas as refs; `git bundle verify` PASS; HEAD local recuperável.
- SHA-256 bundle: `409f2e2499025a04aae50f80526eecf416cd7a8b168e63d13b05ad6c235a6280`.
- `manifests/files.json`: caminho relativo, tamanho, SHA-256 e estado; dados privados
  têm manifesto separado protegido, sem conteúdo divulgado neste documento.
- SHA-256 `files.json`: `3d33cb4be09b103d34faab486734627dfdc32d84ef059127b79f2b429112cef2`.
- Outros registos: `removed.json` (3 remoções), `directories.json`, `state.json`,
  `ct-files.json` (97 ficheiros), `worktree-verification.json` e `checksums.json`.
- Índice e referências preservados; hashes de todos os ficheiros copiados comparados
  com origem e snapshot. Dois ficheiros privados separados; ACL limitada ao utilizador
  atual e SYSTEM; nenhuma chave transportada para a worktree ou adicionada ao Git.

### Worktree e verificações

- Branch: `reorganization/settingslab`.
- Worktree: `E:/Wot_Mods_/Drift_Kings_ModPack/Driftkings_SettingsLab_reorganization`.
- HEAD exatamente igual à baseline. 1.094 ficheiros existentes de fontes/non-ignored
  comparados byte a byte; os mesmos 46 caminhos antes da atualização deste documento.
- Três remoções reproduzidas; staging vazio; catálogo 20 nativos / 0 OpenWG /
  2 janelas próprias do lobby; dois documentos do plano presentes.
- A cópia física exata provocou inicialmente avisos de estado do índice de checkout
  para ficheiros sem diff. Foi transportado o índice preservado para a worktree,
  após confirmar igualdade das entradas staged, sem alterar índice ou fontes originais.
- Nenhum ignorado transportado: nesta etapa não há build nem necessidade comprovada
  de toolchain local, caches ou outputs. Esses recursos continuam recuperáveis no snapshot.
- Única divergência posterior autorizada: este documento de progresso na worktree.
  O plano diretor e os restantes ficheiros continuam iguais à origem.
- Original: branch, HEAD, índice, 46 estados e hashes de 8.787 ficheiros preservados.
  Beta.9, backups e `build/unified` intactos. CT: 97 ficheiros em mods/res_mods
  com nomes e hashes idênticos, incluindo dependências externas; nenhuma operação no cliente.
- Beta.9 produzida, preservada e instalada: SHA-256
  `22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9`.
- Verificações: inventário, hashes, bundle, estados Git e leitura estática do catálogo;
  sem geradores, formatadores, testes completos, builds ou instalações.

### Recuperação, limites e aprovação

Recuperar sempre para um diretório novo: verificar manifestos e bundle; clonar o
bundle, selecionar o HEAD indicado e restaurar os ficheiros físicos preservados,
com as três remoções. Recuperar dados privados separadamente e só quando necessários.
Comparar todos os hashes e o staging antes de utilizar a recuperação. Não executar
reset/clean sobre o original. Para abandonar a reorganização, deixar a worktree
intacta e voltar ao original; remoção ou integração futuras exigem decisão própria.

Riscos residuais: snapshot no mesmo disco físico; worktrees partilham o armazenamento
Git, embora o bundle externo seja independente; mudanças futuras têm de ser reconciliadas
com os 46 caminhos locais originais. A proteção privada é por ACL, sem alegar cifragem.
Validação runtime beta.9 e independência sem OpenWG continuam pendentes.

Resultados técnicos: `PRESERVATION PASS`; `WORKTREE ISOLATION PASS`;
`ORIGINAL BASELINE INTEGRITY PASS`. Confirmação do responsável: pendente.
Próxima autorização necessária: aceitar expressamente a baseline da Fase 0;
qualquer análise da Fase 1 exige autorização específica. Nenhuma fase seguinte iniciada.

## 10. Aceitação da Fase 0 e análise da Fase 1

Data: 2026-11-11, Europe/Lisbon.
Aceitação expressa do responsável, em resposta à pergunta de confirmação da baseline
e do relatório de preservação/isolamento: **«Confirmo a aceitação da Fase 0»**.
A Fase 0 passa de `VALIDATION_PENDING` a `COMPLETE`; isto não aprova runtime CT
nem independência sem OpenWG. A secção 9 conserva o estado histórico da entrega.

### Ficha de execução da Fase 1

- Estado: `PENDING` → `IN_ANALYSIS` → `AWAITING_APPROVAL`.
- Autorização: pedido «FASE 1 — Inventário e Nomenclatura Global», análise exclusivamente,
  sem implementação; pré-requisito de aceitação da Fase 0 satisfeito pela confirmação acima.
- Objetivo: inventariar nomes por tecnologia e propor normalização fundamentada,
  distinguindo nomes físicos, identidades, recursos, configurações e contratos externos.
- Ambiente: apenas `reorganization/settingslab`, na worktree de reorganização,
  HEAD `bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3`.
- Estado Git inicial/final: 46 caminhos, 26 M / 3 D / 17 untracked; staging vazio.
- Âmbito lido: fontes Python, catálogo, adaptadores/modelos Wulf, JS/CSS/HTML,
  AS3/Scaleform, configurações, assets, geradores/manifestos/patches, instalador, testes e docs.
- Inventário: 1.094 ficheiros existentes; 465 Python, 88 JS, 19 CSS, 22 HTML,
  65 AS3, 112 JSON e 36 Markdown. Produção: 308 Python, incluindo 29 Gameface
  e 39 Flash; Gameface: 55 JS. Sem artefactos históricos copiados para esta worktree.
- Nomes inventariados por leitura estática: 4.988 declarações Python (617 classes,
  4.371 funções/métodos), 65 classes/interfaces AS3, 373 funções/acessores AS3,
  592 chaves JSON distintas nos 53 defaults canónicos e 22 identidades Gameface.
  As contagens são categorias de inventário, não nomes únicos globais nem prova runtime.
- Catálogo reconfirmado: 9 own_window, 6 native_document, 4 native_user_missions,
  1 native_battle_results e 2 janelas do lobby. Janela partilhada e nove modelos preservados.
- Referência beta.9: hash e evidências da Fase 0 reutilizados; não se repetiu auditoria
  completa de hashes/artefactos, regressão ou validação do cliente.

### Resultado e decisões pendentes

- Conservar as nove configurações HUD: battle_statistics, vehicle_health,
  battle_performance, high_caliber_progress, battle_marks_of_excellence,
  target_information, penetration_indicator, shell_flight_time e aiming_countdown.
- Nome funcional preferido de MainGun: high_caliber_progress, coerente com cálculo,
  configuração e texto «Progresso de Alto Calibre»; não main_gun.
- TeamStrength: team_strength como nome funcional; possível alinhamento de módulos
  condicionado ao host/gerador, conservando battle_statistics como configuração.
- HUD de eficiência e resultados pós-batalha devem ter nomes internos distintos;
  não unificar os IDs DriftkingsBattleEfficiency e driftkingsbattleEfficiency.
- Candidatos: high_caliber_gameface → high_caliber_progress, main_gun.js/css →
  high_caliber_progress.js/css; marks_panel.js → ui_presentation.js (renomeação
  apenas, sem extração); panel_gameface → player_ratings; lobby/main.py → hangar_clock.py.
- Classes AS3 próprias em minúsculas contrastam com PascalCase; propor nomes
  descritivos, preservando linkage, classes nativas e exports até mapa completo aprovado.
- carroucel → carousel é uma correção fundamentada, mas envolve macros/configurações
  persistidas, regex, templates, instalador/testes e embalagem; não é uma troca textual simples.
- Sixth Sense: 0.png–9.png são IDs persistidos (defaultIconName), não índices da lista.
  Manter IDs; nomes visuais descritivos dependem da Fase 2. Avaliar o destino
  gui/icons/driftkings/sixth_sense/ sem o aprovar, mudar ou assumir suporte do carregador.
- Preservar chaves camelCase atuais e aliases legacy.*; cada transição exige decisão,
  mapa de consumidores e eventual migração conjunta de configurações.
- Não editar manualmente model.html gerado, bloco de catálogo do bootstrap,
  componentcatalog.as ou default_values.py. Usar os geradores existentes quando autorizado.
- Contratos protegidos: coui:// e recursos R; payload/DriftkingsUI, comandos Wulf;
  overrides e métodos DAAPI; nomes de recursos do cliente; classes linkage dos painéis;
  SWC/SWF de referência; nomes e estrutura exigidos por ferramentas externas.

### Verificação, riscos e próximos passos

Somente leituras Git, inventário, AST/JSON e pesquisas direcionadas; sem testes completos,
builds, geradores ou alterações de produção. Único ficheiro editado: este progresso.
Relatório detalhado entregue diretamente na resposta, secções A–J; nenhum novo documento.

Riscos: imports dinâmicos, globais JS/owners, referências em configs/macros, sensibilidade
a maiúsculas, linkage AS3 e hashes de patches por cliente. Referências externas e
comportamento dos carregadores não ficam provados por pesquisa estática. Runtime CT
e independência sem OpenWG permanecem pendentes.

Implementação futura proposta por grupos independentes: helpers/imports internos;
Alto Calibre; módulos de superfície; classes AS3 próprias (Fase 4); paths de assets
e Sixth Sense (Fase 2); configurações apenas por necessidade e aprovação separadas.
Cada grupo requer mapa exato, testes direcionados, geradores autorizados quando aplicável
e runtime para recursos/linkage. Rollback por grupo para diretório novo a partir
do snapshot Fase 0, incluindo configuração compatível; nunca reset/clean do original.

Veredicto da análise: `FASE 1 — NOMENCLATURE AUDIT: COMPLETE`.
Estado da fase: `AWAITING_APPROVAL`; confirmação do responsável pendente.
Nenhuma renomeação, commit, build, instalação ou Fase 2 autorizada por este relatório.

## 11. Encerramento da Fase 1 e auditoria de assets

Data do registo: 2026-11-12, Europe/Lisbon. Autorização: pedido
«FASE 1 — Encerramento documental / FASE 2 — Auditoria global dos assets»,
DOCUMENTAÇÃO + ANÁLISE, SEM IMPLEMENTAÇÃO.

### FASE 1 — AUDITORIA DE NOMENCLATURA ACEITE

O responsável declarou: «O responsável aceitou o resultado técnico da auditoria
de nomenclatura». A Fase 1 passa a `COMPLETE` enquanto etapa de auditoria e
aprovação conceptual. O registo da secção 10 descreve a entrega anterior.

Convenções aceites: diretórios/ficheiros internos em snake_case quando permitido;
classes Python/AS3 em PascalCase; métodos/propriedades AS3 em camelCase;
assets próprios em minúsculas/snake_case; preservar configurações adequadas
e contratos externos/identificadores técnicos até migração especificamente autorizada.

Nomes funcionais aceites para futura implementação: team_strength, vehicle_health,
battle_efficiency_hud, high_caliber_progress, battle_marks_of_excellence,
target_information, penetration_indicator, shell_flight_time e aiming_countdown.

Decisões:
- panel_gameface → player_ratings: candidato aceite para implementação futura.
- carroucel → carousel: candidato aceite, sujeito ao mapa de referências.
- Classes AS3 próprias: normalização reservada à Fase 4.
- marks_panel.js → ui_presentation.js: proposta adiada; reavaliar na Fase 3.
- Identificadores Wulf e comandos: preservar inicialmente.
- battle_statistics/model.html: reorganização apenas na Fase 3, pelo gerador.
- Sixth Sense: conservar IDs de seleção independentemente de futuros nomes físicos.

Nenhuma destas decisões autoriza executar renomeações nesta sessão.

### Ficha da Fase 2

Estado: `PENDING` → `IN_ANALYSIS` → `AWAITING_APPROVAL`.
Objetivo: inventariar recursos gráficos, metadados, consumidores, duplicados e
propostas de organização/otimização, sem alterar produção.
Ambiente: worktree Driftkings_SettingsLab_reorganization, branch reorganization/settingslab,
HEAD bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3.
Git inicial/final: 46 caminhos (26 M / 3 D / 17 untracked), staging vazio.

Âmbito: imagens em mod/res/gui/maps, Gameface, aimingangles, objetos DDS, fontes,
fontes Flash/embeds e instalador; catálogo, manifestos, CSS/JS, Python, AS3 e
configurações relevantes. Reutilizados os relatórios anteriores; sem nova
auditoria do histórico ou dos artefactos beta.9.

### Inventário e verificações

- 186 ficheiros gráficos/fontes, 14.163.289 bytes: 112 PNG, 65 SVG, 2 DDS,
  1 JPEG, 1 ICO e 5 TTF. Não inclui áudio, SWC nem recursos internos de SWF.
- Recursos Gameface locais: 64; mapas gerais: 41; aimingangles: 48;
  fontes: 5; instalador: 25 (21 previews e 4 branding); DDS: 2;
  PNG de fallback incorporado por AS3: 1.
- SHA-256 e metadados lidos para todos os 186. Bitmaps decodificados sem erro,
  SVG analisados como XML, fontes abertas para ler nomes internos.
- Visualizados os 112 PNG e o JPEG. ICO/DDS: metadados/decodificação apenas.
  SVG: estrutura e consumidores inspecionados, sem visualização renderizada;
  a ferramenta de imagem não suporta diretamente SVG. Não foram convertidos.
- SVG: sem scripts, hrefs externos ou filtros encontrados; usam formas básicas
  e gradientes. Compatibilidade real Gameface continua por verificar.
- 29 referências CSS locais resolvidas, nenhuma em falta nesse conjunto.
  Não equivale a resolução exaustiva de referências dinâmicas ou recursos do cliente.
- Quatro SVG sociais embebidos em app.js coincidem com os ficheiros canónicos,
  após trim. São cópias intencionais para hover/tema/fallback, cobertas por teste
  existente de cabeçalho (lido, não executado); não propor remoção automática.
- Todos os ficheiros da worktree conservaram tamanho/mtime durante a leitura
  até à atualização autorizada deste progresso; hashes dos assets conferidos no fim.

### Sixth Sense

Dez ícones confirmados, IDs 0–9. Todos transparentes (alpha mínimo 0, máximo 255).
ID 1: 194×210; restantes: 180×180.
O seletor usa defaultIconName numérico, metadata optionValues e descoberta
ResMgr.openSection('gui/maps/icons/sixthsense/').
controls_schema.images constrói os previews nesse mesmo caminho.
O AS3 constrói '../../gui/maps/icons/sixthsense/' + ID + '.png'.
userIcon continua separado, com loader local e caminho configurável em
mods/configs/driftkings/sixthsense/SixthSenseIcon.png.

Achado estático: o bitmap ID 1 não é quadrado, mas updateParams atribui a mesma
largura e altura a todos os ícones, causando alteração da proporção.
Não corrigido; exige decidir entre preservar aspeto atual, ajustar asset ou loader.
O destino gui/icons/driftkings/sixth_sense/ exige adaptar seletor, metadados,
ResMgr, AS3, manifesto e testes, conservando IDs/custom icons.

| ID | PNG atual | Dimensões | Bytes | SHA-256 | Nome descritivo candidato |
|---|---|---|---:|---|---|
| 0 | 0.png | 180×180 | 36427 | `93bfd80157e8a21f5d24e2a6ef0da1aea2366ea8c957ddf94f91ba584f27790e` | `red_chili_gear.png` |
| 1 | 1.png | 194×210 | 163528 | `5824a0d7d4a3ff0470fba013814e3e1b896d96b1d23fd218a7772bdb13f49e3a` | `dark_helmet.png` |
| 2 | 2.png | 180×180 | 6808 | `0f49ef2a7aabf880c0ad11de7e30eaf76fd9f78e4bb0081cfd614aaaee92a6b5` | `orange_light_bulb.png` |
| 3 | 3.png | 180×180 | 13870 | `eb8016cbdd7db376aa0a570bb681377dec2e8ab17d870d669b1118749f0cb2e9` | `fiery_eye.png` |
| 4 | 4.png | 180×180 | 11397 | `e2b890eb3e8bbbb08bcc8f06e2758e8bc94a26f1f38059c58033774e366a1376` | `purple_energy_orb.png` |
| 5 | 5.png | 180×180 | 6896 | `d95b49597abd83489bb9a6ee37b6c1f36160e96a6ed49a01dff1ba383f2ffbd1` | `saxon_wot_badge.png` |
| 6 | 6.png | 180×180 | 9759 | `b2c712062d1612208ca43a98589c9ca9cb95a79b5b418f8faa58afb85609e882` | `yellow_goggled_character.png` |
| 7 | 7.png | 180×180 | 13868 | `cecc93b3c95ebeefc5a7e8c9e038b328ac8f9912003176713dc94d77cf37d25f` | `flaming_skull.png` |
| 8 | 8.png | 180×180 | 13161 | `c0cd966ade902745b7a0ac2b964a0c2cc024a87f37ff76e24429fe0587da37ca` | `golden_flash.png` |
| 9 | 9.png | 180×180 | 10960 | `b291c81a983d2c62317dc9ded0e52eddf0f48044ad9627684539f482401dcebe` | `fire_ice_ring.png` |

Nomes apenas descritivos da imagem observada; nenhum ficheiro/ID foi alterado.

### Duplicados e oportunidades

Três grupos SHA-256 idênticos:
- settings_window/assets/icon_gear.svg e assets/mods/general.svg:
  1d3d88590f1b7147710eaaf4b5bcb0ae0ef9afc102e13135eccafadea21f2999.
  Fallback dinâmico iconFor e ícone legacy.main: ambos têm consumidores.
- aimingangles/6/bottom.png e bottom_limit.png:
  27275fa9b9e178d9d03fe9ca1542a57364ce2ed3423f2b7b330a51abbcb9f6ba.
- aimingangles/6/top.png e top_limit.png:
  5442ef7bd72e2883c8e82fb22825d01b8a5f215524b7d7b0dd0638944be4b78f.
  Os dois pares pertencem a estados normal/limite construídos dinamicamente
  por gun_traverse_limits.py; não remover caminhos sem resolver esses contratos.
Economia bruta potencial de consolidar uma cópia por grupo: 1.311 bytes;
não implica a mesma economia no pacote ZIP.

Molduras vehicle_health: 3.760.086 bytes em quatro PNG; bastion/ion/vanguard
têm 1536×1024 e frame clássico 960×156. Variantes distintas, não duplicadas.
health_bar.js guarda canvas/crop/slot explicitamente e é partilhado pelo preview;
qualquer corte/redimensionamento exige geometria e testes conjuntos.

Previews do instalador: 21 PNG, todos 960×540, 6.634.482 bytes, opacos,
visualmente ilustrativos. battle_performance.png representa FPS/ping e
battle_statistics.png contadores individuais; desalinhamento com as funções
atuais de eficiência e força das equipas. Propor revisão editorial após aprovação.

header_tank.jpeg: referência histórica encontrada em docs/STATUS.md;
CSS atual usa header_driftkings.png. POTENTIALLY_UNUSED, sem autorização de remoção.
autoaimopt.svg: não é selecionado pelo mapa MOD_ICONS atual (usa autoaim);
POTENTIALLY_UNUSED, não prova de inutilidade de todos os consumidores.
big.png e dot-lost/dot-spotted: utilização dinâmica não totalmente demonstrada;
DYNAMIC_USAGE_UNCONFIRMED. Não eliminar por ausência de literal.
icon_gear/icon_puzzle/icon_speaker têm construção dinâmica em iconFor:
não são obsoletos por falta de referência literal ao nome completo.

### Organização e plano propostos, sem execução

- KEEP: assets Gameface específicos junto do componente; stars em shared/assets;
  fontes e aliases existentes; ícones sociais simples; DDS/modelos dependentes.
- MOVE condicionado: mapas próprios para gui/icons/driftkings/{sixth_sense,battle,
  garage,shared}, só após demonstrar resolução por loader e mapear persistência.
  Nem os modelos DDS nem todos os assets Gameface pertencem a esse destino.
- RENAME condicionado: carroucel → carousel; nomes abreviados/concatenados
  conforme convenção aceite, sem misturar alterações de IDs ou algoritmos.
- OPTIMIZE candidato: PNG grandes de vehicle_health e branding/previews,
  primeiro sem alterar pixels, alpha ou dimensões; nenhuma poupança medida.
- REPLACE condicionado: futuros previews semanticamente corretos e botão SVG
  simples do FooterLauncher, este último apenas no âmbito futuro da Fase 5.
- POTENTIALLY_UNUSED/DYNAMIC_USAGE_UNCONFIRMED não autorizam remoção.

Sequência futura: decidir organização e mapa ID→asset; grupo isolado Sixth Sense;
grupo isolado carousel/macros; assets locais por componente; otimização separada
de nomes/paths; consolidação de duplicados apenas se benefício justificar.
Testes futuros proporcionais: seletor/IDs/persistência/custom icons, carregadores,
paths e manifesto, previews, geometria health_bar, compilação/embeds e CT
quando alterados recursos reais. Builds/instalações exigem autorização própria.
Rollback: preservar todos os originais da Fase 0 e restaurar grupo completo,
código/manifesto/configuração compatíveis, para diretório novo; nunca reset/clean original.

### Limitações e aprovação

Não foram examinados novos binários SWF, símbolos internos de bibliotecas SWC,
pacotes externos do jogo ou renderização CT. Recursos WoT usados por referências
(marcas, veículos, bandeiras, mapas, Warhelios) são dependências do cliente,
não ficheiros Driftkings em falta nem candidatos a mover.
Nenhuma prova nova de compatibilidade SVG, runtime CT ou independência OpenWG.

Único ficheiro escrito: este progresso. Plano diretor, código, configurações,
catálogo, geradores, imagens, fontes e cliente não modificados.
Sem novas imagens, conversões, builds, instalações, regressões ou Git mutations.
Relatório direto entregue em secções A–K; nenhum documento de auditoria adicional.

Veredicto da análise: `FASE 2 — ASSET AUDIT: COMPLETE`, com limitações acima.
Estado da fase: `AWAITING_APPROVAL`. O responsável deve decidir destinos,
IDs/nome físico, proporção do ID 1, prioridades de otimização, revisão de previews
e eventuais candidatos sem consumidor demonstrado. Nenhuma ação física autorizada.
Fase 3 não iniciada.

## 12. Aceitação da Fase 2 e arquitetura Gameface/Wulf

Data: 2026-11-12, Europe/Lisbon.
Autorização: pedido «FASE 3 — AUDITORIA E REDESENHO ARQUITETURAL GAMEFACE/WULF»,
documentação e análise, sem implementação.

### FASE 2 — COMPLETE enquanto auditoria

Registada a aceitação da auditoria dos assets pelo responsável, conforme o ponto 4
do pedido. A secção 11 conserva o estado histórico da entrega.
Aceites como orientação futura: raiz conceptual gui/icons/driftkings/; sixth_sense/;
IDs 0–9 preservados; nomes descritivos candidatos sujeitos a correspondência visual;
carroucel → carousel; assets Gameface específicos junto do componente; localização
comum dos recursos partilhados; instalador separado; FooterLauncher SVG na Fase 5.
Pendentes: proporção do ID 1, caminhos/loaders, previews, otimização sem perda das
molduras, recursos potencialmente não utilizados e SVG real no Gameface.
Nenhuma intervenção física foi autorizada ou executada.

### Ficha da Fase 3

Estado: PENDING → IN_ANALYSIS → AWAITING_APPROVAL.
Objetivo: proposta modular fundamentada para host, modelos, renderers, helpers,
catálogo, gerador e superfícies nativas, sem alterar código ou testes.
Branch reorganization/settingslab; HEAD bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3;
46 caminhos (26 M / 3 D / 17 untracked); staging vazio.
Baseline beta.9 preservada conforme Fase 0; sem repetir hash/auditoria dos artefactos.
Runtime CT e independência sem OpenWG continuam pendentes.

### Estado observado

- Catálogo: 9 own_window, 6 native_document (9 documentos), 4 native_user_missions,
  1 native_battle_results, 2 janelas próprias do lobby: 20 / 0 / 2.
- Host own_window.py: uma janela por RandomHUDView em WeakKeyDictionary;
  flags WINDOW | WINDOW_FULLSCREEN e layer MARKER; hooks _onLoading/_finalize;
  registo de cartões por adaptador; factories isolam erros individuais de criação.
- Host usa HOST_FEATURE = DriftkingsTeamStrength; gerador repete essa seleção.
  Não depende de TeamStrength estar ativado, mas depende do seu recurso/documento.
- Cada cartão tem modelo próprio, payload JSON, metadata DriftkingsUI e onSavePosition;
  filhos usam R.aliases.common.none(), só a raiz carrega o documento composto.
- publish_card usa transação, rejeita NaN e só atualiza cache após sucesso;
  publicação por cartão é protegida contra exceções. Não mudar índice payload=0.
- common.py gere GUI_VISIBILITY, cursor, readiness/attachment, settings e persistência;
  hudVisibility gere bloqueadores TAB. Preservar Ctrl/V, âncoras, unidades e transparência.
- Sem chamadas diretas entre renderers HUD identificadas; partilham helpers e contexto
  JS, e os adaptadores de texto partilham classes. Estado de cálculo continua nos módulos
  battle/components/core, não nos renderers ou no host.
- Textos junto à mira ligam crosshair/câmara; FlightTime liga gun marker;
  AimingCountdown liga battleEvents.dispersion; Penetration liga eventos de armor/color.
  vehicle_health usa tracker de vida; marcas usam marks_state; TargetInformation
  conserva o timer de ocultação do componente e cancelHide.

### model.html e catálogo

battle_statistics/model.html é output de generate_ui_catalog.py: own_window_assets
faz união ordenada sem repetição, TeamStrength primeiro e depois ordem do catálogo.
Leitura estática confirmou correspondência exata com 15 scripts e 8 folhas CSS,
todos existentes; nenhum bootstrap.js no documento. Body transparente e pointer-events
none, roots criados pelos renderers. Scripts clássicos em ordem; engine.whenReady e
subViews fazem a ligação posterior. Helpers devem existir antes dos consumidores;
fontes/imagens/layout ainda podem exigir frames de medição.

Ordem JS: marks_panel, flash_lines, screen_text, battle_statistics, health_bar,
vehicle_health, reticle_text, aiming_countdown, shell_flight_time,
penetration_indicator, battle_performance_hud, rating_text, target_information,
main_gun e marks. CSS: fonts, screen_text, health_bar, vehicle_health, reticle_text,
main_gun, marks_panel e marks. Não inferir vantagem técnica de um HTML mais curto.

O catálogo é fonte principal das identidades/assets/transportes, não a única de todos
os contratos. Repetições: host e allowlists; strings de feature nos adaptadores/renderers;
comandos; manifestos/R; testes de contagem. Contratos nativos de documentos, hashes,
versão/região e recursos externos devem permanecer explícitos.
Validações existentes cruzam layouts/R, owners, recursos únicos, manifestos quando
há build plan, patches e outputs gerados. Propor extensão dessas validações, não outro catálogo.

### Comparação e recomendação

A: composição estática atual; menor mudança imediata e rollback de referência,
mas mantém o host semanticamente ligado a TeamStrength.
B: anfitrião neutro com composição estática gerada; recomendação como arquitetura-alvo.
C: documento mínimo/loader dinâmico; implica async, ordem, cancelamento, falhas e
novos contratos sem benefício demonstrado; não recomendado.

B conserva janela, flags/layer, nove modelos/recursos/comandos, ordem de JS/CSS,
renderers e configurações. Acrescenta metadata de infraestrutura do host no catálogo
existente, documento/recurso R neutro (ex.: battle_hud/window), seleção runtime,
manifesto e validações. Não contar o host como 21.º componente nativo.
R/validação deve distinguir recurso anfitrião dos recursos de funcionalidades;
resource_id hoje só aceita recursos das entradas GAMEFACE, pelo que também exige
adaptação explícita. Os nove recursos atuais permanecem inicialmente.
Se necessário, conservar temporariamente o documento antigo gerado como compatibilidade,
sem o carregar como segunda raiz. Não editar HTML manualmente nem acoplar esta mudança
a renomeações funcionais. Validar no CT antes de substituir a baseline.

### Achados reconfirmados e propostas independentes

1. reticle_text.js:70–77 envolve dispose depois de K.connect; marks_panel.js:238
   regista a função original em unload. Unload não executa a limpeza extra do wrapper.
   Proposta: percurso único/idempotente de descarte com extensões de cleanup registadas
   antes da ligação, preservando API pública inicialmente.
2. marks_panel.js:232 compara owner.dispose com a função original; o wrapper quebra
   essa identidade e o owner não é eliminado nesse percurso. Usar identidade estável
   do objeto proprietário; não apagar um owner de geração posterior.
3. screen_text.js:68–71, reticle_text.js:59–62 e vehicle_health.js:18–21 agendam rAF
   sem guardar/cancelar handle nem guarda própria de descarte. Propor handles por owner,
   cancelamento e guarda de validade; não alterar fórmulas de posicionamento.
4. BattleCardAdapter.dispose pode parar em beforeDispose/disconnect/resource/child.destroy;
   own_window.dispose_card não usa finally. Propor tentativas independentes por recurso,
   bookkeeping em finally e registo de falhas sem impedir restantes cartões/host.
5. own_window._close remove a referência antes de destroy. Evita bloquear finalize,
   mas perde handle para diagnóstico/recuperação se destroy falhar. O teste atual exige
   essa remoção; qualquer nova política de recuperação precisa de decisão/teste explícitos.
6. Fixture test_own_battle_window.js:100 clearTimeout apaga a fila completa; rAF usa
   essa fila e disposeAll chama owners diretamente. Propor scheduler por IDs, filas
   separadas, unload real e falhas injetadas antes de corrigir código.

São constatações estáticas e caminhos condicionais de erro. Não provaram fuga persistente,
falha real de segunda batalha ou degradação no CT. HookRegistry mantém wrappers inativos
por desenho; eventual acumulação com reinstalações de novos adaptadores exige caracterização,
não refatorização global nesta fase.

### Helpers, superfícies e estrutura conceptual

marks_panel.js combina ligação/modelo, ownership, listeners, timers/drag, posição,
tema/formatação e widgets das marcas. Preservar __dkMarksKit e API; separar primeiro
responsabilidades internamente e só depois avaliar módulos físicos.
screen_text/reticle_text: tipos de texto e geometria; health_bar: renderer/skins
partilhado com preview; bootstrap: loader legado com catálogo gerado vazio, não loader HUD.
Não ativar bootstrap nem criar loader/event bus/registo de componentes paralelo.

Organização lógica: estado/cálculos existentes → adaptadores por função → modelos e
publicação existentes → renderers; host apenas composição/lifecycle. Compartilhar só
primitivas compatíveis. Nas fontes, manter paths até renomeações aprovadas; no wotmod,
recursos continuam sob res/gui e Python compilado sob res/scripts/client.

TAB/native_document continua no TabView; footer/header/perfil/crew/árvore nos próprios
documentos e hooks. Os quatro plugins UserMissions e a extensão de resultados mantêm
presenters e ciclos independentes; settings/accounts mantêm janelas próprias.
ResourceScope/CoreSession e native_assets já oferecem guardas de geração/cleanup em
contextos de módulos nativos; reutilizar princípios/código quando compatível, sem
impor ESM/async aos scripts clássicos ES5 nem fundir superfícies.
Clock e outros plugins não têm todos a mesma estratégia de ownership; uniformização
só após caracterização por superfície.

Patches native_document fixam versão 2.4.2.0, realm CT, build 995, input/output SHA-256
com substituição exata. Perfis regionais futuros pertencem à Fase 6, selecionados nos
mecanismos existentes, com renderers comuns. Nenhum hash/patch/fallback OpenWG alterado.
Hooks HUD apontam para RandomHUDView: cobertura de outras hierarquias/modos depende
realmente das classes do cliente e do runtime, não da simples existência do catálogo.

### Invariantes e sequência futura

Invariantes propostas: uma instância por owner/contexto; listeners/callbacks removidos;
nenhum trabalho válido após dispose; owner antigo nunca remove novo; cleanup tenta
limpar todos os filhos apesar de erros; reabertura sem duplicados; geometria, input,
valores, aparência e persistência preservados; restantes superfícies independentes.

Grupos, cada um dependente de autorização específica:
G1 scheduler e caracterização dispose/unload/model replacement/falhas;
G2 percursos JS de cleanup/owner, rAF cancelável e guards;
G3 teardown Python resistente a exceções e política de destroy falhado;
G4 reduzir duplicações seguras de model factory conservando wrappers/índices/commands;
G5 separar internamente helpers sem mudar API, renderers, geometria ou algoritmos;
G6 host neutro + composição estática gerada (mudança atómica de catálogo/R/runtime/
manifesto/HTML gerado/testes); G7 ampliar validações cruzadas sobre o catálogo existente.
Validações mínimas necessárias a G6 acompanham G6; G7 é o reforço adicional, não adia checks.

Testes futuros: G1–G3 descarte repetido, unload antes/depois de engine ready, frames
pendentes, troca/perda de modelo, erro individual e segundo contexto; Python 2.7/3
relevante. G4 schema e comandos/idempotência/cache transacional sem OpenWG.
G5 contratos de layout/input/formatação/previews. G6/G7 catálogo/R/manifestos,
composição/ordem/duplicados, componente desativado, subviews, janela única e rejeição
de perfil desconhecido. CT para lifecycle, modelos, host, carregamento e input afetados;
regressão final uma vez ao integrar âmbito autorizado, sem execuções nesta análise.

Rollback por grupo: patch isolado e hashes da baseline; restaurar conjunto coerente
para diretório novo a partir da preservação Fase 0, sem reset/clean do original.
Para G6, voltar conjuntamente a seleção TeamStrength, R, manifesto e documento gerado
anteriores, conservando configurações. Builds/instalações/restauração CT exigem autorização.
Riscos altos: cleanup interrompido, lifecycle, host/R, input e modos; médios: ordem/assets,
duplicações/contratos e conflitos com working tree pendente. Benefícios de B: nome neutro,
composição previsível e menor acoplamento sem nove janelas ou nova arquitetura de transporte.

### Verificação e aprovação

Apenas leituras, AST/JSON, inspeção de HTML, comparação de assets com catálogo e
leitura de testes. Nenhuma suite, gerador, build ou instalação executada.
Único ficheiro escrito nesta execução: este progresso; plano diretor inalterado.
Relatório direto em A–N. Fase 3 AWAITING_APPROVAL; não COMPLETE.
Próximas decisões: aceitar B como alvo, aprovar G1 e limites/testes, definir política
para destroy falhado e host neutro/compatibilidade; demais grupos não autorizados.
Fase 4 não iniciada. Runtime CT e independência sem OpenWG continuam pendentes.
Veredicto: FASE 3 — GAMEFACE ARCHITECTURE AUDIT: COMPLETE (análise estática).

## 13. Fase 3 — G1: caracterização de lifecycle e scheduler

Data: 2026-11-12, Europe/Lisbon.
Autorização: pedido «FASE 3 — G1: Caracterização do Lifecycle e Scheduler»,
implementação exclusivamente nos testes e respetivas fixtures, mais este progresso.
O pedido determina registar a aceitação da auditoria da Fase 3 e a aprovação da
Opção B como arquitetura-alvo. Aceitação registada nesses limites: não autoriza
host neutro, produção, G2–G7 ou Fase 4. Fase 3 IN_PROGRESS; G1 VALIDATION_PENDING.

### Ficheiros identificados antes da edição

- tests/support/frontend/deterministic_scheduler.js (novo).
- tests/frontend/battle/test_deterministic_scheduler.js (novo).
- tests/frontend/battle/test_own_battle_window.js (fixture local e caracterização).
- tests/runtime/battle/test_own_battle_window.py (fixture e casos Wulf).
- Este registo de progresso, única documentação alterada.

Git inicial: reorganization/settingslab, HEAD bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3,
46 caminhos: 26 M / 3 D / 17 untracked; staging vazio.
Git final: mesma branch/HEAD, 48 caminhos: 26 M / 3 D / 19 untracked; staging vazio.
Os dois testes existentes já estavam modificados na baseline; alterações prévias
foram preservadas. Novos caminhos são apenas a fixture e o teste do scheduler.

### Implementação limitada aos testes

Scheduler determinístico sem dependências: IDs únicos, mapas independentes de timers
/frames, clearTimeout/cancelAnimationFrame por ID, deadlines e ordem por ID, snapshots
por turno, callbacks aninhados, relógio explícito, inspeção pending sem executar trabalho
e flush explícito limitado para detetar fixtures infinitas. advance apenas avança tempo;
frame e runTimers são operações separadas. Cancelar um callback não apaga os restantes.
O relógio Date.now da fixture também é determinístico.

A fixture de eventos distingue captura e identidade, evita duplicação da mesma inscrição,
regista remoções de callbacks e permite adiar engine.whenReady. A fixture Wulf passou
a observar connect/disconnect das definições. Não foi alterado o scheduler de produção.

Caracterização JS: dez casos adicionais além dos contratos existentes dos nove HUD.
Cobrem cancelamento individual entre owners, substituição de modelo no mesmo recurso,
remoção de subview, callback antigo, dispose antes de readiness, unload real/repetido,
frames pendentes, nova geração de renderer, owner antigo, contexto reaberto e independência.
Os contratos existentes de payload, posições, dragging, visibilidade e nove renderers
continuam presentes e passaram com o scheduler novo.

Caracterização Python: seis métodos adicionais, incluindo dois expectedFailure estreitos.
Cobrem install/loading repetidos, nove schemas independentes, contexto Wulf/alias/flags,
exceção beforeDispose, exceção child.destroy, estado de listeners/registries, cartão saudável
independente, destroy de janela falhado e segunda inicialização. Mantida a expectativa
histórica de remover o handle após destroy falhado; isso não é sucesso de destruição.

### Defeitos reproduzidos, não corrigidos

| ID | Observação atual | Expectativa futura |
|---|---|---|
| G1-JS-OWNER | Três owners dos reticles permanecem após dispose explícito | G2: remover o owner próprio sem afetar geração nova |
| G1-JS-UNLOAD | Unload remove roots/callbacks principais mas deixa seis listeners extra dos reticles | G2: percurso completo e idempotente |
| G1-JS-FRAME-SCREEN | Frame pendente modifica root já destacado | G2: cancelar/invalidar frame |
| G1-JS-FRAME-HEALTH | Mesmo comportamento na vida própria | G2: cancelar/invalidar frame |
| G1-JS-FRAME-RETICLE | Mesmo comportamento em texto da mira | G2: cancelar/invalidar frame |
| G1-JS-EARLY-UNLOAD | Unload antes de readiness não fecha owners; readiness posterior ainda agenda nove timers | Descoberta adicional: G2 deve invalidar esse contexto |
| G1-PY-DISPOSE | beforeDispose falhado interrompe disconnect, destruição e bookkeeping desse adaptador | G3: tentar limpeza restante apesar do erro |
| G1-PY-CHILD | child.destroy falhado deixa views/installed/cards por limpar | G3: concluir tentativas/bookkeeping apesar do erro |
| Política destroy do host | Falha registada, handle removido, nova janela pode abrir sem retry da antiga | G3: decisão explícita sobre recuperação/diagnóstico |

Os seis casos JS defeituosos têm rótulo KNOWN DEFECT e expectativa futura no output;
são reproduções do comportamento atual, não aprovação desse comportamento.
Os dois defeitos Python têm reproduções positivas separadas e testes dos invariantes
futuros com unittest.expectedFailure. Não há skip amplo. G3 deverá substituir/remover
essas marcações ao corrigir os invariantes; um unexpected success será reportado.

### Execução e resultados

Sem regressão completa. Conjunto direcionado:
- Frontend: seis suites PASS: deterministic_scheduler, own_battle_window,
  screen_text, reticle_text, vehicle_health e main_gun, executadas diretamente com Node.
- Python 3: cinco módulos, 55 testes; 53 PASS, 2 expected failures; zero falhas inesperadas.
- Python 2.7 (F:/Python27/python.exe): os mesmos 55; 53 PASS, 2 expected failures.
- Módulos: test_own_battle_window, test_screen_texts, test_reticle_texts,
  test_vehicle_health_gameface e test_high_caliber.
- Estática: node --check nos três JS alterados/novos; AST Python; diff --check
  delimitado e whitespace dos novos ficheiros: PASS. Sem instalações de ferramentas.

Na primeira execução, o teste novo child.destroy libertava o HUD por não guardar
referência forte; a WeakKeyDictionary removia a janela antes da asserção final.
A fixture/teste foi corrigida para conservar o HUD. Não foi necessário mudar produção;
o conjunto direcionado foi reexecutado por essa correção e passou como indicado.

### Preservação, limites e decisões

Hashes dos ficheiros da worktree capturados antes das edições para conferir âmbito.
Nenhum ficheiro de produção, asset, configuração, catálogo, gerador ou model.html alterado.
Branch/HEAD original e staging confirmados; beta.9 original conserva SHA-256
22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9.
Sem builds, instalações, alterações CT, commits ou operações Git destrutivas.

Fixtures não reproduzem o motor Gameface nem a cascata completa Wulf; asserções de
flags/modelos/input são contratos simulados. Não equivalem a CT RUNTIME PASS nem
OPENWG INDEPENDENCE PASS. Impacto real das retenções/callbacks exige CT posterior.

Rollback do G1: restaurar apenas os dois testes existentes à baseline pré-G1,
conservar alterações anteriores e retirar os dois ficheiros novos somente se essa
reversão for autorizada; nunca reset/clean da árvore com alterações pendentes.
Próxima decisão: aceitar a caracterização G1; aprovar separadamente G2 e a inclusão
do caso early-unload, e posteriormente a política G3. Nenhum grupo seguinte iniciado.

Veredictos técnicos: G1 — CHARACTERIZATION PASS;
PRODUCTION CODE UNCHANGED — PASS; ORIGINAL BETA.9 PRESERVED — PASS.
Fase 3 IN_PROGRESS; G1 VALIDATION_PENDING, aceitação do responsável pendente.

## 14. Fase 3 — G2: cleanup JavaScript

Data: 2026-11-12, Europe/Lisbon.
Autorização: pedido «FASE 3 — G2: Correção do Lifecycle JavaScript», implementação
limitada ao cleanup JavaScript. O pedido aceita expressamente G1 — COMPLETE.
A secção 13 conserva o estado histórico da entrega G1. Fase 3 IN_PROGRESS;
G2 VALIDATION_PENDING; nenhum G3–G7 iniciado ou autorizado.

### Ambiente e âmbito

Branch reorganization/settingslab; HEAD bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3.
Git inicial: 48 caminhos (26 M / 3 D / 19 untracked), staging vazio.
Git final: 54 caminhos (32 M / 3 D / 19 untracked), staging vazio.
Nenhum novo ficheiro. Alterações anteriores preservadas.

Produção JS alterada exclusivamente:
- mod/res/gui/gameface/mods/driftkings/shared/marks_panel.js
- mod/res/gui/gameface/mods/driftkings/shared/screen_text.js
- mod/res/gui/gameface/mods/driftkings/shared/reticle_text.js
- mod/res/gui/gameface/mods/driftkings/vehicle_health/vehicle_health.js

Testes alterados:
- tests/frontend/battle/test_own_battle_window.js
- tests/frontend/battle/test_screen_text.js
- tests/frontend/battle/test_reticle_text.js
As duas últimas fixtures passaram a usar o scheduler determinístico G1 para expor
cancelAnimationFrame real por ID; são consumidores diretamente afetados pela correção.
O scheduler G1 e os testes Python permaneceram intactos. Única documentação: este progresso.

### Correções e contratos

O owner de K.connect é agora um objeto de identidade estável, comparado diretamente
com window[owner], sem depender da identidade de owner.dispose. A limpeza dos listeners
extra dos reticles foi integrada no mesmo percurso de descarte; deixou de usar wrapper
registado depois de unload. Dispose repetido mantém a guarda idempotente existente.

Unload é registado ao criar o owner, antes de engine.whenReady. Se unload acontecer
primeiro, dispose marca a instância, remove os recursos e a readiness posterior retorna
sem subscrever eventos, criar callbacks ou reativar o DOM.

Frames de segunda medição passaram para o owner existente de K.connect, ativados apenas
pelos três renderers afetados. Guarda um handle por instância; cancela apenas esse ID
no descarte, ocultação ou libertação do modelo, e invalida gerações antigas. O callback
verifica disposed, geração, identidade do owner, subview/modelo atual e payload antes
de posicionar. A segunda medição após layout permanece; fórmulas de posição intactas.

API existente __dkMarksKit, owners, seis argumentos originais de connect, recursos,
modelos e comandos preservados. connect aceita adicionalmente um sétimo argumento
opcional para afterLayout e cleanup específico. Chamadas antigas continuam válidas.
Nenhum loader, event bus, framework, factory ou host novo.

### Regressões e resultados

Os seis casos JS KNOWN DEFECT do G1 foram convertidos em regressões normais:
- Três owners dos reticles removidos após dispose.
- Seis listeners extra removidos em unload.
- Frames de texto fixo, vida e reticle cancelados e inertes após descarte.
- Unload anterior à readiness impede subscrições tardias.

A suite da janela tem 14 casos adicionais de lifecycle (10 convertidos/preservados,
mais 4 novos): cancelamento de frames isolado por owner; modelo substituído/removido
antes do timer de atualização; owner com wrapper externo; substituição sucessiva dos
nove renderers sem duplicar roots, callbacks ou listeners. Inclui invocação manual
de callbacks cancelados para verificar guardas, além de inspecionar o scheduler.

Conjunto direcionado, sem regressão completa:
- Seis suites de batalha/scheduler PASS: deterministic_scheduler, own_battle_window,
  screen_text, reticle_text, vehicle_health, main_gun.
- Três suites associadas ao helper partilhado PASS: hangar_marks,
  native_hangar_marks e native_marks_loader. A última é um modelo de contrato,
  não uma execução do loader real do CT.
- Wulf Python 2.7: 15 testes, 13 PASS e 2 expected failures existentes de G3.
- ESLint nos quatro ficheiros de produção alterados: PASS, zero avisos, sem cache.
  Usada a ferramenta local já existente, sem instalação nem modificação do original.
- node --check nos sete JS alterados e diff --check delimitado: PASS.

Durante a criação das quatro regressões adicionais, foram corrigidos dois pressupostos
nos testes: entrega de frame deve consumir a entrada do scheduler antes de simular
callback tardio; contagem por filter(Boolean) exige IDs de recursos não nulos.
Não se alterou produção para satisfazer esses pressupostos. O conjunto passou após
corrigir as fixtures/asserções; a suite da janela foi repetida após a revisão final.

### Preservação, limites e decisões

Hashes da worktree capturados antes/depois para delimitar alterações aos oito ficheiros
acima (quatro de produção JS, três testes JS e este progresso).
Nenhum Python de produção, teste Python, CSS, HTML/model.html, asset, configuração,
catálogo, gerador, Flash/Scaleform ou documento do plano diretor alterado.
Beta.9 original verificada por SHA-256:
22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9.
Sem builds, instalações, commits, alterações CT ou operações Git destrutivas.

Não há CT RUNTIME PASS. Os testes simulam Gameface e Wulf; ordem real de eventos,
input, performance e lifecycle em jogo continuam dependentes da validação CT futura.
As exceções de cleanup Python e a política de destroy falhado continuam pendentes de G3;
os dois expectedFailure correspondentes não foram removidos nem ocultados.

Rollback do G2 exige restaurar coerentemente os quatro JS e os testes associados à
baseline pré-G2, preservando G1 e a migração beta.9. Não restaurar apenas um renderer
sem o helper compatível. Nenhuma reversão executada.
Próxima decisão: aceitar G2 e autorizar separadamente G3; não avançar automaticamente.
G2 — JAVASCRIPT CLEANUP PASS; PRODUCTION PYTHON UNCHANGED — PASS;
ORIGINAL BETA.9 PRESERVED — PASS; FASE 3 — IN_PROGRESS.
G2 VALIDATION_PENDING; confirmação do responsável pendente.

## 15. Fase 3 — G3: robustez do descarte Python/Wulf

Data: 2026-11-12, Europe/Lisbon.
Autorização: pedido «FASE 3 — G3: Cleanup Python/Wulf», implementação limitada à
robustez do descarte. O responsável aceita G2 — COMPLETE (código e testes locais;
CT pendente). G1 permanece COMPLETE; Fase 3 IN_PROGRESS. Não autoriza G4–G7.
O pedido «vamos avançar» confirma a continuação deste âmbito após indicar a worktree.

### Ambiente e ficheiros

Branch reorganization/settingslab, HEAD bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3.
Git inicial: 54 caminhos, 32 M / 3 D / 19 untracked, staging vazio.
Git final: 56 caminhos, 34 M / 3 D / 19 untracked, staging vazio; nenhum ficheiro novo.
Alterações pendentes anteriores preservadas.

Produção alterada:
- mod/res/scripts/client/driftkings/gameface/battle/common.py
- mod/res/scripts/client/driftkings/gameface/battle/own_window.py
Teste associado: tests/runtime/battle/test_own_battle_window.py.
Única documentação alterada: este progresso.

### Correções

BattleCardAdapter.dispose tem guarda de descarte repetido/reentrante. beforeDispose,
disconnectSignals, resolução do recurso, verificação de ownership, setEnabled e destroy
são etapas separadas: exceções são registadas por fase e não impedem etapas/filhos
independentes. Falha em setEnabled não impede a tentativa de destroy do mesmo filho.
Falha num parent não impede tentar os restantes. Um filho substituído por recurso
alheio não é destruído. Se a identidade/ownership não puder ser verificada, não se
adivinha o dono: a libertação desse filho fica explicitamente não confirmada.

finally retira as views do adaptador e define installed/active como False.
_disposed impede repetir operações concluídas. _disposeFailures conserva os nomes
das etapas falhadas, sem criar registo global ou guardar handles órfãos. Remover uma
referência/inscrição não é apresentado como sucesso de libertação do recurso.
Falhas internas de um hook podem deixar a limpeza desse hook incompleta; são reportadas,
sem afirmar que todas as suas subscriptions foram libertadas nem repetir hooks já tentados.

own_window.dispose_card tem proteção reentrante e remove o registo em finally,
mesmo perante uma falha inesperada do dispose do adaptador. O último cartão tenta
fechar todas as janelas registadas; uma falha de destroy não bloqueia outras janelas.
Não foram criadas factories, modelos ou abstrações de host.

### Política de destruição preservada

_close continua a remover o handle antes de chamar window.destroy. Uma exceção é
registada com diagnóstico explícito: handle removido, sem retry, libertação da janela
não confirmada. Nova inicialização permanece possível. Não existem retries automáticos,
listas globais de órfãs, alterações de identidade do host ou declarações falsas de sucesso.
Pode permanecer uma janela que o motor não tenha destruído; a política autorizada
aceita remover a referência sem garantir recuperação desse recurso.

### Testes e diagnóstico

As duas reproduções de falhas Python G1 foram convertidas em regressões da limpeza
corrigida. Os dois expectedFailure foram removidos e os respetivos invariantes passam
como testes normais. Nenhuma expectativa da política de destroy falhado foi invertida.

Sete casos adicionais cobrem: múltiplas falhas numa limpeza; restantes filhos/parents;
ownership indisponível ou recurso substituído; resolução de recurso falhada; dispose
inesperado do adaptador; falhas parciais entre nove cartões; reentrância; fecho de várias
janelas com uma falhada e ausência de retry (alguns casos agregam vários cenários).
A suite da janela tem agora 22 testes. Logging observado por fase, incluindo quatro
falhas independentes na mesma limpeza, sem ocultar as seguintes.

Execução final, apenas direcionada:
- Python 3: 62 testes PASS, zero falhas/expectedFailure.
- Python 2.7: os mesmos 62 PASS, zero falhas/expectedFailure.
- Módulos: test_own_battle_window, test_screen_texts, test_reticle_texts,
  test_vehicle_health_gameface e test_high_caliber.
- Suite da janela executada primeiro com 21 casos PASS nos dois interpretadores;
  adicionado depois o caso explícito de múltiplas janelas/destroy falhado; conjunto
  final de 62 repetido para incluir esse caso.
- AST Python, isort --check-only nos três Python alterados e diff --check delimitado:
  PASS. Sem alteração automática de formatação ou dependências.
- Não foi executada regressão completa, frontend, build ou instalação.

### Contratos e preservação

Preservados: uma janela partilhada, nove modelos, payload, DriftkingsUI,
onSavePosition, R.aliases.common.none(), flags/layer, configurações, recursos,
posições, visibilidade, dragging e input. Só o descarte foi alterado.
JavaScript, CSS/HTML/model.html, assets, Flash, catálogo, gerador e configurações
comparados com os hashes pré-G3; nenhum desses ficheiros alterado.

Beta.9 original verificada: SHA-256
22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9.
Projeto original e CT não modificados. Sem commits, push, builds ou instalações.

### Riscos e aprovação

Testes usam fixtures Wulf; não demonstram libertação real pelo motor nem performance
CT. Uma falha de destroy ou de hook pode deixar recursos vivos; o diagnóstico conserva
essa incerteza. Não introduzido retry desses recursos. Runtime CT e independência
sem OpenWG continuam pendentes; G2 continua sem validação em jogo.

Rollback requer restaurar coerentemente os dois módulos e o teste à baseline pré-G3,
preservando G1/G2 e alterações beta.9 anteriores. Nenhuma reversão executada.
Próxima decisão: aceitar G3; qualquer G4 exige autorização expressa posterior.
G3 — PYTHON/WULF CLEANUP PASS; JAVASCRIPT UNCHANGED — PASS;
ORIGINAL BETA.9 PRESERVED — PASS; FASE 3 — IN_PROGRESS.
G3 VALIDATION_PENDING; confirmação do responsável pendente. G4 não iniciado.

## 16. Fase 3 — G4: auditoria dos modelos e factories Wulf

Data: 2026-11-12, Europe/Lisbon.
Autorização: pedido «FASE 3 — G4: Auditoria de Modelos e Factories Wulf», análise
apenas; única escrita autorizada neste progresso. Registada a aceitação expressa
do G3 ao nível dos testes locais: COMPLETE, tal como G1/G2. A secção 15 conserva
o estado histórico da entrega. Runtime CT e independência sem OpenWG pendentes.
G4: IN_ANALYSIS → AWAITING_APPROVAL. Fase 3 permanece IN_PROGRESS.

### Baseline, âmbito e verificações

Worktree E:/Wot_Mods_/Drift_Kings_ModPack/Driftkings_SettingsLab_reorganization;
branch reorganization/settingslab; HEAD bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3.
56 caminhos: 34 modificados, 3 removidos, 19 untracked; staging vazio.
Lidos plano diretor, auditoria arquitetural (secção 12), resultados G1–G3 e fontes/testes
relacionados. Não executadas suites, regressão completa, gerador, build ou instalação.
Beta.9 original novamente conferida: build/experiments/20261111T115234Z-1d26e1e9/
output/driftkings.wotmod, SHA-256
22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9.
Original conserva 46 caminhos pendentes. Nenhuma escrita no original ou CT.

### Arquitetura e responsabilidades

BattleCardAdapter.install seleciona own_window.payload_model pelo catálogo, criando
uma classe por cartão; cada child tem instância/cache/comando próprios. HostView._factory
não é uma segunda factory de schema: cria a ViewComponent com R.aliases.common.none(),
regista ownership adapter.views[host] e isola falhas. _cards, _windows e _types gerem
cartões/janelas/tipos de janela, não constituem cache global de modelos Wulf.
Nove cartões partilham só a janela/documento; não partilham instâncias de modelo.
Payload é propriedade 0; DriftkingsUI contém AssetsModel.name; onSavePosition é comando.
Views declaram eventos/listeners, adaptadores subscrevem settings e fontes próprias;
a factory de modelo não deve absorver subscriptions, hooks, dragging ou destruição.
G3 mantém ownership e diagnóstico de release não confirmado em caso de falhas.

core.payload_model encaminha os seis native_document para native_payload_model;
os quatro native_user_missions e o native_battle_results chamam esta diretamente.
São onze consumidores nativos dessa factory, além dos nove da factory own_window.
resource_id valida recursos do catálogo e resolve R. Não alterar IDs/aliases/declarações.
SettingsModel usa schema/state e AccountsModel payload sem DriftkingsUI: contratos
próprios das duas janelas, não duplicações do schema dos vinte consumidores.

### Duplicações comprovadas e distinções

1. own_window.py:payload_model (linha 24) e core.py:native_payload_model (linha 67):
   repetem geração de ViewModel, duas propriedades, metadata e comandos (9 + 11
   consumidores). Dependem de Wulf/AssetsModel; a segunda valida transportes e coloca
   metadata antes dos comandos, enquanto a primeira usa imports tardios e ordem inversa.
   Benefício possível: uma implementação de schema em vez de duas, sem benefício runtime
   demonstrado. Risco médio: validação, ordem, imports e tipo criado. Alternativa sem
   abstração nova: manter ambas sob testes de equivalência. Testes futuros, se aprovado:
   traço de inicialização, schema/commands/metadata, classes e instâncias independentes,
   vinte transportes sem import/injeção OpenWG e Python 2.7/3.
2. Publicação compare/transaction/cache repete-se em panel_gameface.py:GamefaceLoading.update,
   lobby/battle_performance.py:ResultsView.refresh e tech_tree_marks_of_excellence.py:
   MarksView.refresh (três consumidores), relativamente a payloads.publish_card.
   Esta primitiva já é reutilizada pelos nove HUD e cinco adaptadores de lobby
   (clock, marks, crew progression, carousel, crew details). Não criar publicador paralelo.
   TAB usa cache no record e diagnóstico; resultados serializam JSON com defaults e
   registam primeira publicação; árvore recebe string já serializada. publish_card usa
   JSON compacto/allow_nan=False e cache no child. Consolidação direta mudaria contratos
   ou duplicaria serialização. Benefício pequeno, risco médio; manter por superfície.
   Se alterado futuramente: testar bytes/NaN, rollback de cache na falha da transação,
   diagnóstico, primeira publicação e reabertura de cada superfície.
3. _lastPayload=None e lifecycle repetidos nos adaptadores: ownership/readiness/events
   dependem do parent e do presenter; duplicação legítima, não motivo para superclasse
   universal. Os quatro plugins UserMissions repetem registo transacional/desregisto,
   mas os descritores, comandos e políticas de ownership não são todos equivalentes.
   Manter código atual; eventual consolidação exigiria caracterização específica dos
   quatro plugins, sem alterar host. Testes existentes de colisão, substituição e dispose
   são essenciais; benefício adicional não demonstrado nesta análise.
4. Escritas simples no perfil, header e launcher não têm o mesmo cache/transação que
   publish_card. Acrescentar estes mecanismos seria mudança comportamental, não simples
   eliminação de duplicação. Sem defeito demonstrado; não recomendado no G4.

### A/B/C e recomendação

A — manter: menor risco, contratos atuais cobertos; conserva uma pequena duplicação.
B — delegar o wrapper own_window na factory nativa existente: reduziria um único bloco,
mas exige alargar a validação ao transporte own_window, preservar lazy imports/API e
resolver equivalência da ordem de inicialização. É alternativa futura delimitável,
não correção necessária nem implementação autorizada.
C — factory/base/registry adicional: aumenta acoplamento e superfície de manutenção;
sem benefício substancial demonstrado, rejeitada como recomendação.
Recomendação única: A, NÃO ALTERAR produção ou testes neste G4. Não há defeito funcional
comprovado na criação/publicação de modelos que justifique consolidar agora. Aceitar
explicitamente a duplicação pequena sob cobertura existente; não criar arquitetura paralela.

### Cobertura e lacunas concretas

- test_native_documents.py: vinte schemas, metadata, commands e classes distintas;
  ausência de import/injeção OpenWG na fixture. Não valida runtime sem biblioteca instalada.
- test_own_battle_window.py: nove modelos/janela, positions/visibility/commands,
  instalação repetida, ownership, descarte, reentrância, falhas e segunda batalha.
- test_battle_cards.py: attachment pendente, replacement, listeners/input e reabertura.
- test_gameface_architecture.py: cache só após transação bem-sucedida, deduplicação,
  recursos, fronteiras de imports e registry de janelas.
- test_native_carousel.py: equivalência com baseline, comando, subscription/descarte,
  remoção apenas do descritor próprio; test_native_crew_runtime.py: colisões/ownership.
- test_native_rating_tab.py: comandos, payload/ordem/visibilidade, duplicate load,
  finalize/reopen, foreign replacement e ownership dos hooks.
- test_native_results.py: schema, cache, finalize, novo modelo na reabertura.
- G3 documentou 62 PASS nos dois interpretadores, zero expectedFailure; resultado
  histórico aceite, não reexecutado no G4. G1/G2 frontend igualmente não reexecutado.

Lacuna relevante a B: testes de schema não observam ordem relativa de criação de
propriedades/comandos. Só acrescentar teste se B vier a ser autorizado.
O teste genérico de falha de transação não demonstra os três publicadores específicos;
se forem consolidados, acrescentar falha injetada em cada um e equivalência da serialização.
Não propor nova regressão completa para uma entrega exclusivamente analítica.

### Ficheiros, contratos, riscos e aprovação

Único ficheiro alterado: este progresso. Candidatos apenas se B for futuramente aprovado:
core.py, battle/own_window.py e testes direcionados de schema/janela/native_documents.
Sem necessidade de alterar common.py, payloads.py, host, catálogo, gerador ou renderers
para a recomendação A. Contratos protegidos: janela única, nove modelos independentes,
payload, DriftkingsUI, onSavePosition, alias none, IDs, recursos, configurações, cache,
transações, posições, visibilidade, input/dragging e Python 2.7.

Riscos altos ainda existentes: runtime CT e independência real sem OpenWG não provados.
Risco médio se B implementada: inicialização/identidade/ownership; baixo na manutenção
textual duplicada atual. Nenhuma medição demonstra ganho de desempenho por factory única.
Rollback desta análise: retirar somente o delta documental G4 se autorizado, preservando
histórico e G1–G3. Futuro B exigiria patch coerente de dois módulos/testes sobre baseline
pré-G4; não restaurar ficheiros inteiros do HEAD nem perder migrações pendentes.

Decisão pendente: aceitar análise/recomendação A e encerrar G4 sem implementação,
ou autorizar expressamente estudo/implementação B com critérios acima. Nenhuma
aceitação implícita de G5–G7, builds, instalações ou alteração do CT.
G4 — MODEL/FACTORY AUDIT: COMPLETE (análise); G4 — AWAITING_APPROVAL.
PRODUCTION CODE UNCHANGED — PASS; ORIGINAL BETA.9 PRESERVED — PASS.

## 17. Fase 3 — G5: auditoria dos helpers Gameface

Data: 2026-11-12, Europe/Lisbon.
Autorização: pedido anexado «FASE 3 — G5: Auditoria e Organização dos Helpers
Gameface», análise exclusivamente; única escrita neste progresso.
Aceitação expressa: G4 COMPLETE, sem implementação; Opção A aprovada, manter
own_window.payload_model e core.native_payload_model separados. A secção 16 é histórica.
G5 IN_ANALYSIS → AWAITING_APPROVAL; Fase 3 IN_PROGRESS. G6/G7 não iniciados.

### Ambiente, âmbito e preservação

Worktree autorizada: E:/Wot_Mods_/Drift_Kings_ModPack/Driftkings_SettingsLab_reorganization.
Branch reorganization/settingslab, HEAD bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3.
Baseline: 56 caminhos, 34 M / 3 D / 19 untracked; staging vazio; sem divergências.
Lidos plano diretor, progresso, auditoria da Fase 3 e resultados G1–G4. Inspeção
estática dos nove helpers pedidos, consumidores diretos, flash_text.js, plugin das
marcas da garagem, adaptador/binding de resultados, documento HUD e testes associados.
Sem execução de suites, geradores, builds, instalações ou alterações ao original/CT.
Beta.9 original novamente verificada, no experimento 20261111T115234Z-1d26e1e9:
SHA-256 22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9.

### Inventário e fronteiras

- marks_panel.js: __dkMarksKit; DOM/style, números/locale, stars/graph/scale,
  theme, geometria/savedPosition e connect. Nove HUD dependem diretamente ou através
  de screen_text/reticle_text; marcas da garagem também usam widgets/utilitários,
  com lifecycle do plugin próprio. Locale é estado por documento, não por owner;
  graph mantém assinatura/pools por instância. connect mantém modelo/resource/callback,
  payload, timer, frame/geração, drag/shield/data por owner. Engine/viewEnv/subViews,
  window/document e CSS são dependências. Não carrega scripts/CSS. Assets das estrelas
  vêm do CSS; theme aplica cores/escala/opacidade, sem calcular marcas no JavaScript.
- screen_text.js: __dkScreenText(feature,owner,modifier), três consumidores TeamStrength,
  BattleEfficiency e TargetInformation. Usa K/FlashLines e, em modo rich com imagens,
  DKRatingText.localImage. Mantém root/content e cache html/layout por instância;
  sombras/fonte/background/alinhamento são seus. connect gere listeners/timer/frame,
  drag e descarte; position/savedPosition vêm de K. Sem loader próprio.
- reticle_text.js: __dkReticleText, AimingCountdown/FlightTime/Penetration; K/FlashLines.
  Root/content/cache e retenção de drag próprios; posição relativa à mira, não à margem
  do ecrã. Duas inscrições document mousedown/mouseup removidas pelo lifecycle.dispose
  de connect (G2). Janela de 1500 ms usa Date.now, não um timer adicional. Medição rAF
  é gerida por connect. Offset salvo preserva âncora e alinhamento.
- health_bar.js: __dkHealthBar.create/preset; OwnHealth e previews settings controls/hud.
  Oito presets, crops/slots/assets, fill/texto e cache do skin por instância. Sem listeners,
  timers, frames ou owner global de instância; chamador detém/remove o DOM. Sem transporte
  Wulf próprio, posicionamento de ecrã ou dragging. Reutilização entre preview e HUD legítima.
- flash_lines.js: __dkFlashLines.lines/face; screen_text/reticle_text. Parser do subset
  Flash para linhas/runs flex, rich tabs/leading/imagens opcionais e regras de fontes.
  Usa K.node, DOM temporário/local; não cria subscriptions/timers/owners persistentes.
  O renderer chamador limpa o conteúdo; isso não exige dispose próprio do parser.
- rating_text.js: DKRatingText ou CommonJS; ratings TAB e localImage usado por rich
  TargetInformation. flag/number/localImage/color/writeRuns/copyRuns; DOM flex, fontes,
  alpha acumulado, size=0 e imagens locais. Sem timers/listeners/ownership de roots.
  Parsing numérico coercivo difere intencionalmente de K.number.
- bootstrap.js: __dkUIBridge; loader legado por catálogo gerado atualmente vazio.
  active/retiring/disposed, sequenciamento de scripts, links/fontes e owners por feature;
  engine readiness/subViews/unload. Nenhum timer/rAF explícito. Não é carregado pelo
  HTML HUD, e não é a infraestrutura a ativar ou generalizar no G5/G6. Bloco GENERATED
  pertence ao gerador. Ausência de consumidores nativos não autoriza remover o ficheiro.
- native_assets.js: export loadResultsAssets; results.js. CSS de fonts/results em
  leases por documento/URL, WeakMap/Map/refcounts, Promise/load/error; scope.defer liberta
  só links próprios e preserva links estrangeiros preexistentes. Sem timers/rAF/input,
  Wulf, tema ou geometria. É ESM da superfície de resultados, não helper clássico HUD.
- native_extension_core.js: exports ResourceScope/CoreSession, usados pelo adaptador
  battleinfo_adapter. LIFO cleanup, estados, generations, guards, pending/retirement
  Promises e diagnóstico; sem DOM, Wulf, eventos/timers/rAF próprios. Scope é dono dos
  disposers registados; owner init/destroy são contratos assíncronos desta superfície.
- flash_text.js (dependência direta adicional): DriftkingsFlashText.inert/copy,
  resultados/settings. Reconstrói markup permitido, não linhas flex; opções de fonte,
  alpha e unidades. Sem estado persistente, subscriptions, timers ou dragging.

### marks_panel: análise detalhada e G2

Referências: connect:144; dispose:243; unit:272; position:273;
savedPosition:293; theme:305; API exportada:316. Widgets e formatação estão nas
funções anteriores, separadas de connect; ficheiro com cerca de 320 linhas.
connect conserva os seis argumentos originais e lifecycle opcional do G2.
Encontra modelo por DriftkingsUI.name; segue identidade do model/resource, retira
callback antigo e invalida frames antes de rebind. Cache compara payload string.
Eventos de dados/subViews coalescem num setTimeout(0) por owner; frame opcional
após layout valida owner/model/resource/payload/geração e é cancelado em release/hide.
Drag usa primeiro filho como handle, captura de rato e shield fullscreen temporário;
move limita ao viewport e end envia onSavePosition. Input/posições não devem ser
fundidos com as fórmulas de reticle_text. Ctrl/V são refletidos nos contratos Python/config.
Dispose idempotente marca disposed, limpa drag/shield/timer/listeners/callback/frame/root,
executa cleanup específico e elimina owner só se window[owner] ainda for o mesmo bridge.
Unload é registado antes de whenReady, que verifica disposed antes de subscrever.
Nove renderers já partilham este lifecycle; não há justificação para segundo framework.

Ressalva comprovada por leitura, não reproduzida como falha CT: se engine.off,
removeDataChangedCallback ou lifecycle.dispose lançar, dispose não tem isolamento por
etapa e poderá não concluir as etapas seguintes. G2 não é prova de robustez perante
qualquer exceção destas APIs. Tal alteração seria correção funcional separada, exigindo
reprodução/testes e aprovação; não a disfarçar como organização de funções.

### Duplicações reais e acoplamento

1. unit(): mesma expressão em marks_panel:272 e reticle_text:9, dois ficheiros.
   Extrair/expor mais API pouparia uma linha com novo contrato; manter.
2. inert(): mesmo neutralizador textual de event attributes em flash_lines:17,
   rating_text:27 e flash_text:6. Três consumidores/famílias, dependências de carregamento
   distintas; consolidar obrigaria recurso comum/ordem extra ou alargar API existente.
   Pequeno ganho de manutenção; não alterar antes de testes de equivalência por parser.
3. Reconstrução de texto, cores e números parece semelhante, mas contratos diferem:
   linhas flex versus árvore DOM; fontes permitidas versus heredadas; alpha acumulado;
   imagens/tabs/size=0; coerção numérica. Não são renderers intercambiáveis.
4. DOM node/style e lifecycle nos módulos ESM não justificam dependência em MarksKit:
   resultados/settings/HUD são superfícies independentes. Duplicação de primitivas
   pequenas preserva isolamento legítimo. Locale global do kit é acoplamento por
   documento, mas só os renderers de marcas identificados chamam setLocale; não foi
   demonstrada colisão entre owners no mesmo documento. Não alegar bug observado.

### Alternativas, estrutura e impacto no G6

A — manter: recomendado. Separação funcional já existe; evita tocar no G2 antes do CT.
B — reorganizar internamente: possível melhoria editorial futura, mas apenas mover
funções não reduz estado/contratos nem resolve defeito; sem ganho concreto suficiente
nesta análise para recomendar implementação. Conservar mapa lógico DOM/formatting,
widgets, connect, geometry/theme sem criar namespaces públicos ou objetos de lifecycle.
C — módulos especializados: não recomendado. Exigiria ordem/manifestos/catálogo e
carregamento adicional inclusive no plugin das marcas da garagem; dimensão não justifica.
Recomendação única: NÃO ALTERAR OS HELPERS neste G5. Não há pré-requisito técnico
nos helpers para G6: conservar uma janela, nove modelos, composição estática gerada,
catálogo e ordem explícita. HTML atual tem 15 scripts/8 CSS sem duplicados; K precede
FlashLines/screen/reticle/consumidores. DKRatingText precede TargetInformation; a
consulta opcional em screen_text ocorre ao renderizar, não ao definir a função.
Não converter scripts clássicos para ESM nem usar CoreSession/async loader no HUD.
G6 continua não iniciado e exige autorização própria.

### Testes, riscos e rollback

Cobertura lida, sem nova execução:
- test_own_battle_window/test_deterministic_scheduler: APIs/renderers reais, ordem,
  nove owners independentes, init tardio/unload/replacement, timers/frames, listeners,
  posições/input/visibilidade e segunda geração; G2 tem 14 casos lifecycle documentados.
- test_screen_text/test_reticle_text: posição, dragging, alinhamento, fontes/sombras,
  formatação rich, tabs/imagens e limpeza específica; test_main_gun/hangar_marks:
  widgets/tema/formatação/gráfico; test_vehicle_health: skins/geometry/preview.
- test_ratings/test_native_rating_tab/test_flash_text: valores/markup/imagens/fontes
  e contratos TAB. Não presumir que test_flash_text cobre os outros dois parsers.
- test_native_results: módulos reais, binding/identity, guards, falhas de cleanup,
  LIFO, leases CSS/falhas, imports tardios, isolamento e montagem/reabertura React.
- test_native_hangar_marks testa plugin real; test_native_marks_loader usa modelo de
  contrato do loader, não execução do loader do CT. Bootstrap tem checks de catálogo
  e ausência no HUD; não identificada suite direta completa de seu lifecycle legado.

Se futura reorganização B/C for autorizada: executar suites dos consumidores afetados,
ESLint/compatibilidade clássica, catálogo/ordem sem regenerar baselines indevidamente;
acrescentar apenas lacunas concretas. Para eventual robustez de dispose, primeiro
injetar exceções de engine.off/remove callback/cleanup e verificar tentativas seguintes,
owner novo protegido e bookkeeping; não implementado nem testado agora.
CT necessário após alterações de lifecycle/timing/DOM/geometria/ordem; as fixtures
não provam fontes/layout/input/performance do cliente real. Manter pendências G1–G3,
beta.9 e independência sem OpenWG. Risco alto em mudar lifecycle/loader/ordem, médio
em unificar parsers, baixo em manter pequenas duplicações textuais.
Rollback desta análise: só delta documental. Futuro grupo B: helper e testes associados
como patch sobre baseline pós-G3. Grupo C exigiria helper, consumidores, recursos,
catálogo/gerador e HTML gerado coerentes; não recomendado. Nunca restaurar HEAD inteiro
nem desfazer G1–G3/migração beta.9. Nenhum rollback executado.

Decisões pendentes: aceitar auditoria e recomendação A, encerrando G5 sem código;
qualquer reorganização/correção exige pedido específico e critérios delimitados.
G5 — AWAITING_APPROVAL.
G5 — SHARED HELPERS AUDIT: COMPLETE (análise estática).
PRODUCTION CODE UNCHANGED — PASS; ORIGINAL BETA.9 PRESERVED — PASS.

## 18. Fase 3 — G6: preparação da migração para host neutro

Data: 2026-11-12, Europe/Lisbon.
Autorização: pedido anexado «FASE 3 — G6: Preparação da Migração para Host Gameface
Neutro», análise de implementação exclusivamente. Única escrita neste progresso.
Aceitação expressa: G5 COMPLETE; OPTION A — KEEP EXISTING SHARED HELPERS.
Observação sobre exceções em marks_panel.dispose permanece pendente, sem correção:
engine.off, removeDataChangedCallback ou lifecycle.dispose podem interromper etapas
seguintes se lançarem. Requer caracterização/aprovação própria; fora do G6.
G4 continua concluído sem consolidar factories. G6 IN_ANALYSIS → AWAITING_APPROVAL;
Fase 3 IN_PROGRESS. G7 não iniciado. Arquitetura-alvo B aceite não autoriza implementação.
CT novamente disponível segundo o responsável; validação em jogo expressamente adiada
para depois da reorganização. Não sondado, iniciado ou modificado nesta análise.

### Baseline e método

Worktree E:/Wot_Mods_/Drift_Kings_ModPack/Driftkings_SettingsLab_reorganization,
branch reorganization/settingslab, HEAD bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3.
56 caminhos: 34 M / 3 D / 19 untracked; staging vazio. Sem divergência material.
Lidos plano diretor, progresso, auditoria da Fase 3 e resultados G1–G5. Apenas leitura,
AST/JSON, pesquisas de referências e comparação de composição; sem executar gerador,
outputs(), testes, build ou instalação. Nenhum HTML gerado nesta execução.

### Percurso atual e dependências comprovadas

own_window.py:15 HOST_FEATURE='DriftkingsTeamStrength'; _open:112 resolve
resource_id(gameface_spec(HOST_FEATURE)['resource']). Catálogo liga o recurso
mods/driftkings/battle_statistics/model ao layout battle_statistics/model.html.
JSON driftkings.battle_statistics.json declara R.mods.driftkings.battle_statistics.model.
Runtime Wulf usa o layout resolvido na raiz HostView; filhos são keyed pelos nove
resources individuais e criados com R.aliases.common.none(). _cards/adapter.views,
_windows por HUD, flags fullscreen/MARKER e hooks RandomHUDView não exigem mudança.
TeamStrength desativado já não impede a janela, mas o recurso/documento são seus.

generate_ui_catalog.py:16 OWN_WINDOW_HOST repete a seleção. own_window_assets:93
põe esse componente primeiro e une assets dos outros own_window em ordem do catálogo.
outputs:138 escreve no layout desse componente; validate:257 lê o mesmo documento.
core.resource_id:15 só aceita resources das entradas GAMEFACE. validate:194 exige
igualdade entre declarações R e recursos dessas entradas e paths distintos.
components.json associa battle_statistics/** e seu JSON R à funcionalidade; ui é
manifesto shared já existente, adequado para infraestrutura sempre empacotada.
compiler usa plan.assets e normalização mod/ → target sem mod/; não descobre um
novo JSON/layout automaticamente sem declaração de assets no manifesto.
Declarações JSON R são fontes mantidas no repositório; a árvore/accessor numérico
R é fornecida pelo cliente. Não gerar/editar gui.impl.gen.R Python no projeto.
HTML HUD é output do gerador; não editar manualmente.

### Identidade e metadata propostas (sujeitas a aprovação)

Adicionar BATTLE_HUD_HOST como dict literal no MESMO interface_catalog.py, fora
GAMEFACE, com resource='mods/driftkings/battle_hud/window',
layout='coui://gui/gameface/mods/driftkings/battle_hud/window.html' e
asset_priority=('DriftkingsTeamStrength',). Esta prioridade conserva a composição
histórica; não escolhe o host por uma funcionalidade. Restantes assets derivam do
catálogo e transportes existentes; validar prioridade única e pertencente aos nove HUD.
Não adicionar owner, settings, renderer, modelo ou entrada GAMEFACE para o host.
Não adicionar framework/loader/registry. O catálogo mantém 22 entradas = 20/0/2;
recursos Layout tornam-se 23: 22 existentes mais um de infraestrutura.

### Mapa exato proposto

| Ficheiro | Símbolo atual | Símbolo proposto | Consumidor | Alteração necessária | Risco | Teste |
|---|---|---|---|---|---|---|
| mod/res/scripts/client/driftkings/interface_catalog.py | Apenas GAMEFACE para recursos de UI | BATTLE_HUD_HOST, separado de GAMEFACE | Runtime e gerador AST | Adicionar metadata literal acima; manter nove specs | Médio | Contagens, host fora dos componentes, schema/colisões/prioridade |
| mod/res/scripts/client/driftkings/gameface/core.py | resource_id whitelist GAMEFACE | União com BATTLE_HUD_HOST.resource | _open e callers existentes | Alargar apenas allowlist; manter quatro partes/R/sentinel/rejeições | Médio | Resolver novo recurso e 22 antigos; recusar desconhecidos |
| mod/res/gui/gen_resources/driftkings.battle_hud.json (novo, fonte) | Ausente | R.mods.driftkings.battle_hud.window | Loader de recursos do cliente | Layout, path coui neutro, parameters entrance main/impl gameface | Alto | ID/path/capitalização/unicidade/packaging e CT |
| build_data/components.json | ui.assets sem host; battle_statistics mantém assets | ui.assets mais novo HTML e novo JSON | build_plan/compiler | Acrescentar dois paths exatos; não mudar feature manifests existentes | Médio | Targets únicos, owner ui/shared, presente com TeamStrength desativado |
| build_tools/generate_ui_catalog.py | OWN_WINDOW_HOST, own_window_assets, outputs, validate | Metadata BATTLE_HUD_HOST; composição derivada com asset_priority | Geração/check de contratos | Retirar seleção semântica do host; gerar ambos HTML da mesma string; validar R união e manifesto | Alto | Ordem exata, outputs atuais, host/compat iguais, negativos sem recurso/asset/prioridade |
| mod/res/gui/gameface/mods/driftkings/battle_hud/window.html (novo, output) | Ausente | Raiz neutra composta | HostView | Gerar apenas com ferramenta atual após autorização | Alto | 15 JS/8 CSS, URLs/ordem, transparência/input, sem bootstrap |
| mod/res/gui/gameface/mods/driftkings/battle_statistics/model.html (output existente) | Raiz ativa ligada a TeamStrength | Output compatível, não selecionado como raiz normal | Recurso individual antigo/potenciais consumidores | Manter e gerar pela mesma composição | Baixo se não carregado | Igualdade com neutro, um único layout raiz runtime |
| mod/res/scripts/client/driftkings/gameface/battle/own_window.py | HOST_FEATURE e _open/gameface_spec | _open usa BATTLE_HUD_HOST.resource | Hooks/HostWindow | Trocar apenas seleção/import/comentários; sem alterar factory/dispose/_cards/flags | Alto | LayoutID novo distinto dos cartões, janela única, falhas/reabertura/sem fallback |
| tests/build/test_own_window_catalog.py | OWN_WINDOW_HOST/FEATURE e layout da feature | Metadata/novo layout; prioridade independente | Contratos estáticos | Atualizar seleção e acrescentar negativos de infraestrutura/compat/manifesto | Médio | Mesma lista de nove; 20/0/2; 23 recursos; ordem estável |
| tests/runtime/integration/test_gameface_architecture.py | resource_id testado só para GAMEFACE | Testar também resource neutro/rejeições | Resolver runtime | Acrescentar asserts sem mudar limites de componentes | Médio | Wulf stub em Python 2.7/3 |
| tests/runtime/battle/test_own_battle_window.py | HOST_FEATURE assert; resolver com default 50 | Metadata e recurso do host explícito distinto | Host Wulf em fixture | Atualizar import/stub/assert para não mascarar ID errado; preservar regressões G3 | Alto | Nove filhos, oito sem TeamStrength, repeated loading, dispose/reopen/falhas |
| tests/frontend/battle/test_own_battle_window.js | Lê battle_statistics/model.html | Lê battle_hud/window.html; confere compat antigo | Nove renderers reais na fixture | Trocar documento de entrada, manter asserts G1/G2 e snapshots de ordem | Médio | Inicialização/owners/DOM/listeners/frames/posições/input |

Não alterar common.py, payload_model, renderers, helpers, configs, patches CT,
bootstrap gerado vazio, arquivos SWF ou build_config.json. AS3/BOOTSTRAP são outros
outputs do gerador e devem permanecer idênticos quando futuramente executado.
Se uma suite consumidora de validate falhar por contrato antigo, analisar o assert
concreto; não atualizar baselines nem alargar âmbito automaticamente.

### Composição preservada e compatibilidade

Comparação estática direta confirmou HTML atual exatamente igual à união ordenada:
JS (15): shared/marks_panel, shared/flash_lines, shared/screen_text,
battle_statistics/battle_statistics, shared/health_bar, vehicle_health/vehicle_health,
shared/reticle_text, aiming_countdown/aiming_countdown, shell_flight_time/shell_flight_time,
penetration_indicator/penetration_indicator, battle_performance_hud/battle_performance_hud,
shared/rating_text, target_information/target_information, high_caliber_gameface/main_gun,
battle_marks_of_excellence/marks (todos .js).
CSS (8): shared/fonts, shared/screen_text, shared/health_bar, vehicle_health/vehicle_health,
shared/reticle_text, high_caliber_gameface/main_gun, shared/marks_panel,
battle_marks_of_excellence/marks (todos .css).
URLs continuam coui://gui/gameface/mods/driftkings/; nenhuma alteração de bytes nos
assets individuais é necessária. Ambos HTML podem ter bytes iguais; resources/path
R são distintos. Sem <base>, URLs relativas novas ou async/defer adicionais.

Manter documento antigo e JSON R de TeamStrength temporariamente. Referências diretas
atuais: catálogo, JSON R, fixture frontend; indiretas: gerador/testes/manifesto via glob.
Não encontrados patches CT selecionando esse path na pesquisa dirigida; outros mods
ou consumidores externos não são enumeráveis estaticamente, justificando compat.
A raiz normal seleciona SÓ o novo recurso: nunca carregar antigo adicionalmente, nunca
usar fallback para antigo em falha do neutro. Nove children usam alias none; recurso
antigo continua key do cartão TeamStrength, sem carregar seu HTML como filho.
Uma raiz ativa, dois documentos físicos empacotados não equivalem a duas janelas.

### Recursos, manifesto e packaging

JSON novo: type Layout; path coui neutro; parameters {entrance:main,impl:gameface};
id R.mods.driftkings.battle_hud.window. Manter todos os JSON R antigos, IDs e paths.
resource_id mantém validação de prefixo mods/driftkings e quatro segmentos.
validate deve usar união exata recursos de componentes + infraestrutura, impedir
colisões/paths partilhados e conferir path/manifesto/HTML gerado dos dois documentos.
Manifesto ui.assets acrescenta:
mod/res/gui/gen_resources/driftkings.battle_hud.json e
mod/res/gui/gameface/mods/driftkings/battle_hud/window.html.
Targets no futuro wotmod: res/gui/gen_resources/driftkings.battle_hud.json e
res/gui/gameface/mods/driftkings/battle_hud/window.html. Sem nova startup feature,
sem alteração component_list, dependências externas ou configurações de publicação.
Pipeline existente só empacota o output gerado presente e validado; não acrescentar
um gerador de patches CT nem editar builds existentes para transportar este recurso.

### Matriz mínima e aceitação futura

| Camada | Verificação mínima | Evidência para aceitar implementação |
|---|---|---|
| Estática | Catálogo, R, manifesto, paths/case, outputs | 20/0/2, 23 Layouts distintos, host fora de GAMEFACE; união exata, targets únicos, gerados coerentes |
| Estática | Composição/compat | 15 JS/8 CSS iguais em URL/ordem; HTML neutro e antigo iguais; outros outputs sem delta; negativos rejeitados |
| Python 2.7/3 | Resolver/host/cartões | HostID independente; nove schemas/commands originais; uma janela por HUD; oito cartões funcionam sem TeamStrength; repeated loading |
| Python 2.7/3 | Erros/teardown | Recurso neutro inválido não abre raiz antiga; falha de cartão isolada; finalize/reopen, testes G3 preservados |
| Frontend clássico | Documento novo/renderers | Nove owners/roots/callbacks independentes, init/replacement/dispose/reopen, frames/timers/listeners limpos, input/posição/tema preservados |
| Pacote futuro autorizado | ZIP/R/caminhos/assets | Dois HTML físicos, um host selecionado; nenhum recurso faltante/duplicado; hashes de assets preservados |
| CT adiado | Carregamento/input/lifecycle | R real resolve; nove HUD/visuais/drag/Ctrl/V; entrada/saída/segunda batalha, TeamStrength desativado, logs Wulf/Gameface/performance/outros mods |

Suites existentes alvo: test_own_window_catalog, test_gameface_architecture,
test_own_battle_window Python/JS; testes screen/reticle/health/main_gun para contratos
compartilhados; consumers de validate para regressão de contagem/recursos. Verificações
mínimas acompanham G6, não dependem do futuro G7. Nada executado nesta análise.
Validação local poderá concluir source pass, nunca CT runtime pass. Runtime adiado por
decisão do responsável; build/instalação/jogo exigem autorização separada.

### Riscos, rollback atómico e decisões

Alto: novo recurso não registado no cliente/colisão, raiz dupla, drift de composição,
alteração inadvertida do lifecycle/input. Médio: manifesto omitir host ou validar
infraestrutura como componente, capitalização e fixture mascarar recurso errado.
Mitigação: metadata única, allowlist exata, shared ui, testes negativos e IDs distintos,
manter G1–G3 e nenhum fallback silencioso. Outros modos/realms/clientes não recebem
compatibilidade por inferência; patches CT existentes ficam intactos. Outro mod pode
colidir no namespace; inspeção/testes locais não provam coexistência runtime.

Rollback atómico futuro sobre a baseline pós-G5: catálogo/core/own_window, gerador,
components.json, dois HTML, novo JSON R e testes relacionados em conjunto; retirar
somente novos paths G6 e deltas aprovados, restaurar seleção TeamStrength e geração
antiga. Preservar descarte G3, JS G2, testes/scheduler G1 e migração beta.9. Não usar
reset/clean nem restaurar HEAD inteiro. Antes de implementação, registar hashes/diff
pré-G6 e lista de novos paths no âmbito aprovado; backup adicional exige autorização.
Nenhuma restauração executada. Artefactos originais permanecem referência independente.

Decisões pedidas para futura implementação: aprovar nomes provisórios battle_hud/window,
BATTLE_HUD_HOST/resource/layout/asset_priority no catálogo existente; JSON R adicional
fora de GAMEFACE; empacotamento ui/shared; retenção do HTML antigo gerado idêntico sem
segunda raiz/fallback; mapa atómico e testes acima. Não implementar nem iniciar G7
até autorização expressa. Observação de exceções de MarksKit permanece separada.
G6 — AWAITING_APPROVAL.
G6 — NEUTRAL HOST MIGRATION PLAN: COMPLETE (análise).
PRODUCTION CODE UNCHANGED — PASS; ORIGINAL BETA.9 PRESERVED — PASS.

## 19. Fase 3 — G6: implementação do host neutro

Data: 2026-11-12, Europe/Lisbon.
Autorização expressa: pedido anexado «FASE 3 — G6: Implementação do Host Gameface
Neutro», implementação controlada e atómica, sem build/instalação CT. Plano da secção
18 aprovado, Opção B; nomes definitivos e compatibilidade transitória aprovados.
G6 APPROVED_FOR_IMPLEMENTATION → IN_PROGRESS → VALIDATION_PENDING.
Fase 3 permanece IN_PROGRESS; G7 não iniciado. G4/G5 mantidos sem refatorizações.

### Baseline, identidade e âmbito

Worktree exclusiva Driftkings_SettingsLab_reorganization, branch reorganization/settingslab,
HEAD bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3. Inicial 56 caminhos, 34 M / 3 D /
19 untracked, staging vazio. Hashes da worktree capturados antes de editar.
Catálogo BATTLE_HUD_HOST fora de GAMEFACE contém só resource/layout/asset_priority;
recurso mods/driftkings/battle_hud/window, layout coui neutro battle_hud/window.html,
prioridade histórica ('DriftkingsTeamStrength',). Nove specs originais preservadas.
23 Layouts distintos; 22 entradas GAMEFACE, 20 native / 0 OpenWG / 2 own lobby windows.

Ficheiros com delta G6:
- mod/res/scripts/client/driftkings/interface_catalog.py
- mod/res/scripts/client/driftkings/gameface/core.py
- mod/res/scripts/client/driftkings/gameface/battle/own_window.py
- build_tools/generate_ui_catalog.py
- build_data/components.json
- mod/res/gui/gen_resources/driftkings.battle_hud.json (novo)
- mod/res/gui/gameface/mods/driftkings/battle_hud/window.html (novo, gerado)
- tests/build/test_own_window_catalog.py
- tests/runtime/integration/test_gameface_architecture.py
- tests/runtime/battle/test_own_battle_window.py
- tests/frontend/battle/test_own_battle_window.js
- este progresso, única documentação alterada.

core.resource_id alarga a allowlist exclusivamente ao host declarado; import da
metadata é tardio dentro do resolver, preservando imports dos consumidores de modelos.
JSON R segue Layout/entrance main/impl gameface; manifesto shared ui reclama os dois
novos targets. Expansão dos manifestos: 334 targets, todos únicos; novos paths só ui.
Nenhum startup component, config, dependência externa ou módulo R Python criado.
Host Python remove HOST_FEATURE e resolve BATTLE_HUD_HOST.resource. _cards, factories,
WeakKeyDictionary, flags/layer, hooks, ownership e cleanup G3 permanecem intactos.
Nenhum fallback antigo/OpenWG. Comentário indica identidade neutra ainda sem teste CT.

### Geração e integridade

Executada API outputs() do gerador existente com escrita filtrada EXCLUSIVAMENTE para
battle_hud/window.html e battle_statistics/model.html, conforme autorização; sem --write
global, sem escrita de AS3 ou bootstrap. Antigo HTML conserva hash pré-G6; o novo tem
bytes iguais. Os dois derivam da mesma string gerada. Identidade do destino e prioridade
de assets estão separadas. validate verifica metadata/colisões, R união, paths, manifesto,
composição e outputs. Ordem/URLs dos 15 JS e 8 CSS permanecem os da baseline.
Validação do gerador executada sem geração adicional: flash7/gameface22/injected0/native20.
Nenhum renderer/helper/CSS, factory/payload, configuração, patch CT ou build_config alterado.

### Testes e resultados

- Runtime direcionado final Python 3: 74 PASS, zero expectedFailure.
- Mesmo conjunto em F:/Python27/python.exe: 74 PASS, zero expectedFailure.
- Módulos: own_battle_window, screen_texts, reticle_texts, vehicle_health_gameface,
  high_caliber, gameface_architecture e native_documents. Não é regressão completa.
- test_own_window_catalog: 5 PASS, incluindo schema/R/prioridade/compat/determinismo,
  paths do manifesto e ausência de packaging/metadata inválida rejeitados.
- Frontend own_battle_window: nove renderers e 14 regressões G2 PASS.
- Frontend screen_text, reticle_text, vehicle_health e main_gun: PASS.
- AST dos sete Python afetados e node --check do teste JS: PASS.
- isort --check-only: catálogo/core/own_window/test_own_window_catalog/test_own_battle_window
  PASS. Check alargado assinalou imports pré-existentes no gerador/integration; blocos
  de imports comparados com original sem alterações. Nenhuma formatação global aplicada.
- git diff --check delimitado: PASS. Avisos CRLF/LF são do Git, sem erros de whitespace.

Primeiras execuções expuseram pressupostos de fixtures: catálogo de packaging sem plugins;
import eager de nova metadata no stub core; ID do host confundido com cartão TeamStrength;
lista de filhos incluindo agora infraestrutura. Corrigidas fixture/asserções de identidade
sem remover regressões G3. Import metadata movido ao resolver para preservar fronteira de
carregamento. Runner Python 2.7 usa TestLoader separado por diretório de descoberta.
Resultado final inclui teste dos oito HUD sem TeamStrength e falha de recurso neutro sem
fallback; resource_id mantém antigos e rejeita desconhecidos. Nenhum teste extra fora
dos quatro ficheiros de testes autorizados foi alterado.

### Preservação e rollback

Hashes pré/pós delimitam as alterações aos doze ficheiros acima; nenhuma remoção G6.
O HTML antigo foi regenerado mas ficou byte a byte igual. Novos paths: apenas JSON R
e HTML neutros. Regressões G1–G3 e política de destroy falhado preservadas.
Beta.9 original conserva SHA-256
22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9.
Sem builds, instalações, commits, push, reset/clean/stash ou alterações CT.

Rollback a executar só com autorização: aplicar inverso do delta G6 nos nove ficheiros
existentes de produção/testes/manifesto; retirar exclusivamente os dois novos paths;
repor conjuntamente catálogo/resolver/host/gerador/manifesto e testes sobre baseline
pós-G5. HTML antigo já é idêntico; verificar hash. Preservar G3 no own_window e todos
os deltas beta.9/G1/G2/G4/G5. Não usar checkout/reset do HEAD, nem restaurar só um
módulo isolado. Este progresso conserva histórico; rollback documental deve manter
rastreabilidade. Nenhum rollback executado, nenhum backup adicional criado.

### Limites e aprovação

Novo R resolvido apenas em análise estática/fixtures, ainda sem carregamento real no
cliente. CT disponível segundo responsável, mas runtime reservado para depois da
reorganização. Input/layout/fonts/lifecycle/performance/coexistência real e independência
sem OpenWG continuam pendentes; não há CT RUNTIME PASS. MarksKit exception isolation
permanece observação separada, não corrigida. Fase 3 não COMPLETE; G7 não autorizado.
G6 — NEUTRAL HOST MIGRATION PASS (source/tests locais).
G6 — VALIDATION_PENDING; confirmação do responsável e CT pendentes.
FASE 3 — IN_PROGRESS.

Conferência adicional do original: 1011 ficheiros de fontes/testes/recursos coincidem
com o snapshot preservado da Fase 0; toolchain.local.json privado fica fora desta
comparação de fontes (a preservação privada é separada). Sem leitura de segredos no output.

Hashes pré-G6 dos ficheiros existentes com delta (para conferência do rollback):
build_data/components.json | 9e0873539bc376d1a5aee369cda62aee19232909c13207504dd9197b904fcd8a
build_tools/generate_ui_catalog.py | 6623ce78430fb21ca71f4df5cb56d60c8ee0ebd36b2abdae03e9ac4787229604
tests/build/test_own_window_catalog.py | 7d9fb040b6f765788188ddeda33bb4afef69695ee57a25d8f8021d07b0a7d43a
tests/runtime/battle/test_own_battle_window.py | f59f8a9f52b7d93037970fd04caa5ad07631a6f99ddfcc9a2b2cf3e4c9e88685
tests/runtime/integration/test_gameface_architecture.py | e7bc8d4ff6b5bfe93e123df036c322613378b47f1ad8f01b34888716dd8f5c05
tests/frontend/battle/test_own_battle_window.js | a68f1266305d1e378b1213b42bc252af1a52c188749e6b450965e62d2ad16ad2
mod/res/scripts/client/driftkings/interface_catalog.py | c68e87fbe3db9feba6a947c90abf459d98e8614514525dbd5914553077cb5ad5
mod/res/scripts/client/driftkings/gameface/core.py | ef004c87398d2f9ebe0e8c3ed3bb6f31d1043e2e782f641b7b3ae035a60e37e9
mod/res/scripts/client/driftkings/gameface/battle/own_window.py | b394ac41ecd5c853270f39b969ed8cc738b9eeb31d8ad6d5db092780816b1bad

Git final G6: 59 caminhos, 35 M / 3 D / 21 untracked; staging vazio;
branch e HEAD intactos. Original: 46 caminhos, staging vazio.
HTML novo/antigo SHA-256: 60c111911b77ba820235352cb3bcca2cf2fd77b16de1968807d2bb6cd2c91667.
PRODUCTION BASELINE PRESERVED OUTSIDE WORKTREE — PASS.
ORIGINAL BETA.9 PRESERVED — PASS.

## 20. Fase 3 — G7: validações cruzadas do catálogo

Data: 2026-11-12, Europe/Lisbon.
Autorização expressa: pedido anexado «FASE 3 — G7: Validações Cruzadas do Catálogo
Gameface», implementação limitada às validações existentes e testes. Aceitação do G6
registada ao nível do código e testes locais: COMPLETE nesse âmbito; resolução CT
real do novo R continua pendente. G1–G6 aceites localmente, não há CT RUNTIME PASS.
G7 APPROVED_FOR_IMPLEMENTATION → IN_PROGRESS → VALIDATION_PENDING.
Fase 3 VALIDATION_PENDING; não COMPLETE. Fase 4 não iniciada.

### Baseline e âmbito

Worktree Driftkings_SettingsLab_reorganization, branch reorganization/settingslab,
HEAD bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3. Inicial 59 caminhos: 35 M / 3 D /
21 untracked, staging vazio. Hashes da worktree capturados antes das alterações.
Lidos plano diretor, progresso e relatórios G1–G6. Sem divergência material inicial.

Ficheiros alterados exclusivamente:
- build_tools/generate_ui_catalog.py (somente read_catalog/validate; composição intacta).
- tests/build/test_own_window_catalog.py.
- tests/runtime/integration/test_gameface_architecture.py.
- este progresso, única documentação alterada.
Nenhum ficheiro novo ou removido no G7. Nenhuma alteração funcional ao Python do mod,
catálogo, host, modelos, adaptadores, renderers/helpers/CSS, recursos, HTML ou manifesto.

### Validações acrescentadas

read_catalog inspeciona chaves dos dicts AST antes de literal_eval, evitando que nomes
ou campos repetidos sejam silenciosamente sobrescritos. validate recusa recursos de
componentes repetidos. Valida identidade/schema do host fora de GAMEFACE e mantém
verificações R/path/owners/assets existentes; classificação final exige 22 componentes,
20 nativos, dois owners None e nove own_window. Host não entra na contagem funcional.

Validador reutiliza read_components/expand_asset existentes para confrontar manifesto
com recursos e outputs, sem compilador/toolchain/artefactos gerados. Recusa targets
repetidos, host ausente ou fora de ui/shared/enabled. Quando recebe plano de packaging,
valida também unicidade desse plano. Número 334 fica só como referência independente
no teste de baseline, não como segundo manifesto no validador. O import mantém suporte
à chamada como módulo e CLI; primeira execução revelou necessidade desse fallback.

AST do _open confirma uma única resolução resource_id(BATTLE_HUD_HOST['resource']);
teste negativo injeta seleção adicional da raiz antiga. É guarda estática localizada
sobre o nosso host, não inspeção genérica de recursos/loaders do WoT nem prova runtime.
Geração/composição e APIs funcionais não alteradas; outputs() executado só em memória
para confirmar determinismo e coerência. Nenhum HTML foi escrito.

### Testes negativos (alterações simuladas em memória)

- Nome de catálogo repetido, owner JS repetido, resource de componente repetido.
- Infraestrutura adicionada como componente funcional.
- Declaração R neutra ausente ou duplicada.
- Layout anfitrião declarado, mas ficheiro ausente.
- Output neutro ausente no manifesto ou target duplicado; plano com target repetido.
- URL HTML inválido, script obrigatório retirado e ordem de scripts trocada.
- Duas seleções de raiz em _open.
- Documento transitório divergente do gerado.
- Resolver confrontado com cinco recursos desconhecidos/malformados; fixture R é
  permissiva, portanto retirar a allowlist causa falha real nestas asserções.
Casos preexistentes de catálogo inválido, scripts removidos/invertidos/duplicados e
metadata/prioridade inválidas continuam a passar. Sem alterar ficheiros reais para
simular negativos e sem snapshots/baselines substituídos.

### Resultados finais e contratos

- Python 3, testes build catálogo: 11 PASS.
- Python 3, manifesto: 6 PASS.
- Runtime Python 3: 34 PASS (own_battle_window, gameface_architecture, native_documents).
- Runtime Python 2.7: os mesmos 34 PASS, zero expectedFailure.
- Frontend own_battle_window: PASS, nove renderers e 14 regressões lifecycle G2.
- Validador CLI: flash7/gameface22/injected0/native20, PASS.
- AST dos três Python alterados, outputs() determinísticos/coerentes e diff --check
  delimitado: PASS. Avisos Git CRLF/LF sem erros whitespace; sem reformatação global.

Catálogo 20/0/2; nove HUD/modelos independentes; 23 Layouts; 334 targets únicos.
Novo host continua ui/shared; individuais mantidos. Dois HTML continuam idênticos,
15 JS/8 CSS, mesmos URLs e ordem. Composição funcional, roots runtime, resource_id,
input/dragging/configs e lifecycle G1–G3 permanecem código idêntico ao pré-G7.
Não executada regressão completa, build, instalação, gerador --write ou arranque CT.

### Preservação, riscos e decisões

Beta.9 original verificada por SHA-256:
22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9.
Hashes pré/pós da worktree verificam exclusividade dos quatro ficheiros acima.
Original e CT não escritos; fontes/artefactos da Fase 0 preservados.
Risco restante: validação estática/fixtures não prova o carregamento R, DOM/layout,
input, performance ou coexistência em cliente real. CT reservado para depois da
reorganização; independência sem OpenWG ainda não demonstrada em runtime.
Guardas de contagem/hash/composição são baseline intencional; uma expansão funcional
futura exige autorização e atualização justificada dos testes independentes, não
remoção automática da guarda. AST _open verifica seleção, não comportamento arbitrário
adicionado fora desse método. Pendência MarksKit exception isolation continua separada.

Rollback G7: inverter apenas deltas de read_catalog/validate e testes correspondentes
sobre baseline pós-G6, conservando host neutro/G1–G6. Nenhum reset/clean/stash, commit,
push ou rollback executado. Não criar nova arquitetura ou alterar transporte por causa
de um negativo. Aceitação G7 e encerramento da Fase 3 exigem confirmação expressa.
G7 — CATALOG VALIDATION PASS.
FUNCTIONAL PRODUCTION CODE UNCHANGED — PASS.
ORIGINAL BETA.9 PRESERVED — PASS.
G7 — VALIDATION_PENDING.
FASE 3 — VALIDATION_PENDING.

Git final G7: 59 caminhos, 35 M / 3 D / 21 untracked; staging vazio;
branch/HEAD preservados. Original mantém 46 caminhos, sem staging.

## 21. Fase 4 — Auditoria e planeamento Flash/Scaleform

Data: 2026-11-12, Europe/Lisbon.
Autorização: pedido anexado «FASE 4 — Auditoria e Planeamento da Reorganização
Flash/Scaleform», análise técnica/documentação exclusivamente. «continuar» mantém
este âmbito. Única escrita autorizada: este progresso; implementação não autorizada.
FASE 3 — COMPLETE (LOCAL VALIDATION), aceite expressamente no pedido. G1–G7 aceites
nos âmbitos locais. Continuam pendentes para Fase 7: host neutro no CT, R runtime,
independência efetiva sem OpenWG, input/dragging/lifecycle real; MarksKit exception
isolation permanece revisão futura separada. Aceitação local não equivale a runtime.
Fase 4 PENDING → IN_ANALYSIS → AWAITING_APPROVAL; nenhum grupo iniciado.

### Baseline e método

Worktree Driftkings_SettingsLab_reorganization, branch reorganization/settingslab,
HEAD bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3; 59 caminhos, 35 M / 3 D / 21 untracked;
staging vazio, sem divergência material. Plano diretor/progresso lidos; conclusões das
Fases 1–3 reutilizadas. Leitura de fontes, manifests, SWC ZIP/catalog e tags SWF na
beta.9 preservada; sem compilação, disassembly externo, testes completos ou instalações.
Inventário AS3 feito por paths/packages/declarations, não por compilador AS3. Não
confundir esta inspeção com prova de linkage/bytecode de todas as classes.

### Inventário confirmado

65 fontes .as: battle 47; shared 11; vehicle_markers 7. Há duas classes internal
(panelitemcache, minimapzoomstate) e uma interface própria disposable. As restantes
declarações principais são classes públicas. Packages próprios estão em minúsculas,
mas muitas classes e a interface estão em minúsculas, contrastando com PascalCase.
Não há SWF fonte em mod/: três filmes distribuídos vêm de generators do build.
Oito SWC, todas com SHA-256 igual ao manifest; versão fonte/export 2.4.2.5516,
jogo 2.4.2.0. SWC são dependências binárias externas, não fontes a refatorizar.

Distribuição completa por package (ficheiros/classes):
- (default) [7]: DriftkingsVehicleMarkersFlash, PlayerPanelListLeftUI, PlayerPanelListRightUI, PlayersPanelListItemLeftUI, PlayersPanelListItemRightUI, driftkingsbattle, driftkingspanels.
- driftkings.battle.base [1]: battledisplayable.
- driftkings.battle.components.debug_panel [1]: debugpanelui.
- driftkings.battle.components.distance_marker [4]: config, disposable, distancemarker, distancemarkerui.
- driftkings.battle.components.minimap [15]: artilleryaim, geometrylayer, mapgeometry, mapscale, mapsizelabel, minimapenhancementsui, minimaplines, minimapzoom, minimapzoomstate, nativestyles, nearbyenemies, rangecircles, vehicleicons, vehiclelabel, vehiclelabels.
- driftkings.battle.components.overlay [2]: overlayelement, overlayui.
- driftkings.battle.components.ratings [13]: extrafields, frameprofiler, loadingclock, nativestate, panelhook, panelitemcache, panelitems, panelrenderer, panelrow, ratingscreens, rowlookup, tablerenderer, viewbindings.
- driftkings.battle.components.sixth_sense [2]: radialprogressbar, sixthsenseui.
- driftkings.battle.components.vehicle_health [1]: ammohealthui.
- driftkings.battle.factory [2]: componentcatalog, componentfactory.
- driftkings.utils [9]: align, colorutils, constants, fontlibrary, imageloadercomponent, screentransform, shadowutils, textext, utils.
- driftkings.utils.tween [2]: tween, tweenevent.
- driftkings.vehiclemarkers [6]: VMDamage, VMFields, VMHealthBar, VMIcons, VMState, VMText.

### Mapa prioritário de alterações (propostas, não execução)

Paths relativos a flash_source/battle/src/ nas oito primeiras linhas. A classe pública
e o nome do ficheiro devem mudar juntos, incluindo construtor/import/type/new.

| Ficheiro | Símbolo atual → proposta | Referências / contrato | Classificação | Risco | Testes / rollback |
|---|---|---|---|---|---|
| driftkings/battle/base/battledisplayable.as | battledisplayable → BattleDisplayable | extends net.wg BattleUIDisplayable; 6 subclasses próprias e componentfactory; resize/visibility e as_setBattleHudVisible fixos | RENAME_CANDIDATE | Médio | Imports/herança, seis HUD, visibilidade/resize/dispose; inverso do conjunto base+consumidores |
| driftkings/battle/factory/componentfactory.as | componentfactory → ComponentFactory | driftkingsbattle chama create; catálogo gerado e cast da base; registerFlashComponentS/isFlashComponentRegisteredS protegidos | RENAME_CANDIDATE | Médio | Imports, aliases, factory battle/ratings sem duplicação; restaurar factory+entrypoint |
| driftkings/battle/factory/componentcatalog.as | componentcatalog → ComponentCatalog | Gerado por generate_ui_catalog.py AS3/template; consumidor componentfactory | GENERATED_SOURCE | Médio/alto | Alterar gerador e fonte declarativa, outputs/checks; rollback gerador+output+imports, nunca editar só output |
| driftkings/battle/components/ratings/panelrenderer.as | panelrenderer → PanelRenderer | classe interna funcional, pública AS3; ratingscreens new; panelrow/cache/nativestate | RENAME_CANDIDATE | Médio | Imports/new/row cache/restore/profiling; restaurar ficheiro e ratingscreens |
| driftkings/battle/components/ratings/panelrow.as | panelrow → PanelRow | criada/usada por panelrenderer, sem alias Python próprio; overrides native por string | RENAME_CANDIDATE | Médio | Cache/invalidations/restore/posições, imports/compilação; rollback row+renderer |
| driftkings/battle/components/ratings/viewbindings.as | viewbindings → ViewBindings | ratingscreens new; scan getQualifiedClassName e membros nativos dinâmicos | RENAME_CANDIDATE | Médio/alto | Loading/tips/frontline/panel por modo; mudar só type próprio, preservar strings nativas; rollback par de fontes |
| driftkings/battle/components/sixth_sense/sixthsenseui.as | sixthsenseui → SixthSenseUI, condicionado | extends battledisplayable; catálogo + SixthSenseMeta.FLASH_CLASS; alias SixthSenseView; Embed error.png | DYNAMIC_REFERENCE; REQUIRES_BINARY_VERIFICATION | Alto | ABC/SymbolClass/Embed, getSettings/playSound/onIconReady/getTimerString/as_show/as_hide, timers/loader; restaurar catálogo/meta/gerado/SWF juntos |
| driftkings/battle/components/vehicle_health/ammohealthui.as | ammohealthui → AmmoHealthUI, condicionado | extends battledisplayable; catálogo + AmmoHealthMeta.FLASH_CLASS; alias DriftkingsAmmoHealth; ConsumablesPanel | DYNAMIC_REFERENCE; REQUIRES_BINARY_VERIFICATION | Alto | Classe publicada/DAAPI, docked HP, inherited transforms/visibility e dispose; rollback catálogo/meta/gerado/SWF |
| driftkingsbattle.as / driftkingspanels.as | manter nomes e outputs | Document classes e bibliotecas requeridas Python; SymbolClass id0 observado | KEEP; EXTERNAL_CONTRACT | Alto se renomeados | Bibliotecas/ordem/DAAPI; conservar nomes SWF e root classes |
| PlayersPanelListItemLeftUI/RightUI.as | manter | linkage do cliente, extends PlayersPanelListItem; draw/updatePositions; dkVehicleID | EXTERNAL_CONTRACT | Muito alto | Classes ABC e symbols nativos reais, prioridade de carregamento; não renomear |
| PlayerPanelListLeftUI/RightUI.as | manter | extends PlayersPanelListLeft/Right, setVehicleData/updateOrder, VO e interfaces SWC | EXTERNAL_CONTRACT | Muito alto | Row identity/ordem/resize/modos; preservar contratos exatos |
| driftkings/battle/components/ratings/panelhook.as | manter inicialmente | Compilado em DOIS SWF; primeira definição carregada partilha Dictionary/dirty com renderer | DYNAMIC_REFERENCE; KEEP | Alto | Compilar/inspecionar ambos SWF atomicamente se algum dia mudar; não tratar como duplicação dispensável |
| shared/as3/driftkings/utils/fontlibrary.as | manter | Fonts Embed/registerFont; símbolos fontlibrary_Face0..9 observados em battle e marcadores | KEEP; REQUIRES_BINARY_VERIFICATION | Alto | Font names/glyphs/font IDs/SymbolClass e remapping; preservar TTF/nomes/hashes |
| shared/as3/driftkings/utils/tween/tween.as e tweenevent.as | não renomear neste primeiro grupo | Event metadata type contém FQN por string; timers/dispose | DYNAMIC_REFERENCE; INVESTIGATE | Médio/alto | Metadata, eventos motion*, late timer/dispose; mapear antes de PascalCase |
| components/distance_marker/disposable.as | disposable → IDisposable como candidato posterior | Interface disposeState própria; mapear implementadores antes de aprovar | INVESTIGATE | Médio | Compilação implements e lifecycle; preservar método disposeState |
| components/ratings/panelitemcache.as e minimap/minimapzoomstate.as | PascalCase apenas em grupo futuro | classes internal, ficheiros não exportam classe pública; regras de resolução de package/compilador | INVESTIGATE | Médio | Import/resolução AS3 com compilador real; não presumir equivalência de public class |
| vehicle_markers/DriftkingsVehicleMarkersFlash.as | manter | QName vazio literal em vehicle_markers_patch.py; entrypoints static chamados por ABC nativo | EXTERNAL_CONTRACT; DYNAMIC_REFERENCE | Muito alto | Lock/patch/QName/stack/ABC/font remap; conservar helper e patch em conjunto |
| vehicle_markers/driftkings/vehiclemarkers/VM*.as | manter PascalCase | VMState/Fields/Text/Icons/HealthBar/Damage já coerentes | KEEP | Médio | Marcadores/slots, restauração e estatísticas; nenhuma reorganização necessária |
| outros minimap/overlay/distance/debug/utils | manter nesta proposta | Classes próprias de nomenclatura candidata, dependências por funcionalidade | INVESTIGATE | Médio | Mapear por grupo antes de alargar lista; não executar rename global |
| mod/.../flash/battle/meta/*.py | manter APIs; só FQN se classe publicada renomeada | Sete FLASH_CLASS, as_*/callback Python↔Flash | KEEP; DYNAMIC_REFERENCE | Alto | Schema/DAAPI e registo; não apagar adaptadores por aparente legado |

Para cada candidato interno, referências AS3 diretas encontradas:
- battledisplayable: base, componentfactory, debugpanelui, distancemarkerui,
  minimapenhancementsui, overlayui, sixthsenseui e ammohealthui (8 ficheiros).
- componentfactory: próprio ficheiro e driftkingsbattle (2).
- componentcatalog: próprio output e componentfactory (2).
- panelrenderer: próprio ficheiro e ratingscreens (2).
- panelrow: próprio ficheiro e panelrenderer (2).
- viewbindings: próprio ficheiro e ratingscreens (2).
- sixthsenseui/ammohealthui: output gerado e próprio ficheiro, mais catálogo/Python meta.
Ausência de outra referência textual não prova ausência em ABC/SWC/mod externo.

### Contratos Python ↔ AS3 e lifecycle

Catálogo FLASH_COMPONENTS tem 7 aliases; gen componentcatalog liga alias a Class,
registry BattleViews.register confere FLASH_CLASS/section e recusa duplicações.
BattlePackageRegistration publica driftkings.flash.battle/BATTLE_REQUIRED_LIBRARIES;
remove só registos próprios e fecha handlers. BattleViewHandler acompanha aliases do
cliente, cancela BigWorld callback, espera DAAPI e chama por getattr as_DriftkingsCreate
ou as_DriftkingsCreateRatings. Factory acrescenta filho, define battlePage e chama
registerFlashComponentS. Preservar todos estes métodos, aliases e superfícies.

| Alias | FQN AS3 final no catálogo | Python / dados e callbacks |
|---|---|---|
| DriftkingsAmmoHealth | components.vehicle_health.ammohealthui | flash/battle/vehicle_health.py, meta/vehicle_health.py; as_setHealth (fração/texto/cor/style/visível) |
| DistanceMarkerView | components.distance_marker.distancemarkerui | target_distance.py, meta/distance_marker.py; as_applyConfig/as_isPointInMarker e py_requestFrameData |
| DriftkingsDebugPanel | components.debug_panel.debugpanelui | debug_panel.py, meta/debug_panel.py; relógio/debug |
| DriftkingsOverlay | components.overlay.overlayui | overlay.py, meta/overlay.py; as_reset/as_create/as_update/as_remove; onElementMoved |
| DriftkingsRatingScreens | components.ratings.ratingscreens | player_ratings.py, meta/players_panel.py; as_setRoster, reportState/hoverPanel/reportWidths/reportScreens/reportPerformance |
| MinimapEnhancementsView | components.minimap.minimapenhancementsui | minimap_enhancements.py, meta/minimap.py; presentation/vehicle/ranges/camera |
| SixthSenseView | components.sixth_sense.sixthsenseui | sixth_sense_alert.py, meta/sixth_sense.py; as_show/as_hide, getSettings/getTimerString/playSound/onIconReady |

Prefixo AS3 completo em todas as linhas: driftkings.battle.; aliases/nomes dos métodos
não são alvos de PascalCase. ComponentMeta deduplica setters escalares, compromete cache
após sucesso e invalida em dispose/recriação; OverlayScene conserva estado e reenvia
snapshot ao attach, rejeita callbacks de view antiga. São responsabilidades existentes
adequadas; não introduzir bridge paralelo nem event bus novo.

Lifecycle observado: battledisplayable associa/remove RESIZE e combina requested/hud/
native visibility; SixthSense fecha loader/listeners/timers/tweens; ammohealthui remove
UPDATE_POSITION de ConsumablesPanel; minimap tem timer próprio removido em dispose;
ratingscreens remove ENTER_FRAME/ADDED_TO_STAGE/MOUSE_MOVE e restaura overrides/caches;
ImageLoader trata callbacks do loader atual; tween tem disposed/stop/remoção de timer.
Inspeção destes percursos não prova libertação perante todas as exceções no cliente.
Não foi demonstrado defeito runtime nem autorizada correção de lifecycle na Fase 4.

Referências dinâmicas protegidas: viewbindings usa tipos Frontline e membros listLeft/
listRight/playerNameCollection etc.; panelrow mexe em campos nativos por string;
player_ratings carrega PANELS_LIBRARY só para classic page com painel ativado.
Alguns ramos de deteção TAB/loading podem ser compatibilidade histórica ou usados em
modos alternativos; não eliminar com base na migração Gameface do TAB clássico.
Hooks de login/lobby/native_preferences/reticles/game_log também são integração nativa,
não classes AS3 próprias dispensáveis; remoção exigiria mapa funcional separado.

### Pipeline e verificação binária em leitura

build_config battle_flash/panels_flash: entrypoints driftkingsbattle.as/driftkingspanels.as,
source paths battle/src e shared/as3; Java+mxmlc/Flex/framework.swc/playerglobal, oito
SWC externos com manifest/hashes; player11.1, SWF14, 1024x768, 30fps, strict/optimize.
compiler.py:161..178 gera output isolado, normaliza data de compilação e valida SWF.
.as3proj é configuração IDE alternativa, não substituir pipeline canónico por ela;
alterar entradas/classpaths se um futuro rename as afetar. Nenhuma ferramenta executada.

Marcadores têm pipeline DIFERENTE: build_tools/vehicle_markers.py compila helper
(player11.0/SWF13), lê movie nativo gui-part2.pkg/gui/flash/battleVehicleMarkersApp.swf
com SHA fixo de native-lock.json; usa RABCDAsm/abcexport/rabcasm/abcreplace e patches
VehicleMarker/VehicleMarkersManager, injeta helper/fontes e exige dois ABC. Produto
final conserva estrutura/header nativo; não esperar que header seja o do helper.
Native lock: 34d92354f1c755313b99fd4e268bb78dc130ece24797a271aece5f0a7346537e.
Não reler/alterar cliente CT nem atualizar lock para contornar incompatibilidade.

Inspeção de tags SymbolClass/ExportAssets/DoABC dos SWF já empacotados na beta.9:
- driftkingsbattle.swf: versão14, 1 ABC, SymbolClass id0 driftkingsbattle;
  10 símbolos fontlibrary_Face* e sixthsenseui_DefaultIcon.
- driftkingspanels.swf: versão14, 1 ABC, SymbolClass id0 driftkingspanels.
- battleVehicleMarkersApp.swf: versão11 (nativo), 2 ABC, símbolos de fontes próprias.
As quatro classes linkage dos painéis NÃO aparecem como SymbolClass próprio neste
code-only SWF; isso não elimina a dependência: vínculo acontece pelos nomes de classes
ABC e símbolos do filme do cliente. Precisa de inspeção ABC/SWF nativo futura.
A inspeção de tags não valida todos os traits/methods/imports ABC nem prova bytecode
igual à fonte atual. Não foi descompilado ou reconstruído qualquer SWF.

Fontes/outputs/manifesto:
battle/src/driftkingsbattle.as → battle_flash → build/flash/driftkingsbattle.swf
→ res/gui/flash/driftkingsbattle.swf, manifesto ui;
battle/src/driftkingspanels.as → panels_flash → build/flash/driftkingspanels.swf
→ res/gui/flash/driftkingspanels.swf, ui;
vehicle_markers/DriftkingsVehicleMarkersFlash.as + nativo → vehicle_markers_flash
→ build/flash/driftkings_vehicle_markers.swf → res/gui/flash/battleVehicleMarkersApp.swf,
manifesto vehicle_markers. SWC não são filmes de runtime a substituir no pacote.

### Assets e configuração (reutilização da Fase 2)

Sixth Sense: 10 PNG em maps/icons/sixthsense/0.png..9.png, IDs defaultIconName persistidos;
loader usa ../../gui/maps/icons/sixthsense/<id>.png ou userIcon validado; error.png Embed
é fallback. Nunca trocar IDs por nomes visuais sem transição/aprovação específica.
Aiming angles: gun_traverse_limits.py monta ../aimingangles/<marker>/left/right/top/bottom
com sufixo _limit; manifesto inclui gui/aimingangles/**. Strings construídas dinamicamente
impedem remoção por ausência de path literal. Overlay carrega imagens/templates via
ImageLoader; panelrows/markers usam ícones nativos e locais por configuração/strings.
fontlibrary incorpora 10 aliases a partir de TTF existentes; Gameface partilha fontes
físicas mas tem renderer/transporte distinto. Não alterar nomes/glyphmaps/paths, nem
fundir renderers Flash/Gameface. Configs de markers perfis/native/custom e schemas
Python permanecem contrato. Não mover/otimizar recursos, fontes ou previews.

### Duplicações, factos e sugestões

Comprovado: nomes próprios minúsculos; output gerado; oito refs da base; FQN Python por
string; metadados tween por string; fontes/Embed geram símbolos; panelhook é compilado
em dois filmes com estado estático partilhado por identidade. Não confundir este último
com duplicação eliminável. Overrides de listas esquerda/direita são próximos mas têm
heranças/linkage distintos; conservar ambos.

Python e AS3 fazem cache em camadas distintas (dados enviados, estado nativo, DOM/movie),
não são trabalho automaticamente redundante. Scene/registry/factory/meta já separam
estado, transporte, criação e lifecycle. Não há benefício demonstrado para nova factory,
base universal ou reorganização de packages nesta fase. Recomendar renomeações editoriais
pequenas e preservar estrutura; não alterar algoritmos, ciclos de frame ou restauração.
Hipóteses não confirmadas: ramos de deteção sem utilização no CT atual, símbolos de
classe publicados fora do mod, interação de load order com outros mods. Exigem provas,
não remoção automática. Fonte/ABC completo e runtime não verificados nesta auditoria.

### Grupos futuros propostos e aceitação

F4-G1 — nomenclatura interna limitada: panelrow/panelrenderer/viewbindings; depois base
BattleDisplayable em subgrupo próprio. Exige aprovação da lista exata, imports/types/
constructors, compilação isolada do filme afetado e inspeção ABC, callbacks intactos.
Sem callback/alias/Python ou asset rename. Ganho editorial, não ganho de desempenho.
F4-G2 — catálogo/factory/gerado: ComponentFactory/ComponentCatalog e, apenas se aprovado
separadamente, AmmoHealthUI/SixthSenseUI. Alterar gerador/template/AS3 path/catalog/meta
atomicamente. Só gerar outputs afetados; Gameface e outros outputs devem ser idênticos.
F4-G3 — integração Python/Flash: auditoria focal dos FQN publicados se G2 os alterar;
nenhuma refatorização funcional proposta. Manter APIs/callbacks e perfis de modos.
F4-G4 — verificação de compilação/binário: gate OBRIGATÓRIO por grupo, não adiar até ao
fim. Duas compilações isoladas comparáveis se necessário para determinismo; SymbolClass,
ABC/exports/Embed/fonts/SWC hashes/manifesto. Qualquer build exige autorização própria,
nenhum build aprovado por esta análise. Proibir substituição de lock ou SWC em falha.
F4-G5 — consolidação: deltas/rollback/coerência final e testes proporcionais; regressão
completa só quando autorizada na integração final, CT na Fase 7. Cada grupo termina
em relatório e espera aceitação; nada implementado agora.

| Camada | Critério futuro | Testes/evidência existente a reutilizar |
|---|---|---|
| AS3 estática | packages/classes/files/imports exatos e case-sensitive; zero referência antiga própria fora das exceções | Inventário de imports/refs e compilador real; testes textuais não bastam |
| Catálogo/gerado | 7 aliases Flash, classes/meta/superfícies corretas; saída determinística; Gameface intocado | generate_ui_catalog e test_flash_architecture; gerador só quando autorizado |
| Python2.7/3 | DAAPI setters/callbacks, ownership/cache/late page/dispose intactos | test_flash_architecture (12 casos), player_panel (20), minimap (21), minimap_sector (8), markers (14), schemas |
| SWC/compilação | mesmos 8 hashes, Flex/Java/playerglobal fixos; compile limpo, outputs mapeados | SWC manifest, compiler/validate_build_data; execução futura autorizada |
| SWF/ABC | root/library names, linkages cliente, imports/classes/helper calls/fonts corretos | inspeção SymbolClass/DoABC + disassembly ABC completo futuro; test_vehicle_markers_patch remapping/ambiguidades |
| Packaging | 3 targets SWF únicos, nomes fixos, artefactos correspondentes à revisão | manifesto/build plan e hash do novo pacote, sem reaproveitar binário antigo como prova |
| Gameface | nenhum delta nas fontes/outputs/23 R/host/15JS8CSS | hashes Fase3 e validações G7 direcionadas, sem renomeações colaterais |
| CT Fase7 | SixthSense/icon/timer, docked HP, minimap, overlay, painel/modos/reorder/TAB, markers/Alt/damage/colourblind/2ª batalha | Runtime manual e logs, coexistência/outros mods e desempenho |

Nenhuma suite foi executada nesta auditoria. As contagens de casos acima vêm da leitura
dos testes, não são novos PASS. Teste DAAPI existente agrega métodos de todas as fontes;
não prova assinatura/declaring class exata. Lacuna concreta: verificar cada método na
classe correta e traits ABC depois de compilar, incluindo symbols do cliente, não só
presença de string em qualquer fonte. Testes de mocks não executam Flash AVM2/Scaleform.

### Riscos e rollback

Muito alto: linkage cliente/entrypoints SWF/helper QName/nativo protegido; KEEP.
Alto: published FQN, Embed/fonts, panelhook cross-SWF e packages externos; mapa atómico
+ binário + runtime, sem modernização estética. Médio: nomes internos/capitalização
Windows; rename por nome temporário dentro do grupo autorizado e conferência case-sensitive
na árvore/pacote (nenhum rename executado). Baixo: documentação/inventário.
SWC da versão declarada e CT real têm contratos temporais específicos; hashes corretos
não provam compatibilidade de outro build/região. Interação com mods externos permanece
risco runtime, não autorização para os modificar. Private toolchain não foi divulgado.

Rollback por grupo: patch inverso só do delta aprovado e nomes físicos/imports antigos;
G2 inclui catálogo/meta/template/output juntos; G4 guarda artefactos/hashes por revisão
e restaura fontes+SWF coerentes sem overwrite de beta.9. Não misturar símbolos novos
com bytecode antigo nem reconstruir silenciosamente locks. Preservar G1–G7/Fase3,
configs/assets/backup Fase0; nunca reset/clean original. Sem rollback executado.

### Aprovação e preservação

Pendente: aceitar relatório e selecionar lista exata F4-G1; decidir se custos de rename
justificam ganho editorial; autorizar compilação/verificação binária por grupo antes
de entregar alteração funcional. KEEP para contratos externos, fontes e marcadores.
Nenhum grupo F4 iniciado, Fase5 não autorizada. Pendências CT e revisão MarksKit mantidas.
Beta.9 SHA-256: 22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9.
Fase4 AWAITING_APPROVAL. FASE 4 — FLASH/SCALEFORM AUDIT: COMPLETE (análise estática).
PRODUCTION CODE UNCHANGED — PASS. ORIGINAL BETA.9 PRESERVED — PASS.

Git final desta análise: 59 caminhos, 35 M / 3 D / 21 untracked, staging vazio;
branch/HEAD preservados. Original mantém 46 caminhos. Única escrita executada:
este progresso; zero fontes ou binários escritos, zero ficheiros criados/removidos.

## 22. Fase 4 — F4-G1a: normalização de três classes ratings

Data: 2026-11-12, Europe/Lisbon.
Autorização expressa: pedido anexado «FASE 4 — F4-G1a: Normalização das Classes
ActionScript de Ratings». Auditoria Fase4 aceite. Implementação limitada a PanelRow,
PanelRenderer, ViewBindings e referências/testes; compilação local isolada só de SWF
diretamente afetado, sem modpack/build completo ou instalação. Fase4 IN_PROGRESS.
F4-G1a APPROVED_FOR_IMPLEMENTATION → IN_PROGRESS → VALIDATION_PENDING.
F4-G1b/F4-G2 não iniciados nem autorizados. Fase3 e pendências CT preservadas.

### Preflight

Branch reorganization/settingslab, HEAD bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3;
inicial 59 caminhos, 35 M / 3 D / 21 untracked; staging vazio. Worktree exclusiva.
Plano diretor/progresso/auditoria lidos; hashes worktree e fontes capturados antes
de editar. Três fontes conferidas contra snapshot preservado Fase0, sem divergência.
Package driftkings.battle.components.ratings; classes/construtores públicos minúsculos;
refs confinadas a PanelRenderer/ratingscreens. Pesquisa de strings AS3 não encontrou
consumidores dinâmicos dos três nomes; SWC catalog.xml não os exportam, SymbolClass e
ExportAssets dos SWF beta.9 não lhes atribuem linkage. Isto foi complementado pela
inspeção ABC posterior, não usado isoladamente como prova de ausência de consumidores.

Toolchain discover existente: Java jre1.8.0_491, Flex/mxmlc.jar existente, playerglobal
Animate 2024; oito SWC inalterados. Não existe toolchain.local.json na worktree; usada
descoberta canónica, sem copiar configuração privada ou mudar flags. RABCDAsm não foi
necessário: swfdump.jar do Flex existente inspecionou ABC. Nenhuma ferramenta instalada.

### Alterações exatas

Sob flash_source/battle/src/driftkings/battle/components/ratings/:
- panelrow.as → PanelRow.as; classe/construtor/tipos/instanciação PanelRow.
- panelrenderer.as → PanelRenderer.as; classe/construtor e referências PanelRow.
- viewbindings.as → ViewBindings.as; classe/construtor.
- ratingscreens.as: exclusivamente referências de tipo/new para PanelRenderer/ViewBindings;
  nome da classe, métodos e lógica não alterados. Não houve imports novos necessários
  porque as quatro classes permanecem no mesmo package.

Renames de ficheiros feitos via nomes temporários exclusivos para garantir case no
Windows; nenhum temporário ficou. Conferido os.listdir/filesystem: três nomes PascalCase
presentes, antigos ausentes. core.ignorecase=true mantém grafia antiga no índice até
futura preparação de commit; não foi alterado nem usado staging. git -c core.ignorecase=false
status confirma exatamente três antigos removidos e três novos presentes. A futura
consolidação Git deve registar corretamente as mudanças de case, sem perder este delta.
Teste adicional no único ficheiro tests/runtime/integration/test_flash_architecture.py
confere nomes reais, package, classes/construtores, referências e ratingscreens preservado.
Nenhum Python de produção, catálogo, gerador ou output gerado alterado.

Prova de escopo da fonte: ao inverter somente os três identificadores nos quatro AS3,
os bytes coincidem com a baseline preservada. A classe ratingscreens mudou apenas nas
referências autorizadas, não em identidade/lógica. Nenhum algoritmo/propriedade nativa,
callback/interface/alias foi renomeado; panelhook e os quatro linkage UI intactos.

### Compilação isolada e artefactos

Uma única compilação: compiler.generate existente com plan de generator battle_flash
apenas; contexto IsolatedOutput existente. Flags/entrypoint/source paths/SWC/player
inalterados. Não compilados panels_flash ou vehicle_markers_flash, pois não dependem
das três classes alteradas. Panels anterior inspecionado em ABC; markers preservado.

Área exclusiva na worktree:
build/experiments/f4-g1a-20261112/
Output: generated/build/flash/driftkingsbattle.swf.
Logs: logs/battle_flash.log. Diagnósticos: old/new/panels-swfdump.xml e binary-contracts.json.
Cópias de leitura dos filmes anteriores só nesta área experimental, sem sobrescrever
beta.9/backups. TEMP/TMP/user.home Java direcionados para workspace/temp isolado.
Nenhum output escrito no original, CT, build/unified ou builds existentes.

Hashes SWF anteriores beta.9:
- driftkingsbattle.swf: 4c42711cbc2978772378f6fa98bc929fd231899d3216bdb17a5dc7e9010ab2c7
- driftkingspanels.swf: 5649b84ec84e1ec0bee634cb664e3210b0f6450afade38db9d21ae1b940586bc
- battleVehicleMarkersApp.swf: aab221f353f2fb874e5efde4ee79c19139528cd6ad6ba70443d3127a804046be
Novo driftkingsbattle.swf:
10449ac1f7898a9959f75c33edf79d937cc8370cb9cbf6132361637dff66917c.
SWF14/30fps/document class driftkingsbattle inalterados; tamanho descomprimido 594722
bytes nos dois. Não exigida igualdade de hash entre filmes antes/depois.

### Comparação binária

Todos os tags não-ABC são BYTE A BYTE iguais, incluindo headers/fonts/SymbolClass,
ProductInfo normalizado, root e símbolos incorporados. Só DoABC mudou.
Diferenças brutas ABC incluem reordenação de pools e ordinais de scripts: não são
apenas substituições dos caracteres de nomes. Investigadas via dumps completos -abc
com ferramenta Flex, sem modificar SWF. Normalização canónica limita-se aos três nomes
autorizados e IDs sintéticos scriptN; ordem dos blocos é comparada como multiset.

Resultado: 532 corpos de método iguais após essa normalização; 644 entradas de método
com mesmas assinaturas; traits/herança/interfaces das 72 classes coincidem; nomes
novos presentes e declarações antigas ausentes. Não foram ignoradas instruções, stack/
locals/scope ou propriedades/callbacks. Ordinais de scripts mudaram com resolução de
dependências, mas os inicializadores correspondentes mantêm instruções equivalentes.
Nenhum delta funcional de bytecode adicional identificado. Relatório JSON na área
experimental. Não é execução AVM2/Scaleform nem prova de comportamento CT.

panelhook: nome/traits/métodos no battle coincidem com anterior; classe confirmada
no ABC de driftkingspanels anterior. Esse SWF não foi recompilado ou alterado; mantém
root, quatro classes UI e identidade partilhada. Carregamento Python permanece intacto.
Pipeline/helpers/QName/fonts dos marcadores e lock nativo não alterados.

### Testes direcionados

- Arquitetura Flash + player_panel: 33 PASS Python3 e mesmos 33 PASS Python2.7.
- embedded_font_assets: 2 PASS; valida packaging e aliases/fontes partilhadas.
- Validador catálogo existente: flash7/gameface22/injected0/native20 PASS.
- isort --check-only do único teste Python alterado e diff --check delimitado: PASS.
- Pesquisa em fontes AS3/Python/build_tools: zero tokens antigos dos três tipos.
- Fonte inversamente normalizada igual à baseline e verificações ABC/tags: PASS.
Na primeira execução o novo teste usava assertRegexpMatches, removido em Python3.14;
substituído por re.search/assertIsNone/IsNotNone, compatíveis com ambos. Reteste final
passou. Não alterada produção para satisfazer a fixture. Sem regressão completa.

### Preservação, rollback e limitações

Gameface/Wulf, helpers G2, catálogos/geradores, Fase3 G1–G7, configs/assets/SWC,
três nomes de SWF distribuídos e original beta.9 preservados. Hash pacote original:
22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9.
Nenhuma instalação/arranque CT/commit/push/merge/reset/clean/stash ou nova worktree.
Única documentação alterada: este progresso. Artefactos experimentais mantidos.

Rollback proposto: renomear PanelRow/PanelRenderer/ViewBindings para os três nomes
anteriores via temporário, inverter só estes tokens nos quatro AS3, retirar somente
regressão G1a se autorizado; comparar bytes com baseline. Não restaurar ficheiros
inteiros do HEAD. Binários anteriores continuam intocados; se futuramente instalado
um pacote novo, voltar ao pacote anterior coerente por hash, sem misturar source/SWF.
Nenhum rollback executado. Fase3 e restantes alterações pendentes ficam intactas.

CT real continua pendente: painel, rows/hover/reorder/modos, callbacks/performance e
segunda batalha; ausência de mudança nos dumps não substitui teste no cliente.
A grafia case-sensitive deve ser preservada no futuro staging/commit, ainda não
executado. Não iniciar G1b/G2 por inferência do PASS local.
F4-G1a — VALIDATION_PENDING.
F4-G1a — AS3 RENAME PASS (local).
SWF BINARY CONTRACTS — PASS.
GAMEFACE UNCHANGED — PASS.
ORIGINAL BETA.9 PRESERVED — PASS.
FASE 4 — IN_PROGRESS.

Git final: 64 caminhos no modo normal (core.ignorecase=true), 40 M / 3 D /
21 untracked; staging vazio. Leitura case-sensitive: 67 caminhos, incluindo os
três pares de rename; nenhuma configuração Git alterada. Hashes pré/pós confirmam
quatro fontes AS3, teste associado, progresso e outputs experimentais como único delta.

## 23. Fase 4 — F4-G1b: BattleDisplayable

Data: 2026-11-12, Europe/Lisbon.
Autorização expressa: pedido anexado «FASE 4 — F4-G1b: Normalização de BattleDisplayable».
Aceitação local F4-G1a registada: COMPLETE nesse âmbito; CT continua pendente.
F4-G1b APPROVED_FOR_IMPLEMENTATION → IN_PROGRESS → VALIDATION_PENDING.
Fase4 IN_PROGRESS. F4-G2/posteriores não iniciados nem autorizados.

### Preflight e âmbito

Worktree exclusiva Driftkings_SettingsLab_reorganization; branch reorganization/settingslab,
HEAD bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3; inicial 64 caminhos (40 M / 3 D /
21 untracked), staging vazio. Sem divergências; plano/progresso/auditoria/G1a lidos.
Hashes worktree e textos das oito fontes diretamente relacionadas capturados antes.
Base pública em driftkings.battle.base, extends net.wg.gui.battle.components.BattleUIDisplayable;
construtor battledisplayable(). Nenhuma instanciação direta da base encontrada: subclasses
herdam e factory faz cast. Pesquisa lexical de strings excluindo comentários não revelou
consumidor dinâmico; SWC catalogs sem export próprio. Baseline ABC pós-G1a tem a classe
com a herança esperada; SymbolClass não a publica. Referências externas fixas preservadas.

### Alterações exatas

flash_source/battle/src/driftkings/battle/base/battledisplayable.as → BattleDisplayable.as;
classe/construtor, sem outro delta. Rename case via temporário exclusivo, eliminado
pelo segundo rename. Filesystem PascalCase conferido; configuração Git não alterada.
Seis subclasses mantêm os próprios nomes e herdam a base com o novo nome:
- components/debug_panel/debugpanelui.as
- components/distance_marker/distancemarkerui.as
- components/minimap/minimapenhancementsui.as
- components/overlay/overlayui.as
- components/sixth_sense/sixthsenseui.as
- components/vehicle_health/ammohealthui.as
Em cada uma, somente import/extends. Oitava fonte: factory/componentfactory.as, somente
import e tipo/cast BattleDisplayable; sem alterar factory/create/registo ou arquitetura.

Prova lexical: inversão exclusiva de BattleDisplayable para battledisplayable nos oito
textos devolve exatamente o conteúdo pré-G1b. Packages, métodos, propriedades, visibility,
interfaces, resize/populate/dispose/as_setBattleHudVisible e callbacks preservados.
PanelRow/PanelRenderer/ViewBindings/ratingscreens e artefactos G1a permanecem intactos.
Nenhuma mudança Python de produção, catálogo/gerador, Gameface, config, asset ou SWC.

### Compilação e baseline correta

Uma compilação de battle_flash por compiler.generate existente dentro de IsolatedOutput;
flags/player/SWC/sourcepaths/entrypoint inalterados. Não executado build completo.
Somente driftkingsbattle.swf afetado: panels não inclui a base e markers não depende
destas fontes. Não recompilados panels/markers, nem alterados os seus pipelines.
Área nova exclusiva, sem sobrescrever F4-G1a:
build/experiments/f4-g1b-20261112/
Output: generated/build/flash/driftkingsbattle.swf.
Log: logs/battle_flash.log. Evidências: diagnostics/new-swfdump.xml e binary-contracts.json.
Java TEMP/TMP/user.home confinados ao workspace/temp experimental. Sem output fora da
worktree, sem escrita em build/unified/artefactos anteriores/original/CT.

Baseline de comparação pós-F4-G1a, NÃO apenas beta.9:
build/experiments/f4-g1a-20261112/generated/build/flash/driftkingsbattle.swf
SHA-256 10449ac1f7898a9959f75c33edf79d937cc8370cb9cbf6132361637dff66917c.
Novo SWF SHA-256:
080020557203ff7528bd67ffcfedb896cb5b8d06a30466e2a43ff357199e7d47.

### Inspeção ABC e contratos

swfdump.jar existente do Flex executado sobre novo output; comparado com dump G1a.
Todos os tags não-ABC BYTE A BYTE iguais, incluindo versões/header/document class,
fonts/Embed/SymbolClass/entrypoint. Só DoABC alterado. Comparação canónica normaliza
apenas nome BattleDisplayable, ordinais sintéticos scriptN e line endings; não normaliza
os nomes F4-G1a ou remove instruções. 532 corpos de método equivalentes, 644 assinaturas
e traits/herança/interfaces das 72 classes coerentes. Seis subclasses confirmadas no
ABC com nova base. PanelRow/PanelRenderer/ViewBindings presentes, panelhook inalterado.
Primeira leitura assumiu UTF-8 e falhou num carácter CP1252 do swfdump; repetida sobre
os bytes existentes com CP1252 consistente nos dois dumps. Não houve recompilação nem
normalização de comportamento para contornar a diferença de encoding.
Equivalência local demonstrada com esta ferramenta; não execução de AVM2/cliente CT.

### Testes direcionados e verificações

Único teste escrito: tests/runtime/integration/test_flash_architecture.py, nova regressão
case-sensitive de base/package/construtor, seis subclasses/imports e cast/registo factory.
Preservadas regressões G1a e restantes expectativas da arquitetura.
- Arquitetura Flash + player_panel: 34 PASS Python3 e mesmos 34 PASS Python2.7.
- Validador catálogo existente: flash7/gameface22/injected0/native20, PASS.
- isort --check-only do teste alterado: PASS.
- Comparação lexical oito fontes e comparação ABC/tags: PASS.
- git diff --check bruto reporta espaço final na linha de extends de distancemarkerui;
  conferido no texto pré-G1b: espaço já existente, mantido para limitar delta à nomenclatura.
  Não apresentado como check limpo, não feita limpeza oportunista de whitespace.
Nenhuma regressão completa. Nenhum lock/SWC/flag alterado para fazer os testes passar.

### Preservação, Git e rollback

Hashes pré/pós delimitam oito AS3, teste associado, progresso e outputs da nova experiência.
Gameface/Fase3 G1–G7 e fontes/artefactos F4-G1a conservam hashes. Staging vazio;
core.ignorecase=true mostra rename apenas como modificação. Leitura temporária
case-sensitive prova o par battledisplayable.as removido / BattleDisplayable.as novo;
preparação futura de commit deverá conservar as quatro mudanças de case acumuladas.
Git final normal: 72 caminhos, 48 M / 3 D / 21 untracked. Leitura case-sensitive:
76 caminhos, 44 M / 7 D / 25 untracked. Branch/HEAD intactos.
Beta.9 original novamente conferida:
22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9.

Rollback futuro: inverter somente este identificador nas oito fontes, renomear base
via temporário para battledisplayable.as; preservar todos os deltas G1a. Verificar
igualdade com textos/hashes pré-G1b e voltar ao SWF G1a por hash se necessário num
pacote futuro autorizado. Não usar HEAD/reset/clean nem misturar catálogo/callbacks
antigos. Artefactos G1a e beta.9 não foram substituídos; nenhum rollback executado.
Sem instalações/arranque CT/commits/push/merge/stash/novas branches ou worktrees.

Riscos residuais: runtime CT (seis funcionalidades, visibility, resize, eventos e segunda
batalha) continua pendente; grafia case-sensitive requer cuidado no futuro staging.
Não há mudança comportamental encontrada em fonte/ABC; isso não equivale a CT PASS.
F4-G1b — VALIDATION_PENDING.
F4-G1b — AS3 RENAME PASS.
SWF BINARY CONTRACTS — PASS.
GAMEFACE UNCHANGED — PASS.
ORIGINAL BETA.9 PRESERVED — PASS.
FASE 4 — IN_PROGRESS.

## 24. Fase 4 — F4-G2: plano factory/catálogo AS3

Data: 2026-11-12, Europe/Lisbon.
Autorização: pedido anexado «FASE 4 — F4-G2: Planeamento da Normalização da Factory
e do Catálogo AS3», análise técnica/documentação apenas. F4-G1b aceite localmente:
COMPLETE nesse âmbito, tal como F4-G1a; todos os resultados runtime CT pendentes.
F4-G2 IN_ANALYSIS → AWAITING_APPROVAL; Fase4 permanece IN_PROGRESS, não COMPLETE.
Não autorizada implementação F4-G2, testes, geração, build ou grupos posteriores.

### Baseline e método

Worktree Driftkings_SettingsLab_reorganization; branch reorganization/settingslab,
HEAD bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3; 72 caminhos, 48 M / 3 D / 21 untracked,
staging vazio. Confirmado antes de editar, sem divergência material. Plano/progresso,
auditoria Fase4, G1a/G1b e contratos Fase3 consultados. Hashes da worktree capturados.
Apenas leituras/pesquisas/AST/hash e consulta de dumps binários já existentes; nenhuma
suite, outputs(), regeneração, compilação ou ferramenta de inspeção externa executada.
Única escrita: este progresso; zero fontes/testes/artefactos alterados.

### Inventário e consumidores atuais

flash_source/battle/src/driftkings/battle/factory/componentfactory.as:
package driftkings.battle.factory; public class componentfactory; método static
create(host:Object,aliases:Array,surface:String):void. Sem construtor explícito,
sem extends/implements explícitos; ABC pós-G1b confirma base Object e traits próprios.
Não adicionar construtor explícito ou mudar assinatura durante renomeação.
Imports DisplayObject, BattleDisplayable e BaseBattlePage; usa type:Class, new type(),
cast BattleDisplayable, host.addChild e registerFlashComponentS. A própria factory
não é instanciada nas fontes: chamada estática.

componentcatalog.as no mesmo package é output gerado. Public class componentcatalog,
static classes(surface:String):Object; igualmente sem construtor explícito/interfaces,
extends Object implícito. Sete imports FQN das funcionalidades, map battle com sete
aliases e map ratings com DriftkingsRatingScreens. Surface desconhecida retorna {}.
Consumer direto único: componentfactory.create, via componentcatalog.classes(surface).

Consumer direto da factory: driftkingsbattle.as importa o FQN e chama create em DOIS
callsites, nos closures de BaseBattlePage.prototype.as_DriftkingsCreate e
AbstractView.prototype.as_DriftkingsCreateRatings. Entry class/root driftkingsbattle
permanece. Não foram encontradas instanciações por nome ou strings AS3 dos dois FQN;
pesquisa lexical exclui comentários. SWC catalogs não exportam esses FQN; SymbolClass
pós-G1b também não os publica. Classes constam do ABC; não confundir ausência de export
com prova universal de ausência de consumidores externos desconhecidos.

Percurso indireto:
FLASH_COMPONENTS → generate_ui_catalog/template → componentcatalog.classes →
componentfactory.create → DAAPI component instance/registro; Python BattleViews confere
aliases/FLASH_CLASS/settings section; BattlePackageRegistration carrega biblioteca;
BattleViewHandler chama dinamicamente as_DriftkingsCreate/as_DriftkingsCreateRatings
com aliases de selected_components/surface_aliases, sem referir o FQN da factory.
As referências dinâmicas protegidas são aliases, métodos de protótipo/registo e FQN
das sete funcionalidades, NÃO nomes de factory/catalog. Não alterar esses contratos.

panelhook não depende destas classes; driftkingspanels e helper vehicle markers não
as importam. Só battle_flash é diretamente afetado pela proposta. Catálogo funcional,
metas Python, configs, aliases e classes publicadas sixthsenseui/ammohealthui intactos.

### Origem exata do gerado

build_tools/generate_ui_catalog.py:
- SOURCE aponta interface_catalog.py; FLASH_COMPONENTS fornece as sete specs.
- AS3, linha10: destino flash_source/battle/src/driftkings/battle/factory/componentcatalog.as.
- outputs, linha108: imports vêm de sorted(set(spec['as3'])); sem alterar FQN.
- superfícies ('battle','ratings'); entries de sorted(flash.items()) filtradas por surfaces.
- template, linha125: public class componentcatalog; método classes sem alteração.
- retorno outputs inclui AS3, bootstrap e dois HTML; validate usa esse retorno para
  detectar ficheiros stale; main --write escreve TODOS os outputs.

Alterações futuras estritamente necessárias: AS3 termina ComponentCatalog.as; template
public class ComponentCatalog; factory passa a chamar ComponentCatalog.classes. Manter
imports/maps/ordem/configs/método classes. Nenhuma mudança em interface_catalog.py ou
FLASH_COMPONENTS é necessária: factory/catalog não são componentes funcionais.

### Mapa atómico proposto

| Ficheiro / tipo | Atual | Proposto | Consumidor | Operação necessária | Risco | Teste |
|---|---|---|---|---|---|---|
| flash_source/battle/src/driftkings/battle/factory/componentfactory.as — fonte | componentfactory, create | ComponentFactory, create intacto | driftkingsbattle | Rename físico via temporário; declaração; referência ComponentCatalog | Médio | Filename/class/package, create/casts/registo e fonte inversamente equivalente |
| flash_source/battle/src/driftkingsbattle.as — referência interna/entrypoint protegido | Import + dois componentfactory.create | Import + dois ComponentFactory.create | Protótipos DAAPI battle/ratings | Só import e receiver estático; manter nome/classe/closures/assinaturas | Alto se âmbito alargado | Dois callsites, aliases e callbacks; ABC init/traits/métodos |
| build_tools/generate_ui_catalog.py — gerador | AS3 path minúsculo + template class | AS3 path ComponentCatalog.as + class ComponentCatalog | outputs/validate/geração | Só constante AS3 e declaração no template; não tocar emissão Gameface nem validadores G7 | Médio/alto | Emissão AS3 coerente/determinística; outputs não-AS3 idênticos |
| flash_source/battle/src/driftkings/battle/factory/componentcatalog.as — output | Ficheiro/classe minúsculos | ComponentCatalog.as / ComponentCatalog | Factory, source-path compilador | Emitir exclusivamente pelo gerador; assegurar grafia física por operação controlada | Médio/alto | Package/imports/7+1 maps idênticos; nunca editar conteúdo à mão |
| tests/runtime/integration/test_flash_architecture.py — teste existente | open(...componentfactory.as) no teste BattleDisplayable | open(...ComponentFactory.as) | Suite Python2.7/3 | Atualizar path; ampliar invariantes específicas de factory/entrypoint | Baixo | Preservar todos os testes G1a/G1b e contratos DAAPI |
| tests/build/test_flash_catalog.py — teste novo proposto | Não existe suite focal deste template | Contratos AS3 gerado e outputs partilhados | Gerador Python3 | Criar somente se aprovado; preencher lacuna de emissão/identidade | Baixo | Destino/class alinhados, mapas derivados do catálogo, não-AS3 sem delta |
| build_data/build_config.json / components.json / .as3proj — manifestos/config | source paths por pasta e SWF fixos | KEEP | compiler/build_plan/IDE | Nenhuma alteração necessária; novos nomes continuam nas mesmas pastas | Baixo | Targets/names/generator/entrypoint iguais; integridade de caminhos |
| build/.../experimento-novo/generated/build/flash/driftkingsbattle.swf — compilado | Baseline G1b | Novo SWF no futuro experimento exclusivo | Cliente numa futura validação autorizada | Compilar battle_flash apenas, com pipeline e flags atuais | Alto | ABC e tags comparados ao pós-G1b; preservar snapshots G1a/G1b |
| driftkingspanels.swf / battleVehicleMarkersApp.swf — contratos externos | Filmes/nome/bytes atuais | KEEP | Cliente/linkage/helper | Não recompilar por inferência nem tocar pipeline markers | Alto se alterados | Hash/ABC panelhook e ausência de dependência; ficheiros anteriores intocados |

Não mudar: BATTLE_HUD_HOST/GAMEFACE/interface_catalog.py, nenhum Python de produção,
FLASH_CLASS/aliases/sections, component_list, BattleDisplayable/subclasses e classes G1a,
panelhook/ratingscreens/UI linkage, bibliotecas/fonts/SWC/locks, métodos as_*, assets,
configurações, patches CT, flags/player/source paths e nomes dos SWF.

### Prova futura de Gameface intacto

Antes da implementação, guardar em memória/hash os ficheiros e resultados não-AS3 de
outputs(); depois comparar key sets/conteúdo dos outputs não-AS3 antes/depois, além dos
bytes físicos, sem os escrever. Única mudança de chave permitida: antigo AS3 → novo AS3.
Gerar só outputs()[AS3], não executar main --write global. Assegurar case real do ficheiro
gerado por rename temporário controlado e emissão com nome final, sem edição manual do
conteúdo. Não criar wrapper/loader/segundo gerador para esta operação.

Hashes de referência atuais:
- interface_catalog.py: 623de3bc1bf5b7d322f384785fc48d6c29fd38a310a2305fa095439343ae171c
- shared/bootstrap.js: 2c7491a252e8c026817f201c4d667ffdee20a5f998a1c9b7f6331453c689bf20
- battle_hud/window.html e battle_statistics/model.html:
  60c111911b77ba820235352cb3bcca2cf2fd77b16de1968807d2bb6cd2c91667
Conferir todo o restante Gameface/Wulf/23 R por hashes pré/pós, não só estes exemplos.
Manter 20/0/2, 9 modelos, 15 JS/8 CSS, duas cópias físicas/uma raiz ativa, G1–G3 e G7.

### Sequência exata proposta (futura autorização)

1. Reconfirmar Git/case/staging/hash de fontes, gerado e SWF G1b; inventário final de refs.
2. Capturar hashes/textos pré-G2 e outputs não-AS3 em memória para conferência/rollback.
3. Renomear factory via temporário, classe para ComponentFactory; imports e receivers
   em driftkingsbattle e call ao ComponentCatalog, sem criar construtores novos.
4. Alterar somente AS3 e nome da classe no template do gerador; controlar rename físico
   do output gerado via temporário, emitir conteúdo apenas com o gerador existente.
5. Validar destino/class, 7 aliases battle/1 ratings, FQN/sections/maps/ordem idênticos;
   antigos identificadores ausentes de fontes ativas, salvo testes/documentação histórica.
6. Provar outputs não-AS3 e ficheiros Gameface idênticos antes/depois; validate/checks.
7. Atualizar teste do path factory e teste focal de geração aprovado; nenhum teste funcional
   relaxado. Executar arquitetura/DAAPI em Python2.7/3 e checks build/gerador em Python3.
8. Compilar só battle_flash numa NOVA experiência IsolatedOutput, mesma toolchain/flags;
   preservar G1a/G1b/beta.9, sem .wotmod/instalação/markers.
9. Comparar ABC/traits/signatures/corpos/strings/tags/fontes ao G1b; investigar qualquer
   delta fora dos dois nomes e reordenação sintética. Se inconclusivo, PARTIAL, não PASS.
10. Rever delta/source normalizado/manifesto/case real/staging; atualizar progresso e parar.

### Baseline binária e aceitação

Referência mais recente:
build/experiments/f4-g1b-20261112/generated/build/flash/driftkingsbattle.swf
SHA-256 080020557203ff7528bd67ffcfedb896cb5b8d06a30466e2a43ff357199e7d47.
Hash novamente verificado nesta análise. Dump/diagnóstico G1b existente confirma 72
classes, 644 entradas de método, 532 corpos; não são novos resultados de teste.

Futura comparação deve normalizar SÓ componentfactory→ComponentFactory e
componentcatalog→ComponentCatalog, ordinais sintéticos scriptN e line endings da
ferramenta, sem normalizar G1a/G1b ou remover instruções. Conferir entrypoint/root,
constructors implícitos/herança Object, métodos create/classes e closures dos protótipos,
casts BattleDisplayable, todas as subclasses, panelhook, aliases/strings/fontes e tags
não-ABC. Mudança de pools/ordem de blocos pode ser sintética, mas deve ser explicada;
novas instruções/propriedades/signatures/IDs de alias são divergências funcionais.
Dumps preservam encoding consistente; comparar objetos sem mascarar diferenças de tipo.
Document/SymbolClass não devem passar a publicar factory/catalog. ABC pós-G1b confirma
que ambos já são classes Object, sem interfaces; nenhuma fonte publica novo contrato.

### Testes existentes e lacunas concretas

- test_flash_architecture.py: sete metas/classes/registry/DAAPI, dedup/cache/failure,
  lifecycle, imports, G1a e G1b. Hardcoded path da factory é o único teste encontrado
  que exige atualização de nome físico nesta proposta. Teste agrega nomes de métodos;
  não prova assinatura exata em cada classe, por isso manter inspeção ABC.
- test_own_window_catalog.py: contagens/gerados/ordem/manifesto/raízes; suites native
  clock/crew/carousel/hangar_marks leem outputs bootstrap. Usar verificações direcionadas
  para emissão partilhada sem alterar esses testes apenas pelo rename Flash.
- test_components_manifest.py e font_assets: normalização/packaging/fontes; nenhuma
  alteração esperada dos 334 targets, 23 Layouts ou três targets SWF.
- player_panel/arquitetura Python2.7/3 e inspeção SWF/ABC dos experimentos anteriores
  oferecem referências, não prova de uma compilação futura que ainda não existe.
- Lacunas: teste focal do novo AS3 path/class e source discovery case-sensitive,
  ligação estática dos dois callsites, maps gerados derivados de FLASH_COMPONENTS,
  recusa de output stale/destino antigo e equivalência dos outputs não-AS3. Propor teste
  novo só para estas lacunas, sem listas paralelas de URLs/componentes desnecessárias.
Nenhuma suite direcionada/completa, generator ou build executado nesta análise.

### Riscos, rollback e decisões

Médio: nomenclatura/case Windows e fonte/gerado divergentes; operação via temporário,
verificação filesystem e futura preparação Git mantendo case correto. Alto: alterar
por engano template Gameface, FQN publicado, bytecode funcional ou misturar SWF antigo;
restringir delta e exigir hashes/inspeção por baseline G1b. Colisões de nomes novos
não encontradas na pesquisa atual, revalidar antes de implementar. Consumidores
externos desconhecidos e comportamento real permanecem limitação CT Fase7.

Rollback G2 limitado: ComponentFactory/ComponentCatalog → nomes antigos; restaurar
apenas receivers/imports de driftkingsbattle/factory, constante AS3/template e gerado
emitido coerentemente. Repor path no teste e deltas do teste focal; conservar a base
BattleDisplayable e classes G1a. Voltar ao SWF pós-G1b por hash se um pacote futuro
estiver em validação, nunca ao HEAD ou a SWF beta.9 anterior às renomeações aceites.
Preservar Fase3, configs/assets/locks/artefactos originais. Nenhum rollback executado.

Recomendação: VIÁVEL como grupo pequeno e atómico, sem alteração da arquitetura.
Benefício é consistência editorial; não há ganho funcional/desempenho demonstrado.
Aprovação seguinte deve delimitar os três AS3 envolvidos (incluindo gerado), gerador
apenas emissão AS3, testes indicados e uma compilação experimental de battle_flash
com inspeção contra pós-G1b. Não autoriza renomear sixthsenseui/ammohealthui, F4-G3,
instalar no CT ou criar aliases adicionais. Fase4 não COMPLETE.
Beta.9 SHA-256 confirmado:
22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9.
F4-G2 — AWAITING_APPROVAL.
F4-G2 — FACTORY/CATALOG MIGRATION PLAN: COMPLETE.
PRODUCTION CODE UNCHANGED — PASS.
GAMEFACE UNCHANGED — PASS.
ORIGINAL BETA.9 PRESERVED — PASS.

Git final desta análise: 72 caminhos (48 M / 3 D / 21 untracked), staging vazio;
branch/HEAD intactos. Original mantém 46 caminhos. Comparação de hashes pré/pós:
só este progresso alterado, zero ficheiros criados/removidos nesta execução.

## 25. Fase 4 — F4-G2: implementação Factory / ComponentCatalog

Data: 2026-11-12, Europe/Lisbon.
Autorização expressa: pedido anexado «FASE 4 — F4-G2: Implementação Factory /
ComponentCatalog». Plano da secção24 aprovado; só duas renomeações, referências,
emissão AS3 controlada, testes e compilação isolada de battle_flash.
F4-G2 APPROVED_FOR_IMPLEMENTATION → IN_PROGRESS → VALIDATION_PENDING.
Fase4 IN_PROGRESS, não COMPLETE; F4-G3/posteriores não iniciados nem autorizados.

### Baseline e proteção

Worktree exclusiva Driftkings_SettingsLab_reorganization, branch reorganization/settingslab,
HEAD bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3; inicial 72 caminhos (48 M / 3 D /
21 untracked), staging vazio. Sem divergência material. Plano/progresso/auditoria,
G1a/G1b e planeamento G2 lidos. Hashes worktree e outputs() capturados antes de editar.
SWF baseline pós-G1b conferido:
080020557203ff7528bd67ffcfedb896cb5b8d06a30466e2a43ff357199e7d47.
Experimentos G1a/G1b disponíveis e hashes mantidos, original beta.9 preservado.

### Delta exato de fontes e gerador

- factory/componentfactory.as → ComponentFactory.as; public class ComponentFactory;
  mesmo package, create estático e construtor implícito. Só receiver do catálogo muda
  para ComponentCatalog.classes(surface). Cast BattleDisplayable/registo intactos.
- driftkingsbattle.as: import ComponentFactory e dois callsites battle/ratings;
  class/root, protótipos as_DriftkingsCreate/as_DriftkingsCreateRatings e lógica intactos.
- build_tools/generate_ui_catalog.py: SÓ constante AS3 termina ComponentCatalog.as e
  declaração public class ComponentCatalog no template. Sem alteração de outputs
  Gameface, lógica de ordenação, read_catalog/validate ou contratos G7.
- factory/componentcatalog.as → ComponentCatalog.as: nome físico atualizado via
  temporário exclusivo, conteúdo emitido só por outputs()[AS3] do gerador existente.
  Nunca editado manualmente; não executado --write global. Método classes, sete FQN
  imports, mapas battle/ratings e ordem inalterados.

Dois nomes PascalCase conferidos fisicamente; antigos ausentes na listagem case-sensitive.
Sem temporários remanescentes. Git core.ignorecase não alterado/staging não usado.
Inverter somente identificadores nas fontes factory/entrypoint devolve conteúdo pré-G2
pós-G1b; gerado normalizado só ComponentCatalog devolve exatamente output anterior.
Não adicionados construtores, aliases ou alterações funcionais.

### Testes alterados

- tests/runtime/integration/test_flash_architecture.py: path da factory atualizado,
  regressão nova confirma nome físico/classe/API/construtor implícito e dois callsites;
  preserva G1a/G1b, base/heranças/DAAPI/ownership.
- tests/build/test_flash_catalog.py (novo): suite focal necessária porque não havia
  cobertura direta do destino/classe deste template. Confere case real, API/mapas
  derivados de FLASH_COMPONENTS, imports ordenados, sete specs, ausência da chave de
  output antiga, determinismo e coerência dos outputs não-AS3 com ficheiros existentes.
Não criadas listas paralelas de componentes/URLs; nenhuma expectativa funcional relaxada.

### Gameface e packaging

Comparação pré/pós dos outputs em memória: três outputs não-AS3 idênticos; única troca
de chave é componentcatalog.as → ComponentCatalog.as. Hashes de TODO Gameface/Wulf e
gen_resources iguais antes/depois; nenhum JS/CSS/HTML/R escrito. BATTLE_HUD_HOST,
interface_catalog.py, FLASH_COMPONENTS, modelos/payloads/comandos/lifecycle e patches
CT intactos. 20 nativos / 0 OpenWG / 2 lobby, nove HUD/modelos, 23 Layouts únicos,
334 targets únicos. Testes G7 confirmam dois HTML iguais, 15 JS/8 CSS e ordem histórica.
Manifestos/flags/configs/assets/SWC não alterados, três nomes SWF mantidos.

### Compilação experimental

Uma única compilação de driftkingsbattle.swf via compiler.generate/battle_flash e
IsolatedOutput existentes, com toolchain/flags/player/entrypoint/SWC inalterados.
Área nova: build/experiments/f4-g2-20261112/
Output: generated/build/flash/driftkingsbattle.swf.
Log: logs/battle_flash.log.
Diagnostics: new-swfdump.xml e binary-contracts.json.
Java TEMP/TMP/user.home dentro da área experimental. Nenhum build completo, wotmod,
panels_flash ou vehicle_markers_flash executado. Nada substituído no original/CT,
build/unified ou experiências anteriores.

Novo SHA-256 SWF:
28329a4a9e3b33c4578cbf489eb50df873f8de663021d056d8dd4cfe9dc8b758.
Baseline pós-G1b:
080020557203ff7528bd67ffcfedb896cb5b8d06a30466e2a43ff357199e7d47.

### Comparação ABC

swfdump.jar existente, encoding CP1252 consistente e line endings normalizados para
comparação. Normalizações estritamente limitadas aos nomes ComponentFactory /
ComponentCatalog e ordinais sintéticos scriptN. Nenhum nome G1a/G1b normalizado.
532 corpos de método equivalentes; 644 entradas/assinaturas e traits/herança/interfaces
das 72 classes coerentes. Duas classes novas presentes extends Object; panelhook,
BattleDisplayable/PanelRow/PanelRenderer/ViewBindings mantidos. Todos os tags não-ABC
BYTE A BYTE iguais, incluindo headers/versão/root/entrypoint/fonts/Embed/SymbolClass.
Nada ignorado em instruções/stack/locals/scope para obter equivalência. Reordenação
sintética comparada por blocos; nenhum delta funcional adicional identificado.
Resultado machine-readable em diagnostics/binary-contracts.json. Sem execução AVM2/CT.

### Resultados finais

- Arquitetura Flash + player_panel: 35 PASS Python3 e mesmos 35 PASS Python2.7.
- test_flash_catalog: 2 PASS Python3.
- test_own_window_catalog/G7: 11 PASS Python3, incluindo 334 targets e invariantes host.
- Validador existente: flash7/gameface22/injected0/native20 PASS.
- isort --check-only dos dois testes Python escritos e diff --check delimitado: PASS.
- Nomes físicos, fonte inversamente equivalente, hashes e ABC/tags: PASS.
Nenhuma regressão completa, build de panels/markers, instalação, CT, commit, push,
merge, tag/release, reset/clean/stash ou branches/worktrees.

### Preservação, riscos e rollback

Única documentação escrita: este progresso. Hashes delimitam delta à factory, gerado,
entrypoint, duas substituições no gerador, dois testes e novos artefactos experimentais.
G1a/G1b fontes e outputs fora das referências autorizadas preservados; nenhuma fonte
base/subclasse/ratings renderer mudou. Original beta.9 novamente conferido:
22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9.

Git final normal: 75 caminhos, 50 M / 3 D / 22 untracked; staging vazio. Modo temporário
case-sensitive: 81 caminhos, 44 M / 9 D / 28 untracked, confirmando seis pares case
acumulados. Branch/HEAD intactos. Preparação de commit futura deve registar nomes reais,
sem alterar configuração ou staging nesta execução. Original conserva 46 caminhos.

Rollback limitado G2: nomes antigos da factory/catalog; import/dois receivers no
entrypoint; referência classes no factory; constante AS3/template anteriores e emissão
antiga somente se autorizada; regressões/path de teste correspondentes. Preservar
BattleDisplayable e classes G1a. Artefacto fallback técnico é pós-G1b por SHA, nunca
HEAD ou substituição indiscriminada. Nenhum rollback executado; nada instalado.

Risco residual: runtime CT, load order/coexistência e comportamento real ainda pendentes
Fase7. Comparação de fonte/ABC não substitui AVM2/Scaleform no cliente. F4-G3 não iniciado.
F4-G2 — VALIDATION_PENDING.
F4-G2 — FACTORY/CATALOG RENAME PASS.
SWF BINARY CONTRACTS — PASS.
GAMEFACE OUTPUTS UNCHANGED — PASS.
ORIGINAL BETA.9 PRESERVED — PASS.
FASE 4 — IN_PROGRESS.

## 26. Fase 4 — F4-G3: auditoria Python ↔ AS3

Conclusão: 2026-11-13, Europe/Lisbon; leituras e testes iniciados em 2026-11-12.
Autorização: pedido anexado «FASE 4 — F4-G3: Auditoria de Integração Python ↔
ActionScript 3», auditoria e testes existentes não destrutivos, sem implementação.
«podemos continuar» confirma continuação do mesmo âmbito. Aceitação local F4-G2
registada: COMPLETE nesse âmbito; G1a/G1b e Fase3 também aceites localmente.
F4-G3 IN_ANALYSIS → AWAITING_APPROVAL; Fase4 IN_PROGRESS, não COMPLETE.
Nenhuma correção, teste novo, geração ou compilação autorizada/executada.

### Baseline e evidência

Worktree exclusiva Driftkings_SettingsLab_reorganization; branch reorganization/settingslab,
HEAD bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3. Inicial/final 75 caminhos:
50 M / 3 D / 22 untracked; staging vazio. Sem divergência material. Plano/progresso,
auditoria Fase4, G1a/G1b/G2 e contratos Fase3 consultados. Única escrita persistente:
este progresso. Hashes do inventário capturados; nenhum comando de escrita em fontes,
testes, geradores, binários ou artefactos. Não executado outputs --write nem SWF tool.

### Direção efetiva das chamadas

Definição estática: FLASH_COMPONENTS fornece sete aliases/FQN/meta/config/surface;
gerador emite ComponentCatalog.classes(surface) com sete entradas battle e uma ratings.
Registo Python: BattleViews.register valida FLASH_CLASS e section; start publica
BATTLE_COMPONENTS via BattlePackageRegistration, adiciona pacote/livraria ao cliente.
Carregamento: o cliente carrega driftkingsbattle.swf; static init e construtor instalam
as_DriftkingsCreate/as_DriftkingsCreateRatings nos protótipos nativos. O nome do filme
não é o nome do catálogo/factory. O library driftkingspanels é solicitado separadamente
só no contexto classic/painel habilitado, para linkage/estado panelhook.
Invocação: BattleViewHandler acompanha LOAD_VIEW/aliases reais, agenda descoberta e
chama o método de protótipo disponível via getattr com os aliases ainda não registados.
AS3: ComponentFactory.create consulta ComponentCatalog, ignora desconhecidos/registados,
new type(), associa battlePage para BattleDisplayable, addChild e registerFlashComponentS.
O cliente liga a meta Python/DAAPI e controla populate/dispose/destruição; Python e AS3
não criam janelas ou ownership paralelos. A ordem apresentada no pedido é dependência,
não a ordem de execução acima.
Atualização: componentes/controladores Python produzem valores/payloads; metas verificam
_isDAAPIInited e enviam setters. AS3 chama funções ligadas ao Python por DAAPI para
frames, interação e diagnóstico. Cleanup segue owner do recurso, sem destruir vistas
nativas alheias. Fim/recriação exige coordenação cliente/controladores, não só limpar registry.

### Matriz dos sete contratos

Prefixo FQN AS3 em todas as linhas: driftkings.battle.components.
Prefixo metas Python: driftkings.flash.battle.meta.
Todos usam driftkingsbattle.swf e criação ComponentFactory → new Class → registo DAAPI.
S = VERIFIED_STATIC; T = VERIFIED_TEST; B = BINARY_VERIFIED; R = RUNTIME_PENDING.
T significa apenas cobertura concreta descrita abaixo, não lifecycle completo em AVM2.

| Alias | FQN AS3 (sufixo) | Meta Python | Surface / config | Python→AS3 | AS3→Python | Owner / cleanup | Testes / estado / risco |
|---|---|---|---|---|---|---|---|
| DriftkingsAmmoHealth | vehicle_health.ammohealthui | vehicle_health.AmmoHealthMeta | battle / vehicle_health | as_setHealth(Number,String,uint,int,Boolean) | Nenhum callback próprio | AmmoHealthView weak set/settings; AS3 ConsumablesPanel UPDATE_POSITION/remove; cliente destrói | ammo_health + flash_architecture; S/T/B/R; assinatura coerente, lifecycle em motor pendente |
| DistanceMarkerView | distance_marker.distancemarkerui | distance_marker.DistanceMarkerMeta | battle / target_distance | as_applyConfig(Object), as_isPointInMarker(Number,Number):Boolean | py_requestFrameData():Object | Python _view/controller/keyboard; AS3 ENTER_FRAME e markers; dispose remove eventos/callback/config | battle_small_modules + flash_architecture; S/T/B/R; frame data/drag completo não executado em AVM2 |
| DriftkingsDebugPanel | debug_panel.debugpanelui | debug_panel.DebugPanelMeta | battle / battle_preferences | as_setClock(String,Boolean) | Nenhum callback próprio | DebugPanelView CyclicTimerEvent; stop no dispose; AS3 clock retirado do parent | flash_architecture; S/T/B/R; sem teste focal do relógio real |
| DriftkingsOverlay | overlay.overlayui | overlay.OverlayMeta | battle / section None (OverlayConfig enabled) | as_reset(Array), as_create(String,String,Object), as_update(String,Object,Number=0), as_remove(String) | onElementMoved(String,Number,Number) | OverlayScene mantém snapshot/view atual; AS3 nodes/drag/tweens, dispose/dead | overlay_scene + flash_architecture; S/T/B/R; floating coords e resto dependem de cliente |
| DriftkingsRatingScreens | ratings.ratingscreens | players_panel.PlayersPanelMeta / RosterView interno | battle+ratings / team_panels | as_setRoster(Object) | reportState(state), hoverPanel(bool), reportWidths(left,right), reportScreens(panel,loading,tab), reportPerformance(message) | RatingViews controla roster/subscriptions/callback; AS3 ENTER_FRAME/stage/overrides/cache | player_panel + flash_architecture; S/T/B/R; callback tardio de old view sem guarda Python própria |
| MinimapEnhancementsView | minimap.minimapenhancementsui | minimap.MinimapMeta | battle / minimap_enhancements | as_minimapPresentation(Object), as_minimapVehicle(Object), as_minimapRanges(Object), as_minimapCamera(Boolean) | Nenhum callback próprio de retorno | VIEWS/ctrl/Alt/camera/release callback; AS3 timer/zoom/native overrides restaurados | minimap/minimap_battle/minimap_sector + flash_architecture; S/T/B/R; mudança do handler entre populate/dispose não caracterizada |
| SixthSenseView | sixth_sense.sixthsenseui | sixth_sense.SixthSenseMeta / SixthSense | battle / sixth_sense_alert | as_show(Number), as_hide() | getSettings():Object herdado; getTimerString(timeLeft), playSound(), onIconReady() | g_view/signals/sons; AS3 imageDisposed/loader/timers/tweens e onBeforeDispose | flash_architecture para identidade/meta; S/T/B/R; sem teste focal da integração som/loader em AVM2 |

Bases AS3: exceção explícita: ratingscreens herda diretamente
BattleUIDisplayable; as outras seis herdam BattleDisplayable, que herda BattleUIDisplayable.
BattleDisplayable combina requested/hud/native visibility e gere RESIZE. Ratings usa
ComponentMeta em vez de HudMeta para conservar superfícies nativas distintas.

### Assinaturas, dados e disponibilidade

Quinze setters as_* próprios identificados nas sete fontes; nomes, aridade e tipos de
parâmetros/retorno conferidos contra as funções no dump ABC existente F4-G2, por classe
correta. Isto reforça o teste existente, que agrega nomes em todas as fontes. Aliases/FQN
coincidem com metas e catálogo; assinaturas de create/classes/protótipos preservadas.
HudMeta ainda transmite as_setBattleHudVisible(Boolean); ComponentMeta usa
setCompVisible e guarda _isDAAPIInited. Não são contratos renomeados pela Fase4.

Ammo: fração float protegida para máximo zero, texto HP, int da cor hexadecimal, skin
style-5 e bool; cinco argumentos concordam com AS3. Overlay usa dict/list/copied props
nativos do bridge, não JSON; duration convertido float e default 0 coerente. Distância
retorna dict com screenWidth/screenHeight e observedVehicles list; IDs str, números e
bool; AS3 limpa observedVehicles depois do frame, compatível com pool Python mas requer
bridge real para comprovar identidade/cópia de coleções. Minimap transmite dicts e bool;
ratings envia snapshot/rowUpdates/object, sem confundir com payload JSON Gameface.
Clock converte bytes do strftime para Unicode com encoding local/fallback; getTimerString
usa .format. Nenhuma migração para Python3 assumida; Python2.7 continua runtime alvo.

Os wrappers verificam DAAPI antes de enviar. _sendChanged só deduplica setters escalares,
invalida cache ao ficar indisponível/dispose, usa identidade do flashObject e só guarda
cache após sucesso. Exceção não compromete cache. Dados compostos têm estratégias
próprias; não aplicar cache universal nem alterar serialização nesta auditoria.

### Ownership, destruição e reabertura

- BattleViews.start/stop têm active guard; falha de install tenta uninstall e stop da
  visibilidade. PackageRegistration mantém addedPackages/addedLibrary e não remove
  entradas preexistentes de outros donos. BATTLE_HANDLERS WeakSet é fechado no uninstall.
- Handler.close marca inactive, cancela callback e elimina inscrição; _findPage verifica
  active e limita tentativas a 80. Recriação limpa pendência e volta a resolver página.
- ComponentMeta/HudMeta delegam destruição no cliente; limpar Python registry NÃO
  demonstra destruição AVM2. Fim de batalha/segunda página depende lifecycle nativo.
- Ammo retira settings listener e weak set; Sixth limpa g_view só se próprio, sons e
  signals. AS3 sixth usa imageDisposed/loader guards nos callbacks COMPLETE/error,
  remove listeners, clear timers, unload e dispose tweens. Callback de imagem antigo
  retorna após dispose; garantia de outros percursos sob exceções não provada.
- OverlayScene só aceita moved da view atual, elemento existente/draggable e coordenadas
  finitas. AS3 overlayelement.dead impede report após dispose; finishDrag liberta stage
  listeners; tweens/ENTER_FRAME são retirados. Attach novo recebe snapshot completo.
- Minimap cancela release callback, retira VIEWS/Alt/camera, desativa ctrl no último;
  AS3 stop/remove timer, restore labels/native state/zoom/alpha, artilleryAim dispose.
- Ratings.end cancela BigWorld callback e esvazia view/model/caches; stop retira signals,
  stats listener/eventBus e gameface bridge; AS3 remove frames/stage/mouse e restaura
  panel/row overrides. panelhook state estático é partilhado com panels por desenho.
- Clock usa CallbackService que rejeita tokens cancelados mesmo entregues tardiamente;
  timer.stop cancela inscrição. Proteção não depende só de backend.cancelCallback.

### Riscos fundamentados e lacunas, sem correções

Não encontrada divergência nominal/assinatura nos sete contratos. Nenhuma referência
antiga das seis classes renomeadas permanece em fontes ativas; testes/histórico podem
conter nomes antigos como negativos, não consumers runtime.

UNRESOLVED / risco condicional, não falha observada no CT:
1. ComponentFactory.as:21–23 faz addChild antes de registerFlashComponentS, sem try/
   rollback por alias. Se registo lançar, pode ficar filho não registado e o loop não
   continua; retry pode criar outro. Proposta futura: primeiro teste de falha parcial
   por alias e ownership; só depois decidir cleanup/isolamento. Não causado pelo rename.
2. registry.py:uninstall chama handler.close sequencialmente sem isolamento. Uma exceção
   pode impedir limpeza dos restantes handlers/pacotes/library. Testes atuais cobrem
   ownership normal/failed start, não todos os erros de teardown. Propor fault injection.
3. player_ratings.py:callbacks do RosterView alteram owner sem verificar owner.view is self;
   _dispose só limpa a referência se própria. AS3 remove listeners, mas callback nativo
   já entregue/retido depende do descarte DAAPI. Distância py_requestFrameData também
   resolve controller global sem guarda de identidade da view. Não foi demonstrada
   chamada tardia real; propor teste old-view/replacement antes de qualquer correção.
4. minimap_enhancements.py:42–44 e 67–69 obtém getInputHandler novamente para desligar
   onCameraChanged. Se handler trocar entre populate/dispose, o antigo pode manter
   listener. Cenário não coberto explicitamente; propor teste de substituição do handler.
5. Cleanup de várias views é sequencial sem finally por recurso. Exceção no som/signal/
   restore pode interromper próximos passos; não declarar robustez universal apenas
   porque os métodos onDispose existem. Não confundir cancelamento normal testado com
   prova de libertação real do motor ou ausência de callbacks em qualquer falha.

RUNTIME_PENDING: ordem de bibliotecas, prioridade de linkage/UI de outros mods,
panelhook entre ApplicationDomains, estilos ConsumablesPanel, modos por versão/build,
fonts/Scaleform coercions, input/drag e segunda batalha. Guardas hasCompetingMarkers
reduzem interferência no minimap; não provam coexistência de todos os mods.
Nenhum destes riscos autoriza modificar dependências externas ou corrigir cliente CT.

### Testes existentes executados (sem novos testes)

Conjunto direcionado final: 89 PASS Python3 e os mesmos 89 PASS Python2.7, zero
expectedFailure. Módulos: test_flash_architecture, test_player_panel, test_ammo_health,
test_minimap, test_minimap_battle, test_minimap_sector, test_battle_small_modules,
test_overlay_scene. Sem regressão completa. 2 PASS test_flash_catalog e 6 PASS
test_components_manifest em Python3. Não foram executadas suites sem seleção.
Testes de stores minimap usam tempfile.mkdtemp no diretório temporário do sistema,
fora da worktree, com cleanup; não escrevem produção. Restantes suites selecionadas
usam mocks/in-memory/leitura de fontes. Não criados testes ou ficheiros de baseline.

Cobertura testada: sete metas/registo, factory/catalog/source names, DAAPI scalar cache,
failed setter sem cache, owned package entries, idempotência/failed start, discovery
cancelado, ratings/roster/eventos, HP/persistência de settings listener, minimap estado/
políticas/geometry, overlay deltas e snapshot de recriação. Não cobre som/loader real
SixthSense, requests por frame de DistanceMarker no bridge real ou AVM2 cleanup.
Nenhuma inconsistência estática/binária encontrada; lacunas acima permanecem explícitas.

### Binários e preservação

Apenas lidos dumps/diagnósticos já existentes, sem regenerar/recompilar/reescrever:
G1a SWF 10449ac1f7898a9959f75c33edf79d937cc8370cb9cbf6132361637dff66917c
G1b SWF 080020557203ff7528bd67ffcfedb896cb5b8d06a30466e2a43ff357199e7d47
G2 SWF 28329a4a9e3b33c4578cbf489eb50df873f8de663021d056d8dd4cfe9dc8b758
Hashes conferidos, BINARY_VERIFIED prévio mantido; signatures atuais conferidas no dump.
Gameface/Fase3, host/R/outputs, gerador, AS3/produção Python/testes, SWC/assets/configs e
experiências mantidos. Beta.9 original:
22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9.
Original mantém 46 caminhos, sem staging; branch/HEAD não alterados. Não houve escrita
no original/CT/backups. Não executar rollback: esta auditoria só acrescenta documentação.

### Recomendação e aprovação

Aceitar coerência LOCAL dos sete contratos; manter pendências de runtime e lacunas
específicas de falhas/old-view/handler replacement. Se o responsável quiser corrigir,
autorizar primeiro caracterização direcionada, sem refatorização global ou novos
mecanismos paralelos. Nenhuma alteração funcional necessária identificada por estas
renomeações. Não propor eliminação de adaptadores legados sem prova por modo.
F4-G3 AWAITING_APPROVAL; Fase4 IN_PROGRESS. G4/G5 não iniciados nem autorizados.
F4-G3 — PYTHON/AS3 CONTRACT AUDIT: COMPLETE.
SEVEN FLASH CONTRACTS — PASS (coerência local de identidade/assinatura, não runtime).
PRODUCTION CODE UNCHANGED — PASS.
GAMEFACE UNCHANGED — PASS.
ORIGINAL BETA.9 PRESERVED — PASS.
FASE 4 — IN_PROGRESS.

Conferência final: hashes antes/depois da redação mostram só este progresso alterado;
zero ficheiros adicionados/removidos. Git 75 caminhos, staging vazio; fonte/binários
e Gameface intactos. Não executado diff --check global sobre deltas anteriores.

## 27. F4-G3.1 — Caracterização de falhas e lifecycle Flash/Scaleform

2026-11-13, Europe/Lisbon. Pedido expresso F4-G3.1: aceitação de F4-G3 como
`COMPLETE (LOCAL AUDIT)` e autorização de testes direcionados, sem correções.
F4-G3.1: `IN_PROGRESS` → `VALIDATION_PENDING`. Fase 4 permanece `IN_PROGRESS`.
As referências AWAITING_APPROVAL da secção 26 descrevem o estado histórico anterior.
Pendências AVM2 e CT preservadas; F4-G4/G5 não iniciados.

### Baseline e âmbito efetivo

Worktree reorganization, branch `reorganization/settingslab`, HEAD
`bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3`. Inicial: 75 caminhos
(50 M / 3 D / 22 untracked), staging vazio. Final: 76 caminhos
(50 M / 3 D / 23 untracked), usando --untracked-files=all. O status compacto
agrupa diretórios e não é o contador deste inventário. Apenas acrescentado
`tests/runtime/integration/test_flash_failure_characterization.py` e atualizado
este progresso, já untracked na baseline. Não alterados testes anteriores.

### Evidência e matriz de decisão

Probabilidade no cliente desconhecida em todos os cenários condicionais. Gravidade
abaixo descreve impacto se o gatilho ocorrer, não frequência demonstrada no CT.

| Cenário | Componente | Evidência | Classificação | Gravidade | Impacto | Intervenção proposta | Prioridade | CT necessário |
|---|---|---|---|---|---|---|---|---|
| A | ComponentFactory.as | Guarda estática da sequência catálogo/new/host/addChild/register; sem rollback | STATIC_RISK / UNVERIFIED_AVM2 / CT_PENDING | Alta, condicional | Filho potencialmente não registado se falhar após addChild | Validar em AVM2 antes de decidir rollback | P2, Fase 7 | Sim |
| B | BattleViewHandler / registry / BattleViews | Exceção real em close por cancelCallback controlado interrompe uninstall | REPRODUCED_LOCAL / CT_PENDING | Alta | Handlers e registos pendentes; stop do serviço não repete limpeza | Cleanup e possibilidade de retry delimitados, antes de encerrar Fase 4 | P1 | Sim |
| C1 | RosterView / RatingViews | Callbacks de widths/screens da view antiga alteram owner após substituição/dispose | REPRODUCED_LOCAL / CT_PENDING | Média | Estado partilhado modificado por emissor antigo | Guarda de ownership, antes de encerrar Fase 4 | P1 | Sim |
| C2 | DistanceMarker | Pedido antigo lê payload do controller novo; sem guarda de emissor | REPRODUCED_LOCAL / CT_PENDING | Baixa | Leitura tardia; não demonstrada mutação | Guarda opcional, dependente de aprovação; validar bridge na Fase 7 | P2 | Sim |
| D | Minimap | Regista A, remove em B; listener fica em A nos dois fakes | REPRODUCED_LOCAL / CT_PENDING, fidelidade parcial | Média; alta se remoção lançar | Retenção; exceção pode interromper dispose | Guardar owner original da inscrição, antes de encerrar Fase 4 | P1 | Sim |
| E1 | Minimap | deactivate controlado lança após cancel e remoção de VIEWS | REPRODUCED_LOCAL / CT_PENDING | Alta | Alt/camera e dispose base pendentes | Isolar cleanup destes recursos antes de encerrar Fase 4 | P1 | Sim |
| E2 | SixthSense | sound.stop controlado lança antes de unsubscribe | REPRODUCED_LOCAL / CT_PENDING | Alta | Cache de sons, signals e dispose base pendentes | Cleanup tolerante à falha concreta antes de encerrar Fase 4 | P1 | Sim |

A: falhas antes de addChild não demonstram filho anexado; falhas no registo após
addChild podem deixar criação parcial. Não existe execução AVM2 nem modelo Python
substituto da factory. Guarda estática não prova rollback, estado do motor ou retry.

B: após erro, service.active=False, primeiro handler.active=False e segundo=True;
ambos permanecem no conjunto de owners, com callbacks 11/22 pendentes. Library,
packages e BATTLE_COMPONENTS mantidos; visibility ainda ativa. Segundo service.stop
é inerte por active=False. Com falha desligada, chamada explícita ao uninstall inferior
limpa handlers/registos, mas não pára visibility. Ordem do fake de owners é deliberada,
não pretende reproduzir ordem do WeakSet. Close normal repetido e discovery tardio
após close estão PROTECTED nos casos testados.

C1: dispose antigo preserva referência owner.view atual (PROTECTED), mas callbacks
antigos alteram widths e visibleScreens. Callback de screens ainda altera estado após
owner.end. Refresh foi substituído por observador: demonstra que o destino é o owner
atual, não execução de renderer, transporte nem atualização visual real.
C2: chamada antiga devolve payload do controller atual; sem controller devolve frame
vazio. Apenas leitura/encaminhamento; não confundir com mutação C1. Dispose antigo
não apaga nova referência (PROTECTED). Entrega DAAPI tardia real continua CT_PENDING.

D: fake permissivo deixa listener em A, mas dispose base termina e guarda DAAPI
impede envio posterior a Flash (PROTECTED). Fake estrito lança ao remover de B:
dispose base não ocorre e emissão em A ainda envia. Sem troca de handler, unsubscribe
normal é PROTECTED. Semântica real de remoção e possibilidade/ordem da troca no
motor não demonstradas. onAltKey substituído no teste para isolar ownership da
geometria/configuração; restante populate/dispose/onCameraChanged/meta real.

E1: cancel do callback 99 e remoção de VIEWS concluem antes do erro; controller,
Alt/camera e base permanecem ativos/pendentes. Segunda chamada com falha desligada
conclui, sem repetir cancel. E2: iconReady=False e g_view=None antes da falha;
sons, quatro signals e base pendentes. Segunda chamada conclui stop/cache/unsubscribe/
base. Não extrapolar estes dois pontos Python para outros componentes ou cleanup AS3.

### Testes e limites

Novo ficheiro: 12 testes determinísticos, uma guarda estática AS3 e 11 casos Python
que executam fontes reais contra fronteiras simuladas. Sem rede ou esperas reais.
12 PASS em Python 3 e 12 PASS em Python 2.7. Conjunto direcionado final:
59 PASS Python 3 e os mesmos 59 PASS Python 2.7, zero skips/expectedFailure:
- test_flash_failure_characterization;
- test_flash_architecture;
- test_player_panel;
- test_minimap_battle;
- test_overlay_scene.

Não executada regressão completa. Testes aprovados caracterizam também comportamentos
indesejados atuais; não significam riscos corrigidos. Um primeiro erro no fake Meta
(as_setRosterS ausente) foi corrigido apenas no teste novo. Tentativas de invocação
com discovery/top-level/sys.path incorretos não chegaram a executar os cenários;
com sys.path=tests e discovery por diretório, as suites acima passaram nos dois Python.
Verificação de imports/isort do teste novo aprovada. Nenhum harness AVM2 utilizado.

### Preservação e próximos gates

Comparação SHA-256 integral da worktree antes/depois: apenas este progresso e o teste
novo diferem. Fase 3/Gameface, Python/AS3 de produção, F4-G1a/G1b/G2, geradores,
configurações, assets e SWC intactos. SWF experimentais conservados:
- G1a: 10449ac1f7898a9959f75c33edf79d937cc8370cb9cbf6132361637dff66917c
- G1b: 080020557203ff7528bd67ffcfedb896cb5b8d06a30466e2a43ff357199e7d47
- G2: 28329a4a9e3b33c4578cbf489eb50df873f8de663021d056d8dd4cfe9dc8b758
Beta.9 original: 22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9.
Original sem alterações desta execução; branch/HEAD e staging preservados.
Sem builds, geração, instalações ou operações Git de escrita.

Recomenda-se aprovação separada para correções B/C1/D/E antes de encerrar Fase 4;
C2 opcional; A requer prova AVM2 e validação na Fase 7 antes de escolher correção.
Casos PROTECTED não justificam intervenção. Nenhuma proposta implementada.
Rollback desta tarefa limita-se ao novo teste e às alterações desta secção/cabeçalho,
preservando integralmente o progresso anterior; não executar reset/clean.
Aguardar aceitação da caracterização e autorização específica de qualquer correção.
F4-G3.1 — VALIDATION_PENDING. FASE 4 — IN_PROGRESS. CT RUNTIME PENDING.

## 28. F4-G3.2 — Recuperação do lifecycle Handler / Registry

2026-11-13, Europe/Lisbon. Autorização expressa F4-G3.2: implementação mínima e
exclusiva do cenário B. F4-G3.1 aceite como `COMPLETE (LOCAL CHARACTERIZATION)`;
as referências VALIDATION_PENDING na secção 27 são históricas. Pendências CT e
AVM2 mantidas. F4-G3.2: `IN_PROGRESS` → `VALIDATION_PENDING`.
Fase 4 permanece `IN_PROGRESS`. Não iniciados F4-G3.3 ou F4-G5.

### Baseline e ficheiros

Worktree `Driftkings_SettingsLab_reorganization`; branch `reorganization/settingslab`;
HEAD `bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3`. Inicial 76 caminhos:
50 modificados / 3 removidos / 23 untracked; staging vazio, sem divergências.
Final 77 caminhos: 51 modificados / 3 removidos / 23 untracked; staging vazio.
Contagens com --untracked-files=all, sem alterar core.ignorecase ou staging.

Apenas três ficheiros alterados relativamente ao início desta tarefa:
- `mod/res/scripts/client/driftkings/flash/battle/registry.py`;
- `tests/runtime/integration/test_flash_failure_characterization.py`;
- este registo de progresso.

### Percurso real e causa

Core regista BattleViews como serviço battle_views. start liga visibilidade e instala
BattlePackageRegistration. O registry publica BATTLE_COMPONENTS e acrescenta apenas
library/packages que ainda não existiam, conservando ownership. Handlers registam-se
no WeakSet BATTLE_HANDLERS; close marca active=False, cancela pending, limpa pageAlias
e retira-se do conjunto. Cancelamento que lança conserva token/referência para retry.

Antes: BattleViews.stop marcava inactive antes de uninstall; uninstall interrompia na
primeira exceção de close e não removia restantes owners/packages/library/componentes.
Visibility.stop não era alcançado. Segundo service.stop era no-op. Evidência original
preservada na secção 27 e no comentário do teste B substituído; não reescrever histórico.

### Alteração mínima aplicada

Nenhuma alteração em handler.py: close já preserva pending e inscrição quando cancel
falha e _findPage rejeita discovery se inactive. A correção fica no registry existente.

BattlePackageRegistration.uninstall tenta todos os handlers, conserva referências
fortes dos que falham em pendingHandlers e retira dos conjuntos os que concluem.
Depois remove os packages/library de que é owner e limpa BATTLE_COMPONENTS, mesmo
quando um close falhou. Regista cada falha com logger existente e propaga a primeira
após a limpeza independente. Entradas preexistentes de terceiros permanecem intactas.

BattleViews mantém _pendingStop, lista local dos métodos de cleanup ainda por concluir.
Primeiro stop invalida active e tenta uninstall seguido de visibility.stop na ordem
anterior; sucesso retira a operação, exceção mantém-na e não bloqueia a seguinte.
As falhas são registadas e a primeira é propagada após percorrer ambas as operações.
Novo stop tenta apenas operações pendentes. start rejeita reativação enquanto existir
cleanup pendente. Failed start utiliza o mesmo percurso recuperável; com cleanup normal
continua a propagar a exceção de instalação, com falha de cleanup propaga esta última,
como no percurso anterior, mantendo logs e estado recuperável.
Não foi criada factory, serviço, scheduler, event bus ou estado global adicional.

### Antes/depois e retry

Teste definido ANTES de editar produção: 15 testes, duas falhas e dois erros esperados
na nova semântica B; restantes 11 passaram. Erros referiam atributos de estado ainda
inexistentes. Após correção, acrescentada cobertura de cleanup de failed start.

Falha isolada no token 11: token 22 cancelado, segundo handler fechado, owned entries
removidas e visibility inativa. Primeiro handler inativo conserva token 11; serviço
active=False, mas _pendingStop não vazio e pendingHandlers conserva owner. Nova tentativa
com falha ainda presente propaga novamente e não repete visibility.stop nem close do
segundo handler. Retirada a falha, novo service.stop completa cancel e liberta owner;
stop posterior é inerte. Não se afirma cleanup completo com pendências.

Falha em ambos os handlers: ambos tentados/invalidados e retidos. Discovery tardio do
primeiro não cria componentes e consome o token entregue. Retry fecha ambos mesmo se
um tiver saído do WeakSet. Callback cancelado com sucesso não é cancelado novamente.
Falha de visibility.stop: uninstall concluído não é repetido; retry executa apenas
visibilidade e mantém identidade da exceção propagada. Fecho normal preserva ordem
uninstall → visibility.stop e idempotência. Retry não é agendado automaticamente.

### Testes e contratos

16 testes no ficheiro de caracterização + 15 em test_flash_architecture:
31 PASS Python 3; os mesmos 31 PASS Python 2.7. Zero skips/expectedFailure.
Cobertura: fecho normal/repetido, falha isolada/múltipla, logs/propagação, limpeza
independente, ownership, retry persistente/recuperado, discovery tardio, visibilidade,
failed start e estado recuperável. Suites A/C1/C2/D/E continuam a caracterizar exatamente
as implementações anteriores; nenhuma correção desses cenários foi aplicada.
Checks isort executados individualmente por ficheiro, respeitando configuração local;
execução conjunta encontrou diferenças de contexto de configuração, sem correção global.
Sem regressão completa, build, geração, instalação ou execução CT.

DAAPI, aliases, FQN, catálogo, sete contratos Flash, AS3 e assinaturas intactos;
testes direcionados de contratos aprovados. Janela/modelos Gameface inalterados.

### Limitações e pendências

Mocks não demonstram cancelamento real BigWorld nem destruição de instâncias AVM2.
Exceção persistente mantém referências fortes deliberadamente até retry bem-sucedido.
Só garantida continuação face a exceções de close; falhas arbitrárias na API de listas,
logging ou internals do cliente não recebem uma garantia universal nesta intervenção.
A lista de pendências não desfaz efeitos parciais internos de visibility.stop se este
falhar: repete a operação; semântica real sob falha continua por validar no CT.
Core.stop atualmente marca closed e descarta instances após tentar serviços: não foi
alterado nem agenda retries. Recuperação demonstrada exige conservar a instância de
BattleViews e chamar stop novamente; não equivale a recuperação automática do loader.
Nenhuma alteração ao core ou ao serviço de visibilidade/Gameface autorizada/aplicada.
Validação Fase 7: teardown real, callbacks já enfileirados, subscriptions e segunda
batalha; nenhuma declaração CT RUNTIME PASS.

### Preservação e rollback

SHA-256 antes/depois da árvore confirma só os três ficheiros acima alterados, sem
adições/remoções. Gameface/Wulf, F4-G1a/G1b/G2, AS3, geradores, assets, configurações,
SWC e SWF experimentais mantidos. SWF G1a/G1b/G2 com hashes das secções 26/27 intactos.
Beta.9 original confirmada:
22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9.
Original continua em feature/wot-2.4.2-ct, mesmo HEAD, 46 caminhos (26 M/3 D/17 untracked),
staging vazio. Nenhuma escrita no original, CT ou backups.

Rollback proposto, não executado: reverter somente o diff F4-G3.2 de registry.py
(lista _pendingStop, guarda start, percurso failed-start e isolamento/pendingHandlers);
restaurar exclusivamente o teste B anterior descrito na secção 27, retirando apenas
novos testes/helpers B/setUp desta tarefa; reverter só a secção 28 e o cabeçalho/quadro
alterados nesta tarefa. Preservar todos os restantes deltas, incluindo A/C1/C2/D/E.
Antes de aplicar, comparar conteúdo atual com o final desta execução; não restaurar
ficheiros indiscriminadamente do HEAD, não usar reset/clean e não tocar nos artefactos.

F4-G3.2 — HANDLER/REGISTRY CLEANUP PASS (local, cenário B).
RETRY AFTER FAILURE — PASS (chamada explícita à instância conservada).
NORMAL LIFECYCLE PRESERVED — PASS.
GAMEFACE/SWF UNCHANGED — PASS.
ORIGINAL BETA.9 PRESERVED — PASS.
F4-G3.2 — VALIDATION_PENDING. FASE 4 — IN_PROGRESS.
Aguardar aceitação local; nenhuma intervenção seguinte autorizada por este registo.

## 29. F4-G3.3 — Proteção de callbacks antigos dos Ratings / Roster

2026-11-13, Europe/Lisbon. Pedido expresso F4-G3.3 aceita localmente F4-G3.2:
`COMPLETE (LOCAL VALIDATION)`. Autorização limitada à correção C1, sem alterações
visuais ou de contratos. F4-G3.3 `IN_PROGRESS` → `VALIDATION_PENDING`.
Fase 4 `IN_PROGRESS`; F4-G3.4/F4-G5 não iniciados. Estados anteriores na secção 28
são históricos; todas as limitações dessa execução continuam aplicáveis.
`LOADER RETRY / INSTANCE OWNERSHIP — UNRESOLVED`.

### Baseline e ficheiros alterados

Worktree reorganization; branch `reorganization/settingslab`; HEAD
`bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3`. Inicial e final: 77 caminhos,
51 modificados / 3 removidos / 23 untracked, staging vazio (--untracked-files=all).
Sem divergências inesperadas. Quatro ficheiros, todos já pendentes, alterados:
- `mod/res/scripts/client/driftkings/flash/battle/player_ratings.py`;
- `tests/runtime/integration/test_flash_failure_characterization.py`;
- `tests/runtime/battle/test_team_rosters.py`;
- este progresso.

### Causa e sequência de ownership

PlayersPanelMeta declara os cinco métodos públicos. Cada RatingViews cria uma classe
RosterView interna com closure para o mesmo owner. Os bound methods preservam a
identidade da instância emissora self; não existe generation ID nem parâmetro público
com identidade adicional. _populate executa a base, atribui owner.view=self, invalida
lastPayload e pede refresh. _dispose só retira owner.view se ainda for a mesma view.
end desliga a apresentação, cancela callback, retira view e limpa modelo/caches.

As subscriptions de RatingViews.start ligam eventos ao owner e não a cada RosterView;
stop retira essas subscriptions e chama end. Não foram modificadas. Refresh agenda
um tick apenas quando owner.active e callback ausente. Antes, callbacks antigos
chegavam ao mesmo owner e mutavam widths/visibleScreens, chamavam hover ou refresh
sem verificar a identidade da view. reportState/reportPerformance também aceitavam
mensagens de instâncias antigas. Evidência anterior preservada na secção 27 e nos
comentários dos dois testes C1 substituídos; não reescrito histórico.

### Correção mínima

Apenas cinco linhas de produção: guarda `if owner.view is not self: return` no
início de reportState, hoverPanel, reportWidths, reportScreens e reportPerformance.
Rejeição antes de mutação, refresh, leitura de settings de diagnostics ou logging.
Nenhum parâmetro/método público novo. Não acrescentado owner.active à guarda: uma
view associada mantém os callbacks legítimos mesmo durante transições de atividade.
Uma candidata apenas construída não retira ownership da atual; só _populate o transfere.
Dispose antigo continua a preservar a nova referência. End retira ownership e torna
os callbacks dessas instâncias inertes; nova instância pode associar-se ao mesmo owner.
Não acrescentadas referências fortes, tokens, wrappers ou infraestrutura de callbacks.

### Testes antes/depois

Testes definidos antes de editar produção. Primeira execução teve cinco falhas;
uma asserção de diagnóstico estava inicialmente sem captura INFO. Ajustado apenas o
nível de captura do teste e repetida a execução: cinco falhas reais de comportamento
antigo, zero erros, nos 20 testes então existentes. Callback legítimo de transição
já passava antes da guarda. Depois da correção, casos C1 aprovados.

Suite team_rosters revelou um fixture que construía RosterView sem o associar ao
owner e chamava reportScreens. A guarda corretamente rejeitou esse emissor não atual.
Atualizada exclusivamente a preparação desse caso: liga o emissor ao owner e conserva
os métodos DAAPI do proxy existente. Mantidas todas as asserções de rows/rowOrder/
rowUpdates e transição loading → oculto → painel. Não afrouxada a guarda de produção.

Acrescentado teste com refresh real de RatingViews e backend BigWorld determinístico:
a view antiga não agenda callback; a atual agenda normalmente; end cancela o token
pendente e end repetido não o cancela de novo; callbacks da view encerrada não alteram
widths/screens/hover nem voltam a agendar. Outros testes usam observador de refresh
para distinguir chamada indevida de ausência de renderização real.

Conjunto direcionado final: 64 PASS Python 3 e 64 PASS Python 2.7; zero skips ou
expectedFailure. Módulos: test_flash_failure_characterization (21),
test_flash_architecture (15), test_player_panel (20), test_team_rosters (8).
Testes de A/B/C2/D/E continuam aprovados; implementação F4-G3.2 intacta.
Imports/isort dos dois testes verificados individualmente, whitespace das novas linhas
e comparação delimitada aprovados. Sem regressão completa.

Cobertura C1: widths/screens antigos, substituição, end repetido, dispose atual/antigo,
novo vínculo ao mesmo owner, hover antigo e legítimo, diagnóstico antigo/legítimo,
refresh observado e scheduling real sobre backend fake, e candidata não populada.

### Preservação, limitações e próximos gates

Comparação SHA-256 integral antes/depois limita as alterações aos quatro ficheiros
listados, sem adições/remoções. Produção fora das cinco guardas inalterada.
Fase 3/Gameface/Wulf, F4-G1a/G1b/G2, registry/handler F4-G3.2, AS3, geradores,
catálogo, configurações, assets, SWC e SWF experimentais intactos.
DAAPI/aliases/FQN/as_*/payloads/roster e configurações persistidas preservados.
Beta.9 original com SHA-256 confirmado:
22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9.
Original mantém 46 caminhos (26 M / 3 D / 17 untracked), staging vazio, mesmo HEAD
na branch feature/wot-2.4.2-ct; nenhuma escrita no original, backups ou CT.

Mocks demonstram rejeição por identidade Python, não entrega real DAAPI/AVM2 ou
aspeto visual. Fase 7 deve validar criação, troca de ecrãs/modos e segunda batalha.
Bound method não distingue duas entregas de gerações diferentes se o motor reutilizar
exatamente o mesmo objeto após nova associação: tal reutilização não foi demonstrada,
nem existe identidade de geração no contrato público. Não se inventou uma garantia
de rejeição desse cenário. View antiga distinta é rejeitada, nova instância funciona.
Subscriptions/refresh do owner e outros cenários A/B/C2/D/E não foram refatorizados.
Nenhuma correção do loader, Distance Marker, minimapa ou SixthSense.
Sem build, instalação, compilação SWF, commit ou operação Git de escrita.

### Rollback exclusivo proposto

Não executado. Remover apenas as cinco guardas deste grupo; restaurar exclusivamente
os dois testes C1 anteriores conforme secção 27, retirando os cinco testes C1 novos;
remover a associação explícita acrescentada ao fixture team_rosters; reverter apenas
esta secção e o cabeçalho/quadro desta tarefa. Preservar todos os testes B e alterações
F4-G3.2, restantes caracterizações e deltas anteriores. Conferir diff antes de aplicar;
não restaurar ficheiros do HEAD nem usar reset/clean. Não tocar nos artefactos.

F4-G3.3 — STALE CALLBACK PROTECTION PASS (local, instâncias distintas).
CURRENT VIEW CALLBACKS — PASS.
OLD VIEW ISOLATION — PASS (ownership Python).
PUBLIC DAAPI CONTRACTS UNCHANGED — PASS.
GAMEFACE/SWF UNCHANGED — PASS.
ORIGINAL BETA.9 PRESERVED — PASS.
F4-G3.3 — VALIDATION_PENDING. FASE 4 — IN_PROGRESS.
Aguardar aceitação e nova autorização; não iniciar F4-G3.4.

## 30. F4-G5 — Consolidação e encerramento local Flash/Scaleform

2026-11-13, Europe/Lisbon. Pedido expresso F4-G5 aceita F4-G3.3 localmente:
`COMPLETE (LOCAL VALIDATION)`, autoriza consolidação e permite marcar encerramento
local se satisfeitos os critérios. F4-G5 concluído sem implementação funcional.
`FASE 4 — COMPLETE (LOCAL VALIDATION; CT PENDING)`.
Os estados IN_PROGRESS/VALIDATION_PENDING das secções 21–29 são históricos,
superados apenas quanto à aceitação/encerramento local, nunca quanto às pendências CT.
Fase 5 permanece PENDING; análise/implementação dependem de nova autorização expressa.

### Baseline e operação delimitada

Worktree Driftkings_SettingsLab_reorganization; branch reorganization/settingslab;
HEAD bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3. Inicial/final: 77 caminhos,
51 modificados / 3 removidos / 23 untracked, staging vazio (--untracked-files=all).
Nenhuma divergência material. Única escrita: este progresso. Nenhuma suite reexecutada,
compilação, geração de output, build, instalação, modificação de produção ou operação
Git de escrita. Reutilizados resultados aprovados das secções 19–29.

### Renomeações, geração e contratos

Seis nomes físicos PascalCase presentes e antigos ausentes em listagem case-sensitive:
PanelRow, PanelRenderer, ViewBindings (package driftkings.battle.components.ratings),
BattleDisplayable (driftkings.battle.base), ComponentFactory e ComponentCatalog
(driftkings.battle.factory). Declarações/packages/imports/referências coerentes.
Sem tokens internos antigos em fontes AS3 de battle, Python runtime ou build_tools.
BattleDisplayable mantém seis subclasses; ratingscreens continua na base nativa direta.
Entrypoint driftkingsbattle conserva import da factory e dois callsites battle/ratings.

ComponentCatalog.as permanece gerado: destino e classe do template correspondem;
sete imports e mapas battle/ratings do ficheiro existente conferidos por leitura
estática com FLASH_COMPONENTS. Não chamado outputs(), não regenerado nem escrito AS3.
A origem e equivalência integral do gerado já foram verificadas no F4-G2 (secção25).
As seis mudanças de case exigem preparação correta num eventual futuro commit;
core.ignorecase/staging não alterados nesta consolidação.

Matriz F4-G3 mantida para sete aliases: DriftkingsAmmoHealth, DistanceMarkerView,
DriftkingsDebugPanel, DriftkingsOverlay, DriftkingsRatingScreens,
MinimapEnhancementsView e SixthSenseView. Aliases/FQN/metas/as_*/callbacks/DAAPI/
entrypoints/configurações/SWC permanecem coerentes conforme verificação prévia.
As correções Python posteriores não renomearam contratos nem alteraram payloads.
Não realizada nova auditoria profunda ou execução de testes de contratos.

### Artefactos e evidência binária existente

Todos em build/experiments/<grupo>/generated/build/flash/driftkingsbattle.swf:
- f4-g1a-20261112: 10449ac1f7898a9959f75c33edf79d937cc8370cb9cbf6132361637dff66917c
- f4-g1b-20261112: 080020557203ff7528bd67ffcfedb896cb5b8d06a30466e2a43ff357199e7d47
- f4-g2-20261112: 28329a4a9e3b33c4578cbf489eb50df873f8de663021d056d8dd4cfe9dc8b758

Hashes recalculados iguais aos esperados e aos binary-contracts.json respetivos;
relatórios e new-swfdump.xml presentes e preservados. Cadeia baseline beta.9 → G1a
→ G1b → G2 coerente. Relatórios ABC existentes: PASS nos três, 532 corpos de método,
644 entradas/assinaturas e 72 classes; tags não-ABC idênticos. Normalizações delimitadas
por grupo documentadas, sem nova comparação binária profunda ou ferramenta de dump.
F4-G2 é o ÚLTIMO SWF experimental Flash aprovado da sequência. Nenhum destes SWF foi
instalado nesta fase; não são os binários da beta.9 original. Panels/markers não foram
recompilados por estas renomeações.

### Correções preservadas e aplicabilidade dos testes

G3.2: isolation de close, limpeza independente, pendingHandlers e _pendingStop,
logs/propagação, retry explícito e ordem normal preservados. Registry com mesmo hash
da baseline G3.3; handler intacto. G3.3: cinco guardas owner.view is self mantidas,
sem nova alteração. Testes e fontes relevantes não alterados nesta execução;
resultados finais anteriores aplicáveis, sem repetir suites ou abrir correções.

| Grupo | Objetivo | Alterações | Testes existentes | Resultado | Limitações | Estado |
|---|---|---|---|---|---|---|
| F4-G1a | Nomes ratings | PanelRow/PanelRenderer/ViewBindings | 33 Python3 e 33 Python2.7; fontes/assets; ABC | RENAME/BINARY PASS | AVM2/CT pendentes | COMPLETE LOCAL, implementação e verificação binária |
| F4-G1b | Nome da base | BattleDisplayable e seis subclasses | 34 Python3 e 34 Python2.7; ABC | RENAME/BINARY PASS | Espaço final preexistente preservado; CT pendente | COMPLETE LOCAL, implementação e verificação binária |
| F4-G2 | Factory e catálogo | ComponentFactory/ComponentCatalog, template e referências | 35 Python3 e 35 Python2.7; catálogo 2; G7 11; ABC | RENAME/BINARY PASS | Load order/AVM2 pendentes | COMPLETE LOCAL, implementação e verificação binária |
| F4-G3 | Sete contratos | Auditoria, sem correção | 89 Python3 e 89 Python2.7; catálogo 2/manifesto 6 | CONTRACT AUDIT PASS | Lifecycle real não demonstrado | COMPLETE LOCAL AUDIT |
| F4-G3.1 | Cinco riscos | Caracterização determinística | 59 Python3 e 59 Python2.7 | CHARACTERIZATION PASS | Mocks/AVM2; expectativas B/C1 depois atualizadas | COMPLETE LOCAL CHARACTERIZATION |
| F4-G3.2 | Recuperação B | Registry, pendências e retry explícito | 31 Python3 e 31 Python2.7 | CLEANUP/RETRY PASS | Loader não conserva automaticamente instância | COMPLETE LOCAL VALIDATION |
| F4-G3.3 | Isolamento C1 | Cinco guardas de identidade | 64 Python3 e 64 Python2.7 | CALLBACK PROTECTION PASS | Reutilização da mesma instância não demonstrada | COMPLETE LOCAL VALIDATION |

Contagens históricas não são somadas como testes distintos nem apresentadas como novas
execuções. As 64 verificações finais de G3.3 incluem os contratos de arquitetura Flash,
regressões B e C1 e roster. Alteração intencional de expectativas B/C1 documentada nas
secções 28/29; restantes cenários mantêm caracterização de risco, não correção.

### Gameface/Wulf preservado

Relatórios G6/G7 e G2 mantêm: 20 nativos / 0 consumidores OpenWG / 2 janelas próprias
do lobby; host neutro; nove modelos/cartões; 23 Layouts; 334 targets únicos; dois HTML
idênticos; 15 scripts e oito CSS sem duplicados. Nesta leitura, HTML idênticos e
contagens/URLs únicos reconfirmados. Catálogo tem 20 transportes nativos e as duas
entradas window/owner=None (AccountManager/ModSettings), que não são consumidores
OpenWG; não classificar ausência da chave transport dessas janelas como injeção.

Comparação SHA-256 dos 213 ficheiros Gameface/Wulf/gen_resources contra baselines
G3.1/G3.2/G3.3: nenhuma diferença. A preservação durante G1a/G1b/G2 é sustentada
pelos relatórios de hashes dessas intervenções; deltas existentes face ao HEAD
incluem migração beta.9 e Fase3, não são mudanças novas desta consolidação.
Não reexecutadas as regressões da Fase3 nem expansão do manifesto/geração de layouts.

### Riscos conhecidos transportados para Fase 7

| Tema | Classificação | Pendência preservada |
|---|---|---|
| Factory | KNOWN_RISK / CT_PENDING / DEFERRED_TO_PHASE_7 | addChild anterior ao registo; STATIC_RISK e UNVERIFIED_AVM2; criação parcial real por verificar |
| Handler/registry | LOCAL_TESTED / KNOWN_RISK / CT_PENDING / DEFERRED_TO_PHASE_7 | Retry explícito funciona; LOADER RETRY / INSTANCE OWNERSHIP — UNRESOLVED; Core descarta instâncias, sem retry automático |
| Ratings/roster | LOCAL_TESTED / KNOWN_RISK / CT_PENDING / DEFERRED_TO_PHASE_7 | Isolamento de objetos distintos aprovado; reutilização do mesmo objeto entre gerações não demonstrada |
| Distance Marker | LOCAL_TESTED / KNOWN_RISK / CT_PENDING / DEFERRED_TO_PHASE_7 | Pedido antigo pode ler controller atual; sem mutação demonstrada |
| Minimap | LOCAL_TESTED / KNOWN_RISK / CT_PENDING / DEFERRED_TO_PHASE_7 | Troca A→B pode reter listener; fidelidade parcial dos fakes; cleanup sequencial interrompível |
| SixthSense | LOCAL_TESTED / KNOWN_RISK / CT_PENDING / DEFERRED_TO_PHASE_7 | Falha intermédia em som pode interromper unsubscribe/base; sem garantia universal de cleanup |
| Gameface/Wulf | LOCAL_TESTED / KNOWN_RISK / CT_PENDING / DEFERRED_TO_PHASE_7 | Resolução do host neutro, independência sem OpenWG, input/dragging/lifecycle/segunda batalha; robustez de descarte em marks_panel.js |

LOCAL_TESTED caracteriza o comportamento ou correção delimitada, não elimina KNOWN_RISK.
Nenhum destes pontos reaberto/corrigido aqui ou promovido a CT RUNTIME PASS.

### Preservação, critérios finais e decisões

SHA-256 da beta.9 original recalculado e confirmado:
22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9.
Original mantém feature/wot-2.4.2-ct e mesmo HEAD, 46 caminhos (26 M/3 D/17 untracked),
staging vazio; original/CT/backups não escritos. Experimentos preservados, sem novos
artefactos. Comparação integral antes/depois desta tarefa: apenas este progresso muda,
sem adições/remoções; fontes, testes e restantes documentos intactos.

Todos os critérios locais do pedido F4-G5 satisfeitos. Riscos preexistentes diferidos
não bloqueiam encerramento local por decisão expressa neste pedido. Fase 5 preparada
apenas quanto ao pré-requisito documental; não analisada/implementada nesta execução.
Pendentes: autorização expressa da Fase5, futura validação Fase7 e decisões sobre
riscos conhecidos após evidência runtime. Nenhum commit/publicação autorizado.
Rollback desta redação, se autorizado: inverter somente cabeçalho/quadro e secção30,
conservando todo o histórico e código. Não executar rollback de produção nesta tarefa.

F4-G5 — CONSOLIDATION PASS.
SIX AS3 RENAMES — PASS.
SEVEN FLASH CONTRACTS — PASS (coerência local; evidência anterior preservada).
SWF EXPERIMENTS INTEGRITY — PASS.
GAMEFACE UNCHANGED — PASS.
ORIGINAL BETA.9 PRESERVED — PASS.
FASE 4 — COMPLETE (LOCAL VALIDATION; CT PENDING).
Parar; não iniciar Fase 5 sem nova autorização expressa.

## 31. F5-G1 — Integração e planeamento do botão exclusivo Driftkings

2026-11-13, Europe/Lisbon. Pedido expresso F5-G1 aceita encerramento local da Fase4
(CT PENDING) e autoriza apenas análise técnica/planeamento visual. Fase5 PENDING →
IN_ANALYSIS; F5-G1 IN_ANALYSIS → AWAITING_APPROVAL. F5-G2/G3/G4 e Fase6 não iniciados.
A única escrita é este progresso, sem código, testes, SVG, manifesto ou artefactos.

### Baseline confirmada

Worktree Driftkings_SettingsLab_reorganization, branch reorganization/settingslab,
HEAD bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3. Inicial/final: 77 caminhos,
51 M / 3 D / 23 untracked; staging vazio. Sem divergências materiais.
Reutilizadas conclusões Fases1–4 e fontes diretamente relacionadas com o launcher.
Nenhum teste/regressão executado. Documentação NATIVE_FOOTER_LAUNCHER.md é histórica
(beta.2): comentários sobre OpenWG não descrevem o transporte atual do catálogo.

### Factos — ModsListAPI e acesso existente

Não existe registo ativo addModification/updateModification Driftkings no runtime.
SettingsService inicia o controller e FooterLauncher diretamente. Há um launcher
Driftkings próprio no footer, com PNG small.png, sem SVG metálico e sem lógica de
ocultação por entrada ModsList funcional. Não se está a criar um launcher do zero.

core/mod_compatibility.py observa sys.modules sem importar mods externos. PRESENT
para gui.modsListApi exige g_modsListApi não nulo; não verifica entrada Driftkings,
callable, disponibilidade no lobby ou abertura do painel. ABSENT significa não
observado carregado, não prova ausência em disco. Presença instalada/carregada,
API operacional, entrada registada e capacidade de abrir são estados distintos.

Pacote de referência res/wotmods/me.poliroid.modslistapi_1.8.0.wotmod inspecionado
em leitura: ZIP e code objects Python2.7 com marshal/dis, sem importar/executar o mod,
extrair ficheiros ou instalar ferramentas. Fachada g_modsListApi expõe add/update/
remove/alert/clearAlert; não expõe consulta pública de entradas nem readiness.
addModification pode devolver None tanto em sucesso como em parâmetros inválidos,
pelo que ausência de exceção ou return None não confirma sucesso. Internamente há
g_controller.modifications, items available/dpData e g_eventsManager.onListUpdated;
são detalhes internos da versão, não contrato estável da fachada pública. Callback
é guardado internamente e invocado por evento; introspeção não prova UI renderizada.

Não há hoje callback ModsList ativo Driftkings a seguir. Qualquer ponte futura terá
de usar o controller.open já existente, identidade estável e ownership da sua própria
entrada; não editar/remover entradas de outros mods nem ocultar o botão global.
ModsList é opcional para este acesso. O pacote continua declarado na distribuição;
não remover nem mudar dependências nesta fase. Dependências transitivas da própria
ModsList são independentes da integração nativa Driftkings.

### Factos — abertura, janela e lifecycle

SettingsService.start → controller.start(settings) + SectionPanelBinding →
FooterLauncher(controller,title). LauncherView._getEvents liga onOpen; open verifica
owner.visible e chama owner.controller.open. Payload atual: visible/title; metadata
DriftkingsUI e comando onOpen. Controlador em gameface/lobby/settings_window.py:
canOpen valida espaço/player; open recusa duplicação, popula adapter, cria a única
SettingsWindow, carrega e recupera estado em erro. Window usa WINDOW_MODAL,
WINDOW_FULLSCREEN e TOP_WINDOW; foco efetivo é delegado a Wulf, não provado no CT
atual. Clique repetido não chama explicitamente focus numa janela já aberta.

windowClosed limpa referência e adapter; close destrói janela; onContextLeft retira
space e fecha; stop retira subscriptions/teclado e fecha. SettingsView retira
subscriptions e captura ao finalizar. X/Esc/atalho continuam pelo mecanismo existente,
sem novo caminho. Só launcher é restrito ao lobby; controller também suporta abertura
em battle/replay quando canOpen permite. Não alterar esse contrato por esta fase.

### Factos — integração nativa e recursos

DriftkingsFooterLauncher tem transport=native_document. payload_model seleciona
native_payload_model sem gf_mod_inject. LobbyFooter._initChildren recebe o hook existente,
chama primeiro o original e preserva retorno; getChildView/setChildView por recurso R
impedem filho duplicado. Comp7, Comp7Light, LastStand e BattleRoyale têm variantes
opcionais já enumeradas. Sem nova janela Wulf para o botão: reutilizar LauncherView
filho do footer e a janela de configurações atual.

Patch CT #995 native_document_footerlauncher_0_2.4.2_ct.json injeta uma vez CSS/fonts
+ launcher.js no HTML do footer por replace_exact com hashes. Manifesto atual entrega
essa saída, launcher/** e driftkings.launcher.json. model.html é layout vazio do filho;
o renderer vive no documento nativo. Não usar bootstrap/OpenWG como novo transporte.

JS procura div[data-test-id="menu"] sob Footer_section_* e insere um único botão
antes do menu. Âncora é contrato DOM interno; sem ela o botão não é desenhado fora do
footer. Usa subViews/dataChanged, MutationObserver e render agendado uma vez, sem
polling contínuo. Dispose retira callback de dados, eventos engine/unload, observer,
timeout e botão. WeakSets Python guardam views/parents; stop destrói apenas filhos
que pertencem ao launcher. CSS usa rem, alvo atual 40×32rem e ícone 24×24rem.
Resize/reconstrução acompanham layout/observer; DPI/escala/foco/teclado real requerem CT.
Troca de veículo não tem hook novo próprio; preservar eventos/contextos existentes.

### Proposta — coexistência, sem implementação

Reutilizar FooterLauncher como ponto único de decisão, separado da deteção passiva de
compatibilidade. Não usar is_installed/PRESENT para ocultar. Estados conceptuais:
UNKNOWN (inicialização), NATIVE (sem alternativa confirmada), MODSLIST_CONFIRMED
(entrada nossa identificada, habilitada no lobby e ligada ao mesmo controller),
UNAVAILABLE (API/entrada falhou). Não são estados implementados.

| Condição | Comportamento proposto |
|---|---|
| Acesso Driftkings ModsList confirmado | Ocultar apenas o nosso launcher |
| ModsList presente sem entrada funcional | Mostrar launcher nativo |
| ModsList ausente/indisponível | Mostrar launcher nativo |
| Inicialização desconhecida | Suspender publicação inicial até checkpoint de lobby/footer; reavaliar uma vez e em eventos de lifecycle relevantes |
| Não é possível confirmar após checkpoint | Conservar acesso nativo; não ocultar com base em presença; registar limitação de unicidade |

Não introduzir polling periódico, hooks globais ou execução automática do callback
para testar funcionalidade (abriria janela sem ação do utilizador). Um defer único,
se necessário, deve pertencer ao launcher e ser cancelado no stop. Sem API pública de
mudanças, não inventar evento: onListUpdated só pode ser usado por adaptador específico
da versão, se aprovado, com remoção no descarte. Não depender do evento interno por
defeito nem substituir o manager passivo de compatibilidade.

Recomendação conservadora: manter launcher nativo como acesso principal e não voltar
a registar uma entrada ModsList apenas para ocultar o botão que já funciona. Se for
exigida interoperabilidade com uma entrada existente, aprovar separadamente uma ponte
mínima para versão conhecida que possa confirmar identidade/estado/callback por
readback; fachada atual não permite essa garantia. API futura documentada com consulta
e readiness seria preferível. Se houver registo próprio, não assumir sucesso por None
nem sobrescrever ID existente sem confirmar ownership.

Limitação explícita: com a fachada atual não é possível provar genericamente abertura
funcional nem garantir simultaneamente fallback e zero duplicações perante entradas
externas desconhecidas. NATIVE no estado não verificável privilegia acesso, mas pode
coexistir com entrada externa não comprovada. Esse compromisso exige decisão do
responsável; não apresentar unicidade absoluta como resolvida.
MODSLIST COEXISTENCE STRATEGY — UNRESOLVED quanto à garantia integral; política
conservadora e alternativas acima propostas, não aprovadas nem implementadas.

### Proposta visual inicial, sem SVG/mockup final

Ícone vetorial compacto DK/engrenagem simplificada, silhueta reconhecível sem texto
miúdo; viewBox conceptual 24×24, mantendo inicialmente alvo do botão 40×32rem.
Laranja base #E7771C, sombra #B84C0A, highlight #FFC06A e grafite #272B30.
Gradiente linear simples com poucos stops, sem filtros complexos/data URI; ficheiro
SVG externo e transparência. Aparência metálica subtil, sem caixa permanente.
Normal: contorno/silhueta legíveis; hover: highlight e fundo discreto; pressed:
escurecimento/relevo reduzido; disabled, se contexto não permitir ação: menos brilho,
sem clique. Preservar focus visível e testar teclado/tooltip Gameface.
Tooltip/aria-label localizado sugerido: Driftkings Settings. Sem animação pesada.
Não alterada geometria do footer nem produzido qualquer desenho/asset nesta execução.

### Ficheiros potencialmente envolvidos na implementação futura

Necessários: gameface/lobby/launcher.py, launcher/launcher.js, launcher/launcher.css,
um novo asset SVG aprovado (destino proposto junto do launcher), testes runtime e
frontend diretamente afetados. Sem novo controller/modelo/janela; manter onOpen.
SettingsService só se for necessária ligação explícita da disponibilidade ModsList;
preferir mantê-la no owner atual. Adapter isolado adicional só se a decisão de
coexistência demonstrar necessidade; não criar um framework de integrações.

Catálogo/manifesto/patch somente se mudar lista de assets ou contrato do documento.
launcher/** já cobre asset local; não alterar manifesto por hábito. Novo SVG em raiz
comum gui/icons/driftkings exigiria entrada explícita se não coberta; essa movimentação
não está aprovada. R/model.html e gameface/core.py não precisam de alteração prevista.
Geradores não precisam de nova arquitetura. Nenhum ficheiro acima foi alterado.

### Riscos, testes futuros e compatibilidade

Factos CT: patch atual limitado a versão/build/hash; variantes opcionais e âncora DOM
não provam suporte EU/NA/ASIA/CN. Planeamento regional é requisito, comparação profunda
reservada à Fase6. Manter perfis/patches explícitos, sem copiar hashes CT para regiões.
Outros riscos: ausência de ack ModsList, corrida de inicialização, entrada externa,
SVG/carregamento e contraste a pequena escala, foco/tooltip, reconstruction e mods
que partilham o footer. Não modificar outros mods ou o cliente para contornar riscos.

Testes mínimos futuros: API ausente; apenas presente; registo inválido/None; entrada
habilitada/desabilitada; callback correto/errado; estado inicial desconhecido e tardio;
visibilidade exclusiva se confirmável; fallback sem perda de acesso; controller.open
único; logout/reentrada/stop/recriação; observer/listeners/callbacks cancelados; render
único/âncora ausente/substituída; variantes; SVG e rem; nenhum delta noutros plugins.
Testes existentes consultados: test_launcher.py e test_launcher.js; não executados nem
modificados. Uma implementação futura terá de ajustar o teste que proíbe qualquer uso
ModsList somente se a ponte for expressamente aprovada. CT manual continua na Fase7.

### Sequência proposta e decisões pendentes

F5-G1: análise e contrato de coexistência/especificação visual → AWAITING_APPROVAL.
F5-G2: proposta SVG/mockup, sem aplicar antes de aprovação expressa.
F5-G3: delta mínimo sobre launcher existente, onOpen/controller atuais e coexistência
aprovada; testes direcionados. Sem nova arquitetura de configurações.
F5-G4: consolidação proporcional/documentação; preparar Fase6 sem iniciá-la.

Decisões: aceitar plano/limitação ModsList; escolher acesso nativo principal ou ponte
versionada com dependência interna; aceitar direção visual preliminar antes de G2.
Não exigir aprovação de um asset inexistente: desenho final só será produzido em G2
quando autorizado. Sem autorização implícita de implementação, build ou instalação.
Rollback desta análise limita-se ao cabeçalho/quadro e secção31, sem tocar código.

### Preservação e veredictos

Hashes antes/depois: só este progresso alterado; sem adições/remoções, código/testes/
assets/geradores e experiências intactos. Beta.9 original verificada:
22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9.
Nenhuma escrita no original/CT/backups; nenhuma regressão, build, commit ou execução
runtime de módulos de produção/terceiros. Leitura marshal/dis não executou bytecode.

F5-G1 — GARAGE LAUNCHER PLAN: COMPLETE (análise entregue, decisões pendentes).
MODSLIST COEXISTENCE STRATEGY — UNRESOLVED.
SETTINGS OPEN PATH — VERIFIED (fonte, não nova validação runtime).
PRODUCTION CODE UNCHANGED — PASS.
ORIGINAL BETA.9 PRESERVED — PASS.
F5-G1 — AWAITING_APPROVAL. FASE 5 — IN_ANALYSIS.
Parar; não iniciar F5-G2/G3/G4 ou Fase6 sem nova autorização.

## 32. F5-G3 — Implementação visual do launcher Driftkings

2026-11-13, Europe/Lisbon. Pedido expresso F5-G3: aceita auditoria F5-G1, confirma
conceito F5-G2 aprovado (imagem de referência com quatro estados) e autoriza SVG
vetorial original e atualização mínima do launcher nativo existente. Não foi executado
um grupo F5-G2 autónomo nesta worktree: aprovação visual consta deste pedido.
Decisão expressa: NATIVE PRIMARY; sem nova entrada ModsList, hooks privados ou polling.
F5-G3 IN_PROGRESS → VALIDATION_PENDING; Fase5 IN_PROGRESS, não COMPLETE.
F5-G4 e Fase6 não iniciados. Estados/decisões pendentes da secção31 são históricos;
a limitação de prova de acesso externo ModsList permanece, com política agora decidida.

### Baseline e ficheiros

Worktree reorganization, branch reorganization/settingslab, HEAD
bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3. Inicial 77 caminhos (51 M/3 D/23 untracked),
staging vazio. Final 81 caminhos (54 M/3 D/24 untracked), staging vazio.
Sem divergências inesperadas antes de editar. Ficheiros alterados exclusivamente:
- mod/res/gui/gameface/mods/driftkings/launcher/launcher.js;
- mod/res/gui/gameface/mods/driftkings/launcher/launcher.css;
- novo mod/res/gui/gameface/mods/driftkings/launcher/launcher_dk.svg;
- tests/frontend/lobby/test_launcher.js;
- este progresso.
Nenhum Python, AS3, manifesto, catálogo ou patch modificado.

### SVG e estados visuais

SVG original desenhado em geometria vetorial, baseado na referência aprovada:
viewBox 0 0 64 64, oito dentes, anel metálico laranja, centro grafite e letras DK em
path com recorte do D, sem fontes externas. Usa paths/circle/use e três gradientes
lineares simples: metal, graphite e letters. Cores #FFC06A/#E7771C/#B84C0A/#272B30.
Fundo transparente. Referências href/xlink locais e fills url(#id); nenhum raster
embutido, script, animação, filtro SVG, recurso externo ou foreignObject/text.
Contornos/reflexos simplificados para conservar legibilidade a pequena escala.

Um único SVG para quatro estados CSS: normal brightness(1); hover brightness(1.22)
e fundo/borda laranja discretos; pressed brightness(.78); disabled grayscale(1),
brightness(.75), opacity .65, sem cursor de ação nem fundo/borda. Transições de 100ms
em cores/filter, sem deslocamento ou mudança de tamanho. Focus continua visível.
Dimensões anteriores mantidas: botão 40×32rem, margem 0 6rem, padding 4rem e ícone
24×24rem. Sem caixa permanente. Estado disabled estilizado e bloqueio de clique
quando button.disabled; não acrescentada regra Python para desativar contextos.
No fluxo normal de lobby o botão permanece habilitado como antes.

### Integração e packaging

JS troca apenas URL PNG para coui://gui/gameface/mods/driftkings/launcher/launcher_dk.svg
e acrescenta a guarda button.disabled ao clique. Continua a chamar model.onOpen.
Mantidos owner único __dkFooterLauncher, âncora, posição antes do menu, título/aria-label,
listeners existentes, um MutationObserver, subscriptions e descarte/reconstrução.
Sem segundo launcher, hook, controlador, janela, API ou dependência OpenWG adicional.
SettingsController/SettingsWindow e LauncherView Python byte a byte intactos.

Manifesto existente inclui mod/res/gui/gameface/mods/driftkings/launcher/**; novo SVG
coberto sem novo target/generator. URL do renderer resolve para esse asset, sem path
de desenvolvimento. Patch nativo/footer e resource R mantidos; catálogo/20 componentes
nativos/host de batalha preservados. Esta é verificação de inclusão pelo manifesto,
não auditoria de pacote compilado; nenhum build foi executado nem artefacto instalado.

### Verificações direcionadas e pré-visualização

- Parse XML SVG aprovado; viewBox, elementos vetoriais e referências exclusivamente
  internas conferidos. Nenhum recurso/script/raster/fonte externo.
- Glob existente e URL no renderer conferidos; sem alterações de packaging/manifestos.
- Teste frontend test_launcher.js PASS: mantém clique, unicidade, troca de âncora,
  modelos, recriação e cleanup; acrescenta URL SVG, clique disabled e invariantes CSS.
- tests/runtime/lobby/test_launcher.py: 5 PASS Python3 e os mesmos 5 PASS Python2.7;
  callback/controller/janela única/contexto/variantes/limpeza preservados.
- ESLint focal launcher.js PASS, usando instalação já existente no original como
  ferramenta em leitura, sem instalar dependências nem escrever no original. Primeira
  tentativa procurou node_modules inexistente na worktree; não foi falha de lint.
- Diff --check delimitado PASS, apenas avisos CRLF/LF, sem reformatação global.
- Nenhuma regressão de Fases3/4 ou suite completa executada.

Pré-visualização estática criada em área temporária isolada, sem artefactos no repo:
C:/Users/<utilizador>/AppData/Local/Temp/driftkings-launcher-preview-3c8f7436/preview.html
C:/Users/<utilizador>/AppData/Local/Temp/driftkings-launcher-preview-3c8f7436/preview.png
Render Edge/Chromium headless local, inspecionado visualmente a 20/24/32px nos quatro
estados. Os efeitos de estado são simulados com os mesmos valores CSS na grelha;
a prova de pseudo-estados interativos em Gameface continua pendente. Não iniciado CT.
Ficheiros temporários de preview/perfil Chromium não fazem parte do mod ou packaging.

### Compatibilidade, riscos e preservação

SVG básico e CSS visual aprovados em Chromium local; isso NÃO prova carregamento
coui, suporte de filtros CSS brightness/grayscale ou apresentação no Gameface do CT.
SVG COMPATIBILITY — PARTIAL enquanto falta essa validação do renderer real.
Se o cliente não suportar adequadamente SVG/efeitos, usar futura alternativa derivada
do vetor só após evidência e autorização, preservando esta fonte SVG. Não foi criado
fallback PNG especulativo nem adicionado listener de erro/loading nesta intervenção.

Validar no CT em Fase7: leitura DK/contraste real a pequena escala, hover/pressed/
disabled, filtros, tooltip, foco/input, alinhamento/resize/DPI, menus/regresso ao hangar
e ausência de duplicação. Nenhuma declaração CT RUNTIME PASS.
ModsList não foi modificada/registada/ocultada. Launcher nativo é acesso principal;
acesso externo duplicado não identificável continua limitação da API pública.
Riscos conhecidos Gameface/Flash das Fases3/4 continuam diferidos, sem correções.

Comparação SHA-256 integral pré/pós: só os quatro ficheiros existentes acima e o SVG
novo diferem. Restantes Gameface, host/modelos de batalha, Python/AS3, SWF experimentais,
SWC, configurações, assets alheios, bibliotecas externas, catálogo e geradores intactos.
Beta.9 original recalculada e preservada:
22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9.
Sem build, instalação, execução CT, commit ou escrita no original/backups.

### Recuperação documental nesta execução

Uma substituição demasiado ampla no cabeçalho removeu temporariamente as secções
1–8. Detetado na conferência final, recuperado o bloco a partir da leitura integral
registada na sessão e das substituições documentais posteriores (apenas dados, sem
reexecutar comandos antigos). Repostos contexto, quadro de fases, decisões, ficha,
histórico e inventário; secção8 conserva o checkpoint histórico F4-G3. Cabeçalho e
quadro atuais indicam F5-G3 VALIDATION_PENDING. Secções9–31 preservadas.
Esta reparação afetou só o progresso; fontes e artefactos não foram alterados.

### Rollback exclusivo

Não executado. Repor somente a referência small.png e guarda de clique anterior no
launcher.js; inverter apenas os estados CSS desta tarefa para o visual anterior;
retirar só as quatro asserções novas no teste frontend (URL, disabled, CSS e dimensões);
remover somente launcher_dk.svg e reverter cabeçalho/quadro/secção32 deste progresso.
Preservar todo o restante trabalho, sem reset/clean ou restauração global do HEAD.
Manifestos, Python e artefactos não precisam de rollback porque não foram alterados.

F5-G3 — LAUNCHER VISUAL IMPLEMENTATION PASS (local).
SVG COMPATIBILITY — PARTIAL (Chromium local PASS; Gameface/CT pendente).
SETTINGS OPEN PATH PRESERVED — PASS.
MODSLIST COEXISTENCE — NATIVE PRIMARY.
GAMEFACE/BATTLE UNCHANGED — PASS (fora do launcher visual autorizado).
ORIGINAL BETA.9 PRESERVED — PASS.
F5-G3 — VALIDATION_PENDING. FASE 5 — IN_PROGRESS.
Parar; não iniciar F5-G4 ou Fase6 sem nova autorização expressa.

## 33. F5-G4 — Consolidação e encerramento local do launcher

2026-11-13, Europe/Lisbon. Pedido expresso F5-G4 aceita localmente F5-G3 e autoriza
apenas consolidação documental/verificações estáticas mínimas, com encerramento local
se cumpridos os critérios. F5-G3 COMPLETE (LOCAL VALIDATION); F5-G4 CONSOLIDATION PASS.
FASE 5 — COMPLETE (LOCAL VALIDATION; CT PENDING).
Os estados AWAITING_APPROVAL/IN_PROGRESS/VALIDATION_PENDING nas secções31/32 são
históricos, superados quanto à aprovação local; limitações runtime permanecem.
Fase6 não iniciada; fontes regionais locais não foram inventariadas/comparadas aqui.

### Estado Git e âmbito

Worktree Driftkings_SettingsLab_reorganization, branch reorganization/settingslab,
HEAD bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3. Inicial e final: 81 caminhos,
54 modificados / 3 removidos / 24 untracked; staging vazio (--untracked-files=all).
Nenhuma divergência inesperada. Única escrita: este progresso. Plano diretor intacto.
Sem testes novos, repetição de suites, alteração de produção, SVG, manifesto ou asset.

### Consolidação estática do SVG e integração

Presente mod/res/gui/gameface/mods/driftkings/launcher/launcher_dk.svg; parse XML aprovado,
viewBox 0 0 64 64, paths para DK e engrenagem de oito dentes, centro grafite e laranja
metalizado. Gradientes lineares simples e fundo transparente. Sem texto/fonte externa,
raster embutido, script, animação, foreignObject ou filtro SVG; href/xlink internos.
Não redesenhado, substituído ou gerada variante nesta consolidação.

Renderer usa coui://gui/gameface/mods/driftkings/launcher/launcher_dk.svg. CSS conserva
normal, hover, pressed e disabled, com foco visível e transição curta. Dimensões,
margens, posição antes do menu e alinhamento existentes mantidos. Tooltip/title e
aria-label preservados. Clique verifica visible/model/disabled e mantém model.onOpen.

Caminho confirmado nas fontes: LauncherView._getEvents onOpen → LauncherView.open →
FooterLauncher.controller.open → SettingsController.open → SettingsWindow. Continua
uma janela, controller e launcher existentes, com hook de footer, observer e listeners
anteriores. Não foram acrescentados hooks, recursos R ou dependências nesta execução.
Comentário antigo de launcher.js menciona OpenWG/bootstrap: é histórico, não altera
o transporte atual native_document confirmado no F5-G1; não foi corrigido por escopo.

### Coexistência e packaging

Decisão aprovada: NATIVE PRIMARY. Não ocultar launcher por mera presença ModsListAPI,
não criar addModification adicional, não alterar botão global e não consultar hooks
privados. A API pública 1.8.0 não confirma uma entrada Driftkings funcional; ausência
absoluta de duplicação com entrada externa não identificável não é garantida.
Nenhum mecanismo adicional de coexistência foi implementado nesta consolidação.

Glob mod/res/gui/gameface/mods/driftkings/launcher/** cobre o SVG. URL do renderer
corresponde ao ficheiro distribuído; sem URLs de desenvolvimento. Reutilizados Layout
R e patch native_document/footer existentes, catálogo intacto. PACKAGING PASS significa
cobertura estática pelo manifesto, não auditoria de um pacote compilado nesta etapa.
Nenhuma alteração/regeneração de manifesto, patch ou catálogo; nenhum build executado.

### Evidências reutilizadas e preservação

F5-G1: auditoria técnica e caminho de abertura verificados em fonte; limitação ModsList
explicitada. F5-G2: aprovação visual confirmada expressamente no pedido F5-G3, sem
execução autónoma desse grupo na worktree. F5-G3: SVG/renderer/CSS/teste focal entregues.
Resultados reutilizados da secção32: teste frontend launcher PASS, cinco testes Python3
e os mesmos cinco Python2.7 PASS, ESLint focal e diff check PASS; preview Chromium
20/24/32px inspecionado. Nenhuma suite reexecutada porque fontes relevantes não mudaram.

Comparação delimitada de hashes nesta tarefa conserva SVG, JS/CSS, teste frontend,
Python do launcher/controlador, catálogo, manifesto/build_config, plano diretor e os
três SWF experimentais F4. Hashes dos SWF confirmam as referências aprovadas:
G1a 10449ac1f7898a9959f75c33edf79d937cc8370cb9cbf6132361637dff66917c;
G1b 080020557203ff7528bd67ffcfedb896cb5b8d06a30466e2a43ff357199e7d47;
G2 28329a4a9e3b33c4578cbf489eb50df873f8de663021d056d8dd4cfe9dc8b758.
Preservação do restante Gameface/Wulf, host neutro, componentes nativos, contratos
Python/AS3, SWC, configurações e assets alheios sustentada pelas comparações já aprovadas
nas secções30/32; nenhuma intervenção nesses ficheiros nesta tarefa.

Beta.9 original novamente conferida:
22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9.
Original/backups/cliente CT não escritos. Não executados instalação, jogo, compilação,
commit ou operação Git de escrita. Secções1–32 preservadas, exceto atualização pontual
do cabeçalho e linha da Fase5 no quadro. Conferida sequência única de secções1–33;
inversão em memória desses dois deltas e retirada da secção33 recupera bytes anteriores.

### Pendências explícitas para Fase7

CT_PENDING / DEFERRED_TO_PHASE_7: carregamento SVG por coui; suporte Gameface a
brightness/grayscale; aparência real a 20/24/32px; hover/pressed/disabled/foco;
posicionamento, resize/escala/DPI; reconstrução do footer; abertura e fecho das
configurações; contexto/regresso ao hangar; ModsList presente/ausente. Preview Chromium
não valida WoT; SVG COMPATIBILITY continua PARTIAL quanto ao renderer real.
Riscos conhecidos das Fases3/4 mantidos, sem reabrir correções ou exigir resolução
para este encerramento local. Nenhum CT RUNTIME PASS declarado.

### Preparação documental da Fase6 e decisões

Fase seguinte: compatibilidade EU / NA / ASIA / CN / CT. Áreas a comparar quando
expressamente autorizadas: resources R; documentos Gameface; patches HTML e hashes;
APIs Wulf; Flash/Scaleform/linkage/SWC; hooks Python; versões/builds do cliente;
manifestos e packaging regional. Fontes locais disponíveis segundo o responsável;
não se iniciou leitura/comparação regional. CT partilhado não demonstra equivalência
entre versões de produção. Exigir perfis/evidência por cliente, sem extrapolar hashes.

Critérios locais F5-G4 satisfeitos: SVG presente, launcher existente integrado, estados
definidos, abertura preservada, política ModsList documentada, cobertura de packaging,
resultados anteriores aplicáveis e fases anteriores/beta.9 preservadas. Fase5 encerrada
localmente por autorização condicional expressa deste pedido; runtime continua pendente.
Próxima decisão: autorização específica da Fase6; não a iniciar por inferência.
Rollback documental, se necessário e autorizado: inverter somente os dois deltas de
cabeçalho/quadro e retirar a secção33. Não reverter código/artefactos nesta consolidação.

F5-G4 — CONSOLIDATION PASS.
SVG AND LAUNCHER INTEGRATION — PASS (local).
SETTINGS OPEN PATH — PRESERVED.
PACKAGING — PASS (manifesto estático).
GAMEFACE/BATTLE UNCHANGED — PASS.
ORIGINAL BETA.9 PRESERVED — PASS.
FASE 5 — COMPLETE (LOCAL VALIDATION; CT PENDING).
Parar; não iniciar a Fase6 sem autorização expressa.

## 34. F6-G1.1 — Compatibilidade estática com Common Test #996

2026-11-13, Europe/Lisbon. Pedido expresso autoriza leitura das fontes já extraídas
CT #996, código/contratos efetivamente usados e atualização só deste progresso.
Fase6 IN_ANALYSIS; F6-G1.1 AWAITING_APPROVAL, revisão PARTIAL. Sem correções, testes,
builds, extrações/decompilações, regeneração ou execução do cliente. Outras regiões
não analisadas. Finalidade: preparar primeira build experimental da reorganização.

### Git, fontes e limites de proveniência

Worktree reorganization; branch reorganization/settingslab; HEAD
bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3. Inicial/final 81 caminhos:
54 M / 3 D / 24 untracked; staging vazio. Nenhuma divergência Git inesperada.
Única escrita este progresso; master plan e código preservados.

Raiz obrigatória utilizada:
E:/Wot_Mods_/Drift_Kings_ModPack/Driftkings_WoT_Sources/wot_src_CT.
.version_name: 2.4.2.0 Common Test #996. manifest.json: CT, versão 2.4.2.0,
build 996, client_revision 2660091, extraction_date 2026-11-12T17:11:00+00:00,
consistent=true, 19963 entradas selecionadas/processadas/sucesso, zero falhas nessa
contagem de extração. Não extrapolar isso para perfeição da descompilação.

Divergência comunicada antes das conclusões: README.md e report.json ainda identificam
#995 (revision 2655094); verify_report.json é de 2026-11-09. update/decompile/Gameface/
ActionScript reports são de 2026-11-12. Não foi corrigido metadata nem reextraído nada.
CT #996 SOURCES — PARTIAL globalmente por metadados históricos misturados; identificação
#996 do manifesto/version_name conferida. Usadas entradas individuais do manifesto:
SHA-256 dos oito Python críticos descompilados conferido contra decompiled.sha256,
com input_sha256 ligado ao bytecode identificado. Não usar relatório antigo como prova
runtime ou chamar a referência inteira INVALID só pelo README desatualizado.

Organização confirmada: sources/res/scripts/{client,common} e árvores de extensões
como sources/res/comp7_core/scripts/client; sources_as/{scripts,swf,assets,asasm,catalog};
sources_gameface/{js,css,html,assets,manifests,VIEWS.md}; __stubs .pyi e sources_xml.
sources_gameface/html está vazio neste snapshot; HTML bruto existe em sources/res/gui/
gameface e consta no manifesto. JS formatado não serve de input bruto de hash/replace.

### Inventário efetivo e ativação

component_list.py contém 35 entrypoints, coerentes com build_data/components.json.
load.json seleciona default. A ativação aqui é a configuração-fonte da worktree,
não o estado runtime de uma sessão nem perfis pessoais do CT (não inferidos).
AimingCountdown e ShellFlightTime têm enabled=false; os módulos continuam incluídos/
carregáveis. Restantes entradas têm flags de topo true, salvo SoundBankLoader (sem
flag geral, serviço de configuração) e VehicleMarkers (markers.enabled=true aninhado).
Flags internas/subopções não equivalem a habilitar todas as funcionalidades de cada mod.

Infraestrutura adicional, não mods duplicados: ui/common/stats/settings_panel nos
manifestos, Core/contextos/hooks/keyboard/battleEvents, SettingsService/SettingsWindow,
FooterLauncher e host HUD neutro. Não contar todos os ficheiros Python como mods.
Catálogo: 20 nativos/0 consumidores OpenWG/2 janelas lobby; nove HUD/modelos, seis
native_document, quatro native_user_missions e um native_battle_results. AccountManager
+ModSettings são janelas lobby independentes. Flash: sete aliases e pipeline markers.
Experimentos F4 em build/experiments são artefactos de desenvolvimento, não módulos
runtime adicionais. Halloween TAB removido não é consumidor ativo. Não instalar ou
retirar dependências para produzir esta classificação.

### Cobertura Python, Gameface/Wulf e Flash

Leitura AST dos 35 entrypoints: imports externos diretos resolvem em sources ou stubs;
isso não demonstra assinaturas transitivas ou funcionamento. Varredura delimitada de
78 referências de hooks diretos dos entrypoints e quatro adaptadores prioritários:
71 nomes encontrados por inspeção inicial; restantes requeriam resolução de property,
herança, extensões ou alvo dinâmico. Confirmados clientMode=property em VehicleGunRotator,
VehicleTypeInfoVO.__init__, _EquipmentZoneSoundPlayer._onVehicleStateUpdated na árvore
comp7_core e as_setPanelModeS herdado de PlayersPanelMeta. Não classificar esses casos
como métodos removidos. CompoundAppearance.prerequisites/camera.enable não receberam
prova completa de resolução de herança/alvo nesta revisão; permanecem lacunas, não
incompatibilidades novas confirmadas. Nem todos os imports transitivos/assinaturas de
35 módulos foram auditados: classificação global PARTIAL é intencional.

CT sources/res/scripts/client/gui/impl/lobby/page/lobby_footer.py: LobbyFooter._initChildren
presente; frameworks/wulf/view/view.py: getChildView(resourceID) e
setChildView(resourceID,view=None,chFlags=ChildFlags.AUTO_DESTROY) presentes.
gui/impl/pub/view_component.py: _onLoading/_getChildComponents/_finalize presentes;
RandomHUDView herda ViewComponent, não precisa de redefinir esses métodos para o hook.
RandomHangar._getChildComponents e UserMissionsPresenter existentes. Footer bundle
formatado conserva menu/data-test-id e Footer_section_. Launcher onOpen e SettingsWindow
são contratos nossos inalterados; SVG/filtros/coui continuam RUNTIME_UNVERIFIED.

Nove HTML native_document (footer/header, quatro crew details, perfil, tech tree, TAB)
com source_sha256 iguais ao CT996; crew_barracks e post-battle bundle também mantêm
hash. Não aplicar nem regenerar patches. Battle/ratings source AS3 importa 20 classes
net.wg encontradas em sources_as/catalog.json, incluindo BattleUIDisplayable,
BaseBattlePage, Minimap e PlayersPanelListItem. Não é prova de equivalência de traits/
SWC/ABC em todas as classes. Sete DAAPI e entrypoints mantêm evidência F4; coexistência,
load order, callbacks e destruição real continuam pendentes. Nenhuma comparação binária
profunda nova ou compilação efetuada.

### Incompatibilidades demonstradas, sem correções

I1 — Pipeline/preflight da referência: build_tools/compiler.py:validate_client exige
igualdade exata .version_name com build_data/build_config.json reference.version=
2.4.2.5516. Nova raiz declara 2.4.2.0 Common Test #996. Esse caminho de build com a
referência indicada é recusado antes de gerar. É incompatibilidade de configuração/
proveniência da build, NÃO falha runtime de um mod. O root antigo WoT_Tools/wot-src-CT
existe mas agora declara 2.4.2.5518, não constitui snapshot inequívoco de #995.

I2 — VehicleCarousel: build_data/patches/carousel_2.4.2_ct.json source_sha256 esperado
7e28391b4c51daa555b04d103a4031f7734b8d0728df03f7b73b47fa781873e5;
CT996 res/gui/gameface/_dist/production/mono/hangar/main/bundle.js tem
81ba2baf167f428204e161e6cc058d657d60ca048cbe687641c6910f4f286250.
Dez find ausentes, operações 2/4/8/9/15/16/20/21/22/23. Não basta trocar hash.

I3 — CrewManagement / tooltip bridge: crew_tooltip_2.4.2_ct.json espera
 a7cb133ce2d0495bd8b9cc29794755c55bc6e694f36e6d257b17fc4b6a4967dd;
CT996 res/gui/gameface/_dist/production/mono/hangar/tooltips/bundle.js tem
 d4ebef3be136dac60c31a504de15abb866143e61afb9f4fe3e274791213d857f.
Find da operação2 ie=ae(d(w({tankman:a}))) ausente. HTML CrewDetails e Barracks JS
mantêm hash, mas o conjunto obrigatório crew_tooltip_bridge continua incompatível.

I2/I3: build_tools/validate_build_data.py:apply_patch_set recusa input cujo SHA diverge
e exige contagem exata por operação; compiler.generate chama essa função. São bloqueios
concretos dos geradores, não hipótese visual. Não executados para demonstrar recusa.

I4 — VehicleMarkers: flash_source/vehicle_markers/native-lock.json exige native SWF
34d92354f1c755313b99fd4e268bb78dc130ece24797a271aece5f0a7346537e;
manifest CT996 res/gui/flash/battleVehicleMarkersApp.swf indica
52c5906b04998132efb7a70422999b5dd225d89fb29c49c89d41ba8a59f090b6.
build_tools/vehicle_markers.py:build recusa alteração do filme nativo antes de patch/ABC.
Não substituir lock, reutilizar SWF antigo nem afirmar equivalência de símbolos sem
análise específica autorizada. Não foi observado crash runtime do mod reorganizado.

Contagem: quatro incompatibilidades de preparação/build (três integrações de módulos
+uma referência/preflight). ZERO novos ImportError/TypeError ou crashes de arranque
Python comprovados nesta análise. O manifesto dos patches continua client_build=995;
isso evidencia perfil ainda não aprovado para #996, mas não é contado como quinto
problema nem impede por si só os inputs cujos hashes/contratos permanecem iguais.

### Matriz por módulo

Legenda de evidência: P=mod/res/scripts/client/driftkings/<entrypoint>.py;
C=sources/res/scripts/client sob a raiz CT obrigatória. Recursos são os declarados
em interface_catalog.py/components.json para o entrypoint, não ficheiros experimentais.
STATIC_INCOMPATIBLE abaixo refere integração/build fixa; não afirma crash runtime.
RUNTIME_PENDING também assinala cobertura estática incompleta do módulo integral.

Módulo | Tecnologia | Contratos CT #996 | Estado | Evidência | Impacto | Próxima ação
---|---|---|---|---|---|---
vehicle_carousel | Python/GF/Wulf | main/bundle.js; CarouselController | STATIC_INCOMPATIBLE | I2, carousel_2.4.2_ct.json | Gerador recusado | Autorizar revisão do bridge #996
crew_management | Python/GF/Wulf | VehicleSelectorPopup.onSelectVehicles; tooltip/Barracks | STATIC_INCOMPATIBLE | I3, crew_tooltip_2.4.2_ct.json | Gerador tooltip recusado | Autorizar revisão focal
vehicle_markers | Python/Flash | battleVehicleMarkersApp.swf/lock | STATIC_INCOMPATIBLE | I4, native-lock.json | Patch ABC bloqueado | Autorizar análise do novo SWF
minimap_enhancements | Python/Flash | MinimapMeta; inputHandler/onCameraChanged | AT_RISK | P battle/minimap_enhancements; F4-G3.1 D/E | Ownership/cleanup já conhecido | CT battle; sem correção aqui
sixth_sense_alert | Python/Flash/áudio | SixthSenseIndicator._sixthSenseToggle; SoundGroups.prepareMP3 | AT_RISK | P battle/sixth_sense_alert; F4 E | Cleanup intermédio conhecido | CT battle/som
team_panels | Python/Flash/GF | PlayersPanelMeta.as_setPanelModeS; TAB HTML | AT_RISK | C gui/Scaleform/daapi/view/meta/PlayersPanelMeta.py; F4 C1 | Mesmo objeto entre gerações não provado | CT roster/TAB/reentrada
account_manager | Python/Wulf | realm/predefined_hosts; AccountManagerWindow | RUNTIME_PENDING | P components/account_manager; catálogo janela própria | Login/contas/foco | Validar login sem expor credenciais
aiming_countdown | Python/GF HUD | ReticleText/host neutro | DISABLED | default/aiming_countdown.json enabled=false | Incluído mas apresentação desligada | Não contar como ativo visual
aiming_reticles | Python/Flash | _SPGGunMarkerController._updateDispersionData; clientMode property | RUNTIME_PENDING | P battle/aiming_reticles; C VehicleGunRotator.py | Modos/marker real | CT arcade/sniper/artilharia
artillery_blast_radius | Python/modelos3D | VehicleGunRotator.__updateGunMarker | RUNTIME_PENDING | P battle/artillery_blast_radius; C VehicleGunRotator.py | Geometria/render3D | CT SPG
autoaim_target_indicator | Python/cliente | AvatarInputHandler/Vehicle | RUNTIME_PENDING | P battle/autoaim_target_indicator | Input e entidade alvo | CT autoaim
battle_marks_of_excellence | Python/GF HUD | CrewPresenter.__updateCrewModel; Vehicle.startVisual | RUNTIME_PENDING | P battle/battle_marks_of_excellence; catálogo own_window | Dados/drag/input | CT HUD/segunda batalha
battle_performance | Python/GF HUD+resultados | RibbonsAggregator.suspend; post-battle bundle | RUNTIME_PENDING | P components/battle_performance; hash battle_results igual | HUD e pós-batalha | CT batalha/resultados
battle_preferences | Python/Flash/helpers | TimersPanel; PlayerAvatar.handleKey; Comp7 sounds | RUNTIME_PENDING | P battle/battle_preferences; árvore comp7_core verificada | Opções/hotkeys/extensões | CT opções selecionadas
battle_statistics | Python/GF HUD | CompoundAppearance/host neutro | RUNTIME_PENDING | P battle/battle_statistics; prerequisites não resolvido integralmente | Dados HP e lifecycle | CT TeamStrength
clan_reward_collection | Python/rede cliente | clan_supply; requests; SystemMessages | RUNTIME_PENDING | P lobby/clan_reward_collection; imports diretos presentes | Servidor/permissões/conta | Validar apenas conta aplicável
enemy_spotting_status | Python/cliente | PersonalEfficiencyController/Vehicle | RUNTIME_PENDING | P battle/enemy_spotting_status | Eventos spotting | CT battle
game_log_manager | Python | battle_constants; logging/files | RUNTIME_PENDING | P components/game_log_manager | I/O e opções de log | Conferir logs da build efetiva
gun_traverse_limits | Python/Flash/input | InterfaceScaleSetting; câmaras; camera.enable | RUNTIME_PENDING | P battle/gun_traverse_limits; alvo dinâmico parcial | Escala/input/limites | CT modos/escala
hangar_marks_of_excellence | Python/GF/Wulf | MarkOnGunAchievement.getUserCondition; UserMissions | RUNTIME_PENDING | P lobby/hangar_marks_of_excellence; C user_missions_presenter | Dados/slot/layout | CT garagem/troca veículo
hangar_preferences | Python/GF/Python hooks | Vehicle readiness; header HTML | RUNTIME_PENDING | P lobby/hangar_preferences; HTML hash igual | Opções/menus/internos | CT header e ações
high_caliber_progress | Python/GF HUD | battle_constants/arena; MainGun card | RUNTIME_PENDING | P battle/high_caliber_progress; catálogo own_window | Valores/posição | CT HUD
main | Python/GF/Wulf | RandomHangar._getChildComponents; UserMissions | RUNTIME_PENDING | P components/main; gameface/lobby/main.py | Relógio/locale/slot | CT garagem
penetration_indicator | Python/GF HUD | gun_marker_ctrl/DestructibleEntity/Vehicle | RUNTIME_PENDING | P battle/penetration_indicator; catálogo own_window | Alvo/armadura | CT arcade/sniper
repair_controls | Python/DAAPI/input | BATTLE_VIEW_ALIASES; processors/vehicle | RUNTIME_PENDING | P battle/repair_controls | Uso de consumíveis/input | CT opções reais
server_turret_sync | Python | VehicleGunRotator.setShotPosition | RUNTIME_PENDING | P battle/server_turret_sync; C VehicleGunRotator.py | Servidor/interpolação | CT rotação/disparo
shell_flight_time | Python/GF HUD | ReticleText/host neutro | DISABLED | default/shell_flight_time.json enabled=false | Incluído mas visual desligado | Não afirmar valor visível
sniper_camera | Python/câmara | SniperCamera._readConfigs; SniperControlMode.__setupBinoculars | RUNTIME_PENDING | P battle/sniper_camera; imports/hooks encontrados | Câmara/contextos | CT sniper
sound_bank_loader | Python/áudio/Wulf | dialog_window/WWISE/audio config | RUNTIME_PENDING | P components/sound_bank_loader; sem flag geral | Banks/settings/restart | Validar áudio sem corrigir cliente
target_distance | Python/Flash | VehicleMarkerPlugin.start/stop; py_requestFrameData | AT_RISK | P battle/target_distance; F4 C2 | View antiga lê controller atual, sem mutação | CT markers/segunda batalha
target_information | Python/GF HUD | Vehicle/current target/battle_constants | RUNTIME_PENDING | P battle/target_information; catálogo own_window | Dados e imagem alvo | CT HUD
tech_tree_marks_of_excellence | Python/GF | TechTree native document | RUNTIME_PENDING | P lobby/tech_tree_marks_of_excellence; HTML hash igual | Layout/dados árvore | CT árvore tech
third_person_zoom | Python/câmara | ArcadeCamera.create/readCfg; Strategic/ArtyCamera | RUNTIME_PENDING | P battle/third_person_zoom; hooks diretos presentes | Zoom/modos | CT câmaras
vehicle_health | Python/GF HUD | PlayerEvents/session provider/HP | RUNTIME_PENDING | P battle/vehicle_health; catálogo own_window | Atualização HP/modelo | CT HUD
profile_ratings | Python/GF | AchievementsMainView native document | RUNTIME_PENDING | P lobby/profile_ratings; HTML hash igual | Dados/perfil/layout | CT perfil
Settings/Launcher (serviço) | Python/GF/Wulf | LobbyFooter._initChildren; View.getChildView/setChildView | STATIC_COMPATIBLE | C lobby_footer.py:41; view.py:210/216; HTML/DOM iguais | SVG/filtros e foco por provar | CT garagem; contrato parcial não runtime PASS
Host neutro (infraestrutura) | Python/GF/Wulf | RandomHUDView/ViewComponent; R custom; nove subViews | RUNTIME_PENDING | C gui/impl/battle/random/hud.py; view_component.py:65/71/161 | R/none/dragging/lifecycle | CT nove cartões e segunda batalha
ModsListAPI/OpenWG (externos) | Terceiros | Pacotes pins no build_config; API externa | NOT_EVALUATED | Não incluídos nas fontes CT; análise F5 conservada | Compatibilidade dos binários externos não provada | Confirmar versões/carga; não remover dependências

### Recursos, dependências e lifecycle do inventário

Ficheiros principais por módulo: P <entrypoint>.py, respetiva settings/definitions e
config_files/assets do components.json; adapters de apresentação referidos pelo catálogo
GAMEFACE/FLASH_COMPONENTS. Sem duplicar componentes por superfície. Grupos próprios:
account_manager/SettingsWindow no lobby; quatro plugins UserMissions; nove cards own_window;
seis native_documents; battle_performance também pós-batalha; câmaras/input sem renderer
Gameface; Minimap/Sixth/Distance/Ammo/Debug/Overlay/RatingScreens pelo Flash.

Core importa/declarara hooks, inicia serviços e componentes pelas ServiceSpec/contextos;
init/start e fini/stop pertencem aos owners existentes. onSettingsChanged/subscriptions
seguem esse owner; eventos e dados chegam dos controladores cliente. Não foi validada
cada transição dinâmica no CT996. Resource R custom é entregue pelo pacote Driftkings,
não se espera encontrar os IDs Driftkings já no cliente limpo. Sentinela/common.none,
input/dragging/model commands requerem runtime. Não inferir ausência de R próprio como
ImportError do cliente nem afirmar que um import presente garante funcionalidade.

ModsListAPI 1.8.0 e OpenWG 1.2.2 continuam listados/pinados em ui_dependencies. Os 20
componentes nativos não usam OpenWG no seu transporte; independência efetiva de toda
a instalação continua RUNTIME_UNVERIFIED. Launcher NATIVE PRIMARY sem novo registo
ModsList. A biblioteca ModsList tem dependências próprias; não foram executadas nem
alteradas e não fazem parte das fontes WG fornecidas. Ordem externa de carregamento
só pode ser confirmada em logs inequivocamente CT996 da build em teste.

### Comparação anterior e problemas conhecidos

Evidência #995 disponível: patches/hash/lock aprovados e registos Fases3–5/beta.9.
Root legado WoT_Tools já anuncia 5518, pelo que diferença de texto descompilado nele
não prova mudança #995→#996 (headers/ferramenta também diferem). Comparação limitada
às hashes de input e âncoras efetivamente usadas; não exigido snapshot completo antigo.

CT996_CONTRACT_CHANGE / NEW_STATIC_INCOMPATIBILITY: I2/I3/I4 contra pins anteriores;
I1 incompatibilidade de referência/preflight. Causalidade temporal exata por revisão
intermédia não provada além desse confronto. KNOWN_REORGANIZATION_RISK: host neutro/R,
G3.2 retry dependente de instância conservada, C1 mesma instância reutilizada, SVG/filtros.
KNOWN_BETA9 / riscos anteriores à reorganização: criação parcial factory, callbacks
Distance, troca de input handler e cleanup Minimap/Sixth. Estes já foram caracterizados
na F4 e não são imputados como crashes novos CT996. RUNTIME_UNVERIFIED para todos os
resultados em cliente; nenhum log antigo usado como prova da reorganização atual.
Nenhum log CT996 com versão de modpack inequivocamente aplicável foi usado.

### Preparação da primeira build e próximos passos propostos

Build completa com os 35 módulos não pode avançar sem decisões sobre I1–I4: são
recusas demonstradas do pipeline, não receios hipotéticos de runtime. Próxima autorização
proposta: atualização mínima do contrato de referência e revisão focada dos dois
bridges e do patch nativo de marcadores, com fontes996 e critérios de hash/semântica.
Não mudar só hashes, não aplicar patches aproximados e não instalar SWF antigos.
Alternativa de build reduzida só se explicitamente aprovada e preservando dependências;
nenhum módulo foi desativado/removido para contornar bloqueios nesta execução.

Os restantes módulos podem integrar a primeira build experimental após resolver os
bloqueios obrigatórios, conservando classificação runtime pendente e flags atuais;
não exigir antes prova de eliminação de riscos já conhecidos. Prioridade manual:
1) arranque e serviços/logs da build experimental exata; 2) garagem, launcher/settings,
relógio/marks/crew/carrossel/perfil/árvore; 3) treino/batalha arcade+sniper com HUD oficial,
nove cards (dois desativados por config, ativar apenas se autorizado), input/V/Ctrl/drag;
4) Flash/TAB/minimap/Sixth/markers/SPG; 5) segunda batalha e regresso ao hangar;
6) áudio, performance e coexistência de dependências. Não iniciado jogo/build/teste aqui.

### Preservação e veredicto

Apenas cabeçalho/quadro e secção34 deste progresso alterados. Texto anterior conferido
por reversão em memória destes deltas. Código de produção, assets, catálogo, pipeline,
SWF/SWC, testes e master plan intactos; hashes delimitados conferidos antes/depois.
Fontes CT apenas lidas; metadata divergente não corrigida. Beta.9 original preservada:
22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9.
Sem Git de escrita, extração/decompilação, regeneração, build, instalação ou cliente.

F6-G1.1 — CT #996 STATIC COMPATIBILITY REVIEW: PARTIAL.
CT #996 SOURCES — PARTIAL (manifest/version #996 verificados; relatórios #995 históricos).
STATIC INCOMPATIBILITIES — 4 CONFIRMED (3 módulos/geradores + 1 preflight).
RUNTIME VALIDATION — PENDING.
PRODUCTION CODE UNCHANGED — PASS.
ORIGINAL BETA.9 PRESERVED — PASS.
F6-G1.1 — AWAITING_APPROVAL. Parar; correções exigem autorização específica.

## 35. F6-G2 — Correção dirigida do preflight CT #996

2026-11-13, Europe/Lisbon. Pedido expresso aceita F6-G1.1 como diagnóstico parcial e
autoriza exclusivamente identificação/validação CT #996, testes focalizados e progresso.
Fase6 IN_PROGRESS; F6-G2 VALIDATION_PENDING. Não iniciados F6-G3 ou outras regiões.
A secção34 conserva diagnóstico anterior e quatro bloqueios históricos; só I1 resolvido
neste âmbito. I2/I3/I4 permanecem sem correção.

### Baseline, causa e identificadores distintos

Worktree reorganization; branch reorganization/settingslab; HEAD
bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3. Inicial 81 caminhos:
54 M/3 D/24 untracked, staging vazio. Final 83: 55 M/3 D/25 untracked, staging vazio.
Sem divergências materiais. Função real chama-se check_client em build_tools/compiler.py;
validate_client nas descrições anteriores era designação informal, não símbolo existente.

Causa: comparação literal de .version_name com reference.version=2.4.2.5516.
Esse identificador de referência legado também é usado pelo validador das bibliotecas
SWC (libraries.source_version). Não é o mesmo campo que versão pública ou revisão.
Não foi alterado nem reinterpretado como 2.4.2.0/2660091.

Cliente instalado lido em C:/Games/World_of_Tanks_CT/version.xml:
version v.2.4.2.0 Common Test #996; meta/client 2660091; meta/realm CT.
Fontes autorizadas em Driftkings_WoT_Sources/wot_src_CT: .version_name e manifest
com essa versão/build/revisão. Manifest .game_version.raw e campos estruturados são
agora confrontados, não apenas a versão normalizada. #995 revisão2655094 tem evidência
histórica no report.json de 2026-11-09; esse relatório não identifica a raiz atual.
Root legado WoT_Tools/wot-src-CT anuncia 5518: não foi mapeado ou aceite como sinónimo
de #996. Nenhuma correspondência 5516/5518 → revisão pública foi inventada.

### Ficheiros modificados e patch mínimo

- build_tools/compiler.py: check_client e lista local dos oito contratos Python
  críticos CT_REFERENCE_FILES; import re para parsing estrito.
- build_data/build_config.json: acrescentado apenas reference.ct_builds, allowlist
  995:2655094 e 996:2660091. reference.version=2.4.2.5516 permanece para contrato legado
  e validação SWC; demais deltas anteriores do ficheiro não foram alterados.
- novo tests/build/test_client_preflight.py: nove testes focalizados.
- este progresso.
Nenhum módulo dos mods, patch de recurso, lock SWF, gerador ou toolchain.local alterado.
O caminho novo é passado explicitamente em reference_root; não alterado default da
máquina nem escritas nas fontes CT. Não criado subsistema de perfis regionais.

### Semântica do preflight

Preservadas versão pública alvo e realm suportado. Exigidos CT, formato completo
v.x.x.x.x Common Test #N e combinação build/revisão explicitamente aprovada. Prefixo
2.4.2 sozinho, build desconhecida, revisão errada ou cliente de outra região falham.

Raiz moderna: .version_name deve corresponder exatamente à identidade do cliente;
manifest schema/realm/version_name/consistent e game_version.raw/number/suffix/build/
client_revision/realm devem concordar. Exigidas pastas sources/sources_as/
sources_gameface/__stubs e os oito ficheiros da revisão estática anterior:
LobbyFooter, View, ViewComponent, RandomHUDView, RandomHangar, UserMissionsPresenter,
PlayersPanelMeta e PackageBusinessHandler. Paths de output têm de ser os esperados,
ficheiros existentes sem escape da raiz, status success, input_sha256 ligado ao sha256
do bytecode e conteúdo descompilado com hash igual ao manifesto. Bool não vale como
número de build. Não se aceita raiz incompleta nesses contratos.

Compatibilidade histórica: mantido identificador legado EXATO 2.4.2.5516 para target
CT #995 aprovado; nunca serve para #996. Se a raiz legada não tem manifesto, conserva
a igualdade estrita e exige presença segura dos oito contratos; sem manifesto não
há nova prova dos seus hashes nem de integridade global.
Se houver manifesto, também tem de concordar e passar verificações modernas; um
manifest #996 por trás de label legado no target995 é rejeitado. Formato moderno #995
com revisão2655094 também aprovado nos testes. Não foram aceites outros labels internos.

Metadados de identidade: version.xml, .version_name e manifest nos campos usados.
Metadados documentais: README/report antigos, não usados para selecionar target atual.
Metadados de integridade: entradas individuais e hashes dos oito outputs exigidos.
README/report/verify antigos continuam inalterados e explicitamente desatualizados.
Não se afirma integridade global de todos os milhares de ficheiros a partir de uma
etiqueta ou manifest: só contratos críticos conferidos mais os locks independentes.
Recursos Gameface/SWF continuam sujeitos a hashes e contratos dos próprios geradores.

### Testes positivos, negativos e verificação real sem build

Primeira invocação dos testes antes do patch: falha de import da nova constante ainda
inexistente; nenhum gerador foi chamado. Resultado final: nove testes de preflight PASS
em Python3 (tooling de build; não runtime Python2). Cobertura:
- CT996 correto, aceitando documentos históricos #995 sem os confundir com identidade;
- CT995 moderno e label legado estrito;
- cliente com versão/build/revisão/realm errados;
- fonte com label/build desconhecido ou legado usado para #996;
- manifesto contraditório em realm/build/revisão/versão/suffix/raw/consistent;
- manifesto/pastas/ficheiro crítico ausentes;
- conteúdo crítico alterado ou proveniência input_sha256 divergente;
- manifesto contraditório escondido por label legado;
- apply_patch_set continua a rejeitar bundle com hash inválido mesmo após preflight válido.

Três testes existentes test_compiler_version.py PASS. Total focalizado: 12 PASS,
sem suite completa. Isort do teste novo e diff --check delimitado PASS.
Execução direta e isolada check_client(ROOT,config,{game_root: CT, reference_root:
Driftkings_WoT_Sources/wot_src_CT}) devolveu CT com cliente #996/revisão2660091.
Não chamado compiler.main, generate, build_plan, gerador de assets ou compilador.
Nenhum output de build produzido. Fixtures dos testes usam diretórios temporários
isolados e são removidos pelo próprio teste.

### Segurança preservada e bloqueios seguintes

A nova identidade permite ultrapassar I1, não aprova recursos ou produz uma build.
reference.version e verificação SWC não foram relaxadas. apply_patch_set continua a
exigir source/output hash e contagem por operação. VehicleMarkers.build mantém o lock
do filme nativo. Código desses validadores/geradores não alterado; patches/locks e
mod code preservados por comparação delimitada de hashes antes/depois.

Continuam explícitos: I2 carousel_2.4.2_ct.json com bundle e dez âncoras divergentes;
I3 crew_tooltip_2.4.2_ct.json com bundle/operação2 divergentes; I4 native-lock.json de
battleVehicleMarkersApp.swf divergente. Nenhuma atualização de hash ou tentativa de
aplicar/generar esses recursos. São os três bloqueios restantes à build completa.

### Preservação, limites e rollback

Código dos mods Python/Gameface/Flash, launcher, catálogo, assets, configurações de
mods, ModsList/OpenWG, SWF/SWC e experiências preservados; única configuração alterada
é o allowlist de referência do build_config autorizado. Master plan intacto.
Fontes CT e cliente lidos, nunca escritos. Beta.9 original confirmada:
22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9.
Progresso anterior preservado por inversão em memória de dois deltas e retirada da
secção35. Sem build, instalação, jogo, extração, commit ou operação Git de escrita.

Limites: teste positivo real identifica cliente/fonte e oito contratos, não runtime
ou equivalência binária de recursos; label legado conserva garantia histórica mais
limitada. Fase7 mantém validação em jogo. Não transformar aceite do preflight em
CT996 MODPACK PASS ou autorização para corrigir os próximos três bloqueios.
Rollback proposto, não executado: inverter somente check_client/CT_REFERENCE_FILES e
import re desta tarefa, retirar reference.ct_builds e teste novo e reverter este delta
documental. Preservar todos os deltas anteriores, não restaurar ficheiros inteiros do
HEAD nem usar reset/clean. Aguardar aceitação e autorização específica F6-G3.

F6-G2 — CT996 PREFLIGHT FIX: PASS.
CT996 IDENTITY — VERIFIED (cliente, fonte e oito contratos críticos).
VERSION SAFETY — PRESERVED.
INDEPENDENT RESOURCE LOCKS — PRESERVED.
PRODUCTION MOD CODE — UNCHANGED.
ORIGINAL BETA.9 — PRESERVED.
F6-G2 — VALIDATION_PENDING. Parar; não iniciar F6-G3.

## 36. F6-G3 — Compatibilidade dos bridges Gameface com Common Test #996

2026-11-13, Europe/Lisbon. Pedido expresso autoriza análise dirigida e adaptação apenas dos dois bridges (carrossel e tooltip da tripulação), geradores e testes diretamente afetados. Não iniciados F6-G4, build completa, instalação, arranque do CT, testes em jogo ou Fase 7. Sem commits, push, merge, tags, reset, clean ou stash.

### Estado Git inicial e final

Worktree reorganization; branch reorganization/settingslab; HEAD bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3 (confirmado). Staging vazio antes e depois. Inicial: 84 entradas (56 M, 3 D, 25 untracked) mais os dois patches `_ct996.json`, já presentes no disco e não registados em progresso antes desta fase. Final: 86 entradas (56 M, 3 D, 27 untracked). Delta desta fase: `build_tools/validate_build_data.py` (M), `build_tools/compiler.py` (alteração local sobre o M já existente), `build_data/build_config.json` (dois generators acrescentados sobre o M já existente) e `tests/build/test_gameface_patch_variants.py` (novo). Alterações de `mod/`, `flash_source/` e SWF/lock preexistentes não foram tocadas.

### Ficheiros e geradores envolvidos

- Patches 995 (inalterados, tracked): `build_data/patches/carousel_2.4.2_ct.json`, `build_data/patches/crew_tooltip_2.4.2_ct.json`.
- Patches 996 (untracked, revistos, não reescritos): `build_data/patches/carousel_2.4.2_ct996.json` (24 operações) e `build_data/patches/crew_tooltip_2.4.2_ct996.json` (3 operações).
- Geradores: `build_tools/validate_build_data.py` (`apply_patch_set`, `build_plan`) e `build_tools/compiler.py` (`generate`, `check_client`).
- Inputs: `res/packages/gui-part1..4.pkg` do cliente CT #996 instalado; bundles `gui/gameface/_dist/production/mono/hangar/main/bundle.js` e `.../hangar/tooltips/bundle.js`.
- Testes diretos: `tests/build/test_client_preflight.py`, `tests/build/test_compiler_version.py`, `tests/build/test_native_carousel_catalog.py`, `tests/build/test_native_crew_catalog.py`, e o novo `tests/build/test_gameface_patch_variants.py`.
- Não alterados: contratos Python, launcher DK, componentes Gameface/Wulf, Flash/SWF, `native-lock.json`, fontes CT.

### Identificação das builds e hashes

| Recurso | Build | source SHA-256 | output SHA-256 |
|---|---|---|---|
| carousel `main/bundle.js` | 995 (pin histórico) | 7e28391b4c51daa555b04d103a4031f7734b8d0728df03f7b73b47fa781873e5 | 0ad03065a96418af626a78b8ee2f8954fbc1accb899f5f328e9946cf0518eec3 |
| carousel `main/bundle.js` | 996 | 81ba2baf167f428204e161e6cc058d657d60ca048cbe687641c6910f4f286250 | c03f1d989b87d352b29e28e8ba4d572253076b66d1d637875ee3286f6f5ddf98 (458078 bytes) |
| tooltip `tooltips/bundle.js` | 995 (pin histórico) | a7cb133ce2d0495bd8b9cc29794755c55bc6e694f36e6d257b17fc4b6a4967dd | 190534383748a3daac3d8097a15d6436174dbcf12648540cb1f06aa0eef9a498 |
| tooltip `tooltips/bundle.js` | 996 | d4ebef3be136dac60c31a504de15abb866143e61afb9f4fe3e274791213d857f | 1d7914a159426ad0e0d1f35562d51b5cde5b55132c15c1ad95c2180a610f9596 (20732 bytes) |

Os bundles #996 em `wot_src_CT` e os do cliente instalado (`C:/Games/World_of_Tanks_CT`, `version.xml` = `v.2.4.2.0 Common Test #996`, client 2660091) têm os mesmos hashes de input (leitura apenas do pacote, sem extração). Os hashes #996 ficam associados exclusivamente a `patch_files['996']` e a `client_build == '996'` do patch.

### Carrossel — análise das dez operações que falhavam em #995

Numeração 1-based de G1.1: #2, #4, #8, #9, #15, #16, #20, #21, #22, #23. A equivalência foi verificada pela tabela de exports de `hangar/chunks/lib.js` e pelo alias de cada identificador no bundle #996, não por substituição de string semelhante. Todas as alterações são renomeações de minificação; a função do patch e os callbacks são os de #995.

Operação | Âncora anterior | Equivalente #996 | Alteração encontrada | Resultado | Evidência
---|---|---|---|---|---
#2 | `var[ar,sr]=Ca("HeroTankModelProvider")` | `var[ar,sr]=va("HeroTankModelProvider")` | `Ca` em #996 é o enum `sizes` (`in as Ca`); a fábrica é `va` = `initializeModelWithContext` (`hr as va`) | PASS | export de lib; âncora única
#4 | `p=ds.primitive(()=>{const t=[...c.getAll()]` | `p=ls.primitive(()=>{…` | `ds` em #996 é `placeholderVisibility` (`q`); `ls` = `computeds` (`pr`), com `.primitive`/`.structural` no mesmo bloco | PASS | export de lib; uso local
#8 | `className:Es(ty,i?.base)` | `className:Ps(ty,i?.base)` | `Ps` = `clsx` (`to`); `Es` passou a outro símbolo | PASS | export de lib
#9 | `Jt(zx.default,zx.breakpoints)` e `Xe(…)` | `Ut(…)` e `Ze(…)` | `Ut` = `useAdaptive(e,t)` (`di`); `Ze` = `remToPx$1` (`Ta`); `Jt` passou a `Currency` | PASS | export de lib; assinatura
#15 | `return 2===_?(0,ai.jsx)(rs,` | `return 2===_?(0,ai.jsx)(xs,` | `xs` = `ErrorHandler` (`rt`), wrapper com `failure` | PASS | export de lib; uso `failure:`
#16 | `elementWidth:t-Xe(1)` | `elementWidth:t-Ze(1)` | `Ze` = `remToPx` | PASS | export de lib
#20 | `eg=Qt(function({type:e}){const a=Yr()` | `eg=qt(function({type:e}){const t=Yr()` | `qt` = `observer` (`cr`); o corpo usa `t.model` | PASS | export de lib; corpo do componente
#21 | `children:n})})});if(e===Ch.rentTank)` | `children:r})})});if(e===Ch.rentTank)` | `r` = `t.model.slots.price.value.get()`; o Fragment recebe o valor de preço | PASS | atribuição local no mesmo componente
#22 | `params:{count:r}}),e===Ch.restoreTank` | `params:{count:i}}),e===Ch.restoreTank` | `i` = `t.model.slots.free.get()` (buyTankEmptyCount) | PASS | atribuição local
#23 | `c=Qs()` | `c=Ys()` | `Ys` = `useSounds` (`xr`); `c.play("mouse-enter",…)` no mesmo componente; `Qs` em #996 é `heavyTankRoles` | PASS | export de lib; uso `c.play`

Restantes 14 operações: âncora byte-idêntica à de #995, uma ocorrência exata em #996 (`count` verificado) e identificadores livres do mesmo módulo. Semântica inferida do contexto idêntico, não de análise de escopo completa. Nenhuma substituição aproximada; nenhuma operação eliminada.

Resultado do carrossel: 24/24 operações aplicadas; output completo; nenhuma substituição parcial.

### Tooltip da tripulação — operação 2

- Âncora: `(0,me.jsx)(ue,{})]})})})}),ks=` (inalterada e única em #996).
- Contexto: `ie=ae(…)` é o accessor dos parâmetros do componente; `ie().dkCrewProgression` só é lido quando `lines` existe.
- Operação 1 (schema): `ie=ae(d(w({tankman:a})))` passa a `ie=ae(n(p({tankman:u})))` em #996, com `n`=createParser, `p`=object (`Wt`), `u`=TankmanSchema. O campo `dkCrewProgression` usa `Gt`=`optional`, `t`=array e `x`=string. Em #995, `sn` era `optional`; em #996 `sn` é `TruncatedText`, por isso o import passou a `Gt`.
- Callbacks e eventos: nenhum novo; o bloco só lê `window.__dkCrewProgression` no mesmo fluxo.
- Timing/lifecycle: sem alteração estrutural; o JSX acrescentado é um bloco irmão opcional.
- Resultado: PASS (estático e isolado). Contrato do Crew Progression preservado; sem redesenho do tooltip.

### Adaptações implementadas

1. `build_tools/validate_build_data.py`:
   - `ct_client_build(game_root, config)`: lê `version.xml` e aceita apenas builds listadas em `reference.ct_builds`, com revisão exata.
   - `gameface_patch_for_build(root, spec, build)`: seleção determinística por build; rejeita build desconhecida; exige `client_build == build` e `resource` corretos.
   - Geradores com `patch_files` validam todas as variantes. Geradores de ficheiro único (`patch_file`: crew_barracks e nove native_document) mantêm o pin histórico #995 e o hash exato, sem fallback nem mudança de comportamento.
   - Ramo `check_game`: seleciona a variante pela identidade instalada antes de `apply_patch_set`.
2. `build_tools/compiler.py`: `check_client` usa `ct_client_build` (sem duplicação); `generate` seleciona o patch por build. Ficheiro mantido com CRLF.
3. `build_data/build_config.json`: `carousel` e `crew_tooltip` passam de `patch_file` a `patch_files: {"995": …, "996": …}`. Patches 995 não alterados.
4. `tests/build/test_gameface_patch_variants.py` (novo, 5 testes): pins 995/996 por hash e `client_build`; build desconhecida; patch declarando outra build; input de outro bundle ou com um byte alterado; identidade e revisão instaladas.

Nenhum patch 995 foi alterado; nenhum hash 995 foi substituído.

### Testes e validação

- Testes diretos (`PYTHONPATH=tests`): 20 PASS, 2 FAIL (ver abaixo). Preflight F6-G2 (9 testes) e `test_compiler_version` (3) PASS.
- Falhas pré-existentes, não causadas por esta fase e não corrigidas:
  - `test_native_carousel_catalog::test_protected_sources_and_calculations_are_preserved`: falha em `launcher.js` (diferente do baseline, Fase 5) antes de chegar ao build_config.
  - `test_native_crew_catalog::test_calculations_patches_and_existing_integrations_preserved`: `build_config.json` difere do hash base desde a F6-G2 (`ct_builds`). Antes desta fase o valor era `d3d36b99…`; agora é `7a9d685a…`; ambos diferem de `0a4ed486…`. A fixture não foi alterada; decisão pendente.
- Validação isolada dos bundles (scripts em scratchpad, fora das pastas de distribuição; sem build):
  - Input #996 validado: carousel `81ba2baf…` e tooltip `d4ebef3b…`, lidos do pacote instalado.
  - Carrossel: 24/24 operações, 24 substituições esperadas, output `c03f1d98…` igual ao hash declarado.
  - Tooltip: 3/3 operações, output `1d7914a1…` igual ao hash declarado.
  - `node --check` (ESM) sobre os dois outputs: sem erros de sintaxe.
  - Integração presente: `window.DKCarouselNative` (12), `dkCarouselConfig` (14), `dk-carousel-config` (1), `dkCrewProgression` (2), `dkOptional` (2).
  - `lib.js` já era importado antes de `global.js` nos dois bundles: a ordem de avaliação não muda com a nova linha de import.
  - Casos negativos, todos recusados: bundle de outro recurso; um byte alterado; build 997; contagem de operação errada (aplicação parcial); âncora ausente; patch 995 sobre bundle 996.

### Compatibilidade #995

- Patches e hashes 995 preservados. `gameface_patch_for_build(…, '995')` devolve o ficheiro 995 com o `source_sha256` histórico (coberto pelo teste novo).
- Geradores de ficheiro único mantêm o pin #995 sem alteração.
- Os inputs #995 não puderam ser validados binariamente (sem bundles #995 no workspace). A garantia é o hash pinado e a recusa de qualquer input diferente.

### Hash safety

- Verificação por hash mantida; nenhum fallback silencioso; nenhum patch parcial; erros explícitos.
- Nenhum hash aceite por prefixo de versão nem qualquer hash aceite.

### Contratos Driftkings preservados

- Carrossel: `window.DKCarouselNative` (config, compare, actionAllowed, wheel, footprint, rowCount, groupColumns, gap, vehicleTypes, filterAllowed, counts), evento `dk-carousel-config` e `dkCarouselRevision` preservados textualmente.
- Tooltip: `window.__dkCrewProgression.getRow` e campo `dkCrewProgression` (`lines`, `kinds`) preservados.
- Nenhum módulo Python de contrato, launcher DK, componente Gameface, Flash/SWF, `native-lock.json` ou fonte CT foi alterado.

### Riscos e limitações

- Sem validação runtime: nenhum arranque do CT, nenhuma instalação, nenhum teste em jogo. A equivalência é estática e de bundle; o runtime continua pendente (Fase 7).
- As renomeações foram validadas por tabela de exports/aliases e uso local, não por análise AST de escopo completa (acorn não está instalado; não foi instalado para não alterar o ambiente).
- Operações com âncora inalterada foram aceites por identidade textual e unicidade, não por análise de escopo independente.
- Geradores de ficheiro único (crew_barracks, native_document) permanecem pinados a #995 e não foram analisados nesta fase. G1.1 indicou que algumas fontes têm hash igual em #996; isso não está decidido aqui.
- Testes `test_native_*_catalog` com baseline antigo continuam a falhar (ver acima).
- `build_tools/generate_ui_catalog.py` exige `client_build == '995'` nos native_document; não foi tocado.

### Estado dos bloqueios

- I2 (carrossel): resolvido estaticamente e por bundle.
- I3 (tooltip, operação 2): resolvido estaticamente e por bundle.
- I4 (VehicleMarkers / `native-lock.json`): inalterado; fora de âmbito.
- Pendente de decisão: baseline dos testes protegidos (hash do `build_config`, `launcher.js`).

### Veredictos

F6-G3 — GAMEFACE BRIDGES CT996: PASS (estático e validação isolada; runtime pendente)
CAROUSEL CT996 — PASS
CREW TOOLTIP CT996 — PASS
CT995 COMPATIBILITY — PRESERVED
HASH SAFETY — PRESERVED
OUTPUT STRUCTURAL VALIDATION — PASS
PRODUCTION MOD CODE — UNCHANGED
ORIGINAL BETA.9 — NOT RE-VERIFIED (nenhum ficheiro Beta.9/backup tocado; hash de referência 22ed6826… não recalculado nesta sessão)
FASE 6 — IN_PROGRESS

F6-G3 — aguarda revisão. Não iniciar F6-G4 sem autorização expressa.

## 37. F6-G4 — Compatibilidade do SWF nativo dos marcadores com Common Test #996

2026-11-13, Europe/Lisbon. Pedido expresso autoriza investigar e corrigir apenas o bloqueio I4 (`battleVehicleMarkersApp.swf`), com alteração mínima do lock/seleção e verificações isoladas. Não executados: build completa, instalação, arranque do CT, testes em jogo, compilação de outros SWF, F6-G5, Fase 7, commits ou operações Git destrutivas.

### Estado Git inicial e final

Worktree reorganization; branch reorganization/settingslab; HEAD bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3; staging vazio antes e depois. Inicial: 86 entradas (56 M, 3 D, 27 untracked). Final: 90 entradas (58 M, 3 D, 29 untracked). Delta desta fase: `build_tools/vehicle_markers.py` (M), `build_tools/vehicle_markers_patch.py` (M), `flash_source/vehicle_markers/native-lock.ct996.json` (novo), `tests/build/test_vehicle_markers_lock.py` (novo), mais alterações locais em `build_tools/validate_build_data.py` e `build_data/build_config.json` (já M) e este progresso. Repositório original e fontes CT apenas lidos.

### Causa do bloqueio

`build_tools/vehicle_markers.py:build` lia um único `native-lock.json` e recusava qualquer filme nativo com SHA-256 diferente de `34d92354…` (#995). O filme #996 tem outro hash, por isso o gerador parava antes de qualquer patch. Não havia seleção por build.

### Identidade e proveniência do SWF #996

- Recurso: `gui/flash/battleVehicleMarkersApp.swf` em `res/packages/gui-part2.pkg`.
- SHA-256: `52c5906b04998132efb7a70422999b5dd225d89fb29c49c89d41ba8a59f090b6`, 143792 bytes, `CWS` versão 11.
- O mesmo hash foi obtido do pacote do cliente instalado (`C:/Games/World_of_Tanks_CT`, `v.2.4.2.0 Common Test #996`, client 2660091) e de `wot_src_CT/sources/res/gui/flash/`.
- SWF nativo #995 (`34d92354…`): não está disponível no disco. Referência usada: o output `driftkings_vehicle_markers.swf` de 2026-11-09 no repositório original (`build/flash/`, 827071 bytes, lido sem alterar), que contém o ABC nativo #995 já patchado.
- Os três SWF experimentais da Fase 4 são `driftkingsbattle.swf` (battle Flash), não o filme dos marcadores; não existe SWF experimental de marcadores.

### Estrutura SWF

| | nativo #996 | output #996 | output #995 (referência) |
|---|---|---|---|
| Assinatura / versão | CWS / 11 | FWS / 11 | FWS / 11 |
| RECT, frame rate, frame count | `780004e200000ea60000180100` | igual | igual |
| Tags | 10 | 32 | 32 |
| DoABC (82) | 1 (`frame1`) | 2 (`frame1`, `driftkings_vehicle_markers`) | 2 (iguais) |
| SymbolClass | 1 entrada: `net.wg.app.impl.BattleVehicleMarkersApp` (id 0) | 11 entradas | 11 entradas, idênticas às de #996 |
| Fontes (75) / nomes (88) | 0 / 0 | 10 / 10 | 10 / 10 |

Os nove tags não-ABC do filme nativo #996 aparecem byte a byte e pela mesma ordem no output. Não há DefineSprite, ExportAssets nem ImportAssets no filme nativo. As dez entradas adicionais do SymbolClass são as faces `driftkings.utils.fontlibrary_Face0..9`, com ids remapeados sem colisão.

### Estrutura ABC/AVM2

- ABC nativo #996: 366 classes. Output #996: as mesmas 366 classes mais 20 no ABC do helper.
- Output #995 contra output #996 (ABC nativo patchado, desmontado com RABCDAsm): mesmo conjunto de 366 classes; zero diferenças de superclasse, interfaces, traits ou assinaturas; todos os ficheiros de classe idênticos. A única diferença é a ordem de dois scripts: `net/wg/mock/utils/MockCommons` e `MockDateTime` trocam os índices 309/310. Classificação: cosmética (ordenação do compilador), sem alteração de contrato.
- ABC do helper: 20 classes idênticas entre os dois outputs.
- Nativo #996 contra output #996: diferem só `VehicleMarker` e `VehicleMarkersManager` (corpos patchados; traits e assinaturas iguais) e dois artefactos de reassemblagem do RABCDAsm (rótulos `#0/#1` de namespaces privados homónimos em `lesta.managers.windows:BitmapManager` e de dois `init` em `GoalFlagMarker`). Os mesmos artefactos existem no output #995.

Limite: sem o SWF nativo #995 não há comparação binária integral dos dois inputs; a comparação é entre o ABC #995 patchado e o #996 patchado.

### Contratos dos marcadores

- Entrada do filme: `net.wg.app.impl.BattleVehicleMarkersApp`, inalterada.
- `VehicleMarker` em #996: `draw()`, `updateMarkerSettings()`, `updateCriticalLayout()`, `onBeforeDispose()` e `showHitLabelAnim(int,String,uint)` protegidos; `setHealth(int)`, `updateHealth(int,uint,String,int)`, `updateState(String,Boolean,String,String,Boolean)` públicos; todos `void`, uma ocorrência cada. Getter `markerSettings`:`Object`. Slots protegidos `model`:`VehicleMarkerVO`, `vehicleDestroyed`:`Boolean`, `isStickyAndOutOfScreen`:`Boolean`.
- `VehicleMarkersManager`: `as_setMarkerSettings(Object)` e `as_setColorBlind(Boolean)`, `void`, uma ocorrência cada.
- Membros lidos dinamicamente pelo helper AS3 existem em #996: `marker.entityType`, `exInfo`, `isSpeaking`, `levelIcon`, `marker`, `vehicleIcon`, `vehicleMarkerHoverMC`; `model.currHealth`, `entityName`, `maxHealth`, `pClan`, `pName`, `vClass`, `vLevel`, `vType`.
- Contratos Python ↔ AS3, DAAPI e código Python dos marcadores: não alterados.

### Mecanismo de patch

- Identificação do input: SHA-256 exato do filme no lock.
- Operações: `abcexport` → `rabcdasm` → edição textual de `VehicleMarker.class.asasm` e `VehicleMarkersManager.class.asasm` → `rabcasm` → `abcreplace` do ABC 0 → injeção do ABC do helper e das fontes.
- As operações localizam métodos pelo nome do trait e exigem exatamente uma ocorrência; não usam offsets, índices ABC nem ordinais. O único índice é o ABC `0`, e o output é recusado se não tiver exatamente dois DoABC.
- `VehicleMarker`: `restoreIcons` no início e `render` antes de cada `returnvoid` em seis métodos; `damage` em `updateHealth`; `clearTransient` em `setHealth`; guarda `damageEnabled` em `showHitLabelAnim`; `nativeSettings` no getter `markerSettings`; `clear` em `onBeforeDispose`.
- `VehicleMarkersManager`: `receiveStats`/`configure` em `as_setMarkerSettings`; `setColorBlind` em `as_setColorBlind`.
- Risco identificado: um método com o mesmo nome mas outra assinatura seria patchado e produziria um SWF válido mas incompatível. Foi acrescentada uma verificação de contrato antes do patch (ver abaixo).
- Nenhuma operação precisou de adaptação para #996.

### Alterações implementadas

1. `flash_source/vehicle_markers/native-lock.ct996.json` (novo): `clientBuild` 996, `clientRevision` 2660091, hash `52c5906b…`. O `native-lock.json` histórico não foi tocado.
2. `build_data/build_config.json`: `vehicle_markers_flash` passa de `lock` a `locks: {"995": …native-lock.json, "996": …native-lock.ct996.json}`.
3. `build_tools/vehicle_markers_patch.py`: `marker_lock_for_build` (seleção exata por build; lock sem `clientBuild` vale só para #995), `verify_native_movie` (hash exato), `verify_marker_contract` e `verify_manager_contract` (presença única, parâmetros usados, retorno e tipos dos slots).
4. `build_tools/vehicle_markers.py`: identifica a build com `ct_client_build` (mecanismo do F6-G3), escolhe o lock, verifica o hash e o contrato antes de patchar. CRLF mantido.
5. `build_tools/validate_build_data.py`: valida todos os locks (build conhecida, `clientBuild` coerente, hashes distintos).
6. `tests/build/test_vehicle_markers_lock.py` (novo, 7 testes).

### Locks por build e compatibilidade #995

| Build | Lock | SHA-256 do filme nativo |
|---|---|---|
| 995 | `flash_source/vehicle_markers/native-lock.json` (inalterado) | 34d92354f1c755313b99fd4e268bb78dc130ece24797a271aece5f0a7346537e |
| 996 | `flash_source/vehicle_markers/native-lock.ct996.json` | 52c5906b04998132efb7a70422999b5dd225d89fb29c49c89d41ba8a59f090b6 |

Seleção e lock #995 preservados textualmente e cobertos por teste. Compatibilidade binária #995 não verificada nesta execução (filme nativo #995 indisponível). O ABC #995 patchado satisfaz o mesmo contrato, por ter classes e assinaturas idênticas às de #996.

### Testes

- Diretos (`PYTHONPATH=tests`): 33 PASS, 2 FAIL. Novos 7 e os 5 existentes de `test_vehicle_markers_patch.py` passam; F6-G2 (9), F6-G3 (5) e `test_compiler_version` (3) passam.
- As 2 falhas são as anteriores (`test_protected_sources…` por `launcher.js`; `test_calculations_patches…` por hash do `build_config.json`, agora `f283710e…`). Não corrigidas; reservadas para a consolidação F6-G5.
- Casos negativos cobertos: hash desconhecido; filme de outra build; build 997; lock de outra build nos dois sentidos; método ausente; método duplicado; slot ausente; assinatura incompatível (parâmetros, tipo de retorno, tipo do slot `model`, retorno do getter); operação incompleta (`patch_marker` sem `onBeforeDispose`).
- Com o filme real: lock #996 aceita o nativo #996; lock #995 recusa-o; um byte alterado é recusado.

### Geração isolada

Executado apenas `vehicle_markers.build` para um diretório em scratchpad (fora das pastas de distribuição), com RABCDAsm de `WoT_Tools/xvm-master/src_build/bin/windows_i686/rabcdasm` indicado explicitamente (a worktree não tem `toolchain.local.json`).

- Output: 827072 bytes, SHA-256 `6eb3e726ae6021078c30a82cbc0b1971977388a3cacd4a09a1e99c6b347fa8d9`.
- Duas execuções produziram o mesmo hash (determinístico).
- Parsing SWF e ABC sem erros; dois DoABC; chamadas injetadas com as contagens esperadas (`render` 7, `restoreIcons` 6, `damage` 1, `clearTransient` 1, `damageEnabled` 1, `nativeSettings` 1, `clear` 1; `receiveStats`, `configure`, `setColorBlind` 1 cada).
- Nada foi instalado nem copiado para `build/`.

### Preservação

- `native-lock.json`, patches e bridges F6-G3, preflight F6-G2 (apenas reutilizado), launcher, Gameface, outros módulos Flash e código Python dos marcadores: não tocados.
- SWF experimentais F4 com os hashes registados: `10449ac1…`, `08002055…`, `28329a4a…`.
- Beta.9: NOT_REVERIFIED. O pacote com hash `22ed6826…` não foi localizado; `build/unified/driftkings.wotmod` do repositório original tem hoje `f0ff0cde…`.

### Limitações e pendências runtime

- Sem execução no CT: carregamento do filme pelo Scaleform, linkage das fontes, callbacks e lifecycle continuam por validar (Fase 7).
- A equivalência #995/#996 baseia-se nos ABC patchados, não nos dois filmes nativos.
- A verificação de contrato cobre os membros que o patch usa em bytecode; os membros lidos dinamicamente pelo helper foram conferidos nesta análise mas não são verificados pelo gerador.
- O caminho do RABCDAsm continua a depender de configuração local da máquina.

### Veredictos

F6-G4 — CT996 VEHICLE MARKERS SWF: PASS (estático e geração isolada)
NATIVE SWF INPUT — VERIFIED
FLASH CONTRACTS — COMPATIBLE_STATIC
CT996 PATCH — PASS
CT995 COMPATIBILITY — PRESERVED (definições; binário #995 não verificado)
HASH SAFETY — PRESERVED
OUTPUT STRUCTURAL VALIDATION — PASS
RUNTIME VALIDATION — PENDING
ORIGINAL BETA.9 — NOT_REVERIFIED
FASE 6 — IN_PROGRESS

F6-G4 — aguarda revisão. Não iniciar F6-G5 nem Fase 7 sem autorização expressa.

## 38. F6-G5 — Consolidação final e preparação da build CT #996

2026-11-13, Europe/Lisbon. Pedido expresso autoriza consolidação dirigida, correção justificada de dois baselines de teste e verificação de prontidão. Não executados: build completa, instalação, arranque do CT, instalação de ferramentas, alterações de código de produção, commits ou operações Git destrutivas. Fase 7 não iniciada.

### Estado Git

Worktree reorganization; branch reorganization/settingslab; HEAD bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3; staging vazio antes e depois. Inicial: 90 entradas (58 M, 3 D, 29 untracked). Final: 91 entradas (59 M, 3 D, 29 untracked). Único ficheiro novo no delta: `tests/fixtures/native_baselines.json` (M), além deste progresso.

### Consolidação F6-G2 / G3 / G4

- Preflight: 9 testes PASS. CT #996 com revisão 2660091 aceite; build desconhecida, revisão errada, fonte incompatível e label legado usado para #996 recusados; identificador legado `2.4.2.5516` preservado em `reference.version`.
- Carrossel: `patch_files['996']` selecionado; 24 operações; input `81ba2baf…`, output `c03f1d98…`; variante #995 inalterada.
- Crew Tooltip: `patch_files['996']` selecionado; 3 operações; input `d4ebef3b…`, output `1d7914a1…`; variante #995 inalterada.
- Marcadores: lock #996 (`52c5906b…`) selecionado; verificação de métodos e assinaturas ativa; output F6-G4 `6eb3e726…` não regenerado; lock #995 inalterado.
- Verificação adicional de leitura, sem gerar ficheiros: os 12 geradores `gameface_patch` aplicam-se em memória aos pacotes do cliente #996 instalado com hash de input e output corretos (carrossel e tooltip pela variante 996; crew_barracks e nove native_document pelo pin histórico, cujos inputs não mudaram). O input do `battleinfo_native` tem o `source_sha256` pinado (`0857328d…`).

### Diagnóstico dos dois baselines

Teste A — `test_native_carousel_catalog::test_protected_sources_and_calculations_are_preserved`.
- Objetivo: garantir que fontes protegidas não mudam sem registo, contra o baseline `native_crew`.
- Referência: `files['mod/res/gui/gameface/mods/driftkings/launcher/launcher.js']` = `39480b06…`, igual ao ficheiro em HEAD.
- Delta atual contra HEAD: duas linhas. `click()` passa a ignorar o clique quando o botão está desativado; o ícone passa de `gui/maps/icons/driftkings/small.png` para `launcher/launcher_dk.svg`. São as alterações do launcher nativo da Fase 5. Nenhuma outra diferença.
- Decisão: atualizar a referência para `82efc1d4…`.

Teste B — `test_native_crew_catalog::test_calculations_patches_and_existing_integrations_preserved` (e a mesma verificação no teste A).
- Objetivo: garantir que o `build_config.json`, sem `battleinfo_native` e sem `native_document_*`, não muda sem registo.
- Referência: `build_config` = `0a4ed486…` nos baselines `native_crew` e `native_marks`, igual ao ficheiro em HEAD.
- Delta atual contra HEAD: `reference.ct_builds` (F6-G2); `carousel_bridge` e `crew_tooltip_bridge` de `patch_file` para `patch_files` (F6-G3); `vehicle_markers_flash` de `lock` para `locks` (F6-G4); nove geradores `native_document_*` (já excluídos pelo teste). Revertendo exatamente os três deltas F6, o hash volta a `0a4ed486…`. Nenhuma diferença por explicar.
- Decisão: atualizar a referência para `f283710e…`.

### Alterações à fixture

Só `tests/fixtures/native_baselines.json`:
- `baselines.native_crew.files[launcher.js]`: `39480b06…` → `82efc1d4…`.
- `baselines.native_crew.build_config` e `baselines.native_marks.build_config`: `0a4ed486…` → `f283710e…`.
- Novo bloco `approved_revisions` com o hash histórico, o hash aprovado, a data e o motivo de cada uma das duas revisões. O bloco é só registo; nenhum teste o lê.

Não foram removidas assertions nem ficheiros das listas protegidas; os hashes continuam fixados na fixture e não são calculados a partir do ficheiro sob teste. Código de teste e de suporte não alterado.

Adulterações verificadas depois da atualização, todas recusadas: `launcher.js` com um comentário acrescentado; `launcher.js` com a guarda `disabled` alterada; `build_config` com build 997 acrescentada; caminho do patch 996 trocado; lock 995 removido.

### Testes

- Dirigidos (`PYTHONPATH=tests`): 35 PASS, 0 FAIL em `test_native_carousel_catalog`, `test_native_crew_catalog`, `test_client_preflight`, `test_gameface_patch_variants`, `test_vehicle_markers_lock`, `test_vehicle_markers_patch`, `test_compiler_version`.
- Outros testes que leem a mesma fixture, corridos para confirmar que a atualização não os afetou: 15 PASS, 3 FAIL. As 3 falhas não vêm desta alteração:
  - `test_native_hangar_marks_catalog::test_validated_clock_and_unrelated_marks_are_byte_preserved`: `mod/res/gui/gameface/mods/driftkings/shared/marks_panel.js` difere do baseline (`fc2e10b7…` contra `042a35d9…`). O ficheiro já estava modificado antes da Fase 6. É uma terceira falha de baseline, não identificada antes e fora da autorização desta fase; não foi tocada.
  - `test_native_results_source` (2 testes): `acorn` não está instalado em `build_tools/javascript/node_modules` desta worktree.

### Toolchain

Encontrado por descoberta automática: Python 2.7 (`F:/Python27`), hg, Flex SDK e `mxmlc.jar`, `playerglobal.swc`, Java 8, Roslyn `csc`. Node.js v20.19.2 e npm 11.12.1 no PATH. Python 3.14 para o pipeline.

Sem configuração nesta worktree (não existe `build_data/toolchain.local.json`): `rabcdasm_home`, `game_root`, `reference_root`. O pipeline aceita os três por argumento (`--rabcdasm-home`, `--game-root`, `--reference-root`) ou por variável de ambiente (`DK_RABCDASM_HOME`, `DK_GAME_ROOT`, `DK_REFERENCE_ROOT`), por isso não é preciso criar ficheiro no repositório. Valores verificados: RABCDAsm em `E:/Wot_Mods_/Drift_Kings_ModPack/WoT_Tools/xvm-master/src_build/bin/windows_i686/rabcdasm`; cliente em `C:/Games/World_of_Tanks_CT`; fontes em `E:/Wot_Mods_/Drift_Kings_ModPack/Driftkings_WoT_Sources/wot_src_CT`.

Em falta: `acorn` 8.19.0 em `build_tools/javascript/node_modules` da worktree (a pasta `node_modules` não existe). O gerador `battleinfo_native` recusa sem ele. O repositório original tem `acorn` 8.19.0 instalado, mas o pipeline só lê a pasta da própria raiz. Comando indicado pelo próprio pipeline: `npm --prefix build_tools/javascript ci --ignore-scripts`. Não foi executado (instalação não autorizada).

Não verificado nesta fase (sem compilar): compilação Flash com as bibliotecas SWC, compilação C# e empacotamento.

### Estado #995

Patches #995 do carrossel e do tooltip, lock #995 dos marcadores e contrato legado do preflight presentes e inalterados. CT995 DEFINITIONS — PRESERVED. CT995 BINARY VALIDATION — NOT_EXECUTED (inputs #995 indisponíveis).

### Beta.9

Procura dirigida. `C:/Games/World_of_Tanks_CT/mods/2.4.2.0 Common Test/driftkings.wotmod` tem SHA-256 `22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9`, igual à referência. É a cópia instalada no CT. `build/unified/driftkings.wotmod` do repositório original e do snapshot de preservação têm `f0ff0cde…`, ou seja, são outro pacote.

### Readiness da build

- Preflight, seleção dos patches #996 e locks: prontos.
- Inputs dos geradores Gameface e do BattleInfo: conferem com o cliente instalado.
- Destino experimental: `--isolated-output` escreve em `build/experiments/<run-id>/output`, sem tocar em `build/unified` nem no pacote publicado.
- Impedimento concreto: `acorn` não instalado na worktree. Até ser instalado, a geração pára no `battleinfo_native`.
- Limitações documentadas: três caminhos locais a passar por argumento ou ambiente; falha de baseline de `marks_panel.js` por decidir.

### Pendências runtime para a Fase 7

Transportadas sem alteração: inicialização e limpeza Gameface/Wulf; host neutro; carrossel; Crew Tooltip; SWF dos marcadores; configurações; launcher SVG; ModsListAPI/OpenWG; callbacks Python; lifecycle Flash; segunda batalha; áudio; performance; compatibilidade geral no cliente CT #996. Trabalhos WGMods e Fog Remover continuam adiados.

### Veredictos

F6-G5 — CONSOLIDATION PARTIAL (consolidação e dois baselines concluídos; um pré-requisito de toolchain em falta)
BASELINE TESTS — PASS (os dois autorizados; terceira falha `marks_panel.js` encontrada e não tratada)
CT996 BUILD CONFIGURATION — READY
TOOLCHAIN — PARTIAL (acorn em falta na worktree)
HASH SAFETY — PRESERVED
CT995 DEFINITIONS — PRESERVED
CT995 BINARY VALIDATION — NOT_EXECUTED
ORIGINAL BETA.9 — PRESERVED (cópia instalada no CT)
BUILD READINESS — BLOCKED_BY_CONFIRMED_ISSUE (acorn; resolve-se com um comando)
RUNTIME VALIDATION — PENDING
FASE 6 — VALIDATION_PENDING (falta apenas o pré-requisito de toolchain)

Requisitos para iniciar a Fase 7: instalar `acorn` na worktree com o comando acima; passar `--game-root`, `--reference-root` e `--rabcdasm-home`; usar `--isolated-output`; decidir o baseline de `marks_panel.js`. Não iniciar a build sem autorização expressa.

## 39. F6-G5.1 — Desbloqueio final da toolchain e encerramento local da Fase 6

2026-11-13, Europe/Lisbon. Pedido expresso autoriza instalar as dependências JavaScript pelo lockfile, resolver de forma justificada o baseline de `marks_panel.js`, verificar a toolchain e encerrar a Fase 6 se os critérios forem cumpridos. Não executados: build, compilação SWF, instalação no cliente, arranque do CT, alterações de produção, commits ou operações Git destrutivas. Fase 7 não iniciada.

### Estado Git

Worktree reorganization; branch reorganization/settingslab; HEAD bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3; staging vazio antes e depois. Inicial e final: 91 entradas (59 M, 3 D, 29 untracked). Alterados nesta fase: `tests/fixtures/native_baselines.json` (já M) e este progresso. `build_tools/javascript/node_modules` está ignorado por `.gitignore` (`node_modules/`) e não criou caminhos Git.

### Acorn

- Antes: `package.json` declara `acorn` 8.19.0; `package-lock.json` (lockfileVersion 3, 82 pacotes) fixa `acorn` 8.19.0 com integridade; dependências de raiz iguais nos dois ficheiros; nenhum pacote com script de instalação. Node v20.19.2, npm 11.12.1.
- Executado na raiz da worktree: `npm --prefix build_tools/javascript ci --ignore-scripts`. Concluído sem erro; o npm emitiu apenas o aviso habitual de `npm audit`, sem ação tomada.
- Depois: `node_modules/acorn/package.json` indica 8.19.0; `require_battleinfo_toolchain` do pipeline resolve Node e o parser; `package.json` e `package-lock.json` com os mesmos SHA-256 de antes; contagem Git inalterada.

### BattleInfo

`tests/build/test_native_results_source.py`: 8 PASS, incluindo os dois antes bloqueados (`test_patch_subprocess_stays_inside_isolated_output`, `test_supported_buffer_is_deterministic_and_hash_pinned`). O parsing JavaScript correu. Nenhum output de produção escrito; BattleInfo e geradores não alterados.

### Baseline de `marks_panel.js`

- Teste: `test_native_hangar_marks_catalog::test_validated_clock_and_unrelated_marks_are_byte_preserved`, baseline `native_clock` (commit 57881e7b).
- Hash esperado: `fc2e10b74d5899c98551a355e90b975436d6f84ba83f9aa5199bcbb4a82f60af`, igual ao ficheiro em HEAD e no commit do baseline.
- Hash atual: `042a35d9ff65c67651fd242e4819d05311ff638204fe692a0c0de1da5edd9b93`.
- Diff contra HEAD: 32 inserções, 8 remoções, todas dentro de `connect`:
  - sétimo argumento opcional `lifecycle`;
  - objeto `bridge` como owner, comparado por identidade (`window[owner] === bridge`) em vez de `owner.dispose === dispose`;
  - `lifecycle.dispose()` chamado no descarte;
  - `place()` e `cancelPosition()`: segunda medição em `requestAnimationFrame` só com `afterLayout`, com guardas de geração, owner, subview/modelo e payload, e cancelamento em ocultação e descarte;
  - `unload` registado quando o owner é criado, antes de `engine.whenReady`.
- Proveniência: secção 14, «Fase 3 — G2: cleanup JavaScript», que lista `shared/marks_panel.js` entre os quatro ficheiros alterados e descreve cada um destes pontos (owner de identidade estável; cleanup integrado; unload antes da readiness; frames no owner com as mesmas guardas; sétimo argumento opcional). G2 foi aceite pelo responsável (secção 15). Corresponde às propostas 1 e 2 da secção de achados da Fase 3.
- Consumidores coerentes com o registo: `reticle_text.js`, `screen_text.js` e `vehicle_health.js` passam `{afterLayout: true}`; `marks.js` e `main_gun.js` mantêm os seis argumentos.
- Nenhuma alteração sem proveniência. Decisão: baseline aprovado.

### Alterações à fixture

Só `tests/fixtures/native_baselines.json`:
- `baselines.native_clock.files[shared/marks_panel.js]`: `fc2e10b7…` → `042a35d9…`.
- Nova entrada em `approved_revisions` com o hash histórico, o aprovado, a data e o motivo.

Restantes baselines, assertions e código de teste inalterados. O hash aprovado é um valor fixo na fixture.

### Integridade e adulteração

- Testes que leem a fixture: 23 PASS, 0 FAIL (`test_native_hangar_marks_catalog`, `test_native_carousel_catalog`, `test_native_crew_catalog`, `test_native_document_catalog`, `test_native_results_source`, `tests/runtime/lobby/test_native_carousel.py`).
- Adulterações em memória sobre o conteúdo de `marks_panel.js`, sem tocar no ficheiro real, todas recusadas pela referência fixa: comentário acrescentado; comparação de owner alterada; listener de `unload` removido.
- Testes F6-G2/G3/G4 não repetidos: nenhum ficheiro que cobrem mudou desde F6-G5 (35 PASS).

### Toolchain

`require_tools` do pipeline passa com os três caminhos externos fornecidos como overrides:

| Ferramenta | Caminho |
|---|---|
| Python 2.7 | `F:\Python27\python.exe` |
| hg | `%LOCALAPPDATA%\Atlassian\SourceTree\hg_local\hg.exe` |
| Flex SDK / mxmlc | `E:\Wot_Mods_\Drift_Kings_ModPack\Programas\Flex` (`lib\mxmlc.jar`, `frameworks\libs\framework.swc`) |
| playerglobal | Adobe Animate 2024, FP32.0 |
| Java 8 | `C:\Program Files\Java\jre1.8.0_491\bin\java.exe` |
| C# (Roslyn) | Visual Studio 2022 BuildTools |
| Node.js / npm / acorn | v20.19.2 / 11.12.1 / 8.19.0 |
| Python 3 | 3.14 (pipeline e testes) |

Empacotamento: feito pelo próprio pipeline em Python (ZIP), sem executável externo. Nada instalado além do `npm ci` autorizado. Sem compilação: a execução real de mxmlc, csc e do worker Python 2.7 só será exercida na build.

### Caminhos externos

Sem `build_data/toolchain.local.json` e sem variáveis `DK_*` definidas; nada escrito em ficheiros versionados. Valores confirmados para passar por argumento:

- `--rabcdasm-home E:/Wot_Mods_/Drift_Kings_ModPack/WoT_Tools/xvm-master/src_build/bin/windows_i686/rabcdasm` — contém `abcexport.exe`, `rabcdasm.exe`, `rabcasm.exe`, `abcreplace.exe`.
- `--game-root C:/Games/World_of_Tanks_CT` — `version.xml`: `v.2.4.2.0 Common Test #996`, client 2660091, realm CT.
- `--reference-root E:/Wot_Mods_/Drift_Kings_ModPack/Driftkings_WoT_Sources/wot_src_CT` — `.version_name` e `manifest.json` #996.

`check_client` com estes três caminhos devolve `CT`. O `toolchain.local.json` do repositório original aponta para o cliente e as fontes EU; não é lido pela worktree e não deve ser copiado. Nenhuma referência à build CT anterior nos caminhos usados.

### Consolidação dos quatro bloqueios

Resultados reutilizados sem nova execução: preflight F6-G2 (9 testes); carrossel 24/24 e Crew Tooltip 3/3 com hashes exatos e seleção #995/#996 (F6-G3); SWF dos marcadores com lock #996, contratos ABC e output determinístico (F6-G4); 12 geradores Gameface e input do BattleInfo conferidos contra o cliente instalado (F6-G5).

### Beta.9

`C:/Games/World_of_Tanks_CT/mods/2.4.2.0 Common Test/driftkings.wotmod` recalculado: `22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9`, igual à referência. Não modificado; nada copiado para o cliente.

### Readiness da build experimental

- Dependências disponíveis; caminhos resolvidos; identidade CT #996 reconhecida; patches e lock #996 selecionados.
- `--isolated-output` escreve em `build/experiments/<run-id>/output`; o identificador combina data/hora UTC e um sufixo aleatório, por isso não sobrescreve execuções anteriores nem `build/unified`, e não aponta para o pacote instalado no CT.
- Nenhum bloqueio concreto conhecido. Por exercer só na build: compilação Flash/C#, worker Python 2.7 e empacotamento.

### Veredictos

F6-G5.1 — FINAL TOOLCHAIN UNBLOCK: PASS
ACORN — INSTALLED
BATTLEINFO TESTS — PASS
MARKS PANEL BASELINE — APPROVED
HASH SAFETY — PRESERVED
TOOLCHAIN — READY
CT996 BUILD CONFIGURATION — READY
ORIGINAL BETA.9 — PRESERVED
BUILD READINESS — READY_FOR_EXPERIMENTAL_BUILD
FASE 6 — COMPLETE (LOCAL VALIDATION; CT PENDING)

Validação runtime continua pendente. Próxima autorização: Fase 7 — primeira build experimental para o Common Test #996. Não iniciar a compilação sem autorização expressa.

## 40. F7-G1 — Primeira build experimental e instalação controlada no CT #996

2026-11-13, Europe/Lisbon. Pedido expresso autoriza gerar a build experimental isolada, validar artefactos, fazer backup da beta.9, instalar no cliente CT #996 e preparar rollback. Início da Fase 7. Resultado desta execução: a build falhou num gerador e a execução parou antes de qualquer backup, cópia ou alteração no cliente, conforme a regra de tratamento de erros.

### Estado Git

Worktree reorganization; branch reorganization/settingslab; HEAD bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3; staging vazio antes e depois; 91 entradas antes e depois (59 M, 3 D, 29 untracked). `build/` está ignorado pelo Git. Único ficheiro alterado: este progresso. Sem commits.

### Identidade e pré-condições

- Cliente `C:/Games/World_of_Tanks_CT`: `v.2.4.2.0 Common Test #996`, client 2660091, realm CT. Fontes `wot_src_CT` #996. Nenhum processo World of Tanks em execução.
- Toolchain resolvida pelo pipeline com os três caminhos externos por argumento; acorn 8.19.0 presente.
- `--plan` antes da build: versão empacotada 0.1.8-beta.10, versão de origem 0.1.8-beta.1, canal beta, modo debug, 308 módulos Python, 335 assets, 54 defaults, output isolado.
- Versão: a beta.9 instalada declara 0.1.8-beta.9 no `meta.xml`. Seguindo a sequência dos pacotes de teste locais, foi usado `--version 0.1.8-beta.10 --keep-source-version`, que altera só a versão dentro do pacote; `release.json` e `VERSION` de origem ficam em 0.1.8-beta.1.

### Comando

Executado na raiz da worktree:

`python build_tools/compiler.py --isolated-output --keep-source-version --version 0.1.8-beta.10 --mode debug --game-root C:/Games/World_of_Tanks_CT --reference-root E:/Wot_Mods_/Drift_Kings_ModPack/Driftkings_WoT_Sources/wot_src_CT --rabcdasm-home E:/Wot_Mods_/Drift_Kings_ModPack/WoT_Tools/xvm-master/src_build/bin/windows_i686/rabcdasm`

Run ID: `20261113T204554Z-16125d84`. Início 20:45:52Z, fim 20:46:05Z (13 s), código de saída 1.

### Resultado da compilação — BUILD_FAILED

Concluído sem erro, por esta ordem: compilação Python 2.7 (308 módulos); `battle_flash`; `battleinfo_native`; `carousel_bridge`; `crew_barracks_bridge`; `crew_tooltip_bridge`; `fog_package_helper`; nove `native_document_*`; `panels_flash`; `updater_helper`.

Falhou em `vehicle_markers_flash`, fase `generate`:

`ValueError: Isolated marker workspace too deep for safe Windows paths` (`build_tools/vehicle_markers.py`, `marker_workspace`).

Causa: a proteção calcula o caminho projetado do workspace isolado dos marcadores mais 1 + `DISASSEMBLY_BUDGET` (120) + `PATH_MARGIN` (8) e recusa se chegar a 260. Nesta worktree o workspace `…\Driftkings_SettingsLab_reorganization\build\experiments\<run-id>\workspace\tmp\vm-xxxxxxxx` tem 140 caracteres: 140 + 129 = 269. No repositório original o mesmo caminho tem 125 caracteres (254), por isso a proteção nunca disparou lá. A diferença são os 15 caracteres de `_reorganization`. A árvore de desmontagem #996 precisa de 107 caracteres (97 do ficheiro mais fundo mais `markers-0/`), igual ao valor documentado no código.

Não é um problema de compatibilidade #996. A geração isolada de F6-G4 não passou por esta proteção porque chamou `vehicle_markers.build` fora de um output isolado, num diretório temporário próprio; foi por isso que o impedimento não apareceu antes.

Não existe opção de configuração para mudar a raiz de `build/experiments`: o caminho é fixo em `build_tools/isolated_output.py`.

### Artefactos

Nenhum pacote produzido. `build/experiments/20261113T204554Z-16125d84/output` está vazio. A pasta da execução ficou com `diagnostics/` (`error.json`, `inventory.json`, `state.json`), `manifests/` e `workspace/` (338 ficheiros no total), conservada como evidência e não reutilizável como build. Experimentos F4 e `build/unified` não tocados.

### Instalação, backup e cliente

Não executados. Beta.9 instalada reconfirmada depois da falha: `22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9`. Nenhum ficheiro copiado, removido ou alterado em `C:/Games/World_of_Tanks_CT`.

Inventário de leitura feito antes da build, para a próxima tentativa: 97 ficheiros em `mods` e `res_mods`. Em `mods/2.4.2.0 Common Test`: `driftkings.wotmod`, `Driftkings.RemoveFog.wotmod`, `Core/` (`izeberg.modssettingsapi_1.7.1`, `me.poliroid.modslistapi_1.8.0`, `net.openwg.gameface_1.2.2`) e `SteelFox/` (terceiros). Em `mods/configs/driftkings`: `load.json`, `.settings`, `cache/` e `default/` (52 ficheiros). `res_mods/2.4.2.0 Common Test`: `audioww/audio_mods.xml`, `engine_config.xml`, `readme.txt`.

### Opções para desbloquear (nenhuma aplicada)

1. Encurtar o caminho da worktree em pelo menos 10 caracteres (por exemplo mover a worktree para um nome mais curto). Não altera código nem a proteção; exige autorização para mover a worktree e atualizar os caminhos documentados.
2. Reduzir `DISASSEMBLY_BUDGET` de 120 para 110 em `build_tools/vehicle_markers.py`. A árvore real precisa de 107; ficaria 140 + 1 + 110 + 8 = 259, um carácter abaixo do limite. É uma alteração de ferramenta de build que reduz a folga da proteção.
3. Tornar configurável a raiz do output isolado. Alteração maior em `build_tools/isolated_output.py`; não recomendada para esta fase.

### Pendências runtime

Inalteradas: SVG do launcher via `coui`; estados CSS; carrossel e Crew Tooltip; host neutro Gameface; SWF dos marcadores; lifecycle Wulf; callbacks Flash; minimap; Sixth Sense; segunda batalha; ModsListAPI; OpenWG; áudio; performance; problemas conhecidos da beta.9.

### Veredictos

F7-G1 — EXPERIMENTAL BUILD: FAIL (bloqueio de comprimento de caminho no gerador de marcadores)
CT996 TARGET — VERIFIED
BUILD OUTPUT — FAILED
PACKAGE INTEGRITY — não aplicável (nenhum pacote)
ORIGINAL BETA.9 BACKUP — não executado (beta.9 instalada intacta, hash conferido)
INSTALLATION — NOT_EXECUTED
INSTALLED HASHES — NOT_EXECUTED
USER CONFIGURATIONS — PRESERVED (cliente não tocado)
ROLLBACK — não necessário (nada instalado)
RUNTIME VALIDATION — NOT_EXECUTED
FASE 7 — IN_PROGRESS

F7-G1 parado na etapa de compilação. Aguarda decisão sobre a opção de desbloqueio.

## 41. F7-G1.1 — Correção do workspace RABCDAsm, build experimental e instalação no CT #996

2026-11-13, Europe/Lisbon. Pedido expresso autoriza corrigir apenas o comprimento do caminho do workspace temporário do gerador dos marcadores, executar a build experimental isolada, validar artefactos, fazer backup e instalar no cliente CT #996. Jogo não iniciado; nenhuma correção runtime; F7-G2 não iniciada.

### Estado Git

Worktree reorganization; branch reorganization/settingslab; HEAD bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3; staging vazio antes e depois; sem commits. Inicial: 91 entradas (59 M, 3 D, 29 untracked). Final: 93 entradas (60 M, 3 D, 30 untracked). Delta: `build_tools/isolated_output.py` (M), `build_tools/vehicle_markers.py` (já M, alteração local), `tests/build/test_marker_short_workspace.py` (novo) e este progresso. `build/` ignorado pelo Git.

### Causa e correção

Causa (secção 40): o workspace dos marcadores dentro da execução isolada tinha 140 caracteres; com a reserva de 129 dava 269, acima do limite 260.

Inspeção: o workspace é criado em `marker_workspace` (`build_tools/vehicle_markers.py`) dentro de `<run>/workspace/tmp` porque a guarda de escrita de `IsolatedOutput` só autoriza escritas Python dentro da pasta da execução. As ferramentas RABCDAsm e mxmlc correm como subprocessos com `cwd` no workspace e recebem caminhos absolutos; não exigem que o workspace esteja dentro do output. O SWF final é escrito pelo próprio pipeline no destino da execução, por isso o workspace pode ficar fora.

Correção:
- `build_tools/isolated_output.py`: `IsolatedOutput.adopt(path, protected)` cria e passa a possuir um único diretório externo, e `release(path)` remove esse diretório e só esse. `check()` aceita escritas dentro do diretório adotado, verificando a identidade (dispositivo e inode) em cada operação.
- `build_tools/vehicle_markers.py`: `too_deep()` (a mesma fórmula e o mesmo limite 260), `short_workspace_root()` e `short_marker_workspace()`. `marker_workspace` só recorre ao workspace curto quando o caminho dentro da execução excede o orçamento e quando a build lhe indica uma raiz curta; sem isso mantém o erro anterior. `build()` passa a raiz curta e os diretórios protegidos (cliente, fontes CT, RABCDAsm).

`DISASSEMBLY_BUDGET` (120), `PATH_MARGIN` (8) e o limite 260 não foram alterados. Repositórios com caminho curto continuam a usar o workspace dentro da execução, sem mudança de comportamento.

### Workspace temporário e segurança

- Localização: `<drive do repositório>\DK_TMP\vm_<run-id>`, ou a raiz indicada em `DK_MARKER_WORKSPACE`. Nesta execução: `E:\DK_TMP\vm_20261113T205332Z-7318b280` (38 caracteres; 38 + 129 = 167).
- Pertence a uma execução: o nome inclui o run ID; o diretório é criado em modo exclusivo e nunca reutilizado (um diretório já existente faz falhar a build sem lhe tocar); cada execução só pode adotar um.
- Caminho validado antes de criar: absoluto, sem `..`, sem symlinks nem junctions em nenhum componente, fora do repositório, do cliente, das fontes CT e do RABCDAsm, e dentro do orçamento de caminho.
- Escritas e remoção limitadas ao diretório adotado; o resto de `DK_TMP` e qualquer outro caminho fora da execução continuam recusados pela guarda.
- Diagnóstico: o caminho usado fica em `<run>/workspace/marker_workspace.txt` e no log da build.
- Limpeza: em sucesso e em falha, só o diretório da execução é removido; uma falha de limpeza é propagada. No fim desta execução `E:\DK_TMP` ficou vazio (a pasta base permanece).

### Testes dirigidos

`tests/build/test_marker_short_workspace.py` (11 testes): orçamento e limite inalterados; raiz curta por omissão e por variável; execução funda usa o workspace curto e remove só esse; execução curta mantém o workspace interno; sem raiz curta ou com raiz curta demasiado funda continua a recusar; execuções diferentes não colidem; diretório existente não é reutilizado; falha de criação comunicada; localizações protegidas e o repositório recusados; falha no corpo limpa e propaga; segunda adoção e libertação alheia recusadas; junction na raiz curta recusada.

Resultado com os testes vizinhos (`test_windows_cleanup`, `test_isolated_output`, `test_vehicle_markers_lock`, `test_vehicle_markers_patch`, `test_native_results_source`): 69 PASS, 1 ignorado, 0 FAIL.

### Build

Comando, igual ao da tentativa anterior:

`python build_tools/compiler.py --isolated-output --keep-source-version --version 0.1.8-beta.10 --mode debug --game-root C:/Games/World_of_Tanks_CT --reference-root E:/Wot_Mods_/Drift_Kings_ModPack/Driftkings_WoT_Sources/wot_src_CT --rabcdasm-home E:/Wot_Mods_/Drift_Kings_ModPack/WoT_Tools/xvm-master/src_build/bin/windows_i686/rabcdasm`

Run ID `20261113T205332Z-7318b280` (diferente da tentativa falhada, cuja pasta não foi reutilizada). Início 20:53:30Z, fim 20:53:48Z, código de saída 0, `Build complete`, estado `complete`, `publishable: false`. Sem warnings nem erros no log. Python 2.7: 308 módulos. 19 geradores concluídos, incluindo `vehicle_markers_flash` e `windows_files_helper`.

Artefactos em `build/experiments/20261113T205332Z-7318b280/output`:

| Ficheiro | Bytes | SHA-256 |
|---|---|---|
| `driftkings.wotmod` | 14517048 | 2e169b29db91f4d029101de6997a4c17436748fc4483713986cff989ce4337c0 |
| `Driftkings-0.1.8-beta.10-WoT-2.4.2.0.zip` | 8802213 | 2a25d299f40f664f1d0e5ae550b3ceb8eebdb69a9cb28c8f2dc01e6a27d90e6c |
| `Driftkings-defaults.zip` | 29413 | a828f31bc10bb23ff17729b577c2958d352ba3db89902318ac7ffb05f3ec2a40 |
| `dependencies/me.poliroid.modslistapi_1.8.0.wotmod` | 167079 | c6e4a1d9476b0195c3b4fab392cf5d68c00f1d02fd79e29bd7424ebda88b498c |
| `dependencies/net.openwg.gameface_1.2.2.wotmod` | 48445 | 2bb65f28663e3ab34b5a1102a1bbd1f6e17a65e1f6a898a8645c4ab732b50184 |
| `modpack.json` | 12974 | 64b750010d3946ad676f54dfa4fb98dd358c64a35a476df8bb908ab8de45cf60 |
| `release.json` | 14871 | 972846c381d4aa307a7e9d67852665bbeef315fdbd19b52fba43c1037e07bccc |
| `build-report.json` | 114260 | deb2a7d94c510d4ad5c42769d7728113ddf60c1e3aaed63d8d27a58b09640622 |
| `SHA256SUMS.txt` | 751 | 2b19058d0feeb8f1f21dc50322ea45a15ed61e792933ed0cd150591fa8b869c5 |

### Validação do pacote e recursos CT #996

- `driftkings.wotmod`: ZIP íntegro, 644 entradas, sem compressão; `meta.xml` com versão 0.1.8-beta.10; 308 `.pyc`.
- Carrossel `mono/hangar/main/bundle.js`: `c03f1d98…`, igual ao output pinado #996.
- Crew Tooltip `mono/hangar/tooltips/bundle.js`: `1d7914a1…`, igual ao output pinado #996.
- Marcadores `gui/flash/battleVehicleMarkersApp.swf`: `6eb3e726…`, igual ao da geração isolada F6-G4.
- BattleInfo `post_battle/random/bundle.js`: `fdb10d97…`, igual ao `output_sha256` pinado.
- `driftkingsbattle.swf`: `28329a4a…`, igual ao experimento F4-G2.
- Launcher: `launcher.js`, `launcher.css` e `launcher_dk.svg` incluídos; o JS referencia `launcher/launcher_dk.svg` e mantém `model.onOpen()`.
- Recursos R: 23 ficheiros em `gui/gen_resources`, incluindo `driftkings.battle_hud.json`; `battle_hud/window.html` e `component_list.pyc` incluídos.
- Contra a beta.9 instalada (641 entradas): nenhuma entrada removida; três acrescentadas (`battle_hud/window.html`, `launcher/launcher_dk.svg`, `gen_resources/driftkings.battle_hud.json`).
- Dependências do pacote: ModsListAPI 1.8.0 e OpenWG Gameface 1.2.2, com os hashes pinados.

Não verificado nesta fase: funcionamento em jogo de qualquer destes recursos.

### Beta.9 e backup

- Antes da instalação: jogo encerrado (nenhum processo `WorldOfTanks.exe`); `driftkings.wotmod` instalado com `22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9`.
- Backup novo, fora do cliente, em pasta criada em modo exclusivo: `E:\Wot_Mods_\Drift_Kings_ModPack\Driftkings_Preservation\f7-g1.1-20261113T205332Z-7318b280\driftkings.wotmod.beta9` (14506766 bytes), SHA-256 igual. Na mesma pasta: `pre-install-manifest.json` (hash e tamanho dos 97 ficheiros de `mods` e `res_mods`) e `install-record.json`. O snapshot `phase0` não foi tocado.

### Inventário pré-instalação

97 ficheiros, como na inspeção anterior. Em `mods/2.4.2.0 Common Test`: `driftkings.wotmod` (beta.9), `Driftkings.RemoveFog.wotmod` (`37fa5ad4…`), `Core/` com `izeberg.modssettingsapi_1.7.1`, `me.poliroid.modslistapi_1.8.0` e `net.openwg.gameface_1.2.2`, e `SteelFox/` com dois mods de terceiros. As duas dependências instaladas em `Core/` têm exatamente os hashes das dependências da build, por isso não foram copiadas.

Defaults: o pacote traz 54 ficheiros com política `missing_only`. No cliente existem 53 (todos diferentes dos do pacote e deixados como estão) e falta um, `mods/configs/driftkings/default/minimap_enhancements.json`; o cliente tem a pasta `default/minimap_enhancements/` com 4 ficheiros. Esse ficheiro não foi acrescentado, para não alterar a configuração existente sem decisão; fica como ponto a observar em F7-G2.

### Instalação e verificação

Operação única: `build/experiments/20261113T205332Z-7318b280/output/driftkings.wotmod` copiado para `C:\Games\World_of_Tanks_CT\mods\2.4.2.0 Common Test\driftkings.wotmod`, substituindo a beta.9.

Depois da cópia: SHA-256 instalado `2e169b29db91f4d029101de6997a4c17436748fc4483713986cff989ce4337c0` (14517048 bytes), igual ao output. Comparação do inventário completo antes e depois: muda apenas esse ficheiro; 97 ficheiros antes e depois; nada acrescentado nem removido. `Driftkings.RemoveFog.wotmod`, `Core/`, `SteelFox/`, `mods/configs` e `res_mods` com os mesmos hashes. Fog Remover não manipulado. Cliente EU não tocado.

### Rollback

Não executado. Com o jogo encerrado, copiar `E:\Wot_Mods_\Drift_Kings_ModPack\Driftkings_Preservation\f7-g1.1-20261113T205332Z-7318b280\driftkings.wotmod.beta9` para `C:\Games\World_of_Tanks_CT\mods\2.4.2.0 Common Test\driftkings.wotmod` e confirmar o SHA-256 `22ed6826…97e9`. Não há ficheiros novos a remover nem outros a restaurar. O backup não deve ser apagado.

### Pendências runtime

Inalteradas e por validar em F7-G2: SVG do launcher via `coui`; estados CSS; carrossel e Crew Tooltip; host neutro Gameface; SWF dos marcadores; lifecycle Wulf; callbacks Flash; minimap (incluindo o default em falta); Sixth Sense; segunda batalha; ModsListAPI; OpenWG; áudio; performance; problemas conhecidos da beta.9. O updater do mod não foi avaliado contra a versão 0.1.8-beta.10.

### Veredictos

F7-G1.1 — WORKSPACE FIX: PASS
WINDOWS PATH SAFETY — PRESERVED
EXPERIMENTAL BUILD — PASS
CT996 PACKAGE — COMPLETE
ORIGINAL BETA.9 BACKUP — VERIFIED
INSTALLATION — SUCCESS
INSTALLED HASHES — VERIFIED
USER CONFIGURATIONS — PRESERVED
ROLLBACK — READY
RUNTIME VALIDATION — NOT_EXECUTED
FASE 7 — IN_PROGRESS

Próxima etapa: F7-G2 — validação funcional no Common Test #996. Não iniciada.

## 42. F7-G3 — Consolidação runtime e prontidão para integração

2026-11-13, Europe/Lisbon. Pedido expresso F7-G3 autoriza exclusivamente consolidação
Fase7, verificação Git em leitura e relatório de prontidão. Não autoriza código,
correções, builds, instalações, testes novos, commits, push, PR ou integração.
F7-G3 VALIDATION_PENDING (entregável de consolidação); Fase7 IN_PROGRESS.
F7-G4/F7-G5 não iniciados. O registo F7-G1.1 é histórico quanto a runtime NOT_EXECUTED:
a execução funcional posterior é comunicada expressamente pelo responsável neste pedido.

### Ambiente, artefacto e níveis de evidência

Cliente lido nesta execução: C:/Games/World_of_Tanks_CT/version.xml, v.2.4.2.0 Common
Test #996, revisão2660091, realm CT. Worktree exclusiva reorganization/settingslab,
HEAD bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3. Beta.10 experimental, sem alteração
VERSION/release.json ou preparação de publicação estável.

Evidência independente desta execução: Git, cliente version.xml, hashes build/instalação/
backup e registos de instalação. Evidência funcional: capturas/logs/testes anteriores
relatados e confirmação expressa do utilizador no pedido F7-G3. As capturas mencionadas
não foram inspecionadas novamente aqui; não se presume disponibilidade de anexos no disco.

C:/Games/World_of_Tanks_CT/game.log existe com ZERO bytes. Não encontradas outras logs
runtime na localização habitual consultada; logs do experimento em workspace/logs são
de BUILD, não das duas batalhas. Não usados como prova de funcionamento. Relatórios
anteriores indicam ausência de tracebacks/falhas de inicialização; nesta execução isso
não pôde ser revalidado independentemente: PYTHON TRACEBACKS — NOT_VERIFIED (local).
Não confundir esta lacuna documental com traceback encontrado ou regressão comprovada.
Nenhuma cópia integral de log/token foi criada no repositório.

### Garagem e configurações — confirmação comunicada

| Componente | Evidência comunicada | Conclusão delimitada |
|---|---|---|
| Clock nativo | Presença visual | Funcionamento observado na garagem |
| Hangar Marks of Excellence | Presença visual | Integração observada; não prova todos os cálculos |
| Vehicle Carousel | Presença visual e teste funcional geral | Bridge reorganizado observado |
| Crew Progression | Presença visual | Apresentação observada |
| Tooltips tripulação | Presença visual | Tooltip/integração observados |
| Launcher Driftkings | Presença visual/funcional | Acesso ao painel observado |
| Settings Window | Abertura correta comunicada | Caminho de abertura funcional no cenário testado |
| Tech Tree Marks | Presença visual | Integração na árvore observada |

Transparência da área central do Settings Panel: melhoria estética possível, sem
falha funcional confirmada, não bloqueante. Não alterada nesta tarefa.
Border Color: utilizador confirmou cor personalizada em batalha, alterações de cor e
persistência, sem anomalia funcional reportada. BORDER_COLOR — PASS (RUNTIME VERIFIED,
por confirmação do utilizador). Não generalizar para todos os parâmetros/perfis.

### Batalha e lifecycle — dois ciclos comunicados

Confirmados pelas capturas/logs anteriores segundo o responsável: Battle HUD Gameface,
Team Panels, Team Strength, High Caliber Progress, Vehicle Markers, Minimap Enhancements,
indicadores junto à mira, Server Turret Extended, retorno aos resultados e Battle
Efficiency Results. O utilizador confirmou funcionamento correto nos dois ciclos.
Não declarar que todos os cálculos internos foram matematicamente validados ou que
cada opção/modo/renderer foi exercitado isoladamente.

TWO BATTLE CYCLES — PASS (confirmação comunicada). Ambos chegaram aos resultados;
marcadores inicializados e finalizados em ambas as batalhas, segundo os relatos.

| Ciclo | created | destroyed | remaining | Interpretação |
|---|---|---|---|---|
| Primeira batalha | 22 | 7 | 15 | Diagnóstico comunicado; sem regressão funcional reportada |
| Segunda batalha | 24 | 6 | 18 | Diagnóstico comunicado; sem regressão funcional reportada |

VEHICLE_MARKERS_LIFECYCLE — PASS (TWO BATTLE CYCLES), no âmbito funcional observado.
Contadores permanecem DIAGNOSTIC_OBSERVATION — NO_FUNCTIONAL_REGRESSION_CONFIRMED.
Não provam fuga de memória nem ausência absoluta de referências retidas. Não foi
iniciada investigação/correção para limpar contadores ou logs.

### Avisos conhecidos, sem atribuição indevida

| Mensagem | Classificação | Tratamento nesta consolidação |
|---|---|---|
| Gameface :not / :disabled / font: inherit | KNOWN_WARNING — NO_CONFIRMED_REGRESSION | Comunicados; sem correção CSS |
| Partículas Ch62_BZ_75_M ausentes | CLIENT_RESOURCE_ERROR — ATTRIBUTION_UNCONFIRMED | Não atribuídas ao Driftkings |
| rudimentaryPopovers: must not load into login screen! | KNOWN_CLIENT_WARNING — ATTRIBUTION_UNCONFIRMED | Sem correção Scaleform |
| Texture Manager, duplicadas/indisponíveis | KNOWN_WARNING — ATTRIBUTION_UNCONFIRMED | Não atribuir automaticamente ao mod |
| remaining dos marcadores | DIAGNOSTIC_OBSERVATION — NO_FUNCTIONAL_REGRESSION_CONFIRMED | Preservar números, sem conclusão de leak |

Os relatos não indicam traceback Python nem falha de inicialização Driftkings. Não há
log runtime local útil nesta sessão para certificar essa ausência independentemente.
Conhecimento de warnings não equivale a log integralmente limpo.

### Artefactos e rollback preservados

Hashes recalculados nesta execução:
- build/experiments/20261113T205332Z-7318b280/output/driftkings.wotmod:
  2e169b29db91f4d029101de6997a4c17436748fc4483713986cff989ce4337c0;
- instalado C:/Games/World_of_Tanks_CT/mods/2.4.2.0 Common Test/driftkings.wotmod:
  mesmo hash beta.10;
- beta.9 original em Driftkings_SettingsLab/build/experiments/20261111T115234Z-1d26e1e9/
  output/driftkings.wotmod: 22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9;
- backup Driftkings_Preservation/f7-g1.1-20261113T205332Z-7318b280/driftkings.wotmod.beta9:
  mesmo hash beta.9.

install-record.json e pre-install-manifest.json presentes. Registo de instalação:
2026-11-13T20:55:20.437587+00:00, só driftkings.wotmod substituído, zero acrescentados/
removidos. Procedimento reversível na secção41 permanece válido documentalmente;
nenhum rollback, cópia, reinstalação ou remoção de backup executado aqui.
Defaults pessoais não alterados. A ausência do ficheiro minimap_enhancements.json
anotada na instalação continua observação de configuração, sem nova falha funcional
reportada nos testes de minimapa; não foi corrigida nem tratada como bloqueio automático.

### Git e higiene dirigida para futura integração

Inicial/final: 94 caminhos, 60 M / 3 D / 31 untracked, staging vazio. Contagem histórica
aproximada de91 superada pelas alterações F7-G1.1. Diff tracked: 63 ficheiros,
1688 inserções/736 remoções; não inclui conteúdo dos31 untracked. Sem entradas não
resolvidas no índice ou marcadores de conflito nos textos inspecionados.

Remoções pendentes: panel_gameface/halloween_tab.js e dois testes Halloween TAB;
pertencem à migração já autorizada, não foram removidos nesta execução. Novos ficheiros
incluem patches996, lock996, recursos do host/SVG, planos e testes dirigidos; não
confundir com outputs de build. Seis renames AS3 PascalCase presentes fisicamente;
core.ignorecase=true pode mostrar grafia antiga no status. Preparação futura deve
registar esses renames corretamente, sem git add/config nesta tarefa.

Nenhum output .wotmod/.zip/.exe/.pyc/.swf/.swc/.log/.tmp/.bak encontrado entre os caminhos
pendentes. build/experiments, build/unified e toolchain.local são ignorados, conforme
check-ignore. Backups e perfis temporários não pertencem à integração. Não alterar
.gitignore nem forçar inclusão de outputs para os tornar parte de develop.

Leitura dirigida dos textos pendentes não encontrou padrões de alta confiança de
chaves privadas/tokens GitHub/AWS/Bearer; nenhum valor sensível foi reproduzido. Não é
certificação geral de ausência de dados pessoais. Caminhos locais encontrados em docs
são evidência histórica; em testes são exemplos/fallback CT configurável. Correspondências
em vehicle_markers_patch.py eram labels ASM, não drive paths reais. Não identificado
hardcode pessoal de produção que bloqueie esta preparação; rever seleção final em G4.

Refs locais develop e origin/develop disponíveis, ambas
832d3263c3e69a8ca22e5210d5328188c0266b09. develop...HEAD: 0 exclusivos de develop,
13 exclusivos de HEAD. Sem fetch; refs remotas locais podem estar desatualizadas.
Isto não demonstra que um futuro merge será sem conflitos e não inclui deltas não
commitados. Não executado merge, ensaio de merge, commit, push, PR ou mudança de branch.

### Prontidão, limitações e pendências futuras

READY_WITH_DOCUMENTED_LIMITATIONS para futura preparação de commits. Nenhuma regressão
funcional confirmada nesta evidência exige bloquear F7-G4. Melhorias estéticas, warnings
e cobertura não realizada não são convertidos em novas tarefas/bloqueios automáticos.

Limites: resultados runtime específicos da beta.10 no CT996; ausência de log local para
reinspeção; nem todos os cálculos/opções/modos/escalas foram verificados; sem prova
absoluta de libertação de referências; independência sem OpenWG não demonstrada nesta
execução; cliente EU de produção não validado. Não declarar release estável pronta.

Pendências futuras, sem execução: Fog Remover/default OFF; divulgação de gasto de
moedas Tour of Duty; explicações Account Manager; analytics opcional; atualização do
Updater; textos WGMods; estética Settings Panel; próxima versão EU; preparação dos
commits e PR para develop. Relevância para publicação continua registada, sem bloquear
por si esta consolidação CT. Fog/Updater/Analytics não alterados aqui.

F7-G4 recomendado apenas após autorização expressa: preparar commits por âmbito,
preservar case AS3, selecionar somente fontes/recursos/testes/documentação apropriados
e excluir outputs/segredos/artefactos locais. F7-G5 futura integração em develop;
integração main não autorizada. Não iniciado qualquer desses grupos.

### Integridade documental e veredictos

Única escrita: cabeçalho/linha Fase7 no quadro e esta secção42. Secções1–41 preservadas
fora desses dois deltas, com reversão em memória conferida contra os bytes anteriores.
Ficheiros pendentes fora do progresso mantêm hashes. Master plan, versão, release,
fontes CT, original, backups, cliente, produção e testes não modificados.
Nenhum teste/build/instalação/jogo/auditoria arquitetural reexecutado.

F7-G3 — RUNTIME CONSOLIDATION: PASS.
CT996 FUNCTIONAL VALIDATION — PASS_WITH_LIMITATIONS (runtime comunicado pelo responsável).
TWO BATTLE CYCLES — PASS.
VEHICLE_MARKERS LIFECYCLE — PASS_FUNCTIONAL.
PYTHON TRACEBACKS — NOT_VERIFIED (log local vazio; relatórios comunicam nenhum).
KNOWN WARNINGS — DOCUMENTED.
ORIGINAL BETA.9 — PRESERVED.
GIT INTEGRITY — PRESERVED.
COMMIT PREPARATION — READY_WITH_LIMITATIONS.
DEVELOP INTEGRATION — NOT_EXECUTED.
MAIN INTEGRATION — NOT_AUTHORIZED.
F7-G3 — VALIDATION_PENDING. FASE 7 — IN_PROGRESS.
Parar; aguardar autorização para F7-G4, sem executar preparação de commits agora.

### Reconfirmação do F7-G3 — 2026-11-14

O pedido F7-G3 reenviado repete o âmbito e as evidências funcionais anteriores;
nenhuma autorização de F7-G4/G5 foi acrescentada. Consolidação da secção42 reutilizada,
sem nova auditoria, repetição de testes ou duplicação do relatório runtime.

Reconfirmados em leitura: branch reorganization/settingslab; HEAD
bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3; 94 caminhos (60 M/3 D/31 untracked), staging
vazio e sem conflitos. Diff tracked continua 63 ficheiros, +1688/-736. develop e
origin/develop locais continuam 832d3263c3e69a8ca22e5210d5328188c0266b09, sem fetch.
Nenhum output de build/log/binário inesperado entre os caminhos pendentes.

Beta.10 instalada mantém 2e169b29db91f4d029101de6997a4c17436748fc4483713986cff989ce4337c0.
Beta.9 original e backup reversível mantêm
22ed682634dfe84137a2f8ac775dc3ea1d1bb72544a2e01791fa88b5190b97e9.
O game.log habitual continua vazio; PYTHON TRACEBACKS NOT_VERIFIED independentemente.
Runtime permanece atribuído aos relatos/capturas e confirmação do utilizador, incluindo
Border Color e duas batalhas. Contadores 22/7/15 e 24/6/18 conservados como diagnóstico,
sem fuga de memória demonstrada ou garantia de ausência de referências retidas.

Sem novas evidências de regressão, mantidos PASS_WITH_LIMITATIONS e
READY_WITH_DOCUMENTED_LIMITATIONS. Warnings, pendências EU/publicação e tarefas futuras
continuam documentados acima. Nenhum código, teste, configuração, artefacto, backup,
cliente ou Git alterado. Única escrita: esta nota no progresso; todo o texto anterior
preservado byte a byte. F7-G3 VALIDATION_PENDING; Fase7 IN_PROGRESS.
Recomendada autorização específica de F7-G4; nenhuma preparação de commits iniciada.

## 43. F7-G4 — Commits locais C1–C6 e preparação documental C7

2026-11-15, Europe/Lisbon. Atualização apenas no índice, autorizada pelo pedido
F7-G4B.13. Os três ficheiros físicos não são editados. O pedido F7-G4A confirmou
expressamente a conclusão e aprovação de F7-G3; os estados VALIDATION_PENDING
anteriores permanecem como histórico das respetivas entregas, sem apagar evidências.

### Estado real após C6 e gates

Branch `reorganization/settingslab`; HEAD `1fcdb20f74f3de9fd01c1daee324bc8cc68dabde`.
Antes de C7: quatro caminhos pendentes, um modificado (whitespace C2), três documentos
untracked, staging vazio, sem conflitos; `core.ignorecase=true`. Snapshot de 1 108
ficheiros físicos guardado fora da worktree para comparação de SHA-256.
F0–F6 mantêm os encerramentos locais e limites históricos; Fase 7 `IN_PROGRESS`.
F7-G4A concluiu o plano; C1–C6 foram preparados, testados em árvores exportadas e
criados individualmente mediante autorização. C7 está em preparação/validação,
`AWAITING_APPROVAL`; não está criado. Não iniciado F7-G5 nem integração em `develop`.

| Grupo | Commit local criado | Mensagem |
|---|---|---|
| C1 | `b658d36b4285b7b65fdba3a7c9bb3d29d2e44b81` | `feat(gameface): complete native surfaces and shared battle host` |
| C2 | `50722492e3ca02ef2e97472dfc0fd9a7b24633d5` | `refactor(flash): normalize six internal AS3 class names` |
| C3 | `f0258da495901eb568dc6e4da4bde83df3593695` | `fix(flash): make teardown retryable and reject stale roster callbacks` |
| C4 | `d498e4b9c507535737a76338a8887ac9ac09f4fe` | `feat(launcher): add metallic DK vector states` |
| C5 | `58dcb405a3fe80c03937d99cc28a57b352642d71` | `fix(build): pin CT996 identity and resource bridges` |
| C6 | `1fcdb20f74f3de9fd01c1daee324bc8cc68dabde` | `fix(build): isolate short RABCDAsm workspaces on Windows` |
| C7 | Não criado | `docs: record reorganization and CT996 validation` (planeado) |

Parents consecutivos verificados; C1 parte de `bebe4cc5bd24a529d160a8c1ac2c58f79b8015d3`.
Nenhum push, PR, tag, release ou integração foi realizado nesta sequência.
Refs protegidas: `develop` em `832d3263c3e69a8ca22e5210d5328188c0266b09` e `main`
em `c30d08d37c90d49bbdcd07f67e401c93ac600ae6`, sem alterações. Sem operações remotas;
isto não certifica atualização das refs remotas nem ausência de futuros conflitos.

### CT #996 e evidências de C5

Referência: **World of Tanks 2.4.2.0 Common Test #996 — revision 2660091**, realm CT.
Cliente e fontes externas consultados apenas em leitura. Preflight verifica identidade,
manifesto, proveniência e hashes de oito contratos recuperados. Variantes e locks
#995/#996 explícitos; contratos históricos #995 preservados; builds desconhecidas
recusadas sem fallback silencioso. Os documentos nativos single-file conservam pins
históricos e continuam sujeitos à verificação exata dos buffers.

Resultados da preparação C5, reportados antes do commit e não confundidos com build:
32 testes unitários prioritários PASS; três verificações adicionais do workspace
anterior PASS. Integração read-only: carrossel com 24 operações e Crew Tooltip com
três, aplicadas em memória com hashes de entrada/saída exatos. Movie nativo dos markers
corresponde ao lock #996, SHA-256
`52c5906b04998132efb7a70422999b5dd225d89fb29c49c89d41ba8a59f090b6`.
Contratos estruturais são verificados antes de modificar o ABC. Plano estático: 335
assets. Contagens de operações, métodos de teste, assets, catálogo e identidade
reconfirmadas documentalmente nesta etapa; não foram repetidos os testes C5.

### Workspace C6 e limitações dos testes

Workspace interno preservado quando cabe no orçamento. Caso contrário, usa
`DK_MARKER_WORKSPACE` ou `DK_TMP` na unidade do repositório, com subdiretório exclusivo
`vm_<run_id>`. A adoção exige caminho absoluto sem traversal/redirecionamentos,
sem sobreposição com repositório ou diretórios protegidos, criação exclusiva e
identidade verificável. Diretórios preexistentes não são reutilizados.

Preparação C6: **53 testes, 52 PASS e 1 SKIPPED**, zero falhas/erros. O teste ignorado
exige descritores POSIX reais de `/proc/self/fd`; os cenários Windows de junctions
foram executados. Testados limites de comprimento, override, execuções sucessivas,
isolamento, preservação de sentinelas e outputs, limpeza após sucesso/exceção e
rejeição de locais impróprios. Três verificações adicionais confirmaram propagação
de falhas de cleanup (com causa anterior quando existente) e libertação após falha
de preparação. Não equivalem a garantia de cleanup quando o sistema de ficheiros falha.

Os testes de isolamento incluem fluxos instrumentados do compilador em fixtures
temporárias; não são builds WoT. **RABCDASM_INTEGRATION — PARTIAL**: nesta fase C6
não foi executado RABCDAsm real nem compilador WoT. Concorrência multiprocesso não
foi testada; os testes demonstram execuções independentes/sucessivas e criação
exclusiva, sem prova de todas as condições de corrida.

### Runtime histórico, dependências e pendências

Catálogo atual: 20 nativos / 0 consumidores OpenWG / 2 janelas próprias do lobby;
nove HUD numa janela Wulf neutra, nove modelos independentes; sete componentes Flash
preservados. Isto não prova eliminação integral de OpenWG do modpack nem independência
runtime sem a biblioteca. ModsListAPI, ModsSettingsAPI e dependências instaladas intactas.

F7-G2/F7-G3 consolidaram relatos/capturas e confirmação do responsável sobre garagem,
painel, integrações visíveis e duas batalhas no CT #996 da beta.10. Mantido
PASS_WITH_LIMITATIONS; nenhuma nova observação direta no cliente nesta sequência.
PYTHON TRACEBACKS — NOT_VERIFIED independentemente na consolidação: log local vazio.
Contadores dos markers e warnings continuam diagnósticos, sem prova de fuga ou de
libertação absoluta, e sem atribuição automática ao Driftkings. Todos os limites e
pendências da secção 42 permanecem, incluindo cálculos/modos/escalas não exaustivos,
independência sem OpenWG, EU não validado e tarefas futuras de publicação.

Nenhuma nova build completa ou instalação foi feita na preparação C1–C7; a build
beta.10 de F7-G1.1 é evidência histórica distinta. Release pública não autorizada;
integração em `develop` pendente e sujeita a nova autorização. `main` não integrada.
O plano original não é reescrito para declarar requisitos concluídos por inferência.

Residual C2 preservado fora de C7:
`flash_source/battle/src/driftkings/battle/components/distance_marker/distancemarkerui.as`,
linha 11: um espaço ASCII `0x20` após `BattleDisplayable` só no ficheiro físico.
Avaliar separadamente antes de declarar a worktree limpa; não corrigido nem descartado.

### Próxima decisão

Rever a seleção documental C7 e autorizar expressamente a criação, se aprovada.
Este registo não declara C7 criado, reorganização integrada, runtime EU aprovado ou
release pronta. Não iniciar integração, push ou PR automaticamente.
