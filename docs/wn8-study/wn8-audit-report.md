# Auditoria WN8 — _DkRuben_

> Contexto atualizado em 26/10/2026: estudo histórico com snapshots locais; valores e fórmulas experimentais abaixo não foram recalculados nem adotados como novas métricas do mod. O runtime atual calcula WN8 com estatísticas aleatórias e WNX pela sua fórmula própria. Os scripts, JSON e CSV citados são artefactos locais ignorados pelo Git, necessários para reproduzir o estudo. Ver o [estado atual](../STATUS.md) e as [notas de WNX](../../CONTRIBUTING.md#wnx-and-tomatogg).

O valor 1 610 foi reproduzido usando os dados WG guardados e a tabela XVM WG versão 2026-10-22.

| Conjunto de dados | Batalhas | Fórmula painel | Fórmula perfil |
|---|---:|---:|---:|
| all | 23191 | 1610 | 1610 |
| random | 22673 | 1629 | 1629 |

As fórmulas reais do mod concordam para entradas iguais. Não foi demonstrado um erro na equação. Na altura da auditoria, o painel pedia statistics.all e account/tanks; o perfil passava dossier.getRandomStats(). Essa diferença motivou a correção posterior para estatísticas aleatórias no painel. Os resultados de snapshots abaixo permanecem como evidência histórica e não comprovam o estado da cache do cliente atual.

O estudo inicial usou o endpoint genérico https://static.modxvm.com/wn8-data-exp/json/wn8exp.json, cujo header identifica 2024-09-12. O mod usa o endpoint /json/wg/wn8exp.json, versão consultada 2026-10-22. Corrigiu-se o URL do script de recolha para futuras execuções. Snapshots iniciais preservados. Os protótipos de contribuição não são WN8.

Verificação: audit_wn8.py executa o método wn8 extraído do AST real de player_ratings.py e importa profile_ratings.py, usando os mesmos totais em ambos. Os quatro testes de test_native_profile.py passaram. A verificação é offline com snapshots; não comprova o cache ou os dados do cliente em execução.
