# Revisão geral — 8 de outubro de 2026

Revisão estática e execução dos testes locais em SettingsLab. Referências usadas exclusivamente em leitura: `E:/Wot_Mods_/Drift_Kings_ModPack/WoT_Tools`. Não houve instalação, deployment nem alterações no projeto original. O código funcional foi preservado; foram acrescentados o inventário reproduzível e este relatório.

## Resultados prioritários

### 1. Valores distribuídos divergem dos valores predefinidos — prioridade alta

`test_unified_player_panel.test_shipped_json_matches_python_defaults` e `test_carousel_store.test_distributed_templates_match_defaults` falham. O levantamento completo identifica **15 diferenças em seis JSON**, não apenas as duas diferenças de cor que aparecem primeiro nos testes:

| Configuração | Diferenças |
| --- | ---: |
| PlayerPanelPro/playersPanel.json | 2 |
| PlayerPanelPro/statisticForm.json | 3 |
| PlayerPanelPro/panelMedium.json | 1 |
| PlayerPanelPro/panelMedium2.json | 1 |
| CarouselStats/carouselNormal.json | 6 |
| CarouselStats/carouselSmall.json | 2 |

As diferenças incluem cores `0x...` versus `#...`, espaços nas macros e fontes `mono` versus `$FieldFont` ou fonte omitida. Isto pode produzir apresentação diferente ao usar os ficheiros distribuídos ou restaurar defaults. Não é evidência de que todas as cores antigas sejam inválidas. Antes de corrigir, escolher a apresentação pretendida e sincronizar ambas as representações, preservando configurações pessoais. Detalhes exatos: `build/review/default_differences.json`.

### 2. Teste de layout incompatível com BOM — prioridade média

`build_tools/tests/test_source_layout.py:37` lê com `utf-8` antes de passar o conteúdo a `ast.parse`. Um dos ficheiros inspecionados contém BOM, causando `SyntaxError: U+FEFF`. As outras verificações do mesmo teste já usam `utf-8-sig`. Corrigir essa leitura de forma consistente. A verificação real em Python 2.7 passou; esta falha não demonstra erro de sintaxe do mod no jogo.

### 3. Helper de diálogos antigo contém atributos desatualizados — prioridade média

`source/scripts/client/Driftkings/common/utils/delayed/utils/old_dialogs.py:51` usa `_SimpleDialog__handler` e `_SimpleDialog__isProcessed`; o `SimpleDialog` de referência usa `_handler` e `_isProcessed`. O hook de dispose também escreve o atributo antigo. Num diálogo de três botões, o callback pode falhar ou a marca de processamento pode ser ignorada, permitindo novo processamento ao fechar.

O nome `__callHandler` passado a `override` é resolvido pelo helper `find_attr_name` para `_callHandler`; portanto, não há fundamento para afirmar que esse nome sozinho impede o import. O módulo continua importado por `delayed/utils/__init__.py` e instala patches diretamente, mas não foram encontrados consumidores internos das três funções públicas. É candidato a remoção após verificar consumidores externos; em alternativa, adaptar os atributos e colocar os hooks sob gestão de Core.

### 4. AimingAngles silencia exceções — prioridade média

`source/scripts/client/Driftkings/battle/aiming_angles.py` contém 13 retornos em blocos `finally`. Exemplo: linhas 94–114. Se o processamento do mod falhar, o retorno suprime a exceção sem registo, dificultando perceber por que o indicador parou ou ficou desatualizado. Preservar a chamada original e registar erros do mod explicitamente. Não substituir todos os `finally` do projeto indiscriminadamente: vários fazem limpeza necessária ou acompanham tratamento de erro já existente.

### 5. Atualizações das dependências exigem migração coordenada — prioridade alta antes de atualizar

O projeto distribui **ModsListAPI 1.7.9 + OpenWG Gameface 1.1.6**, explicitamente documentados e verificados por testes. As referências locais contêm ModList 1.8.0 e GameFace 1.2.1/1.2.2, mas a versão mais recente não é automaticamente adequada:

- O README de ModList 1.8.0 exige **WoT 2.4.1 ou posterior**. O alvo deste workspace é **2.4.0.2**. Manter 1.7.9 neste alvo.
- Nas fontes de GameFace 1.2.1 e 1.2.2, `res_id_by_key` no ramo WG é um placeholder obsoleto que devolve `-1`. `Driftkings/ui/gameface.py:14` depende dessa função. Atualizar apenas o pacote comprometeria a resolução dos recursos das janelas, cartões do hangar e bridge de ratings. Migrar para os accessors nativos compatíveis com o novo cliente juntamente com a atualização.
- A pasta de referências não contém as fontes de GameFace 1.1.6. O teste JavaScript executou o bootstrap do pacote 1.1.6 realmente distribuído e passou; isso não equivale a validar todo o Python dessa biblioteca em jogo.

O bridge atual é legado em relação às versões futuras, mas a revisão não o classifica como quebrado com a dependência 1.1.6 atual.

### 6. Documentação do protótipo ficou desatualizada — prioridade baixa

`SETTINGS_LAB.md` descreve uma janela independente Scaleform. A implementação em `views/hangar/settings_window.py` e o adapter de `settings/panel/compatibility.py` usam Gameface/WULF. Atualizar a descrição do estado atual para evitar diagnósticos e instruções baseados no protótipo anterior.

### 7. Módulo vazio — prioridade baixa

`common/utils/delayed/utils/dialogs.py` contém apenas `pass`, embora seja importado com wildcard. É candidato a limpeza, preservando eventual compatibilidade de imports externos. Os `__init__.py` vazios de pacotes não devem ser removidos pelo mesmo critério.

## Referências e integridade

`sources/version.xml` identifica **EU v.2.4.0.2 #966**; `.version_name` contém **2.4.0.5473**. `build_data/build_config.json` regista ambos corretamente. Estes identificadores diferentes, por si só, não provam uma extração incompleta.

Foram indexados **8 600 módulos Python** nas raízes client/common/shared, stubs e APIs selecionadas. Nos grupos de imports inventariados por `build_tools/review_reference_imports.py`, **nenhum import ficou sem ficheiro de referência**. Foram analisados 228 ficheiros do projeto em Python 3; o helper `abstract.py`, com sintaxe específica de Python 2, foi validado pela verificação Python 2.7. Foram confirmados métodos relevantes dos hooks de câmaras, Vehicle, MapCaseMode e crosshair.

Este levantamento confirma a presença das referências utilizadas, mas não certifica a extração inteira por hash nem a compatibilidade de todas as assinaturas. O relatório JSON identifica as raízes efetivamente verificadas. A análise de imports não cobre todos os imports dinâmicos, namespaces de eventos especiais ou módulos nativos.

## Validação executada

| Verificação | Resultado |
| --- | --- |
| `python -B -m unittest discover -s build_tools/tests` | 473 testes: 470 passaram, 2 falhas, 1 erro |
| Smoke check no Python 2.7 incorporado no Mercurial | Passou: sintaxe/imports locais, hooks, settings, recuperação, perfis, i18n, carousel, painel e minimapa |
| `python -B build_tools/check_flash_contracts.py` | 9 componentes OK |
| `python -B build_tools/localize_configs.py --check` | 12 catálogos; 0 erros |
| `node build_tools/tests/gameface_dependency_test.js` | Bootstrap real OpenWG 1.1.6 + Driftkings passou |
| `python -B build_tools/review_reference_imports.py` | 0 imports não resolvidos nos grupos verificados |

O log completo dos testes está em `build/review/tests.log`. Mensagens de `disk full`, configuração inválida e falhas de callbacks no log fazem parte de testes deliberados de recuperação; não são novos erros de execução. O aviso de `datetime.utcnow` vem do Python 3.14 de desenvolvimento e não justifica usar `datetime.UTC`, indisponível no Python 2.7 do jogo.

Os scripts `release.cmd`, `build_tools/run_build.cmd`, `run_build.ps1` e `build_lab.py` foram inspecionados: o fluxo atual produz artefactos locais. Não foi executado um novo build completo nem testada a UI no cliente. Presença de APIs e testes com mocks não garantem renderização, foco, transições lobby/batalha ou callbacks no motor real.

Não foram encontrados imports diretos de ModSettingsAPI no código funcional pesquisado. O adapter de templates tem função atual no painel próprio e não deve ser removido simplesmente pelo nome `compatibility`.

## Ordem recomendada

1. Harmonizar os seis JSON com os defaults pretendidos e corrigir a leitura BOM no teste.
2. Retirar ou adaptar o helper antigo de diálogos e rever o tratamento de erros de AimingAngles.
3. Atualizar a documentação do protótipo.
4. Validar em jogo as janelas, PlayerPanelPro e transições; qualquer deployment continua dependente de pedido explícito.
5. Planear a migração de recursos nativos quando o alvo mudar para WoT 2.4.1 ou posterior.
