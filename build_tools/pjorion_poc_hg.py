"""Use the real build Python host to validate the protected POC bytes."""
from mercurial import registrar
import os
import sys

cmdtable = {}
command = registrar.command(cmdtable)


@command('dkorionpoc', [], '', norepo=True)
def run(ui, **opts):
    import hgdemandimport
    hgdemandimport.disable()
    sys.path.insert(0, os.path.abspath('build_tools'))
    from pjorion_poc_runtime import validate
    folder = os.path.abspath('build/obfuscation/poc')
    validate(os.path.abspath('source/scripts/client/Driftkings/core/marks_calculator.py'),
             os.path.join(folder, 'protected/marks_calculator.pyc'),
             os.path.join(folder, 'runtime-build.json'))
    validate(os.path.abspath('source/scripts/client/Driftkings/core/marks_calculator.py'),
             os.path.join(folder, 'protected/marks_calculator.pyc'),
             os.path.join(folder, 'runtime-build-package.json'),
             os.path.join(folder, 'Driftkings-PJOrion-POC.wotmod'))
    ui.write('PJOrion POC: protected file and experimental package passed in build Python\n')
    return 0
