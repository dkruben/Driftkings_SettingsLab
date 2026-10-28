# Estado da documentação

Atualizado em 28 de outubro de 2026. Os caminhos e comandos partem da raiz do repositório.

## Referência atual

- Branch de desenvolvimento: `develop`.
- Alvo do cliente: WoT `2.4.1.1`, Wargaming EU/NA/ASIA; contratos e ferramentas em `build_data/` e `build_tools/`.
- As versões publicadas e os downloads estão no [README](../README.md). O histórico de publicação permanece nas releases e no Git.
- O painel de configurações continua em construção. A ausência de erros num replay não valida todas as páginas, previews ou operações de gravação.
- As seis fases de otimização foram revistas e enviadas no commit `202f476`. A auditoria estática não demonstra ganhos quantitativos de FPS.

## Guias mantidos

| Área | Documento |
| --- | --- |
| Instalação, funcionalidades e downloads | [README](../README.md) |
| Desenvolvimento, verificações e publicação | [CONTRIBUTING](../CONTRIBUTING.md) |
| Painel de configurações | [Relatório funcional](RELATORIO_PAINEL_CONFIGURACAO.md) |
| Marcadores dos veículos | [Guia dos marcadores](vehicle_markers/README.md) |
| Carrossel | [Guia do carrossel](vehicle_carousel/README.md) |
| Preferências do lobby | [Guia](hangar_preferences/README.md) |
| Fontes e caracteres | [Fontes](FONTES.md) |
| Traduções | [Guia i18n](i18n/README.md) |
| Áudio e Sexto Sentido | [Bancos](audioww/README.md) e [ícones](sixthsense_icons/README.md) |
| Referências locais de desenvolvimento | [Fontes de desenvolvimento](FONTES_DESENVOLVIMENTO.md) |
| Arquitetura Gameface | [Inventário e migração](PLANO_GAMEFACE.md) |
| Arquitetura Flash/Scaleform | [Inventário e migração](PLANO_FLASH.md) |
| Painel Grande Calibre | [Gameface](MainGun_Gameface.md) |
| Otimização e pendências | [Plano](PLANO_OTIMIZACAO.md) e [auditoria final](AUDITORIA_FINAL_INTEGRACAO.md) |

Os inventários de migração preservam o contexto histórico; a localização atual dos adaptadores usa `gameface/battle`, `gameface/lobby`, `flash/battle` e `flash/lobby`. Os estudos em `wn8-study/` são investigação, não métricas adicionais de produção. Os dados e scripts locais associados continuam excluídos do Git.

## Comportamentos e limites a preservar

- Configurações de cor usam `#RRGGBB`; as APIs nativas recebem números através dos conversores existentes.
- Preservar fontes, Unicode, aliases de fontes e identificadores externos necessários à compatibilidade.
- Marcadores distinguem equipa, estado vivo/destruído e modo normal/ALT. O editor inclui modelos partilhados e secção de rating.
- A preview do carrossel usa dois veículos fictícios; deve representar a geometria nativa horizontal e aplicar as mesmas regras de campos, macros e cores do renderer.
- O carrossel dispõe de um ícone para zero marcas. Um perfil que oculte o campo através da opacidade pode continuar a escondê-lo.
- O dano efetuado e o esperado têm macros de cor independentes; o separador pode ter a sua própria cor.
- Apply também persiste valores, conforme o contrato atual do painel. Os riscos de aplicação parcial, gravação de segredos e invalidação de estatísticas estão na auditoria final.
- As correções históricas do replay retiraram acessos TextField não suportados do relógio, declararam fontes nativas dos cartões e rejeitaram curvas de calibração planas/invertidas.

## Limpeza do projeto

Foram retirados 14 relatórios e planos antigos de revisão, correção e publicação, substituídos pelos guias atuais e pela auditoria final. O conteúdo original continua recuperável no histórico Git. Foram também retirados bytecodes, caches, saídas de build regeneráveis e o replay de teste local de WoT 2.4.1.0. Ao todo, 1 704 ficheiros (incluindo 1 582 bytecodes), cerca de 72,9 MiB, foram movidos para `../Driftkings_SettingsLab_cleanup_20261028/`, com manifesto para recuperação. Uma pasta vazia adicional foi retirada. A revisão automática bloqueou a eliminação em lote; foi usada esta alternativa reversível.

Os testes versionados continuam a visar módulos existentes e são usados pelo CI; foram mantidos. As dependências locais, preferências do editor, fontes, configurações, chave de assinatura e backups de perfis foram preservados. Esta limpeza não executa testes nem compila ou instala o mod.

## Verificação da beta 0.1.4-beta.2

Metadados e changelog preparados em `build_data/release.json`, com `VERSION` e downloads alinhados. Antes da compilação passaram 449 testes Core e 27 testes do painel em Python 2.7 e Python 3, 36 testes do instalador em Python 3, suites JavaScript, ESLint, traduções, defaults, catálogo UI e contratos de build. Foram atualizadas apenas as dependências simuladas de três fixtures que ainda representavam os contratos anteriores do carrossel, eventos WG e constantes das secções. O aviso de painel em construção permanece.
