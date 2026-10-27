# Fontes e caracteres

## Objetivo
Preservar fontes, Unicode e entidades HTML em todos os textos configuráveis. Incluir as fontes de símbolos usadas pelos perfis, sem depender do mod de origem.

## Trabalho
- [x] Diagnóstico: a adaptação Python/JavaScript substituía fontes e glifos; os campos Flash forçavam fontes incorporadas.
- [x] Incorporar as fontes reais no Flash e disponibilizar os mesmos TTF ao Gameface, preservando nomes e créditos.
- [x] Preservar o texto configurado e permitir procura nas fontes do cliente.
- [x] Testar a preservação de Unicode/HTML e a integração dos recursos na build.
- [x] Atualizar o registo de alterações, fazer commit/push e acompanhar CI.

## Limites
Uma fonte só desenha os caracteres que contém. As fontes adicionais precisam de estar disponíveis ao renderizador; não prometemos cobertura universal nem substituímos símbolos silenciosamente. A validação visual no cliente continua necessária.

## Registo

- Fontes originais incorporadas nos dois SWF, incluindo tags/metadados e bindings com IDs remapeados. TTF e licença incluídos no pacote; cinco recursos, dez nomes.
- Python e JavaScript deixam de substituir fontes e glifos. Campos Flash configuráveis permitem procura no cliente; Gameface aceita nomes Unicode e carrega os mesmos recursos.
- 444 testes core em Python 2.7/3 e 36 testes installer/build aprovados; testes Gameface e ESLint aprovados. Build nativa e auditoria dos glifos `!`/U+0115 aprovadas; build final após a ordenação dos bindings também aprovada.
- Nenhuma configuração ou instalação EU alterada. Aceitação visual pendente.

- Implementação e documentação no commit `4d1b961`, enviado para `develop`; [validação GitHub aprovada](https://github.com/dkruben/Driftkings_SettingsLab/actions/runs/40541534633). Este encerramento do plano segue num commit de documentação, com validação própria.
- Pacote do commit: `build/debug/beta/0.1.3-beta.2/driftkings.wotmod`; SHA-256 `f9fade6cb62c0c76197703a1aec607cb64dde7d64c97ce143c870476197443cf`. Auditoria final: cinco TTF e licença presentes, dez fontes por SWF, IDs únicos, símbolos de classe depois do ABC e glifos originais confirmados.
