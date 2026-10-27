# Fontes locais de desenvolvimento — Driftkings

Guia atualizado em 26/10/2026 para a beta 0.1.3-beta.2. Os Markdown de `docs/` fazem parte do repositório; dados, scripts e snapshots locais de investigação continuam excluídos. A documentação não integra os pacotes do mod. Ver o [estado atual](STATUS.md).

## Localização e prioridade

Raiz das ferramentas: `E:\Wot_Mods_\Drift_Kings_ModPack\WoT_Tools`.

| Fonte | Caminho a partir dessa raiz | Utilização |
| --- | --- | --- |
| WoT SRC EU | `wot-src-EU/` | Referência do cliente de produção: APIs, assinaturas, eventos, modelos, modos de batalha e código Scaleform. É a referência atualmente configurada na build. |
| WoT SRC CT | `wot-src-CT/` | Consulta das mudanças do Common Test antes de uma atualização. Comparar com EU; não assumir que uma API CT já existe no cliente de produção. |
| XVM | `xvm-master/` | Comparar implementação de funcionalidades equivalentes, configuração, câmaras, tripulação, carrossel, minimapa e ciclo de vida. Preservar os valores e apresentação Driftkings. |
| ModsList | `ModList/` | Consultar API e integração do acesso ao painel de mods, recursos WULF e dependências. Começar por `README.md`, `python/`, `resources/` e `as3/`. |
| OpenWG Gameface | `GameFace/` | Consultar registo de recursos, injeção de UI e bibliotecas JavaScript. Começar por `README.md`, `python/openwg_gameface.py`, `resources/` e `tests/`. |

Existem também cópias em `wot-src-EU/`, `wot-src-CT/`, `ModList/` e `GameFace/`, além de `xvm-master/`. São referências alternativas para comparação; o nome «Atualizados» não prova que sejam mais recentes. Confirmar versão, revisão e diferenças antes de escolher uma cópia. Não trocar silenciosamente a fonte usada pelo compilador.

## Estado confirmado

- `wot-src-EU/.version_name`: **2.4.1.5504**.
- `wot-src-CT/.version_name`: **2.4.1.5466**. Neste conjunto local, o CT tem um número inferior ao EU; não o considerar automaticamente mais recente.
- As cópias EU e CT apresentam esses mesmos números; isso não demonstra igualdade de todos os ficheiros.
- `build_data/build_config.json`, em `reference`, aponta para `WoT_Tools/wot-src-EU`, versão **2.4.1.5504**, em leitura apenas.
- O contrato atual indica jogo **2.4.1.1**, raiz `D:/Games/World_of_Tanks_NA`, com regiões suportadas EU, NA e ASIA. A versão do snapshot SRC e a versão da pasta `mods` são identificadores diferentes.

Estes valores são um registo da consulta, não uma garantia de que as pastas não serão atualizadas posteriormente.

## Onde procurar

### Cliente WoT

- `sources/`: código Python do cliente. Procurar a classe/método original antes de criar ou alterar um hook; confirmar parâmetros, retorno e sequência de chamadas.
- `sources-as3/`: classes ActionScript e contratos Scaleform usados pelas interfaces Flash.
- `_stubs/`: apoio à análise de APIs; confirmar o comportamento no código disponível e no jogo.
- `.version_name` e `README.md`: identificação e contexto da extração.

### XVM

- `src/xvm_battle_camera/`: câmaras e zoom.
- `src/xvm_crew/` e `src/xvm_tooltips/`: tripulação e informação contextual.
- `src/xvm_tankcarousel/`, `src/xvm_hangar/` e `src/xvm_techtree/`: funcionalidades do hangar.
- `src/xvm_battle/`, `src/xvm_battle_minimap/` e `src/xvm_battle_replay/`: contexto de batalha, minimapa e replay.
- `release/`: procurar os exemplos de configurações distribuídas e relacionar cada campo com o código que o consome.

XVM é uma referência de implementação, não a especificação das nossas configurações. Confirmar dependências próprias, compatibilidade do cliente e licença antes de incorporar código.

### ModsList e Gameface

Consultar os README locais e a implementação correspondente à dependência efetivamente empacotada em `res/wotmods/`, declarada em `build_data/build_config.json`. Uma API da cópia de consulta pode não estar presente no binário distribuído.

No README Gameface consultado, WG 2.4.1 utiliza registo nativo `gui/gen_resources/*.json`; algumas APIs antigas de resolução de recursos são placeholders para WG. Verificar a implementação e a versão antes de as usar. Não transportar caminhos ou comportamentos exclusivos da Lesta para EU/NA/ASIA sem confirmação.

## Procedimento numa nova versão do jogo

1. Registar versão/build e região do cliente alvo, `.version_name` dos SRC e revisão das bibliotecas consultadas. Tratar estas pastas como fontes de leitura, sem alterar os originais para fazer a nossa build passar.
2. Comparar EU com CT e com o novo snapshot nos métodos, eventos, enums, modelos WULF/Gameface e classes Flash usados pelo Driftkings. Procurar também símbolos removidos ou renomeados.
3. Para cada funcionalidade alterada, confirmar o modo real: hangar, batalha normal, replay, treino/Topography ou eventos especiais. Não alargar suporte apenas porque um módulo importa sem erro.
4. Consultar XVM para a funcionalidade equivalente e relacionar as configurações com os respetivos consumidores. Manter os defaults Driftkings e remover ou corrigir opções sem efeito mediante o plano acordado.
5. Validar as dependências ModsList/Gameface e os SDK/bibliotecas Flash contra a versão pretendida. Só depois atualizar os contratos e manifestos da build que necessitem da alteração; não mudar apenas o número da referência.
6. Executar `python build_tools/validate_build_data.py`, testes Python 2.7/3, testes Gameface e lint. Manter Python 2.7 e JavaScript ES5 no cliente; regenerar defaults/catálogos pelas ferramentas próprias quando necessário.
7. Compilar e testar no cliente alvo. Verificar `game.log`, entrada/saída de batalha, mudança de veículo/modo e descarregamento dos componentes. Testes com stubs não substituem o teste no jogo.

## Publicação

Este guia descreve referências locais de desenvolvimento. Não copiar os SRC, repositórios externos ou snapshots de consulta para `mod/` ou para o GitHub. A versão pública contém apenas documentação Markdown; os ficheiros locais de estudo não são distribuídos. Nenhum destes caminhos constitui uma nova dependência de runtime; o contrato da build continua a ser a fonte de verdade para a compilação.

Atualização de 27 outubro 2026: SWC sincronizados com a referência 2.4.1.5504, alvo 2.4.1.1 e novo hash dos marcadores verificado em EU/NA. [Plano e validação](PLANO_ATUALIZACAO_2_4_1_1.md). Os hashes dos três recursos Gameface usados pelos patches mantêm-se idênticos.
