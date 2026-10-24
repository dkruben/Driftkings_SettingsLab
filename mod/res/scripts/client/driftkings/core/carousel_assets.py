# -*- coding: utf-8 -*-
"""Carousel PNGs from the resource tree mounted by the client's .wotmod loader."""
import base64
import os
import re

from driftkings.logger import get_logger

RESOURCE_ROOT = 'gui/maps/driftkings/carroucel/'
ICON_PATH = re.compile(r'gui/maps/driftkings/carroucel/[#a-z0-9_-]+\.png')
SAVED_ICON_PATH = re.compile(r'(?:(?:coui|img)://)?(?:gui/maps|mods)/driftkings/carroucel/([^\s\'"<>/]+\.png)', re.IGNORECASE)
MAX_IMAGE_SIZE = 2 * 1024 * 1024


def normalize_icon_paths(text):
    """Normalize owned paths once on load/render, preserving macro names."""
    def replace(match):
        filename = ''.join(part if part.startswith('{{') else part.lower()
                           for part in re.split(r'(\{\{.*?\}\})', match.group(1)))
        return RESOURCE_ROOT + filename
    return SAVED_ICON_PATH.sub(replace, text)


def normalize_icon_config(value):
    if isinstance(value, dict):
        return dict((key, normalize_icon_config(item)) for key, item in value.items())
    if isinstance(value, list):
        return [normalize_icon_config(item) for item in value]
    if isinstance(value, (str, type(u''))):
        return normalize_icon_paths(value)
    return value


class CarouselImages(object):
    def __init__(self, root=None):
        # Explicit resource root for offline tools; the game always uses ResMgr.
        self.root = os.path.realpath(root) if root is not None else None
        self.cache = {}
        self.missing = set()

    def resolve(self, path):
        if not ICON_PATH.match(path) or ICON_PATH.match(path).group(0) != path:
            return ''
        resource = path
        if resource in self.cache:
            return self.cache[resource]
        try:
            try:
                import ResMgr
            except ImportError:
                data = None
                if self.root is not None:
                    with open(os.path.join(self.root, resource), 'rb') as stream:
                        data = stream.read(MAX_IMAGE_SIZE + 1)
            else:
                section = ResMgr.openSection(resource)
                data = section.asBinary if section is not None else None
        except (IOError, OSError, ValueError):
            data = None
        if data and len(data) <= MAX_IMAGE_SIZE and data.startswith(b'\x89PNG\r\n\x1a\n'):
            result = 'data:image/png;base64,' + base64.b64encode(data).decode('ascii')
            if len(self.cache) >= 32:
                self.cache.clear()
            self.cache[resource] = result
            self.missing.discard(path)
            return result
        if path not in self.missing:
            self.missing.add(path)
            get_logger('Driftkings.CarouselStats').warning('Packaged carousel icon not found: %s', resource)
        return ''

    def collect(self, vehicles):
        paths = set()
        for profiles in vehicles.values():
            for profile in profiles.values():
                for field in profile.get('extraFields', ()):
                    if field.get('showIcons', True):
                        for key in ('src', 'format'):
                            paths.update(ICON_PATH.findall(field.get(key, '')))
        return dict((path, self.resolve(path)) for path in sorted(paths))
