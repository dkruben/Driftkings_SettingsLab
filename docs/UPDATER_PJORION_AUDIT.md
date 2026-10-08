# Auditoria de updater e PJOrion — Fase 1

Data: 2026-10-08. Base: commit `5ef8583`.

Este relatório precede a implementação pedida. Distingue observações locais,
decisões de arquitetura e validações ainda necessárias. Não houve alteração de
código funcional, execução do ofuscador, deployment ou publicação de release.
A suite Python foi executada novamente: **524 testes, todos verdes**.

## 1. Arquitetura atual relevante

`source/scripts/client/gui/mods/mod_Driftkings.py` instancia um único `Core`;
`init()` chama `start()` e `fini()` chama `stop()`.

`Driftkings/core/__init__.py` importa componentes por `importlib.import_module`
usando `component_list.COMPONENTS`, declara os hooks, inicia serviços, inicializa
componentes e inicia `Contexts`. Os serviços atuais são keyboard, callbacks,
WindowViews, BattleViews e SettingsService. No encerramento, Contexts termina
primeiro; componentes e serviços terminam em ordem inversa.

`Driftkings/settings/__init__.py` contém o serviço de integração com o cliente.
`settings/service.py` contém o acesso partilhado e notificações de settings.
Não são dois pontos de entrada. A UI usa o SettingsAPI, Registry, Presenter,
EditSession, TemplateAdapter e ConfigStore existentes.

`ui/gameface.py` é a integração Gameface existente; `views` contém os registos
e controladores do cliente. Nada disso deve ter um lifecycle paralelo de updater.

## 2. Comparação conceptual com Battle Observer

Referência local lida: `WoT_Tools/battle_observer-master/mod/res/scripts/client/`
`armagomen/battle_observer/updater/__init__.py` e `utils/async_request.py`.

O updater observado verifica em login/lobby com intervalo de duas horas,
consulta a API GitHub, usa `BigWorld.fetchURL` com timeout de 15 segundos,
descarrega ZIP por WebDownloader, extrai novos ficheiros e oferece restart.
Subscreve diretamente appLoader e descarrega um cleanup_launcher.exe externo.

Para DriftKings aproveitam-se apenas os conceitos de check espaçado,
notificação discreta, staging e restart. Não copiar código; não herdar comparação
numérica limitada, extração de ZIP, subscrição duplicada nem download de helper.
O intervalo será quatro horas; o payload será apenas o WOTMOD unificado.

## 3. Entrada exata do UpdaterService no Core

Criar `Driftkings/core/updater/__init__.py` com `UpdaterService`.
Na construção dos serviços default de `Core.__init__`, instanciá-lo **depois de
SettingsService**, com dependências explícitas para settings, callbacks e contexto.
O Core continua a iniciar/parar o serviço e a entregar contextos normalmente.
Serviços fornecidos explicitamente pelos testes não devem ser alterados.

As responsabilidades Versioning, Manifest, Checker, Downloader, Installer e State
serão módulos internos desse serviço, não serviços independentes nem entry points.

## 4. Eventos e contextos reutilizados

`Contexts.start()` já subscreve `onGUISpaceEntered` e `onGUISpaceLeft`, entrega
o contexto atual e evita entradas duplicadas. Serviços com `onContextEntered`
entram automaticamente na lista de owners.

Usar `onContextEntered(space)` e `onContextLeft(space)` do updater. Check automático
apenas em LOGIN/LOBBY quando o intervalo expirar; check manual ignora o intervalo.
Uma operação pendente bloqueia outra. Não haverá polling por frame ou novo loop
permanente. Usar CallbackService para entregas/callbacks no thread do cliente.
Cancelar callbacks e invalidar resultados tardios em `stop()`.

Segurança de instalação exige LOBBY confirmado, ausência de arena, replay não
loading/não playing e contexto completo. BattleCapabilities é consultado sem
alterar a sua lógica. Ausência de informação bloqueia agendamento.

## 5. Fonte recomendada das releases

GitHub Releases do repositório `dkruben/Driftkings_SettingsLab`.
API centralizada: `https://api.github.com/repos/dkruben/Driftkings_SettingsLab/releases`.
Selecionar releases publicadas e os assets `release.json` e `Driftkings.wotmod`.
Não usar HTML nem confiar no ordenamento da lista para comparar versões.

O endpoint de listagem permite considerar prereleases para beta; `/latest` sozinho
não resolve essa política. Limitar páginas/resultados. `draft` é rejeitado.
Endpoint alternativo oficial poderá ser configurado na política de distribuição,
não por campos arbitrários do manifest nem por preferências pessoais adicionais.

Referência primária:
https://docs.github.com/en/rest/releases/releases?apiVersion=latest

## 6. Contrato definitivo proposto de release.json, schema 1

Campos obrigatórios:

| Campo | Contrato |
| --- | --- |
| schema | inteiro exatamente 1; booleanos rejeitados |
| version | SemVer válida, igual à VERSION que originou o artefacto |
| channel | stable ou beta |
| gameVersion | versão numérica normalizada do WoT, quatro segmentos |
| file | literal Driftkings.wotmod, sem diretórios |
| size | inteiro positivo, máximo 64 MiB; booleanos rejeitados |
| sha256 | exatamente 64 caracteres hexadecimais |
| download | HTTPS absoluto, host autorizado e sem credenciais |

Opcionais: `minGameVersion`, `maxGameVersion`, `changelog`.
Sem limites explícitos, exigir igualdade com gameVersion. Limites devem ser
válidos, ordenados e conter gameVersion; comparar tuplos numéricos com quatro
segmentos. Não reinterpretar a versão do WoT como SemVer de três segmentos.
`changelog` é lista de até 50 strings, até 500 caracteres cada e 16 KiB no total.
Manifest limitado a 64 KiB; campos desconhecidos rejeitados em schema 1.
O manifest não pode definir comandos, paths locais, helper ou argumentos.

Exemplo de forma, sem fingir que já existe uma release ou hash:

```text
schema: 1
version: VERSION central
channel: stable ou beta, coerente com a versão
gameVersion: build_config.game_version normalizada
file: Driftkings.wotmod
size: tamanho do WOTMOD final validado
sha256: SHA-256 desse mesmo WOTMOD
download: URL oficial do asset dessa release
changelog: texto limitado
```

## 7. Estratégia de versionamento e versão do jogo

Fonte única do produto: `Driftkings/__init__.py`, atualmente `VERSION = '0.1.0'`.
`build_unified.package_version()` lê-a por AST, mas atualmente só aceita X.Y.Z;
precisa de aceitar a mesma gramática SemVer do runtime, sem duplicar VERSION.

Comparar major/minor/patch numericamente e prerelease segundo SemVer: beta.2 antes
de beta.10, beta antes de rc, prerelease antes de versão final igual. Identificadores
numéricos não aceitam zeros iniciais; build metadata não altera precedência.
Stable aceita só finais; beta considera beta/rc e finais, escolhe a maior compatível.
Nunca downgrade automático. Development não é selecionado automaticamente.

Build: `build_data/build_config.json` aponta para 2.4.0.2.
Referência `sources/version.xml`: `v.2.4.0.2 #966`; `.version_name`: 2.4.0.5473.
São valores diferentes; o segundo não substitui a versão do diretório de mods.
Runtime: normalizar `helpers.getClientVersion()`, que lê version.xml por ResMgr;
remover prefixo `v.` e sufixo de build apenas pela gramática esperada.
Versão desconhecida ou divergente bloqueia instalação, com informação na UI.

## 8. Estratégia de download

Auditei `web/cache/web_downloader.py` e `gui/shared/RemoteDataDownloader.py` da
referência do cliente. WebDownloader entrega o conteúdo completo em memória;
a interface exposta não oferece streaming, percentagem ou validação de redirects.
Não adotá-lo cegamente para cumprir limites durante a transferência.

Proposta: adaptador de transporte interno ao updater, uma operação de cada vez,
streaming em chunks num worker gerido, HTTPS com certificado validado, timeout,
limite antes e durante leitura e validação de **cada** redirect. Resultados passam
para o cliente pelos callbacks existentes; worker não chama APIs UI/BigWorld.
Verificar disponibilidade real de ssl/urllib2 no runtime WoT antes de selecionar
esse backend. O Python 2.7.18 local não prova a presença deles no jogo.

Hosts oficiais permitidos serão centralizados, incluindo hosts de assets GitHub
necessários; rejeitar HTTP mesmo num redirect. Proibir userinfo e URLs locais.
Se não houver backend que cumpra TLS/redirects/limites, falhar de forma informativa,
sem recorrer a transporte inseguro. Check falhado é WARNING e não bloqueia boot.

Escrever `.download`, contar bytes e SHA-256 incremental; só publicar `.ready`
após igualdade de tamanho/hash e validação do package. Cancelamento remove parcial.
Não simular percentagens; mostrar percentagem só a partir dos bytes transferidos.

## 9. Staging e preferências

Runtime: `mods/configs/Driftkings/cache/update/`, com nomes fixos:
`Driftkings.wotmod.download`, `Driftkings.wotmod.ready`, `release.json` e resultado
local de instalação. Nenhum diretório é recebido do manifest remoto.
Metadados de lastCheck ficam nessa cache, separados das configs de componentes.

Adicionar apenas autoCheckUpdates e updateChannel à página existente do sistema.
Usar o ConfigStore já usado pela página, em `.settings/dk_settings.json`, mantendo
as preferências existentes e sem migrations novas. Estado/progresso/erros não
entram em perfis. O serviço funciona com a janela fechada; a UI observa o estado.

## 10. Substituição do WOTMOD com WoT aberto

Package instalado observado: `C:/Games/World_of_Tanks_EU/mods/2.4.0.2/Driftkings.wotmod`.
Não foi encontrado processo WorldOfTanks no momento da inspeção.
**Não está comprovado que o WOTMOD montado possa ser substituído em runtime.**
As referências Python não mostram o comportamento de locking do mount nativo.
A extração consultada contém os módulos de rede/replay/helpers citados; não contém
uma implementação Python completa que prove a política Windows do motor.
Não inferir que a ausência de um módulo prova a inexistência da funcionalidade.

Não haverá replace do package ativo com o WoT aberto. Também não se assume que
`Core.start()` corre antes de o arquivo estar montado. Um teste de lock/replace
com cópia de ensaio será obrigatório; não experimentar sobre o package instalado.

## 11. Helper externo

Para aplicar automaticamente com nome fixo após a saída, a opção conservadora
é um helper DriftKings mínimo, sem rede, incluído com source e build controlado.
A necessidade absoluta de C face a A/B ainda depende da prova do mount; não está
demonstrada nesta auditoria. Sem prova de alternativa segura, não prometer B puro.

Proposta caso C se confirme: helper Windows nativo, com argumentos locais validados,
abre handle do processo pai **antes** de este sair, espera a sua terminação e só
então instala. Sem shell, comandos, extração, rede ou download de executável.
O WGC pode relançar depressa: coordenação com restart deve ser testada; se não
puder garantir exclusão com novo WoT, adiar a instalação e preservar READY.
Não invocar restart enquanto o helper não confirmar preparação segura.

O restart funcional continua a ser `SettingsWindowController.restart()`, que
valida lobby/arena, fecha a janela, guarda preferências, notifica WGC e chama
`BigWorld.restartGame()`. O Presenter terá de admitir a razão updater mediante
esse fluxo e as mesmas proteções, sem criar outro mecanismo de restart.

## 12. Rollback e atomicidade

Destino fixo sob mods/<gameVersion>/Driftkings.wotmod, validado localmente por
identidade de meta.xml e unicidade do package. Caminhos virtuais de `__file__`
não bastam para identificar o arquivo instalado. Ambiguidade bloqueia instalação.

Depois da saída: revalidar staged, colocar cópia temporária no mesmo volume do
destino, flush, conservar o atual como `.old` e usar replace Windows com backup.
Nunca construir o destino com bytes de rede. Revalidar destino e registar resultado.
Falha mantém/restaura o package anterior; não apagar backup até confirmação de
sucesso. Recuperação de interrupção é parte dos testes. Rejeitar symlinks/reparse
points que desviem os caminhos autorizados. Nunca varrer/remover configs pessoais
nem packages de terceiros. Cleanup só de staging e backup próprio confirmado.

## 13. Versão e modo real do PJOrion encontrado

Encontrado pelo atalho local: `F:/Programas/PJOrion/PjOrion.exe`.
Metadados do executável: **FileVersion 1.3.5.501, ProductVersion 1.3.5**.
DLL incluída `python27.dll`: **2.7.13**, não 2.7.18.

O executável contém ações `obfuscate-bytecode-file` e `protect-bytecode-file`,
associações `--obfuscate-bytecode-file="%1" /exit` e avisos de suporte Python 2.7.X.
Isso é evidência de interface, **não uma execução validada da CLI**.
O compilador histórico invoca `/obfuscate-bytecode-file <arquivo.py> /exit` e depois
`/protect-bytecode-file <arquivo.pyc> /exit`. Não se assume que essa forma, extensão
de input ou posição de argumentos esteja correta para o pipeline requerido.

O build atual não define ORION_PATH, portanto esse ramo não participa no build
normal. Ainda exige a string pjorion_protected e bytes alterados, mas isso não é
prova de importabilidade. Não reutilizar essa verificação como certificado.

## 14. Compatibilidade real e limitações do perfil

Python local `F:/Python27/python.exe -V`: **Python 2.7.18**. O build corrente usa
o Python 2.7 embutido no hg.exe do SourceTree, com extensão Mercurial.
Os .pyc são gerados por compile/marshal, header de oito bytes e magic 03f30d0a.
Timestamps vêm do Git quando disponíveis. É preciso provar o output no host do
build **e** no 2.7.18; magic correto por si só não basta.

O PjOrion.ini instalado contém:

* AllNamesIsPublic=0 e DetailedAnalysis=0: não preserva nomes por contrato.
* ExecOnlyInWOT=1 e LockAttributesReview=1: proteção potencialmente incompatível
  com smoke standalone/introspection.
* UseWOTInjector=0: não prova, sozinho, ausência de qualquer runtime adicional.
* CheckWebUpdate=1: copiar a ferramenta/config para sandbox local antes de ensaiar,
  desativar atualizações da ferramenta nesse ambiente, sem mudar o original.

Compatibilidade com 2.7.18, ausência de runtime extra, suporte real a .pyc de input,
CLI e determinismo **ainda não foram demonstrados**. Não ativar release por default
até a prova de conceito passar. Não distribuir outputs que só funcionem no WoT se
isso impedir a validação pós-ofuscação exigida.

## 15. Candidatos seguros de ofuscação

Perfil inicial de allowlist, não todos core/battle/lobby/components por glob.
Candidato existente: `core/marks_calculator.py`, apenas aritmética sem hooks;
preservar exatamente nomes e resultados, sem editar fórmulas/source.
Candidatos novos: versioning e manifest, se puros e com API nominal preservada.
Entram na allowlist apenas depois de importar/testar os outputs reais.
Não existe módulo certificado seguro apenas por inspeção nesta fase.

## 16. Exclusões iniciais

Entry point, Driftkings/__init__, component_list, core/__init__, hooks, callbacks,
contexts, settings, templates, registries, views, ui e i18n.
Também todos os componentes battle/lobby/components inicialmente: imports e hooks
dependem de nomes; a pesquisa nesses três grupos encontrou introspection dinâmica.
CompatibilityManager e BattleCapabilities permanecem em claro inicialmente.

Evidências: hooks.override lê handler.__name__ e __module__; callbacks usa __module__;
TemplateAdapter usa type(config).__module__; locais são importados por __import__;
views hangar atribuem __module__ e passam __name__ como owner. Proteger nomes
exportados e caminhos de módulos mesmo nos poucos candidatos permitidos.
Não ofuscar Gameface, Flash, JSON, meta.xml, traduções ou release.json.

## 17. Ficheiros novos planeados

Todos relativos ao workspace; nomes definitivos podem ajustar-se à prova da CLI:

* source/scripts/client/Driftkings/core/updater/__init__.py
* source/scripts/client/Driftkings/core/updater/versioning.py
* source/scripts/client/Driftkings/core/updater/manifest.py
* source/scripts/client/Driftkings/core/updater/state.py
* source/scripts/client/Driftkings/core/updater/endpoints.py
* source/scripts/client/Driftkings/core/updater/checker.py
* source/scripts/client/Driftkings/core/updater/downloader.py
* source/scripts/client/Driftkings/core/updater/installer.py
* source/scripts/client/Driftkings/core/updater/transport.py
* build_data/obfuscation.json
* build_tools/obfuscate_staging.py
* build_tools/python27_staging_smoke.py
* build_tools/build_release.py
* build_tools/tests/test_updater.py
* build_tools/tests/test_obfuscation.py
* build_tools/tests/test_release_artifacts.py
* docs/UPDATER.md e docs/OBFUSCATION.md

Se confirmado helper: build_tools/updater_helper/Program.cs e
build_tools/build_updater_helper.py, usando compilação local controlada, sem NuGet.
Verificar o target Windows e disponibilidade do runtime antes de distribuir.
Um helper dependente de .NET instalado não pode ser tratado como universal.

## 18. Ficheiros existentes a alterar

* source/scripts/client/Driftkings/core/__init__.py — adicionar serviço default.
* source/scripts/client/Driftkings/settings/panel/core_page.py — duas preferências.
* source/scripts/client/Driftkings/settings/panel/presenter.py — ações/estado/restart.
* source/scripts/client/Driftkings/views/hangar/settings_window.py — observar estado,
  notificações e preparação do restart no controlador existente.
* source/scripts/client/Driftkings/settings/panel/locales/en.py e pt.py — fallback atual.
* res/gui/gameface/mods/Driftkings/DKModSettings/js/app.js — secção Atualizações.
* res/gui/gameface/mods/Driftkings/DKModSettings/window.html — conteúdo da secção.
* res/gui/gameface/mods/Driftkings/DKModSettings/css/main.css — estados/progresso.
* build_tools/run_build.ps1 — diferenciar debug/release e opção NoObfuscation.
* build_tools/build_lab.py — etapas novas e encaminhar --no-obfuscation.
* build_tools/build_unified.py — staging escolhido e VERSION com prerelease.
* build_tools/compiler.py — retirar o ramo histórico da rota nova; evitar duas
  implementações ativas de ofuscação e manter compilação limpa.
* build_data/components/common.json — helper local, apenas se necessário.
* build_tools/tests/dk_settings_gameface_test.js — UI e disposal do updater.
* UNIFIED_BUILD.md — pipeline e limitações.

release.cmd/debug.cmd foram inspecionados: ambos encaminham run_build.cmd e este
run_build.ps1. Não fazem deployment. Só alterar wrappers se necessário para opções;
não adicionar publicação, cópia para o jogo ou outro entry point.

## 19. Riscos e gates de implementação

1. CLI/perfil PJOrion ainda não executados; importabilidade e nomes não garantidos.
2. 2.7.13 da ferramenta versus 2.7.18 exigido: testar, não presumir compatibilidade.
3. TLS/redirects/streaming precisam de prova no runtime WoT.
4. Mount/lock nativo desconhecido; replace em runtime desautorizado no desenho.
5. Corrida restart/WGC e processo novo exige protocolo de helper comprovado.
6. Manifests externos são não confiáveis; SHA-256 verifica integridade, enquanto
   origem confiável depende de HTTPS e endpoints autorizados.
7. Build pode ser não determinístico; calcular hash sobre bytes finais e documentar
   dois ensaios iguais/diferentes, sem prometer reproducibilidade.
8. Não permitir que outputs antigos pareçam uma release nova após falha. Staging
   por execução e promoção final apenas depois de todos os checks.

Nenhum destes gates autoriza alterar fórmulas/layouts Marks, ColorPicker,
Compatibility logic, BattleCapabilities logic, migrations ou hooks alheios.

## 20. Plano de testes e pipeline final

SemVer: iguais/antigas/novas, beta/rc/final, zeros iniciais, metadata e inválidas.
Manifest: schema, campos obrigatórios, tipos, canais, versão WoT, nomes fixos,
HTTPS/redirects, hosts, limites e changelog como texto.
Rede/download: timeout, 404, indisponibilidade, tamanho excessivo, truncamento,
hash errado/correto, cancelamento e concorrência check/download.
Lifecycle/UI: login/lobby/intervalo, battle/loading/replay/unknown bloqueados,
resultado tardio, janela fechada, lastCheck, Mais tarde e restart existente.
Installer: paths/reparse/identidade, processo vivo bloqueia, staging íntegro,
backup/replace/falha/rollback/interrupção e configs byte a byte intactas em fixtures.

PJOrion: ensaio de módulo pequeno compilado em 2.7.18, CLI isolada e observada,
import/exec de funções, nomes exportados, dependências e segundo ensaio de hash.
Só depois allowlist mínima; smoke diretamente no staging e depois diretamente
nos .pyc extraídos **do WOTMOD**, sem imports acidentais do source limpo.
Cobrir Core/component_list, settings/views registration, hooks, Marks calculator,
CompatibilityManager, BattleCapabilities e updater com stubs explícitos do jogo.
Stubs não substituem prova no cliente; não chamar essa prova de certificação WoT.

Pipeline pretendido, sem deployment/publicação:

```text
source limpo
  -> suite Python + Gameface/Hangar + traduções/configs + contratos
  -> Flash compilation
  -> Python 2.7 compilation
  -> staging novo isolado
  -> PJOrion SAFE (release; debug OFF)
  -> smoke 2.7/2.7.18 diretamente no staging
  -> WOTMOD unificado
  -> validação ZIP + imports/code do package + contratos
  -> SHA-256 do WOTMOD FINAL
  -> build/release/Driftkings.wotmod
  -> build/release/Driftkings.wotmod.sha256
  -> build/release/release.json
  -> contrato consumido pelo updater
```

Release com ofuscação, depois de validada, falha fechada se DK_PJORION faltar ou
qualquer etapa falhar. Só `--no-obfuscation` explícito permite artefacto diagnóstico
em claro, documentado como tal no relatório local. Nunca fallback silencioso.
Gerar `build/obfuscation/report.json` com perfil, versões, processed/excluded/failed
e hashes input/output. Fonte do repositório e ferramenta original permanecem intactas.

Entrega desta fase: relatório e baseline; as provas operacionais acima continuam
pendentes. Não existe ainda updater implementado, release ofuscada ou release.json.
