"""Owned debug workspace and scoped write guard; no compiler or package logic."""
import contextvars
import ctypes
import os
from pathlib import Path
import re
import stat
import sys
import uuid

_ACTIVE = contextvars.ContextVar('driftkings_isolated_output', default=None)


def no_redirects(path):
    """Reject symlinks and every Windows reparse point, including junctions."""
    path = Path(path).absolute()
    for part in reversed((path,) + tuple(path.parents)):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('Isolated output rejects symlink/reparse point: ' + str(part))
    return path


_PROC_FD = '/proc/self/fd'
# Position of dir_fd in each audit event; os.truncate has none.
_DIR_FD_ARG = {'os.mkdir': 2, 'os.remove': 1, 'os.rmdir': 1, 'os.chmod': 2, 'os.utime': 3, 'shutil.rmtree': 1}


def descriptor_directory(fd):
    """Directory behind a POSIX dir_fd, proven through /proc/self/fd.

    Fails closed: ValueError whenever the directory cannot be proven (bad, closed
    or non-directory descriptor, no /proc, deleted or replaced directory). The
    current working directory is never used as a substitute.
    """
    if type(fd) is not int or fd < 0:
        raise ValueError('Invalid dir_fd in isolated output: %r' % (fd,))
    try:
        opened = os.fstat(fd)
        if not stat.S_ISDIR(opened.st_mode):
            raise ValueError('dir_fd is not a directory: %d' % fd)
        name = os.readlink('%s/%d' % (_PROC_FD, fd))
        if not isinstance(name, str) or not os.path.isabs(name):
            raise ValueError('dir_fd %d has no absolute directory name' % fd)
        named = os.lstat(name)  # lstat: a link put in place of the directory is not followed
    except (OSError, NotImplementedError, AttributeError) as error:
        raise ValueError('Cannot resolve dir_fd %d in isolated output: %s' % (fd, error)) from error
    if not stat.S_ISDIR(named.st_mode) or (named.st_dev, named.st_ino) != (opened.st_dev, opened.st_ino):
        raise ValueError('dir_fd %d does not match its directory name: %s' % (fd, name))
    return Path(name)


def _checked(scope, path, dir_fd=None):
    """Owned absolute destination of a path-based operation; dir_fd never authorises by itself."""
    # No dir_fd: CPython reports -1; os.utime reports the raw AT_FDCWD (-100 on Linux).
    absent = dir_fd is None or (type(dir_fd) is int and dir_fd in (-1, -100))
    if absent or isinstance(path, int) or os.path.isabs(path):
        return scope.check(path)  # the OS ignores dir_fd for absolute paths
    base = descriptor_directory(dir_fd)
    if not base.is_relative_to(scope.path):
        raise ValueError('dir_fd outside isolated output: ' + str(base))
    return scope.check(base / Path(path))  # rejects '..', links in any component and other runs


def _audit(event, args):
    scope = _ACTIVE.get()
    if scope is None:
        return
    argument = lambda index: args[index] if index is not None and len(args) > index else None
    if event == 'open':
        path, mode, flags = args
        if isinstance(path, int):
            return  # inherited descriptors are not created here
        if (mode and any(c in mode for c in 'wax+')) or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC):
            scope.check(path)
    elif event in ('os.mkdir', 'os.remove', 'os.rmdir', 'os.chmod', 'os.utime', 'os.truncate'):
        path = _checked(scope, args[0], argument(_DIR_FD_ARG.get(event)))
        if event == 'os.rmdir':
            scope.unpin_tree(path)
        if event in ('os.remove', 'os.rmdir') and path == scope.path:
            raise ValueError('Cannot remove owned execution root')
    elif event in ('os.rename', 'os.replace'):
        _checked(scope, args[0], argument(2)); _checked(scope, args[1], argument(3))
    elif event == 'shutil.rmtree':
        if _checked(scope, args[0], argument(_DIR_FD_ARG[event])) == scope.path:
            raise ValueError('Cannot recursively remove execution root')
    elif event in ('os.symlink', 'os.link'):
        raise ValueError('Links are forbidden in isolated output')


sys.addaudithook(_audit)


class IsolatedOutput:
    """Reserve once, preserve incomplete runs, never recursively clean directories."""
    def __init__(self, root, run_id=None):
        self.root = Path(root).absolute()
        if '..' in self.root.parts:
            raise ValueError('Parent traversal in repository root')
        self.run_id = run_id or uuid.uuid4().hex
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,95}', self.run_id):
            raise ValueError('Invalid isolated run ID')
        self.path = self.root / 'build' / 'experiments' / self.run_id
        self.identity = None
        self.handles = {}

    def _pin(self, path):
        # Windows directory handles deny DELETE sharing: pinned directories cannot
        # be renamed/replaced by junctions during this execution.
        if os.name != 'nt':
            return
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        create = kernel.CreateFileW
        create.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
                           ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
        create.restype = ctypes.c_void_p
        for parent in reversed((path,) + tuple(path.parents)):
            if parent in self.handles or not parent.is_dir():
                continue
            handle = create(str(parent), 0, 3, None, 3, 0x02200000, None)
            if handle == ctypes.c_void_p(-1).value:
                raise OSError(ctypes.get_last_error(), 'Cannot pin isolated directory: ' + str(parent))
            self.handles[parent] = handle
            no_redirects(parent)

    def reserve(self):
        try:
            no_redirects(self.path)
            if not self.root.is_dir():
                raise ValueError('Repository root must exist')
            self._pin(self.root)
            for parent in (self.root / 'build', self.root / 'build/experiments'):
                try:
                    parent.mkdir()
                except FileExistsError:
                    if not parent.is_dir():
                        raise ValueError('Isolated parent is not a directory')
                no_redirects(parent); self._pin(parent)
            self.path.mkdir()  # exclusive; NEVER exist_ok=True
            self._pin(self.path)
            info = self.path.stat()
            self.identity = (info.st_dev, info.st_ino)
            for name in ('workspace', 'output', 'manifests', 'diagnostics'):
                (self.path / name).mkdir()
            return self
        except BaseException:
            self.close()
            raise

    def check(self, value):
        if isinstance(value, int):
            raise ValueError('Descriptor destinations are not supported')
        value = Path(value)
        if '..' in value.parts:
            raise ValueError('Parent traversal in isolated output')
        path = no_redirects(value)
        if not path.is_relative_to(self.path):
            raise ValueError('Write outside isolated output: ' + str(path))
        info = self.path.stat()
        if (info.st_dev, info.st_ino) != self.identity:
            raise ValueError('Isolated output ownership changed')
        self._pin(path.parent)
        return path

    def activate(self):
        self.token = _ACTIVE.set(self)
        return self

    def unpin_tree(self, path):
        if path == self.path:
            return
        if self.handles:
            close = ctypes.WinDLL('kernel32', use_last_error=True).CloseHandle
            close.argtypes = [ctypes.c_void_p]
            for parent in list(self.handles):
                if parent.is_relative_to(path):
                    close(self.handles.pop(parent))

    def close(self):
        if hasattr(self, 'token'):
            _ACTIVE.reset(self.token)
            del self.token
        if self.handles:
            close = ctypes.WinDLL('kernel32', use_last_error=True).CloseHandle
            close.argtypes = [ctypes.c_void_p]
            close.restype = ctypes.c_int
            for handle in reversed(list(self.handles.values())):
                close(handle)
            self.handles.clear()

    def __enter__(self):
        return self.reserve().activate()

    def __exit__(self, *unused):
        self.close()


def active_output():
    return _ACTIVE.get()


def tool_environment(env=None):
    scope = active_output()
    if scope is None:
        return env
    result = dict(os.environ if env is None else env)
    temp = scope.check(scope.path / 'workspace' / 'temp')
    temp.mkdir(exist_ok=True)
    for key in ('TEMP', 'TMP', 'TMPDIR', 'XDG_CACHE_HOME', 'DOTNET_CLI_HOME'):
        result[key] = str(temp)
    result['PYTHONDONTWRITEBYTECODE'] = '1'
    result['JAVA_TOOL_OPTIONS'] = (result.get('JAVA_TOOL_OPTIONS', '') +
                                  ' -Djava.io.tmpdir="%s" -Duser.home="%s"' % (temp, temp)).strip()
    return result
