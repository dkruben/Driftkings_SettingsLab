# DriftKings 0.1.1-beta.4 e base 0.1.0

O game.log registou um crash nativo imediatamente depois da preparação. Não houve
confirmação prepared nem substituição do package. O helper gravado tinha 18 294 bytes,
contra 17 920 no recurso original. A comparação byte a byte confirmou exatamente
a substituição de cada LF por CRLF (374 bytes acrescentados). A sequência do log
localiza o crash na tentativa de lançamento; o dump nativo não foi analisado.

WoT usa um CRT cujo modo por omissão para descritores é texto. os.fdopen(..., 'wb')
não corrigia esse modo no seu Python 2.7. As criações exclusivas os.open do helper
e metadata passam a usar O_BINARY explicitamente no Windows. Depois de fechar e
flush/fsync o helper, o Installer valida o ficheiro, tamanho e SHA-256 no disco
contra o recurso próprio. Só depois volta a confirmar contexto, grava ticket e lança.
Se os bytes diferirem, não lança e remove apenas os ficheiros que acabou de criar;
preserva READY, manifest, package instalado e configurações.

Esta correção altera só a fronteira de escrita/validação do Installer Python.
Não altera o helper C#, schemas, restart, TLS, downloads ou componentes.
Mantém as correções anteriores de redirects e ausência de _ctypes.
VERSION muda na fonte única para 0.1.1-beta.4. A base de teste mantém 0.1.0.
Sem PJOrion. Builds/metadata locais em build/, sem deployment automático.
O SWF gerado e a remoção preexistente do ZIP ficam fora do commit.

Testes novos cobrem bytes LF/CRLF/NUL/0x1A/0xFF, corrupção do helper escrito sem
alterar o tamanho (nunca lança) e execução da mesma escrita no Python 2.7 com o
modo de texto do CRT explicitamente simulado. Os testes nativos usam o helper real
apenas em raízes/processos fictícios sob build/.

## Repetir o teste no cliente

1. Fechar WoT e confirmar ausência de helper ativo.
2. Guardar backup do package instalado e instalar a base corrigida
   build/updater-test-base/Driftkings.wotmod, mantendo configs.
3. Mover toda a pasta da operação antiga download-d_7zze para backup fora de
   mods/configs/Driftkings/cache/update. Contém um executável corrompido e ticket da
   beta.3; não reutilizar nem editar manualmente o ticket, versão ou hashes.
4. Abrir WoT, canal Beta, procurar 0.1.1-beta.4 e descarregar até READY.
5. Preparar instalação. Confirmar prepared e RESTART_REQUIRED antes do restart.
   O helper gravado deve corresponder exatamente ao tamanho/hash do helper.json.
6. Reiniciar pelo diálogo existente. Confirmar VERSION 0.1.1-beta.4, resultado
   installed e SHA-256 no disco; não inferir sucesso só pela janela fechar.

A validação automatizada não certifica o restart real no WoT/WGC. É necessário
confirmar o próximo arranque. Releases anteriores ficam intactas; beta.4 é prerelease,
sem marcar Latest stable, com WOTMOD, release.json schema 1 e checksum.

## Validação final

- Python: 684/684, incluindo helper nativo, instalação e rollback.
- Smoke Python 2.7: 10/10 sobre fontes, base compilada e beta.4 compilada.
- Settings Gameface, Hangar/TechTree, dependências e UI bridge: passaram.
- Contratos Python/Flash: 9; i18n: 12 catálogos sem erros; diff --check passou.
- CRC, identidade, entry point, recursos e 246 módulos Python 2.7 válidos.

Base 0.1.0: 6 681 832 bytes.
SHA-256: cb9ebdfc52e2beac43c6b4373123728f68fad37deb24046b8c92d50ea1ff78b2.

Beta.4: 6 681 846 bytes.
SHA-256: 1bdeb1b3d5fa59febdc6f04e9834fcbbab1a51f98f29c49637870753ad6227e4.
Manifest schema 1, canal beta, gameVersion 2.4.0.2, URL oficial do asset beta.4.
O download publicado será novamente verificado pelo updater antes da entrega.
