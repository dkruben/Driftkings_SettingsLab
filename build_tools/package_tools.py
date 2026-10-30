"""Build and inspect deterministic ZIP entries; never install into the game."""
import hashlib
import json
from pathlib import Path
import struct
import xml.etree.ElementTree as ET
import zipfile
import zlib

from build_tools.validate_build_data import relative_path, require

MAGIC = b'\x03\xf3\x0d\x0a'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))


def zip_entries(path, entries, compression=zipfile.ZIP_STORED):
    """entries maps archive names to bytes. Reject case-insensitive collisions."""
    require(len({name.casefold() for name in entries}) == len(entries), 'Duplicate ZIP paths')
    with zipfile.ZipFile(path, 'w', compression=compression) as archive:
        for name, data in sorted(entries.items()):
            relative_path(name)
            info = zipfile.ZipInfo(name, (2000, 1, 1, 0, 0, 0))
            info.compress_type = compression
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)


def metadata(release, version):
    root = ET.Element('root')
    for key, value in (('id', release['package_id']), ('version', version),
                       ('name', release['title']), ('description', release['title']), ('author', release['author'])):
        ET.SubElement(root, key).text = value
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def validate_swf(raw):
    require(len(raw) > 8 and raw[:3] in (b'FWS', b'CWS'), 'Invalid compiled SWF')
    expanded = raw if raw[:3] == b'FWS' else raw[:8] + zlib.decompress(raw[8:])
    require(struct.unpack('<I', raw[4:8])[0] == len(expanded), 'SWF length mismatch')


def normalize_swf_compile_date(raw, epoch):
    """Replace the ProductInfo compile date written by mxmlc with SOURCE_DATE_EPOCH (milliseconds)."""
    validate_swf(raw)
    expanded = bytearray(raw if raw[:3] == b'FWS' else raw[:8] + zlib.decompress(raw[8:]))
    position = 8 + (5 + (expanded[8] >> 3) * 4 + 7) // 8 + 4
    changed = False
    while position < len(expanded):
        header = struct.unpack('<H', bytes(expanded[position:position + 2]))[0]
        code, length = header >> 6, header & 0x3f
        position += 2
        if length == 0x3f:
            length = struct.unpack('<I', bytes(expanded[position:position + 4]))[0]
            position += 4
        if code == 41 and length == 26:
            expanded[position + 18:position + 26] = struct.pack('<Q', epoch * 1000)
            changed = True
        position += length
    if not changed:
        return raw
    if raw[:3] == b'FWS':
        return bytes(expanded)
    return bytes(expanded[:8]) + zlib.compress(bytes(expanded[8:]), 9)


def verify_package(path, expected, version, package_id):
    require(Path(path).stat().st_size <= 64 * 1024 * 1024, 'Package exceeds updater size limit')
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require(set(names) == set(expected) and len(names) == len(expected), 'WOTMOD inventory mismatch')
        require(len(names) <= 5000 and sum(i.file_size for i in archive.infolist()) <= 128 * 1024 * 1024,
                'Package exceeds installer limits')
        require(len({name.casefold() for name in names}) == len(names), 'Duplicate WOTMOD entries')
        entrypoints = [n for n in names if n.startswith('res/scripts/client/gui/mods/mod_')]
        require(entrypoints == ['res/scripts/client/gui/mods/mod_driftkings.pyc'], 'Unexpected mod entrypoints')
        for item in archive.infolist():
            relative_path(item.filename)
            require(item.compress_type == zipfile.ZIP_STORED, 'WOTMOD compression must be stored')
            data = archive.read(item)
            require(data == expected[item.filename], 'WOTMOD content mismatch: ' + item.filename)
            require(not item.filename.endswith('.py') and '/configs/' not in item.filename, 'Source/config in WOTMOD')
            if item.filename.endswith('.pyc'):
                require(data[:4] == MAGIC and len(data) > 8, 'Wrong bytecode: ' + item.filename)
            if item.filename.endswith('.swf'):
                validate_swf(data)
        meta = ET.fromstring(archive.read('meta.xml'))
        require(meta.findtext('id') == package_id and meta.findtext('version') == version, 'Wrong package identity/version')
        for prefix, executable in (('updater', 'Driftkings.UpdateInstaller.exe'), ('windows-files', 'Driftkings.WindowsFiles.exe')):
            base = 'res/gui/driftkings/' + prefix + '/'
            binary = archive.read(base + executable)
            helper = json.loads(archive.read(base + 'helper.json').decode('utf-8'))
            require(binary.startswith(b'MZ') and helper == dict(schema=1, size=len(binary), sha256=hashlib.sha256(binary).hexdigest()),
                    'Invalid native helper metadata: ' + prefix)
