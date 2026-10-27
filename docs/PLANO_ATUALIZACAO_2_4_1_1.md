# Atualização para WoT 2.4.1.1

Data: 27 outubro 2026. Atualização da referência em WoT_Tools confirmada pelo autor.

## Etapas
- [x] Verificar a referência EU 2.4.1.5504 e os clientes EU #989 / NA #987.
- [x] Comparar recursos Gameface e contrato nativo dos marcadores antes de alterar pins.
- [x] Atualizar alvo, oito SWC, hashes e metadados de patches/locales.
- [x] Executar validações e gerar WOTMOD completo.
- [x] Registar resultados, commit/push e acompanhar CI.

## Evidência
- Referência local `WoT_Tools/wot-src-EU/.version_name`: 2.4.1.5504. Atualização upstream registada como `ed377b7bc5e8c232cf41bd0887bcfa0d75005fcb` nas notas de WoT_Tools. A referência é usada apenas para leitura.
- Oito SWC copiados de `sources/res/gui/flash/swc`, conservando os nomes locais e recalculando SHA-256; todos diferem dos exemplares anteriores.
- Carrossel, Barracks e tooltip de tripulação mantêm hashes de origem idênticos, tanto em EU como em NA. Mantidas operações e hashes dos patches; atualizados apenas os metadados de versão/build.
- O SWF dos marcadores tem o mesmo novo hash em EU/NA: `6f6711bb56832850b7b0286ff76540ca209b54752775ffa23406aaa5a66db10e`.
- Revistos os campos e assinaturas usados (`model`, `vehicleDestroyed`, `isStickyAndOutOfScreen`, `updateHealth(int,uint,String,int)`, settings e colorblind). O patcher aceitou os métodos/getter únicos do novo ABC e o RABCDAsm remontou o ABC alterado. As notas upstream não indicam alterações aos fontes dos marcadores.
- O alvo continua NA, com referência EU, conforme a configuração existente. As configurações pessoais e a instalação EU não são alteradas. As fixtures de testes que usam versões antigas como dados de exemplo mantêm-se válidas.
- Nenhuma release/tag será substituída por esta atualização de desenvolvimento. A confirmação visual em jogo continua necessária.

## Registo
- Build completa debug/beta concluída: 313 módulos Python 2.7, bibliotecas e marcadores Flash recompilados e todos os geradores Gameface/nativos concluídos. O bloqueio de versão foi resolvido sem desativar validações.
- README e guias distinguem o novo alvo de desenvolvimento das releases publicadas para 2.4.1.0.
- Auditoria do pacote: manifesto para 2.4.1.1, 313 bytecodes, dois ABC e dez fontes no SWF dos marcadores; ZIP instala em `mods/2.4.1.1`. SHA-256 WOTMOD: `73fdcb6f5d526c145f0130d5b4c2d2077847d23de31250acbe0c6389daf5c5e9`.
- Aprovados 443 testes core e 27 testes de configuração em Python 2.7/3, 36 testes installer/build, suite Gameface/ESLint, defaults/catálogo e validação dos patches contra o cliente instalado. Zero nomes indefinidos.

- Atualização enviada para `develop` em `e019622`, com [CI aprovado](https://github.com/dkruben/Driftkings_SettingsLab/actions/runs/40567140916). Pacote regenerado a partir desse commit; SHA acima atualizado. Este encerramento documental terá validação própria.
- Build disponível em `build/debug/beta/0.1.3-beta.2/`, incluindo WOTMOD e ZIP com pasta de instalação 2.4.1.1. Não houve publicação de release nem alteração da instalação EU.
