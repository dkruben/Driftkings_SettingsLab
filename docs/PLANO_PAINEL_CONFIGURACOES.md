# Integração do painel de configurações

Origem: `C:/Users/Ruben/Desktop/GameFace_ConfigPanel/painel/gameface/settings_window`.

## Âmbito
Integrar o painel redesenhado pelo autor, mantendo o seletor de espectro atual do projeto (canvas, comparação, HEX, predefinições e opacidade), as fontes reais e o contrato Python de configurações. A pasta de origem e a instalação EU não são alteradas.

## Etapas
- [x] Inventariar os recursos e comparar os contratos das duas interfaces.
- [x] Integrar HTML, CSS, ícones e JavaScript; adaptar o seletor atual ao novo sistema de janelas.
- [x] Corrigir diferenças de contrato e preservar fontes, estados e validação dos marcadores.
- [ ] Verificar todos os módulos, controlos, fluxos e ciclo de vida; gerar build.
- [ ] Atualizar documentação e release.json; commit/push e validação GitHub.

## Registo
- O desenho novo usa schema/state/onAction existentes e acrescenta pré-visualizações de HUD, minimapa, texto e carrossel.
- O seletor novo de HSV será substituído pelo seletor de espectro existente. Os recursos de teste/simulador e pacotes sobrepostos não fazem parte da build.
- O relatório da origem descreve Aplicar sem gravação, mas o backend atual persiste; o contrato do backend continua a ser a autoridade.
- A aceitação visual no cliente será distinguida da verificação automatizada.

- Integrados os recursos de produção e o catálogo; removidos os módulos da interface anterior que deixaram de ser usados. O seletor de espectro mantém o algoritmo e o canvas originais, com o ciclo de vida da nova janela.
- Mantidas as fontes e as macros/cores reais dos marcadores. Corrigidos o acréscimo a listas vazias, a edição imutável, a reposição após rejeição e a limpeza de arrastos/tarefas de layout.
- Testes frontend abrem as 35 páginas e 1104 controlos reais, exportados pelo backend em ambiente isolado. Suite JavaScript/ESLint, catálogo, build data e nomes indefinidos aprovados.
- Inspeção visual bloqueada nesta sessão: o pipe nativo de Computer Use está indisponível e não existe browser IAB. Não se considera a apresentação validada em jogo.
