# Beta 0.1.4-beta.1

Pedido: publicar beta, fazer commit e push apenas em develop. A stable 0.1.3 e main permanecem intactos.

## Etapas
- [x] Rever alterações locais e reservar versão 0.1.4-beta.1, posterior à stable 0.1.3.
- [x] Registar correções no release.json, atualizar VERSION e downloads; manter aviso de painel em construção.
- [x] Validar fontes, testes, traduções e contratos de build.
- [x] Commit/push em develop e acompanhar CI.
- [x] Compilar release beta limpa, instalador e assinatura; verificar os 11 artefactos.
- [x] Criar rascunho, verificar hashes remotos e publicar como prerelease sem alterar latest stable.

## Âmbito
Marcadores: referências partilhadas editáveis e controlos dentro da coluna. Carrossel: dois veículos fictícios com cores calculadas pela API real e propriedades de texto/ícone/sombra coerentes com o renderer. A aceitação visual em Gameface continua pendente. A instalação EU não será substituída.

Validação local: 446 testes core e 27 testes do painel, suite JavaScript (35 páginas/1104 controlos), ESLint, zero nomes indefinidos, traduções, defaults e build data aprovados.

## Resultado

- Commit compilado e tag: `18042f6b892ecb12a5dc65a3a108397da078dc42`. CI [40599148010](https://github.com/dkruben/Driftkings_SettingsLab/actions/runs/40599148010) aprovado.
- [Beta 0.1.4-beta.1](https://github.com/dkruben/Driftkings_SettingsLab/releases/tag/v0.1.4-beta.1) publicada como prerelease em 27 outubro 2026 às 23:03 UTC. A stable 0.1.3 continua a ser latest e main não foi alterado.
- WOTMOD, ZIP, instalador, defaults, dependências e manifesto: 11 assets auditados localmente e por comparação dos SHA-256 remotos. Manifesto público e assinatura Ed25519 verificados depois da publicação.
- Uma alteração concorrente local acrescentou `docs/` ao .gitignore durante a preparação. Foi preservada, sem entrar no commit. A publicação usou um worktree limpo e isolado do commit compilado, respeitando a proteção contra publicação de fontes alteradas.
- Checkout principal em develop. Instalação EU e stable intactas. Artefactos em `build/releases/beta/0.1.4-beta.1`; logs/auditoria em `build/beta-0.1.4-*`.
