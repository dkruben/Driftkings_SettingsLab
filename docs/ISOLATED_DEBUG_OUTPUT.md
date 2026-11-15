# Isolated debug output — Fase 3F.2B-FIX-A

Atualizado em 2026-11-10. **ISOLATED OUTPUT SOURCE PASS**, limitado a origem e testes simulados; nenhuma build real executada e nenhum ARTIFACT PASS atribuído.

## CLI e utilização futura

`--isolated-output` é uma flag booleana do compilador existente, exclusivamente para `--mode debug`, com `--keep-source-version` obrigatório e versão prerelease beta/rc. Stable é rejeitado, mesmo em debug; release é rejeitado para beta e stable. Beta aqui é o canal da versão experimental, não modo de publicação. Sem a flag, os destinos e a promoção normais mantêm-se.

Exemplo para futura fase **ainda não autorizada nesta execução**:

```powershell
python -B build_tools/compiler.py --mode debug --isolated-output --keep-source-version --version 0.1.8-beta.4 --channel beta --game-root "C:\Games\World_of_Tanks_CT" --reference-root "E:\Wot_Mods_\Drift_Kings_ModPack\Driftkings_WoT_Sources\wot_src_CT"
```

Confirmar primeiro que a referência indicada satisfaz a versão exigida pelo contrato de build. `--plan` produz apenas um preview sem reservar workspace. O help explica as restrições; erros indicam `requires --mode debug`, `requires --keep-source-version` ou `requires an experimental prerelease`. O run ID é gerado internamente (UTC + UUID); não existe opção CLI de destino arbitrário.

## Layout e ownership

```text
build/experiments/<run-id>/
  workspace/     jobs, bytecode, assets gerados, logs, relatórios, temp/cache
  output/        distribuição, pacote e manifestos de distribuição futuros
  manifests/     relatório final da execução
  diagnostics/   state.json: running, failed ou complete
```

A configuração, ferramentas e cliente são validados antes da reserva; os nomes de outputs dos geradores, changelog e epoch são verificados antes de criar outputs isolados. `mkdir` exclusivo rejeita IDs existentes (diretório ou ficheiro), sem reutilização ou promoção de outputs anteriores. Só os diretórios build/experiments necessários podem ser criados como infraestrutura fora do run; nenhum ficheiro partilhado é escrito. Fontes, configurações e dependências são lidas nas localizações originais; o compilador não é duplicado.

## Inventário dos efeitos de escrita

| Writer / fase | Build normal | Build isolada / tratamento |
| --- | --- | --- |
| sync_release_version / seleção | VERSION e build_data/release.json; pode substituir | Não chamado: keep-source-version obrigatório |
| Criação de execução | build/runs/novo-id | workspace do novo run exclusivo |
| run_worker / jobs, resultados, logs | run/*.json, run/logs, compiled | Todos em workspace; worker -B, jobs com destinos isolados |
| Worker Python 2.7 | mkdir e bytecode nos destinos do job | compiled dentro do workspace; sem bytecode de import externo |
| generate / Flash, C#, patches AST e replace_exact | run/generated e logs | Mesma ordem e conteúdo, dentro do workspace |
| vehicle_markers / ferramentas auxiliares | TemporaryDirectory abaixo do output do gerador; remove apenas esse temporário | Mesmo comportamento dentro de workspace; cwd/env instrumentados, cleanup próprio permitido |
| Subprocessos Java/.NET/Node e compiladores | cwd e ambiente anteriores | cwd isolado, TEMP/TMP/TMPDIR e caches configurados no run; Java tmpdir/user.home redirecionados |
| Catálogos/defaults / python_overrides | Render em memória para jobs | Mesmo render em memória; CLIs --write não são invocadas |
| package_entries/metadata | Buffers em memória | Sem alterações |
| zip_entries / pacote e distribuição | Candidate irmão do destino versionado | output do run; mesmas regras internas |
| write_distribution / cópias de dependências | Candidate/dependencies, ZIP defaults e instalação manual | output do run; sem instalação |
| write_json / release, modpack, reports | Candidate/run; substitui relatórios próprios | output/workspace/manifests/diagnostics próprios |
| SHA256SUMS / listagem final | Candidate | output do run |
| publish_local / rename e preservação anterior | Destino versionado, build/previous | Não chamado |
| atomic_copy / pacote unificado | build/unified/driftkings.wotmod, replace | Não chamado |
| atomic_copy / gerados globais | build/gameface, build/flash, helpers e metadata configurados | Não chamado |
| atomic_copy / staging Python global | build/staging | Não chamado |
| git_state / estado Git | Comportamento normal | Apenas leitura, antes da reserva, GIT_OPTIONAL_LOCKS=0 para impedir refresh do index |
| Cache Python do processo / imports | Comportamento normal | dont_write_bytecode durante caminho isolado; recomendar CLI -B desde o arranque |
| Limpeza | Helpers temporários e substituição de diretórios normais | Nenhuma limpeza global, nenhuma eliminação de run; temporários próprios apenas |

`generate_ui_catalog.py --write` e `generate_defaults.py --write` são ferramentas independentes; não integram este percurso do compilador. A flag não altera essas CLIs nem autoriza executá-las. Instalação/publicação/assinatura não são acrescentadas.

## Proteções e limites

`isolated_output.py` fornece uma guarda de escrita Python contextual: open mutável, mkdir, rename/replace, remove/rmdir, rmtree, chmod/utime/truncate são verificados; hardlinks e symlinks são proibidos. Caminhos relativos com `dir_fd` são resolvidos pelo diretório do descritor (ver secção 3F.2D-C1-FIX). Não atua quando a flag está ausente. A raiz tem identidade de dispositivo/inode verificada; `..`, saída da raiz, symlinks e todos os reparse points Windows (incluindo junctions) são rejeitados. No Windows, handles dos diretórios sem partilha DELETE impedem substituição/rename dos diretórios fixados durante a execução. Handles de subárvores próprias são libertados para a limpeza dos temporários, mantendo a raiz reservada. Falhas de abertura/permissão fazem abortar, não desativam a proteção.

Não é um sandbox do sistema operativo para executáveis hostis: subprocessos recebem destinos/cwd/ambiente isolados mas conservam as permissões do utilizador. Um executável que ignore deliberadamente essas opções, crash dumps/telemetria do SO ou um atacante com acesso concorrente aos ficheiros não estão integralmente confinados pela guarda Python. Usar apenas as ferramentas confiáveis já configuradas. Não se reclama proteção absoluta contra todas as corridas de ficheiros ou equivalência a ACL/sandbox. O reforço Windows reduz corridas de substituição de diretórios; não depende apenas de resolve(). A validação real dos compiladores e seus efeitos permanece pendente de uma build autorizada.

## Falha, diagnóstico e limpeza

Política: preservar toda a execução incompleta, sem limpeza recursiva automática do run. Nunca renomear/eliminar diretórios anteriores. Helpers podem remover apenas os temporários próprios no run. Falhas deixam state failed e relatório quando o filesystem permite; sem state complete a execução não é aprovada. Complete só é escrito após todas as verificações e relatórios. Falha de reserva/permissão pode impedir a criação do próprio diagnóstico; exceção é devolvida ao chamador e nenhum sucesso é registado. Uma futura limpeza manual requer validar ownership/caminho e autorização separada; não há comando novo de limpeza.

## Testes e evidência

Testes novos em tests/build/test_isolated_output.py: parsing/modos; reserva exclusiva; ficheiro/diretório existente; traversal e destinos externos; symlink real ou deteção simulada quando falta privilégio; junction real Windows; permissões/criação; ownership; guardas de escrita/rename/link/cwd; cleanup de temporário próprio; preservação de diretório externo; env/cwd de subprocesso; processo-filho real com buffers em stdin/stdout (autocontido desde a 3F.2D-FIX; o patch AST real sob escopo isolado passou para `tests/build/test_native_results_source.py`, opcional quando falta a fixture CT); fluxo completo instrumentado e falhas em compile/generate/patch/package/copy/verify/diagnóstico; dispatch debug/release beta/stable normal. Doubles substituem compiladores e packaging, criam apenas .fixture; nenhum .wotmod é criado. Mensagens “Compiling” e “Build complete” no log pertencem ao fluxo simulado, não a uma compilação real.

Resultados/comandos e hashes finais: build/diagnostics/phase3f2b-fix-a/20261110/. Os resultados 3F.2A são históricos. Frontend e runtime cliente não foram modificados nem repetidos sem necessidade. Avisos CRLF/LF não são falha de build. Scaleform continua em observação, causa não determinada.

## Desativação e retoma

Para não usar a funcionalidade, omitir --isolated-output: o fluxo normal mantém publish_local e os seus efeitos originais. Não é uma solução para preservar build/unified numa experiência. Nenhum rollback foi executado.

Retomar 3F.2B exige nova autorização expressa, conferir snapshot atualizado, versões/fontes/clientes/ferramentas, pacotes/backup protegidos, flag isolada e novo destino. Só depois uma única build real e auditoria do artefacto/diferenças beta.3. Testes simulados não demonstram ARTIFACT PASS nem CT PASS; instalação/3F.2C continuam separadas.

## Fase 3F.2B-FIX-B2 — temporário Windows e diagnóstico — 2026-11-10

**WINDOWS CLEANUP SOURCE PASS**, apenas código/testes. Nenhuma build real, .wotmod, instalação ou ARTIFACT PASS nesta correção.

A retoma 3F.2B falhou na limpeza de vehicle_markers_flash. FIX-B1 classificou caminhos longos como causa provável. Antes da alteração, fixtures Windows reproduziram o mecanismo: aos 259 caracteres unlink/rmtree funcionaram; aos 260/263/264, unlink devolveu FileNotFoundError/WinError 3 e rmtree terminou em WinError 145. Condição medida: Python 3.14.3, LongPathsEnabled=0. A reprodução confirma o mecanismo nas fixtures; sem traceback original, a atribuição histórica ao incidente continua provável, com confiança elevada.

`vehicle_markers.marker_workspace` usa, exclusivamente em contexto isolado, `<run>/workspace/tmp/vm-<random>/`. Mantém TemporaryDirectory, nomes exclusivos e guardas, valida o destino e não depende do cwd. Modo normal mantém o temporário antigo abaixo de destination.parent. Não altera nomes internos do jogo, pipeline de patches, metadata ou compiladores. Orçamento genérico de 120 caracteres relativos para a árvore descompilada (recurso pinned atual observado até 107), mais 8 de margem; comprimentos da raiz são medidos em unidades UTF-16. Se a projeção for demasiado profunda, falha antes de criar o temporário/iniciar ferramentas; tamanho efetivo também validado antes de entregar o workspace. Mudanças futuras da árvore/recurso pinned exigem rever esse orçamento.

O cleanup aguarda a conclusão do bloco síncrono, liberta handles próprios da subárvore e remove exclusivamente o TemporaryDirectory criado. Falhas bloqueiam, sem retries/ignore_errors. Se corpo e cleanup falharem, ambos são preservados por exception chaining. Outputs incompletos mantêm-se para diagnóstico. Não se muda política global Windows, antivírus ou LongPathsEnabled.

`build_diagnostics.py` regista tipo/mensagem, traceback com chain e sem locals, fase/componente/workspace, filename/errno/winerror e timestamp. Apenas a build isolada usa os novos relatórios; o handler normal mantém o formato anterior. Erro de gravação é anexado ao erro original e enviado a stderr com traceback original, sem substituir a exceção inicial. Se não houver filesystem/stderr disponível, não há garantia de persistência, mas a execução continua falhada. Mensagens e tracebacks passam por redaction de credenciais comuns e campos payload/html; não se incluem variáveis locais, ambiente, payloads funcionais ou telemetria externa. Redaction não é um detetor universal de segredos arbitrários: não inserir credenciais em exceções.

O inventário usa nomes relativos e APIs de leitura Windows estendidas para metadata/hashing, sem mudar globalmente paths de escrita nem enfraquecer a guarda. Conta file_count/hashed_count/unhashed_count/unknown_count, lista erros e entradas sem hash; complete só é true sem lacunas. Não segue links/reparse points. Diretórios inacessíveis geram erro explícito; entradas cujo tipo não possa ser determinado ficam unknown, sem se declarar inventário completo. Num erro de build, inventory.json é um snapshot antes da gravação do próprio inventário, não um manifesto autorreferente final de todos os diagnósticos.

Validação nesta fase: 223 testes de build PASS (14 novos), zero FAIL/SKIP finais; Windows real nas fixtures de limites/handle/junction/cleanup, falhas simuladas de diagnóstico/leitura/metadata/criação, partial cleanup, writer aguardado, modo normal, escapes e regressões isoladas/AST/replace_exact. O primeiro ensaio do handle falhou porque acesso apenas a metadata não bloqueou remoção; corrigida a fixture para GENERIC_READ e partilha restrita, sem mudar o código por essa falha. Logs iniciais preservados.

Medição do layout curto com raiz equivalente ao projeto e run-id de 26 caracteres: temporário 126, sufixo do incidente 234, ficheiro com sufixo genérico de 120 caracteres 247; cleanup completo. O run do incidente tinha ID de 25 caracteres, pelo que a projeção equivalente seria um carácter menor. Não é medição de uma nova build real.

O novo inventário foi aplicado apenas em leitura ao incidente preservado: 871 ficheiros, 871 hashes, unhashed_count=0, errors=0, corrigindo a omissão de três caminhos longos no manifesto anterior de 868 hashes. Os antigos diagnósticos/ficheiros não foram alterados. Evidência, comandos e snapshot desta correção: `build/diagnostics/phase3f2b-fix-b2/20261110T004135Z/`.

Retoma da build exige nova autorização expressa, conferir snapshot novo e hashes protegidos, usar --isolated-output/--keep-source-version/CT explícito e executar apenas a tentativa autorizada. Não se validaram nesta fase os compiladores Flash reais, empacotamento, Gameface/coui ou execução CT. Para desativar o caminho novo, não usar modo isolado; builds normais continuam com os efeitos globais anteriores, não sendo alternativa segura para uma experiência protegida.

## Resultado posterior — Fases 3F.2B e 3F.2C — 2026-11-10

A retoma autorizada usou `--isolated-output --keep-source-version` e concluiu com **ARTIFACT PASS**: pacote experimental `0.1.8-beta.4` em `build/experiments/20261110T031027Z-b23d8daf/output/`, 632 entradas, SHA-256 `49749a9e221cecca45b83978edd113f0b2b60e54dabee09760f01f280e5118d0`, estado `complete` e `publishable: false`. Compiladores Flash reais, empacotamento e cleanup Windows do temporário curto funcionaram nessa execução única. Nenhum output global foi promovido; `build/unified` manteve a beta.3. O workspace da tentativa falhada (`build/experiments/20261110T001806Z-bc49af60`) continua preservado. A validação CT está descrita em [STATUS.md](STATUS.md). As afirmações anteriores deste documento sobre ausência de build real descrevem o estado à data de cada correção.

## Fase 3F.2D-C1-FIX — caminhos relativos com `dir_fd` (POSIX) — 2026-11-11

**Correção de origem e testes; sem build, sem validação Linux real.** Em POSIX, `shutil.rmtree` e `TemporaryDirectory.cleanup` removem entradas por nome relativo a um descritor de diretório (`os.unlink(nome, dir_fd=fd)`, `os.rmdir(nome, dir_fd=fd)`). A guarda resolvia esses nomes contra o `cwd` e rejeitava a limpeza de temporários próprios. No Windows o `dir_fd` não existe nestas operações (a plataforma devolve `NotImplementedError` antes de qualquer evento de auditoria), pelo que o comportamento Windows não mudou.

Contrato, fail-closed:

- Sem `dir_fd` (`None`, `-1` ou `AT_FDCWD`), ou com caminho absoluto (o sistema operativo ignora o `dir_fd`): guardas anteriores, sem alteração.
- Caminho relativo com `dir_fd`: o descritor tem de ser um inteiro não negativo, aberto e de um diretório; o diretório é obtido por `readlink` de `/proc/self/fd/<fd>` e confirmado por identidade dispositivo/inode entre `fstat(fd)` e `lstat(nome)`. O diretório tem de pertencer ao run ativo; o destino `diretório/nome` passa depois pelas guardas habituais (`..`, symlinks/reparse points em qualquer componente, outros runs, identidade da raiz, proibição de remover a raiz).
- O `dir_fd` nunca autoriza por si só e nunca há recurso ao `cwd`. Descritor inválido, fechado ou de ficheiro, `/proc` ausente ou ilegível, diretório eliminado ou substituído, nome relativo ou identidade divergente: `ValueError` e a operação é abortada.
- Um symlink como entrada final continua a ser rejeitado e nunca é seguido, mesmo que aponte para dentro do run.
- Eventos abrangidos: `os.mkdir`, `os.remove`/`os.unlink`, `os.rmdir`, `os.chmod`, `os.utime`, `os.rename`/`os.replace` (`src_dir_fd` e `dst_dir_fd`) e `shutil.rmtree`.

Limites conhecidos. Sistemas POSIX sem `/proc/self/fd` (macOS, BSD, `/proc` não montado) ficam sem limpeza relativa a descritores dentro de um run isolado: falha explícita, não degradação silenciosa. O evento de auditoria `open` do CPython não expõe o `dir_fd` de `os.open`; uma abertura para escrita com caminho relativo continua a ser avaliada contra o `cwd` (o compilador não usa essa forma e não muda de diretório). A verificação precede a chamada ao sistema: uma troca concorrente do diretório entre ambas não é coberta, como já se declarava para as restantes corridas.

Testes em `tests/build/test_isolated_output.py` (`DirFdGuardTests`): descritores e `/proc` simulados, executáveis em qualquer plataforma, mais descritores reais fechados e de ficheiro regular. `test_real_posix_descriptors` usa descritores reais e só corre onde existe `/proc/self/fd`; no Windows fica SKIP. **A compatibilidade Linux permanece não verificada** até a CI (ubuntu, Python 3.12) executar `python -B tests/run_python.py --suite build`: os cenários simulados não são validação Linux.
