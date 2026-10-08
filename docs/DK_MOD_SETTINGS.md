# Configurações integradas do Driftkings

O Core inicia o serviço de configurações como parte do pacote único. Não existe
um componente Python DKModSettings independente. O manifesto com esse nome
empacota apenas os recursos Gameface e o respetivo mapa de recursos.

## Utilização

No hangar, abrir pelo ModList → Driftkings ou pelo atalho configurado (F10 por
defeito). O botão adicional do hangar foi removido. Em batalha, usar o atalho.
A navegação lateral inclui pesquisa e barra de deslocamento arrastável; os
controlos também têm barra própria. A roda foi ajustada ao sentido reportado
no Gameface: rodar para baixo faz avançar para as opções inferiores.

Os menus usam duas colunas, dropdowns, seleção visual de cores e atalhos.
Os valores numéricos usam sliders, com entrada direta (incluindo vírgula decimal)
e ajuste pelas setas do teclado. Os pares de opções esquerda/direita mantêm
a respetiva coluna; menus anteriormente com uma coluna são distribuídos em duas.
Em janelas estreitas, as colunas passam a uma. Português e inglês estão incluídos.

- Aplicar guarda as alterações e mantém a janela aberta.
- Guardar e aplicar guarda e fecha, exceto quando é necessário decidir o reinício.
- Cancelar descarta alterações ainda não aplicadas.
- Fechar com alterações pendentes permite guardar, descartar ou continuar.
- Desfazer e repor predefinições trabalham sobre o rascunho.
- Perfis permitem guardar e importar conjuntos de opções no hangar.

## Pré-visualizações

No Sexto Sentido, a lista de ícones mostra miniaturas e a imagem selecionada
aparece abaixo do seletor. O caminho de uma imagem personalizada também tem
pré-visualização. Os campos de imagem dos restantes módulos, como a mira de
artilharia do minimapa, usam o mesmo mecanismo.

As imagens locais PNG/JPEG dentro de `mods/configs/` (até 2 MiB) são lidas sem
alterar ficheiros e mantidas apenas em memória enquanto a janela está aberta.
Recursos `gui/` são apresentados diretamente pelo cliente. Uma imagem ausente
mostra uma indicação no painel; a seleção não é aplicada automaticamente.

O seletor de som do Sexto Sentido inclui os dez eventos do banco do pacote e
preserva um evento personalizado já configurado. **Ouvir / Parar** testa a
seleção do rascunho antes de guardar. Mudar de som, mudar de módulo ou fechar
a janela interrompe a pré-visualização anterior. A reprodução depende do banco
estar disponível no cliente; não carrega nem altera bancos externos.

## Alterações durante a batalha

Estão disponíveis AutoAimOptimize, SafeShot, InfoPanel e PlayerPanelPro, além
das preferências da interface. As opções de ativação do InfoPanel e PlayerPanelPro
ficam bloqueadas porque a criação das vistas ocorre no início da batalha.
Não se recarregam os JSON nem se reinicializam os módulos ao abrir o painel.
A importação de perfis fica indisponível em batalha, incluindo no backend.

`BATTLE_EDITABLE`, `APPLY_TIMING`, `application_timing()` e `requires_restart()`
em `settings_data.py` definem esta política. A descrição de cada opção indica
quando a alteração passa a ser usada. O prazo é resolvido pelo caminho real
da opção, incluindo campos aninhados, não pelo texto traduzido ou nome do controlo.

| Aplicação | Exemplos | Aviso de reinício |
| --- | --- | --- |
| Ao guardar / próxima atualização do módulo | Carrossel, marcas na garagem e árvore tecnológica, relógio, AutoAim, SafeShot, formato do BattleStat | Não |
| Próxima batalha | Ativação de InfoPanel, PlayerPanelPro e OwnHealth; FlightTimer, DispersionTimer e SixthSense | Não |
| Ao reabrir o ecrã / próxima utilização | Opções do hangar, tripulação, gestor de contas, resultados de BattleEfficiency | Não |
| Reinício do cliente | Perfil principal, bancos de som, cache do ArcadeZoom e opções do listener de mudança de câmara do ZoomExtended | Sim |

Campos não classificados conservam o aviso de reinício. Por exemplo, MainGun
atualiza a posição e opacidade pelos callbacks, mas a imagem e dimensões do fundo
são definidas na construção; BattleStat mantém o estilo `textFormat` em cache,
mas lê o conteúdo `format` durante a atualização. Estas opções têm prazos distintos.
O editor em batalha mantém bloqueadas todas as opções que não se aplicam ao vivo.

Quando necessário, depois de guardar, surge **Reiniciar agora / Mais tarde**.
O reinício usa a API do cliente/WGC e só é permitido no hangar. Não é automático.
Reverter as opções aos valores anteriores elimina o respetivo aviso pendente.

## Organização, comparada com battle_observer

A referência local usa `SettingsData` para reunir os valores dos módulos e
mantém o carregamento separado. Foi adotada essa separação:

| Local | Responsabilidade |
| --- | --- |
| `settings/settings_data.py` | Valores predefinidos, atalhos, estado partilhado e política de aplicação |
| `settings/loader.py` e `store.py` | Perfis, leitura, migração e persistência dos JSON |
| `settings/templates.py` | Declarações dos menus dos módulos |
| `settings/registry.py` | Integração com os callbacks dos módulos |
| `settings/panel/` | Backend interno da interface, controlos, rascunhos, perfis e traduções do painel |
| `views/hangar/settings_window.py` | Janela Gameface partilhada entre hangar e batalha |
| `res/gui/gameface/mods/Driftkings/DKModSettings/` | HTML, CSS e JavaScript |

Os módulos Python usam nomes em minúsculas com palavras separadas por `_`.
Exemplos: `auto_aim`, `players_panel`, `minimap`, `gun_marks`, `info_panel`.
O mapa completo está em `docs/module-renames.json`. Os IDs das configurações
continuam estáveis, evitando perder os JSON e traduções dos jogadores.

## Persistência

Os módulos mantêm os seus documentos em `mods/configs/Driftkings/<perfil>/`.
As preferências da interface ficam em `mods/configs/Driftkings/.settings/`,
incluindo `dk_settings.json`, `profiles/` e eventuais traduções em `locales/`.
No primeiro arranque, documentos antigos de `mods/configs/DriftKingsMods/`
são copiados apenas quando o destino ainda não existe. Os originais são
preservados; documentos inválidos são assinalados no log e não são copiados.

O adaptador chama os escritores e callbacks existentes, sem criar uma segunda
configuração dos módulos. As demonstrações de tradução e som não são incluídas.

## Verificação e limites

Executar no SettingsLab:

```text
py -3 -m unittest discover -s build_tools/tests
node build_tools/tests/dk_settings_gameface_test.js
py -3 build_tools/audit_project.py --check all
py -3 build_tools/build_lab.py
```

Os testes cobrem permissões em batalha, rascunhos, migração, políticas por opção e caminhos aninhados, avisos de reinício,
roda, arrasto das barras e limpeza dos eventos. A compilação produz
`build/unified/Driftkings.wotmod`; não instala no jogo.
A integração da janela já foi confirmada pelo jogador no cliente. As novas
classificações de aplicação por opção devem ser verificadas ao testar este pacote.

## Próximas melhorias possíveis

- Acrescentar callbacks para atualizar as opções que ainda dependem de caches de arranque.
- Mostrar uma comparação antes de importar um perfil.
- Validar macros e referências dos JSON com indicação do ficheiro e campo.

Estas extensões não são dependências da integração atual.
