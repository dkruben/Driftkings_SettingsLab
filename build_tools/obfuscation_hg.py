"""Run protected-bytecode contracts in the actual Python 2.7 build host."""
from mercurial import registrar
import os
import sys
cmdtable = {}
command = registrar.command(cmdtable)

@command('dksafe', [], '', norepo=True)
def run(ui, **opts):
    import hgdemandimport
    hgdemandimport.disable()
    sys.path.insert(0, os.path.abspath('build_tools'))
    from obfuscation_runtime import validate
    base = os.path.abspath('build/obfuscation/safe/staging')
    package = os.environ.get('DK_SAFE_PACKAGE')
    output = os.path.abspath('build/obfuscation/safe/runtime-build%s.json' % ('-package' if package else ''))
    if os.environ.get('DK_SAFE_MARKS'):
        from pjorion_poc_runtime import validate as marks
        marks(os.path.abspath('source/scripts/client/Driftkings/core/marks_calculator.py'),
              os.path.join(base, 'Driftkings/core/marks_calculator.pyc'),
              os.path.abspath('build/obfuscation/safe/marks-build%s.json' % ('-package' if package else '')), package)
    else:
        validate(base, output, package, hooks=not bool(package))
    return 0
