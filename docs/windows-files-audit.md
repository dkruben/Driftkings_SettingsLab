# Fase 10.3 — auditoria anterior à alteração

Baseline windows_files.py: `212e2a8679d2baf9a60c4637f875dd0314329fea75e9aa25969560acfdd5df1d`.
L2 reproduziu interrupção do host durante safe_path(release.json), após quatro
lançamentos PowerShell observados, sem PJOrion; o utilizador confirmou ATD
`SuspiciousBehavior.234FFCC6F2F49D4`. Não se conhece a regra interna/limiar do AV.

| Função antiga | Inputs / outputs | Callers | Semântica e limitações |
| --- | --- | --- | --- |
| literal(path) | path local → expressão PowerShell de descodificação base64 UTF-8 | safe_path/replace_receipt; antigo teste de junction | os.path.abspath e mbcs→Unicode em Python 2.7. Encoding evita interpolação de shell, mas não valida a localização/namespace por si só. |
| run(script) | script interno → None ou OSError | safe_path/replace_receipt; testes antigos | Lança PowerShell oculto com EncodedCommand, pipes, timeout 10s. Exige exit=0 e stdout OK. Cria um processo por chamada. Não funciona se o host for terminado pelo AV antes da resposta. |
| safe_path(path) | path → None ou OSError | results.safe_path para fallback Windows sem atributos lstat; Results.scan/ticket/package/acknowledge | CHECK percorre path e ancestrais usando File.GetAttributes; recusa qualquer ReparsePoint. Missing file/directory são permitidos; outros erros bloqueiam. Python 2.7 lstat não expõe junctions de forma suficiente. |
| replace_receipt(source,destination) | source e destino no mesmo diretório → None ou erro | Results.acknowledge quando notified.json já existe | Valida ambos com CHECK e chama File.Replace(source,target,null). Caller já escreveu, flush/fsync/close do temporary. Target deve existir; não trunca target em falha. Sem backup nesta operação. |

Testes existentes: test_updater_results (junction, missing validator, falha de
replacement preservando notified.json), test_updater_smoke (recibos pós-restart,
paths Unicode, dedup e ausência de _ctypes), testes de Results/Installer/recovery.
Os testes antigos que invocavam run(script) para criar junction precisam de
fixtures Win32 reais; essa interface de scripts não é parte da API runtime a
preservar. safe_path/replace_receipt e comportamento de Results continuam iguais.

## Decisão de desenho

Python puro faz canonicalização/serialização e verificações de protocolo. No
Python 2.7/WoT, os.stat/os.path.islink não garantem todos os reparse points;
ctypes não está sempre disponível. Não foi comprovada outra API WoT que exponha
GetFileAttributes/ReplaceFile com todas as garantias. Não usar heurísticas nem
introduzir _ctypes obrigatório.

Criar `source/updater/WindowsFiles.cs`, helper próprio compilado localmente:
Win32 GetFileAttributesW para todos os ancestrais e ReplaceFileW para o recibo.
Servidor local via stdin/stdout, um processo por sessão de validação, sem shell,
rede, scripts ou polling. O processo termina com EOF/fecho do cliente ou morte
do pai. Pedidos serializados e bounded; timeout/EOF/erro bloqueiam, sem retry.

Protocolo fixo: validar path ou substituir temporary por notified.json, paths
UTF-8 em base64 apenas como dados de IPC. Root local fixado pelo cliente; recusar
escape, UNC/device namespaces, traversal, ADS e reparse de qualquer tipo. Mutação
restrita a notice-* → notified.json no mesmo download-* de cache/update próprio.
Nenhum pedido executa comandos arbitrários.

Binary e metadata são recursos do package; bootstrap valida tamanho/SHA-256 dos
bytes e do ficheiro escrito antes de lançar. O helper valida root, localização
do próprio executável e ancestrais na inicialização. Resources são obtidos no
client thread, não por trabalhadores de Results. A extração usa diretório privado
exclusivo dentro da cache própria; nunca reaproveita executável não verificado.
O helper não é ofuscado. Build/package validam também source/helper hash.

Segurança de substituição: valida source/target e ancestral, mesmo diretório e
volume, target existente e não read-only, source regular com prefixo notice-,
flush/close antes de ReplaceFileW. Nenhum fallback de copy/truncate/delete. Sem
backup, preservando a política atual. Erros Win32 explícitos, target conservado.
As verificações de atributos não eliminam todas as races TOCTOU do filesystem;
a implementação deve manter handles nos ancestrais durante cada operação para
impedir rename/delete de diretórios verificados até terminar.

Validação escalonada: testes Win32 reais sob build/diagnostics/windows-files-v2;
depois receipt-l2-v2 e gate humano; só após PASS+NO_ALERT, teste original isolado
e segundo gate. Suites/updater/PJOrion apenas após esses gates. Não repetir
diagnósticos antigos, não mudar AV nem publicar automaticamente.

## Referências e limites que devem permanecer explícitos

APIs documentadas: [GetFileAttributesW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfileattributesw),
[CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew),
[ReplaceFileW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-replacefilew).
GetFileAttributesW devolve atributos do próprio symlink. O bit reparse é
recusado sem distinguir tags; não existe uma allowlist de reparse points.

ReplaceFileW sem backup preserva a política antiga de File.Replace(..., null),
mas a documentação descreve erros raros 1176/1177 com efeitos parciais sobre
nomes/metadata. Não prometer rollback universal para todas as falhas possíveis
da API. Não há fallback destrutivo; locks/readonly/falhas prévias testadas
preservam os bytes do target. As corridas sobre leaf files não são completamente
eliminadas pelos handles mantidos nos diretórios ancestrais.

Bootstrap: o Python verifica os bytes e o ficheiro escrito antes do lançamento;
a validação nativa dos ancestrais da cache ocorre no startup, depois da extração.
Uma cache local previamente redirecionada por reparse pode portanto receber os
bytes do helper antes de a sessão recusar o startup. A cache é local e o helper
é fixo/verificado, mas não afirmar que a extração dispõe da mesma verificação
nativa anterior à escrita. Este limite precisa de revisão antes do PASS global.

Os testes reais cobrem junction (mount-point tag), symlinks e ACL access denied.
Não foi criada uma tag reparse desconhecida nem um volume adicional: esses casos
são bloqueados pelas mesmas regras de atributos/root, mas não têm fixture física
própria nesta etapa. Nenhuma claim de cobertura física adicional é feita.
