# Cache comum do Driftkings

Os ficheiros de cache e histórico gerados pelo pacote ficam numa única raiz,
independente do perfil de configurações selecionado:

```text
mods/configs/Driftkings/cache/
  gun_marks_battle/
    MarksOnGunBattle_stats.json
  gun_marks_hangar/
    progress_<accountID>.json
  stats/
    wn8exp.json
    xvmScales.json
    xte.json
    xtdb.json
```

`Driftkings/core/cache.py` define os caminhos e a migração. Os módulos pedem
a sua pasta uma vez na inicialização e usam-na tanto para leitura como escrita.
O histórico da garagem mantém um documento por conta; as estatísticas de batalha
mantêm a estrutura anterior, sem converter ou misturar os registos.

Ao iniciar com o pacote novo, são recuperados apenas os ficheiros de dados
conhecidos das pastas antigas `MarksOnGunBattle`, `MarksOnGunHangar`, `Stats/cache`
e `DriftkingsStats/cache`. Um ficheiro já existente no destino tem prioridade.
A cópia é publicada só depois de completa; os originais são preservados como
salvaguarda da migração e deixam de receber novas escritas.

Configurações, perfis, traduções, contas guardadas e a lista de veículos excluídos
do retorno de tripulação são preferências persistentes, não cache descartável.
O antigo nome `getCachePath` da tripulação refere-se a essa lista de preferências.
As caches do PlayerPanelPro, carrossel e cálculos de interface são apenas em memória:
não há ficheiros para transferir e não se acrescenta escrita em disco à batalha.

O histórico de marcas não é totalmente reconstruível a partir do estado atual
do jogo. A centralização não o apaga nem introduz limpeza automática.
O build não inclui dados de cache pessoais e não modifica a instalação do jogo.
