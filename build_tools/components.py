"""Read the single component manifest using canonical runtime section names."""
import json
from pathlib import Path
import re


FIELDS = {'kind', 'enabled', 'entrypoint', 'config_files', 'assets'}
ASSET_FIELDS = {'source', 'target', 'generator'}
SOURCE_PREFIX = 'mod/'


def normalize_asset(asset):
    """Expand a compact asset: a string names a mod/ source packaged at the same path without that prefix."""
    if isinstance(asset, str):
        asset = {'source': asset}
    if not isinstance(asset, dict) or 'source' not in asset or not set(asset) <= ASSET_FIELDS:
        raise ValueError('Invalid asset fields: %r' % (asset,))
    source, target = asset['source'], asset.get('target')
    if target is None:
        if not isinstance(source, str) or not source.startswith(SOURCE_PREFIX):
            raise ValueError('Asset outside %s needs an explicit target: %r' % (SOURCE_PREFIX, source))
        target = source[len(SOURCE_PREFIX):]
    return {'source': source, 'target': target, 'generator': asset.get('generator')}


def normalize_component(item):
    """Apply manifest defaults: an enabled feature without configuration files or assets."""
    if not isinstance(item, dict) or not set(item) <= FIELDS:
        raise ValueError('Invalid component fields')
    kind = item.get('kind', 'feature')
    if kind == 'feature' and 'entrypoint' not in item:
        raise ValueError('Feature component requires an entrypoint')
    assets = item.get('assets', [])
    if not isinstance(assets, list):
        raise ValueError('Expected an assets list')
    return dict(kind=kind, enabled=item.get('enabled', True), entrypoint=item.get('entrypoint'),
                config_files=item.get('config_files', []), assets=[normalize_asset(asset) for asset in assets])


def read_components(root, source):
    root = Path(root).resolve()
    if not isinstance(source, str) or Path(source).is_absolute() or '\\' in source or ':' in source:
        raise ValueError('Expected a relative component manifest path')
    path = root / source
    if any(part in ('', '.', '..') for part in source.split('/')) or not path.resolve().is_relative_to(root):
        raise ValueError('Component manifest path escapes repository')

    def unique_pairs(items):
        result = {}
        for name, value in items:
            if name in result:
                raise ValueError('Duplicate component manifest key: ' + name)
            result[name] = value
        return result

    document = json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=unique_pairs)
    if (not isinstance(document, dict) or set(document) != {'schema_version', 'components'} or
            type(document['schema_version']) is not int or document['schema_version'] != 2 or
            not isinstance(document['components'], dict) or not document['components']):
        raise ValueError('Invalid unified component manifest schema')
    manifests = []
    for name, item in sorted(document['components'].items()):
        if re.fullmatch(r'[a-z][a-z0-9]*(?:_[a-z0-9]+)*', name) is None:
            raise ValueError('Component must use its canonical name: ' + name)
        try:
            item = normalize_component(item)
        except ValueError as error:
            raise ValueError('%s: %s' % (name, error))
        if item['kind'] == 'feature':
            entrypoint = item['entrypoint']
            if not isinstance(entrypoint, str) or entrypoint.split('.')[-1] != name:
                raise ValueError('Component name differs from its runtime module: ' + name)
        manifests.append(dict(item, schema_version=1, id=name))
    return manifests
