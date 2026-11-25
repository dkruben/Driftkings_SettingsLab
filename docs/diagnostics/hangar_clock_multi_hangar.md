# Diagnóstico do HangarClock em hangares múltiplos (CT)

Data dos testes: 2026-11-18. Versão: `0.1.7-beta.2`. Cliente: World of Tanks Common Test `v.2.4.2.0 #996`, realm CT, client `2660091`.
Branch: `develop`, commit base `bc86acc9`. As alterações de diagnóstico estão na árvore de trabalho, sem commit.

## 1. Objetivos

- Observar o ciclo de vida do HangarClock (`RandomHangar`, `ClockView`, plugin nativo em `UserMissionsPresenter`) nos modos do hangar aleatório.
- Verificar criação, visibilidade, destruição e ausência de duplicações.
- Identificar a compatibilidade com Frontline, Onslaught e Black Signal.

Fora de âmbito: alterar o HangarClock, adicionar suporte a hangares específicos ou alterar a apresentação visual.

## 2. Arquitetura atual do HangarClock

- `gameface/lobby/main.py` (`install_clock_gameface`) faz override de `RandomHangar._getChildComponents`, `_onShown` e `_onHidden`, acrescentando um filho `ClockView` por instância de `RandomHangar`.
- `ClockView` publica o payload no layout Gameface `mods/driftkings/main/clock`. O visual e o JavaScript (`clock.js`, `clock.css`, `clock.html`, `clock_plugin.js`) não foram alterados.
- O transporte nativo regista um descritor em `UserMissionsPresenter._onLoading` (slot `resource=35`) e remove-o em `_finalize`.
- `components/main.py` faz `init()` (instala a integração) e `fini()` (para o controlador).
- A visibilidade depende de `controller.active`, de `_onShown`/`_onHidden` do hangar e das configurações `GLOBAL.ENABLED` e `MAIN.CLOCK`.

Não há lógica específica de modo. Não foi identificado defeito reproduzível que justifique uma alteração arquitetural.

## 3. Instrumentação implementada

Módulo: `mod/res/scripts/client/driftkings/gameface/lobby/clock_diagnostics.py`.

- `ENABLED = False` por defeito. Quando desativado, nada é instalado nem registado. O código foi preservado nesta fase.
- Prefixo de log `[Driftkings][ClockDiag]`, uma linha `session.started` por arranque do cliente.
- Identificadores sequenciais por instância (`RandomHangar#n`, `ClockView#n`, `UserMissionsPresenter#n`) via `WeakKeyDictionary`.
- Registos apenas de mudanças de estado (`changed`), sem registos por segundo.
- `install_lifecycle` acrescenta apenas `RandomHangar._onLoading` e `_finalize`, para gerir o listener `PrebattleEvent.SWITCHED` e registar criação e destruição. Os listeners são removidos em `_finalize`.
- Chamadas de diagnóstico isoladas (`guarded`, `try`/`except`): uma falha de diagnóstico não interrompe o relógio.
- Eventos: `session.started`, `children.attached`, `hangar.loaded`, `hangar.visibility`, `mode.switched`, `hangar.destroyed`, `view.loaded`, `view.payload`, `view.destroyed`, `plugin.registered`, `plugin.removed`.
- O registo do plugin inclui `executed=unobserved-from-python`. Não prova a execução do JavaScript.

Alterações em `main.py` estão cobertas pela baseline aprovada (`approved_revisions`, entrada `main.py`, hash `f8e98462…dbf`). A baseline histórica é `a4dd68…78`, commit `57881e7b`. A alteração de `main.py` é apenas aditiva (50 linhas, nenhuma removida).

## 4. Build utilizada

- Pacote: `Driftkings_HangarClock_Diagnostics_CT_0.1.7-beta.2_CT2.4.2.0-996_772a9184.wotmod`.
- Build isolada em `C:\dkd\src` (cópia da árvore com `ENABLED = True` apenas na cópia), com `--isolated-output`.
- Experiência de build: `20261118T010212Z-772a9184`.
- Pacote e cópia de build mantidos enquanto os artefactos essenciais estiverem preservados.

## 5. SHA-256

- Pacote de diagnóstico instalado e testado: `12fc6cee47187e96208427b15393ea8ed36d370e388a85ad6118215cd86a0135`.
- Pacote anterior à instalação de diagnóstico (cópia de segurança): `f1735c37f3d1bf0fb14f487cac88eccf471fb447f24e3ebb6b70c2e6706f97aa`. Este hash não está documentado noutro ficheiro do repositório.

## 6. Resumo cronológico dos eventos

Fonte: `HangarClock_CT_Diagnostics.log` (51 linhas, todas `ClockDiag`, sem erros nem exceções). Contagem: `session.started` 1, `children.attached` 4, `hangar.loaded` 4, `view.loaded` 4, `view.payload` 12, `hangar.visibility` 7, `mode.switched` 5, `view.destroyed` 4, `hangar.destroyed` 3, `plugin.registered` 4, `plugin.removed` 3.

| Hora (2026-11-18) | Evento | Observação |
|---|---|---|
| 01:04:49 | `session.started` | Início da sessão `20261118T010445` |
| 01:05:14 | `children.attached` / `view.loaded` | `RandomHangar#1`, `ClockView#2` |
| 01:05:15 | `plugin.registered` | `UserMissionsPresenter#3`, slot 35 |
| 01:05:15 | `hangar.loaded` | Modo `RandomEntity` |
| 01:05:17 | `hangar.visibility` shown=True | `visible=True` |
| 01:05:29 | `mode.switched` | Modo `StoryModeEntity` |
| 01:05:30 | `hangar.visibility` shown=False, `view.destroyed`, `plugin.removed`, `hangar.destroyed` | `RandomHangar#1` destruído |
| 01:05:37 | `children.attached` / `view.loaded` | `RandomHangar#4`, `ClockView#5` |
| 01:05:38 | `plugin.registered`, `hangar.loaded` | `UserMissionsPresenter#6`, modo `StrongholdBrowserEntity` |
| 01:05:38 | `hangar.visibility` shown=True | `visible=True` |
| 01:05:43 | `mode.switched` | Modo `RandomEntity` |
| 01:05:56 | `mode.switched`, `hangar.visibility` shown=False, `view.destroyed`, `plugin.removed`, `hangar.destroyed` | `RandomHangar#4` destruído, modo `TrainingIntroEntity` |
| 01:06:00 | `children.attached`, `plugin.registered`, `view.loaded` | `RandomHangar#7`, `ClockView#9`, `UserMissionsPresenter#8`, modo `TrainingIntroEntity` |
| 01:06:01 | `hangar.visibility` shown=True | `visible=True` |
| 01:06:13 | `hangar.visibility` shown=False, `plugin.removed`, `view.destroyed`, `hangar.destroyed` | `RandomHangar#7` destruído |
| 01:06:20 | `children.attached`, `view.loaded`, `plugin.registered`, `hangar.loaded` | `RandomHangar#10`, `ClockView#11`, `UserMissionsPresenter#12`, modo `TrainingIntroEntity` |
| 01:06:20 | `mode.switched` | Modo `RandomEntity` |
| 01:06:21 | `hangar.visibility` shown=True | `visible=True` |
| 01:09:08 | `view.payload` controllerActive=False, `view.destroyed` | Encerramento do cliente. Sem `plugin.removed` nem `hangar.destroyed` para `RandomHangar#10` |

## 7. Modos efetivamente observados

Modos registados em `mode.switched` ou `hangar.loaded`:

- `RandomEntity` (hangar aleatório normal): observado.
- `StoryModeEntity`: observado.
- `StrongholdBrowserEntity`: observado.
- `TrainingIntroEntity`: observado.
- **Frontline: não observado.** O modo não estava disponível no CT.
- **Onslaught: não observado.** O modo não estava disponível no CT.
- **Black Signal: não observado.** O modo não estava disponível no CT, e não foi encontrado nas fontes EU/CT.

## 8. Resultados dos testes

Resultados do repositório (`develop`, árvore com as alterações de diagnóstico):

- Suite runtime: 816 testes, OK.
- Suite build: 294 testes, OK, 1 ignorado.

Resultados no CT (log acima):

- Quatro instâncias de `RandomHangar`, quatro de `ClockView`, quatro registos de plugin. Nenhuma duplicação simultânea observada: cada `ClockView` aparece após o `RandomHangar` correspondente e foi destruída antes do seguinte, exceto a última.
- Visibilidade `visible=True` nas quatro instâncias quando o hangar foi mostrado.
- Sem erros, exceções ou `could not` no log.

Pontos que exigem leitura cuidadosa:

- O `RandomHangar` foi destruído e recriado em todas as transições observadas (`RandomHangar#1` após `StoryModeEntity`, `#4` após `TrainingIntroEntity`, `#7` após o hangar mostrado). Assim, o log não suporta a afirmação de transições de modo sem recriação. A recriação ocorre pelo menos ao sair do hangar aleatório para outros ecrãs. A distinção entre "mudança de modo" e "troca de ecrã" não foi verificada.
- A última instância (`RandomHangar#10`) não teve destruição completa: faltam `plugin.removed` e `hangar.destroyed`, porque o cliente foi encerrado. Não há prova de destruição completa para este caso.

## 9. Limitações e riscos pendentes

- Frontline, Onslaught e Black Signal não foram testados. Não há prova de compatibilidade com estes modos.
- O log não observa a execução do `clock_plugin.js`; apenas o registo do descritor no Python.
- A visibilidade e o payload foram observados como estados do Python. A renderização real no ecrã não foi confirmada por esta instrumentação.
- A destruição não foi observada até ao fim na última instância.
- A afirmação "sem recriação obrigatória" da síntese anterior não é suportada pelo log. Esta documentação regista apenas o que o log mostra.
- O pacote de diagnóstico utiliza o número de versão interno `0.1.7-beta.2`, igual ao pacote normal. A identificação é feita pelo hash.

**Conclusão:** a implementação atual funciona nos cenários observados. Não foi identificado defeito que justifique uma alteração arquitetural. A compatibilidade com hangares especiais permanece por validar. Não se declara suporte universal multi-hangar.

## 10. Procedimento para repetir o diagnóstico

1. Confirmar `ENABLED = True` apenas na cópia de build (nunca na árvore de desenvolvimento). Ver `clock_diagnostics.py`.
2. Construir numa cópia com `build_tools/compiler.py --mode debug --channel beta --version 0.1.7-beta.2 --keep-source-version --isolated-output` e as ferramentas explícitas (ver `build_tools/toolchain.py`).
3. Verificar o `.pyc` empacotado de `clock_diagnostics.py` (`ENABLED` atribuído a `True`) e o `meta.xml` (`0.1.7-beta.2`).
4. Fazer cópia de segurança do `driftkings.wotmod` instalado no CT, verificar o hash e instalar o pacote de diagnóstico com o CT encerrado.
5. Iniciar o CT (`mods/2.4.2.0 Common Test/`), percorrer: hangar normal, Frontline, Onslaught, regresso ao hangar normal, transições consecutivas, saída do hangar e Black Signal (se disponível).
6. Recolher as linhas `[Driftkings][ClockDiag]` de `C:\Games\World_of_Tanks_CT\game.log`, filtrar, verificar que não há dados pessoais, e arquivar com SHA-256.
7. Restaurar o pacote original a partir da cópia de segurança, confirmar o hash e o encerramento do cliente.

Nota: `game.log` contém também as linhas do cliente. O filtro `ClockDiag` é o mesmo usado para o ficheiro arquivado.

## 11. Trabalhos futuros (pendentes)

1. Testar Frontline, Onslaught e Black Signal quando estiverem disponíveis no cliente.
2. Confirmar o host Gameface usado por cada modo.
3. Investigar a execução efetiva de `clock_plugin.js`.
4. Avaliar um mecanismo de confirmação de renderização JavaScript.
5. Investigar hangares históricos apenas através de fontes verificáveis.
6. Reavaliar a necessidade de adaptadores multi-hangar apenas depois de encontrar um defeito reproduzível.

O projeto Driftkings UI Framework (DKUI) é independente e está em planeamento. Não foi iniciada a sua implementação.
