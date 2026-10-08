# Fase 10.1 — interferência do host de build

Estado final desta execução: **INCONCLUSIVE — cenário D**. Probe executado uma
única vez e concluído; o utilizador confirmou ausência de novo alerta.
Não publicar beta, desativar proteção ou criar exclusões amplas.

## Evidência já disponível

O utilizador reportou Bitdefender Advanced Threat Defense,
`SuspiciousBehavior.234FFCC4EE6F3D`, com bloqueio de todas as aplicações envolvidas.
Processos iniciais/filhos, caminhos completos, command line, ficheiro responsável,
timestamp e árvore do alerta continuam desconhecidos. A leitura dos diretórios
locais `Atc/Feedback` e `Desktop/Events` não devolveu ficheiros de evento; não foi
encontrado um canal Windows de eventos Bitdefender legível. Estes campos precisam
dos detalhes/exportação da notificação, não podem ser inferidos do ID.

Logs locais do controlo limpo: última escrita às 23:26:43 de 8 de outubro de 2026;
ensaio protegido do host: 23:24:56. Ambos terminaram durante
`test_post_restart_receipt_python27_windows_paths_and_deduplication`, sem relatório
final. São timestamps dos nossos logs, **não timestamps confirmados da deteção**.

Cadeia esperada pelo código: Python 3 do build → hg.exe/Python 2.7.15 →
`windows_files.safe_path` → PowerShell com `-EncodedCommand`, oculto. O teste de
recibos chama esse mecanismo através de `Results.scan`. Sem a árvore do alerta
não é possível afirmar qual processo/ficheiro originou a decisão do antivírus.

## Reprodução única

Antes da execução, recolher manualmente no evento Bitdefender os seguintes
campos; marcar "não disponibilizado" quando não existir, sem os inferir:

- [ ] detection name e timestamp, incluindo timezone
- [ ] application/file path e SHA-256, se disponível
- [ ] parent process e child process, com caminhos completos
- [ ] process tree e full command line
- [ ] blocked action e file/module responsible
- [ ] product module e remediation/action taken

Já fornecidos: Advanced Threat Defense, `SuspiciousBehavior.234FFCC4EE6F3D`,
bloqueio de todas as aplicações envolvidas. Os restantes campos são desconhecidos.

Comando autorizado para esta execução (já executado; não repetir):

```powershell
python build_tools/host_interference_probe.py --run-once
```

O comando importa apenas o `windows_files.py` limpo e executa **uma chamada** a
`safe_path` para uma fixture em `build/diagnostics/host-interference/fixture`.
Não carrega PJOrion, updater completo ou código ofuscado. Não toca no jogo.
Os registos capturam argv, PID do host, argv planeado do filho, PID do filho se
criado, timestamps UTC, runtime, resultado e hash do source. O comando original
da operação é mantido; a instrumentação só escreve evidência no workspace.

`attempt.json` é criado de forma exclusiva antes do lançamento: outra execução
é recusada, incluindo após bloqueio parcial. A ausência de relatório final não
é tratada como sucesso, mesmo com exit code 0. Não apagar o marcador para repetir.

## Gate de alteração

Só substituir o mecanismo Windows depois de a reprodução e o evento do antivírus
confirmarem a associação. A substituição deverá preservar recusa de reparse
points/junctions, paths Unicode, validação de ancestrais e substituição atómica
de recibos, inclusive no Python 2.7 do WoT sem `_ctypes`. Não enfraquecer essas
verificações nem trocar hosts/caminhos para contornar o bloqueio.

Depois, validar o mecanismo novo e repetir a suite completa da Fase 10 sobre
source, bytes protegidos e pacote final. Não correr a suite que contém a operação
suspeita antes dessa confirmação, para preservar a reprodução única.

## Entrega — reprodução de 8 de outubro de 2026

| Item | Evidência / resultado |
| --- | --- |
| 1. Bitdefender | Evento anterior: Advanced Threat Defense, `SuspiciousBehavior.234FFCC4EE6F3D`; utilizador reportou bloqueio das aplicações. Timestamp original, ficheiro, command line e árvore não disponibilizados. **Sem novo alerta**, confirmado pelo utilizador após o probe. |
| 2. Timestamps | Logs antigos: protegido 23:24:56, limpo 23:26:43; não são horas confirmadas da deteção. Probe: 23:39:27.173251–23:39:28.321194 Europe/Lisbon (UTC 22:39:27–22:39:28). Sem evento novo para correlacionar. |
| 3. attempt.json | Regista Python 3.14.3 x64, executável `C:/Python314/python.exe`, PID 23988, argv/cwd, source/hash e fixture vazia (directory, atributos 16), sem PJOrion. Criado exclusivamente antes do lançamento. |
| 4. Probe | **COMPLETED**, exit code 0, `operation-completed.json` presente, sem timeout; source intacto. Não baseado apenas no exit code. |
| 5. Árvore | Instrumentada: Python 3 PID 23988 → hg.exe PID 13224 → PowerShell PID 13996. Não é uma árvore fornecida pelo Bitdefender. |
| 6. Comando | `python build_tools/host_interference_probe.py --run-once`; host `hg.exe --config extensions.dkfileprobe=build_tools/host_interference_hg.py dkfileprobe`. Filho: `C:/WINDOWS/System32/WindowsPowerShell/v1.0/powershell.exe -NoLogo -NoProfile -NonInteractive -EncodedCommand <payload original>`. Payload completo em `process-events.jsonl`. |
| 7. Executável bloqueado | Nenhum bloqueio observado nesta reprodução. Executável responsável pelo alerta anterior permanece desconhecido. |
| 8. SHA-256 | hg.exe: `ac78054d2d998e22b872b4caa231009fcfff9da7793532cc8a5af8cbce4022d2`; windows_files.py: `212e2a8679d2baf9a60c4637f875dd0314329fea75e9aa25969560acfdd5df1d`. |
| 9. hg.exe | `C:/Users/Ruben/AppData/Local/Atlassian/SourceTree/hg_local/hg.exe`, 20 992 bytes, FileVersion/ProductVersion 4.8.1, ProductName mercurial, OriginalFilename hg.exe, Authenticode NotSigned. Runtime observado: Python 2.7.15 x86. Metadados e execução são consistentes com o Mercurial do SourceTree; ausência de assinatura não comprova origem por si só. Lançado pelo Python de build para compilar/testar Python 2.7, via extensão local. |
| 10. Causa provável | Não identificada. Uma chamada a safe_path no código limpo não reproduziu o bloqueio; isso não explica nem exclui o problema da cadeia completa de receipts. |
| 11. Confiança | Alta quanto à conclusão desta chamada e ausência de alerta reportada; insuficiente para atribuir o evento anterior a PowerShell, hg.exe, PJOrion ou windows_files.py. |
| 12. Alterações | Só instrumentação/checklist/auditoria. Nenhuma alteração funcional ou proposta de substituição do filesystem; sem causa confirmada, não há base para a implementar. |
| 13. Testes posteriores | Não executados. Paragem após o probe; sem suite completa, sem PJOrion. `git diff --check` aprovado. |
| 14. Fase 10 | **FROZEN**: interferência original não resolvida nem explicada. Sem beta publicada, tag, deployment ou avanço para Fase 11. |
| 15. Decisão | **INCONCLUSIVE**, cenário D. Não forçar PASS. |

PowerShell foi criado às 23:39:27.559 e terminou às 23:39:28.231, com código 0.
O comando preservou `CREATE_NO_WINDOW` (134217728), os argumentos e o mecanismo
original. O caminho acima é o caminho pedido ao launcher; não se obteve uma
identidade independente da imagem resolvida pelo Windows/WOW64.

Artefactos em `build/diagnostics/host-interference/`: `attempt.json`, `launch.json`,
`result.json`, `operation-completed.json`, `process-events.jsonl`, `stdout.log`,
`stderr.log`, `hg-audit.json`, `analysis.json`. O marcador permanece intacto.
Nenhuma configuração do Bitdefender foi alterada. Próxima investigação requer
evidência do evento original ou um plano separado autorizado; não repetir este
probe nem retomar a suite por iniciativa automática.
