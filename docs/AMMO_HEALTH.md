# Vida integrada no painel de munições

Implementação CT local de 2026-11-07, ainda sem aprovação visual em batalha.

Em **Vida do veículo**, escolher um dos três novos estilos: **Painel de munições — Minimalista**, **Painel de munições — Clássica WoT** ou **Painel de munições — Driftkings**. Os cinco estilos anteriores e a escolha atual do perfil são preservados. Não é necessário repor configurações. Nos estilos integrados a posição é nativa: os valores X/Y do estilo flutuante são conservados, mas não deslocam o painel nativo.

O componente `DriftkingsAmmoHealth` é registado no pacote Flash existente e parentado ao `ConsumablesPanel` nativo. A largura vem de `basePanelWidth`, nunca de `DisplayObject.width`, que incluiria a própria barra. O evento `ConsumablesPanelEvent.UPDATE_POSITION` atualiza a geometria após layout/redimensionamento. A barra tem 26 px de altura e 8 px de intervalo acima dos slots, e herda transformações, escala, animações e visibilidade do painel. Não substitui os ícones nem a lógica de munições/consumíveis. As molduras são vetoriais, desenhadas no Flash; a imagem da conversa era uma proposta ilustrativa.

O tracker de vida existente fornece valor atual/máximo e cores configuradas aos adaptadores Gameface e Flash. Só um deles fica visível conforme o estilo. O transporte DAAPI reutiliza o cache de setters. A vida é ocultada fora do período de batalha e após destruição/câmara de morte. O suporte inicial mantém a condição de batalha com HUD Gameface do tracker existente; páginas sem esse HUD não mostram a barra. Páginas sem um `ConsumablesPanel` compatível não recebem uma barra flutuante de substituição. A pré-visualização representa um painel de seis slots; a largura real segue os slots nativos.

## Confirmar em jogo

- Alternar entre as três molduras e um estilo flutuante: apenas uma barra visível.
- Verificar vida cheia, dano, morte e entrada numa nova batalha.
- Confirmar alinhamento com diferentes números de slots, resoluções e escalas.
- Ocultar o HUD, abrir TAB e verificar ocultação/animação do painel e retorno.
- Confirmar tooltips, teclas e cliques nos consumíveis sem interferência da barra.
- Rever `game.log` após saída para detetar erros de registo ou descarregamento.

A build de teste mantém `0.1.8-beta.2` por instrução do autor; não constitui uma publicação.

## Verificação local

846 testes Python 3 e 665 testes runtime Python 2.7 aprovados; 19 suites frontend e lint ES5 aprovados. Catálogo de sete componentes Flash, defaults, traduções (zero textos ingleses pendentes), nomes e contratos CT aprovados. Compilação debug CT concluída; sem instalação ou publicação.

Pacote: `build/debug/beta/0.1.8-beta.2/driftkings.wotmod`.
SHA-256: `de1b46eadfc89e0d9d6eb3508c6d22ef57bc98099aa4e49cac263b5e59c96bc5`.

## Ponto de controlo — 2026-11-09

Commit e push autorizados pelo autor antes de iniciar a migração das dependências. Revalidação nesta data: 846 testes Python 3, 19 suites frontend, lint ES5, contratos de build, 18 traduções sem textos ingleses pendentes, nomes indefinidos, ordem dos imports e defaults aprovados. Os resultados Python 2.7 e a compilação acima pertencem à verificação anterior; não foram repetidos neste ponto de controlo. A validação visual em batalha continua pendente. ModsListAPI e OpenWG Gameface permanecem dependências do pacote atual.
