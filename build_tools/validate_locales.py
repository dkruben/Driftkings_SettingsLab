"""Check bundled catalog coverage and formatting against the English source."""
import argparse
import runpy
from collections import Counter
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FORMATTING = re.compile(
    r'<[^>]*>|\{\{.*?\}\}|\{[^{}]*\}|%\([^)]+\)[#0 +\-]*[0-9.]*(?:[sdrifgeouxX])|'
    r'%(?:[0-9.]+)?[sdf]|%%|&(?:\w+|#\d+);')
PATHS = re.compile(r'[A-Za-z0-9_./-]+\.(?:json|xml|png|jpg|jpeg|wotmod|pyc|py|bnk|log)\b')


# Share the engine-free runtime parser; importing the game package is unnecessary.
parse_catalog = runpy.run_path(str(ROOT / 'mod/res/scripts/client/driftkings/core/locale_catalog.py'))['parse_catalog']


def catalog(path):
    result = parse_catalog(path.read_bytes())
    if not result['TEXT'] or not result['PANEL']:
        raise ValueError('Missing component or panel catalog: ' + str(path))
    return result


def leaves(value, prefix=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from leaves(child, prefix + (key,))
    else:
        yield prefix, value


def validate_catalogs(root=ROOT):
    folder = root / 'mod/res/mods/driftkings/text'
    manifest = json.loads((root / 'build_data/locales.json').read_text(encoding='utf-8'))
    reference = dict(leaves(catalog(folder / 'en.yml')))
    errors = []
    for code in manifest['locales']:
        actual = dict(leaves(catalog(folder / (code + '.yml'))))
        for key in sorted(set(reference) - set(actual)):
            errors.append('%s: missing %s' % (code, '.'.join(key)))
        for key in sorted(set(actual) - set(reference)):
            errors.append('%s: unexpected %s' % (code, '.'.join(key)))
        for key in set(reference) & set(actual):
            source, translated = reference[key], actual[key]
            if not isinstance(translated, type(source)):
                errors.append('%s: wrong value type at %s' % (code, '.'.join(key)))
            elif isinstance(source, str):
                if source.strip() and not translated.strip():
                    errors.append('%s: empty translation at %s' % (code, '.'.join(key)))
                if Counter(FORMATTING.findall(source)) != Counter(FORMATTING.findall(translated)):
                    errors.append('%s: changed formatting at %s' % (code, '.'.join(key)))
                if re.fullmatch(r'#[0-9A-Fa-f]{6,8}', source) and translated != source:
                    errors.append('%s: changed color at %s' % (code, '.'.join(key)))
                for path in set(PATHS.findall(source)):
                    if translated.count(path) != source.count(path):
                        errors.append('%s: changed resource path at %s: %s' % (code, '.'.join(key), path))
    if errors:
        raise ValueError('Locale validation failed:\n' + '\n'.join(errors[:60]))
    english = catalog(folder / 'en.yml')
    return {'locales': len(manifest['locales']),
            'componentKeys': len(dict(leaves(english['TEXT']))),
            'panelKeys': len(english['PANEL']), 'untranslated': len(english_prose(root)), 'status': 'passed'}


# Names kept in English on purpose (sound and preset names).
ENGLISH_NAMES = frozenset(('Super Mario', 'WoT-Life'))


def english_prose(root=ROOT):
    """Catalog values still identical to an English phrase of two or more words."""
    folder = root / 'mod/res/mods/driftkings/text'
    manifest = json.loads((root / 'build_data/locales.json').read_text(encoding='utf-8'))
    reference = dict(leaves(catalog(folder / 'en.yml')))
    found = []
    for code in manifest['locales']:
        if code == 'en':
            continue
        actual = dict(leaves(catalog(folder / (code + '.yml'))))
        for key, source in reference.items():
            if not isinstance(source, str) or source in ENGLISH_NAMES or actual.get(key) != source:
                continue
            if len(re.findall(r'[A-Za-z]{3,}', FORMATTING.sub(' ', source))) >= 2:
                found.append((code, '.'.join(key)))
    return found


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(validate_catalogs(args.root), indent=2))
