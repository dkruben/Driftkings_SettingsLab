# MainGun — migração Gameface

Implementação integrada e publicada na beta 0.1.3-beta.2. Comandos e caminhos referem-se à raiz do repositório. Ver o [estado atual](STATUS.md) e o [guia de contribuição](../CONTRIBUTING.md).

## Integração e ficheiros

- `battle/high_caliber_progress.py`: eventos existentes de dano, roster, destruição, configurações e fim de batalha; publica agora o estado calculado.
- `core/high_caliber.py` (novo): projeção única do objetivo, restante, elegibilidade, motivo e progresso; usada pelo módulo de batalha. O frontend não recalcula regras de jogo.
- `views/battle/high_caliber_gameface.py` (novo): filho de `RandomHUDView`, modelo Wulf, payload JSON deduplicado, visibilidade nativa/TAB/cursor, persistência de posição e destruição dos filhos próprios.
- `views/battle/high_caliber_progress.py`: removido, juntamente com o fundo PNG exclusivo da apresentação Scaleform.
- `gui/gameface/mods/driftkings/high_caliber_gameface/` (novo; `model.html`, `main_gun.css`, `main_gun.js`): layout, CSS e JavaScript ES5. Painel 290 × 84 unidades de UI, carvão/dourado, medalha 44 × 44, barra com transição de 200 ms. Texto transmitido por `textContent`.
- `interface_catalog.py`, recurso `gen_resources/driftkings.high_caliber_gameface.json`, bootstrap gerado e `build_data/components.json`: registo e empacotamento. Reutiliza `shared/marks_panel.js`, sem alterar esse helper nem os outros painéis.
- `settings/definitions/battle/high_caliber_progress.py`, `settings/settings_data.py` e JSON default: controlos e aplicação imediata.
- Catálogos `mod/res/mods/driftkings/text/*.yml`: chaves MainGun nos 18 idiomas existentes; rótulos comuns reutilizados. Traduções novas beneficiam de revisão por falantes nativos.
- `settings/default_values.py` e snapshot: regenerados com `generate_defaults.py --write --refresh-snapshot`.
- `tests/core/test_high_caliber.py`, `tests/settings_panel/test_main_gun.js` e inclusão no `test_gameface.js`: regressões portáveis e de apresentação.

## Configurações

Mantidas: `enabled`, `mainGun.enabled`, `mainGun.dynamic`, `textPosition` (incluindo alinhamento), `textLock`, `backGroundEnabled` e `background.alpha`.

Novas: `gameface.scale`, `gameface.accentColor`, `gameface.showPercentage`, `gameface.showProgress`, `gameface.showSecondary`.

Posição, bloqueio e opacidade reutilizam os campos antigos. O arrastamento usa o cursor existente, com posição desbloqueada. O default EU atual desativa o fundo (`backGroundEnabled: false`) e guarda `background.alpha: 80` para quando for ativado; valores personalizados existentes são preservados.

Gameface é a única apresentação. Foram removidos o seletor `renderer`, os formatos HTML/macros, sombras Scaleform e os campos antigos de imagem/largura/altura do fundo. A normalização de configurações remove apenas essas propriedades obsoletas ao carregar/aplicar, preservando as opções atuais e posições. Um `renderer: legacy` residual nunca oculta o novo painel. Os ficheiros do cliente não foram editados diretamente; a limpeza chega pelo fluxo normal de configurações.

## Cálculo e correções comprovadas

Mantidos mínimo de 1000 HP e arredondamento para cima de 20% dos HP máximos inimigos. Em modo dinâmico, o objetivo é o maior entre a base e o dano acompanhado dos concorrentes elegíveis; em modo estático é a base. Preservado o tratamento existente de empates (sem acrescentar 1 HP).

- As chamadas antigas de apresentação estavam comentadas; existe agora publicação efetiva.
- Um concorrente à frente deixa de significar impossibilidade: a barra pode recuar e o jogador recuperar.
- Dano aliado torna a elegibilidade persistente durante a batalha; causar mais dano não a repõe. Concorrentes que se tornam inelegíveis deixam de elevar o objetivo.
- A impossibilidade considera os HP inimigos restantes, incluindo zero, e a destruição do próprio veículo quando ainda falta dano. Um objetivo já cumprido não é anulado apenas pela destruição.
- A diferença temporária entre eventos de saúde e feedback próprio é compensada na disponibilidade, sem somar o dano duas vezes.
- O modo estático também atualiza os valores de dano e a barra.
- Reset e desativação publicam a ocultação, evitando dados visuais da batalha anterior.

`achieved` significa apenas objetivo atual atingido. Não garante a atribuição oficial da medalha pelo servidor.

## Medalha original

Confirmada no cliente NA: `res/packages/gui-part1.pkg`, entrada `gui/maps/icons/achievement/32x32/mainGun.png`.

Gameface referencia `coui://gui/maps/icons/achievement/32x32/mainGun.png`, seguindo os recursos nativos já usados pelos outros painéis. O ícone não é recriado nem duplicado no mod. Não existe apresentação Scaleform nem cópia da medalha no mod.

## Validação local

- Baseline 0.1.3-beta.2: 413 testes core e 27 testes settings em Python 3 e Python 2.7; 33 testes do instalador em Python 3.
- Novos testes cobrem início, mínimo/arredondamento, dano, concorrência, regressão/recuperação, modo estático, elegibilidade, HP insuficientes/zero, ordem saúde-feedback, morte, reset, política de modos, listeners e adaptador Gameface.
- Node: painel existente e testes novos de estados, texto seguro, medalha, opções de visibilidade, arrastamento, resize, reinjeção e remoção de listeners.
- `validate_build_data.py`, ESLint ES5 e `node --check` em todos os JS.
- Compilação debug com Python 2.7, Flash e auxiliares; verificação dos novos recursos dentro do `.wotmod`.

## Pendente dentro do WoT

Ainda não foi validado numa batalha/replay real. Confirmar carregamento da medalha em Gameface, aspeto nas escalas/resoluções usadas, transição CSS, arrastar/persistir, TAB/ocultar HUD, reconfiguração durante batalha, coexistência com Marcas de Excelência, fim/nova batalha e todos os estados de dano. A política de modos original foi mantida: não foi ativado em Topography.

Os testes de DOM/stubs não substituem esta verificação no cliente.
