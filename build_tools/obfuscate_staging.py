"""Phase 10 SAFE allowlist, isolated tool and staging; never deploy or publish."""
import ast
import base64
import configparser
import json
from pathlib import Path, PurePosixPath
import shutil
import time

from pjorion_poc import ROOT, TOOL_FILES, file_version, sha
from pjorion_probe import probe

SAFE = frozenset(('Driftkings/core/marks_calculator.pyc',
                  'Driftkings/core/updater/versioning.pyc',
                  'Driftkings/core/updater/manifest.pyc'))
INTROSPECTION = frozenset(('__name__', '__module__', 'getattr', 'setattr', 'hasattr',
                         '__import__', 'importlib', 'globals', 'locals', 'inspect'))


def load_profile(path):
    config = json.loads(Path(path).read_text(encoding='utf-8'))
    if set(config) != {'enabled', 'profile', 'include', 'exclude'} or config['enabled'] is not True or config['profile'] != 'safe':
        raise ValueError('Release requires enabled SAFE profile; use --no-obfuscation for diagnostics')
    includes, excludes = config['include'], config['exclude']
    if not isinstance(includes, list) or not includes or len(includes) != len(set(includes)) or not isinstance(excludes, list):
        raise ValueError('Invalid explicit allowlist')
    for name in includes + excludes:
        if not isinstance(name, str) or '\\' in name or PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts or '*' in name:
            raise ValueError('Profile paths must be explicit relative paths')
    if not set(includes).issubset(SAFE):
        raise ValueError('Module has not been audited and tested for SAFE protection')
    if any(name == item or (item.endswith('/') and name.startswith(item)) for name in includes for item in excludes):
        raise ValueError('Included module is explicitly excluded')
    return config


def source_audit(name):
    source = ROOT / 'source/scripts/client' / Path(name).with_suffix('.py')
    tree = ast.parse(source.read_bytes())
    hits = sorted({node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and node.id in INTROSPECTION} |
                  {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute) and node.attr in INTROSPECTION})
    if hits: raise ValueError('Unreviewed introspection in %s: %s' % (name, hits))
    return {'sourceSha256': sha(source), 'introspectionHits': hits}


def protect(compiled, sandbox, tool, profile):
    compiled, sandbox, tool = Path(compiled).resolve(), Path(sandbox).resolve(), Path(tool).resolve()
    sandbox.relative_to((ROOT / 'build/obfuscation').resolve())
    compiled.relative_to((ROOT / 'build').resolve())
    if sandbox == compiled or sandbox in compiled.parents or compiled in sandbox.parents:
        raise ValueError('Compiled input and protected staging must be separate')
    sandbox.mkdir(parents=True, exist_ok=True)
    report = dict(status='running', profile='safe', processed=[], excluded=[], failed=[], timings={}, phase=10)
    started = time.monotonic()
    staging = sandbox / 'staging'
    if staging.exists(): shutil.rmtree(staging)
    originals = {}
    try:
        config = load_profile(profile)
        originals = {name: sha(tool / name) for name in TOOL_FILES}
        report.update(pjOrionVersion=file_version(tool / 'PjOrion.exe'), originalToolHashes=originals,
                      profileSha256=sha(profile), audit={name: source_audit(name) for name in config['include']})
        copied = sandbox / 'tool'
        copied.mkdir(exist_ok=True)
        for name in TOOL_FILES: shutil.copyfile(tool / name, copied / name)
        shutil.copytree(tool / 'DLLs', copied / 'DLLs', dirs_exist_ok=True)
        ini = configparser.ConfigParser()
        ini.optionxform = str
        ini.read(copied / 'PjOrion.ini')
        options = {'GENERAL': {'CheckWebUpdate': '0', 'AutoConnect': '1'},
                   'PATHS': {'Python': base64.b64encode(str(copied / 'python27.dll').encode()).decode(),
                             'SelectedDir': base64.b64encode(str(staging).encode()).decode()},
                   'FILEASSOCIATIONS': {'RegisterApplication': '0', 'PY': '0', 'PYC': '0'},
                   'CONTEXTMENU': {'Integrate': '0'}, 'WOTTRANSMISSION': {'SearchWOT': '0', 'WOT': ''},
                   'OBFUSCATE': {'AllNamesIsPublic': '1', 'DetailedAnalysis': '1'},
                   'PROTECT': {'ExecOnlyInWOT': '0', 'LockAttributesReview': '0', 'UseWOTInjector': '0', 'CreateBackupFile': '0'}}
        for section, settings in options.items():
            for key, value in settings.items(): ini.set(section, key, value)
        with (copied / 'PjOrion.ini').open('w', encoding='utf-8') as stream: ini.write(stream)
        report['configurationSha256'] = sha(copied / 'PjOrion.ini')
        shutil.copytree(compiled, staging)
        before = {path.relative_to(compiled).as_posix(): sha(path) for path in compiled.rglob('*') if path.is_file()}
        report['excluded'] = sorted(set(before) - set(config['include']))
        report['inputHashes'] = before
        for index, name in enumerate(config['include']):
            target = staging / name
            if not target.is_file() or target.is_symlink() or target.read_bytes()[:4] != b'\x03\xf3\x0d\x0a':
                raise ValueError('Missing Python 2.7 input: ' + name)
            action = probe('module-%s' % index, ['--protect-bytecode-file=' + str(target), '/exit'], target, timeout=45, sandbox=sandbox)
            report['timings'][name] = action['seconds']
            if action['timeout'] or action['exitCode'] != 0 or not target.is_file() or sha(target) == before[name] or target.read_bytes()[:4] != b'\x03\xf3\x0d\x0a':
                raise ValueError('Protection failed/unchanged: ' + name)
            report['processed'].append(dict(module=name, inputSha256=before[name], outputSha256=sha(target), seconds=action['seconds']))
        after = {path.relative_to(staging).as_posix(): sha(path) for path in staging.rglob('*') if path.is_file()}
        if set(before) != set(after) or {name for name in before if before[name] != after[name]} != set(config['include']):
            raise ValueError('Only allowlisted Python bytecode may change')
        if any(sha(compiled / name) != value for name, value in before.items()):
            raise ValueError('Compiled input changed')
        if any(sha(ROOT / 'source/scripts/client' / Path(name).with_suffix('.py')) != audit['sourceSha256'] for name, audit in report['audit'].items()):
            raise ValueError('Source changed during protection')
        report['status'] = 'protected; post-protection tests required'
        return staging, report
    except Exception as error:
        report['status'] = 'failed'
        report['failed'].append(str(error))
        if staging.exists(): shutil.rmtree(staging)
        raise
    finally:
        report['originalToolUnchanged'] = bool(originals) and all(sha(tool / name) == value for name, value in originals.items())
        if originals and not report['originalToolUnchanged']:
            report['status'] = 'failed'
            report['failed'].append('Original PJOrion installation changed')
        report['seconds'] = time.monotonic() - started
        (sandbox.parent / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        if originals and not report['originalToolUnchanged']:
            if staging.exists(): shutil.rmtree(staging)
            raise ValueError('Original PJOrion installation changed')
