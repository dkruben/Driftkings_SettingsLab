"""Read-only local reference import inventory; absence is not proof of removal."""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path('E:/Wot_Mods_/Drift_Kings_ModPack/WoT_Tools')


def main():
    roots = [TOOLS / ('wot-src-EU/sources/res/scripts/' + scope) for scope in ('client', 'common', 'shared')]
    roots += [TOOLS / 'wot-src-EU/_stubs',
             TOOLS / 'GameFace/wot.gameface-v1.2.1/python',
             TOOLS / 'ModList/mods-list-v1.7.9/python']
    files = {}
    for root in roots:
        for path in root.rglob('*.py'):
            name = path.relative_to(root).with_suffix('').as_posix().replace('/', '.')
            name = name.removesuffix('.__init__')
            files[name] = str(path)
    unresolved = []
    parsed = 0
    skipped = []
    for path in (ROOT / 'source/scripts/client').rglob('*.py'):
        try:
            tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        except SyntaxError:
            skipped.append(path.relative_to(ROOT).as_posix())
            continue
        parsed += 1
        for node in ast.walk(tree):
            names = ([node.module] if isinstance(node, ast.ImportFrom) and not node.level and node.module
                     else [a.name for a in node.names] if isinstance(node, ast.Import) else [])
            for name in names:
                if name.startswith(('gui.', 'Avatar', 'Vehicle', 'account_helpers', 'frameworks.',
                                    'items.', 'skeletons.', 'helpers.', 'openwg_', 'gui_mods')):
                    if name not in files:
                        unresolved.append({'file': path.relative_to(ROOT).as_posix(),
                                           'line': node.lineno, 'module': name})
    report = {'reference_roots': [str(r) for r in roots], 'indexed_modules': len(files),
              'parsed_project_files': parsed, 'python3_parse_skipped': skipped,
              'unresolved': unresolved,
              'note': 'Generated and native modules may be absent from extraction. Validate individually.'}
    output = ROOT / 'build/review/reference_imports.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('Indexed %d reference modules; parsed %d project files; %d unresolved import sites.' %
          (len(files), parsed, len(unresolved)))
    for item in unresolved:
        print('%s:%d %s' % (item['file'], item['line'], item['module']))


if __name__ == '__main__':
    main()
