# Fase 10.2 — diagnóstico incremental de receipts

Estado final desta etapa: **REPRODUCED_AT_L2**. L1 PASS + NO_ALERT; L2
ABNORMAL_TERMINATION + ALERT. L3–L6 não autorizados nem executados.
Execução única em 8 de outubro de 2026, 23:43:52–23:43:53 Europe/Lisbon.
Python launcher PID 13416 → hg.exe/Python 2.7.15 PID 28560; código de saída 0,
relatório final presente, zero filhos PowerShell. Source e fixture intactos.
Artefactos: `build/diagnostics/receipt-chain/receipt-l1/` e `summary.json`.
O utilizador confirmou L1 NO_ALERT com a resposta "limpo"; registo em human.json.
PASS técnico sozinho não significa ausência de alerta nem resolução.

A Fase 10 permanece FROZEN. Sem PJOrion, build release, alteração funcional,
configuração de antivírus, publicação ou repetição do probe da Fase 10.1.

Cada nível recebe diretório/marker próprio em
`build/diagnostics/receipt-chain/receipt-lN`. O marker exclusivo é criado antes
do lançamento e não pode ser substituído. O launcher verifica os hashes fixos
de hg.exe e windows_files.py e exige PASS técnico e confirmação humana NO_ALERT
de **todos** os níveis anteriores. Não há force/retry.

## L1 — parser/leitura

```powershell
python build_tools/receipt_chain_probe.py --level 1
```

Usa o mesmo hg.exe/Python 2.7.15 e source limpo. Results.scan, ticket/manifest e
parser reais leem fixtures equivalentes às do teste interrompido, mantidas apenas
sob o novo diretório de diagnóstico. O layout interno imita mods/cache para
exercitar a função real; não toca em mods/cache do jogo.

Conforme autorização específica do L1, dois adapters temporários na fixture
isolam validação Windows (`results.safe_path`) e validação do pacote instalado
(`reader._package_matches`); ambos são registados e restaurados. Não alteram os
ficheiros de produção. Ticket e schema continuam a usar a lógica existente.
Não há acknowledge, notified.json, dedup/replacement ou processo filho Windows.
Hashes antes/depois confirmam leitura sem mudança na fixture.

Após cada nível, **parar e pedir confirmação humana do Bitdefender**. PASS técnico
não confirma ausência de alerta. ALERT/UNKNOWN não autorizam o nível seguinte.
Ausência inesperada do relatório ou WinError 5 interrompem o diagnóstico, sem
retry. Os níveis seguintes serão revistos/implementados apenas após o gate humano;
o launcher impede executar L3–L6 por antecipação.

## Entrega L2 — 8 de outubro de 2026

| Item | Evidência |
| --- | --- |
| Pré-condições | L1 PASS e NO_ALERT confirmado; hashes de todo o source updater e da fixture L1 verificados antes do lançamento. Marker L2 exclusivo. |
| Hashes | hg.exe `ac78054d2d998e22b872b4caa231009fcfff9da7793532cc8a5af8cbce4022d2`; windows_files.py `212e2a8679d2baf9a60c4637f875dd0314329fea75e9aa25969560acfdd5df1d`. Coincidem com baseline. Source intacto após execução. |
| Runtime | Mesmo Mercurial 4.8.1 / Python 2.7.15 x86 do SourceTree; launcher Python 3.14.3 x64. |
| Fixture | Apenas `build/diagnostics/receipt-chain/receipt-l2/fixture`; layout interno mods/cache, sem acesso ao jogo ou package real. Ticket, manifest, result e package de fixture; diretório Unicode preparado. |
| Adapter | `reader._package_matches` continua instalado, mas não foi alcançado. `results.safe_path` original, chamando implementação Windows real; wrappers apenas registam chamadas/processos. Nenhuma validação de identidade do package certificada. |
| Chamadas | **4 chamadas reais**, nas categorias cache, download-directory, ticket e manifest. As três primeiras concluíram; interrupção na quarta, release.json. Ready/missing/Unicode/invalid planeados, mas não executados: paragem imediata. |
| PowerShell | **4 filhos** com argumentos/payload originais e CREATE_NO_WINDOW=134217728. |
| Process tree | Launcher PID 22024 → hg.exe PID 14588 → PowerShell PIDs 18616, 15072, 16052, 10176. Árvore instrumentada, não fornecida pelo Bitdefender. Paths pedidos registados; imagem resolvida/WOW64 não certificada independentemente. |
| Exit codes | Host 0, sem relatório final; primeiros três filhos 0, stdout OK/stderr vazio. Último filho: criação registada, fim/código desconhecidos. Código 0 do host não é PASS. |
| WinError | Nenhum WinError 5 registado antes da interrupção. Sem stack trace de exceção ou stderr; o processo terminou sem concluir a operação. |
| Fixture | Hashes before/after iguais; sem writes de notified.json, acknowledge, replacement ou cleanup. Metadata antes estava em memória do host e não foi persistida antes da interrupção; a igualdade de metadata não pode ser certificada. Metadata após preservada no analysis.json. |
| Technical result | **ABNORMAL_TERMINATION**. `operation-completed.json` e `result.json` ausentes; evidência preservada em analysis.json/logs. |
| Human gate | **ALERT**, confirmado pelo utilizador. Advanced Threat Defense, `SuspiciousBehavior.234FFCC6F2F49D4`, "bloqueou todas as aplicações envolvidas". UI mostrou "agora"; timestamp exato, ficheiro responsável e árvore do AV não disponibilizados. |
| Decisão L3 | **Não autorizado**. Global REPRODUCED_AT_L2; Fase 10 FROZEN. Sem repetição, correção, PJOrion, build release ou publicação. |

Janela do probe: **23:48:06.461834–23:48:10.292329 Europe/Lisbon**, UTC
22:48:06–22:48:10. Último evento: criação de PowerShell PID 10176 às
23:48:09.978, durante safe_path(release.json). Alerta confirmado pelo utilizador
para esta execução; falta timestamp detalhado do AV para correlação exata.

O menor nível que reproduziu até agora é L2: scan real com safe_path repetido,
sem PJOrion. Isso associa o bloqueio à cadeia observada, mas não identifica a
regra interna do Bitdefender, a imagem responsável ou um limiar geral de quatro
chamadas. Não concluir que qualquer quarta chamada falha ou que o payload
isoladamente é a causa. A investigação deve seguir numa Fase 10.3 autorizada.

Os rótulos brutos de algumas categorias não normalizavam separadores mistos;
os paths originais são preservados. `derivedPathCategories` no analysis.json
contém a classificação normalizada correta, sem alterar eventos originais.

Artefactos L2: attempt.json, launch.json, process-events.jsonl, stdout.log,
stderr.log, analysis.json, human.json e fixture preservada. result.json ausente
conforme gate de conclusão. Artefactos L1 e da Fase 10.1 intactos.

## Plano dos níveis seguintes

| Nível | Acrescenta | Gate |
| --- | --- | --- |
| L2 | safe_path real, vários paths/chamadas do scan; sem acknowledgement/replacement | L1 PASS + NO_ALERT |
| L3 | filtering/dedup reais, receipts válidos/inválidos, ordenação e Unicode; sem replacement | L2 PASS + NO_ALERT |
| L4 | validação completa incluindo pacote/version/hash e casos inválidos | L3 PASS + NO_ALERT |
| L5 | acknowledge/replacement atómico real apenas na fixture | L4 PASS + NO_ALERT |
| L6 | método original isolado, mesmas funções/ordem/runtime/semântica da fixture | L5 PASS + NO_ALERT |

Todos os artefactos da Fase 10.1 são preservados. Mesmo seis PASS sem alerta
significariam NOT_REPRODUCED, não RESOLVED, e não retomariam automaticamente a
Fase 10. Reproduzir um bloqueio levará primeiro a relatório e Fase 10.3 proposta,
sem corrigir nesta fase.
