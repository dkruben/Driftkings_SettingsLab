# -*- coding: utf-8 -*-
"""Python 2.7 compile/verification worker; standalone or SourceTree hg extension."""
from __future__ import print_function
import imp
import json
import marshal
import os
import struct
import sys
import types
import zipfile

MAGIC = b'\x03\xf3\x0d\x0a'


def process(job_path):
    if sys.version_info[:2] != (2, 7) or imp.get_magic() != MAGIC:
        raise RuntimeError('This worker requires a real Python 2.7 interpreter')
    sys.dont_write_bytecode = True
    with open(job_path, 'rb') as stream:
        job = json.load(stream)
    if job['action'] == 'compile':
        for item in job['files']:
            with open(item['source'], 'rb') as stream:
                source = stream.read()
            if item['target'] in job['overrides']:
                source = job['overrides'][item['target']].encode('utf-8')
            code = compile(source, item['target'][4:-1], 'exec')
            target = os.path.join(job['output'], *item['target'].split('/'))
            parent = os.path.dirname(target)
            if not os.path.isdir(parent):
                os.makedirs(parent)
            with open(target, 'wb') as stream:
                stream.write(MAGIC + struct.pack('<I', job['epoch']) + marshal.dumps(code))
        result = dict(python=sys.version, compiled=len(job['files']))
    elif job['action'] == 'common-probe':
        probe = imp.load_source('_dk_common_startup_probe',
                                os.path.join(os.path.dirname(__file__), 'common_startup_probe_py27.py'))
        result = probe.verify(job['origin'])
    elif job['action'] == 'verify':
        with zipfile.ZipFile(job['package']) as archive:
            count = 0
            for name in archive.namelist():
                if name.endswith('.pyc'):
                    raw = archive.read(name)
                    if raw[:4] != MAGIC or not isinstance(marshal.loads(raw[8:]), types.CodeType):
                        raise ValueError('Invalid Python 2.7 bytecode: ' + name)
                    count += 1
        # Import actual packaged bytecodes without starting game-dependent updater services.
        origin = job['package'].replace('\\', '/') + '/res/scripts/client'
        sys.path.insert(0, origin)
        import driftkings
        if driftkings.VERSION != job['version']:
            raise ValueError('Packaged runtime version differs from release version')
        from driftkings.component_list import COMPONENTS
        if list(COMPONENTS) != job['components']:
            raise ValueError('Packaged component list differs from enabled manifests')
        package = types.ModuleType('driftkings.core.updater')
        package.__path__ = [origin + '/driftkings/core/updater']
        sys.modules[package.__name__] = package
        from driftkings.core.updater.versioning import Version
        from driftkings.core.updater.manifest import Manifest
        from driftkings.core.marks_calculator import ceil_damage
        with open(job['manifest'], 'rb') as stream:
            manifest = Manifest.parse(stream.read())
        if (manifest.version.text != job['version'] or manifest.channel != job['channel'] or
                not manifest.compatible(job['game_version'])):
            raise ValueError('Release metadata is incompatible with the packaged updater')
        if not Version(job['version']).allowed(job['channel']) or ceil_damage(1.1) != 2:
            raise ValueError('Packaged version/calculator contract failed')
        result = dict(python=sys.version, verified=count, version=driftkings.VERSION,
                      components=len(COMPONENTS), updaterManifest='valid')
        if 'modpack' in job:
            from driftkings.core.updater.inventory import Inventory
            with open(job['modpack'], 'rb') as stream:
                document = json.loads(stream.read().decode('utf-8'))
            inventory = Inventory(document, manifest.version.text, manifest.channel, manifest.game_version)
            inventory.verify_archive(os.path.join(os.path.dirname(job['modpack']), inventory.distribution['file']))
            result['modpack'] = dict(status='passed', files=len(inventory.files), defaults=len(inventory.defaults))
        settings_package = types.ModuleType('driftkings.settings')
        settings_package.__path__ = [origin + '/driftkings/settings']
        sys.modules[settings_package.__name__] = settings_package
        from driftkings.settings.default_values import DEFAULTS, SELECTOR
        if DEFAULTS != job['defaults'] or SELECTOR != job['selector']:
            raise ValueError('Packaged Python defaults differ from the canonical JSON')
        result['defaults'] = dict(status='passed', components=len(DEFAULTS), source='canonical-json')
        probe_path = os.path.join(os.path.dirname(__file__), 'common_startup_probe_py27.py')
        if os.path.isfile(probe_path):
            probe = imp.load_source('_dk_common_startup_probe', probe_path)
            result['commonStartup'] = probe.verify(origin)
        else:
            result['commonStartup'] = {'status': 'not-installed', 'reason': 'Optional local probe is not distributed'}
    else:
        raise ValueError('Unknown worker action')
    with open(job['result'], 'wb') as stream:
        stream.write(json.dumps(result, sort_keys=True).encode('utf-8'))
    print('Python 2.7 %s: OK' % job['action'])
    return 0


cmdtable = {}
if __name__ != '__main__':
    from mercurial import registrar
    command = registrar.command(cmdtable)

    @command('dkcompile', [], '', norepo=True)
    def run(ui, **opts):
        import hgdemandimport
        hgdemandimport.disable()
        return process(os.environ['DK_COMPILE_JOB'])
else:
    sys.exit(process(sys.argv[1]))
