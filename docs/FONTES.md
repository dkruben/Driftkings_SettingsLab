# Fontes e caracteres

## Resolução

As configurações mantêm o nome da fonte e o texto original: Unicode, `!`, `&#x115;` e `<font face="…">` não são convertidos em símbolos de outra fonte. Nomes de fontes com caracteres não ASCII são aceites também nos painéis Gameface e no carrossel.

Os campos Flash configuráveis usam `embedFonts = false`, permitindo a procura na biblioteca partilhada do cliente, no fornecedor de fontes configurado pelo cliente e nas fontes incorporadas. `$FieldFont` e `$TitleFont` continuam a ser aliases do jogo, respeitando a língua ativa. Campos que apenas reproduzem texto nativo, como o painel de diagnóstico, mantêm as propriedades nativas.

A biblioteca `flash_source/shared/as3/driftkings/utils/fontlibrary.as` incorpora os recursos abaixo no SWF de batalha e no dos marcadores. A integração dos marcadores copia as definições das fontes, os metadados e os símbolos de classe, atribuindo IDs livres e preservando os recursos nativos; copiar apenas o ABC perderia os glifos. Os símbolos de classe são vinculados depois dos ABC.

Gameface usa os mesmos TTF em `res/gui/fonts/driftkings`, com declarações `@font-face` partilhadas entre as páginas e o carregador de vistas injetadas. O alias `mono` usa a fonte real, em vez do substituto genérico `monospace`. Os aliases nativos usam a fonte carregada pela vista.

| Recurso | Nomes disponíveis | Autor indicado no TTF |
| --- | --- | --- |
| XVMSymbol.ttf | XVMSymbol, xvm | demon2597, 2012–2019 |
| VehicleType.ttf | VehicleType, vtype | XSerzHX, 2015–2018 |
| DynamicDefault.ttf | DynamicDefault, dynamic | XSerzHX, 2015–2018 |
| DynamicOutline.ttf | DynamicOutline, dynamic2 | XSerzHX, 2015–2018 |
| ZurichCondMono.ttf | mono, ZurichCondMono | demon2597, 2012–2018 |

## Origem e licença

Recursos copiados sem alterações de `xvm-master/src/xvm_fonts/assets`, referência local do projeto [XVM](https://modxvm.com/en/). A referência original distribui os recursos sob GPL-3.0; o texto dessa licença está disponível em [licence](../licence). Os nomes originais das fontes e os créditos são preservados; não é necessário instalar o mod de origem. Os TTF são os recursos fonte utilizados para produzir os glifos Flash.

SHA-256 dos recursos importados:

- `DynamicDefault.ttf`: `2f03c81e256ee51e1ee25707084aba3af8ce4eb891ccd4e0880e2c138b20da82`
- `DynamicOutline.ttf`: `3285c29f35987d6f561c11577691eded906a6c995bd5850c14aa4fdd0748b345`
- `VehicleType.ttf`: `7452d77dbe0f7ad2e9fae422395106434426c632865633ddd5dfecc3c29572f7`
- `XVMSymbol.ttf`: `e5bf2810132586a08fcdb887494c86d64d7f28f21e7d4ba5e7c6a66b5632e5f5`
- `ZurichCondMono.ttf`: `6158cb45aff173627540a798b66140c2084a042c353b8ed8497047fc9d340ec6`

## Cobertura e validação

Nenhuma fonte contém todos os caracteres possíveis. Uma fonte adicional só pode ser desenhada se estiver disponível ao renderizador, e um símbolo depende do mapa de glifos da fonte escolhida. Não se substitui silenciosamente uma fonte de ícones por texto normal. As fontes do Windows dependem do fornecedor disponibilizado pelo cliente; não se assume que todas estejam acessíveis. Para distribuir outra fonte com o mod, é necessário incluir o recurso e a respetiva licença, acrescentar a declaração Flash e o `@font-face`, e reconstruir os SWF.

A ordem de procura segue a [documentação Scaleform](https://help.autodesk.com/cloudhelp/ENU/Scaleform-Help/scaleform_help/font/part_3.html). Esta alteração não modifica perfis pessoais nem os recursos/fontes de outros mods.

Validação local: 444 testes core em Python 2.7 e 3; 36 testes de instalação/build, incluindo remapeamento de IDs e ordenação de tags; testes Gameface, ESLint e build nativa. A inspeção das tabelas DefineFont3 confirma dez nomes incorporados em cada SWF, incluindo `!` e U+0115 em `XVMSymbol`/`xvm`. A confirmação visual dos marcadores, minimapa, painéis e carrossel em batalha continua pendente.

O log EU de 27 outubro, 16:08, continha dois avisos Gameface para `monospace` (pesos 400/700). A substituição desse nome genérico pela fonte `mono` carregada é incluída nesta correção.
