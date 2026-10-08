# Verificar atualizacoes das referencias

Na raiz do SettingsLab, executar `Verificar-Atualizacoes.cmd` com duplo clique,
ou no terminal:

```powershell
.\Verificar-Atualizacoes.cmd
```

Requer Python 3.9+ e o launcher `py` (ja existentes neste computador). O Python
2.7 continua a ser o interpretador dos mods; este comando e uma ferramenta de
desenvolvimento independente.

Consulta apenas metadados dos repositorios originais:

- [wot-src, ramo EU](https://github.com/izeberg/wot-src/tree/EU): commit,
  `.version_name` e `sources/version.xml` da mesma revisao publicada.
- [ModList](https://gitlab.com/wot-public-mods/mods-list/-/releases): releases estaveis.
- [GameFace](https://gitlab.com/openwg/wot.gameface/-/releases): releases estaveis.

A pasta predefinida e `WoT_Tools` junto da pasta `Driftkings_Mods_Hide`.
As referencias sao apenas lidas. O comando nao descarrega pacotes, nao extrai
arquivos, nao instala mods e nao altera o jogo ou as configuracoes de compilacao.

Para guardar o resultado ou indicar outra pasta:

```powershell
py -3 build_tools/check_tool_updates.py --report build/updates/report.json
py -3 build_tools/check_tool_updates.py --tools-root "E:\Wot_Mods_\Drift_Kings_ModPack\WoT_Tools" --json
```

As versoes de ModList/GameFace sao inferidas dos nomes das pastas extraidas.
Uma pasta sem `.git` nao permite confirmar a revisao exata de wot-src. Uma
versao coincidente nao prova que a extracao terminou nem que nao houve alteracoes
locais. Metadados em falta ou divergentes sao indicados separadamente.

Uma release mais recente pode exigir outra versao do cliente. Consultar os
requisitos antes de atualizar as dependencias do pacote Driftkings.

Falhas de rede, limites das APIs e erros de leitura aparecem como ERRO; nao sao
tratados como ausencia de atualizacoes. As outras verificacoes continuam.
Codigo de saida: 0 = consulta concluida (incluindo atualizacoes disponiveis),
1 = pelo menos uma verificacao falhou, 2 = argumentos invalidos.
