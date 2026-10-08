# Fase 9 — PJOrion POC

Estado: verificações locais e teste real passaram. **GO para a Fase 10**, autorizado
pelo utilizador após a revisão do game.log de 8 de outubro de 2026. O updater,
as fórmulas, os hooks, a persistência e o build normal não foram alterados.

## Instalação e isolamento

A instalação original é `F:/Programas/PJOrion`. O executável tem FileVersion
**1.3.5.501**, ProductVersion **1.3.5**. A DLL incluída e o terminal da ferramenta
identificam **Python 2.7.13 x86**; o recurso numérico da DLL é
`2.7.13150.1013`, diferente da string de versão do runtime.

O sandbox é `build/obfuscation/poc/tool/`. Foram necessários o executável, INI,
`python27.dll`, `python27.zip`, `DLLs/`, `dispack.zip` e `dcpack.zip`. A primeira
cópia sem os arquivos auxiliares falhou; o terminal mostrou
`ImportError: No module named dispack.disassemble_2`.

Foram modificadas somente cópias locais do INI:

| Opção | Valor do POC | Razão |
| --- | --- | --- |
| `PATHS.Python` | DLL absoluta do sandbox, codificada em base64 | A referência `%ORION_DIR%` não resolveu no ensaio isolado |
| `GENERAL.AutoConnect` | `1` | Conectar o runtime Python da ferramenta |
| `GENERAL.CheckWebUpdate` | `0` | Desligar a procura de atualização no sandbox |
| `FILEASSOCIATIONS.RegisterApplication/PY/PYC` | `0` | Evitar registos de associações |
| `CONTEXTMENU.Integrate` | `0` | Evitar integração no sistema |
| `WOTTRANSMISSION.SearchWOT` / `WOT` | `0` / vazio | Não procurar/contactar a instalação do jogo |
| `OBFUSCATE.AllNamesIsPublic` | `1` | Preservar a API pública |
| `OBFUSCATE.DetailedAnalysis` | `1` | Perfil conservador deste ensaio |
| `PROTECT.ExecOnlyInWOT` | `0` | Permitir validação standalone |
| `PROTECT.LockAttributesReview` | `0` | Permitir testes dos nomes exportados |
| `PROTECT.UseWOTInjector` | `0` | Não usar injector WoT |
| `PROTECT.CreateBackupFile` | `0` | Inputs e outputs já são cópias isoladas |

Os hashes dos seis arquivos principais da instalação e do source foram
comparados antes/depois: **sem alterações**. As tentativas, INI e relatórios são
locais, não assets de release. A ferramenta foi iniciada oculta e só os processos
criados pelo ensaio foram terminados quando excederam o limite.

## CLI observada, formatos e falhas

Comando reproduzível do ensaio:

```powershell
python build_tools/pjorion_poc.py
```

O argv que produziu o output final foi:

```text
E:\Wot_Mods_\Drift_Kings_ModPack\Driftkings_Mods_Hide\Driftkings_SettingsLab\build\obfuscation\poc\tool\PjOrion.exe
--protect-bytecode-file=E:\Wot_Mods_\Drift_Kings_ModPack\Driftkings_Mods_Hide\Driftkings_SettingsLab\build\obfuscation\poc\protected\marks_calculator.pyc
/exit
```

Esse comando aceitou o `.pyc` compilado em Python 2.7.18, alterou-o no mesmo
caminho e terminou com exit code **0**. A compilação de `.py` através de
`--compile-file=... /exit` também foi observada, com exit code 0. O comando
`--obfuscate-bytecode-file=... /exit` aceitou `.py`, mas rejeitou `.pyc` com
`file not consist compilation python-code!`. Portanto, o fluxo requerido
`.py → compile 2.7 → .pyc → PJOrion` usa **protect-bytecode-file** neste POC;
não se substituiu a compilação própria pela compilação interna do ofuscador.

As formas com parâmetros separados também foram ensaiadas. Algumas tentativas
sem configuração/dependências completas ficaram na GUI, sem output alterado.
Foram interrompidas por timeout; o código 1 daí resultante é **terminação forçada**,
não um exit code natural comprovado do PJOrion. Os JSON `attempt-*.json` preservam
essas observações e os textos lidos da GUI do processo isolado.

O runner rejeita timeout, exit code não zero, output ausente/inalterado ou magic
diferente de Python 2.7. Rejeita alterações a qualquer entrada adicional do pacote.
Não há fallback em claro. Uma falha remove o WOTMOD experimental desta execução,
incluindo um artefacto antigo no mesmo caminho. Os testes desses bloqueios passaram.

## Input, output e hashes finais

Só `Driftkings/core/marks_calculator.py` foi candidato à proteção. O source contém
três funções puras e `import math`; a auditoria não encontrou dependências de
nomes dinâmicos/introspection. Os nomes públicos foram preservados.

| Artefacto | Bytes | SHA-256 |
| --- | ---: | --- |
| Source original | 347 | `8db9037f6b8bafb95821c4d0ea7e8ab173bb425b6fe0ff1518b77bb7952077ce` |
| Input `.pyc` | 810 | `4f35608106477361056a3499ee81d56c2e9c3d70885fd03fbc6007a261e5f8e5` |
| Output protegido `.pyc` | 19019 | `fe8a21ce907653eef3973e68398bf3d90ca1d3e25bf6530e7031cbe6eb307813` |
| WOTMOD experimental | 6722100 | `ea10733a51ce588b3c7cdca9dcb82c476403a93c9ae4d955bb7b1667002f8b8e` |

Input: `build/obfuscation/poc/input/marks_calculator.pyc`.
Output: `build/obfuscation/poc/protected/marks_calculator.pyc`.
Pacote: `build/obfuscation/poc/Driftkings-PJOrion-POC.wotmod`.
Relatório privado completo: `build/obfuscation/poc/report.json`.

O pacote experimental deriva do pacote beta.6 validado. Mantém VERSION
`0.1.1-beta.6` e todas as 394 entradas. A comparação byte a byte demonstrou que
somente `res/scripts/client/Driftkings/core/marks_calculator.pyc` mudou. Entry point,
helper/updater, Flash, Gameface, JSON, XML, traduções e imagens permanecem iguais.
Não há release.json novo, tag ou publicação deste pacote.

## Testes dos bytes protegidos

| Runtime | Arquivo direto | Bytes extraídos do WOTMOD | Import real pelo caminho do pacote |
| --- | --- | --- | --- |
| Python 2.7.18 x64, `F:/Python27/python.exe` | Passou | Passou | Passou |
| Python 2.7.15 x86, hg.exe usado pelo build | Passou | Passou | Passou |

Cada execução realizou **20 090 comparações**, incluindo arredondamento em
limites, valores negativos, tipos numéricos, empate de assistências e equivalência
das exceções para NaN/infinito. Os **quatro testes aritméticos existentes** também
passaram, com as funções ligadas ao output protegido. O módulo de teste original
não foi importado, pois isso carregaria source limpo por acidente.

O import real veio do caminho
`Driftkings-PJOrion-POC.wotmod/res/scripts/client/Driftkings/core/marks_calculator.pyc`.
Os testes não acrescentam a pasta da ferramenta ao sys.path. A importação foi
ensaiada com bloqueio de imports de PJOrion/dispack/dcpack e ctypes. Não foi
necessária uma DLL extra ou runtime da ferramenta para executar o output nesses
hosts; o bootstrap observado usa biblioteca padrão (`sys`, `marshal`, `zlib`,
`__builtin__`). Isto ainda não certifica o runtime embutido no WoT.

Também passaram os 23 testes de Marks no source e os quatro novos testes de
isolamento/falha do runner. O registo de regressão do source está no sandbox.

A regressão completa passou em dois grupos: 696 testes gerais e 21 testes
nativos de instalação/rollback, totalizando **717/717**. Foi corrigida apenas
uma corrida na limpeza da fixture nativa: o teste agora aguarda a saída do
processo que lançou antes de remover a pasta temporária. Não houve alteração
ao updater. `git diff --check` passou.

## Limitações e decisão

O CPython emite avisos `XXX lineno: 1, opcode: ...` durante a importação protegida.
Não houve traceback/crash nos ensaios finais nem divergência aritmética, mas esses
avisos são uma limitação concreta. Não foram ocultados, nem foi alterado o código
funcional para satisfazer o ofuscador.

Duas execuções com o mesmo input, configuração e argv produziram outputs
diferentes: `3d8236adec07de6d032c61537575cef99cc66c749b545d02c03e2947b8a58975`
e `fe8a21ce907653eef3973e68398bf3d90ca1d3e25bf6530e7031cbe6eb307813`.
Não é um processo determinístico. O SHA-256 deve identificar o output final
concreto que foi testado, não uma recompilação posterior.

`marks_calculator` é o único módulo validado localmente. `core/updater/versioning`
e `core/updater/manifest` continuam apenas candidatos estáticos; não foram
protegidos nem aprovados. Não foi criada uma allowlist de release nem ativada
ofuscação no build normal.

**WoT real: sessão 22:59–23:14 de 8 de outubro de 2026 revista.** O log confirma
o carregamento de `driftkings-pjorion-poc.wotmod`; o SHA-256 instalado corresponde
ao artefacto acima. Houve entrada em batalha e encerramento normal, sem erros do
calculator/PJOrion nem mensagens `XXX lineno/opcode`. O utilizador confirmou
funcionamento normal. Isto valida este POC, não todos os futuros módulos protegidos.

O recibo da atualização oficial acusou corretamente `invalidResult`, porque o
POC foi instalado manualmente com outro nome/hash. Também houve erros na câmara
do Hangar e recursos gráficos ausentes; o log não os associa ao módulo protegido
e não permite determinar a sua causa. A instalação manual e estas ocorrências
não equivalem a validação do updater para a próxima beta.

## Teste manual controlado

Com o WoT e qualquer helper fechados, guarda o pacote beta.6 normal fora da pasta
ativa. Substitui temporariamente `mods/2.4.0.2/Driftkings.wotmod` pelo pacote
experimental, usando o mesmo nome. Não deixes os dois WOTMOD ativos ao mesmo tempo.
O pacote normal para reposição continua em `build/release/Driftkings.wotmod`.

Guarda também a pasta da transação anterior `cache/update/download-u_tcuv` fora de
`cache/update`, se ainda existir: a instalação manual do POC tem outro hash e a
verificação desse recibo antigo acusaria corretamente uma diferença. Isto evita
confundir o teste de ofuscação com o recibo da atualização oficial. Não alterar
configs do utilizador, tickets ou recibos para simular sucesso.

Depois do teste, a reposição do pacote oficial permite voltar à beta.6 aprovada.
Este procedimento não foi executado automaticamente e o pacote não foi publicado.
