# Validação manual — Driftkings SettingsLab 0.1.0

Estado: build local validado; testes dentro do WoT ainda pendentes.
Alvo: WoT EU 2.4.0.2. Não assumir compatibilidade com outro cliente.
Pacote: `build/unified/Driftkings.wotmod`.
SHA-256: `7181d7f0a605a7c9d84e293949ba9e6ac2c7ec3f4aa32dad714ed8bddb504f07`.

Esta checklist não instala o pacote. A instalação e a execução ficam a cargo do
utilizador, quando decidir testar. Guardar uma cópia dos perfis e do history/cache
existentes antes do teste, para permitir comparação e reposição posterior.
Manter apenas um pacote Driftkings ativo e usar dependências compatíveis com o
cliente alvo: as referências validadas são OpenWG Gameface 1.1.6 e ModList 1.7.9.

## Registo da sessão

- [ ] Registar versão/build EU, resolução, escala da interface e lista de mods.
- [ ] Registar hash do pacote e perfil utilizado.
- [ ] Identificar cada teste como PASS, FAIL ou NÃO TESTADO, com reprodução e imagem/log se necessário.
- [ ] Separar sessão Random ao vivo e sessão de replay.

## Login, hangar e Settings

- [ ] Iniciar o jogo e entrar no hangar sem traceback associado ao Driftkings.
- [ ] Confirmar no log `Initialized 33/33 components` e ausência de erros Analytics.
- [ ] Abrir Settings pelo ModList e por F10; repetir fechar/abrir.
- [ ] Confirmar shell, sidebar por categorias, pesquisa e seleção dos módulos.
- [ ] Confirmar enabled/status, dependências, restartRequired e apply timing visual.
- [ ] Alterar um valor; Cancel não deve persistir; Undo deve restaurar o valor anterior.
- [ ] Apply/Save deve persistir; reabrir Settings e reiniciar o cliente para verificar valores.
- [ ] Confirmar controlos antigos: checkbox, slider, dropdown, texto, cor e hotkey.
- [ ] Dropdowns com fundo escuro e texto legível; linhas sem intervalos verticais enormes.
- [ ] SixthSense: escolher sons e Reproduzir/Parar antes de ativar som personalizado; Cancel preserva a escolha guardada.
- [ ] Testar Tab/Shift+Tab, Enter, Escape, foco, dropdowns e modais; sem captura após fechar.
- [ ] Abrir ColorPicker2D; testar rato, teclado, hex/RGB, Apply e Cancel.
- [ ] Testar Alpha num controlo que exponha essa metadata; verificar a escala correta.
- [ ] Testar hotkey simples, combinações, apagar e cancelar captura; modificador isolado só onde permitido.
- [ ] Selecionar/criar/clonar/renomear perfis pelos fluxos existentes; verificar isolamento dos valores.
- [ ] Abrir um perfil existente personalizado; confirmar que não foi reposto pelos defaults.
- [ ] Confirmar Marks Hangar, delta do período, estrelas, milestones e compactMode.
- [ ] Confirmar TechTree e estilo harmonizado; trocar rapidamente de veículos em ambos.
- [ ] Verificar que dados e marcas pertencem ao veículo selecionado e não ficam desatualizados.
- [ ] Testar pelo menos 1920×1080, 2560×1440, 3440×1440 e 3840×2160, se disponíveis.

## Batalha Random e replay

- [ ] Entrar numa Random; confirmar interface e saída para hangar sem erros.
- [ ] Abrir replay compatível; confirmar visibilidade segundo as configurações existentes.
- [ ] Testar Marks Legacy com mensagem personalizada e cada um dos 12 presets antigos.
- [ ] Testar Compact, Normal e Detailed; alternar pelas opções disponíveis sem duplicar o painel.
- [ ] Confirmar MarksCard: percentagem, delta positivo/negativo/zero, progress e damage/target.
- [ ] Testar veículos com 0/1/2/3 marcas e valores em torno de 65/85/95%.
- [ ] Confirmar que 3 marcas não apresentam uma quarta marca ou meta incoerente.
- [ ] Verificar dados indisponíveis, alvo desconhecido e ausência de combate/dano.
- [ ] Testar drag/posição, reset, alinhamento, scale, opacity/background e visibilidade.
- [ ] Verificar posição após redimensionar e numa segunda batalha/replay.
- [ ] Confirmar ausência de `KeyError: alignX/alignY` no Marks e no InfoPanel.
- [ ] Testar Alt premir/soltar e atalhos Marks sem erro `MARKS_ON_GUN_BATTLE.FONT`.
- [ ] Confirmar as opções showMarks/showDelta/showDamage/showProgress/showTargets.
- [ ] Confirmar teclado e rato da batalha depois de fechar Settings e os seus modais.

## Outros componentes ativos

- [ ] TAB/BattleLoading e PlayerPanelPro: perfis, HP, spotted e estatísticas.
- [ ] Minimap: ícones, labels, escala e configurações personalizadas.
- [ ] SixthSense: imagem, som e ciclo de exibição.
- [ ] OwnHealth, InfoPanel, BattleStat e BattleEfficiency.
- [ ] Outros componentes ativos do `build/unified/components.json`.
- [ ] Repetir transição login/hangar/batalha/hangar e troca rápida de veículos.

## Compatibilidade em runtime

Executar sessões separadas com combinações disponíveis; uma combinação não
disponível deve ficar marcada como NÃO TESTADA.

| XVM | Battle Observer | Estado e observações |
| --- | --- | --- |
| ausente | ausente | pendente |
| presente | ausente | pendente |
| ausente | presente | pendente |
| presente | presente | pendente |

- [ ] Confirmar que warnings são informativos e não desativam módulos automaticamente.
- [ ] Confirmar deteção sem inicialização/import obrigatório dos mods externos.
- [ ] Distinguir presença, possível conflito e conflito confirmado.
- [ ] Verificar PlayerPanelPro, Minimap e Marks com cada combinação.

## game.log e python.log

Após cada sessão, guardar o log completo com horário e passos executados. Consultar
`game.log` e também `python.log`, se o cliente o produzir. Procurar por:

```text
Traceback
ERROR
CRITICAL
Driftkings
Gameface
Scaleform
resource
view
exception
```

Uma pesquisa opcional, apenas de leitura, em PowerShell:

```powershell
Select-String -LiteralPath 'CAMINHO_DO_LOG' -Pattern 'Traceback|ERROR|CRITICAL|Driftkings|Gameface|Scaleform|resource|view|exception' -Context 3,8
```

- [ ] Classificar cada ocorrência pela origem: Driftkings, cliente, outro mod ou desconhecida.
- [ ] Usar traceback, módulo, recurso e horário para atribuir a origem; não basta a palavra ERROR.
- [ ] Só considerar um warning do cliente conhecido quando houver evidência numa sessão de comparação.
- [ ] Registar erros de layout/resource map, criação/destruição de views e carregamento de scripts/SWF.
- [ ] Confirmar ausência de erros novos nas transições e sessões repetidas.

## Critérios para certificação

O build comprova conteúdo, bytecode, contratos e recursos. Não comprova rendering
no motor real, callbacks do cliente, input da batalha, dados MoE reais, desempenho,
ausência de erros em `game.log` ou convivência com mods externos.

Uma aprovação de runtime exige completar a matriz acima e anexar os logs. O
history/cache não teve formato ou cálculo alterado nesta fase; alterações normais
de dados durante batalhas devem ser distinguidas de corrupção ou migração.
Não publicar release/tag, fazer upload ou distribuir automaticamente após os testes.
