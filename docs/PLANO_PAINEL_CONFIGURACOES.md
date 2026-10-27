# Integração do painel de configurações

Origem: `C:/Users/Ruben/Desktop/GameFace_ConfigPanel/painel/gameface/settings_window`.

## Âmbito
Integrar o painel redesenhado pelo autor, mantendo o seletor de espectro atual do projeto (canvas, comparação, HEX, predefinições e opacidade), as fontes reais e o contrato Python de configurações. A pasta de origem e a instalação EU não são alteradas.

## Etapas
- [x] Inventariar os recursos e comparar os contratos das duas interfaces.
- [x] Integrar HTML, CSS, ícones e JavaScript; adaptar o seletor atual ao novo sistema de janelas.
- [x] Corrigir diferenças de contrato e preservar fontes, estados e validação dos marcadores.
- [x] Verificar todos os módulos, controlos, fluxos e ciclo de vida; gerar build.
- [x] Atualizar documentação e release.json; commit/push e validação GitHub.

## Registo
- O desenho novo usa schema/state/onAction existentes e acrescenta pré-visualizações de HUD, minimapa, texto e carrossel.
- O seletor novo de HSV será substituído pelo seletor de espectro existente. Os recursos de teste/simulador e pacotes sobrepostos não fazem parte da build.
- O relatório da origem descreve Aplicar sem gravação, mas o backend atual persiste; o contrato do backend continua a ser a autoridade.
- A aceitação visual no cliente será distinguida da verificação automatizada.

- Integrados os recursos de produção e o catálogo; removidos os módulos da interface anterior que deixaram de ser usados. O seletor de espectro mantém o algoritmo e o canvas originais, com o ciclo de vida da nova janela.
- Mantidas as fontes e as macros/cores reais dos marcadores. Corrigidos o acréscimo a listas vazias, a edição imutável, a reposição após rejeição e a limpeza de arrastos/tarefas de layout.
- Testes frontend abrem as 35 páginas e 1104 controlos reais, exportados pelo backend em ambiente isolado. Suite JavaScript/ESLint, catálogo, build data e nomes indefinidos aprovados.
- Inspeção visual bloqueada nesta sessão: o pipe nativo de Computer Use está indisponível e não existe browser IAB. Não se considera a apresentação validada em jogo.

- Etapa de integração registada em `1a5b021`. Validação: 444 testes core em Python 2.7/3 e build nativa aprovados.
- Os 73 rótulos novos foram movidos para os 18 catálogos YAML (243 chaves totais de painel), reutilizando traduções existentes quando adequadas; não ficam catálogos paralelos em JavaScript. Verificador de traduções aprovado sem prosa inglesa não autorizada.
- Restauradas teclas Home/End, corrigido encerramento de interações ao mudar de idioma e removidos os estilos do seletor HSV não utilizado. Confirmados todos os fluxos através do contrato existente; testes não efetuam instalações/reinícios reais.

- Verificação final: 444 testes core em Python 2.7/3, 27 testes de configuração em ambos, 36 testes installer/build em Python 3, JavaScript e ESLint aprovados. Catálogo, defaults e 264 recursos validados; zero nomes indefinidos.
- Acrescentados testes dos caminhos de perfis, confirmação de fecho, bloqueio de reinício em batalha e operações do updater; todos usam bridge simulado, sem ações reais no cliente.

- A build final detetou 51 entradas no changelog (limite 50). Consolidada a nota antiga de alias XVMSymbol com as notas atuais de fontes e cobertura de páginas, preservando a informação e o limite do manifesto.

- Implementação, revisão de lifecycle/traduções e documentação enviadas para `develop` nos commits `1a5b021` e `ddbf608`; [CI aprovado](https://github.com/dkruben/Driftkings_SettingsLab/actions/runs/40561989621). Este fecho inclui a consolidação do changelog e terá validação própria.
- Build final aprovada após a consolidação. Pacote: `build/debug/beta/0.1.3-beta.2/driftkings.wotmod`; SHA-256 `99be41aeade20d7e60595a66878c1aa078602da959c9d68db3bf9a0b0e2a5142`. Auditoria dos scripts/styles, seletor original, fontes e exclusão dos recursos antigos aprovada.
- A integração está concluída no projeto; aceitação visual em jogo pendente. A origem no Desktop e a instalação/configurações EU permanecem intactas.
