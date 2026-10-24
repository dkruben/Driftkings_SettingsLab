# -*- coding: utf-8 -*-
"""Disk cache locations shared by all modules, independent of settings profiles."""
import os

CONFIG_ROOT = './mods/configs/driftkings'
MODULES = ('gun_marks_battle', 'gun_marks_hangar', 'stats')


class CacheDirectories(object):
    def __init__(self, config_root=CONFIG_ROOT):
        self.root = os.path.join(os.path.abspath(config_root), 'cache')

    def directory(self, module):
        if module not in MODULES:
            raise ValueError('Unknown cache module: ' + str(module))
        target = os.path.join(self.root, module)
        if not os.path.isdir(target):
            os.makedirs(target)
        return target


cache = CacheDirectories()
cache_directory = cache.directory
