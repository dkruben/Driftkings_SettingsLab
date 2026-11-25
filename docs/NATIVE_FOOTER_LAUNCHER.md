# Driftkings Native Integration — Fase 2

2026-11-09. Branch `feature/wot-2.4.2-ct`, baseline `a19f5d7173ed71a6d091cc9c812291b3acef2654`.

**Fase 2 — Validada funcionalmente no CT 2.4.2.0 sem ModsListAPI.** O autor confirmou os controlos e o ciclo de regresso ao hangar. Outras versões WoT, modos e escalas exigem revalidação. OpenWG continua utilizado e ambos os pacotes externos permanecem no contrato de distribuição. Não constitui distribuição autónoma, publicação ou implementação da Fase 3.

## Decisão e contratos

O cliente CT instalado declara `2.4.2.0 Common Test #995`. A fonte CT `2.4.2.5516`, em `sources/res/scripts/client/gui/impl/lobby/page/lobby_footer.py:36`, implementa `_initChildren`; `frameworks/wulf/view/view.py:211` expõe `setChildView`. Não foi encontrado um slot público dedicado a botões de mods. Foi escolhido um hook mínimo que chama primeiro o original e preserva o retorno, através do gestor de hooks existente.

O bundle CT em `res/packages/gui-part3.pkg`, entrada `gui/gameface/_dist/production/mono/hangar/footer/bundle.js`, coloca `div[data-test-id="menu"]` numa secção `Footer_section_*`. Este é um contrato DOM interno sujeito a alterações. O frontend insere exclusivamente um botão próprio nessa secção. Se a âncora estiver ausente/incompatível, não desenha um botão flutuante. Um MutationObserver acompanha reconstruções por eventos; não há polling contínuo.

O carregamento do frontend utiliza o OpenWG existente: `payload_model` → `gf_mod_inject` → bootstrap Driftkings → assets declarados no catálogo. Não foi substituído o injetor, o seu ViewModel ou `gui/gameface/js/index.js`. O bootstrap só recebeu a entrada gerada do novo catálogo. Os bundles produzidos pelas integrações anteriores continuam a ser gerados sem qualquer patch novo para o launcher.

Comp7, Comp7 Light, Last Stand e Battle Royale redefinem `_initChildren` sem chamar o método base; as respetivas classes opcionais recebem o mesmo hook. Não há integração visual alternativa quando o DOM é incompatível. Cada modo precisa de teste em jogo.

## Propriedade e comportamento

`gameface/lobby/launcher.py` pertence ao serviço `settings_panel`. Guarda referências fracas a views/footers, não substitui filhos existentes e descarta as suas views ao parar. O evento Wulf `onOpen` chama diretamente o controlador atual; este continua a impedir janelas duplicadas e a validar contextos. O botão só é visível em LOBBY. Não foi introduzida abertura no login. O atalho `openKey`, perfis, schema/state e janela de configurações não foram alterados.

O frontend usa `__dkFooterLauncher`, classes `driftkings-launcher*`, ícone próprio existente e o título localizado das configurações como label/title. Hover, pressed e escala usam CSS restrito ao botão e unidades rem. A apresentação efetiva do tooltip/title precisa de verificação no Gameface.

A remoção do modelo ou a destruição do owner limpa botão, callbacks, listeners, observer e trabalho agendado. A ausência de ModsList não é necessária para importar/iniciar o serviço; não existe registo ativo Driftkings em `addModification`. A deteção passiva mantém-se. Não se elimina nenhum pacote instalado por outro mod.

## Distribuição e versões

Ambos os `.wotmod` externos continuam declarados em `build_data/build_config.json`. OpenWG continua obrigatório. ModsList continua incluído na distribuição, embora já não seja utilizado como ponto de entrada Driftkings. Esta fase não é packaging autónomo.

A build local preserva o ciclo CT: `--version 0.1.8-beta.2 --keep-source-version`; o código e os metadados mantêm `0.1.8-beta.1`. Sem instalação no cliente, commit, push, tag ou release.

## Validação automática

Os testes novos executam o código real do launcher e do serviço com fronteiras do cliente simuladas; também exercitam o controlador de configurações existente. Cobrem ausência de utilização da API ModsList, callback, contexto, atalho, janela única, reentrada, falha de attachment com log, variantes opcionais e descarte.

O teste frontend executa o script real num DOM simulado: botão único dentro da secção, clique, alteração dos modelos, substituição da âncora, ausência de âncora, reinicialização e limpeza. Verifica seletores CSS restritos e estados hover/pressed. Não prova layout, foco ou escala no motor real.

Resultados finais: 851 testes Python 3 (runtime/build), 670 testes runtime Python 2.7, 20 suites frontend e três testes de artefactos compilados aprovados. Lint ES5, imports, nomes indefinidos, defaults, 18 traduções (zero pendentes), catálogo e contratos aprovados. O diff não contém alterações no controlador/janela, perfis, build_config, release.json, código OpenWG ou bundles globais.

Build debug CT concluída com compilação Python 2.7 de 307 módulos, contratos de recursos CT e verificação do pacote. Artefacto: `build/debug/beta/0.1.8-beta.2/driftkings.wotmod`. Cinco entradas novas do launcher presentes; os quatro recursos não compilados correspondem às fontes. Não contém `res/gui/gameface/js/index.js`.

SHA-256: `41d2e35472e2d51165125ae4de21aa0965df3b369bf9c48ba63cc43807515adf`.

Comandos principais executados:

```powershell
python -B tests/run_python.py --suite all
F:/Python27/python.exe -B tests/run_python.py --suite runtime
npm --prefix build_tools/javascript test
npm --prefix build_tools/javascript run lint
python -B build_tools/validate_build_data.py
python -B build_tools/validate_locales.py
python -B build_tools/generate_defaults.py --check
python -B build_tools/generate_ui_catalog.py --write
python -B build_tools/check_undefined_names.py
python -B -m isort --settings-path mod/res/scripts/client --check-only mod/res/scripts/client
python -B build_tools/compiler.py --mode debug --channel beta --version 0.1.8-beta.2 --keep-source-version --game-root C:/Games/World_of_Tanks_CT --reference-root E:/Wot_Mods_/Drift_Kings_ModPack/WoT_Tools/wot-src-CT
python -B tests/run_python.py --suite artifacts --wotmod build/debug/beta/0.1.8-beta.2/driftkings.wotmod
```

Uma primeira execução do novo teste do controlador falhou por falta do stub de `gameface_spec`; foi corrigida a fronteira do teste, sem alterar o controlador. As execuções finais acima passaram. Os testes de backend não usam a API ModsList; a coexistência com bibliotecas e outro mod reais, hover/renderização, foco e escalas permanecem pendentes no cliente.

## Aceitação manual obrigatória no CT

- Validar o botão dentro do footer, sem deslocar ou alterar os botões nativos, em várias resoluções/escalas.
- Abrir/fechar por clique, X, Esc e atalho; verificar foco/modalidade, perfis e alterações não guardadas.
- Repetir login → hangar → batalha/replay → hangar; confirmar ausência no login e nenhuma janela/botão duplicado.
- Confirmar reconstrução do footer e os modos especiais suportados.
- Cenário A: ModsList ausente e OpenWG presente. Cenário B: ambos presentes. Cenário C: ModsList utilizado por outro mod. Não remover bibliotecas partilhadas de uma instalação pessoal para preparar estes cenários.
- Rever `game.log`, consola e descarregamento. Não confundir estes pontos com resultados dos testes simulados.

## Rollback específico

Não executar reset/clean. Preservar antes qualquer trabalho posterior.

1. Repor apenas os hunks desta fase em `settings/__init__.py`: retirar criação/refresh/stop do launcher e restaurar o registo ModsList existente na baseline.
2. Retirar `DriftkingsFooterLauncher` do `interface_catalog.py` e as duas entradas novas de assets em `build_data/components.json`.
3. Retirar apenas o novo módulo launcher, JSON de recurso e diretório frontend `launcher/`, depois de confirmar que não contêm alterações posteriores.
4. Regenerar o catálogo com `python -B build_tools/generate_ui_catalog.py --write`.
5. Retirar os testes novos desta fase e restaurar a contagem/expectativa do catálogo apenas se o launcher for efetivamente removido.
6. Atualizar os guias afetados e recompilar uma build debug CT. Para teste em jogo, reinstalar o pacote anterior previamente identificado, preservando os perfis.

Não tocar nos perfis, bibliotecas externas, worktrees ou recursos de outros mods. A baseline está identificada para comparação; não é uma instrução para repor o repositório inteiro.

## Instalação autorizada — 2026-11-09

Após autorização explícita do autor, o pacote acima foi instalado em `C:/Games/World_of_Tanks_CT/mods/2.4.2.0 Common Test/driftkings.wotmod`. SHA-256 instalado confirmado: `41d2e35472e2d51165125ae4de21aa0965df3b369bf9c48ba63cc43807515adf`.

Backup verificado do pacote anterior: `build/backups/ct-footer-launcher-20261109-044034/driftkings.wotmod`, SHA-256 `714e08cf625f981596e765d91ef12cede2fe9184af68ca46aeaa1d4d02d0c8f9`. Para reverter apenas a instalação, com o CT fechado, copiar esse backup para o mesmo destino CT e confirmar o hash anterior.

O CT estava fechado; o processo WoT observado pertencia ao cliente NA e não foi interrompido. Apenas o pacote Driftkings CT foi substituído. Perfis, dependências, pacote de nevoeiro e clientes de produção foram preservados. O jogo não foi iniciado; validação visual/funcional continua pendente. As declarações anteriores de “sem instalação” descrevem o checkpoint de implementação anterior a esta autorização.

## Confirmação do autor e revisão do log — 2026-11-09

O autor declarou ter testado o launcher e confirmou que visualmente e funcionalmente está a funcionar. Esta é uma confirmação do cenário efetivamente testado, sem declaração individual de todos os modos, resoluções, atalhos, ciclos ou cenários de coexistência.

Foi lido `C:/Games/World_of_Tanks_CT/game.log`, sessão de 04:41:33–04:43:32, 751 linhas; SHA-256 do log observado: `ad59f707d56f345328f9ad69c989430dfe2714125a82bfb6b139ae56f2db4dd4`. O pacote instalado mantém o hash de build documentado. O log confirma CT #995 e Driftkings `0.1.8-beta.2`; na linha 360 o arranque regista todos os serviços ativos, `failures=[]` e `disabled={}`.

Não foram encontrados Traceback, ReferenceError, TypeError, SyntaxError, falha de attachment do launcher, rejeição do filho, payload inválido do launcher ou falha de carregamento de assets Driftkings. A ausência dessas mensagens não prova isoladamente a apresentação: a confirmação visual/funcional é a declaração do autor.

Há seis entradas ERROR: quatro de ficheiros de partículas do BZ-75 (linhas 297–300) e duas de carregamento de imagens SVG data URI dos ícones YouTube/GitHub do painel (linhas 635 e 637). Não são erros identificados do launcher. Os recursos sociais não foram alterados nesta fase; não foi estabelecida a causa destas falhas. Existem ainda avisos nativos de texturas e MouseCursor no encerramento, sem atribuição causal ao launcher. Não se declara o log integralmente limpo.

ModsList e OpenWG foram ambos carregados nesta sessão (linhas 178–179). Portanto, há confirmação real com ambas as bibliotecas presentes, mas não prova em jogo do cenário sem ModsList ou com outro mod dependente dela. Não foram aplicadas correções de código, nova build, instalação, commit ou push durante esta revisão. A Fase 3 não foi iniciada.

## Fase 2.5 — sessão sem ModsList e recuperação — 2026-11-09

**PENDENTE — teste real incompleto quanto à confirmação manual dos controlos. Arranque independente confirmado pelo log.**

O pacote ModsList foi temporariamente movido, com o CT e processos associados fechados, para `build/backups/ct-modslist-isolation-20261109-045123/me.poliroid.modslistapi_1.8.0.wotmod`. Hash antes/depois: `c6e4a1d9476b0195c3b4fab392cf5d68c00f1d02fd79e29bd7424ebda88b498c`. Os outros 88 ficheiros de mods/res_mods mantiveram os hashes no isolamento. OpenWG e Driftkings permaneceram nos hashes documentados. O inventário anterior não encontrou outra distribuição carregável ModsList nos caminhos inspecionados.

Após o pedido do autor para analisar os logs, foi revista a nova sessão de 04:52–04:53 no `game.log` acumulado. Não confundir com a sessão anterior de 04:41, que carregou ModsList. Na nova sessão, OpenWG foi carregado (linha 929), sem referências ModsListAPI; Driftkings `0.1.8-beta.2` iniciou com todos os serviços ativos, `failures=[]`, `disabled={}` (linha 1110). Não foram encontrados Traceback, ImportError, ReferenceError, TypeError, SyntaxError nem mensagens de falha do launcher. O pacote ModsList continuava ausente do destino ao analisar o log.

SHA-256 do log acumulado observado (1496 linhas): `dccdd9a6ae51499731d63829b06c51f3dfebb24b0f58ed12543046a0de7a4034`.

A sessão nova contém dez entradas ERROR: quatro de partículas BZ-75 (1044–1047) e seis de carregamento de SVG sociais Discord/Facebook/YouTube/GitHub do painel (1370, 1372, 1374, 1376, 1380, 1382). Estes erros são registados separadamente e não foram corrigidos nesta tarefa. Não se declara o log integralmente limpo.

A confirmação anterior do autor sobre funcionamento visual dizia respeito à sessão com ambas as bibliotecas. O pedido “podes ver logs” não confirma individualmente botão/hover, abertura, X, Esc, atalho, unicidade e regresso ao hangar no cenário sem ModsList. Esses itens continuam PENDENTES até declaração do autor.

Com o CT fechado e destino livre, o pacote foi restaurado por cópia da localização de recuperação; hash original confirmado. A cópia de recuperação foi preservada. Os restantes ficheiros de mods/res_mods, incluindo perfis, OpenWG e Driftkings, mantiveram os hashes durante a restauração. Não foram alterados código, testes, build, instalador ou Git. Apenas este registo documental e STATUS foram atualizados após existirem resultados. Sem Fase 3.

## Encerramento formal da Fase 2 — 2026-11-09

**FASE 2 — CONCLUÍDA E VALIDADA NO CT SEM MODSLISTAPI.**

No pedido de encerramento, o autor confirmou explicitamente, para o teste real sem ModsListAPI: botão visível e funcional no footer, hover e integração visual corretos, abertura das configurações, fecho por X e Esc, atalho configurável, funcionamento após regresso ao hangar e ausência de duplicações. Esta declaração resolve as pendências manuais do registo anterior; não equivale a teste de todos os modos, resoluções ou versões futuras.

A evidência de runtime permanece a sessão sem ModsList descrita acima: OpenWG carregado, serviços Driftkings ativos, `failures=[]`, `disabled={}`, sem falhas de import ou do launcher. ModsList foi restaurado com hash original confirmado e cópia de recuperação preservada. Os erros conhecidos de partículas e SVG sociais permanecem separados e não foram corrigidos.

O launcher é próprio do Driftkings e usa o controlador existente. ModsListAPI deixou de ser necessário para abrir as configurações; OpenWG continua necessário. Os dois pacotes externos permanecem no contrato atual e só serão retirados numa fase posterior de packaging, após a migração correspondente. A compatibilidade com futuras versões WoT requer revalidação dos contratos Wulf e DOM.

Revisão final: sem imports/registo ativos ModsList no serviço; callback original preservado; hook chama o original primeiro e devolve o seu resultado; unicidade e descarte cobertos pelos testes e pelo cenário declarado. Nenhuma alteração ao controlador, perfis, bibliotecas externas ou bundles globais. Não houve refatoração do código validado no encerramento. Verificações finais repetidas conforme pedido; resultados registados no relatório de encerramento. Um único commit local da Fase 2 é autorizado, sem push. A preparação da Fase 3 é exclusivamente de leitura, sem PoC implementado.

Verificação final de encerramento repetida em 2026-11-09: `python -B tests/run_python.py --suite all` (851 aprovados), `F:/Python27/python.exe -B tests/run_python.py --suite runtime` (670 aprovados), `npm --prefix build_tools/javascript test` (20 suites), lint ES5, contratos de build, catálogo UI, 18 traduções/zero pendentes, defaults, nomes indefinidos, imports e diff check aprovados. Sem nova compilação ou instalação.
