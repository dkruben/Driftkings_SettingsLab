"""Owned-path unit tests and instrumented compiler flow: NEVER create a WOTMOD."""
import errno
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from contextlib import ExitStack, contextmanager
from build_tools import compiler as c
from build_tools import isolated_output as iso
from build_tools.isolated_output import IsolatedOutput, tool_environment


class IsolatedOutputTests(unittest.TestCase):
    def test_cli_and_modes(self):
        parser = c.argument_parser()
        args = parser.parse_args(['--isolated-output', '--keep-source-version'])
        c.validate_isolated_args(args, 'beta')
        self.assertTrue(args.isolated_output)
        for flags in (['--isolated-output'], ['--isolated-output', '--keep-source-version', '--mode', 'release'],
                      ['--isolated-output', '--keep-source-version', '--channel', 'stable']):
            with self.subTest(flags=flags), self.assertRaises(ValueError):
                c.build(parser.parse_args(flags))
        with self.assertRaises(ValueError):
            c.validate_isolated_args(args, 'stable')
        c.validate_isolated_args(parser.parse_args(['--mode', 'release', '--channel', 'stable']), 'stable')

    def test_exclusive_paths_and_existing_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ('..', '../bad', '/absolute', 'a/b', 'a\\b'):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    IsolatedOutput(root, name)
            with IsolatedOutput(root, 'one') as scope:
                (scope.path / 'output' / 'own.fixture').write_bytes(b'own')
                for path in (root / 'escape', scope.path / '..' / 'escape'):
                    with self.assertRaises(ValueError):
                        path.write_bytes(b'no')
                with self.assertRaises(ValueError):
                    scope.path.rmdir()
            with self.assertRaises(FileExistsError):
                IsolatedOutput(root, 'one').reserve()
            (root / 'build/experiments/file').write_bytes(b'preexisting')
            with self.assertRaises(FileExistsError):
                IsolatedOutput(root, 'file').reserve()
            self.assertEqual((root / 'build/experiments/file').read_bytes(), b'preexisting')
            self.assertEqual((root / 'build/experiments/one/output/own.fixture').read_bytes(), b'own')

    def test_permission_and_creation_failures(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original = Path.mkdir
            for error in (PermissionError('denied'), OSError('disk failure')):
                def fail(path, *a, **kw):
                    if path.name == 'denied':
                        raise error
                    return original(path, *a, **kw)
                with patch.object(Path, 'mkdir', fail), self.assertRaises(OSError):
                    IsolatedOutput(root, 'denied').reserve()
                self.assertFalse((root / 'build/experiments/denied').exists())

    def test_junction_rejected(self):
        if os.name != 'nt':
            self.skipTest('Windows junction test')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); target = root / 'protected'; target.mkdir()
            (root / 'build').mkdir()
            junction = root / 'build/experiments'
            result = subprocess.run(['cmd', '/c', 'mklink', '/J', str(junction), str(target)], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            try:
                with self.assertRaises(ValueError):
                    IsolatedOutput(root, 'rejected').reserve()
                self.assertEqual(list(target.iterdir()), [])
            finally:
                os.rmdir(junction)

    def test_symlink_rejected_without_admin_requirement(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); target = root / 'protected'; target.mkdir(); (root / 'build').mkdir()
            link = root / 'build/experiments'
            try:
                link.symlink_to(target, target_is_directory=True)
            except OSError:
                # Reparse/symlink detection also covered deterministically without OS privileges.
                import stat
                from types import SimpleNamespace
                original = Path.lstat
                def simulated(path, *a, **kw):
                    if path == link:
                        return SimpleNamespace(st_mode=stat.S_IFLNK, st_file_attributes=0x400)
                    return original(path, *a, **kw)
                with patch.object(Path, 'lstat', simulated), self.assertRaises(ValueError):
                    IsolatedOutput(root, 'rejected').reserve()
            else:
                with self.assertRaises(ValueError):
                    IsolatedOutput(root, 'rejected').reserve()
                link.unlink()
            self.assertEqual(list(target.iterdir()), [])

    def test_scoped_tool_paths_and_guard(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with IsolatedOutput(root) as scope:
                env = tool_environment({'EXAMPLE': 'preserved'})
                self.assertEqual(env['EXAMPLE'], 'preserved')
                self.assertTrue(Path(env['TEMP']).is_relative_to(scope.path))
                log = scope.path / 'diagnostics/tool.log'
                with patch.object(c.subprocess, 'run') as execute:
                    execute.return_value.returncode = 0
                    c.run_tool(['fake-compiler'], log)
                    self.assertTrue(Path(execute.call_args.kwargs['cwd']).is_relative_to(scope.path))
                    self.assertEqual(execute.call_args.kwargs['env']['TEMP'], env['TEMP'])
                with self.assertRaises(ValueError):
                    c.run_tool(['fake'], root / 'outside.log')
                with self.assertRaises(ValueError):
                    os.replace(log, root / 'outside.log')
                with self.assertRaises(ValueError):
                    os.link(log, scope.path / 'output/hardlink')

    def test_own_temporary_cleanup_and_external_directory_preserved(self):
        import shutil
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); old = root / 'old'; old.mkdir(); (old / 'sentinel').write_bytes(b'old')
            with IsolatedOutput(root) as scope:
                child = scope.path / 'workspace' / 'temporary'; child.mkdir()
                nested = child / 'nested'; nested.mkdir(); (nested / 'file.fixture').write_bytes(b'own')
                shutil.rmtree(child)
                self.assertFalse(child.exists())
                with self.assertRaises(ValueError):
                    shutil.rmtree(old)
            self.assertEqual((old / 'sentinel').read_bytes(), b'old')

    def test_runtime_escape_rejected_and_normal_guard_inactive(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); external = root / 'global.fixture'
            with IsolatedOutput(root) as scope:
                with self.assertRaises(ValueError):
                    external.write_bytes(b'bad')
                with self.assertRaises(ValueError):
                    c.run_tool(['fake'], scope.path / 'diagnostics/log', cwd=root)
                original = scope.identity
                scope.identity = (-1,-1)
                with self.assertRaises(ValueError):
                    (scope.path / 'output/file').write_bytes(b'bad')
                scope.identity = original
            external.write_bytes(b'normal')
            self.assertEqual(external.read_bytes(),b'normal')

    def test_readonly_git_does_not_refresh_shared_index(self):
        with patch.object(c.subprocess, 'check_output', return_value=b'946684800') as run:
            c.git_state(Path.cwd(), True)
            for call in run.call_args_list:
                self.assertEqual(call.kwargs['env']['GIT_OPTIONAL_LOCKS'], '0')
        with patch.object(c.subprocess, 'check_output', return_value=b'946684800') as run:
            c.git_state(Path.cwd())
            self.assertNotIn('env',run.call_args.kwargs)

    def test_real_buffers_with_scoped_subprocess(self):
        # Self-contained: a real child process transforms an in-memory buffer through
        # stdin/stdout using the scoped cwd and environment, exactly as buffer tools
        # are launched by the build. No client, diagnostics or repository inputs.
        import hashlib
        import sys
        child = ('import hashlib,json,os,sys,tempfile;raw=sys.stdin.buffer.read();'
                 'sys.stdout.write(json.dumps(dict(cwd=os.getcwd(),temp=tempfile.gettempdir(),'
                 'bytecode=os.environ.get("PYTHONDONTWRITEBYTECODE"),sha=hashlib.sha256(raw).hexdigest(),'
                 'output=raw[::-1].hex())))')
        raw = bytes(range(256)) * 64
        with tempfile.TemporaryDirectory() as temp:
            external = Path(temp) / 'external.fixture'
            external.write_bytes(b'external')
            with IsolatedOutput(Path(temp)) as scope:
                workspace = scope.path / 'workspace'
                result = subprocess.run([sys.executable, '-I', '-B', '-c', child], input=raw, cwd=str(workspace),
                                        env=tool_environment(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual(os.path.realpath(report['cwd']), os.path.realpath(str(workspace)))
                self.assertTrue(Path(os.path.realpath(report['temp'])).is_relative_to(os.path.realpath(str(scope.path))))
                self.assertEqual(report['bytecode'], '1')
                self.assertEqual(report['sha'], hashlib.sha256(raw).hexdigest())
                self.assertEqual(bytes.fromhex(report['output']), raw[::-1])
                owned = scope.path
            self.assertFalse(list(Path(temp).rglob('*.wotmod')))
            self.assertEqual(external.read_bytes(), b'external')
            outside = [p for p in Path(temp).rglob('*') if p.is_file() and not p.is_relative_to(owned)]
            self.assertEqual(outside, [external])

    def simulate(self, failure=None, isolated=True, mode='debug', channel='beta'):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            protected = {}
            for relative in ('build/unified/sentinel.fixture', 'build/debug/beta/old.fixture',
                             'build/releases/stable/old.fixture', 'build/backups/old.fixture', 'VERSION', 'release.json'):
                path = root / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b'protected')
                protected[path] = path.read_bytes()
            config = {'package': {'release_root':'build/releases','debug_root':'build/debug'},
                      'game':{'version':'2.4.2.0'}, 'python':{'archive_root':'res/scripts/client'},
                      'generators':{}}
            plan = {k:[] for k in ('components','python','assets','defaults','dependencies')}
            args = c.argument_parser().parse_args(['--keep-source-version', '--mode', mode, '--channel', channel] +
                                                  (['--isolated-output'] if isolated else []))
            release = {'package_id':'fixture','repository':'fixture','changelog':[]}
            writes=[]
            def stage(name, path):
                path = Path(path)
                if isolated:
                    self.assertTrue(path.is_relative_to(root / 'build/experiments'), path)
                writes.append((name,str(path)))
                path.parent.mkdir(parents=True, exist_ok=True)
                if failure == name:
                    raise OSError('injected '+name)
                path.write_bytes(b'fixture')
            def worker(tools, run, job, name):
                stage('compile' if name == 'python' else 'verify', run / (name+'.fixture'))
                return {}
            def generate(r, conf, pl, tools, run, epoch):
                stage('generate', run/'generated/asset.fixture')
                stage('patch', run/'generated/patch.fixture')
                return {}
            def package(path, entries, *a):
                # Deliberately DO NOT create path (.wotmod). Exercise writer destinations with a .fixture.
                stage('package', Path(path).with_suffix('.fixture'))
            def distribution(r, conf, pl, candidate, *a):
                stage('copy',candidate/'distribution.fixture');return {}
            original_stat = Path.stat
            def fixture_stat(path, *a, **kw):
                return original_stat(path.with_suffix('.fixture') if path.suffix == '.wotmod' else path, *a, **kw)
            with ExitStack() as stack:
                stack.enter_context(patch.object(Path, 'stat', fixture_stat))
                for name,value in {'ROOT':root,'read_json':lambda p:config if p.name=='build_config.json' else release,
                    'check_release_identity':lambda *a:None, 'select_version':lambda *a:('0.1.8-beta.4' if channel=='beta' else '0.1.8',channel,'source'),
                    'discover':lambda *a:{'game_root':'readonly'}, 'build_plan':lambda *a,**k:plan,
                    'require_tools':lambda *a:None,'check_client':lambda *a:'CT',
                    'git_state':lambda *a:{'epoch':946684800},'source_inventory':lambda *a:{},
                    'python_overrides':lambda *a:{},'run_worker':worker,'generate':generate,
                    'package_entries':lambda *a:{},'zip_entries':package,'verify_package':lambda *a:None,
                    'sha':lambda *a:'fixture-hash', 'write_distribution':distribution,
                    'assemble_defaults':lambda *a:({},None,{}), 'create_modpack':lambda *a:{},'artifact_files':lambda *a:[]}.items():
                    stack.enter_context(patch.object(c,name,value))
                original_write_json = c.write_json
                def json_writer(path, value):
                    if failure == 'diagnostic' and value.get('status') == 'complete':
                        raise OSError('injected diagnostic')
                    original_write_json(path, value)
                stack.enter_context(patch.object(c, 'write_json', json_writer))
                publish = stack.enter_context(patch.object(c,'publish_local'))
                if failure:
                    with self.assertRaisesRegex(OSError,'injected'):
                        c.build(args)
                else:
                    output=c.build(args)
                    if isolated:
                        self.assertTrue(output.is_relative_to(root/'build/experiments'))
                    else:
                        self.assertEqual(output,root/config['package']['debug_root' if mode=='debug' else 'release_root']/channel/('0.1.8-beta.4' if channel=='beta' else '0.1.8'))
                self.assertEqual(publish.call_count,0 if isolated else 1)
            self.assertTrue(writes)
            self.assertFalse(list(root.rglob('*.wotmod')))
            for path,raw in protected.items():
                self.assertEqual(path.read_bytes(),raw,path)
            if isolated:
                states=list((root/'build/experiments').glob('*/diagnostics/state.json'))
                self.assertEqual(len(states),1)
                self.assertEqual(json.loads(states[0].read_text())['status'],'failed' if failure else 'complete')

    def test_instrumented_full_flow_and_failures(self):
        for failure in (None,'compile','generate','patch','package','copy','verify','diagnostic'):
            with self.subTest(failure=failure):
                self.simulate(failure)

    def test_normal_debug_and_release_dispatch_preserved(self):
        for mode,channel in (('debug','beta'),('debug','stable'),('release','beta'),('release','stable')):
            with self.subTest(mode=mode,channel=channel):
                self.simulate(isolated=False,mode=mode,channel=channel)


@contextmanager
def simulated_descriptors(table, proc=True):
    """Simulate POSIX directory descriptors and /proc/self/fd on any platform.

    table maps a descriptor number to a directory path, to None (closed) or to a
    (stat_path, proc_name) pair. This drives the guard's resolution logic; it is
    NOT a real Linux validation.
    """
    real_fstat, real_readlink = os.fstat, os.readlink

    def fstat(fd):
        if fd not in table:
            return real_fstat(fd)
        entry = table[fd]
        if entry is None:
            raise OSError(errno.EBADF, 'Bad file descriptor')
        return os.stat(entry[0] if isinstance(entry, tuple) else entry)

    def readlink(path, *args, **kwargs):
        text = os.fspath(path)
        if not (isinstance(text, str) and text.startswith(iso._PROC_FD + '/')):
            return real_readlink(path, *args, **kwargs)
        entry = table.get(int(text.rsplit('/', 1)[1]))
        if not proc or entry is None:
            raise FileNotFoundError(errno.ENOENT, 'No such file or directory', text)
        if isinstance(entry, tuple):
            if isinstance(entry[1], BaseException):
                raise entry[1]
            return entry[1]
        return str(entry)

    with patch.object(iso.os, 'fstat', fstat), patch.object(iso.os, 'readlink', readlink):
        yield


REAL_PROC_FD = os.path.isdir('/proc/self/fd') and os.rmdir in getattr(os, 'supports_dir_fd', ())


class DirFdGuardTests(unittest.TestCase):
    """Relative paths with dir_fd: resolved against the descriptor, never cwd, fail closed."""

    @contextmanager
    def workspace(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            outside = root / 'outside'; outside.mkdir(); (outside / 'victim.tmp').write_bytes(b'external')
            other = IsolatedOutput(root, 'other'); other.reserve(); other.close()
            (other.path / 'workspace' / 'victim.tmp').write_bytes(b'other run')
            with IsolatedOutput(root, 'own') as scope:
                work = scope.path / 'workspace' / 't'; work.mkdir()
                (work / 'file.tmp').write_bytes(b'own')
                (work / 'nested').mkdir(); (work / 'nested' / 'inner.tmp').write_bytes(b'own')
                yield scope, work, outside, other
            self.assertEqual((outside / 'victim.tmp').read_bytes(), b'external')
            self.assertEqual((other.path / 'workspace' / 'victim.tmp').read_bytes(), b'other run')

    def rejected(self, *event):
        with self.assertRaises(ValueError):
            sys.audit(*event)

    def test_relative_without_dir_fd_keeps_cwd_semantics(self):
        with self.workspace() as (scope, work, outside, other):
            self.rejected('os.remove', 'file.tmp', -1)  # cwd is not the owned directory
            sys.audit('os.remove', str(work / 'file.tmp'), -1)
            sys.audit('os.utime', str(work / 'file.tmp'), None, None, -100)  # raw AT_FDCWD
            sys.audit('shutil.rmtree', str(work / 'nested'), None)
            previous = os.getcwd()
            os.chdir(work)
            try:
                sys.audit('os.remove', 'file.tmp', -1)
                # No /proc: must fail even though cwd/file.tmp is owned (no cwd fallback).
                with simulated_descriptors({9001: work}, proc=False):
                    self.rejected('os.remove', 'file.tmp', 9001)
            finally:
                os.chdir(previous)

    def test_relative_with_owned_dir_fd_allowed(self):
        with self.workspace() as (scope, work, outside, other):
            with simulated_descriptors({9001: work, 9002: work / 'nested', 9003: scope.path}):
                sys.audit('os.remove', 'file.tmp', 9001)
                sys.audit('os.rmdir', 'nested', 9001)
                sys.audit('os.mkdir', 'created', 0o777, 9001)
                sys.audit('os.chmod', 'file.tmp', 0o600, 9001)
                sys.audit('os.utime', 'file.tmp', None, None, 9001)
                sys.audit('os.rename', 'file.tmp', 'inner.tmp', 9001, 9002)
                sys.audit('os.replace', 'inner.tmp', 'file.tmp', 9002, 9001)
                sys.audit('shutil.rmtree', 'nested', 9001)
                sys.audit('os.remove', 'workspace/t/file.tmp', 9003)
            self.assertEqual((work / 'file.tmp').read_bytes(), b'own')  # audit only: nothing was removed

    def test_exterior_other_run_and_root_descriptors_rejected(self):
        with self.workspace() as (scope, work, outside, other):
            table = {9001: work, 9002: outside, 9003: other.path / 'workspace', 9004: scope.path.parent, 9005: scope.path}
            with simulated_descriptors(table):
                for fd in (9002, 9003):
                    for event in (('os.remove', 'victim.tmp', fd), ('os.rmdir', 'victim.tmp', fd),
                                  ('os.mkdir', 'created', 0o777, fd), ('os.chmod', 'victim.tmp', 0o600, fd),
                                  ('os.utime', 'victim.tmp', None, None, fd), ('shutil.rmtree', 'victim.tmp', fd),
                                  ('os.rename', 'file.tmp', 'victim.tmp', 9001, fd),
                                  ('os.replace', 'victim.tmp', 'file.tmp', fd, 9001)):
                        with self.subTest(fd=fd, event=event[0]):
                            self.rejected(*event)
                # A descriptor above the run never authorises, even for a target inside it.
                self.rejected('os.remove', 'own/workspace/t/file.tmp', 9004)
                self.rejected('os.rmdir', 'own', 9004)
                self.rejected('os.rmdir', 'workspace/..', 9005)

    def test_absolute_path_ignores_dir_fd(self):
        with self.workspace() as (scope, work, outside, other):
            with simulated_descriptors({9001: work, 9002: outside}):
                sys.audit('os.remove', str(work / 'file.tmp'), 9002)  # same as the OS: dir_fd unused
                self.rejected('os.remove', str(outside / 'victim.tmp'), 9001)
                self.rejected('os.rmdir', str(scope.path), 9001)

    def test_invalid_closed_and_non_directory_descriptors_rejected(self):
        with self.workspace() as (scope, work, outside, other):
            for fd in (-5, 'x', True, 1.5, b'1'):
                with self.subTest(fd=fd):
                    self.rejected('os.remove', 'file.tmp', fd)
            with simulated_descriptors({9001: None}):
                self.rejected('os.remove', 'file.tmp', 9001)
            closed = os.open(str(work / 'file.tmp'), os.O_RDONLY); os.close(closed)
            self.rejected('os.remove', 'file.tmp', closed)  # real closed descriptor
            regular = os.open(str(work / 'file.tmp'), os.O_RDONLY)
            try:
                self.rejected('os.remove', 'file.tmp', regular)  # real descriptor of a regular file
                with simulated_descriptors({regular: (work / 'file.tmp', str(work))}):
                    self.rejected('os.remove', 'file.tmp', regular)
            finally:
                os.close(regular)

    def test_parent_traversal_rejected(self):
        with self.workspace() as (scope, work, outside, other):
            with simulated_descriptors({9001: work, 9002: work / 'nested'}):
                for name in ('..', '../file.tmp', 'nested/../file.tmp', '../../../../outside/victim.tmp'):
                    with self.subTest(name=name):
                        self.rejected('os.remove', name, 9002)
                        self.rejected('os.rmdir', name, 9001)

    def link(self, link, target):
        """Real symlink when the OS allows it, otherwise the same lstat simulation used above."""
        token = iso._ACTIVE.set(None)  # links are forbidden while the guard is active
        try:
            link.symlink_to(target, target_is_directory=target.is_dir())
            return ExitStack()
        except OSError:
            import stat
            from types import SimpleNamespace
            original = Path.lstat

            def simulated(path, *a, **kw):
                if path == link:
                    return SimpleNamespace(st_mode=stat.S_IFLNK, st_file_attributes=0x400)
                return original(path, *a, **kw)
            stack = ExitStack()
            stack.enter_context(patch.object(Path, 'lstat', simulated))
            return stack
        finally:
            iso._ACTIVE.reset(token)

    def test_symlinks_rejected_and_final_link_not_followed(self):
        with self.workspace() as (scope, work, outside, other):
            inner, escape = work / 'inner-link', work / 'escape'
            with self.link(inner, work / 'file.tmp'), self.link(escape, outside):
                with simulated_descriptors({9001: work, 9002: (outside, str(escape)), 9003: (outside, str(outside))}):
                    self.rejected('os.remove', 'inner-link', 9001)  # final link: rejected, never followed
                    self.rejected('os.remove', 'escape', 9001)
                    self.rejected('os.remove', 'escape/victim.tmp', 9001)
                    self.rejected('os.rmdir', 'escape/victim.tmp', 9001)
                    self.rejected('os.remove', 'victim.tmp', 9002)  # name is a link standing for the directory
                    self.rejected('os.remove', 'victim.tmp', 9003)  # descriptor obtained through the link
                    sys.audit('os.remove', 'file.tmp', 9001)
                for path in (inner, escape):
                    if path.is_symlink():
                        token = iso._ACTIVE.set(None)
                        try:
                            path.unlink()
                        finally:
                            iso._ACTIVE.reset(token)

    def test_nested_cleanup_sequence(self):
        # The order used by POSIX shutil.rmtree: entries by name relative to the directory descriptor.
        with self.workspace() as (scope, work, outside, other):
            deep = work / 'nested' / 'deep'; deep.mkdir(); (deep / 'leaf.tmp').write_bytes(b'own')
            with simulated_descriptors({9001: work, 9002: work / 'nested', 9003: deep}):
                for event in (('os.remove', 'leaf.tmp', 9003), ('os.rmdir', 'deep', 9002), ('os.remove', 'inner.tmp', 9002),
                              ('os.rmdir', 'nested', 9001), ('os.remove', 'file.tmp', 9001)):
                    sys.audit(*event)
            shutil.rmtree(work)  # real removal with this platform's implementation
            self.assertFalse(work.exists())
            self.assertTrue(scope.path.is_dir())

    def test_proc_resolution_failures_rejected(self):
        with self.workspace() as (scope, work, outside, other):
            gone = work / 'gone'
            cases = {'no proc entry': (work, FileNotFoundError(2, 'missing')),
                     'permission': (work, PermissionError(13, 'denied')),
                     'unsupported': (work, NotImplementedError('readlink')),
                     'deleted directory': (work, str(gone) + ' (deleted)'),
                     'relative name': (work, 't'), 'bytes name': (work, os.fsencode(str(work))),
                     'identity mismatch': (outside, str(work)), 'name is a file': (work, str(work / 'file.tmp'))}
            for label, entry in cases.items():
                with self.subTest(case=label), simulated_descriptors({9001: entry}):
                    self.rejected('os.remove', 'file.tmp', 9001)
                    self.rejected('os.rmdir', 'nested', 9001)
            with simulated_descriptors({9001: work}, proc=False):
                self.rejected('os.remove', 'file.tmp', 9001)
                self.rejected('shutil.rmtree', 'nested', 9001)
            if not os.path.isdir('/proc/self/fd'):  # this platform really has no /proc: real resolution fails closed
                directory = os.open(str(work / 'file.tmp'), os.O_RDONLY)
                try:
                    with patch.object(iso.os, 'fstat', lambda fd: os.stat(work)):
                        self.rejected('os.remove', 'file.tmp', directory)
                finally:
                    os.close(directory)

    def test_closed_workspace_guard_inactive(self):
        with self.workspace() as (scope, work, outside, other):
            pass
        sys.audit('os.remove', 'file.tmp', 9001)  # no active scope: no descriptor is consulted
        self.assertIsNone(iso.active_output())
        with tempfile.TemporaryDirectory() as temp:
            child = Path(temp) / 'normal'; child.mkdir(); (child / 'file.tmp').write_bytes(b'normal')
            shutil.rmtree(child)
            self.assertFalse(child.exists())

    @unittest.skipUnless(os.name == 'nt', 'Windows behaviour')
    def test_windows_behaviour_unchanged(self):
        with self.workspace() as (scope, work, outside, other):
            with self.assertRaises(NotImplementedError):
                os.unlink('file.tmp', dir_fd=3)  # rejected by the platform before any audit event
            with self.assertRaises(NotImplementedError):
                os.rmdir('nested', dir_fd=3)
            self.assertTrue((work / 'file.tmp').exists())
            with self.assertRaises(ValueError):
                shutil.rmtree(outside)
            with self.assertRaises(ValueError):
                (outside / 'victim.tmp').unlink()
            (work / 'file.tmp').unlink(); shutil.rmtree(work / 'nested'); work.rmdir()
            self.assertFalse(work.exists())

    @unittest.skipUnless(REAL_PROC_FD, 'requires a real POSIX /proc/self/fd')
    def test_real_posix_descriptors(self):
        with self.workspace() as (scope, work, outside, other):
            self.assertTrue(shutil.rmtree.avoids_symlink_attacks)
            own = os.open(str(work), os.O_RDONLY); foreign = os.open(str(outside), os.O_RDONLY)
            sibling = os.open(str(other.path / 'workspace'), os.O_RDONLY)
            try:
                self.assertEqual(iso.descriptor_directory(own), work)
                for fd in (foreign, sibling):
                    with self.assertRaises(ValueError):
                        os.unlink('victim.tmp', dir_fd=fd)
                    with self.assertRaises(ValueError):
                        os.mkdir('created', dir_fd=fd)
                with self.assertRaises(ValueError):
                    os.unlink('../../../../outside/victim.tmp', dir_fd=own)
                os.mkdir('created', dir_fd=own); os.rmdir('created', dir_fd=own)
                os.rename('file.tmp', 'renamed.tmp', src_dir_fd=own, dst_dir_fd=own)
                with self.assertRaises(ValueError):
                    os.rename('renamed.tmp', 'stolen.tmp', src_dir_fd=own, dst_dir_fd=foreign)
                os.unlink('renamed.tmp', dir_fd=own)
                shutil.rmtree('nested', dir_fd=own)
                self.assertEqual(os.listdir(str(work)), [])
            finally:
                for fd in (own, foreign, sibling):
                    os.close(fd)
            closed = os.open(str(work), os.O_RDONLY); os.close(closed)
            with self.assertRaises((ValueError, OSError)):
                os.rmdir('nested', dir_fd=closed)
            tree = scope.path / 'workspace' / 'tree'; (tree / 'a' / 'b').mkdir(parents=True)
            (tree / 'a' / 'b' / 'leaf.tmp').write_bytes(b'own')
            shutil.rmtree(tree)  # fd-relative unlink/rmdir on this platform
            self.assertFalse(tree.exists())


if __name__ == '__main__':
    unittest.main()
