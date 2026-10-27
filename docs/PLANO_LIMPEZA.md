# Limpeza de ficheiros sem utilização

Data: 27 outubro 2026.

## Âmbito e evidência
- Comparação com o plano de empacotamento, imports AST, referências dinâmicas, catálogo UI e documentação.
- Remover os quatro módulos inativos: `stats/ratings.py`, `gameface/lobby/preferences_hooks.py`, `flash/lobby/battle_performance_hooks.py` e `flash/lobby/hangar_preferences_hooks.py`. Os hooks ativos ficam em `native_preferences.py` e nos adaptadores registados.
- Remover oito mapas Gameface antigos não empacotados; o cliente usa `gui/gen_resources`.
- Remover o SWF antigo não empacotado; a build compila `flash_source/battle` para `build/flash`.
- Remover caches/conversões/bancos gerados do projeto Wwise, o índice `.mtimes_r` e as antigas saídas de auxiliares em `installer/build`.
- Consolidar o aviso do componente HangarEfficiency já retirado no STATUS, removendo a pasta documental dedicada.
- Manter WAV/WWU/WPROJ, bancos distribuídos, SDKs/dependências, configurações, fontes, chaves, preferências do editor e estudos locais citados nos relatórios.

## Etapas
- [x] Inventário e verificação de dependências.
- [x] Remoção e prevenção do reaparecimento de artefactos gerados.
- [x] Comparação do plano antes/depois, testes e build nativa.
- [ ] Atualização do release.json, commit/push e CI.

## Registo
- Selecionados 40 ficheiros (27 versionados), 3.43 MiB de artefactos e fontes obsoletas. Todos os alvos foram resolvidos dentro do workspace antes da eliminação.

- Removido o teste exclusivo do adaptador de estatísticas retirado (sem consumidor no runtime). A suite passa de 444 para 443 testes core; os testes dos cálculos ativos mantêm-se.
- Corrigida a mensagem de fallback dos resultados para referir a janela nativa, em vez de uma integração legacy já inativa. Regras de ignore/atributos e guias atualizados.

- Plano antes/depois: removidos apenas os quatro bytecodes inativos (317 → 313 módulos). Iguais os 264 assets, 53 defaults, componentes e dependências.
- Aprovados 443 testes core em Python 2.7/3, testes Gameface (35 páginas/1104 controlos), ESLint, 36 testes installer/build e verificador de nomes indefinidos.
- Verificação isolada: compilados os 313 módulos com Python 2.7 e regenerados o SWF de batalha e os três auxiliares nativos, totalizando sete outputs. O binário antigo e as antigas pastas de build não eram necessários.
- A build WOTMOD completa está bloqueada pela versão instalada: EU/NA 2.4.1.1 contra alvo 2.4.1.0. Não foi alterado o contrato de versão nem produzido um pacote para uma versão não validada. A limpeza não modifica os inputs de patches nativos.

- Após os testes, removidos também 470 bytecodes temporários e 22 diretórios `__pycache__` regeneráveis nas pastas de fontes/testes/ferramentas.
