# Registo de validação de <versão-beta>

<!-- dk-validation-record: 1 -->

Preenchido à mão por quem testou. Valores: `PASS`, `FAIL`, `NOT TESTED`, `NOT APPLICABLE`. Uma região nunca vale como prova de outra. Regras em [docs/releases/README.md](README.md).

## Identificação

| Campo | Valor |
| --- | --- |
| Versão | <versão-beta> |
| Estável alvo | <versão-stable> |
| Commit | <commit-completo> |
| Tag | v<versão-beta> |
| Versão do WoT | <versão-do-wot> |
| SHA-256 do pacote | <sha256-do-driftkings.wotmod> |

## Regiões

| Região | Decisão | Build do cliente | Data | Validador | Ambiente |
| --- | --- | --- | --- | --- | --- |
| EU | NOT VALIDATED | - | - | - | - |
| NA | NOT VALIDATED | - | - | - | - |
| ASIA | NOT VALIDATED | - | - | - | - |

## Testes automáticos

| ID | Verificação | Resultado | Evidência |
| --- | --- | --- | --- |
| auto.ci | GitHub Actions verde no commit da beta (python-package.yml) | NOT TESTED | - |
| auto.runtime | python -B tests/run_python.py --suite runtime | NOT TESTED | - |
| auto.build | python -B tests/run_python.py --suite build | NOT TESTED | - |
| auto.frontend | npm --prefix build_tools/javascript test | NOT TESTED | - |
| auto.artifacts | python -B tests/run_python.py --suite artifacts --wotmod <pacote da beta> | NOT TESTED | - |
| auto.signature | release.json.sig e SHA256SUMS.txt públicos verificados | NOT TESTED | - |

## Testes em jogo

| ID | Bloqueante | Verificação | EU | NA | ASIA | Notas |
| --- | --- | --- | --- | --- | --- | --- |
| install.clean | YES | Instalação limpa com o instalador, sem mods anteriores | NOT TESTED | NOT TESTED | NOT TESTED | - |
| install.manual | NO | Instalação manual com o ZIP e Driftkings-defaults.zip | NOT TESTED | NOT TESTED | NOT TESTED | - |
| install.upgrade | YES | Instalação sobre a stable anterior preserva perfis e configurações | NOT TESTED | NOT TESTED | NOT TESTED | - |
| updater.check | YES | O atualizador encontra a versão no canal escolhido | NOT TESTED | NOT TESTED | NOT TESTED | - |
| updater.apply | YES | O atualizador descarrega, verifica e aplica a versão após reiniciar | NOT TESTED | NOT TESTED | NOT TESTED | - |
| startup.client | YES | Arranque até ao hangar sem exceções Driftkings no game.log | NOT TESTED | NOT TESTED | NOT TESTED | - |
| startup.components | YES | Todos os componentes ativos carregam; nenhum fica desativado por erro | NOT TESTED | NOT TESTED | NOT TESTED | - |
| settings.panel | YES | Painel de configurações abre, aplica e guarda alterações | NOT TESTED | NOT TESTED | NOT TESTED | - |
| settings.profiles | YES | Perfis: criar, mudar, importar e manter as configurações | NOT TESTED | NOT TESTED | NOT TESTED | - |
| ui.gameface | YES | Vistas Gameface em batalha e no hangar sem erros de layout | NOT TESTED | NOT TESTED | NOT TESTED | - |
| ui.flash | YES | Vistas Flash/Scaleform em batalha carregam e atualizam | NOT TESTED | NOT TESTED | NOT TESTED | - |
| battle.players_panel | YES | Painéis de jogadores: painel lateral e TAB | NOT TESTED | NOT TESTED | NOT TESTED | - |
| battle.statistics | YES | Estatísticas de jogadores aparecem e aplicam-se sem paragens | NOT TESTED | NOT TESTED | NOT TESTED | - |
| battle.minimap | YES | Minimapa: círculos, nomes e tamanho do mapa | NOT TESTED | NOT TESTED | NOT TESTED | - |
| battle.markers | YES | Marcadores de veículos | NOT TESTED | NOT TESTED | NOT TESTED | - |
| battle.sixth_sense | NO | Alerta do Sexto Sentido | NOT TESTED | NOT TESTED | NOT TESTED | - |
| battle.high_caliber | NO | Progresso do High Caliber | NOT TESTED | NOT TESTED | NOT TESTED | - |
| battle.performance | NO | Battle Performance e textos de eficiência | NOT TESTED | NOT TESTED | NOT TESTED | - |
| battle.overlays | NO | Informação do alvo, limites de canhão, contagem de mira e penetração | NOT TESTED | NOT TESTED | NOT TESTED | - |
| battle.camera | NO | Câmara de sniper, zoom em terceira pessoa e sons | NOT TESTED | NOT TESTED | NOT TESTED | - |
| lobby.carousel | NO | Carrossel de veículos | NOT TESTED | NOT TESTED | NOT TESTED | - |
| lobby.hangar | NO | Preferências do hangar, marcas, tripulação e reparações | NOT TESTED | NOT TESTED | NOT TESTED | - |
| lobby.account_manager | NO | Gestor de contas | NOT TESTED | NOT TESTED | NOT TESTED | - |
| flow.consecutive | YES | Várias batalhas seguidas sem erros nem estado residual | NOT TESTED | NOT TESTED | NOT TESTED | - |
| flow.replays | YES | Replays abrem e terminam sem erros | NOT TESTED | NOT TESTED | NOT TESTED | - |
| mode.random | YES | Modo: batalhas aleatórias | NOT TESTED | NOT TESTED | NOT TESTED | - |
| mode.frontline | NO | Modo: Linha da Frente | NOT TESTED | NOT TESTED | NOT TESTED | - |
| mode.ranked | NO | Modo: batalhas classificadas | NOT TESTED | NOT TESTED | NOT TESTED | - |
| mode.other | NO | Outros modos disponíveis no cliente | NOT TESTED | NOT TESTED | NOT TESTED | - |
| performance.battle | NO | Desempenho em batalha comparado com a stable anterior | NOT TESTED | NOT TESTED | NOT TESTED | - |
| uninstall.reinstall | YES | Desinstalação e reinstalação preservam as configurações do utilizador | NOT TESTED | NOT TESTED | NOT TESTED | - |

## Problemas conhecidos

| ID | Gravidade | Estado | Verificação | Descrição |
| --- | --- | --- | --- | --- |

## Aprovação final

| Campo | Valor |
| --- | --- |
| Decisão | PENDING |
| Aprovado por | <nome> |
| Data | <AAAA-MM-DD> |
| Commit aprovado | <commit-completo> |
| Versão aprovada | <versão-beta> |
