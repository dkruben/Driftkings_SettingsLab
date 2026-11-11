"""Local build diagnostics: no payloads/locals, explicit inventory failures."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import traceback


def native_path(path):
    """Extended Windows spelling for read-only metadata/hash operations only."""
    path = Path(path).absolute()
    if '..' in path.parts:
        raise ValueError('Parent traversal in diagnostic path')
    text = str(path)
    if os.name == 'nt' and not text.startswith('\\\\?\\'):
        return '\\\\?\\UNC\\' + text[2:] if text.startswith('\\\\') else '\\\\?\\' + text
    return text


def redact(text):
    text = re.sub(r'(?im)(["\']?(?:payload|html)["\']?\s*[:=]\s*).+$', r'\1[REDACTED]', str(text))
    text = re.sub(r'(?i)(bearer\s+)[^\s"\']+', r'\1[REDACTED]', str(text))
    return re.sub(r'(?i)(["\']?(?:password|passwd|token|secret|credential|authorization|payload|html)["\']?\s*[:=]\s*)(?:"[^"\n]*"|\'[^\'\n]*\'|[^\s,;\n]+)',
                  r'\1[REDACTED]', text)


def exception_record(error, scope=None):
    def node(exc, seen):
        if exc is None or id(exc) in seen:
            return None
        seen.add(id(exc))
        return dict(type=type(exc).__name__, message=redact(str(exc)),
                    winerror=getattr(exc, 'winerror', None), errno=getattr(exc, 'errno', None),
                    filename=redact(getattr(exc, 'filename', None)) if getattr(exc, 'filename', None) else None,
                    cause=node(exc.__cause__, seen), context=node(exc.__context__, seen),
                    suppress_context=exc.__suppress_context__)
    return dict(timestamp=datetime.now(timezone.utc).isoformat(),
                phase=getattr(scope, 'phase', None), component=getattr(scope, 'component', None),
                workspace=str(scope.path) if scope else None,
                exception=node(error, set()),
                traceback=redact(''.join(traceback.TracebackException.from_exception(error, capture_locals=False).format(chain=True))))


def inventory_tree(root):
    root = Path(root).absolute()
    # Check every root ancestor before traversal, including long Windows paths.
    def metadata(path):
        return os.lstat(native_path(path))
    for parent in reversed((root,) + tuple(root.parents)):
        info = metadata(parent)
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('Inventory root redirects: ' + str(parent))
    result = dict(timestamp=datetime.now(timezone.utc).isoformat(), root=str(root),
                  file_count=0, hashed_count=0, unhashed_count=0, unknown_count=0,
                  entries={}, errors=[], complete=True)
    def failure(path, operation, error):
        result['errors'].append(dict(path=path, operation=operation, type=type(error).__name__,
                                     message=redact(error), winerror=getattr(error, 'winerror', None)))
    def visit(folder):
        try:
            with os.scandir(native_path(folder)) as stream:
                names = sorted(item.name for item in stream)
        except OSError as error:
            failure(folder.relative_to(root).as_posix(), 'scandir', error)
            return
        for name in names:
            path = folder / name
            relative = path.relative_to(root).as_posix()
            entry = dict(kind='unknown', sha256=None)
            try:
                info = metadata(path)
                if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
                    entry['kind'] = 'blocked_link'
                    failure(relative, 'boundary', ValueError('Link/reparse point not followed'))
                elif stat.S_ISDIR(info.st_mode):
                    visit(path)
                    continue
                elif stat.S_ISREG(info.st_mode):
                    entry.update(kind='file', size=info.st_size)
                    result['file_count'] += 1
                    digest = hashlib.sha256()
                    with open(native_path(path), 'rb') as stream:
                        for block in iter(lambda: stream.read(1024 * 1024), b''):
                            digest.update(block)
                    entry['sha256'] = digest.hexdigest()
                    result['hashed_count'] += 1
                else:
                    failure(relative, 'type', ValueError('Unsupported filesystem entry'))
            except OSError as error:
                failure(relative, 'read' if entry['kind'] == 'file' else 'lstat', error)
                if entry['kind'] == 'unknown':
                    result['unknown_count'] += 1
            result['entries'][relative] = entry
    visit(root)
    result['unhashed_count'] = result['file_count'] - result['hashed_count']
    result['complete'] = not result['errors'] and not result['unhashed_count'] and not result['unknown_count']
    return result


def record_failure(scope, report, error, writer):
    """Never replace the original exception if any diagnostic writer fails."""
    record = exception_record(error, scope)
    report.update(status='failed', error=record['exception']['message'], failure=record)
    failures = []
    tasks = [
        (scope.path / 'diagnostics/error.json', lambda: record),
        (scope.path / 'workspace/build-report.json', lambda: report),
        (scope.path / 'diagnostics/state.json', lambda: dict(status='failed', failure=record)),
        (scope.path / 'diagnostics/inventory.json', lambda: inventory_tree(scope.path)),
    ]
    for path, value in tasks:
        try:
            writer(path, value())
        except Exception as diagnostic_error:
            failures.append(dict(path=str(path), error=redact(diagnostic_error)))
    if failures:
        error.add_note('Diagnostic recording failed: ' + redact(json.dumps(failures)))
        try:
            sys.stderr.write(redact(json.dumps(dict(original=record, diagnostic_errors=failures))) + '\n')
        except Exception:
            pass
    return record
