"""Validate packaged media using only the standard library; branding is optional."""
import ast
import binascii
from pathlib import Path
import struct
import xml.etree.ElementTree as ET
import zlib

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def inventory_limit(root):
    tree = ast.parse((root / 'mod/res/scripts/client/driftkings/core/updater/inventory.py').read_text(encoding='utf-8'))
    assignment = next(node for node in tree.body if isinstance(node, ast.Assign) and
                      any(isinstance(target, ast.Name) and target.id == 'MAX_FILE' for target in node.targets))
    # The inventory constant is an integer multiplication expression.
    def number(node):
        if isinstance(node, ast.Constant) and type(node.value) is int:
            return node.value
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
            return number(node.left) * number(node.right)
        raise ValueError('Unsupported inventory MAX_FILE expression')
    return number(assignment.value)


def validate_png(path, maximum):
    """Check chunks, CRCs, dimensions and bounded scanline data (including Adam7)."""
    require(0 < path.stat().st_size <= maximum, 'PNG exceeds inventory limit: ' + str(path))
    raw = path.read_bytes()
    require(0 < len(raw) <= maximum and raw[:8] == b'\x89PNG\r\n\x1a\n', 'Invalid PNG: ' + str(path))
    offset, chunks, image_data = 8, [], []
    width = height = depth = color = interlace = None
    while offset < len(raw):
        require(offset + 12 <= len(raw), 'Truncated PNG: ' + str(path))
        size = struct.unpack('>I', raw[offset:offset + 4])[0]
        name = raw[offset + 4:offset + 8]
        require(name.isalpha() and (name[0] & 0x20 or name in (b'IHDR', b'PLTE', b'IDAT', b'IEND')),
                'Invalid PNG chunk type: ' + str(path))
        end = offset + 12 + size
        require(end <= len(raw), 'Truncated PNG chunk: ' + str(path))
        data = raw[offset + 8:end - 4]
        crc = struct.unpack('>I', raw[end - 4:end])[0]
        require(binascii.crc32(name + data) & 0xffffffff == crc, 'PNG CRC mismatch: ' + str(path))
        if name == b'IHDR':
            require(not chunks and size == 13, 'Invalid PNG header: ' + str(path))
            width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', data)
            bits = {0: (1, 2, 4, 8, 16), 2: (8, 16), 3: (1, 2, 4, 8), 4: (8, 16), 6: (8, 16)}
            require(0 < width <= 8192 and 0 < height <= 8192 and color in bits and depth in bits[color] and
                    compression == filtering == 0 and interlace in (0, 1), 'Invalid PNG format: ' + str(path))
        elif name == b'IDAT':
            require(not chunks or chunks[-1] in (b'IHDR', b'IDAT') or b'IDAT' not in chunks,
                    'Non-contiguous PNG image data: ' + str(path))
            image_data.append(data)
        elif name == b'IEND':
            require(size == 0 and end == len(raw), 'Invalid PNG end: ' + str(path))
        chunks.append(name)
        offset = end
    require(chunks and chunks[0] == b'IHDR' and chunks[-1] == b'IEND' and image_data and
            (color != 3 or b'PLTE' in chunks), 'Incomplete PNG: ' + str(path))
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color]
    passes = [(0, 0, 1, 1)] if not interlace else [(0, 0, 8, 8), (4, 0, 8, 8), (0, 4, 4, 8),
                                                               (2, 0, 4, 4), (0, 2, 2, 4), (1, 0, 2, 2), (0, 1, 1, 2)]
    rows = []
    for x, y, dx, dy in passes:
        w, h = max(0, (width - x + dx - 1) // dx), max(0, (height - y + dy - 1) // dy)
        if w and h:
            row_size = (w * channels * depth + 7) // 8 + 1
            require(row_size * h <= maximum, 'PNG pixels exceed inventory limit: ' + str(path))
            rows.extend([row_size] * h)
    expected = sum(rows)
    require(expected <= maximum, 'PNG pixels exceed inventory limit: ' + str(path))
    decoder = zlib.decompressobj()
    try:
        decoded = decoder.decompress(b''.join(image_data), expected + 1)
    except zlib.error as error:
        raise ValueError('Invalid PNG image data: ' + str(path)) from error
    require(len(decoded) == expected and decoder.eof and not decoder.unused_data,
            'Invalid PNG scanlines: ' + str(path))
    offset = 0
    for size in rows:
        require(decoded[offset] <= 4, 'Invalid PNG filter: ' + str(path))
        offset += size
    return width, height


def validate(root=ROOT, assets=()):
    root = Path(root)
    maximum = inventory_limit(root)
    sources = {item['source'] for item in assets}
    require(not any(name.startswith('res/sound_bank_wwise/') for name in sources),
            'Wwise source project must not be packaged')
    audio = root / 'mod/res/audioww'
    banks = sorted(audio.glob('*.bnk'))
    for bank in banks:
        xml = bank.with_suffix('.xml')
        require(xml.is_file(), 'Missing bank XML: ' + str(bank))
        for path in (bank, xml):
            require(0 < path.stat().st_size <= maximum, 'Media exceeds inventory limit: ' + str(path))
            require(path.relative_to(root).as_posix() in sources, 'Media not declared in components.json: ' + str(path))
        try:
            document = ET.fromstring(xml.read_bytes())
        except ET.ParseError as error:
            raise ValueError('Invalid bank XML: ' + str(xml)) from error
        names = [node.text for node in document.findall('./loadBanks/bank/name')]
        require(bank.name in names, 'Bank missing from loadBanks: ' + str(xml))
    for xml in audio.glob('*.xml'):
        require(xml.with_suffix('.bnk').is_file(), 'Orphan bank XML: ' + str(xml))
    icons = sorted((root / 'mod/res/gui/maps/icons/sixthsense').glob('*.png'))
    for path in icons:
        require(path.relative_to(root).as_posix() in sources, 'Sixth Sense icon not packaged: ' + str(path))
        validate_png(path, maximum)
    for path in (root / 'installer/setup/assets/previews').glob('*.png'):
        validate_png(path, maximum)
    branding = root / 'installer/setup/assets/branding'
    missing = [name for name in ('setup-icon.ico', 'wizard-large.bmp', 'wizard-small.bmp')
               if not (branding / name).is_file()
                   and not (name.endswith('.bmp') and (branding / name.replace('.bmp', '.png')).is_file())]
    return dict(banks=len(banks), icons=len(icons),
                warnings=['Optional installer branding missing: ' + name for name in missing])
