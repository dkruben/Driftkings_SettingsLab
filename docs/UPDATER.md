# Updater — fases 2 a 7

Implementado: versionamento, manifest schema 1, estado observável, checker de
metadata, download verificado e integração com Core/Settings. A Fase 5 acrescenta
o mecanismo interno de installer/helper/rollback descrito em
[UPDATER_INSTALLER.md](UPDATER_INSTALLER.md). A Fase 6 liga-o ao serviço e aos
contextos existentes, conforme [UPDATER_CONTEXT.md](UPDATER_CONTEXT.md), sem novos
botões de instalação nessa fase. A Fase 7 completa a UI, coordenação com o restart
existente e resultado pós-restart: [UPDATER_UI.md](UPDATER_UI.md).
Os detalhes seguintes das Fases 2–4 registam o estado histórico.
Não há ofuscação nem publicação de release.

## Integração

`UpdaterService` entra depois de SettingsService na lista default do Core. Os
serviços injetados explicitamente continuam intactos. Contexts entrega LOGIN e
LOBBY ao serviço, sem outra subscrição a appLoader. `stop()` cancela pedidos,
invalida callbacks tardios e remove a ligação ao SettingsAPI.

Check automático: contexto LOGIN/LOBBY, intervalo de quatro horas e preferência
autoCheckUpdates ativa. Check manual ignora o intervalo e a preferência automática.
Ambos impedem checks simultâneos. Uma mudança de canal invalida a operação antiga.
Não existe polling periódico de updates, gravação de estado como config ou
operação de instalação. Durante uma transferência, um callback gerido pelo Core
a cada 250 ms entrega eventos do worker; termina com a operação e é cancelado
no stop. O worker não chama APIs do cliente nem atualiza State diretamente.

Preferências novas na página existente do sistema: autoCheckUpdates=true e
updateChannel=stable. Usam o store existente, sem alteração de persistência ou
migração de perfis. Não são gravados lastCheck, erro, progresso ou resultado.

Presenter expõe uma cópia de installedVersion, latestVersion, channel, status,
lastCheck, changelog e compatible. A janela observa State e liberta a subscrição
ao fechar. Changelog remoto usa textContent. A UI permite descarregar/cancelar,
sem ação de instalação ou restart. Percentagem representa bytes recebidos,
não sucesso da validação: os 100% recebidos ainda passam por VERIFYING.

## Transporte HTTPS

O serviço default do Core tenta construir um transporte urllib2/urllib.request
com SSLContext verificado, hostname checking e CA roots. Na ausência desses
recursos, fica indisponível sem usar HTTPS inseguro. O check automático não tenta
esse backend; a tentativa manual mostra ERROR/transportUnavailable, sem impedir
o arranque. Instâncias com API/transport injetados mantêm o contrato testável.

O checker funciona com transporte injetado. Contrato:

```text
request(url, callback, timeout, max_bytes) -> optional cancel handle
callback(Response(status, body, final_url), error)
```

O backend valida TLS e todos os redirects (máximo cinco), impõe limites durante
a transferência e entrega callbacks no thread do cliente. O checker
valida URLs antes do pedido, status, URL final e tamanho/JSON no recebimento.
O mesmo backend implementa stream(url, sink, callback, timeout, max_bytes, progress).
Não lê o package inteiro em memória: chunks de 64 KiB vão para o sink no worker.
Metadata é acumulada apenas até ao limite de resposta do checker.
Não usa proxies/credenciais implícitos nem aceita Content-Encoding comprimido.
O limite total é verificado entre operações; cada IO usa timeout de até 15 segundos.
Cancelamento é cooperativo: uma leitura bloqueada pode aguardar o timeout antes
de libertar o ficheiro parcial. O stop invalida entregas tardias imediatamente e
o worker remove o parcial ao terminar. Não há thread de polling permanente.

Endpoints e hosts estão centralizados em updater/endpoints.py. O checker consulta
até 50 releases numa resposta limitada a 1 MiB e apenas os assets release.json
do repositório oficial, com limite de 64 KiB cada. Nunca solicita a URL do WOTMOD.
Não há paginação nesta fase; não se promete pesquisa ilimitada do histórico.

Drafts são ignorados; tags admitem o prefixo v, enquanto a versão do manifest é
SemVer estrita. Stable aceita finais; beta considera beta, rc e finais. Nunca
considera versões anteriores/equivalentes à instalada. Metadata de build não
altera precedência. Versão/tag/prerelease/channel têm de ser coerentes.

Seleciona a maior versão nova compatível. Se só houver versões novas incompatíveis,
expõe a maior com compatible=false; versão WoT desconhecida também dá false.
O resultado é informativo, não uma autorização de instalação. Download exige uma
manifest selecionada e validada e compatibilidade atual do cliente/canal; erro ou
versão WoT desconhecida bloqueia a operação. Checks e downloads não se sobrepõem.

## Staging da Fase 4

Uma operação cria um diretório próprio download-* em
mods/configs/Driftkings/cache/update/. Dentro dele escreve apenas:

```text
Driftkings.wotmod.download
release.json
Driftkings.wotmod.ready
```

Os nomes são locais/fixos. A subpasta única evita colidir com outro READY; o manifest
não escolhe paths. release.json é uma cópia do contrato remoto validado para uso
futuro do installer, não uma release gerada/publicada pelo build.

Depois do EOF: flush/fsync, fechar, confirmar tamanho em disco, reler/calcular
SHA-256 e comparar com o manifest. Só então validar ZIP/CRC, identidade
driftkings.unified, versão, entry point único e magic Python 2.7. Rejeita paths
perigosos, entradas duplicadas sem distinção de maiúsculas, compressão/encriptação,
symlinks no arquivo, XML DTD e packages excessivos (5.000 entradas/128 MiB internos).
O arquivo é inspecionado; nenhum conteúdo é extraído nem executado.

Publica o manifest local completo antes de renomear o .download para .ready.
Erros removem os ficheiros próprios dessa operação, registam ERROR e mantêm a
versão instalada. Cancelamento volta a AVAILABLE após cleanup. Uma operação
interrompida pode deixar staging para recuperação/cleanup na futura fase do installer;
esta fase não retoma transferências nem procura/aplica READY de sessões anteriores.

READY significa descarregado e verificado; não significa instalado ou agendado.
Mesmo que termine em battle/replay, fica em staging. Não substitui o WOTMOD ativo,
não apaga configs, não executa restart e não cria helper externo.

A inspeção portable de paths rejeita links/reparse points quando a API do runtime
os expõe. Não certifica detecção completa de junctions em todos os Windows/Python 2;
a futura instalação nativa terá de validar os caminhos novamente.

## Contrato do manifest

Schema inteiro 1; versão SemVer; channel stable ou beta; gameVersion normalizada
em quatro segmentos; file exatamente Driftkings.wotmod; size inteiro de 1 a
64 MiB; SHA-256 de 64 hexadecimais; download HTTPS sem credenciais, em host autorizado.
Rejeita campos desconhecidos e campos JSON duplicados.

Opcionais: minGameVersion/maxGameVersion delimitam intervalo numérico que contém
gameVersion; sem cada limite, usa gameVersion nesse extremo. Changelog tem no máximo
50 entradas, 500 caracteres por entrada e 16 KiB de texto UTF-8 no total.
O documento completo tem no máximo 64 KiB. Não aceita paths/comandos remotos.

VERSION continua exclusivamente em Driftkings/__init__.py. O builder lê essa
atribuição por AST e valida-a com o mesmo parser usado pelo updater.

## Validação das fases 2 e 3, 2026-10-08

* Suite Python completa: 565/565, incluindo 41 testes novos.
* Settings Gameface: UI, check manual, botão bloqueado em CHECKING, changelog
  literal, compatibilidade informativa e ausência de ação de download.
* Hangar/TechTree, Gameface dependencies e UI bridge: passaram.
* Python 2.7.18: dois testes de contrato e imports/checker diretamente dos .pyc.
* Smoke Python 2.7 existente via SourceTree: passou.
* Compilação Python 2.7: 240 módulos, em build/scripts/client.
* Contratos Python/Flash: 9 componentes; i18n: 12 catálogos, zero erros.
* AIR HudVisibilityTest: 35 assertions.
* AIR PanelRenderTest: 41 assertions; MinimapAimTest: 61; SharedUtilsTest: passou.
* git diff --check: sem erros.

Os checks usam fixtures; não demonstram rede real nem execução desta versão no WoT.
Não foi gerado WOTMOD/release.json pelo build e o package instalado ficou intacto.

## Validação da Fase 4, 2026-10-08

* Python: 599/599; 32 testes específicos do downloader/transport/service e quatro
  contratos smoke executados também em Python 2.7.18.
* HTTPS real em Python 2.7.18 e Python 3: GitHub Releases respondeu 200, lista vazia;
  nenhuma release foi publicada e nenhum WOTMOD real foi descarregado.
* Compilação Python 2.7: 242 módulos, apenas em build/scripts/client.
* Os quatro testes smoke também passaram diretamente sobre esse bytecode compilado.
* Smoke Python 2.7 existente, Settings Gameface, Hangar/TechTree, Gameface
  dependencies, UI bridge, 9 contratos Python/Flash e 12 catálogos: passaram.

O ensaio 2.7 detetou que HTTPSHandler não aceita check_hostname como argumento.
A implementação passa apenas o contexto, cujo check_hostname permanece True;
o teste verifica isso nos dois runtimes. Não houve fallback de segurança.

O backend precisa ainda de validação dentro do WoT. SSL do Python local não prova
o SSL do motor. Downloader/staging foram testados com fixtures, incluindo hash/
tamanho incorretos, truncamento, excesso de payload, TLS/timeout/404, cancelamento,
concorrência, erros de disco, corrupção local, CRC/identidade inválidos e proteção
de configs/package instalado. Não foi gerada release nem feito deployment.
