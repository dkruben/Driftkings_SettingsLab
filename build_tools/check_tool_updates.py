#!/usr/bin/env python3
"""Read-only upstream checks for the reference sources; Python 3 standard library."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

PROJECT = Path(__file__).resolve().parents[1]
DEFAULT_TOOLS = PROJECT.parent.parent / 'WoT_Tools'
WOT_REPO = 'https://github.com/izeberg/wot-src'
MODS = (
    ('ModList', 'mods-list-', 'wot-public-mods/mods-list'),
    ('GameFace', 'wot.gameface-', 'openwg/wot.gameface'),
)


def version_key(value):
    """Compare numeric stable versions, never prereleases, lexically or as floats."""
    match = re.fullmatch(r'v?(\d+(?:\.\d+){1,3})', value.strip())
    if not match:
        return None
    parts = tuple(int(part) for part in match.group(1).split('.'))
    return parts + (0,) * (4 - len(parts))


def compare_versions(local, remote):
    left, right = version_key(local or ''), version_key(remote or '')
    if right is None:
        raise ValueError('Versao publicada nao reconhecida: ' + str(remote))
    if left is None:
        return 'LOCAL DESCONHECIDO'
    if left < right:
        return 'ATUALIZACAO DISPONIVEL'
    if left > right:
        return 'LOCAL MAIS RECENTE'
    return 'MESMA VERSAO'


def request_text(url, timeout):
    request = urllib.request.Request(url, headers={
        'User-Agent': 'Driftkings-Reference-UpdateCheck/1.0',
        'Accept': 'application/json, text/plain, */*',
    })
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read().decode('utf-8-sig')
    except urllib.error.HTTPError as error:
        hint = ' (limite da API ou acesso recusado; tenta mais tarde)' if error.code in (403, 429) else ''
        raise RuntimeError('HTTP {}{}: {}'.format(error.code, hint, url)) from error


def request_json(url, timeout):
    return json.loads(request_text(url, timeout))


def client_version(text):
    value = ET.fromstring(text).findtext('version', '')
    match = re.search(r'v\.(\d+(?:\.\d+)+)', value)
    if not match:
        raise ValueError('version.xml nao contem a versao do cliente')
    return match.group(1)


def local_head(root):
    # Do not accidentally use the HEAD of a parent project for an extracted ZIP.
    if not (root / '.git').exists():
        return None
    result = subprocess.run(['git', '-C', str(root), 'rev-parse', 'HEAD'],
                            capture_output=True, text=True, timeout=10, check=True)
    return result.stdout.strip()


def check_wot(tools_root, timeout):
    root = tools_root / 'wot-src-EU'
    result = {'name': 'wot-src-EU', 'repository': WOT_REPO, 'path': str(root), 'notes': []}
    marker = root / '.version_name'
    result['local_version'] = marker.read_text(encoding='utf-8-sig').strip() if marker.is_file() else None
    xml = root / 'sources' / 'version.xml'
    result['local_client'] = client_version(xml.read_text(encoding='utf-8-sig')) if xml.is_file() else None
    result['local_commit'] = local_head(root)
    branch = request_json('https://api.github.com/repos/izeberg/wot-src/branches/EU', timeout)
    commit = branch['commit']['sha']
    result['remote_commit'] = commit
    result['published_at'] = branch['commit']['commit']['committer']['date']
    raw = 'https://raw.githubusercontent.com/izeberg/wot-src/{}/'.format(commit)
    result['remote_version'] = request_text(raw + '.version_name', timeout).strip()
    result['remote_client'] = client_version(request_text(raw + 'sources/version.xml', timeout))
    result['url'] = WOT_REPO + '/commit/' + commit
    result['status'] = compare_versions(result['local_version'], result['remote_version'])
    if result['local_commit'] and result['status'] == 'MESMA VERSAO':
        result['status'] = ('MESMA REVISAO' if result['local_commit'] == commit else 'REVISAO DIFERENTE')
    elif not result['local_commit']:
        result['notes'].append('Arquivo sem Git: a revisao exata nao foi confirmada.')
    if not root.exists():
        result['status'] = 'LOCAL AUSENTE'
    elif not marker.is_file() or not xml.is_file():
        result['notes'].append('Faltam metadados locais; a extracao pode estar incompleta.')
        if result['status'] in ('MESMA VERSAO', 'MESMA REVISAO'):
            result['status'] = 'LOCAL INCOMPLETO'
    if result['local_client'] and result['local_client'] != result['remote_client']:
        result['notes'].append('O version.xml local difere do publicado; verificar a extracao.')
        if result['status'] in ('MESMA VERSAO', 'MESMA REVISAO'):
            result['status'] = 'METADADOS DIFERENTES'
    result['notes'].append('Verificacao de metadados; nao valida todos os ficheiros extraidos.')
    return result


def latest_release(releases):
    stable = [item for item in releases if not item.get('upcoming_release')
              and version_key(item.get('tag_name', '')) is not None]
    if not stable:
        raise ValueError('Nao foi encontrada uma release estavel publicada')
    return max(stable, key=lambda item: version_key(item['tag_name']))


def check_mod(tools_root, timeout, name, prefix, project):
    root = tools_root / name
    result = {'name': name, 'repository': 'https://gitlab.com/' + project,
              'path': str(root), 'notes': []}
    local = []
    if root.is_dir():
        for folder in root.iterdir():
            if folder.is_dir() and folder.name.startswith(prefix):
                version = folder.name[len(prefix):]
                if version_key(version) is not None:
                    local.append((version, folder))
    local.sort(key=lambda item: version_key(item[0]))
    result['local_versions'] = [version for version, _ in local]
    result['local_version'] = local[-1][0] if local else None
    base = 'https://gitlab.com/api/v4/projects/' + urllib.parse.quote(project, safe='')
    # Follow pagination: stable versions can be older than many prereleases.
    releases = []
    for page in range(1, 11):
        batch = request_json(base + '/releases?per_page=100&page={}'.format(page), timeout)
        if not isinstance(batch, list):
            raise ValueError('Resposta inesperada da API GitLab')
        releases.extend(batch)
        if len(batch) < 100:
            break
    else:
        raise RuntimeError('Demasiadas paginas de releases; verificacao inconclusiva')
    release = latest_release(releases)
    result['remote_version'] = release['tag_name']
    result['published_at'] = release.get('released_at')
    result['url'] = result['repository'] + '/-/releases/' + urllib.parse.quote(release['tag_name'], safe='')
    result['status'] = compare_versions(result['local_version'], result['remote_version']) if local else 'LOCAL AUSENTE'
    result['notes'].append('Versao local inferida pelo nome da pasta; nao e uma verificacao de integridade.')
    if local:
        folder = local[-1][1]
        if not (folder / 'README.md').is_file() or not (folder / 'python').is_dir():
            result['notes'].append('Faltam README.md ou python; a extracao pode estar incompleta.')
            if result['status'] == 'MESMA VERSAO':
                result['status'] = 'LOCAL INCOMPLETO'
        else:
            readme = (folder / 'README.md').read_text(encoding='utf-8-sig')
            required = re.search(r'Requires World of Tanks (\d+(?:\.\d+)+) or later', readme, re.I)
            if required:
                result['minimum_client'] = required.group(1)
                result['notes'].append('O README local exige WoT {} ou posterior.'.format(required.group(1)))
    return result


def safely_check(name, callback):
    try:
        return callback()
    except Exception as error:
        return {'name': name, 'status': 'ERRO', 'error': str(error), 'notes': []}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Procurar atualizacoes de wot-src-EU, ModList e GameFace (sem instalar).')
    parser.add_argument('--tools-root', type=Path, default=DEFAULT_TOOLS)
    parser.add_argument('--timeout', type=float, default=15, help='Timeout por pedido HTTP, em segundos (1-60).')
    parser.add_argument('--json', action='store_true', help='Mostrar apenas o relatorio JSON.')
    parser.add_argument('--report', type=Path, help='Guardar uma copia JSON no caminho indicado.')
    args = parser.parse_args(argv)
    if not 1 <= args.timeout <= 60:
        parser.error('--timeout deve estar entre 1 e 60')
    if not args.tools_root.is_dir():
        parser.error('Pasta WoT_Tools inexistente: ' + str(args.tools_root))
    jobs = [('wot-src-EU', lambda: check_wot(args.tools_root, args.timeout))]
    jobs.extend((name, lambda n=name, p=prefix, r=project: check_mod(args.tools_root, args.timeout, n, p, r))
                for name, prefix, project in MODS)
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(safely_check, name, callback) for name, callback in jobs]
        results = [future.result() for future in futures]
    report = {'checked_at': datetime.now(timezone.utc).isoformat(),
              'tools_root': str(args.tools_root.resolve()), 'results': results}
    encoded = json.dumps(report, ensure_ascii=True, indent=2)
    if args.report:
        output = args.report.resolve()
        # Reference trees are read-only, even when a report path is supplied.
        if output.is_relative_to(args.tools_root.resolve()) or output.suffix.lower() != '.json':
            parser.error('--report deve ser um JSON fora de WoT_Tools')
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(encoded + '\n', encoding='utf-8')
    if args.json:
        print(encoded)
    else:
        print('Referencias: ' + str(args.tools_root))
        for result in results:
            print('\n{}: {}'.format(result['name'], result['status']))
            if result['status'] == 'ERRO':
                print('  ' + result['error'])
                continue
            print('  Local: {} | Publicada: {}'.format(result.get('local_version') or '-', result['remote_version']))
            if result.get('remote_client'):
                print('  Cliente local: {} | Publicado: {}'.format(result.get('local_client') or '-', result['remote_client']))
                print('  Commit EU: {} ({})'.format(result['remote_commit'][:12], result['published_at']))
            print('  ' + result['url'])
            for note in result['notes']:
                print('  ' + note)
        print('\nNenhum download, extracao ou instalacao efetuado.')
        if args.report:
            print('Relatorio: ' + str(args.report.resolve()))
    return 1 if any(result['status'] == 'ERRO' for result in results) else 0


if __name__ == '__main__':
    raise SystemExit(main())
