"""Validate Gameface declarations; OpenWG owns the global bootstrap and resource map."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def collect_resources(root=ROOT):
    resources, seen = {}, set()
    for path in sorted((root/'build_data/components').glob('*.json')):
        manifest = json.loads(path.read_text(encoding='utf-8-sig'))
        if not manifest.get('enabled'):
            continue
        for relative in manifest.get('files', {}).values():
            if not relative.startswith('res/mods/configs/res_map/') or relative in seen:
                continue
            seen.add(relative)
            for item in json.loads((root/relative).read_text(encoding='utf-8-sig')):
                key = item['itemID']
                if key in resources:
                    raise ValueError('Duplicate UI resource: ' + key)
                if not key.startswith('mods/Driftkings/') or item['type'] != 'Layout':
                    raise ValueError('Unexpected UI resource: ' + key)
                url = item['path']
                prefix = 'coui://gui/gameface/mods/Driftkings/'
                if not url.startswith(prefix):
                    raise ValueError('Unexpected layout URL: ' + url)
                layout = (root/'res'/url[len('coui://'):]).resolve()
                if not layout.is_relative_to((root/'res').resolve()) or not layout.is_file():
                    raise ValueError('Missing or unsafe layout: ' + url)
                resources[key] = item
    return resources


def build():
    resources = collect_resources()
    output = ROOT/'build/gameface/ui'
    output.mkdir(parents=True, exist_ok=True)
    (output/'report.json').write_text(json.dumps({
        'resource_owner': 'OpenWG Gameface 1.1.6 (ModList dependency; client 2.4.0.1)',
        'resources': resources}, indent=2), encoding='utf-8')
    print('Gameface declarations: %d layouts; no global resource overrides' % len(resources))


if __name__ == '__main__':
    build()
