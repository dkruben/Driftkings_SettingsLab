# -*- coding: utf-8 -*-
"""Normal test fixture resources; no compiler, network or game deployment."""
import os


def initialize():
    from Driftkings.core.updater import windows_files
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    mapping = {windows_files.HELPER_RESOURCE:'Driftkings.WindowsFiles.exe', windows_files.INFO_RESOURCE:'helper.json'}
    def reader(name):
        with open(os.path.join(root,'build/windows-files',mapping[name]),'rb') as stream: return stream.read()
    cache = os.path.join(root,'build/diagnostics/windows-files-v2/normal-suite-cache')
    windows_files.initialize(reader,root,cache)


def close():
    from Driftkings.core.updater import windows_files
    windows_files.close()
