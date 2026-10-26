# Segundo teste: assistência normalizada por veículo

> Contexto atualizado em 26/10/2026: estudo histórico com snapshots locais; valores e fórmulas experimentais abaixo não foram recalculados nem adotados como novas métricas do mod. O runtime atual calcula WN8 com estatísticas aleatórias e WNX pela sua fórmula própria. Os scripts, JSON e CSV citados são artefactos locais ignorados pelo Git, necessários para reproduzir o estudo. Ver o [estado atual](../STATUS.md) e as [notas de WNX](../../CONTRIBUTING.md#wnx-and-tomatogg).

## Resultado e alcance

Incluídos 150 tanques e 22673 batalhas aleatórias. Referências ausentes: 0 tanques.

Este é um teste exploratório com referência externa publicada pelo Tomato.gg. A WG fornece as estatísticas da conta; não fornece esta tabela de desempenho esperado. Não foi criada uma referência populacional própria a partir da WG.

## Comparação controlada

Rácio combinado = (dano + alfa × assistência) / (dano esperado + alfa × assistência esperada). Numerador e denominador são agregados com o mesmo número de batalhas por tanque. Assistência neste ensaio = radio_assisted_damage + track_assisted_damage do campo random; stun excluído. Esta definição operacional e a cobertura histórica podem diferir da usada pelo Tomato.gg.

Usamos os quatro valores esperados do Tomato.gg e a equação de pontuação publicada na secção Implementation da página WNX. Com alfa=0 removemos assistência dos dois lados; com alfa=0,67 incluímo-la nos dois lados. Não confundir o controlo sem assistência com WN8. Não apresentamos os resultados como WNX oficial da conta.

| Peso da assistência | Rácio combinado | Pontuação experimental |
|---|---:|---:|
| 0 | 1.0809 | 1523 |
| 0.33 | 1.0623 | 1482 |
| 0.67 | 1.0466 | 1448 |
| 1 | 1.0339 | 1420 |

## Maiores subidas (mínimo 100 batalhas)

| Tanque | Batalhas | Assist./batalha histórica | Assist. esperada | Controlo sem assist. | Com assist. 0,67 | Diferença |
|---|---:|---:|---:|---:|---:|---:|
| Pz.Kpfw. I Ausf. C | 204 | 187.95 | 117.04 | 266 | 530 | +264 |
| Bat.-Châtillon Bourrasque | 195 | 732.96 | 477.31 | 1032 | 1248 | +216 |
| IS-7 | 295 | 611.32 | 452.16 | 879 | 1039 | +160 |
| E 75 | 194 | 575.69 | 366.53 | 1630 | 1771 | +141 |
| Pz.Kpfw. S35 739 (f) | 108 | 108.42 | 77.95 | 532 | 641 | +109 |
| T-43 | 105 | 394.67 | 358.59 | 1156 | 1240 | +84 |

## Maiores descidas (mínimo 100 batalhas)

| Tanque | Batalhas | Assist./batalha histórica | Assist. esperada | Controlo sem assist. | Com assist. 0,67 | Diferença |
|---|---:|---:|---:|---:|---:|---:|
| M41 Walker Bulldog | 105 | 539.87 | 980.97 | 3793 | 1796 | -1997 |
| AMX 13 90 | 456 | 625.12 | 1067.73 | 2274 | 1362 | -912 |
| Lorraine 155 mle. 51 | 237 | 69.27 | 542.76 | 2391 | 1490 | -901 |
| Lorraine 155 mle. 50 | 536 | 56.27 | 479.37 | 2227 | 1354 | -873 |
| T37 | 349 | 415.8 | 540.49 | 2647 | 1826 | -821 |
| Type 62 | 177 | 348.02 | 668.63 | 1241 | 925 | -316 |

## Verificação dos dados e limitações

Ao contrário do primeiro ensaio, acrescentar assistência não faz subir automaticamente o rácio: depende de o desempenho relativo em assistência superar ou ficar abaixo do desempenho relativo em dano.

Existem 26 veículos incluídos com contagens all e random diferentes. Não misturámos médias all com totais random.

Mesmo onde as batalhas all e random coincidem, há casos em que avg_damage_assisted_radio não equivale a radio_assisted_damage / battles. Isto impede assumir cobertura e denominadores históricos iguais. Ausência de assistência registada não prova ausência de assistência real.

A referência é contemporânea; os resultados da conta incluem épocas antigas, mudanças de tier e balanceamento. As comparações históricas por veículo podem por isso ser injustas, em especial em tanques alterados. Não se deve interpretar descidas como prova de mau spotting.

A definição exata de assistência na tabela externa não foi confirmada contra os contadores WG. Em particular, a referência de SPG pode incluir stun, que este ensaio exclui. Portanto nem o agregado nem as comparações de SPG são uma comparação validada com definições equivalentes. É necessário esclarecer esta semântica antes de adotar a métrica.

A pontuação combinada usa a forma publicada na implementação WNX; não foi ajustada aos teus resultados. Não é uma validação independente de WNX nem demonstra que um peso de 0,67 seja ótimo. O peso é uma hipótese publicada.

Não calcular WN8 + assistência usando dano esperado XVM e assistência esperada Tomato como se fossem da mesma população. Este segundo ensaio usa a referência Tomato para todos os seus rácios. O WN8 original permanece apenas como contexto no CSV.

## Próximo teste empiricamente válido

Guardar snapshots WG de vários jogadores agora e depois de novas batalhas; calcular diferenças dos contadores acumulados no mesmo modo. Confirmar a consistência da assistência nesses intervalos. Construir referências por tanque sem incluir o jogador avaliado e validar contra vitórias num período posterior separado. Comparar modelos com e sem assistência, sem usar vitórias do período de avaliação como entrada. Uma só conta e totais históricos não permitem demonstrar superioridade estatística.

## Fontes e reprodução

- https://tomato.gg/wnx — referência e implementação pública.
- https://developers.wargaming.net/reference/all/wot/tanks/stats/ — contadores WG.

Executar python docs/wn8-study/normalized.py. A análise usa os snapshots locais, sem credenciais nem novas chamadas à API. O snapshot da referência e o código público consultado estão nesta pasta.
