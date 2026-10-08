# -*- coding: utf-8 -*-
"""Normal cross-runtime contracts, optionally importing compiled bytecode only."""
import hashlib
import io
import json
import os
import py_compile
import shutil
import struct
import sys
import tempfile
import zipfile


def run(mode, label):
    sys.dont_write_bytecode = True
    root = os.path.abspath('.')
    folder = os.path.join(root,'build/windows-files-regression',label)
    if not os.path.isdir(folder): os.makedirs(folder)
    source = os.path.join(root,'source/scripts/client')
    candidate = os.path.abspath(os.path.join(folder,'payload'))
    compiled = []
    archive = zipfile.ZipFile(os.path.join(root,'build/unified/Driftkings.wotmod')) if mode == 'packaged' else None
    files = ['Driftkings/__init__.py','Driftkings/core/__init__.py']
    files += ['Driftkings/core/updater/'+name for name in os.listdir(os.path.join(source,'Driftkings/core/updater')) if name.endswith('.py')]
    for relative in files:
        target = os.path.join(candidate,relative+('c' if mode != 'source' else ''))
        if not os.path.isdir(os.path.dirname(target)): os.makedirs(os.path.dirname(target))
        if mode == 'packaged':
            data = archive.read('res/scripts/client/'+relative+'c')
            assert data[:4] == b'\x03\xf3\x0d\x0a'
            with open(target,'wb') as stream: stream.write(data)
            compiled.append(target)
        elif mode == 'compiled':
            py_compile.compile(os.path.join(source,relative),cfile=target,dfile=relative,doraise=True)
            compiled.append(target)
        else: shutil.copyfile(os.path.join(source,relative),target)
    if mode != 'source':
        assert not any(name.endswith('.py') for directory,unused,files in os.walk(candidate) for name in files)
    sys.path = [candidate]+[p for p in sys.path if os.path.normcase(os.path.abspath(p or '.')) != os.path.normcase(source)]
    import __builtin__ as builtins
    original_import = builtins.__import__
    blocked = []
    def without_ctypes(name,*args,**kwargs):
        if name.split('.')[0] in ('ctypes','_ctypes'):
            blocked.append(name)
            raise ImportError('WoT-equivalent contract blocks '+name)
        return original_import(name,*args,**kwargs)
    builtins.__import__ = without_ctypes
    for name in ('ctypes','_ctypes'):
        try: __import__(name)
        except ImportError: pass
        else: raise AssertionError('Import blocker ineffective')
    from Driftkings.core.updater import windows_files as windows
    from Driftkings.core.updater.results import Results
    from Driftkings.core.updater.installer import Installer, write_new
    from Driftkings.core.updater.manifest import Manifest
    imports = {name:module.__file__ for name,module in sys.modules.items() if name.startswith('Driftkings') and hasattr(module,'__file__')}
    if mode != 'source':
        assert all(path.endswith('.pyc') and os.path.abspath(path).startswith(candidate+os.sep) for path in imports.values()), imports
    else:
        assert all(path.endswith('.py') and os.path.abspath(path).startswith(candidate+os.sep) for path in imports.values()), imports
    resources = {}
    for resource,name in ((windows.HELPER_RESOURCE,'Driftkings.WindowsFiles.exe'),(windows.INFO_RESOURCE,'helper.json')):
        if archive is not None: resources[resource] = archive.read('res/'+resource)
        else:
            with open(os.path.join(root,'build/windows-files',name),'rb') as stream: resources[resource] = stream.read()
    if archive is not None: archive.close()
    helper_hash = hashlib.sha256(resources[windows.HELPER_RESOURCE]).hexdigest()
    assert helper_hash == json.loads(resources[windows.INFO_RESOURCE])['sha256']
    windows.initialize(resources.__getitem__,root,os.path.join(folder,'client-cache'))
    fixture = tempfile.mkdtemp(dir=folder)
    requests, responses = [], []
    original_request, original_response = windows.WindowsPathValidator.request, windows.WindowsPathValidator.response
    def observed_request(client,operation,*paths):
        requests.append(operation)
        return original_request(client,operation,*paths)
    def observed_response(client):
        value = original_response(client); responses.append(value); return value
    windows.WindowsPathValidator.request, windows.WindowsPathValidator.response = observed_request, observed_response
    try:
        unicode_path = os.path.join(fixture,u'configura\u00e7\u00f5es spaces')
        os.mkdir(unicode_path)
        windows.safe_path(unicode_path)
        pid = windows._client.process.pid
        windows.safe_path(os.path.join(unicode_path,'missing.json'))
        try: windows.safe_path(os.path.join(unicode_path,'invalid\x00path'))
        except OSError: pass
        else: raise AssertionError('Invalid path accepted')
        stage = os.path.join(fixture,'mods/configs/Driftkings/cache/update/download-regression')
        os.makedirs(stage)
        temporary, target = os.path.join(stage,'notice-regression'), os.path.join(stage,'notified.json')
        with open(temporary,'wb') as stream: stream.write(b'{"new":true}'); stream.flush(); os.fsync(stream.fileno())
        with open(target,'wb') as stream: stream.write(b'{"old":true}')
        windows.replace_receipt(temporary,target)
        with open(target,'rb') as stream: assert stream.read() == b'{"new":true}'
        assert not os.path.exists(temporary)
        os.remove(target)
        def package(version):
            out = io.BytesIO()
            with zipfile.ZipFile(out,'w',zipfile.ZIP_STORED) as archive:
                archive.writestr('meta.xml','<root><id>driftkings.unified</id><version>%s</version></root>'%version)
                archive.writestr('res/scripts/client/gui/mods/mod_Driftkings.pyc',b'\x03\xf3\x0d\x0a'+b'\0'*20)
            return out.getvalue()
        old,new = package('0.1.0'), package('1.0.0')
        manifest = Manifest(dict(schema=1,version='1.0.0',channel='stable',gameVersion='2.4.0.2',file='Driftkings.wotmod',
            size=len(new),sha256=hashlib.sha256(new).hexdigest(),download='https://github.com/dkruben/Driftkings_SettingsLab/releases/download/v1.0.0/Driftkings.wotmod'))
        write_new(os.path.join(stage,'release.json'),manifest.document())
        write_new(os.path.join(stage,'install.json'),dict(schema=1,version='1.0.0',gameVersion='2.4.0.2',size=len(new),sha256=manifest.sha256,
            installedVersion='0.1.0',installedSize=len(old),installedSha256=hashlib.sha256(old).hexdigest()))
        write_new(os.path.join(stage,'result.json'),dict(schema=1,status='installed',error=None,helperPid=123))
        package_path = os.path.join(fixture,'mods/2.4.0.2/Driftkings.wotmod')
        os.makedirs(os.path.dirname(package_path))
        with open(package_path,'wb') as stream: stream.write(new)
        reader = Results(fixture,loaded_version='1.0.0')
        reports = reader.scan('2.4.0.2'); assert reports[0]['status'] == 'installed'
        reader.acknowledge(reports[0]); assert reader.scan('2.4.0.2') == []
        assert windows._client.process.pid == pid and responses[0] == b'READY\t1'
        process = windows._client.process
        windows.close(); assert process.returncode == 0
        assert os.path.abspath(fixture).startswith(root+os.sep)
        shutil.rmtree(fixture)
        result = dict(status='PASS',mode=mode,python=sys.version,architecture=struct.calcsize('P')*8,
            imports=imports,compiledModules=len(compiled),noCtypes=True,blockedImports=blocked,
            helperSha256=helper_hash,helperPid=pid,helperExitCode=process.returncode,handshake='READY\t1',
            V=requests.count('V'),R=requests.count('R'),cleanupComplete=not os.path.exists(fixture))
        with open(os.path.join(folder,'result.json'),'wb') as stream: stream.write(json.dumps(result,indent=2).encode('utf8'))
        print(json.dumps(dict((key,result[key]) for key in ('status','mode','python','architecture','compiledModules','noCtypes','V','R','helperExitCode','cleanupComplete')),indent=2))
    finally:
        windows.close()
        windows.WindowsPathValidator.request, windows.WindowsPathValidator.response = original_request, original_response
        builtins.__import__ = original_import


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--mode',choices=['source','compiled'],required=True)
    parser.add_argument('--label',required=True,choices=['py2718-source','py2718-compiled','hg2715-source','hg2715-compiled'])
    args=parser.parse_args(); run(args.mode,args.label)
