# -*- coding: utf-8 -*-
"""Local image previews; no writes and no remote downloads."""
import base64
import os

# Events declared by the bundled SixthSense Wwise work unit.
SIXTH_SENSE_EVENTS = tuple('SixthSense_%02d' % number for number in range(1, 11))


def resource_image(path):
    if not isinstance(path, (str, type(u''))):
        return ''
    path = path.replace('\\', '/').strip()
    for prefix in ('img://', 'coui://'):
        if path.startswith(prefix):
            path = path[len(prefix):]
    if not path.lower().endswith(('.png', '.jpg', '.jpeg')) or any(part in ('', '..', '.') for part in path.split('/')):
        return ''
    if path.startswith('gui/') and ':' not in path:
        return 'coui://' + path
    return ''


class ImagePreviews(object):
    def __init__(self, root=None):
        self.root = os.path.realpath(root or os.getcwd())
        self.cache = {}

    def resolve(self, path):
        resource = resource_image(path)
        if resource:
            return resource
        if not isinstance(path, (str, type(u''))):
            return ''
        path = path.replace('\\', '/')
        if not path.startswith('mods/configs/') or not path.lower().endswith(('.png', '.jpg', '.jpeg')):
            return ''
        absolute = os.path.realpath(os.path.join(self.root, path))
        allowed = os.path.realpath(os.path.join(self.root, 'mods/configs')) + os.sep
        if not os.path.normcase(absolute).startswith(os.path.normcase(allowed)):
            return ''
        try:
            stat = os.stat(absolute)
            if stat.st_size > 2 * 1024 * 1024:
                return ''
            key = (absolute, stat.st_mtime, stat.st_size)
            if key not in self.cache:
                with open(absolute, 'rb') as stream:
                    data = stream.read(2 * 1024 * 1024 + 1)
                mime = 'image/png' if data.startswith(b'\x89PNG\r\n\x1a\n') else 'image/jpeg' if data.startswith(b'\xff\xd8\xff') else None
                if mime is None or len(data) > 2 * 1024 * 1024:
                    return ''
                if len(self.cache) >= 8:
                    self.cache.clear()
                self.cache[key] = 'data:%s;base64,%s' % (mime, base64.b64encode(data).decode('ascii'))
            return self.cache[key]
        except (IOError, OSError):
            return ''

    def clear(self):
        self.cache.clear()
