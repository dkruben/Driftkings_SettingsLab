# Fontes e caracteres

## Resolução

As configurações mantêm o nome da fonte e o texto original: Unicode, `!`, `&#x115;` e `<font face="…">` não são convertidos em símbolos de outra fonte. Nomes de fontes com caracteres não ASCII são aceites também nos painéis Gameface e no carrossel.

Os campos Flash configuráveis usam `embedFonts = false`, permitindo a procura na biblioteca partilhada do cliente, no fornecedor de fontes configurado pelo cliente e nas fontes incorporadas. `$FieldFont` e `$TitleFont` continuam a ser aliases do jogo, respeitando a língua ativa. Campos que apenas reproduzem texto nativo, como o painel de diagnóstico, mantêm as propriedades nativas.

A biblioteca `flash_source/shared/as3/driftkings/utils/fontlibrary.as` incorpora os recursos abaixo no SWF de batalha e no dos marcadores. A integração dos marcadores copia as definições das fontes, os metadados e os símbolos de classe, atribuindo IDs livres e preservando os recursos nativos; copiar apenas o ABC perderia os glifos. Os símbolos de classe são vinculados depois dos ABC.

Gameface usa os mesmos TTF em `res/gui/fonts/driftkings`, com declarações `@font-face` partilhadas entre as páginas e o carregador de vistas injetadas. O alias `mono` usa a fonte real, em vez do substituto genérico `monospace`. Os aliases nativos usam a fonte carregada pela vista.

O pacote `driftkings.fonts`, em `res/mods/openwg_packages`, regista agora os cinco TTF e os sete aliases no fornecedor nativo `openwg_fonts`. O carregador OpenWG executa este pacote depois da dependência `net.openwg.fonts`; não é a ordem alfabética dos ficheiros `gui/mods` que determina a inicialização. Os caminhos `gui/fonts/driftkings/*.ttf` pertencem ao VFS do cliente; o fornecedor extrai os recursos arquivados para a sua cache quando necessário. A inicialização repetida do pacote não repete os registos. A finalização não remove aliases globais que outros mods possam usar.

A distribuição inclui `net.openwg.common_2.8.5.0000.wotmod`, sem alterações, proveniente do checkout local de referência. O SHA-256 fica fixado em `build_data/build_config.json`, tal como nas restantes dependências. Esta biblioteca inclui componentes nativos além do fornecedor de fontes; a compilação e os testes locais não comprovam a sua execução no cliente. Confirmar no `game.log` os registos `OpenWG/Fonts` e os glifos numa batalha após instalar a nova build. Os SWF mantêm os recursos incorporados, e Gameface mantém os seus `@font-face`.

Os campos dos marcadores usam também antialiasing avançado, caixas de tamanho fixo e `TextFieldEx.setNoTranslate`, seguindo o comportamento de referência sem traduzir nomes, macros resolvidos ou símbolos.

| Recurso | Nomes disponíveis | Autor indicado no TTF |
| --- | --- | --- |
| DriftkingsFont.ttf | dkm, DriftkingsFont, xvm, XVMSymbol | DriftkingsMods, 2020–2026 (metadados fornecidos); glifos originais de demon2597 |
| VehicleType.ttf | VehicleType, vtype | XSerzHX, 2015–2018 |
| DynamicDefault.ttf | DynamicDefault, dynamic | XSerzHX, 2015–2018 |
| DynamicOutline.ttf | DynamicOutline, dynamic2 | XSerzHX, 2015–2018 |
| ZurichCondMono.ttf | mono, ZurichCondMono | demon2597, 2012–2018 |

## Origem e licença

As quatro fontes auxiliares foram copiadas sem alterações de `xvm-master/src/xvm_fonts/assets`, referência local do projeto [XVM](https://modxvm.com/en/). A referência original distribui os recursos sob GPL-3.0; o texto dessa licença está disponível em [licence](../licence). Os aliases originais e os créditos são preservados; não é necessário instalar o mod de origem. Os TTF são os recursos fonte utilizados para produzir os glifos Flash.

`DriftkingsFont.ttf` foi fornecida pelo utilizador em `F:/SantaAureliaRP/to_install`, sem alterações ao ficheiro. Substitui o recurso `XVMSymbol.ttf`: a inspeção confirmou os mesmos 114 caracteres e a tabela de contornos `glyf` idêntica à fonte anterior. Preservam-se por isso os créditos dos glifos originais. Os defaults usam `dkm`; os aliases `xvm` e `XVMSymbol` apontam para esse recurso nos três renderizadores.

SHA-256 dos recursos importados:

- `DynamicDefault.ttf`: `2f03c81e256ee51e1ee25707084aba3af8ce4eb891ccd4e0880e2c138b20da82`
- `DynamicOutline.ttf`: `3285c29f35987d6f561c11577691eded906a6c995bd5850c14aa4fdd0748b345`
- `VehicleType.ttf`: `7452d77dbe0f7ad2e9fae422395106434426c632865633ddd5dfecc3c29572f7`
- `DriftkingsFont.ttf`: `368e8ecd244dd6f9dbd805883d9c1bc6a108b39ad1bcc05c39b775e9f3c550da`
- `ZurichCondMono.ttf`: `6158cb45aff173627540a798b66140c2084a042c353b8ed8497047fc9d340ec6`

## Cobertura e validação

Nenhuma fonte contém todos os caracteres possíveis. Uma fonte adicional só pode ser desenhada se estiver disponível ao renderizador, e um símbolo depende do mapa de glifos da fonte escolhida. Não se substitui silenciosamente uma fonte de ícones por texto normal. As fontes do Windows dependem do fornecedor disponibilizado pelo cliente; não se assume que todas estejam acessíveis. Para distribuir outra fonte com o mod, é necessário incluir o recurso e a respetiva licença, acrescentar a declaração Flash e o `@font-face`, e reconstruir os SWF.

A ordem de procura segue a [documentação Scaleform](https://help.autodesk.com/cloudhelp/ENU/Scaleform-Help/scaleform_help/font/part_3.html). Esta alteração não modifica perfis pessoais nem os recursos/fontes de outros mods.

Validação da substituição: build nativa concluída; testes do registo de fontes, schema dos marcadores em Python 2.7 e Gameface passaram. As tabelas DefineFont3 dos dois SWF contêm doze nomes incorporados; `dkm`, `DriftkingsFont`, `xvm` e `XVMSymbol` incluem 114 glifos e U+0115. A confirmação visual no cliente continua pendente.

O log EU de 27 outubro, 16:08, continha dois avisos Gameface para `monospace` (pesos 400/700). A substituição desse nome genérico pela fonte `mono` carregada é incluída nesta correção.
