# Carrossel Driftkings

Os três JSON foram adaptados dos ficheiros `carousel.json_`,
`carouselNormal.json_` e `carouselSmall.json_` fornecidos pelo utilizador.
São JSON estrito: sem comentários, vírgulas finais ou referências XC.
Os originais fornecidos na instalação do jogo não são alterados pelo build.

## Instalação

Com o jogo fechado, extrair `Driftkings-Carousel.zip` na pasta do jogo.
O arquivo contém o pacote unificado, os três JSON do perfil `default` e
as imagens em **mods/Driftkings/Carroucel/**, fora da pasta da versão.
Guardar os JSON atuais antes de substituir; a configuração geral usa a
escala `colorRating: 0`, tal como no ficheiro fornecido. O seletor de escalas
continua disponível. Outros perfis de configuração não são substituídos.

## Apresentação

- Duas filas, perfil normal de 210 × 140; compacto de 160 × 70; intervalo 10.
- `rows` permite 1, 2, 3 ou 4 filas; `0` mantém a seleção automática.
  O padrão continua em duas filas. O painel de configurações permite escolher
  até quatro, ou pode definir-se `"rows": 4` em `carousel.json`.
- Batalhas, vitórias, precisão, dano médio/esperado WN8, intervalo de níveis,
  mestria e marcas no canhão, nas posições fornecidas.
- Fundo selecionado por classe: leves verde, médios azul, pesados castanho,
  caça-tanques vermelho e artilharia roxo, como na configuração DriftKings antiga.
- Perfil compacto com mestria, nome e taxa de vitórias.

## Referências e imagens

`"shadow": "$ref:textFieldShadow"` reutiliza a sombra definida no perfil.
Para sobrescrever propriedades:

```json
"shadow": {
  "$ref": "textFieldShadow",
  "color": "{{v.premium?0xFC3700|0xC8C8B5}}",
  "alpha": "{{v.premium?85|35}}"
}
```

Imagens aceites em `src` e em `<img src='…' width='…' height='…'>`:

- `mods/Driftkings/Carroucel/battles.png` e restantes PNG externos.
- `img://gui/...` ou `coui://gui/...` para recursos do cliente.

O Python lê os PNG externos com cache e o Gameface recebe um mapa comum
de imagens, sem repetir cada imagem nos dados de cada veículo. `showIcons`
também controla as imagens embutidas no texto. Não há pedidos de rede.

## Adaptações de compatibilidade

- Vírgulas/chavetas e referências de sombra corrigidas.
- Imagens de estatísticas têm opacidade 100 quando há dados; foi removido
  `alpha='{{v.c_battles:300}}'`, que usava uma cor como opacidade.
- A marca no canhão usa uma imagem: `_1_mark`, `_2_marks` ou `_3_marks`.
- O símbolo de precisão usa `◎`, sem depender da fonte `XVMSymbol`.
- `v.wn8expd` vem dos dados WN8 já existentes no pacote; `v.wn8effd` é
  dano médio/dano esperado. As cores continuam a usar a escala escolhida.
- Os intervalos de níveis são estimativas visuais segundo a tabela WG do
  XVM local (`vehinfo_tiers.py`), incluindo veículos preferenciais; não são
  regras consultadas ao servidor. Foi retirada a alternativa do antigo Ranked.
- As opções nativas sem equivalente no Gameface atual (por exemplo os
  antigos `coreBorder` e `crystalsBorder`) ficam preservadas no JSON,
  mas não inventam elementos que o cliente já não tem.

Validar no jogo os dois tamanhos, veículo selecionado, veículos sem batalhas,
mestria/marcas, mudança de escala e a opção de mostrar imagens.

`carousel_tiers.py` adapta código dos XVM Contributors (2013–2026), sob
GPL-3.0-or-later. Ver `XVM-CONFIG-LICENSE.txt`; fonte incluída no arquivo.
