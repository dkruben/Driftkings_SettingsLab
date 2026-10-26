# Créditos de contribuição — primeiro protótipo

> Contexto atualizado em 26/10/2026: estudo histórico com snapshots locais; valores e fórmulas experimentais abaixo não foram recalculados nem adotados como novas métricas do mod. O runtime atual calcula WN8 com estatísticas aleatórias e WNX pela sua fórmula própria. Os scripts, JSON e CSV citados são artefactos locais ignorados pelo Git, necessários para reproduzir o estudo. Ver o [estado atual](../STATUS.md) e as [notas de WNX](../../CONTRIBUTING.md#wnx-and-tomatogg).

## Definição operacional

C = s × dano direto + (1 − s) × (assistência rádio + tracking) + 200 × eliminações + 10 × pontos de defesa. O resultado apresentado é C / batalhas. Só usa contadores WG guardados; não usa WN8, WNX ou referências externas.

200 créditos por eliminação e 10 por ponto de defesa são hipóteses arbitrárias de teste, não equivalências demonstradas em HP ou probabilidade de vitória. A eliminação já envolve dano: o seu termo é um bónus adicional proposto para retirar uma arma. Defesa é um proxy disponível, não mede quantas derrotas foram evitadas. Captura não foi incluída porque não sabemos a sua relevância para o resultado.

A repartição s é uniforme e aproximada. Não sabemos quanto dano direto foi feito sem assistência e não conseguimos repartir cada evento. Portanto não há garantia de conservação do crédito: dano próprio sem assistência também é descontado e rádio/tracking podem ter semântica de sobreposição. Isto não implementa uma repartição exata de 1 000 HP entre participantes. Stun excluído para manter o ensaio simples; prejudica a comparabilidade de SPG.

## Conta completa

Batalhas aleatórias: 22673.

| Crédito disparo / assistência | Dano/batalha | Assistência/batalha | Kills/batalha | Defesa/batalha | Total/batalha |
|---|---:|---:|---:|---:|---:|
| 75-25 | 737.32 | 67.86 | 220.85 | 9.71 | 1035.74 |
| 50-50 | 491.55 | 135.71 | 220.85 | 9.71 | 857.82 |
| 25-75 | 245.77 | 203.57 | 220.85 | 9.71 | 679.91 |

## Tanques com mais batalhas

| Tanque | Tier | Batalhas | 75/25 | 50/50 | 25/75 |
|---|---:|---:|---:|---:|---:|
| KV-85 | 6 | 1265 | 879.55 | 728.2 | 576.86 |
| KV-1 | 5 | 1251 | 811.11 | 678.49 | 545.87 |
| Rhm.-Borsig Waffenträger | 8 | 1149 | 1624.12 | 1270.1 | 916.08 |
| Cromwell | 6 | 1065 | 1188.09 | 1007.49 | 826.88 |
| IS-3 | 8 | 984 | 1242.98 | 1010.96 | 778.95 |
| SU-100Y | 6 | 878 | 1040.58 | 843.67 | 646.76 |
| T3 HMC | 2 | 875 | 585.72 | 526.05 | 466.37 |
| Waffenträger auf Pz. IV | 9 | 856 | 1708.5 | 1338.97 | 969.44 |
| M18 Hellcat | 6 | 790 | 1019.5 | 861.2 | 702.89 |
| Lorraine 155 mle. 50 | 7 | 536 | 1031.64 | 775.4 | 519.16 |
| IS | 7 | 533 | 1059.93 | 874.47 | 689.0 |
| T1 Heavy | 5 | 476 | 360.51 | 297.63 | 234.75 |

## Sensibilidade aos bónus (repartição 50/50)

| Créditos por kill | Créditos por ponto de defesa | Total/batalha |
|---|---:|---:|
| 0 | 0 | 627.26 |
| 0 | 10 | 636.97 |
| 100 | 0 | 737.69 |
| 100 | 10 | 747.40 |
| 200 | 0 | 848.11 |
| 200 | 10 | 857.82 |
| 400 | 0 | 1068.97 |
| 400 | 10 | 1078.68 |

## Como interpretar

Unidade: créditos experimentais por batalha, sem cores, percentis ou equivalência a WN8. Não comparar diretamente tanques de tiers ou funções diferentes: o protótipo ainda não normaliza oportunidades de dano nem dificuldade. Não é um ranking de habilidade.

Os contadores históricos de assistência têm cobertura incerta. O ensaio não identifica momento do dano, prioridade de alvo, pelotões ou importância da defesa. A soma rádio+tracking é uma definição operacional que precisa de validação antes de ser tratada como contribuição sem duplicações.

O próximo passo é testar se os pesos mantêm resultados coerentes entre tanques comparáveis e validá-los em períodos futuros separados. Não escolher pesos apenas para elevar a pontuação da conta.

Reprodução: python docs/wn8-study/contribution.py. Dados: tanks.json e vehicles.json obtidos da API pública WG; nenhuma chamada de rede necessária.
