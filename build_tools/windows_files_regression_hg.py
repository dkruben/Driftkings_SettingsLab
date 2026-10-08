# -*- coding: utf-8 -*-
"""Normal regression contracts inside the verified embedded Python runtime."""
from mercurial import registrar
import os
import sys
cmdtable={}
command=registrar.command(cmdtable)


@command('dkwindowsregression',[('', 'compiled', False, 'compiled bytecode only'),('', 'packaged', False, 'debug package bytecode/resources')],'',norepo=True)
def run(ui,**opts):
    import hgdemandimport
    hgdemandimport.disable()
    sys.dont_write_bytecode=True
    sys.path.insert(0,os.path.abspath('build_tools'))
    from windows_files_regression_runtime import run as validate
    if opts['compiled'] and opts['packaged']: raise ValueError('Choose one mode')
    mode='packaged' if opts['packaged'] else 'compiled' if opts['compiled'] else 'source'
    validate(mode,'hg2715-'+mode)
    return 0
