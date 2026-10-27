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
- [ ] Commit e sincronização main/develop; acompanhar CI dos dois branches.
- [ ] Build release limpa, instalador, assinatura e auditoria dos artefactos.
- [ ] Publicação GitHub stable, verificação remota de assets/tag/manifesto e registo final.

## Registo
- Base validada: da47c0f. Main anterior: e3ff2f1 (stable 0.1.2). Versão/canal anteriores: 0.1.3-beta.2/beta.
- Notas da stable reescritas para descrever o comportamento final, incluindo a exigência de configurações novas ao migrar do layout anterior a 0.1.3 e os limites da validação visual.
