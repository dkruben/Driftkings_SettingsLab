# Estado do projeto e da documentação

## Estado operacional — 2026-11-25 (Fase 5F: correções de build, política canónica de fins de linha, changelog K8 e reprodução histórica; sem publicação)

- **Reprodução histórica demonstrada:** a candidata `641d013fb3cb2a64af04ba31530702829e53a971294be16bab0fbf7d94e0cccb` foi reproduzida byte a byte a partir dos inputs históricos (epoch `1794965041`; 644 entradas idênticas). Relatório em `_validation\reproduction-20261125\REPRODUCTION-REPORT.md`.
- **K4 distinguido:** K4a (reprodução histórica) demonstrada; K4b (reprodutibilidade em checkout limpo) ainda não demonstrada.
- **Política canónica de fins de linha (G2):** LF para todas as fontes textuais de produção, exceção CRLF só para `*.cmd`, binários marcados como `binary`. Nenhum blob renormalizado. Teste: `tests/build/test_input_policy.py`.
- **Correções de build (G1):** B1 (descoberta de toolchain em raízes pouco profundas) e B2 (espaço de trabalho de marcadores acima do limite do Windows), com testes; `--expect-realm` e validação do snapshot de referência.
- **K8 (G3):** changelog corrigido em `build_data/release.json` e no rascunho WGMods; versão `0.1.7-beta.2`. Entra num artefacto só no Clean Release Build.
- **Procedimentos:** o modo release não aceita `--isolated-output`; o isolamento vem de um worktree separado (plano §24.7).
- **Construção limpa (Clean Release Build, plano §24.9):** duas construções independentes a partir do mesmo commit `4795ba4579ef9fde18da643e13741fc8662023a4`, em worktrees separados, com epoch do commit `1795579096`, `git.dirty` falso e árvore limpa. WOTMOD `2cc926821b343ab4aaf5033b830805762c8f3aabff1e21ac3b76864169c2ce6c` (14 039 188 bytes), idêntico nas duas construções; 644 entradas idênticas; ZIP e metadados de distribuição idênticos.
- **K4b demonstrado** para este commit, toolchain e epoch. A candidata congelada `641d…0ccc` mantém-se como reprodução histórica (K4a).
- **Comparação com a candidata congelada:** 447 entradas diferentes, todas explicadas: 308 cabeçalhos `.pyc` (epoch), 2 SWF (apenas a data de compilação, 5 bytes descompactados), 137 ativos de texto (só fins de linha). Zero diferenças funcionais ou não explicadas.
- **K8 fechado para o artefacto limpo** (changelog corrigido). A candidata congelada mantém os metadados originais.
- **Lista de verificação manual** para o novo artefacto no plano §24.11. Nada foi instalado nem executado no jogo.
- **Publicação:** NO-GO. Nada foi publicado, assinado, etiquetado ou enviado.

## Estado operacional — 2026-11-25 (Fase 5E: aquisição de entradas de build, CT, CI e changelog; sem commit, sem rebuild)

- **Candidata congelada:** `641d013fb3cb2a64af04ba31530702829e53a971294be16bab0fbf7d94e0cccb`, verificada antes e depois de todos os testes. Não regenerada.
- **Ferramenta de aquisição:** `build_tools/acquire_flash_inputs.py` (sem dependências externas). Lê o cliente só em modo leitura, extrai apenas os SWC do manifesto, verifica cada um pelo SHA-256 fixado, rejeita entradas em falta, incorretas ou inesperadas, usa cache em `build/` (ignorada pelo Git) e não descarrega nada. Testes: `tests/build/test_flash_acquisition.py` (27).
- **NA 999 (execução real, leitura apenas):** os 8 SWC foram extraídos do cliente NA instalado e os 8 SHA-256 coincidem com o inventário congelado. O cliente não foi alterado. As regras `.gitignore` impedem que os binários sejam commitados.
- **D1b (CT):** os 8 SWC CT rastreados e o manifesto CT foram preservados localmente com inventário e hashes. Não foram removidos. O cliente CT instalado não reproduz os bytes rastreados (diferenças de poucos bytes por biblioteca); a remoção fica bloqueada até haver origem, direitos e manifesto CT com pins de cliente. Histórico não reescrito.
- **D2b (changelog):** das sete entradas, três estão verificadas, três estão parcialmente verificadas e uma tem uma afirmação não suportada (traçado da arma sem alteração desde beta.1; "opcional" sem evidência). O WGMods draft público foi corrigido. A correção de `release.json` fica para a Clean Release Build (K8), porque o ficheiro é entrada do build congelado.
- **D4:** eliminação de `test_battle_cards.py` aceite com a cobertura nativa; K5 fechado para as lacunas identificadas. Não é validação de renderização no cliente; as verificações manuais estão listadas (plano §23.6).
- **D6b:** o nome do responsável não aparece em documentação pública, exceto em dois registos históricos de aprovação de 0.1.6-beta.1, que não foram editados. Cópias e inventário preservados localmente.
- **CI:** a validação pública não precisa de recursos proprietários (simulação com cópia sem binários NA, sem `node_modules` e sem `build/`: runtime 863 OK, build 365 OK). Nenhuma alteração de workflows ou de definições do repositório.
- **Testes (2026-11-25):** runtime 863 OK em Python 2.7.18 e 3.14.3; build 365 OK (2 saltos); artefactos 7 OK (2 saltos); frontend 30 suites; teste real de aquisição OK.
- **Avaliador formal:** 13 pontos (inalterados em número). K6 fechado para NA; K7 (CT) e K8 (changelog) abertos, não bloqueantes.
- **Commits locais:** **CONDITIONAL GO** para autorização, na ordem C4 → C4a → C3 → C1 → C2 → C5 → C6 → C8, com as condições do plano §23.15. Nada foi preparado no índice nem commitado.
- **Publicação:** NO-GO.

## Estado operacional — 2026-11-25 (Fase 5D: decisões D1–D6 e testes nativos; sem commit, sem rebuild)

- **Candidata congelada:** `641d013fb3cb2a64af04ba31530702829e53a971294be16bab0fbf7d94e0cccb`, verificada após todos os testes desta fase. Não regenerada.
- **Testes nativos:** T-N1 (marcas, 17 testes), T-N2 (apresentação MainGun, 13 testes) e T-N3 (anexação pendente, anexação atrasada e visibilidade do HUD, 7 testes). Só testes; nenhum ficheiro funcional alterado. Três mutações controladas numa cópia temporária foram apanhadas pelos testes previstos.
- **Remoção de `test_battle_cards.py`:** aceite condicionalmente; a cobertura nativa agora existe. A eliminação segue no commit C7, depois de revisão.
- **D1 (SWC):** os 8 binários NA foram comparados com os pacotes `gui-part1..4.pkg` do cliente NA instalado (leitura apenas): 8/8 corresponderam aos hashes do manifesto. Não há licença que permita redistribuir recursos extraídos da Wargaming; a licença GPL-3.0 do projeto não os cobre. **Não serão commitados.** A proposta de aquisição a partir do cliente instalado, com hashes fixados, está no plano §21.1. Os 8 SWC CT já tracked desde 0.1.7-beta.1 têm o mesmo problema de direitos e exigem decisão própria.
- **D2 (release.json):** a alteração é só o `changelog` (7 entradas da candidata); `version` continua `0.1.7-beta.2`. Não há tags nem registos de publicação.
- **D3 (clock_diagnostics.py):** mantido como ferramenta de investigação. Excluído do WOTMOD pelo `build_config.json`, ausente do ZIP manual e do Setup, sem importações em runtime. Testes de exclusão adicionados.
- **D5 (flatted.py):** `npm ci` a partir do `package-lock.json` tracked, num diretório temporário, recria `flatted.py` com o mesmo SHA-256 da entrada de build (`f784c254…e644`).
- **D6 (nome do proprietário):** removido de `docs/STATUS.md`. Permanece em registos históricos de aprovação de 0.1.6-beta.1 (decisão do proprietário).
- **Regressões (2026-11-25):** runtime 863 OK em Python 2.7.18 e 3.14.3; build 338 OK, 1 salto POSIX (inclui 8 testes de proveniência); artefactos 7 OK, 2 saltos com razão explícita; frontend 30 suites.
- **Avaliador formal (2026-11-25):** 13 pontos abertos (ver plano §21.9): sem commit, sem CI, sem assinatura, regiões EU/ASIA/CN pendentes, K1–K4 abertos, decisão PENDING, sem aprovador nem data.
- **Reprodutibilidade:** não demonstrada. Procedimentos de Reprodução e de Release Limpa preparados (plano §22), não executados.
- **Publicação:** NO-GO. Commits locais: **NO-GO para execução agora** (ver plano §21.11).

## Estado operacional — 2026-11-25 (Fase 5C: regional, rastreabilidade de testes, reprodutibilidade e preparação de commits; sem commit)

- **Publicação:** NO-GO (beta e stable). Nada foi publicado, assinado, etiquetado, integrado nem enviado.
- **Candidata congelada:** `641d013fb3cb2a64af04ba31530702829e53a971294be16bab0fbf7d94e0cccb` (14 043 751 bytes). Não regenerada nesta fase.
- **Arquitetura standalone:** sem dependência de runtime de OpenWG nem de ModsListAPI; 20 consumidores nativos e 0 OpenWG no pacote de marcas; `ui_dependencies` removido. As remoções de `res/wotmods` estão por commitar.
- **Evidência de runtime (última execução, não repetida nesta fase):** `auto.runtime` 823 OK em Python 2.7.18 e 3.14.3; `auto.build` 328 OK, 1 salto POSIX; pacote da candidata 7 OK, 2 saltos com razão explícita. Validação NA com confirmação do proprietário e registo de log conforme o plano §16.
- **Histórico v0.1.6:** upgrade manual isolado a partir do ZIP público verificado (digests e assinatura de produção): 27 verificações, 0 falhas. Não é um Setup e não é um cliente real.
- **ZIP manual:** instalação limpa, reinstalação e corrupção: 27 verificações, 0 falhas, em ambientes sintéticos.
- **Helper nativo Remove Fog:** `Driftkings.FogPackage.exe` da candidata executado contra pastas sintéticas com processo-pai de teste: H1–H4, 11 verificações, 0 falhas.
- **Atualizador ponta a ponta em localhost: 13/13 OK** (S1–S13). Limitações: chave Ed25519 temporária injetada só em memória; transporte mapeado para `127.0.0.1`; jogo substituído por stub `PING.EXE`; assinatura de produção não usada; nenhum cliente real atualizado.
- **Não testado (atualizador):** recuperação de transação de instalação interrompida; execução de rollback; atualização com assinatura de produção; instalação no cliente real do utilizador. As células regionais do atualizador **não** estão verificadas só pelo teste localhost.
- **Bloqueio do instalador:** Windows Setup não executado em isolamento. Windows Sandbox desativado; sem perfil ou VM isolados sem alterar o sistema. Procedimento e `.wsb` preparados em `_validation\sandbox`, não ativados. Instalador: NO-GO.
- **Reprodutibilidade do WOTMOD:** não demonstrada. A candidata foi construída a partir de árvore suja e o HEAD `6bcce1a7` não contém as entradas usadas (plano §20.3). Procedimento preparado para depois da autorização de commit.
- **Matriz regional** (upstream `izeberg/wot-src`, verificada em 2026-11-25; plano §20.1):

| Região | Cabeça da branch | Versão (mensagem do commit) | `.version_name` | Python vs NA | Flash-src vs NA | Estado |
| --- | --- | --- | --- | --- | --- | --- |
| NA | `11b56842` (2026-11-24) | 2.4.2.0 #999 | 2.4.2.5523 | — | — | Fonte verificada; runtime confirmado pelo proprietário para `641d…` |
| ASIA | `8f3971ab` (2026-11-23) | 2.4.2.0 #998 | 2.4.2.5526 | Idêntico (só `_stubs/_warnings.py`) | Idêntico | Compatível esperado; sem `gui-part*.pkg` nem SWF compilados no upstream. **Não** SOURCE VERIFIED |
| CN | `3d408644` (2026-11-24) | 2.4.2.0 #997 | 2.4.2.5525 | Idêntico (só `_stubs/_warnings.py`) | Idêntico | 139 recursos em `sources/res` diferem; `paths.xml` e `loc_version.xml` diferem. **Não** SOURCE VERIFIED |
| EU | `447437a2` (2026-11-05) | 2.4.1.1 #993 | 2.4.1.5514 | 7 ficheiros `.py` diferem | 97 ficheiros Flash diferem | **2.4.2.0 não disponível**; comparação semântica impossível |
| CT | `e2a5105e` (2026-11-12) | 2.4.2.0 Common Test #996 | 2.4.2.5518 | 1 (`_warnings`) | 1 | Só referência de desenvolvimento |

- **Commits propostos:** 8 grupos e 105 entradas do estado de trabalho (67 modificadas, 3 eliminadas, 35 não rastreadas). Nada foi preparado no índice nem commitado. Recomendação e bloqueios no plano §20.5.
- **Pendências:** decisão sobre `.swc` (13,7 MB) e sobre `flatted.py` ignorado pelo Git; eliminação de `tests/runtime/battle/test_battle_cards.py` com justificação corrigida (duas lacunas nativas, plano §20.2); decisão de commit e reconstrução limpa; assinatura de produção; aprovação do proprietário; EU 2.4.2.0; recursos compilados de ASIA e CN.

## Estado operacional — 2026-11-25 (Fase 5B: incidente encerrado; instalador por executar)

- **Incidente:** documentado (plano §18.1). Ficheiros do instalador restaurados e verificados; chave de desinstalação apagada não reconstituída (aceite pelo proprietário). Sem nova execução no cliente real.
- **Instalador:** NO-GO. Sem ambiente isolado disponível sem alterar o sistema (Windows Sandbox desativado). Causa da mudança de destino: não demonstrada; a parte do Git Bash está demonstrada.
- **Histórico:** v0.1.6 público descarregado e verificado (digests e assinatura de produção); upgrade manual isolado 27/27 (sintético por ZIP, não o Setup).
- **Atualizador:** verificação de assinatura com chave temporária 5/5; end-to-end não executado.
- **Artefactos:** inventário e preservação em `_artifact_preservation_641d013f_20261125_014023`. Setup de `565897cc` irrecuperável.
- **Candidata congelada:** `641d013f…0ccc`, verificada no build e no NA. Publicação NO-GO.

### Estado operacional — 2026-11-25 (Fase 5: validação isolada de distribuição)

- **Incidente:** uma execução acidental do Setup (argumentos `/VERYSILENT` convertidos pelo Git Bash) atualizou no cliente NA real o `unins001.exe` e o `unins001.dat` do instalador e criou/apagou uma chave de desinstalação no registo (HKCU). Os ficheiros foram restaurados do checkpoint (hashes conferidos). A chave apagada não está registada e não se pode restaurar só com as evidências; decisão do proprietário. `driftkings.wotmod` com conteúdo idêntico.
- **Validado em isolamento:** procedimento ZIP manual (27 verificações); helper Remove Fog nativo (11 verificações: owned, foreign, sem pacote, repetição); suites automáticas do atualizador e da assinatura.
- **Não validado:** instalador Setup por execução (incidente), upgrade com binário 0.1.6 real, atualizador ponta a ponta, desinstalação.
- **Formulário:** nove problemas do avaliador (§17.6); decisão PENDING.
- **Veredito:** distribuição CONDITIONAL GO; instalador NO-GO até execução isolada; atualizador CONDITIONAL GO; publicação NO-GO.

### Estado operacional — 2026-11-25 (validação pós-runtime da candidata 641d013f…)

- **Sessão final verificada no log:** S4 (01:21:59–01:24:21, replay). Candidata carregada (`0.1.7-beta.2`, NA, `failures=[]`); OpenWG e ModsListAPI carregados sem erro; ReplaysManager sem o erro `modsListApi not installed`; sem Remove Fog ativo; sem `rn.box` nem erros SVG; saída normal.
- **Confirmado só pelo proprietário (sem log desta candidata):** hangar, Marks of Excellence, tripulação, carrossel, primeira e segunda batalha, resultados de batalha, regresso ao hangar, persistência de configurações, launcher sem duplicações.
- **Registo formal NA:** decisão PENDING (testes bloqueantes de instalação, atualizador, perfis e reinstalação não executados). Nove problemas do avaliador; ver plano §16.12.
- **Evidência:** não se transfere de `12e2d26d…` nem `565897cc…`. Log da sessão em `_na_runtime_recovery_20261124_225319\logs\session-final-candidate-01-22.log`.
- **Veredito:** CONDITIONAL GO para a próxima fase de preparação; publicação NO-GO; sem aprovação WG para esta candidata.

## Estado operacional — 2026-11-25 (candidata 641d013f… instalada em NA; pronta para teste manual)

- **Instalação:** `mods\2.4.2.0\driftkings.wotmod` = `641d013fb3cb2a64af04ba31530702829e53a971294be16bab0fbf7d94e0cccb` (verificado). OpenWG, ModsListAPI e ReplaysManager mantidos. Remove Fog em quarentena (recovery). Checkpoint de instalação: `_na_install_checkpoint_20261125_011742`.
- **Runtime:** nenhum resultado para esta candidata. Evidência Run A/B refere-se a `12e2d26d…2a20a`.
- **Veredicto:** READY FOR OWNER MANUAL NA RUNTIME TEST — FINAL CANDIDATE. Jogo não lançado. Não recomendar ativação do Remove Fog em batalhas reais antes de confirmar o âmbito WG.

## Estado operacional — 2026-11-25 (Remove Fog: validação final e candidata 641d013f…)

- **Candidata atual:** `build/releases/beta/0.1.7-beta.2/driftkings.wotmod`, SHA-256 `641d013fb3cb2a64af04ba31530702829e53a971294be16bab0fbf7d94e0cccb`, 14.043.751 bytes, `ELIGIBLE_UNSIGNED`, não publicável. Candidatas anteriores preservadas (`12e2d26d…2a20a`, `565897cc…d44e1d`); nenhuma validação em jogo se transfere.
- **Legado:** pacote `Driftkings.RemoveFog.wotmod` instalado por versões antigas é convergido para OFF (uma remoção após fechar o jogo, com cópia de recuperação em `cache/fog/recovery/`). Perfis antigos com `removeFog: true` não ativam a funcionalidade. O painel mostra o estado efetivo (`off-package-loaded` até reiniciar).
- **Linha de base WG (v0.1.6, aprovada):** diferenças documentadas na secção 14.3 do plano de runtime (default ON→OFF; escolha explícita; convergência legada). Não há aprovação WG para a candidata nova. Regras WG atuais não verificadas: confirmar antes de recomendar ON em batalhas reais.
- **Testes:** build 330 (1 salto POSIX), runtime 826 (Python 2.7 e 3.14), artefactos 7 (2 saltos históricos).
- **Estado:** CONDITIONAL GO para validação manual de NA com a checklist 14.9. Nada instalado, lançado, assinado, commitado ou publicado.

### Estado operacional anterior (Remove Fog restaurado)

### Estado operacional — 2026-11-25 (Remove Fog restaurado como opcional, OFF por omissão)

- **Candidata atual (nova):** `build/releases/beta/0.1.7-beta.2/driftkings.wotmod`, SHA-256 `565897ccf5b5533c49ee36f41dcb389ae6412fa8c6065be72cfe5f3769d44e1d`, 14.042.580 bytes, `ELIGIBLE_UNSIGNED`, não publicável. A candidata anterior `12e2d26d…2a20a` está preservada; a validação em jogo dela não se transfere.
- **Remove Fog:** opcional, desligado por omissão. Ativação e desativação só por escolha explícita do utilizador, persistida em `mods/configs/driftkings/cache/fog/choice.json`. Valores antigos do perfil (incluindo o `true` de 0.1.6) não ativam. Não há reinstalação automática. Pacote legado instalado por versões antigas fica no lugar até o utilizador alterar a opção (limitação aberta).
- **Decisões do proprietário pendentes:** default OFF (0.1.6 tinha ON); pacote legado no disco; conformidade com as regras da Wargaming ainda não verificada. Detalhes: [0.1.7-beta.2-na-runtime-plan.md](releases/0.1.7-beta.2-na-runtime-plan.md), secção 13.
- **Testes após a restauração:** runtime 823 (Python 2.7 e 3.14), build 328 (1 salto POSIX), artefactos 7 (2 saltos históricos), frontend 30 suites.
- **Estado:** CONDITIONAL GO para validação manual em jogo da nova candidata com a checklist da secção 13.8. Nada foi instalado, lançado, assinado, commitado ou publicado.

### Estado operacional anterior (Run B)

### Estado operacional — 2026-11-25 (Run B: instalação verificada; validação funcional não recebida)

- **Run B (coexistência):** OpenWG Gameface e ModsListAPI repostos nas localizações originais (hashes verificados). Candidata `12e2d26d…2a20a` e replaysmanager inalterados. Remove Fog ausente. **Sem evidência de sessão e sem resultados funcionais do proprietário**: Run B não está validada. Nenhuma conclusão "standalone e coexistência verificadas" é emitida.
- **Registo formal NA:** 9 problemas do avaliador (eram 13). Verificações automáticas registadas como PASS: runtime (811), build (320, 1 salto), frontend (30 suites), artifacts (7, 2 saltos). Pendentes: commit limpo, NA com testes bloqueantes por fazer, EU, ASIA/CN, assinatura de produção (não autorizada), aprovação do proprietário. Ver [0.1.7-beta.2-na-runtime-plan.md](releases/0.1.7-beta.2-na-runtime-plan.md), secção 12.
- **Dívida técnica não bloqueante:** `launcher.css` usa `:disabled` (aviso do Gameface; regra do Driftkings).
- **Regiões (`izeberg/wot-src`, 2026-11-25):** NA ficheiros pinados idênticos (10/10); ASIA 9/10 (diferença só em `version.xml`); CN 8/10; EU 2.4.1.1 PENDING para 2.4.2.0; CT desenvolvimento.

### Estado operacional anterior — 2026-11-25 (Run A validada tecnicamente; Run B restaurada)

- **Run A (NA #999, candidata `0.1.7-beta.2`, SHA-256 `12e2d26dd2e8f8f0dd600b1f1d395848a62d708da9c53e1ac030d85f96b2a20a`):** resultados do proprietário: hangar PASS, batalha PASS, replay PASS, operação standalone PASS. Análise técnica do `game.log` (4.204 linhas): sem regressão bloqueante; carregamento único por sessão; sem exceções de dependência; OpenWG, ModsListAPI e Remove Fog ausentes durante a sessão; Remove Fog não recriado; `rn.box` e erros SVG não reapareceram. Detalhes em [0.1.7-beta.2-na-runtime-plan.md](releases/0.1.7-beta.2-na-runtime-plan.md), secção 11.
- **Registo formal NA:** decisão continua PENDING em [0.1.7-beta.2-validation.md](releases/0.1.7-beta.2-validation.md) até fecharem os testes bloqueantes (instalação, atualizador, perfis) e as referências de evidência.
- **Run B:** OpenWG Gameface e ModsListAPI restaurados às localizações originais por cópia verificada; candidata e replaysmanager inalterados; Remove Fog não restaurado. Jogo não lançado.
- **Regiões (upstream `izeberg/wot-src`, 2026-11-25):** NA `11b56842` (2.4.2.0 #999, snapshot 2.4.2.5523); ASIA `8f3971ab` (2.4.2.0 #998, 2.4.2.5526); CN `3d408644` (2.4.2.0 #997, 2.4.2.5525); EU `447437a2` (2.4.1.1 #993, 2.4.1.5514) — **PENDING**; CT `e2a5105e` (2.4.2.0 #996, desenvolvimento).

### Estado operacional anterior — 2026-11-24 (fecho da Fase 3 e preparação da Fase 4)

**Resumo atual, substitui o resumo abaixo para efeitos operacionais.**

- **Versões:** stable pública `0.1.6`; beta pública `0.1.7-beta.1`; candidata local `0.1.7-beta.2`; stable alvo `0.1.7`; WoT `2.4.2.0`.
- **Arquitetura:** standalone. Não há dependência obrigatória de OpenWG Gameface nem de ModsListAPI; `ui_dependencies` e os `.wotmod` correspondentes foram retirados da distribuição. Os recursos nativos do Gameface pertencem ao Driftkings. `core/mod_compatibility.py` apenas deteta bibliotecas de terceiros, sem as importar.
- **Publicabilidade:** o compilador grava sempre `publishable: false`. Os estados explícitos (`NOT_ELIGIBLE`, `ELIGIBLE_UNSIGNED`, `SIGNED_UNVALIDATED`, `VALIDATED_NOT_APPROVED`, `PUBLISHABLE`) vêm de `build_tools/publication_state.py`. Uma assinatura não autoriza publicação.
- **Candidata NA:** `build/releases/beta/0.1.7-beta.2/driftkings.wotmod`, reconstruída de forma reprodutível; SHA-256 completo em [registo de Fase 3](releases/0.1.7-beta.2-phase3-readiness.md). Não assinada, não publicável, não validada em jogo.
- **Regiões:** NA com entradas de produção; EU PENDING para 2.4.2.0 (fonte pública ainda em 2.4.1.1, commit `447437a2`); ASIA e CN apenas com evidência de fonte. Nenhuma compatibilidade global está confirmada.
- **Testes:** runtime 811 (Python 2.7.18 e 3.14.3); build 320 com 1 salto; artefactos com 2 saltos por referências históricas ausentes; Python 3.12 não disponível e não executado.
- **Próximo passo:** validação manual NA com a checklist de [0.1.7-beta.2-phase3-readiness.md](releases/0.1.7-beta.2-phase3-readiness.md). Nada foi instalado nem executado nesta fase.

### Resumo anterior (2026-11-24, manhã)


A candidata `0.1.7-beta.2` para WoT `2.4.2.0` está em preparação local. A stable publicada é `0.1.6` e a beta publicada é `0.1.7-beta.1`. A promoção pretendida é `0.1.7`. O perfil de produção depende dos recursos e da validação registados abaixo. [Registo de preparação](releases/0.1.7-beta.2-readiness.md).

## Fases 3F.2B–3F.2D — build experimental, validação CT e pré-consolidação — 2026-11-10

**ARTIFACT PASS, CT INSTALL PASS e CT RUNTIME PASS — experimental, não publicável, sem consolidação Git.** A integração Native BattleInfo da Fase 3F.2A foi compilada com `--isolated-output --keep-source-version`, auditada, instalada no CT e validada em runtime. Nenhuma release foi autorizada; `VERSION` e `release.json` continuam em `0.1.8-beta.1`.

- **Build (3F.2B).** Pacote experimental `0.1.8-beta.4`, 632 entradas ZIP, SHA-256 `49749a9e221cecca45b83978edd113f0b2b60e54dabee09760f01f280e5118d0`, em `build/experiments/20261110T031027Z-b23d8daf/output/`. A primeira tentativa falhou na limpeza do temporário de `vehicle_markers_flash` (WinError 145) e ficou preservada; a correção FIX-B2 permitiu a build seguinte com cleanup Windows completo. `build/unified` e a beta.3 (`f0ff0cde074b25e0ee5d3f3c0647c870d01a85e6c8dfb8ed5b17bdf0709259a8`) não foram alterados. Face à beta.3: seis entradas novas, 312 modificadas, nenhuma removida; bundle `post_battle/random` com o hash previsto no manifesto do patch; catálogo 5 nativos / 15 OpenWG / 2 janelas próprias.
- **Instalação (3F.2C).** Substituição única e verificada de `driftkings.wotmod` no CT `2.4.2.0 Common Test #995`, com backup da beta.3 em `build/backups/ct-phase3f2c-install-20261110T202843925222Z/`. Nenhum outro mod foi alterado.
- **Runtime (3F.2C).** Confirmação visual do utilizador, apoiada no `game.log`: arranque e garagem; os quatro plugins nativos anteriores; painel Driftkings; HUD BattleEfficiency (continua em OpenWG); nova zona BattleInfo nos resultados; Mission Progress e Battle Pass preservados; duas batalhas diferentes com valores distintos; reabertura de resultados sem duplicação visível. O log regista três batalhas distintas ao longo de três sessões e nenhuma linha de aviso ou erro do Driftkings. A alternância A/B/A/B foi confirmada visualmente; o log analisado contém as aberturas A, B e A.
- **Pré-consolidação (3F.2D-FIX).** Testes sem dependência de `build/diagnostics` nem de `git show`; baselines históricas versionadas em `tests/fixtures/native_baselines.json`; verificação explícita de Node.js e do `acorn` fixado antes do patch AST. Execução desta fase: 907 testes Python 3 (`--suite all`), 682 runtime Python 2.7, seis testes de artefactos sobre o pacote experimental, 27 suites frontend, ESLint e validadores PASS. Numa exportação temporária sem `.git`, `build/`, `node_modules` nem fontes CT: 225 testes de build com três SKIP opcionais (fixture CT ausente) e 682 runtime em ambos os interpretadores.

**Limitações.** Não foram testados o estado sem dados nem a extensão desativada. O lifecycle interno em JavaScript não está instrumentado: os diagnósticos da sessão não chegam ao `game.log`, pelo que a libertação de listeners no Gameface real não foi observada. O pacote substitui integralmente o bundle oficial `post_battle/random` e só é válido para o CT #995; qualquer atualização do cliente exige novo manifesto. A validação visual não é uma medição automatizada. O código continua por consolidar em commits.

## Fase 3F.2A — Native BattleInfo Extension — 2026-11-09

**SOURCE INTEGRATION PASS — estado à data, anterior à build e à validação CT descritas acima.** O catálogo de origem passa a cinco transportes nativos, 15 consumidores OpenWG e duas janelas próprias. Os quatro plugins anteriores permanecem inalterados. A beta.3 instalada mantém quatro plugins/16 consumidores/duas janelas, com o mesmo SHA-256.

Integração localizada no BattleInfo, core mínimo de lifecycle, transporte Wulf `native_battle_results`, binding por instância e patch AST específico CT #995. Resultados locais: 879 testes Python 3, 682 runtime Python 2.7, 27 suites frontend e ESLint PASS. A nova suite frontend contém 13 grupos de asserções; não são 13 casos independentes do runner. Artefactos compilados não foram testados nesta fase.

Gameface real, resolução `coui://`, renderer visual e comportamento dos proxies Wulf ficaram, nesta fase, pendentes da Fase 3F.2B (entretanto concluída; ver secção anterior). Aviso Scaleform 3D.1 em observação, causa não determinada. Sem build, instalação, arranque do CT, staging, commit ou push. [Relatório técnico, inventário e limitações](NATIVE_BATTLE_RESULTS_POC.md). As secções seguintes são históricas.


Atualizado em 2026-11-09. Os caminhos e comandos partem da raiz do repositório.

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

- Branch de desenvolvimento: `develop`. Versão de desenvolvimento atual em `build_data/release.json`: `0.1.7-beta.2`, não publicada. A versão final prevista é a stable `0.1.7`. O alvo de build em `build_data/build_config.json` (WoT `2.4.2.0` CT #996) ainda está por decidir. `main` mantém a stable publicada `0.1.6`.
- Versão stable publicada: `0.1.6` (latest). Beta pública mais recente de produção: `0.1.7-beta.1`, conforme o [README](../README.md); confirmar nos releases antes de a referenciar como atual.
- As secções datadas abaixo são histórico. Para o estado atual do código, usar `build_data/release.json`, `build_data/build_config.json` e o Git, não os commits ou bases citados nas secções antigas.
- Alvos do cliente: produção WoT `2.4.1.1` (EU/NA/ASIA); build experimental CT `2.4.2.0` #996. Contratos e ferramentas em `build_data/` e `build_tools/`.
- As versões publicadas e os downloads estão no [README](../README.md). O histórico de publicação permanece nas releases e no Git.
- A beta `0.1.6-beta.1` foi aprovada funcionalmente pelo responsável do projeto em 2026-11-05, com testes declarados de 2026-11-04 em EU, NA e ASIA. Os 18 bloqueantes estão PASS nas três regiões; 57 células PASS e 36 NOT TESTED no [registo oficial](releases/0.1.6-beta.1-validation.md). O painel e os perfis têm persistência confirmada; detalhes históricos sobre construção/aceitação visual do painel permanecem nas secções datadas abaixo. A aprovação funcional não é uma nova medição de desempenho.
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

Os adaptadores atuais usam `gameface/battle`, `gameface/lobby`, `flash/battle` e `flash/lobby`; os contratos ativos estão em `interface_catalog.py`. Os planos de migração concluídos e os estudos antigos foram retirados de `docs`. Os relatórios retirados continuam recuperáveis no histórico Git. A pasta de cópia local `../Driftkings_SettingsLab_docs_backup_20261028/` referida em revisões anteriores não existe no disco à data desta revisão. As pendências da otimização permanecem na auditoria final.

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
