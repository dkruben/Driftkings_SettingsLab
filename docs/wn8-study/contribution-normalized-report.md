# Contribuição normalizada por veículo — protótipo

> Contexto atualizado em 26/10/2026: estudo histórico com snapshots locais; valores e fórmulas experimentais abaixo não foram recalculados nem adotados como novas métricas do mod. O runtime atual calcula WN8 com estatísticas aleatórias e WNX pela sua fórmula própria. Os scripts, JSON e CSV citados são artefactos locais ignorados pelo Git, necessários para reproduzir o estudo. Ver o [estado atual](../STATUS.md) e as [notas de WNX](../CONTRIBUTING.md#wnx-and-tomatogg).

## Fórmula e escala

Créditos base = 0,5 × dano + 0,5 × (rádio + tracking) + 200 × kills. Índice = 1 000 × soma dos créditos reais / soma dos créditos esperados. Os esperados de cada tanque são multiplicados pelas batalhas desse tanque. Não se calcula a média simples das notas individuais.

1 000 significa igual à contribuição da referência guardada; 1 200 significa 20% acima dessa referência. Não significa percentil, habilidade 20% maior ou mais 20% de probabilidade de vitória. Não é WN8 nem WNX.

Esta normalização usa a tabela Tomato.gg para dano, assistência e kills por veículo, portanto também incorpora o tier através do veículo. Usar a tabela não significa adotar a fórmula WNX. A validade da referência entre veículos, tiers e épocas continua por demonstrar.

## Conta completa

| Variante | Batalhas | Índice |
|---|---:|---:|
| Base, todos os tanques | 22673 | 1106.42 |
| Base, excluindo SPG | 21258 | 1107.56 |
| Com defesa, referência híbrida | 22673 | 1104.57 |

## Veículos mais jogados

| Tanque | Tier | Batalhas | Créditos brutos/batalha, com defesa | Base normalizada | Com defesa híbrida |
|---|---:|---:|---:|---:|---:|
| KV-85 | 6 | 1265 | 728.20 | 1067.68 | 1064.34 |
| KV-1 | 5 | 1251 | 678.49 | 1087.02 | 1084.09 |
| Rhm.-Borsig Waffenträger | 8 | 1149 | 1270.10 | 1412.52 | 1412.85 |
| Cromwell | 6 | 1065 | 1007.49 | 1469.18 | 1471.77 |
| IS-3 | 8 | 984 | 1010.96 | 1099.74 | 1097.49 |
| SU-100Y | 6 | 878 | 843.67 | 1261.10 | 1263.05 |
| T3 HMC | 2 | 875 | 526.05 | 1239.23 | 1228.07 |
| Waffenträger auf Pz. IV | 9 | 856 | 1338.97 | 1252.70 | 1251.68 |
| M18 Hellcat | 6 | 790 | 861.20 | 1286.18 | 1295.02 |
| Lorraine 155 mle. 50 | 7 | 536 | 775.40 | 1009.67 | 1009.22 |
| IS | 7 | 533 | 874.47 | 1042.13 | 1040.89 |
| T1 Heavy | 5 | 476 | 297.63 | 476.59 | 474.31 |
| AMX 13 90 | 9 | 456 | 1126.85 | 1065.24 | 1063.15 |
| Tiger II | 8 | 417 | 1120.93 | 1223.29 | 1212.74 |
| T-10 | 9 | 400 | 1091.08 | 1008.49 | 1010.15 |

## Por classe

| Classe | Batalhas | Base normalizada |
|---|---:|---:|
| AT-SPG | 5647 | 1272.47 |
| SPG | 1085 | 974.47 |
| heavyTank | 8029 | 1064.66 |
| lightTank | 3071 | 896.06 |
| mediumTank | 4511 | 1117.49 |
| unknown | 330 | 1305.97 |

## Por tier

| Tier | Batalhas | Base normalizada |
|---|---:|---:|
| 0 | 330 | 1305.97 |
| 1 | 457 | 509.54 |
| 2 | 1445 | 895.18 |
| 3 | 880 | 719.39 |
| 4 | 613 | 737.77 |
| 5 | 2369 | 918.30 |
| 6 | 5925 | 1198.65 |
| 7 | 3273 | 1053.98 |
| 8 | 4162 | 1188.58 |
| 9 | 2331 | 1172.47 |
| 10 | 888 | 1131.23 |

## Defesa: variante separada

A fórmula completa original acrescenta 10 × pontos de defesa. A tabela Tomato guardada não fornece defesa esperada. Para não inventar esse valor, o índice principal exclui defesa em ambos os lados. A variante completa usa expDef XVM. Esta é uma referência híbrida, de populações e métodos distintos; não deve ser tratada como índice calibrado.

## Limitações

- Os pesos 0,5, 200 e 10 continuam arbitrários e não foram ajustados para elevar a tua nota.
- O peso fixo de 200 por kill varia em importância relativa conforme o tier; a divisão pelo esperado não demonstra equivalência entre tiers.
- A semântica de assistência Tomato não foi confirmada contra rádio + tracking WG. Stun está excluído; SPG é também mostrado separadamente por esse motivo.
- Assistência histórica tem cobertura incerta; referências atuais podem ser inadequadas para resultados anteriores a buffs, nerfs ou mudanças de tier.
- A repartição de crédito não é conservativa por evento: falta saber quanto do dano direto foi assistido.
- Pequenas amostras, configuração stock/top, solo/pelotão e contexto tático não foram controlados.
- As tabelas por classe e tier descrevem esta conta; não demonstram ausência de enviesamento da fórmula numa população.

Veículos ausentes da enciclopédia guardada aparecem como unknown e tier 0 (tier desconhecido, não um tier real). Permanecem no agregado geral se têm referências, mas são excluídos do agregado sem SPG por classe incerta.

## Verificação e reprodução

Executar python docs/wn8-study/contribution_normalized.py. Só lê snapshots locais. Verificado: desempenho exatamente igual à referência dá 1 000; duplicar créditos reais com referência fixa dá 2 000; agregar rácios usa os denominadores como pesos.

Fontes guardadas: tanks.json e vehicles.json (WG), assistance-reference.json (https://tomato.gg/wnx), expected-values.json (https://modxvm.com/en/wn8-expected-values/).
