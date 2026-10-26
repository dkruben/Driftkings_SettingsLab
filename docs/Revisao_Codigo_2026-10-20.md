# Revisão do código: Driftkings_SettingsLab

> Atualização de contexto — 26/10/2026: Os 15 problemas foram registados como corrigidos na revisão original. Esta página mantém essa evidência e as referências de linha da altura. A beta atual é 0.1.3-beta.2 e passou 413 testes core, 27 do painel e 33 do instalador, além das suites Gameface; isto não constitui uma nova auditoria completa de código. Ver o [estado atual](STATUS.md) e o [guia de contribuição](../CONTRIBUTING.md).

**Data:** 20/10/2026 · **Commit:** `b6afb5c` (beta.5)
**Âmbito:** Python do mod (core, updater, settings, battle, lobby, views), GameFace JS, AS3, build tools, instalador C#/Inno e workflows do GitHub.

> **Estado (20/10/2026):**
> - Nº 1–4: corrigidos no commit `e2966f2` (GitHub).
> - Nº 5: resolvido pelo PR #8 (versão mais completa, que substituiu a minha no rebase). Nº 7: commit `88d8d1f`.
> - Nº 6 e 10: corrigidos no commit `801975e` (GitHub).
> - Nº 8 e 9: corrigidos no commit `2ef875f` (GitHub).
> - Nº 11 e 12: corrigidos no commit `7fc4eb2` (GitHub).
> - Nº 13, 14 e 15: corrigidos no commit `179d15f` (GitHub). O SWF foi recompilado; o lock e o helper foram testados no Windows.
> - **Todos os 15 problemas estão corrigidos.** Push feito em 20/10/2026 (`179d15f`). Falta o teste dentro do jogo.
>   - Nº 15: o `-exec ... +` sugerido não serve, porque o `node --check` só verifica o primeiro ficheiro. Usei `xargs -0 -n1`.
> - Os testes passam em Python 3 e 2.7.

Os links apontam para os ficheiros atuais (caminhos em minúsculas); os números de linha referem-se ao commit `b6afb5c`.

Os itens marcados com ✅ foram confirmados à mão no código e, quando aplicável, comparados com `WoT_Tools/wot-src-EU`.

## Testes e validadores: tudo passou

- **Python:** 158 testes OK (settings_panel 25, core 111, installer 22).
- **JavaScript:** os 3 testes OK (`test_flash_text`, `test_gameface`, `test_main_gun`).
- **Validadores:** `validate_build_data`, `validate_locales` e `generate_defaults --check` passaram (31 componentes).

---

## 🔴 Graves: corrigir antes da próxima versão

| # | Onde | Problema | Efeito |
|---|---|---|---|
| 1 | [hangar_preferences.py:121](../mod/res/scripts/client/driftkings/lobby/hangar_preferences.py#L121) | `base.fget(self)` é chamado num `base` que já é o getter: `override` passa `original.fget` às propriedades e `Vehicle.isReadyToFight` é `@property`. ✅ | Cada leitura de `isReadyToFight` lança `AttributeError`, o que parte o carrossel, os validadores pré-batalha e o botão "Batalha". A correção é `base(self, *args, **kwargs)` |
| 2 | [player_ratings.py:273](../mod/res/scripts/client/driftkings/core/player_ratings.py#L273) | Divisão inteira em py2 no EFF (`10 / (avgTier + 2)` e `2 * avgTier / 100`, com `level` inteiro e sem `from __future__ import division`). ✅ | O termo de dano dá 0 nos tiers 9–10 e `2*t/100` dá sempre 0, por isso EFF/xEFF e as cores ficam errados. A correção é usar `10.0` e `100.0` |
| 3 | [loader.py:122](../mod/res/scripts/client/driftkings/settings/loader.py#L122) | Em py2, a variável `name` da list comprehension sobrepõe-se à variável `name` do ciclo `for name in os.listdir(...)`. ✅ | A linha 124 adiciona o nome da última secção em vez do nome do perfil, por isso os perfis clonados não aparecem e surgem entradas falsas que dão erro ao selecionar |
| 4 | [profiles.py:72-75](../mod/res/scripts/client/driftkings/settings/panel/profiles.py#L72-L75) | O comentário diz "keep a bounded backup", mas o código chama `store.write()` (reescreve o ficheiro) em vez de `store.backup()`. ✅ | Apagar ou renomear um perfil não deixa nenhum `.bak` recuperável |
| 5 | [vehinfo.py:82-152](../mod/res/scripts/client/driftkings/stats/vehinfo.py#L82-L152) | 4 downloads `urllib2.urlopen(timeout=10)` síncronos no thread principal | O cliente congela até ~40 s ao arrancar se o static.modxvm.com estiver lento ou em baixo. `httplib.HTTPException` não é `IOError`, por isso escapa ao `loadJsonData` e o cache local não chega a ser carregado |
| 6 | [results.py:283-329](../mod/res/scripts/client/driftkings/core/updater/results.py#L283-L329) | As pastas `download-*` (com `result.json`) nunca são apagadas e o `scan()` volta a verificá-las contra os ficheiros atuais | Depois de v2→v3, a v2 passa a aparecer como "update falhado". O cache cresce até ~128 MB por update, o limite de `[:100]` passa a ignorar stages ao acaso e `lastInstallResult = reports[-1]` ([receipts.py:17](../mod/res/scripts/client/driftkings/core/updater/receipts.py#L17)) é escolhido pela ordem dos nomes `mkdtemp` e não pela data |

## 🟠 Médios

| # | Onde | Problema |
|---|---|---|
| 7 | [battle_preferences.py:53-55, 161-166](../mod/res/scripts/client/driftkings/battle/battle_preferences.py#L53-L55) | `battle_clock.start()` corre em cada `startGUI`, mas `stop()` só corre com `ENABLED` e `IN_BATTLE` ligados. **A:** com o relógio desligado, `active` fica `True` e, ao ligá-lo depois, nunca mais aparece até reiniciar o cliente. **B:** desligado a meio da batalha, o `CyclicTimerEvent` de 1 s continua no hangar, porque `callbacks.endBattle` só cancela owners `Driftkings.battle.*` |
| 8 | [sniper_camera.py:42-65, 117](../mod/res/scripts/client/driftkings/battle/sniper_camera.py#L42-L65) | `ZoomController.updateSettings()` só corre no import e não está ligado a `onModSettingsChanged`. Alterar `DISABLE_CAM_AFTER_SHOT`, a latência ou o skip-clip só tem efeito depois de reiniciar |
| 9 | [json_reader.py:138-172](../mod/res/scripts/client/driftkings/common/config/json_reader.py#L138-L172) | `json_file_write` trunca o ficheiro no sítio (sem ficheiro temporário + rename) e o `json_loads` no modo save não está protegido. Um crash a meio da escrita deixa o cache das marcas vazio, e a partir daí cada `save()` lança `ValueError` |
| 10 | [windows_files.py:157-161](../mod/res/scripts/client/driftkings/core/updater/windows_files.py#L157-L161) e [fog_package.py:79,146](../mod/res/scripts/client/driftkings/core/fog_package.py#L79) | Cada sessão cria um `mkdtemp` com uma cópia de `Driftkings.WindowsFiles.exe` (ou pastas `session-<pid>`) que nunca é apagada |
| 11 | [battle_statistics.py:393-401](../mod/res/scripts/client/driftkings/battle/battle_statistics.py#L393-L401) | O hook de `CompoundAppearance.prerequisites` assume `(typeDescriptor, vehicleID)`, mas o jogo usa `(vID, vInfo, renderMode=None)`. Os veículos que entram tarde não são registados por este caminho. A chamada nativa continua a funcionar |
| 12 | [FogPackage.cs:190-194](../installer/source/fogpackage.cs#L190-L194) | `process.MainModule` é chamado sem verificar `HasExited` nem apanhar `Win32Exception`/`InvalidOperationException`. Um WoT elevado ou já terminado faz o fog falhar. Falha de forma segura: não danifica ficheiros |

## 🟡 Menores

| # | Onde | Problema |
|---|---|---|
| 13 | [SixthSenseUI.as:276](../flash_source/battle/src/driftkings/battle/components/sixth_sense/sixthsenseui.as#L276) | `onResizeHandle` nunca é chamado, porque não há override de `onResized()`, por isso o ícone fica descentrado se a resolução mudar. Nas linhas 160-161, `finish` é atribuído antes de `begin`, o que dá um ponto final errado. A correção é trocar a ordem dessas linhas |
| 14 | [WindowsFiles.cs:66-72](../installer/source/windowsfiles.cs#L66-L72) | O "lock" das pastas com `FILE_READ_ATTRIBUTES` (0x80) não impede rename/delete, ao contrário do que diz o comentário. É uma janela TOCTOU que só um processo do mesmo utilizador conseguiria explorar |
| 15 | [python-package.yml:55](../.github/workflows/python-package.yml#L55) | `find ... -exec node --check {} \;` nunca falha o passo, mas com `+` já falharia. Hoje o `npm run lint` apanha os mesmos erros mais à frente |

---

## ✅ Verificado e sem problemas

- **Updater:**
  - A verificação Ed25519 é canónica, rejeita `y >= p` e `S >= Q`, e `TRUSTED_KEYS` não está vazio.
  - Não há path traversal a partir dos manifests (`safe_relative` e validação dos membros do zip).
  - Os limites de tamanho e hash no transport e no staging estão corretos, assim como os generation guards nos callbacks.
  - A store das settings faz replace atómico e tem journal de transação.
- **Instalador C#/Inno:**
  - Só escreve em `mods/<ver>/` e `mods/configs/driftkings/cache/...` e rejeita reparse points.
  - Verifica os backups por hash antes do rollback, e o journal schema-2 tem ownership correto.
  - O reset-config faz backup antes de mexer.
- **Publicação:** volta a verificar os artefactos, SHA256SUMS, a assinatura do `release.json`, o checkout limpo e o commit.
- **Workflows:** permissões só de leitura, os secrets só passam por env e o texto da release passa por um heredoc Python.
- **GameFace:**
  - Não há XSS: o `innerHTML` é parseado numa div separada com allow-list (`b/i/u/font/img` locais) e os nomes e contas usam `textContent`.
  - Os listeners, timers e observers são todos removidos no `dispose`.
  - Os comandos do modelo batem com os handlers Python.
- **AS3:** todos os componentes libertam listeners, timers, Loaders e Tweens no dispose.
- **Hooks battle/lobby:** a maioria tem assinaturas que batem com o `wot-src-EU`, e os callbacks de batalha são cancelados via `callbacks.endBattle`.

### Notas (não contadas como defeitos)
- `HangarEfficiency/efficiency.js` não está no catálogo do bootstrap e nada em Python produz `DriftkingsHangarEfficiency`, por isso parece código morto.
- Em `DispersionTimerUI.as` e `FlightTimerUI.as` há listeners `Event.RESIZE` num Sprite que nunca os recebe. É inofensivo.
- Falta confirmar se `AppId={code:InstallationId}` no Inno funciona numa instalação limpa sem entrada de desinstalação anterior.

---

## Ordem de correção sugerida

1. **Correções rápidas, de uma linha:** nº 1, 2, 3 e 4.
2. **Impacto direto no jogador:** nº 5 (arranque bloqueado) e nº 7 (relógio de batalha).
3. **Limpeza de cache e pastas temporárias do updater:** nº 6 e 10.
4. **Restantes:** nº 8, 9 e 11–15.
