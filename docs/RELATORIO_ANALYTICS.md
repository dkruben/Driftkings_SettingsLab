# Eventos falsos nas estatísticas anónimas

Proposta de 2026-11-02, só de leitura: o código, a chave e a propriedade GA4 não foram alterados. Os caminhos partem de `mod/res/scripts/client/driftkings/`.

## Situação

`core/analytics.py` envia eventos pelo Measurement Protocol do GA4 com o `MEASUREMENT_ID` e o `API_SECRET` escritos no código. O próprio comentário reconhece que o segredo é público por natureza: qualquer pessoa que abra o pacote consegue enviar eventos para a propriedade. O protocolo só aceita escritas, por isso o risco não é fuga de dados; é **poluição**: números de instalações, versões ou erros inventados.

O que o mod envia, com a opção ligada e fora dos replays:

| Evento | Parâmetros |
| --- | --- |
| `mod_loaded` | `mod_version`, `session_id`, `engagement_time_msec`, `realm`, `game_version` |
| `heartbeat` (de 60 em 60 s) | os mesmos, com `engagement_time_msec` = 60000 |
| `exception` (até 20 distintas por sessão) | os mesmos, mais `description`, `fatal`, `error_channel`, `error_type`, `error_file`, `error_line`, `error_function` |

O `client_id` é sempre `N.N`, derivado de um id aleatório de 32 hexadecimais; `session_id` é fixo durante a sessão.

Nenhuma validação no mod impede eventos falsos: quem os forja não usa o mod. As medidas úteis estão no **GA4** (o que se mostra) e na **análise** (o que se conta). A única que trava os eventos à entrada é um **intermediário com o segredo do lado do servidor**.

## 1. Filtros no GA4 (sem custo, imediato)

O GA4 não deixa rejeitar eventos do Measurement Protocol por conteúdo: os filtros de dados só tratam tráfego interno e de programador. O que se pode fazer é registar dimensões e mostrar só o que é plausível.

1. **Dimensões personalizadas** (âmbito de evento) para `mod_version`, `realm`, `game_version`, `error_type`, `error_file` e `error_line`. Sem elas, os filtros seguintes não existem nos relatórios.
2. **Segmento ou filtro de comparação "Tráfego válido"** aplicado por defeito às explorações:
   - `event_name` em `mod_loaded`, `heartbeat`, `exception`;
   - `mod_version` numa lista de versões publicadas (0.1.4, 0.1.5-beta.1 … 0.1.5-beta.3), atualizada a cada release;
   - `realm` em `EU`, `NA`, `ASIA`;
   - `game_version` a começar pela versão-alvo (`2.4.1.1`).
3. **Contar instalações por `mod_loaded`** e não por utilizadores ativos: um `client_id` que só envia `heartbeat` sem `mod_loaded` não veio do mod.
4. **Alertas personalizados (Insights)** para picos de `mod_loaded` ou de `exception` por hora, ou para uma `mod_version` nova que não esteja na lista.
5. **Propriedade de testes separada** para builds debug, para os números da propriedade real virem só de releases.

## 2. Validação na análise (exportação BigQuery)

A ligação GA4 → BigQuery é gratuita na camada sandbox e dá os eventos em bruto. Uma vista SQL "eventos válidos" exclui o que o mod nunca produziria:

- **Esquema:** só os três nomes de evento; só os parâmetros listados acima; `fatal = 0`; `client_id` a cumprir `^[0-9]+\.[0-9]+$`; `session_id` presente.
- **Valores:** `mod_version` na lista de releases (pode vir dos tags do GitHub); `realm` e `game_version` como no ponto 1; `error_file` igual ao nome de um módulo do pacote, com `error_line` dentro do comprimento desse ficheiro. Ambas as listas saem da build.
- **Comportamento:** cada sessão começa com um `mod_loaded`; os `heartbeat` chegam a cerca de 60 s de intervalo; no máximo 20 `exception` distintas por sessão. Um `client_id` com muitas sessões em paralelo ou ritmo impossível é descartado.
- **Consistência:** o mesmo `client_id` não muda de `realm` nem anda para trás na `mod_version`.

Estas regras repetem os limites que o código já impõe (`MAX_ERRORS`, `HEARTBEAT`, `BATCH`). Devem ficar ao lado do código, com um teste, para não divergirem quando ele mudar.

## 3. Validação no envio (intermediário próprio)

É a única medida que trava eventos falsos antes do GA4, mas exige infraestrutura.

- O mod deixa de enviar para `google-analytics.com` e passa a enviar para um endpoint próprio (por exemplo, um Cloudflare Worker gratuito) **sem o `API_SECRET`**.
- O endpoint valida o esquema e os valores do ponto 2, limita o ritmo por IP e por `client_id`, rejeita versões fora da lista de releases e só depois reenvia para o GA4 com o segredo, que passa a existir só no servidor.
- O segredo atual pode então ser rodado sem afetar as versões novas.
- **Custos:** um serviço para manter, mais um ponto de falha (o envio já tolera falhas: `MAX_FAILURES` e `TIMEOUT`) e uma alteração da política de privacidade no README, porque o intermediário vê o IP.
- O que **não** resolve: quem extraia o endpoint do mod continua a conseguir enviar eventos que imitam o mod na perfeição. O intermediário só tira o caminho direto ao GA4 e impõe limites de ritmo.

Assinar os eventos no mod (HMAC) não ajuda: a chave ficaria no pacote, tal como o `API_SECRET`.

## Recomendação

1. Agora: dimensões personalizadas, o segmento "Tráfego válido" e a propriedade de testes separada (ponto 1). Não exigem alterações ao mod.
2. Se as estatísticas passarem a decidir alguma coisa (por exemplo, que versões continuam suportadas): exportação BigQuery com a vista de eventos válidos (ponto 2).
3. Só se aparecer poluição real e persistente: o intermediário (ponto 3), seguido da rotação do segredo.

Até lá, os números do GA4 devem ser lidos como indicativos.
