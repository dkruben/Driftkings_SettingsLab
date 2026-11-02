# Exceções genéricas silenciosas

Revisão de 2026-11-02, só de leitura: nenhum código foi alterado. Os caminhos partem de `mod/res/scripts/client/driftkings/`.

## Método

Um analisador AST percorreu os módulos Python do cliente e listou os `except Exception`, `except StandardError`, `except BaseException` e `except:` cujo corpo não chama nenhum registo (`LOG.*`, `logging`, `print`) nem volta a lançar o erro. Encontrou **41**; **19** estão nas áreas pedidas (`core/updater`, `core/accounts.py`, `components/account_manager.py`). Cada um foi lido no contexto, incluindo o que acontece ao código de erro depois.

Um `except` silencioso nem sempre é um defeito: muitos convertem a exceção num código de erro que o chamador regista. A recomendação abaixo distingue esses casos dos que perdem a causa.

## Áreas pedidas

| Ficheiro:linha | O que protege | Situação | Recomendação |
| --- | --- | --- | --- |
| `components/account_manager.py:58` | Decifrar `accounts.manager` (`wg_ucpdata` + zlib + JSON); em falha tenta ler JSON simples | Fallback intencional para ficheiros antigos não cifrados. Se o JSON também falhar, o `except` exterior regista `LOG.error` | `LOG.debug` com `type(error).__name__` (nunca o conteúdo: tem palavras-passe). Ajuda a perceber se um ficheiro cifrado deixou de abrir |
| `core/accounts.py:98` | `store.write_accounts()` ao guardar contas | `write_accounts` já regista `LOG.error` nas suas falhas; aqui só chega um erro inesperado (por exemplo `AttributeError`), que vira `AccountError('errorSave')` sem causa | **`LOG.warning`** com `exc_info` ou o nome do tipo, sem dados das contas |
| `core/updater/checking.py:47` | `checker.check(...)` ao pedir a verificação de atualizações | `completed(None, 'checkError')` regista `LOG.warning('Update check failed: checkError')`, mas perde o traceback | **`LOG.warning(..., exc_info=True)`**: um erro de programação no checker fica indistinguível de uma falha de rede |
| `core/updater/context.py:46` | Ler o estado do hangar/replay para decidir se pode instalar | Devolve `unknownContext`, que bloqueia a instalação (falha fechada) | `LOG.debug` com `exc_info`; corre com frequência, por isso não `warning` |
| `core/updater/downloader.py:178` | Iniciar o download (`transport.stream`) | Aborta o ficheiro parcial e reporta `networkError`; o erro de programação perde-se | **`LOG.warning(..., exc_info=True)`** antes de `completed` |
| `core/updater/https_transport.py:181` | `response.close()` depois do pedido | Marca `networkError` se ainda não houver erro; o pedido principal já regista `LOG.exception` | `LOG.debug`; aceitável como está |
| `core/updater/https_transport.py:189` | `sink.abort()` ao cancelar ou falhar | Converte em `stagingError` | `LOG.warning`: um ficheiro temporário que não se apaga merece ficar no log |
| `core/updater/https_transport.py:244` | Criar o transporte HTTPS (SSL, CAs, verificação do hostname) | Devolve `UnavailableTransport` (falha fechada, correta) sem dizer porquê; o utilizador só vê que as atualizações não estão disponíveis | **`LOG.warning`** com o tipo do erro: é a única pista quando um cliente não tem SSL ou CAs |
| `core/updater/installation.py:196` | Confirmar que o instalador preparado corresponde ao bilhete e ao processo atuais | Devolve `False` (não reinicia para instalar) | `LOG.debug` com `exc_info` |
| `core/updater/lifecycle.py:80` | Enviar a leitura de resultados anteriores para a thread de ficheiros | Passa a exceção a `_previous_results_received`, que a trata | Nenhuma: o erro não é engolido, só reencaminhado |
| `core/updater/lifecycle.py:85` | O mesmo, sem thread de ficheiros | Idem | Nenhuma |
| `core/updater/lifecycle.py:174` | `context_policy.blocked_reason` | Igual a `context.py:46` | `LOG.debug` |
| `core/updater/receipts.py:47` | `installer.validate_stage` de um pacote cancelado | Marca o pacote como inválido (`stageValid=False`) | `LOG.debug` com o tipo do erro, para explicar porque um pacote não é retomado |
| `core/updater/receipts.py:55` | Enviar a validação do recibo para a thread de ficheiros | Reencaminha para `_accept_install_probe`, que volta a lançar | Nenhuma |
| `core/updater/results.py:146` | Comparar versões (`Version(...) < Version(...)`) | Uma versão ilegível conta como não substituída | Nenhuma, ou `LOG.debug`: entrada externa, falha esperada |
| `core/updater/windows_files.py:82` | Ler a saída do helper `WindowsFiles.exe` numa thread | Envia uma linha vazia, que o chamador trata como fim/erro do helper | `LOG.debug` |
| `core/updater/windows_files.py:120` | `stdin.close()` em `close()` | Limpeza; `close()` também corre no `atexit` | **Manter silencioso**: registar durante o encerramento do interpretador é o problema que o comentário seguinte descreve |
| `core/updater/windows_files.py:130` | Esperar ou matar o processo do helper em `close()` | Idem | Manter silencioso |
| `core/updater/windows_files.py:133` | Fechar `stdout`/`stderr` em `close()` | Idem | Manter silencioso |

### Prioridade

1. **`LOG.warning` com `exc_info=True`:** `checking.py:47`, `downloader.py:178`, `https_transport.py:244` e `accounts.py:98`. São os pontos em que um erro de programação fica igual a uma falha esperada e o log não ajuda a diagnosticar.
2. **`LOG.warning` sem traceback:** `https_transport.py:189`.
3. **`LOG.debug`:** `account_manager.py:58`, `context.py:46`, `lifecycle.py:174`, `installation.py:196`, `receipts.py:47`, `windows_files.py:82`, `https_transport.py:181` e opcionalmente `results.py:146`.
4. **Sem alteração:** `lifecycle.py:80`/`85` e `receipts.py:55` (reencaminham o erro) e as três limpezas de `windows_files.close()`.

Nos dois módulos de contas, o registo deve continuar a usar só o nome do tipo da exceção, como os `LOG.error` existentes, para nunca levar e-mails ou palavras-passe para o `game.log`.

## Resto do cliente

Os outros 22 não foram analisados em detalhe. A maioria são leituras defensivas de objetos do jogo que podem não existir naquele momento (modo de batalha, hangar, veículo) e devolvem `None`, `False` ou um valor neutro:

- `core/battle_capabilities.py`: linhas 27, 41, 48, 54, 125, 172, 196 e 228.
- `core/mod_compatibility.py`: 30, 42, 52 e 87.
- `core/diagnostics.py`: 65 e 80.
- `settings/panel/presenter.py`: 23 e 36.
- `lobby/hangar_marks_of_excellence.py`: 54 e 213.
- `lobby/hangar_preferences.py:58`, `core/vehicle_markers/context.py:19` e `stats/vehinfo.py:344`.
- `core/analytics.py:190`: silencioso de propósito (a telemetria nunca pode afetar o jogo nem escrever em stderr).

Se forem revistos, `battle_capabilities` e `mod_compatibility` são os candidatos a `LOG.debug`, porque decidem que funcionalidades ficam ativas e uma deteção errada é difícil de explicar sem log.
