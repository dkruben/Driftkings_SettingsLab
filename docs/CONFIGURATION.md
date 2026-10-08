# Configurações por perfil

A organização segue o modelo do battle_observer: valores por defeito em Python,
um `load.json` para escolher o perfil e JSON separados por componente.
A implementação usa o painel próprio do Driftkings, aberto pelo ModList ou F10.

## Estrutura no cliente

```text
mods/configs/Driftkings/
    load.json
    default/
        own_health.json
        minimap_plugins/             # minimap.json, minimap_labels.json, minimap_circles.json, minimap_lines.json
        battle_stat.json
        ...
        carousel_stats/
            carousel.json
            carouselNormal.json
            carouselSmall.json
        player_panel_pro/
            general.json
            playersPanel.json
            battleLoading.json
            statisticForm.json
            panelNone.json
            panelShort.json
            panelMedium.json
            panelMedium2.json
            panelLarge.json
    competitivo/
        ...
    i18n/
        en.json                # traduções personalizadas de todos os componentes
    ...
```

`load.json` contém apenas a seleção do perfil:

```json
{
    "loadConfig": "default"
}
```

Os ficheiros de um perfil são objetos JSON normais, sem a raiz `components`,
sem includes e sem formato `.xc`. Exemplo de `own_health.json`:

```json
{
    "enabled": true,
    "x": 0,
    "y": -55,
    "colors": {
        "ally": "#60CB00",
        "enemy": "#ED070A"
    }
}
```

As restantes opções deste exemplo são preenchidas pelos valores Python. Os
exemplos completos estão em `res/configs/Driftkings/default/`. As escalas de cor,
macros, atalhos, formatos, duas colunas e controlos visuais existentes mantêm-se.

## Python e gravação

- `settings/settings_data.py`: único módulo de valores por defeito, atalhos
  e configuração partilhada dos 33 componentes.
- `settings/templates.py`: todos os menus, com uma inicialização comum.
- `i18n/`: um catálogo Python por idioma, incluído no pacote; o loader partilha
  os textos comuns da janela entre todos os componentes.
- `settings/loader.py`: seleção do perfil, importação inicial, validação dos
  tipos conhecidos, leitura e gravação. `user_settings.own_health`, por exemplo,
  dá acesso ao dicionário usado pelo controlador, sem criar uma segunda cópia.
- `settings/profiles.py`: seleção e cópia de perfis no painel visual próprio.
- `settings/store.py`: escrita atómica, backups, recuperação e leitura do antigo
  documento central para migração.

O painel grava nos mesmos JSON do perfil ativo. Os ficheiros em falta são criados
com os valores por defeito; opções novas são preenchidas em memória. Campos
personalizados desconhecidos são mantidos. JSON inválido e tipos incompatíveis
causam um erro no log, sem substituir o ficheiro do jogador. As gravações mantêm
um `.bak`; o PlayerPanelPro conserva a recuperação conjunta dos seus oito JSON.

## Escolher ou copiar um perfil

No painel, abrir `Driftkings`, escolher um perfil existente e aplicar. Para criar
um perfil, escrever um nome em "Create a copy of the active profile" e aplicar:
a cópia inclui os JSON e subpastas de configuração do perfil ativo. Nomes aceitam
letras ASCII, números, `_` e `-`, até 64 caracteres. Um perfil existente nunca é
substituído por uma cópia.

A seleção é aplicada no próximo arranque do jogo. Até reiniciar, todas as
alterações continuam a ser gravadas no perfil que está ativo. Isto também se
aplica a alterações manuais de `load.json` durante a sessão. Ao contrário da
mudança imediata do battle_observer, esta versão mantém uma única configuração
ativa durante a sessão. As alterações individuais mantêm o comportamento de
atualização que cada módulo já tinha.

Também é possível criar uma pasta com outro perfil e apontar `load.json` para
ela antes de iniciar o jogo. As opções que faltarem recebem os valores Python.

## Migração

Só o perfil `default` importa configurações antigas, quando o novo ficheiro
ou a nova subpasta ainda não existe:

1. Para componentes normais, a secção de `Driftkings.json` tem prioridade;
   se não existir, lê `<Componente>/<Componente>.json`.
2. Carrossel e PlayerPanelPro importam os JSON já divididos das suas antigas
   pastas. O PlayerPanelPro conserva também a migração das configurações
   anteriores de HP/deteção e estatísticas quando não há ficheiros divididos.
3. Sem configuração anterior, cria os valores por defeito. Outros perfis novos
   usam sempre esses valores, sem importar configurações antigas.

Os documentos antigos permanecem disponíveis para recuperação. Não são a
configuração ativa depois da importação. A distribuição contém exemplos: para
preservar as opções instaladas, deixar primeiro o wotmod criar o perfil, sem copiar
os exemplos por cima. Os ficheiros antigos do carrossel com `slot1` a `slot4`
continuam fora da migração, como na implementação anterior.

As traduções personalizadas ficam em `mods/configs/Driftkings/i18n/<idioma>.json`,
fora dos perfis. Contas guardadas e cache de estatísticas mantêm os seus locais. Trocar ou copiar um perfil não duplica contas nem cache.


## Traduções unificadas

Os 11 idiomas do cliente EU estão em `source/scripts/client/Driftkings/i18n/`,
um ficheiro Python por idioma. Cada catálogo tem secções por componente e uma
secção `common` para os botões e mensagens da janela. Não há dicionários de
tradução dentro dos módulos de configuração ou de batalha.

O cliente escolhe o idioma e usa inglês como recurso para idiomas não suportados.
Para personalizar textos, o ficheiro externo do idioma aceita alterações parciais:

```json
{
    "common": {"UI_native_save": "Guardar"},
    "OwnHealth": {"UI_description": "Os meus pontos de vida"}
}
```

Na primeira leitura, as traduções dos antigos `<Componente>/i18n/<idioma>.json`
são reunidas neste ficheiro. Os originais são conservados. Um JSON já existente
na pasta unificada tem prioridade. Sem personalizações, o ficheiro é `{}` e o
jogo usa os catálogos incluídos no wotmod. JSON inválido é preservado e reportado,
com recurso aos textos incluídos no pacote. Catálogos antigos inválidos impedem
concluir a importação desse idioma, permitindo corrigir o original e repetir.
