# -*- coding: utf-8 -*-
"""SourceTree Mercurial extension: compile lab Python only; never deploy."""
from mercurial import registrar
import os
import sys
cmdtable = {}
command = registrar.command(cmdtable)

@command('dkbuild', [], '', norepo=True)
def dkbuild(ui, **opts):
    sys.path.insert(0, os.path.abspath('build_tools'))
    from compiler import compile_dir
    return 0 if compile_dir('source/scripts/client/', d_dir='scripts/client/',
                            o_dir='build/scripts/client/', force=True) else 1
