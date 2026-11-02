"""Generate and verify the same modpack contract used by the runtime."""
import importlib.util
from pathlib import Path

from build_tools.package_tools import sha

ROOT = Path(__file__).resolve().parents[1]


def contract(root=ROOT):
    spec = importlib.util.spec_from_file_location('_dk_modpack_inventory',
                                                  root / 'mod/res/scripts/client/driftkings/core/updater/inventory.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def create(folder, version, channel, game_version, defaults):
    model = contract()
    name = 'Driftkings-%s-WoT-%s.zip' % (version, game_version)
    path = folder / name
    import zipfile
    with zipfile.ZipFile(path) as archive:
        files = []
        for member in archive.infolist():
            target = member.filename
            kind = ('defaults' if target == 'Driftkings-defaults.zip' else
                    'instructions' if target == 'INSTALL.txt' else
                    'code' if target.endswith('/driftkings.wotmod') else 'dependency')
            files.append(dict(path=target, kind=kind, size=member.file_size, sha256=model.sha(archive.read(member))))
    document = dict(schema=1, packageId='driftkings.modpack', version=version, channel=channel,
                    gameVersion=game_version,
                    distribution=dict(file=name, size=path.stat().st_size, sha256=sha(path)), files=files,
                    defaults=[dict(path=target, kind='config', size=len(data), sha256=model.sha(data)) for target,
                              data in sorted(defaults.items())])
    inventory = model.Inventory(document, version, channel, game_version)
    inventory.verify_archive(path)
    return document


def verify(folder, manifest, document):
    inventory = contract().Inventory(document, manifest['version'], manifest['channel'], manifest['gameVersion'])
    inventory.verify_archive(folder / inventory.distribution['file'])
    code = next(item for item in inventory.files if item['kind'] == 'code')
    if code['size'] != manifest['size'] or code['sha256'] != manifest['sha256']:
        raise ValueError('Legacy release and modpack code differ')
    if manifest.get('schema') == 2 and manifest.get('modpack') != document:
        raise ValueError('Release and standalone modpack inventory differ')
    return inventory
