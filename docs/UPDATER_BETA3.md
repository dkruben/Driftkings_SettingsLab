# DriftKings 0.1.1-beta.3 e base corrigida 0.1.0

O cliente WoT não disponibiliza a extensão _ctypes. A beta.2 descarregava e
validava corretamente, mas a preparação falhava ao consultar atributos Windows
em Results.result_stamp, antes de lançar o helper. A leitura pós-restart também
precisava da mesma correção. Substituir notificações recorria ainda a MoveFileExW.

A correção remove a dependência ctypes dessas duas operações. Em Python com
st_file_attributes, os atributos nativos de os.lstat continuam a rejeitar reparse
points. No Python 2.7 do WoT, uma chamada fixa ao PowerShell/.NET incluído no Windows
consulta File.GetAttributes para o caminho e todos os seus pais. Também rejeita
junctions, inclusive quando o ficheiro final ainda não existe. Erros/indisponibilidade
bloqueiam a operação; não existe fallback que salte a validação.

A substituição do recibo usa File.Replace no mesmo diretório, preservando o recibo
anterior se falhar. Invoca o overload via reflexão para preservar backup=null,
pois o binding de Windows PowerShell converteria null para uma string vazia.
Os dados continuam a ser flush/fsync antes da substituição.

windows_files.py é uma função interna de operações de ficheiros, não um serviço
paralelo. Executa apenas o PowerShell de SystemRoot/System32, sem perfil, sem shell
ou janela, com limite de 10 segundos por chamada. Os caminhos são transportados
como base64 UTF-8 dentro de comandos fixos codificados em UTF-16LE: aspas, Unicode
e metacaracteres não são interpretados como comandos. Não instala pacotes, DLLs
ou Python; exige o PowerShell/.NET que acompanha o Windows. A disponibilidade real
desse executável no ambiente WoT continua sujeita ao teste no cliente.

Preserva schema, checks de ticket, geração/PID/freshness, tamanho/SHA-256,
identidade, VERSION carregada, Installer/helper, restart, TLS, configs e componentes.
A versão da nova beta é 0.1.1-beta.3, exclusivamente na fonte única VERSION.
A base de teste continua em 0.1.0; a beta usa a mesma correção. Sem PJOrion.
As releases anteriores não são substituídas. O SWF gerado e o ZIP removido
anteriormente não fazem parte deste commit.

## Teste no cliente

1. Fechar WoT e guardar backup do package instalado.
2. Instalar build/updater-test-base/Driftkings.wotmod (base corrigida 0.1.0).
3. Antes de remover staging antigo, confirmar que não há helper ativo nem instalação
   preparada. Se existir, cancelar na UI e aguardar cancelled/exit 3 primeiro.
4. Mover apenas a pasta download-* da beta.2 para um backup fora de cache/update.
   Não apagar tickets, resultados ou configs e não editar versões/hashes no manifest.
5. Abrir WoT, canal Beta, procurar 0.1.1-beta.3 e descarregar até READY.
6. Preparar helper e confirmar RESTART_REQUIRED, depois reiniciar pelo fluxo existente.
7. Confirmar instalada 0.1.1-beta.3, hash correto, result.json válido e notificação
   apenas uma vez. Rever game.log também no novo arranque.

A aprovação automatizada não certifica o restart real via WGC. A sequência só
estará concluída com verificação no cliente e no arranque seguinte.

## Estado da validação local

- Suite Python completa: 681/681, incluindo os 15 testes nativos do helper,
  instalação e rollback, validada com o WoT fechado.
- Smoke Python 2.7: 9/9 sobre a base compilada e 9/9 sobre a beta.3 compilada,
  incluindo ausência simulada de ctypes/_ctypes.
- Settings Gameface, Hangar/TechTree, dependências e UI bridge: passaram.
- Contratos Python/Flash: 9; i18n: 12 catálogos sem erros; diff --check passou.
- Package beta: CRC, identidade, entry point, recursos e 246 módulos Python 2.7
  válidos; fontes, defaults e imports passivos verificados.

Base 0.1.0: build/updater-test-base/Driftkings.wotmod, 6 681 640 bytes.
SHA-256: df5c15e9be4426eeaa4b88a4d0248fc80144f2c66e77c21e34b60cfe544d3fce.

Beta.3: build/release/Driftkings.wotmod, 6 681 654 bytes.
SHA-256: de36e666a4b1df0872f7e2590143018132f3eaca5a43ed524a3fe0b14db719c7.
Manifest schema 1, canal beta, gameVersion 2.4.0.2, URL prevista para v0.1.1-beta.3.
Publicação autorizada como prerelease com três assets e sem marcar Latest stable;
o download publicado será verificado com o updater real antes da entrega.
Nenhum package ou configuração da instalação do jogo foi alterado.
