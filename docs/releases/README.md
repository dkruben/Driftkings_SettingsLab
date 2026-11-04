# Validação e promoção de releases

Como uma beta se torna stable, com a origem de cada stable identificável. Os comandos partem da raiz do repositório. As ferramentas são `build_tools/validation_record.py` e `build_tools/promote_release.py`; o guia de compilação e assinatura continua no [CONTRIBUTING](../../CONTRIBUTING.md).

## Princípios

- **A promoção não renomeia a beta.** A versão está no código e no pacote, por isso a stable é compilada de novo, tem os seus nomes de artefactos e o seu manifesto, e recebe uma assinatura nova.
- **A stable não é o mesmo commit da beta.** Entre o commit aprovado e o commit da stable só pode mudar o que não chega ao pacote, além da versão. A ferramenta compara os dois no Git e, depois da build, compara os hashes de `inputs` dos dois `build-report.json`. Uma correção de código exige uma nova beta.
- **Compilar, assinar e publicar são passos locais.** A compilação precisa do cliente WoT e a chave está offline. A publicação também fica local porque uma release publicada com o `GITHUB_TOKEN` não dispararia `discord-releases.yml`.
- **A rastreabilidade fica no asset `promotion.json`.** O atualizador rejeita campos desconhecidos no manifesto, por isso nada de rastreabilidade pode entrar em `release.json`.
- **A aprovação identifica os artefactos.** A build vem antes da aprovação. O digest são os primeiros 16 caracteres do SHA-256 de `SHA256SUMS.txt`, que cobre o relatório, o manifesto e todos os artefactos. Uma nova build gera outro digest e exige nova aprovação.
- **Nenhum caminho local é publicado.** `sign_release.py` retira `tools` e `logs` do `build-report.json` e recalcula `SHA256SUMS.txt`; o relatório completo fica em `build/runs/`. O publicador recusa relatórios com caminhos absolutos.

## Registo de validação

Cada beta candidata tem `docs/releases/<versão-beta>-validation.md`. O [modelo](validation-template.md) mostra a estrutura; para criar um registo:

```bash
python build_tools/validation_record.py new 0.1.6-beta.1 --commit <sha-completo> --package-sha256 <sha256-do-wotmod>
python build_tools/validation_record.py check 0.1.6-beta.1
```

O registo é preenchido à mão, com `PASS`, `FAIL`, `NOT TESTED` ou `NOT APPLICABLE`. As ferramentas nunca escrevem um resultado, e o registo é lido como dados, nunca executado.

A avaliação recusa um registo quando:

- a decisão não é `APPROVED`, falta o aprovador ou a data, ou o commit e a versão aprovados não coincidem com a identificação;
- nenhuma região está `VALIDATED`, ou uma região `VALIDATED` não tem build do cliente, data, validador e ambiente;
- numa região `VALIDATED`, uma verificação bloqueante está `NOT TESTED`, ou `NOT APPLICABLE` sem motivo nas notas;
- uma verificação bloqueante está `FAIL` em qualquer região, mesmo numa região não validada;
- uma verificação não bloqueante está `FAIL` sem problema conhecido associado;
- existe um problema `BLOCKER` que não está `FIXED`;
- uma verificação automática falhou, não correu ou não tem evidência;
- falta uma verificação do catálogo, ou o seu campo `Bloqueante` difere do catálogo.

Uma região nunca vale como prova de outra. Uma região sem validação fica `NOT VALIDATED`, e isso é registado em `promotion.json`. A stable pode sair com uma só região validada, mas o changelog tem de dizer o que foi testado. O catálogo de verificações, e quais são bloqueantes, está em `validation_record.py`; apagar uma linha do registo não enfraquece a validação. Podem acrescentar-se linhas próprias.

## Processo completo

### 1. Desenvolver e publicar a beta

Desenvolver em `develop` e publicar a beta como descrito em [Build and publish a new beta](../../CONTRIBUTING.md#build-and-publish-a-new-beta). `publish_release.py --publish` recusa agora um commit sem CI verde e um tag que já tenha release, rascunho ou tag remoto. O publicador exige também o instalador em qualquer canal.

### 2. Validar e registar

Instalar a beta publicada, testar no cliente e preencher o registo, indicando o commit do tag e o SHA-256 do `driftkings.wotmod` publicado. Quando a beta for aceite, mudar `Decisão` para `APPROVED`, preencher o resto da secção `Aprovação final`, fazer commit em `develop` e push.

```bash
python build_tools/validation_record.py check 0.1.6-beta.1
```

### 3. Preparar o commit da stable

`main` tem de receber o commit aprovado. Depois dele, `develop` só pode ter alterações permitidas (ver a tabela abaixo).

```bash
git switch main
git merge --ff-only develop
python build_tools/promote_release.py prepare --beta 0.1.6-beta.1
```

`prepare` só altera a versão e o canal em `build_data/release.json` e `VERSION`; não faz commit. Completar à mão: changelog de `release.json` sem avisos de beta e a dizer que regiões foram testadas, README, SECURITY, exemplo em `.github/ISSUE_TEMPLATE/bug_report.yml` e fixture de `tests/runtime/integration/test_core_startup.py`.

```bash
git add -A
git commit -m "Prepare stable 0.1.6"
git push origin main
```

Esperar pelo CI verde deste commit.

### 4. Verificar a promoção

```bash
python build_tools/promote_release.py check --beta 0.1.6-beta.1
```

| Verificação | O que exige |
| --- | --- |
| `identity` | Commit completo; `release.json` e `VERSION` com a versão stable derivada da beta e canal `stable` |
| `record` | Registo aprovado, lido do commit da stable e não da árvore de trabalho |
| `history` | Commit aprovado é antepassado da stable; stable está em `origin/main` |
| `changes` | Só caminhos permitidos mudaram; `VERSION` é a única alteração no código; em `release.json` só mudam `version`, `channel` e `changelog` |
| `beta` | Prerelease publicada, tag no commit aprovado, assinatura de chave confiável, checksums certos, pacote igual ao validado |
| `ci` | `python-package.yml` verde no commit da beta e no da stable |
| `slot` | Sem release, rascunho nem tag da stable; versão superior a todas as stable publicadas |

Caminhos permitidos entre a beta e a stable: `docs/`, `tests/`, `.github/ISSUE_TEMPLATE/`, `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `build_data/release.json`, `.github/workflows/promotion-gate.yml` e as ferramentas de release (`promote_release.py`, `publish_release.py`, `sign_release.py`, `update_release.py`, `validation_record.py`). Qualquer outra alteração bloqueia, incluindo `python-package.yml` e `compiler.py`.

### 5. Compilar, assinar e verificar a stable

```bash
python build_tools/promote_release.py build --beta 0.1.6-beta.1 --key release-signing.key
```

Com a árvore limpa no commit da stable, repete as verificações, compila, gera o instalador, assina, corre `tests/artifacts` sobre o pacote e aplica as verificações do publicador. Confirma ainda que os `inputs` coincidem com os da beta. Nada é enviado.

No fim, grava `.promotion-build.json` na pasta da versão e mostra o commit e o digest dos artefactos. Esse ficheiro local nunca é enviado; `publish` recusa uma pasta sem ele ou com conteúdo diferente, por isso uma build feita à mão não é aceite.

### 6. Pedir a aprovação

```bash
gh workflow run promotion-gate.yml --ref main -f beta_version=0.1.6-beta.1 -f stable_commit=<sha-completo> -f artifacts_digest=<digest> -f request_approval=true
```

O workflow corre as verificações em modo de leitura e mostra o commit e o digest no título da execução. Com `request_approval`, espera depois pela aprovação no ambiente `stable-release`. Sem esse valor, faz apenas a validação. Quem aprova confirma que o commit e o digest são os mostrados por `build`.

### 7. Publicar

```bash
python build_tools/promote_release.py publish --beta 0.1.6-beta.1
python build_tools/promote_release.py publish --beta 0.1.6-beta.1 --confirm v0.1.6@<digest>
```

Sem `--confirm`, é uma pré-visualização: gera `promotion.json`, mostra o SHA-256 de cada asset e o valor exato de `--confirm`, e não envia nada. Com `--confirm`, cria o rascunho, descarrega cada asset e compara-o com o local, publica como stable `latest` e confirma o tag e os metadados públicos. O rascunho nunca é publicado se um asset faltar ou diferir.

| Falha | Resultado | O que fazer |
| --- | --- | --- |
| Envio interrompido ou asset em falta | O rascunho fica por publicar | Rever e apagar o rascunho, depois repetir o comando |
| Falha de rede depois de todos os assets | O rascunho fica por publicar | Repetir o comando; a ferramenta retoma se o commit e os assets coincidirem |
| Erro depois do `PATCH` aplicado | A release pode estar publicada e o comando repetido para em `slot` | Comparar a release pública com `promotion.json` à mão |

Uma stable publicada nunca é sobrescrita por esta ferramenta.

`--waive-environment-review` aceita só o registo e fica escrita em `promotion.json`. É recusada quando `stable-release` tem revisores obrigatórios, e nesse caso a aprovação no ambiente é a única via.

### 8. Depois de publicar

- Confirmar a notificação no Discord: o evento `published` dispara `discord-releases.yml`. Se falhar, repetir a execução com `gh run rerun <id>`.
- Trazer `main` de volta para `develop`: `git switch develop` e `git merge --ff-only main`.
- Atualizar `docs/STATUS.md`, README e SECURITY, se ainda faltar.

## `promotion.json`

Asset da release que responde de onde veio uma stable: commit e tag da stable e da beta, hashes dos manifestos, do pacote, de `SHA256SUMS.txt` e da assinatura, chave usada, caminhos alterados depois da beta, hash e aprovação do registo, regiões validadas e não validadas, problemas conhecidos, execuções do CI, execução da aprovação e quem promoveu. O histórico fica nas releases, no Git e nos registos desta pasta.

O ficheiro não está assinado nem coberto por `SHA256SUMS.txt`, porque estes são gerados antes dele. A autenticidade da release continua a vir de `release.json.sig`; `promotion.json` aponta para esses hashes.

## Configuração do GitHub

Nada disto foi configurado no repositório. Em 2026-11-04, `main` e `develop` não tinham proteção de branch, não havia rulesets nem ambientes, e os workflows tinham `read` como permissão por omissão.

**Ambiente `stable-release`** (Settings → Environments):

1. Criar o ambiente `stable-release`.
2. Ativar **Required reviewers** e indicar quem aprova.
3. Em **Deployment branches and tags**, limitar a `main`.
4. Sendo o único mantenedor, deixar **Prevent self-review** desligado; com ele ligado ninguém poderia aprovar.

Os revisores obrigatórios estão disponíveis em repositórios públicos; num repositório privado dependem do plano. Convém confirmar na documentação do GitHub antes de contar com isto. Se o ambiente não existir, o GitHub cria-o na primeira execução sem proteção. A aprovação fica vazia e `publish` recusa-a, a menos que se use `--waive-environment-review`. Por isso, o ambiente deve ser criado antes da primeira promoção.

**Disponibilidade do workflow:** `workflow_dispatch` só funciona depois de `promotion-gate.yml` estar na branch por omissão, `main`. Até lá, `publish` não encontra a execução. Em `develop` o workflow não corre, e o job termina como ignorado se for lançado noutra branch.

**Recomendado, não obrigatório:** proteger `main` contra force-push e tornar `validate` obrigatório; proteger `v*` contra mover e apagar tags. Estas regras são o que torna o bloqueio efetivo do lado do GitHub, porque as ferramentas locais podem ser contornadas com `gh` diretamente.

**Limite conhecido:** com `contents: read`, o `GITHUB_TOKEN` pode não ver rascunhos, por isso a verificação `slot` no workflow pode não os detetar. A verificação local em `publish` usa as credenciais do mantenedor e deteta-os.

## Recuperação

`update_release.py --publish` continua a substituir os assets da mesma revisão. Numa stable exige também `--replace-stable-assets`. Depois disso, os hashes em `promotion.json` deixam de coincidir com os novos assets, e isso deve ficar anotado em `docs/STATUS.md`. Uma alteração de código exige sempre uma nova versão.

As releases publicadas antes desta correção continuam a ter caminhos locais no `build-report.json`. Substituir esses assets é uma decisão à parte, que não é feita por nenhuma ferramenta.
