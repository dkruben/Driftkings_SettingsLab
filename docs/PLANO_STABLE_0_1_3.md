# Convergência e release stable 0.1.3

Data: 27 outubro 2026. Pedido do autor: convergir com main e gerar uma versão stable.

## Contrato
- Versão nova: 0.1.3, canal stable, tag v0.1.3, WoT 2.4.1.1, referência EU 2.4.1.5504. Não substituir tags/releases existentes.
- Main estava 80 commits atrás de develop, sem commits exclusivos. Convergência por fast-forward, sem reescrever histórico.
- Preparação no branch main; develop será avançado ao mesmo commit para manter os branches convergentes.
- Publicar instalador, ZIP, WOTMOD, defaults, dependências, inventário e manifesto assinado com a chave já confiada. A chave privada permanece local.
- A preparação não instala no EU nem executa o instalador no cliente. Os testes automáticos/build não equivalem a aceitação visual em jogo.

## Etapas
- [x] Atualizar refs e verificar ancestralidade/ausência da tag v0.1.3.
- [x] Avançar main até develop e preparar versão/canal, notas e documentação stable.
- [x] Commit e sincronização main/develop; acompanhar CI dos dois branches.
- [x] Build release limpa, instalador, assinatura e auditoria dos artefactos.
- [x] Publicação GitHub stable, verificação remota de assets/tag/manifesto e registo final.

## Registo
- Base validada: da47c0f. Main anterior: e3ff2f1 (stable 0.1.2). Versão/canal anteriores: 0.1.3-beta.2/beta.
- Notas da stable reescritas para descrever o comportamento final, incluindo a exigência de configurações novas ao migrar do layout anterior a 0.1.3 e os limites da validação visual.

## Resultado publicado

- Após suspensão a pedido do autor, o painel foi corrigido e a versão recompilada a partir de `7d7314d34a30738b85259db673d1234e621fb71e`, com árvore limpa e main/develop convergentes. A release usa este commit imutável.
- Aviso de painel em construção nas 18 línguas, README e notas da release. A apresentação e as previews ainda necessitam de aceitação visual no Gameface.
- Validação: 446 testes core e 27 de painel, suite JavaScript, ESLint, traduções e build data aprovados. CI [develop](https://github.com/dkruben/Driftkings_SettingsLab/actions/runs/40596306414) e [main](https://github.com/dkruben/Driftkings_SettingsLab/actions/runs/40596306261) aprovados, incluindo Python 2.7/3 e testes do instalador.
- Compilados WOTMOD, ZIP e instalador; manifesto Ed25519 assinado com a chave confiada existente. Auditoria completa local e comparação dos SHA-256 dos 11 assets remotos aprovadas.
- [Stable 0.1.3](https://github.com/dkruben/Driftkings_SettingsLab/releases/tag/v0.1.3) publicada em 27 outubro 2026 às 22:42 UTC, marcada como latest, sem prerelease. A tag aponta exatamente ao commit compilado.
- Downloads públicos de release.json, release.json.sig e modpack.json iguais aos ficheiros auditados; assinatura do manifesto verificada novamente após publicação.
- A automação existente [Driftkings Discord Releases](https://github.com/dkruben/Driftkings_SettingsLab/actions/runs/40596866695) terminou com sucesso. Nenhuma mensagem manual foi enviada.
- A instalação EU não foi substituída. O checkout permanece em develop. Artefactos locais: `build/releases/stable/0.1.3`; logs e auditoria em `build/stable-0.1.3-*`.
