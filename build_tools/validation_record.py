"""Functional validation records: docs/releases/<beta-version>-validation.md.

A record states what a person checked on a published beta. It is plain data: it is parsed with fixed
rules, never executed, and this tool never fills a result in. Which checks exist and which of them
block a promotion is decided here, so removing or relabelling a row in a record cannot weaken the gate.

  python build_tools/validation_record.py new <beta-version> --commit <sha> --package-sha256 <sha256>
  python build_tools/validation_record.py check <beta-version>
"""
import argparse
from datetime import date
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools.compiler import version_contract
from build_tools.validate_build_data import read_json, require

RECORD_FOLDER = 'docs/releases'
MARKER = '<!-- dk-validation-record: 1 -->'
MAX_RECORD = 256 * 1024
REGIONS = ('EU', 'NA', 'ASIA')
PASS, FAIL, NOT_TESTED, NOT_APPLICABLE = 'PASS', 'FAIL', 'NOT TESTED', 'NOT APPLICABLE'
RESULTS = (PASS, FAIL, NOT_TESTED, NOT_APPLICABLE)
VALIDATED, NOT_VALIDATED = 'VALIDATED', 'NOT VALIDATED'
APPROVED, PENDING, REJECTED = 'APPROVED', 'PENDING', 'REJECTED'
SEVERITIES = ('BLOCKER', 'MAJOR', 'MINOR')
ISSUE_STATES = ('OPEN', 'ACCEPTED', 'FIXED')

SECTIONS = {
    'Identificação': ('Campo', 'Valor'),
    'Regiões': ('Região', 'Decisão', 'Build do cliente', 'Data', 'Validador', 'Ambiente'),
    'Testes automáticos': ('ID', 'Verificação', 'Resultado', 'Evidência'),
    'Testes em jogo': ('ID', 'Bloqueante', 'Verificação') + REGIONS + ('Notas',),
    'Problemas conhecidos': ('ID', 'Gravidade', 'Estado', 'Verificação', 'Descrição'),
    'Aprovação final': ('Campo', 'Valor'),
}
IDENTITY_FIELDS = ('Versão', 'Estável alvo', 'Commit', 'Tag', 'Versão do WoT', 'SHA-256 do pacote')
APPROVAL_FIELDS = ('Decisão', 'Aprovado por', 'Data', 'Commit aprovado', 'Versão aprovada')

AUTOMATED = (
    ('auto.ci', 'GitHub Actions verde no commit da beta (python-package.yml)'),
    ('auto.runtime', 'python -B tests/run_python.py --suite runtime'),
    ('auto.build', 'python -B tests/run_python.py --suite build'),
    ('auto.frontend', 'npm --prefix build_tools/javascript test'),
    ('auto.artifacts', 'python -B tests/run_python.py --suite artifacts --wotmod <pacote da beta>'),
    ('auto.signature', 'release.json.sig e SHA256SUMS.txt públicos verificados'),
)
# (id, blocks a promotion, description). Rows added to a record never replace these.
IN_GAME = (
    ('install.clean', True, 'Instalação limpa com o instalador, sem mods anteriores'),
    ('install.manual', False, 'Instalação manual com o ZIP e Driftkings-defaults.zip'),
    ('install.upgrade', True, 'Instalação sobre a stable anterior preserva perfis e configurações'),
    ('updater.check', True, 'O atualizador encontra a versão no canal escolhido'),
    ('updater.apply', True, 'O atualizador descarrega, verifica e aplica a versão após reiniciar'),
    ('startup.client', True, 'Arranque até ao hangar sem exceções Driftkings no game.log'),
    ('startup.components', True, 'Todos os componentes ativos carregam; nenhum fica desativado por erro'),
    ('settings.panel', True, 'Painel de configurações abre, aplica e guarda alterações'),
    ('settings.profiles', True, 'Perfis: criar, mudar, importar e manter as configurações'),
    ('ui.gameface', True, 'Vistas Gameface em batalha e no hangar sem erros de layout'),
    ('ui.flash', True, 'Vistas Flash/Scaleform em batalha carregam e atualizam'),
    ('battle.players_panel', True, 'Painéis de jogadores: painel lateral e TAB'),
    ('battle.statistics', True, 'Estatísticas de jogadores aparecem e aplicam-se sem paragens'),
    ('battle.minimap', True, 'Minimapa: círculos, nomes e tamanho do mapa'),
    ('battle.markers', True, 'Marcadores de veículos'),
    ('battle.sixth_sense', False, 'Alerta do Sexto Sentido'),
    ('battle.high_caliber', False, 'Progresso do High Caliber'),
    ('battle.performance', False, 'Battle Performance e textos de eficiência'),
    ('battle.overlays', False, 'Informação do alvo, limites de canhão, contagem de mira e penetração'),
    ('battle.camera', False, 'Câmara de sniper, zoom em terceira pessoa e sons'),
    ('lobby.carousel', False, 'Carrossel de veículos'),
    ('lobby.hangar', False, 'Preferências do hangar, marcas, tripulação e reparações'),
    ('lobby.account_manager', False, 'Gestor de contas'),
    ('flow.consecutive', True, 'Várias batalhas seguidas sem erros nem estado residual'),
    ('flow.replays', True, 'Replays abrem e terminam sem erros'),
    ('mode.random', True, 'Modo: batalhas aleatórias'),
    ('mode.frontline', False, 'Modo: Linha da Frente'),
    ('mode.ranked', False, 'Modo: batalhas classificadas'),
    ('mode.other', False, 'Outros modos disponíveis no cliente'),
    ('performance.battle', False, 'Desempenho em batalha comparado com a stable anterior'),
    ('uninstall.reinstall', True, 'Desinstalação e reinstalação preservam as configurações do utilizador'),
)


def record_path(version, root=ROOT):
    return root / RECORD_FOLDER / (version + '-validation.md')


def table(header, rows):
    lines = ['| ' + ' | '.join(header) + ' |', '|' + ' --- |' * len(header)]
    return lines + ['| ' + ' | '.join(row) + ' |' for row in rows]


def render(version='<versão-beta>', target='<versão-stable>', commit='<commit-completo>', game='<versão-do-wot>',
           package='<sha256-do-driftkings.wotmod>'):
    """A blank record: every result starts NOT TESTED and the decision starts PENDING."""
    identity = (('Versão', version), ('Estável alvo', target), ('Commit', commit), ('Tag', 'v' + version),
                ('Versão do WoT', game), ('SHA-256 do pacote', package))
    decision = (('Decisão', PENDING), ('Aprovado por', '<nome>'), ('Data', '<AAAA-MM-DD>'),
                ('Commit aprovado', '<commit-completo>'), ('Versão aprovada', '<versão-beta>'))
    lines = ['# Registo de validação de ' + version, '', MARKER, '',
             'Preenchido à mão por quem testou. Valores: `PASS`, `FAIL`, `NOT TESTED`, `NOT APPLICABLE`. '
             'Uma região nunca vale como prova de outra. Regras em [docs/releases/README.md](README.md).', '']
    lines += ['## Identificação', ''] + table(SECTIONS['Identificação'], identity)
    lines += ['', '## Regiões', '']
    lines += table(SECTIONS['Regiões'], [(region, NOT_VALIDATED, '-', '-', '-', '-') for region in REGIONS])
    lines += ['', '## Testes automáticos', '']
    lines += table(SECTIONS['Testes automáticos'], [(name, text, NOT_TESTED, '-') for name, text in AUTOMATED])
    lines += ['', '## Testes em jogo', '']
    lines += table(SECTIONS['Testes em jogo'], [(name, 'YES' if blocking else 'NO', text) +
                                                (NOT_TESTED,) * len(REGIONS) + ('-',)
                                                for name, blocking, text in IN_GAME])
    lines += ['', '## Problemas conhecidos', ''] + table(SECTIONS['Problemas conhecidos'], ())
    lines += ['', '## Aprovação final', ''] + table(SECTIONS['Aprovação final'], decision)
    return '\n'.join(lines) + '\n'


def split_row(line):
    return [cell.strip() for cell in re.split(r'(?<!\\)\|', line.strip()[1:-1])]


def parse(text):
    """Tables of a record by section; layout errors raise ValueError instead of being guessed around."""
    require(isinstance(text, str) and len(text.encode('utf-8')) <= MAX_RECORD, 'Validation record is too large')
    require(MARKER in text, 'Not a validation record (missing format marker)')
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    found, current = {}, None
    for line in text.splitlines():
        heading = re.match(r'##\s+(.+?)\s*$', line)
        if heading:
            current = heading.group(1)
            require(current not in found, 'Duplicate record section: ' + current)
            found[current] = []
        elif current is not None and line.strip().startswith('|'):
            found[current].append(split_row(line))
    tables = {}
    for name, header in SECTIONS.items():
        require(name in found, 'Missing record section: ' + name)
        rows = found[name]
        require(len(rows) >= 2 and tuple(rows[0]) == header, 'Unexpected table header in section: ' + name)
        require(all(len(row) == len(header) for row in rows), 'Malformed table row in section: ' + name)
        tables[name] = rows[2:]
    return tables


def fields(rows, expected, section):
    values = {}
    for name, value in rows:
        require(name not in values, 'Duplicate field in %s: %s' % (section, name))
        values[name] = value
    require(set(values) == set(expected), 'Unexpected fields in section: ' + section)
    return values


def valid_date(value):
    try:
        return date.fromisoformat(value) if re.match(r'\A\d{4}-\d{2}-\d{2}\Z', value) else None
    except ValueError:
        return None


def is_placeholder(value):
    return not value or value == '-' or '<' in value or '>' in value


def evaluate(text, version, target=None, commit=None):
    """Return the approved summary of a record, or raise ValueError listing every reason it does not pass."""
    tables = parse(text)
    problems = []
    identity = fields(tables['Identificação'], IDENTITY_FIELDS, 'Identificação')
    approval = fields(tables['Aprovação final'], APPROVAL_FIELDS, 'Aprovação final')
    recorded = identity['Commit']
    if identity['Versão'] != version or identity['Tag'] != 'v' + version:
        problems.append('Record identifies %s, not %s' % (identity['Versão'], version))
    if target is not None and identity['Estável alvo'] != target:
        problems.append('Record targets stable %s, not %s' % (identity['Estável alvo'], target))
    if not re.match(r'\A[0-9a-f]{40}\Z', recorded):
        problems.append('Record commit must be a full lowercase SHA-1')
    elif commit is not None and recorded != commit:
        problems.append('Record commit %s differs from %s' % (recorded[:12], commit[:12]))
    if not re.match(r'\A[0-9a-f]{64}\Z', identity['SHA-256 do pacote']):
        problems.append('Record package digest must be a lowercase SHA-256')
    if is_placeholder(identity['Versão do WoT']):
        problems.append('Record has no World of Tanks version')

    regions = {}
    for row in tables['Regiões']:
        require(row[0] not in regions and row[0] in REGIONS, 'Unknown or duplicate region: ' + row[0])
        regions[row[0]] = row
    require(set(regions) == set(REGIONS), 'Every region must be listed, even when not validated')
    for row in regions.values():
        require(row[1] in (VALIDATED, NOT_VALIDATED), 'Invalid region decision: ' + row[1])
    validated = [name for name in REGIONS if regions[name][1] == VALIDATED]
    if not validated:
        problems.append('No region is marked VALIDATED')
    for name in validated:
        if not valid_date(regions[name][3]):
            problems.append('Region %s has no valid test date' % name)
        if any(is_placeholder(regions[name][index]) for index in (2, 4, 5)):
            problems.append('Region %s needs client build, validator and environment' % name)

    automated = {}
    for name, _, result, evidence in tables['Testes automáticos']:
        require(name not in automated, 'Duplicate automatic check: ' + name)
        require(result in RESULTS, 'Invalid result for %s: %s' % (name, result))
        automated[name] = result
        if result == FAIL:
            problems.append('Automatic check failed: ' + name)
        elif result == PASS and is_placeholder(evidence):
            problems.append('Automatic check %s has no evidence' % name)
    for name, _ in AUTOMATED:
        if name not in automated:
            problems.append('Missing automatic check: ' + name)
        elif automated[name] in (NOT_TESTED, NOT_APPLICABLE):
            problems.append('Automatic check was not run: ' + name)

    catalogue = {name: blocking for name, blocking, _ in IN_GAME}
    seen, failed = {}, []
    for row in tables['Testes em jogo']:
        name, blocking, notes = row[0], row[1], row[-1]
        require(name not in seen, 'Duplicate in-game check: ' + name)
        seen[name] = row
        require(blocking in ('YES', 'NO'), 'Invalid blocking flag for ' + name)
        if name in catalogue and (blocking == 'YES') != catalogue[name]:
            problems.append('Blocking flag of %s differs from the catalogue' % name)
        results = dict(zip(REGIONS, row[3:3 + len(REGIONS)]))
        for region, result in results.items():
            require(result in RESULTS, 'Invalid result for %s/%s: %s' % (name, region, result))
            if result == FAIL:
                failed.append(name)
                if blocking == 'YES':
                    problems.append('Blocking check failed: %s (%s)' % (name, region))
        if blocking == 'YES' or catalogue.get(name):
            for region in validated:
                if results[region] == NOT_TESTED:
                    problems.append('Blocking check not tested in validated region %s: %s' % (region, name))
                elif results[region] == NOT_APPLICABLE and is_placeholder(notes):
                    problems.append('Blocking check %s is NOT APPLICABLE in %s without a reason' % (name, region))
    for name in catalogue:
        if name not in seen:
            problems.append('Missing in-game check: ' + name)

    issues = {}
    for name, severity, state, check, description in tables['Problemas conhecidos']:
        require(name not in issues, 'Duplicate known issue: ' + name)
        require(severity in SEVERITIES, 'Invalid issue severity: ' + severity)
        require(state in ISSUE_STATES, 'Invalid issue state: ' + state)
        issues[name] = (severity, state, check)
        if is_placeholder(description):
            problems.append('Known issue %s has no description' % name)
        if severity == 'BLOCKER' and state != 'FIXED':
            problems.append('Blocking issue is not fixed: ' + name)
    listed = {check for _, _, check in issues.values()}
    for name in failed:
        if name not in listed:
            problems.append('Failed check has no known issue: ' + name)

    decision = approval['Decisão']
    if decision not in (APPROVED, PENDING, REJECTED):
        problems.append('Invalid decision: ' + decision)
    elif decision != APPROVED:
        problems.append('Record decision is ' + decision)
    if is_placeholder(approval['Aprovado por']):
        problems.append('Record has no approver')
    approved_on = valid_date(approval['Data'])
    if approved_on is None:
        problems.append('Record has no valid approval date')
    else:
        for name in validated:
            tested = valid_date(regions[name][3])
            if tested is not None and tested > approved_on:
                problems.append('Approval predates the tests in ' + name)
    if approval['Commit aprovado'] != recorded:
        problems.append('Approved commit differs from the recorded commit')
    if approval['Versão aprovada'] != identity['Versão']:
        problems.append('Approved version differs from the recorded version')
    if problems:
        raise ValueError('; '.join(problems))
    return dict(version=version, target=identity['Estável alvo'], commit=recorded, gameVersion=identity['Versão do WoT'],
                packageSha256=identity['SHA-256 do pacote'], approvedBy=approval['Aprovado por'],
                approvedOn=approval['Data'], validatedRegions=validated,
                notValidatedRegions=[name for name in REGIONS if name not in validated],
                knownIssues=sorted(name for name, issue in issues.items() if issue[1] != 'FIXED'))


def stable_target(version):
    """The stable version a beta or release candidate promotes to."""
    parsed = version_contract().Version(version)
    require(parsed.prerelease and parsed.prerelease[0] in ('beta', 'rc') and not parsed.metadata,
            'Only beta or rc versions can be promoted: ' + version)
    return '%d.%d.%d' % parsed.release


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    create = commands.add_parser('new', help='Write a blank record; never overwrites one')
    create.add_argument('version')
    create.add_argument('--commit', required=True, help='Full commit of the published beta')
    create.add_argument('--package-sha256', required=True, help='SHA-256 of its driftkings.wotmod')
    check = commands.add_parser('check', help='Evaluate a record offline')
    check.add_argument('version')
    args = parser.parse_args()
    try:
        path = record_path(args.version)
        target = stable_target(args.version)
        if args.command == 'check':
            for key, value in evaluate(path.read_bytes().decode('utf-8'), args.version, target).items():
                print('%s: %s' % (key, value))
            return
        require(not path.exists(), 'Refusing to overwrite ' + str(path))
        game = read_json(ROOT / 'build_data/build_config.json')['game']['version']
        text = render(args.version, target, args.commit, game, args.package_sha256)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode('utf-8'))
        print('Wrote %s; results stay NOT TESTED until a person records them.' % path)
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, 'Validation record: %s\n' % error)


if __name__ == '__main__':
    main()
