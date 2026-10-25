"""Minimal reproducible ABC patch of the pinned EU marker movie."""
import re
import struct
import zlib

HELPER = 'QName(PackageNamespace(""), "DriftkingsVehicleMarkersFlash")'
PROTECTED = 'ProtectedNamespace("net.wg.gui.battle.views.vehicleMarkers:VehicleMarker")'


def patch_method(text, name, instructions, minimum_stack, before=False):
    # Trait boundaries avoid accidentally modifying calls in neighbouring methods.
    pattern = r'(?m)^  trait method [^\n]*, "' + re.escape(name) + r'"\)[^\n]*\n.*?^  end ; trait'
    found = list(re.finditer(pattern, text, re.S))
    if len(found) != 1:
        raise ValueError('Expected exactly one native method: ' + name)
    match = found[0]
    block = match.group(0)
    block = re.sub(r'maxstack (\d+)', lambda m: 'maxstack ' + str(max(int(m[1]), minimum_stack)), block, count=1)
    if before:
        # Clear our children before the native disposal path clears its fields.
        anchor = '      pushscope\n'
        if block.count(anchor) != 1: raise ValueError('Unexpected method scope: ' + name)
        block = block.replace(anchor, anchor + '\n' + instructions, 1)
    else:
        if '      returnvoid' not in block: raise ValueError('No void return: ' + name)
        block = block.replace('      returnvoid', instructions + '      returnvoid')
    return text[:match.start()] + block + text[match.end():]


def patch_marker(text):
    render = ('      getlex              ' + HELPER + '\n'
              '      getlocal0\n'
              '      getlocal0\n'
              '      getproperty         QName(' + PROTECTED + ', "model")\n'
              '      getlocal0\n'
              '      getproperty         QName(' + PROTECTED + ', "vehicleDestroyed")\n'
              '      getlocal0\n'
              '      getproperty         QName(' + PROTECTED + ', "isStickyAndOutOfScreen")\n'
              '      callpropvoid        QName(PackageNamespace(""), "render"), 4\n\n')
    for name in ('draw', 'setHealth', 'updateHealth', 'updateMarkerSettings'):
        text = patch_method(text, name, render, 5)
    damage = ('      getlex              ' + HELPER + '\n'
              '      getlocal0\n      getlocal0\n'
              '      getproperty         QName(' + PROTECTED + ', "model")\n'
              '      getlocal1\n      getlocal2\n'
              '      callpropvoid        QName(PackageNamespace(""), "damage"), 4\n\n')
    text = patch_method(text, 'updateHealth', damage, 5, before=True)
    reset = ('      getlex              ' + HELPER + '\n      getlocal0\n'
             '      callpropvoid        QName(PackageNamespace(""), "clearTransient"), 1\n\n')
    text = patch_method(text, 'setHealth', reset, 2, before=True)
    guard = ('      getlex              ' + HELPER + '\n'
             '      callproperty        QName(PackageNamespace(""), "damageEnabled"), 0\n'
             '      iffalse             VMTEST_NATIVE_DAMAGE\n      returnvoid\n'
             'VMTEST_NATIVE_DAMAGE:\n')
    text = patch_method(text, 'showHitLabelAnim', guard, 1, before=True)
    clear = ('      getlex              ' + HELPER + '\n      getlocal0\n'
             '      callpropvoid        QName(PackageNamespace(""), "clear"), 1\n\n')
    return patch_method(text, 'onBeforeDispose', clear, 2, before=True)


def patch_manager(text):
    code = ('      getlex              ' + HELPER + '\n      getlocal1\n'
            '      callpropvoid        QName(PackageNamespace(""), "configure"), 1\n\n')
    text = patch_method(text, 'as_setMarkerSettings', code, 2)
    blind = ('      getlex              ' + HELPER + '\n      getlocal1\n'
             '      callpropvoid        QName(PackageNamespace(""), "setColorBlind"), 1\n\n')
    # Update the flag before the native UPDATE_COLORS event triggers marker redraws.
    return patch_method(text, 'as_setColorBlind', blind, 2, before=True)


def swf_parts(data):
    if data[:3] == b'CWS': data = b'FWS' + data[3:8] + zlib.decompress(data[8:])
    if data[:3] != b'FWS' or len(data) != struct.unpack('<I', data[4:8])[0]:
        raise ValueError('Unsupported or damaged SWF')
    rect_size = (5 + 4 * (data[8] >> 3) + 7) // 8
    offset = 8 + rect_size + 4
    prefix = data[:offset]
    tags = []
    while offset < len(data):
        start = offset
        header = struct.unpack('<H', data[offset:offset+2])[0]
        offset += 2
        length = header & 63
        if length == 63:
            length = struct.unpack('<I', data[offset:offset+4])[0]
            offset += 4
        offset += length
        if offset > len(data): raise ValueError('Truncated SWF tag')
        tags.append((header >> 6, data[start:offset]))
    return prefix, tags


def inject_helper(native, helper):
    prefix, tags = swf_parts(native)
    _, helper_tags = swf_parts(helper)
    abc = [tag for kind, tag in helper_tags if kind == 82]
    if len(abc) != 1: raise ValueError('Expected one helper ABC')
    # Flex calls its ABC frame1 too. Scaleform must not see duplicate ABC names.
    helper_tag = abc[0]
    header = struct.unpack('<H', helper_tag[:2])[0]
    payload_offset = 6 if header & 63 == 63 else 2
    payload = helper_tag[payload_offset:]
    name_end = payload.index(b'\x00', 4)
    payload = payload[:4] + b'driftkings_vehicle_markers\x00' + payload[name_end+1:]
    unique_helper = struct.pack('<H', (82 << 6) | 63) + struct.pack('<I', len(payload)) + payload
    output = []
    inserted = False
    for kind, tag in tags:
        output.append(tag)
        if kind == 82 and not inserted:
            output.append(unique_helper)
            inserted = True
    if not inserted: raise ValueError('No native ABC')
    body = prefix[8:] + b''.join(output)
    return b'FWS' + prefix[3:4] + struct.pack('<I', len(body)+8) + body
