# -*- coding: utf-8 -*-
"""Resolve legacy vehicle image tags through the client's resource catalogue."""
import re
from xml.sax.saxutils import escape

_VEHICLE_IMAGE = re.compile(
    r"<img\b[^>]*\bsrc\s*=\s*(['\"])img://(?P<path>gui/maps/icons/vehicle/"
    r"(?P<contour>contour/)?(?P<name>[^/'\"]+)\.png)\1[^>]*>", re.IGNORECASE)


def resolve_vehicle_images(text, get_icon, get_contour):
    def replace(match):
        name = match.group('name').replace('-', ':', 1)
        path = (get_contour if match.group('contour') else get_icon)(name)
        if not path:
            # A missing illustration must not submit a broken image to Scaleform.
            return ''
        if path.startswith('img://'):
            path = path[6:]
        if path.startswith('../'):
            path = 'gui/' + path[3:]
        tag = match.group(0)
        offset = match.start('path') - match.start()
        end = match.end('path') - match.start()
        return tag[:offset] + escape(path, {'"': '&quot;', "'": '&apos;'}) + tag[end:]
    return _VEHICLE_IMAGE.sub(replace, text)
