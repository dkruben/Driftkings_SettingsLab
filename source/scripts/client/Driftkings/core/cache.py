# -*- coding: utf-8 -*-
"""Disk cache locations shared by all modules, independent of settings profiles."""
import logging
import os
import re
import tempfile

LOG = logging.getLogger('Driftkings.Cache')
CONFIG_ROOT = './mods/configs/Driftkings'
# Only known data files are migrated; settings, images and account secrets stay
# in their own stores. The source is retained as a migration backup.
LAYOUT = {
    'gun_marks_battle': (('MarksOnGunBattle',), r'MarksOnGunBattle_stats\.json\Z'),
    'gun_marks_hangar': (('MarksOnGunHangar',), r'progress_[0-9]+\.json\Z'),
    'stats': (('Stats/cache', 'DriftkingsStats/cache'),
              r'(?:wn8exp|xvmScales|xte|xtdb)\.json\Z'),
}


class CacheDirectories(object):
    def __init__(self, config_root=CONFIG_ROOT):
        self.config_root = os.path.abspath(config_root)
        self.root = os.path.join(self.config_root, 'cache')
        self.ready = set()

    def directory(self, module):
        legacy, pattern = LAYOUT[module]
        target = os.path.join(self.root, module)
        if module in self.ready and os.path.isdir(target):
            return target
        if not os.path.isdir(target):
            os.makedirs(target)
        success = True
        for relative in legacy:
            source = os.path.join(self.config_root, *relative.split('/'))
            if not os.path.isdir(source):
                continue
            try:
                for name in os.listdir(source):
                    if not re.match(pattern, name):
                        continue
                    old = os.path.join(source, name)
                    new = os.path.join(target, name)
                    if os.path.isfile(old) and not os.path.exists(new):
                        self._copy(old, new)
            except (IOError, OSError):
                success = False
                LOG.exception('Could not migrate cache from %s', source)
        if success:
            self.ready.add(module)
        return target

    @staticmethod
    def _copy(source, destination):
        # Publish a complete copy, including on the client's Python 2.7 (which
        # has no ctypes/os.replace). Existing destinations always take priority.
        descriptor, temporary = tempfile.mkstemp(prefix='.migration-', dir=os.path.dirname(destination))
        try:
            with os.fdopen(descriptor, 'wb') as output:
                with open(source, 'rb') as original:
                    while True:
                        block = original.read(65536)
                        if not block:
                            break
                        output.write(block)
                output.flush()
                os.fsync(output.fileno())
            if not os.path.exists(destination):
                os.rename(temporary, destination)
        finally:
            if os.path.isfile(temporary):
                os.remove(temporary)


cache = CacheDirectories()
cache_directory = cache.directory
