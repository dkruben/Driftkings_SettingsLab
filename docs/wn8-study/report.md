> Correção da auditoria: o resultado inicial 1 627 usou a tabela genérica XVM de 2024-09-12 e dados random. Com a tabela WG de 2026-10-22: all = 1 610 (23 191 batalhas); random = 1 629 (22 673 batalhas). As duas fórmulas reais do mod reproduzem estes valores com entradas iguais. Ver wn8-audit.json e audit_wn8.py. Os ficheiros iniciais permanecem como registo do ensaio original.

# Estudo exploratório WN8 — _DkRuben_ (EU)

> Contexto atualizado em 26/10/2026: estudo histórico com snapshots locais; valores e fórmulas experimentais abaixo não foram recalculados nem adotados como novas métricas do mod. O runtime atual calcula WN8 com estatísticas aleatórias e WNX pela sua fórmula própria. Os scripts, JSON e CSV citados são artefactos locais ignorados pelo Git, necessários para reproduzir o estudo. Ver o [estado atual](../STATUS.md) e as [notas de WNX](../../CONTRIBUTING.md#wnx-and-tomatogg).

Recolha UTC: 2026-10-24T04:11:29.253366+00:00

## Método

Dados públicos WG, apenas campo random por tanque. WN8 original com tabela XVM guardada nesta pasta. O total é calculado sobre rácios agregados, não pela média dos ratings por tanque.

Teste de sensibilidade: substituir dano por dano + alfa × assistência de rádio, mantendo o denominador de dano original e todos os outros termos. Alfa: 0, 0,33, 0,67 e 1. Apenas alfa=0 é WN8; os restantes NÃO são WN8 nem uma métrica validada.

Usa-se apenas assistência de rádio para evitar somar modalidades que podem sobrepor-se. Tracking e stun são apresentados nos dados, mas não adicionados ao score.

## Resultados

Tanques incluídos: 150; batalhas: 22673; excluídos sem referência: 0.

| Alfa | Pontuação experimental |
|---|---:|
| 0 | 1627.30 |
| 0.33 | 1747.96 |
| 0.67 | 1872.27 |
| 1 | 1992.93 |

### Veículos com pelo menos 100 batalhas — maior alteração com alfa=0,67

| Tanque | Batalhas | Dano/batalha | Rádio/batalha* | WN8 | Experimental 0,67 |
|---|---:|---:|---:|---:|---:|
| T37 | 349 | 800.57 | 396.32 | 2889.79 | 3776.75 |
| M41 Walker Bulldog | 105 | 1179.97 | 506.63 | 2851.78 | 3673.86 |
| AMX ELC bis | 150 | 436.73 | 298.29 | 1670.37 | 2454.86 |
| T71 DA | 303 | 695.09 | 492.78 | 1495.07 | 2219.2 |
| Pz.Kpfw. I Ausf. C | 204 | 191.25 | 179.5 | 1044.56 | 1767.24 |
| AMX 13 90 | 456 | 1187.52 | 555.51 | 2066.52 | 2707.87 |
| Bat.-Châtillon Bourrasque | 195 | 1145.82 | 694.4 | 1192.3 | 1759.67 |
| Type 62 | 177 | 683.8 | 323.35 | 1477.73 | 1999.02 |
| T-43 | 105 | 853.16 | 361.46 | 1487.88 | 1946.48 |
| Cromwell | 1065 | 1022.61 | 265.32 | 2821.92 | 3265.26 |
| T-44 | 284 | 1241.65 | 389.56 | 1993.26 | 2399.99 |
| VK 30.01 (D) | 106 | 853.43 | 261.27 | 1947.18 | 2347.58 |

## Limitações e interpretação

*Rádio/batalha é o total exposto pela API dividido pelas batalhas históricas. Não foi verificada a cobertura histórica deste contador: pode subestimar assistência antiga; zero não demonstra ausência de contribuição. Não reconstruir períodos recentes por diferença de médias sem verificar os denominadores.

Adicionar uma contribuição positiva sem recalibrar o valor esperado tende a aumentar o score por construção. Este teste mede sensibilidade e não prova que a variante é melhor. Para comparação justa são necessários valores esperados de assistência por veículo e período, uma população de jogadores e validação fora da amostra contra resultados futuros.

Não há dados de batalhas individuais, contexto tático ou distinção solo/pelotão nesta análise. Não foram estimados intervalos de confiança a partir de totais agregados.

Os resultados podem diferir de sites que usam outro modo, data ou tabela de referência. Capturar novos snapshots permite estudar intervalos futuros, desde que os contadores tenham cobertura consistente.

## Fontes

https://developers.wargaming.net/reference/all/wot/tanks/stats/
https://developers.wargaming.net/reference/eu/wot/account/info/
https://modxvm.com/en/wn8-expected-values/

O Application ID é lido da variável WG_APPLICATION_ID; não é guardado nos ficheiros. Este script não altera ficheiros fora desta pasta.
