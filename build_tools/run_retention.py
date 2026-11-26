"""Run retention for build/runs: preview by default, deletion only with --apply.

Policy (development runs are regenerable; release and unknown runs are never touched):
- The newest KEEP_SUCCESSFUL successful development runs per target keep their WOTMOD and evidence;
  their workspace intermediates are removed after verification.
- Older successful development runs are removed completely.
- Failed runs keep their evidence for FAILED_DAYS; their workspace is trimmed to the job and result files.
- Everything else is protected: active or incomplete runs, release runs, runs marked with evidence/RETAIN,
  unknown or unreadable directories, links, runs referenced from build/releases, and runs whose artifacts
  no longer match their recorded hashes.
"""
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import stat
from pathlib import Path

from build_tools.validate_build_data import read_json

KEEP_SUCCESSFUL = 3
FAILED_DAYS = 14
ACTIVE_WINDOW_MINUTES = 30
RETAIN_MARKER = 'RETAIN'
RUN_NAME = re.compile(r'\d{8}T\d{6}Z-[0-9a-f]{8}')
RUN_LAYOUT = {'workspace', 'output', 'evidence'}
DEVELOPMENT_MODES = ('dev', 'debug')
KEEP_FAILED_WORKSPACE = ('-job.json', '-result.json')
MAX_REFERENCE_BYTES = 5 * 1024 * 1024


def is_link(path):
    """Symlinks and Windows reparse points, including junctions."""
    info = os.lstat(path)
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & 0x400)


def has_link(path):
    """Walk without following links; any link or reparse point anywhere in the tree is a refusal."""
    if is_link(path):
        return True
    if not os.path.isdir(path):
        return False
    with os.scandir(path) as entries:
        for entry in entries:
            if is_link(entry.path) or (entry.is_dir(follow_symlinks=False) and has_link(entry.path)):
                return True
    return False


def tree_size(path):
    if os.path.isfile(path) and not os.path.islink(path):
        return os.lstat(path).st_size
    total = 0
    with os.scandir(path) as entries:
        for entry in entries:
            total += tree_size(entry.path)
    return total


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def run_started(name):
    return dt.datetime.strptime(name[:16], '%Y%m%dT%H%M%SZ').replace(tzinfo=dt.timezone.utc)


def completed_at(name, state, now):
    """Completion time when the record is trustworthy: parseable, not before the run started, not in the future.
    Otherwise the run's start time, which is the conservative choice for age."""
    started = run_started(name)
    for value in (state.get('completed'), (state.get('failure') or {}).get('timestamp')):
        try:
            moment = dt.datetime.fromisoformat(value)
        except (TypeError, ValueError):
            continue
        if moment.tzinfo is None:
            continue
        if started <= moment <= now:
            return moment
    return started


def recently_touched(path, now):
    """A run whose files changed in the last minutes may still be written by an active build."""
    newest = max(os.lstat(p).st_mtime for p in (str(path), str(path / 'evidence'), str(path / 'evidence/state.json'))
                 if os.path.exists(p))
    return now - dt.datetime.fromtimestamp(newest, dt.timezone.utc) < dt.timedelta(minutes=ACTIVE_WINDOW_MINUTES)


def referenced_by_releases(root):
    """Run IDs named by, and WOTMOD hashes present in, the canonical release folders."""
    ids, hashes = set(), set()
    releases = root / 'build/releases'
    if not releases.is_dir() or has_link(releases):
        return ids, hashes
    for dirpath, _, filenames in os.walk(releases):
        for name in filenames:
            path = Path(dirpath) / name
            if name == 'driftkings.wotmod':
                hashes.add(file_sha256(path))
            elif name.endswith('.json') and os.path.getsize(path) <= MAX_REFERENCE_BYTES:
                ids.update(re.findall(r'\d{8}T\d{6}Z-[0-9a-f]{8}', path.read_text(encoding='utf-8', errors='replace')))
    return ids, hashes


def decide(runs, name, now, targets, references):
    """Classify one run directory. Returns a decision dict; unknown or unreadable state is protected."""
    base = dict(run=name, target=None, mode=None, action='protect', reason='', bytes=0, paths=[])
    path = runs / name
    def protect(reason):
        base.update(action='protect', reason=reason)
        return base
    if not RUN_NAME.fullmatch(name):
        return protect('unrecognized directory name')
    try:
        if not path.is_dir() or has_link(path):
            return protect('not a plain directory or contains links')
        children = {entry.name for entry in os.scandir(path)}
        if not children or not children <= RUN_LAYOUT or 'evidence' not in children:
            return protect('not in the run layout (historical or unknown)')
        evidence = path / 'evidence'
        if (evidence / RETAIN_MARKER).exists():
            return protect('retained as validation evidence')
        if not (evidence / 'build-report.json').is_file():
            return protect('invalid run metadata')
        report = read_json(evidence / 'build-report.json')
        if not isinstance(report, dict):
            return protect('invalid run metadata')
        # state.json arrived with the unified layout; earlier unified runs are judged by their report alone.
        if (evidence / 'state.json').exists():
            state = read_json(evidence / 'state.json')
        else:
            state = {'status': 'complete' if report.get('status') == 'success' else report.get('status')}
        if not isinstance(state, dict):
            return protect('invalid run metadata')
        if report.get('run_id') != name or report.get('schema') != 1:
            return protect('run metadata does not match its directory')
        base.update(target=report.get('target'), mode=report.get('mode'))
        if state.get('status') == 'running' or report.get('status') == 'running':
            return protect('active or incomplete run')
        if recently_touched(path, now):
            return protect('recently modified: possible active build')
        if report.get('mode') == 'release':
            return protect('release run')
        if report.get('mode') not in DEVELOPMENT_MODES or report.get('target') not in targets:
            return protect('unknown mode or target')
        if name in references[0] or (path / 'output' / 'driftkings.wotmod').is_file() and \
                file_sha256(path / 'output' / 'driftkings.wotmod') in references[1]:
            return protect('referenced by a canonical release')
        started = run_started(name)
        workspace = path / 'workspace'
        if state.get('status') == 'complete' and report.get('status') == 'success':
            wotmod = path / 'output' / 'driftkings.wotmod'
            recorded = (report.get('artifacts') or {}).get('driftkings.wotmod', {}).get('sha256')
            if not wotmod.is_file() or file_sha256(wotmod) != recorded:
                return protect('artifact does not match its recorded hash')
            if {p.name for p in (path / 'output').iterdir()} != {'driftkings.wotmod'}:
                return protect('development output contains unexpected files')
            base.update(action='successful', started=started.isoformat())
            base['bytes'] = tree_size(workspace) if workspace.exists() else 0
            return base
        if state.get('status') == 'failed' and report.get('status') == 'failed':
            if now - completed_at(name, state, now) > dt.timedelta(days=FAILED_DAYS):
                base.update(action='remove', reason='failed run older than %d days' % FAILED_DAYS,
                            bytes=tree_size(path), paths=[str(path)])
                return base
            # Intermediates named by the preserved evidence are kept as diagnosis evidence.
            text = ' '.join(p.read_text(encoding='utf-8', errors='replace') for p in evidence.glob('*.json')
                            if p.stat().st_size <= MAX_REFERENCE_BYTES)
            trimmed = [entry for entry in os.scandir(workspace)
                       if not entry.name.endswith(KEEP_FAILED_WORKSPACE)
                       and not any(ref in text for ref in ('workspace/' + entry.name, 'workspace\\' + entry.name))
                       ] if workspace.is_dir() else []
            base.update(action='trim', reason='failed run within %d days: keep job and result files' % FAILED_DAYS,
                        bytes=sum(tree_size(e.path) for e in trimmed), paths=[e.path for e in trimmed])
            return base
        return protect('state and report disagree')
    except (OSError, ValueError, TypeError, KeyError) as error:
        return protect('unreadable run metadata: %s' % type(error).__name__)


def plan(root, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    runs = root / 'build/runs'
    if not runs.is_dir():
        return []
    config = read_json(root / 'build_data/build_config.json')
    targets = set(config.get('targets', {}))
    references = referenced_by_releases(root)
    decisions = []
    for entry in sorted(os.scandir(runs), key=lambda e: e.name):
        decisions.append(decide(runs, entry.name, now, targets, references))
    # Latest successful development runs per target keep their WOTMOD; the rest of that target's successes go.
    successful = {}
    for item in decisions:
        if item['action'] == 'successful':
            successful.setdefault(item['target'], []).append(item)
    for items in successful.values():
        items.sort(key=lambda item: item['run'], reverse=True)
        for rank, item in enumerate(items):
            workspace = runs / item['run'] / 'workspace'
            if rank < KEEP_SUCCESSFUL:
                if workspace.exists():
                    item.update(action='trim', paths=[str(workspace)],
                                reason='latest %d successful runs for target: remove intermediates, keep WOTMOD and evidence'
                                % KEEP_SUCCESSFUL)
                else:
                    item.update(action='keep', paths=[], reason='latest %d successful runs for target' % KEEP_SUCCESSFUL)
            else:
                item.update(action='remove', reason='older than the latest %d successful runs for target'
                            % KEEP_SUCCESSFUL, bytes=tree_size(runs / item['run']), paths=[str(runs / item['run'])])
    return decisions


def execute(root, decisions, now=None):
    """Delete only what the decisions name, after re-checking each run's metadata, ownership and links."""
    runs = (root / 'build/runs').resolve()
    removed, freed = [], 0
    for item in decisions:
        if item['action'] not in ('remove', 'trim'):
            continue
        path = runs / item['run']
        require_inside(path, runs)
        if has_link(path):
            raise ValueError('Refusing to delete a run containing links: ' + item['run'])
        fresh = decide(runs, item['run'], now or dt.datetime.now(dt.timezone.utc),
                       set(read_json(root / 'build_data/build_config.json').get('targets', {})),
                       referenced_by_releases(root))
        if fresh['action'] == 'protect':
            removed.append(item['run'] + ' (skipped: now protected, ' + fresh['reason'] + ')')
            continue  # status or ownership changed since the preview: skip, never guess
        for target in item['paths']:
            entry = Path(target)
            require_inside(entry, runs)
            if has_link(entry):
                raise ValueError('Refusing to delete a link: ' + str(entry))
            freed += tree_size(entry) if entry.exists() else 0
            if entry.is_dir():
                shutil.rmtree(entry)
            elif entry.exists():
                entry.unlink()
        removed.append(item['run'] + ' (' + item['action'] + ')')
    return removed, freed


def require_inside(path, runs):
    resolved = Path(path).resolve()
    if resolved == runs or not resolved.is_relative_to(runs) or '..' in Path(path).parts:
        raise ValueError('Path escapes build/runs: ' + str(path))


def human(size):
    for unit in ('B', 'KiB', 'MiB', 'GiB'):
        if size < 1024 or unit == 'GiB':
            return '%.1f %s' % (size, unit)
        size /= 1024.0


def run_retention(root, apply=False, now=None):
    decisions = plan(root, now)
    mode = 'APPLY' if apply else 'PREVIEW (no changes made)'
    print('Run retention %s: %d directories under build/runs' % (mode, len(decisions)))
    for item in decisions:
        print('  %-28s %-8s %-10s %-9s %s' % (item['run'], item['target'] or '-', item['mode'] or '-',
                                              item['action'], item['reason']))
    removable = [item for item in decisions if item['action'] == 'remove']
    trimmable = [item for item in decisions if item['action'] == 'trim']
    protected = [item for item in decisions if item['action'] == 'protect']
    estimated = sum(item['bytes'] for item in removable + trimmable)
    print('Eligible for removal: %d run(s); workspace trim: %d run(s)' % (len(removable), len(trimmable)))
    print('Estimated recoverable space: %s (%d bytes)' % (human(estimated), estimated))
    print('Protected: %d run(s)' % len(protected))
    if apply:
        removed, freed = execute(root, decisions, now)
        print('Removed or trimmed: %s' % (', '.join(removed) or 'nothing'))
        print('Freed: %s (%d bytes)' % (human(freed), freed))
    return decisions
