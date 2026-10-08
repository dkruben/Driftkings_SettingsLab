# -*- coding: utf-8 -*-
"""Run only diagnostic serialization tests inside Hg Python 2.7.15."""
from mercurial import registrar
import os
import sys
import unittest

cmdtable = {}
command = registrar.command(cmdtable)


@command('dkwindowsunicode', [], '', norepo=True)
def run(ui, **opts):
    import hgdemandimport
    hgdemandimport.disable()
    sys.dont_write_bytecode = True
    assert sys.version_info[:3] == (2, 7, 15)
    sys.path.insert(0, os.path.abspath('build_tools/tests'))
    import test_windows_files_diagnostic_json as tests
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    assert not any(name.startswith('Driftkings') for name in sys.modules), 'No backend allowed'
    return 0 if result.wasSuccessful() else 1
