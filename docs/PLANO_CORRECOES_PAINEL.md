# Correções do painel — 2026-10-27

O lançamento stable 0.1.3 permanece suspenso e em rascunho. As alterações em curso do autor são preservadas; esta intervenção não publica nem instala uma build.

- [x] Analisar rolagem, botão Discord e pré-visualizações no código atual.
- [x] Permitir que a roda continue a rolar a página quando uma área interna ou textarea chega ao limite; atualizar a barra depois da montagem e limpar eventos/tarefas ao fechar.
- [x] Dar acesso por rolagem às descrições, detalhes, perfis e lista de elementos dos marcadores sem comprimir os respetivos itens.
- [x] Mostrar apenas `DISCORD` no botão, mantendo a ação e o destino existentes.
- [x] Corrigir a cor por omissão do texto dos marcadores para acompanhar a equipa/estado; descodificar entidades HTML em texto, preservando caracteres Unicode sem interpretar o resultado como marcação.
- [x] Ajustar a escala do HUD à área disponível e enquadrar todos os elementos do relógio ou painéis maiores no zoom.
- [x] Executar testes JavaScript, incluindo regressões de rolagem, eventos, caracteres e zoom; ESLint e `git diff --check` aprovados. Os testes de schema abrem 35 páginas e 1104 controlos.
- [ ] Confirmar visualmente no cliente os campos e previews indicados pelo autor; os testes de geometria usam medidas explícitas e não substituem o Gameface.

Sem commit, push ou alteração dos artefactos da release nesta intervenção.

## Seguimento — previews dos marcadores

O autor confirmou que os erros visuais se encontram nos marcadores. Corrigidos a atualização ao mudar opções gerais (a comparação anterior usava o conteúdo JSON como chave em vez do identificador do campo), a visibilidade quando o módulo está desativado, a vida de exemplo no estado destruído, as dimensões/alinhamento vertical/sombra dos textos e o gradiente configurado da barra de vida. Acrescentadas regressões para atualização de visibilidade e geometria/formatação dos campos. Suite JavaScript e ESLint aprovados; confirmação visual em jogo continua pendente.

## Capturas shot_029–032

- As capturas mostram o cenário do HUD sem os elementos esperados, além de descrições com placeholders de cor. Corrigida a interpolação de legenda e tooltip nas 18 línguas, sem duplicar o prefixo `#`; seis testes de controlos localizados aprovados.
- Acrescentadas camadas explícitas entre cenário, mira e elementos do HUD, e uma área de texto com dimensões explícitas. É uma medida de compatibilidade que precisa de confirmação no renderizador Gameface. Os testes verificam conteúdo e mudança de posição dos dois temporizadores, mas não reproduzem o desenho nativo.
- Acesso visual tentado: Computer Use sem pipe nativo, inventário de browsers vazio e IAB indisponível. Não houve validação visual no browser.
- O `game.log` EU contém avisos de macros de cor enviadas ao CSS e estilos não suportados. Os ficheiros `hud.js` e `markers.js` do WOTMOD EU instalado diferem do código local corrigido; as capturas não validam esta árvore de trabalho. A instalação EU não foi substituída.

## Carrossel — dados reais

- Ligada a preview ao inventário do cliente: até quatro veículos, selecionado primeiro, nomes/imagens reais, nação/classe/nível, premium, favorito, em batalha, multiplicador diário e estatísticas do mesmo coletor/cache usado pelo carrossel.
- As cores usam a função real do mod e a tabela escolhida no rascunho do painel. A cache é invalidada na mudança de conta e mantém a invalidação existente após sincronização dos dossiers. A recolha não é executada em batalha nem para outras páginas.
- Sem inventário disponível, mantêm-se os exemplos identificados como tal. Dados reais não são duplicados para preencher cartões vazios. A preview respeita o número de linhas configurado.
- Consultado o CSS original em `gui-part3.pkg`, `gui/gameface/_dist/production/mono/hangar/main/main.css` do EU 2.4.1.1. Aplicados os tamanhos/âncoras de base da imagem do veículo, bandeira e favorito, incluindo a variante de duas linhas. Outros elementos e variantes `mediaMedium`/`mediaLarge`/`mediaExtraLarge` continuam a necessitar de comparação visual; não se afirma equivalência integral ao cartão nativo.
- Testes cobrem limite e ordenação dos veículos, cache por conta, seleção da paleta no painel, consumo do snapshot no JavaScript, macros/ícones e fallback. A leitura de dados reais só acontece quando esta árvore for compilada e executada no cliente; não foi inspecionada a memória do processo nem substituído o WOTMOD EU.

## Compilação stable autorizada

Pedido do autor: commit em develop, convergir main, compilar stable 0.1.3 com aviso de painel em construção, regressar a develop e acompanhar CI. A autorização abrange a compilação; a publicação pública permanece suspensa. Aviso acrescentado ao painel nas 18 línguas, README e release.json.

## Seguimento após publicação 0.1.3 — orientação do autor

O autor clarificou que a preview do carrossel pode usar dois veículos e estatísticas fictícias: a prioridade é corresponder às regras que o mod aplica aos cartões. As alterações abaixo são locais em develop e não modificam a release publicada.

- Marcadores: referências de texto têm uma linha própria e botão de edição abaixo do campo; inputs podem encolher dentro da coluna. O teste percorre o botão, edita `def.tankName.format`, grava o documento correto e confirma que a referência original não é substituída por uma cópia.
- Carrossel: substituída a leitura de inventário/dossiers da preview por dois exemplos fixos, T32 e Obj. 140, identificados como exemplos. As cores continuam calculadas pela mesma API de estatísticas dos cartões reais, com a paleta em edição.
- Comparado o renderer de preview com `core.carousel.build_profile` e `vehicle_carousel/carousel_layout.js`: corrigidos cor/tamanho base do texto, tamanho independente do ícone, cor de fundo com macros, alinhamento flex e parâmetros de sombra. O nome do veículo passa a ancorar à direita.
- Testes JavaScript/ESLint e testes específicos Python 2.7/3 aprovados. A reprodução visual das proporções nativas, das variantes normal/compacto e da ausência de cortes a 140% ainda necessita de confirmação no Gameface. Não se considera a preview integralmente equivalente ao renderer nativo.
- A captura do carrossel real sem estatísticas não foi tratada como prova de falha de recolha: o autor esclareceu que a tarefa é a coerência da preview. Não foram alterados os hooks nem o renderer dos cartões reais nesta intervenção.
