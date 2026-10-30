"""Locate build hosts without changing their installations."""
import os
from pathlib import Path
import shutil

from build_tools.validate_build_data import read_json, require

# Machine-specific locations: build_data/toolchain.local.json, DK_<KEY> or --<key>; never the build contract.
KEYS = ('python27', 'hg', 'flex_home', 'mxmlc_jar', 'playerglobal', 'java', 'csc', 'rabcdasm_home',
        'game_root', 'reference_root')


def discover(root, overrides):
    local = root / 'build_data/toolchain.local.json'
    settings = read_json(local) if local.exists() else {}
    require(not set(settings) - set(KEYS), 'Unknown local toolchain field')

    def configured(key):
        return overrides.get(key) or os.environ.get('DK_' + key.upper()) or settings.get(key)

    def choose(key, candidates, directory=False):
        explicit = configured(key)
        candidates = [explicit] if explicit else candidates
        for candidate in candidates:
            if not candidate:
                continue
            path = Path(candidate).expanduser()
            if not path.is_absolute():
                found = shutil.which(str(path)) if not directory else None
                path = Path(found) if found else root / path
            valid = path.is_dir() if directory else path.is_file()
            if valid:
                return str(path.resolve())
        require(not explicit, 'Configured tool is missing: %s=%s' % (key, explicit))
        return None

    result = {}
    result['python27'] = choose('python27', [shutil.which(n) for n in ('python2.7', 'python2', 'python27')] +
                                ['C:/Python27/python.exe', 'F:/Python27/python.exe'])
    result['hg'] = choose('hg', [Path(os.environ.get('LOCALAPPDATA', '')) / 'Atlassian/SourceTree/hg_local/hg.exe'])
    if configured('hg') and not configured('python27'):
        result['python27'] = None
    result['flex_home'] = choose('flex_home', [root.parent / 'Programas/Flex', root.parents[1] / 'Programas/Flex'], True)
    sdk = Path(result['flex_home']) if result['flex_home'] else None
    result['mxmlc_jar'] = choose('mxmlc_jar', [sdk / 'lib/mxmlc.jar'] if sdk else [])
    adobe = Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'Adobe'
    result['playerglobal'] = choose('playerglobal', sorted(adobe.glob('Adobe Animate */Common/Configuration/ActionScript 3.0/FP32.0/playerglobal.swc'), reverse=True))
    java = Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'Java'
    result['java'] = choose('java', sorted(java.glob('jre1.8*/bin/java.exe'), reverse=True) + [shutil.which('java')])
    result['csc'] = choose('csc', [Path(os.environ.get('WINDIR', 'C:/windows')) / 'Microsoft.NET/Framework/v4.0.30319/csc.exe'])
    result['rabcdasm_home'] = choose('rabcdasm_home', [root.parent / 'WoT_Tools/xvm-master/src_build/bin/windows_i686/rabcdasm'], directory=True)
    result['game_root'] = choose('game_root', [], directory=True)
    result['reference_root'] = choose('reference_root', [], directory=True)
    return result


def require_game_root(tools):
    require(tools['game_root'], 'Game installation missing; set game_root in build_data/toolchain.local.json, '
            'DK_GAME_ROOT or --game-root')
    return tools['game_root']


def require_tools(tools):
    require(tools['python27'] or tools['hg'], 'Python 2.7 host missing; set --python27 or --hg')
    require_game_root(tools)
    for name in ('flex_home', 'mxmlc_jar', 'playerglobal', 'java', 'csc', 'rabcdasm_home', 'reference_root'):
        require(tools[name], 'Missing build dependency: %s; configure toolchain.local.json or --%s' % (name, name.replace('_', '-')))
    require((Path(tools['flex_home']) / 'frameworks/libs/framework.swc').is_file(), 'Missing Flex framework.swc')
