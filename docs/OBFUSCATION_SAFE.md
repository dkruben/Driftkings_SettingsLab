# Fase 10 — ofuscação seletiva

Estado: implementação preparada; **beta bloqueada nas verificações do host
de build**. Nenhum asset utilizável, deployment, commit, tag ou publicação.
A Fase 11 não foi iniciada.

## Âmbito

`build_data/obfuscation.json` declara três módulos explícitos:

* `Driftkings/core/marks_calculator.pyc`
* `Driftkings/core/updater/versioning.pyc`
* `Driftkings/core/updater/manifest.pyc`

Todos os outros ficheiros ficam em claro. São rejeitados globs, traversal,
duplicados, conflitos com exclusões e módulos não auditados. O código fonte
funcional não mudou; apenas VERSION passa a `0.1.2-beta.1`. Nenhuma fórmula,
persistência, hook, componente ou lógica de updater foi alterada.

A pesquisa AST dos candidatos não encontrou os identificadores de introspection
proibidos. A dependência implícita de nomes de `functools.total_ordering` é
tratada preservando nomes públicos e verificando comparações e métodos de
Version no output. O consumidor JSON usa `Manifest.parse/document` e os atributos
públicos; os contratos existentes e o smoke do updater exercitam essas APIs.
Nomes/módulos das classes são verificados explicitamente.

## Build local

```powershell
python build_tools/build_lab.py --release
```

O comando normal continua debug, sem PJOrion. `--release --no-obfuscation` é
diagnóstico explícito e não produz os assets da beta protegida. O wrapper
`release.cmd` encaminha agora o modo release para este fluxo local. Os scripts
foram inspecionados: não instalam no cliente, não fazem push ou publicação.

Após compilar em Python 2.7, o build copia os inputs para
`build/obfuscation/safe/staging`, copia/isola PJOrion e usa a CLI/perfil testados
na Fase 9. Mantém intactos source, inputs compilados e instalação original da
ferramenta. Compara todos os hashes e permite alterações apenas nos três módulos.

Falha, timeout, output ausente/inalterado, magic incorreto ou erro de teste
abortam o build. O host deve gerar relatórios novos de conclusão: exit code 0
sozinho não basta. Os assets antigos da beta são removidos antes da tentativa;
não há fallback silencioso em claro.

O WOTMOD é comparado com o pacote sem proteção: exatamente três entradas podem
mudar; entrypoint, assets e outras entradas permanecem iguais. Os imports do ZIP
são confirmados pelos caminhos reais e hashes dos bytes protegidos.

Outputs previstos, apenas depois de todas as verificações:
`build/beta/0.1.2-beta.1/{Driftkings.wotmod,Driftkings.wotmod.sha256,release.json}`.
O manifest usa SHA-256/tamanho do WOTMOD final. Não substitui a beta.6 oficial em
`build/release`. O relatório interno fica em `build/obfuscation/report.json` e
não deve ser publicado como asset.

## Verificação atual e bloqueio

Atualização Fase 10.1: o probe mínimo único de safe_path concluiu às 23:39:28 de
8 de outubro de 2026, sem novo alerta segundo o utilizador. Resultado
**INCONCLUSIVE (cenário D)**; mecanismo funcional intacto e Fase 10 congelada.
Ver `HOST_INTERFERENCE.md` para auditoria, árvore instrumentada e artefactos.

* Suite source completa: **722/722**.
* Settings Gameface, Hangar updates, Carousel lifecycle e UI bridge: passaram.
* Python/Flash contracts: **9 componentes** passaram.
* `git diff --check`: passou.
* Output protegido em Python 2.7.18 x64: **15 testes de metadata + 12 updater smoke** passaram.
* Host Python 2.7.15 x86 do build: execução incompleta, sem relatório final.

O hg.exe chegou a terminar com exit code 0 durante o teste de recibos, antes de
o terminar. Um controlo com source limpo reproduziu exatamente a saída
incompleta; não é evidência de erro no bytecode protegido. O Windows também
recusou intermitentemente novas execuções com WinError 5. O utilizador identificou
o Bitdefender e confirmou Advanced Threat Defense, deteção
`SuspiciousBehavior.234FFCC4EE6F3D`, com bloqueio das aplicações envolvidas.
Ainda não foi obtida a lista de processos/caminhos do alerta. Não se desligou
proteção nem se criaram exclusões.

A última operação do controlo limpo é o teste de recibos pós-restart. Esse teste
executa o código existente de `windows_files.py`, que lança PowerShell oculto
com `-EncodedCommand` para validar caminhos e substituir recibos. Essa cadeia
é um candidato concreto ao alerta comportamental, mas a causa exata não está
confirmada sem a árvore de processos/detalhes da deteção. O ID fornecido não
identifica sozinho o ficheiro responsável. Não foi alterado o updater nem
repetido o comportamento bloqueado após esta confirmação.

Os testes do pacote final e o teste real de update para a beta protegida continuam
pendentes. Não considerar a Fase 10 concluída nem publicar enquanto faltar a
verificação completa. Primeiro recolher os detalhes do alerta, resolver a causa
com segurança e repetir o build; depois publicar apenas como prerelease, mediante
confirmação explícita, e testar update/restart no jogo.
