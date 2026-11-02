# Exceções genéricas silenciosas

Revisão de 2026-11-02. Os caminhos partem de `mod/res/scripts/client/driftkings/`. A revisão foi primeiro só de leitura; os pontos de prioridade alta e média foram depois tratados no mesmo dia (secção [Estado](#estado)), sem alterar retornos, estados nem exceções propagadas.

## Método

Um analisador AST percorreu os módulos Python do cliente e listou os `except Exception`, `except StandardError`, `except BaseException` e `except:` cujo corpo não chama nenhum registo (`LOG.*`, `logging`, `print`) nem volta a lançar o erro. Encontrou **41**; **19** estão nas áreas pedidas (`core/updater`, `core/accounts.py`, `components/account_manager.py`). Cada um foi lido no contexto, incluindo o que acontece ao código de erro depois. Depois das correções restam **29**: os 7 das áreas pedidas que ficam silenciosos de propósito e os 22 do resto do cliente.

Um `except` silencioso nem sempre é um defeito: muitos convertem a exceção num código de erro que o chamador regista. A recomendação abaixo distingue esses casos dos que perdem a causa.

## Estado

| Prioridade | Pontos | Estado |
| --- | --- | --- |
| Alta: `LOG.warning` com traceback | `checking.py`, `downloader.py`, `https_transport.py` (transporte indisponível), `accounts.py` (só o tipo) | Tratado (`8b48e6a`, `c53ada6`, `5b376f8`, `60b01e7`) |
| Alta: `LOG.warning` sem traceback | `https_transport.py` (limpeza do staging) | Tratado (`5b376f8`) |
| Média: `LOG.debug` | `account_manager.py` (só o tipo), `context.py`, `lifecycle.py` (política de contexto), `installation.py`, `receipts.py` (validação do pacote cancelado), `windows_files.py` (leitura do pipe), `https_transport.py` (`response.close()`) | Tratado na branch `fix/debug-logging-exceptions` |
| Opcional | `results.py` (comparação de versões) | **Não alterado**: falha esperada com entrada externa, e a recomendação principal era nenhuma |
| Deixar como está | `lifecycle.py` (dois reencaminhamentos), `receipts.py` (reencaminhamento) e as três limpezas de `windows_files.close()` | Sem alteração, de propósito |

Cada ponto tratado tem um teste que confirma o nível do registo e que o comportamento original se mantém. Nos dois módulos de contas, os testes confirmam também que nem e-mails, nem palavras-passe, nem a mensagem da exceção chegam ao registo.

## Áreas pedidas

As linhas são as atuais, depois das correções.

| Ficheiro:linha | O que protege | Situação | Registo |
| --- | --- | --- | --- |
| `components/account_manager.py:58` | Decifrar `accounts.manager` (`wg_ucpdata` + zlib + JSON); em falha tenta ler JSON simples | Fallback intencional para ficheiros antigos não cifrados. Se o JSON também falhar, o `except` exterior regista `LOG.error` | ✅ `LOG.debug` só com `type(error).__name__` (o ficheiro tem palavras-passe) |
| `core/accounts.py:102` | `store.write_accounts()` ao guardar contas | `write_accounts` já regista `LOG.error` nas suas falhas; aqui só chega um erro inesperado, que vira `AccountError('errorSave')` | ✅ `LOG.warning` só com o nome do tipo, sem traceback nem dados das contas |
| `core/updater/checking.py:47` | `checker.check(...)` ao pedir a verificação de atualizações | `completed(None, 'checkError')` regista o código, mas perdia o traceback | ✅ `LOG.warning(..., exc_info=True)` |
| `core/updater/context.py:47` | Ler o estado do hangar/replay para decidir se pode instalar | Devolve `unknownContext`, que bloqueia a instalação (falha fechada) | ✅ `LOG.debug(..., exc_info=True)` |
| `core/updater/downloader.py:179` | Iniciar o download (`transport.stream`) | Aborta o ficheiro parcial e reporta `networkError` | ✅ `LOG.warning(..., exc_info=True)` |
| `core/updater/https_transport.py:181` | `response.close()` depois do pedido | Marca `networkError` se ainda não houver erro; o pedido principal já regista `LOG.exception` | ✅ `LOG.debug(..., exc_info=True)` |
| `core/updater/https_transport.py:190` | `sink.abort()` ao cancelar ou falhar | Converte em `stagingError` | ✅ `LOG.warning` sem traceback |
| `core/updater/https_transport.py:246` | Criar o transporte HTTPS (SSL, CAs, verificação do hostname) | Devolve `UnavailableTransport` (falha fechada, correta) | ✅ `LOG.warning(..., exc_info=True)` |
| `core/updater/installation.py:196` | Confirmar que o instalador preparado corresponde ao bilhete e ao processo atuais | Devolve `False` (não reinicia para instalar) | ✅ `LOG.debug(..., exc_info=True)` |
| `core/updater/lifecycle.py:80` | Enviar a leitura de resultados anteriores para a thread de ficheiros | Passa a exceção a `_previous_results_received`, que a regista | Sem alteração: o erro não é engolido, só reencaminhado |
| `core/updater/lifecycle.py:85` | O mesmo, sem thread de ficheiros | Idem | Sem alteração |
| `core/updater/lifecycle.py:174` | `context_policy.blocked_reason` | Devolve `unknownContext` | ✅ `LOG.debug(..., exc_info=True)` |
| `core/updater/receipts.py:47` | `installer.validate_stage` de um pacote cancelado | Marca o pacote como inválido (`stageValid=False`) | ✅ `LOG.debug(..., exc_info=True)` |
| `core/updater/receipts.py:56` | Enviar a validação do recibo para a thread de ficheiros | Reencaminha para `_accept_install_probe`, que volta a lançar | Sem alteração |
| `core/updater/results.py:146` | Comparar versões (`Version(...) < Version(...)`) | Uma versão ilegível conta como não substituída | Sem alteração: entrada externa, falha esperada |
| `core/updater/windows_files.py:84` | Ler a saída do helper `WindowsFiles.exe` numa thread | Envia uma linha vazia, que termina a sessão do helper | ✅ `LOG.debug(..., exc_info=True)` |
| `core/updater/windows_files.py:124` | `stdin.close()` em `close()` | Limpeza; `close()` também corre no `atexit` | **Silencioso de propósito**: registar durante o encerramento do interpretador é o problema que o código já evita |
| `core/updater/windows_files.py:134` | Esperar ou matar o processo do helper em `close()` | Idem | Silencioso de propósito |
| `core/updater/windows_files.py:137` | Fechar `stdout`/`stderr` em `close()` | Idem | Silencioso de propósito |

Nos dois módulos de contas, o registo usa só o nome do tipo da exceção, como os `LOG.error` existentes, para nunca levar e-mails ou palavras-passe para o `game.log`.

## Resto do cliente (fora de propósito)

Os outros 22 não foram alterados. A maioria são leituras defensivas de objetos do jogo que podem não existir naquele momento (modo de batalha, hangar, veículo) e devolvem `None`, `False` ou um valor neutro:

- `core/battle_capabilities.py`: linhas 27, 41, 48, 54, 125, 172, 196 e 228.
- `core/mod_compatibility.py`: 30, 42, 52 e 87.
- `core/diagnostics.py`: 65 e 80.
- `settings/panel/presenter.py`: 23 e 36.
- `lobby/hangar_marks_of_excellence.py`: 54 e 213.
- `lobby/hangar_preferences.py:58`, `core/vehicle_markers/context.py:19` e `stats/vehinfo.py:344`.
- `core/analytics.py:190`: silencioso de propósito (a telemetria nunca pode afetar o jogo nem escrever em stderr).

Se forem revistos, `battle_capabilities` e `mod_compatibility` são os candidatos a `LOG.debug`, porque decidem que funcionalidades ficam ativas e uma deteção errada é difícil de explicar sem log.
