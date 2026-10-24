# -*- coding: utf-8 -*-
"""Schedule the optional map package; the native worker applies it after exit."""
import hashlib
import json
import os
import subprocess
import xml.etree.ElementTree as ET
import zipfile

from driftkings._constants import BATTLE_PREFERENCES, GLOBAL
from driftkings.core.updater.installer import read_resource
from driftkings.core.updater.versioning import normalize_game_version
from driftkings.logger import get_logger
from driftkings.settings.service import settings_service

LOG = get_logger('Driftkings.Fog')
RESOURCE = 'gui/driftkings/fog/Driftkings.FogPackage.exe'
INFO = 'gui/driftkings/fog/helper.json'
PACKAGE = 'Driftkings.RemoveFog.wotmod'
_controller = None


def coordinated_restart():
    """None means no fog work; True means its worker now owns the restart."""
    if _controller is None or _controller.process is None:
        return None
    return _controller.request_restart()


def source_stamp(root):
    """Match the native generator's inventory stamp without reading map content."""
    import re
    folder = os.path.join(root, 'res', 'packages')
    lines = []
    for name in sorted(os.listdir(folder)):
        if not re.match(r'^\d+_.+\.pkg\Z', name) or name.endswith('_hd.pkg'):
            continue
        stat = os.stat(os.path.join(folder, name))
        lines.append('%s:%d:%d\n' % (name, stat.st_size, int(stat.st_mtime)))
    return hashlib.sha256(''.join(lines).encode('utf-8')).hexdigest()


def package_current(path, stamp):
    if not os.path.isfile(path):
        return False
    with zipfile.ZipFile(path) as archive:
        info = archive.getinfo('meta.xml')
        if info.file_size > 8192:
            raise ValueError('Fog metadata exceeds limit')
        meta = ET.fromstring(archive.read(info))
        if meta.findtext('id') != 'driftkings.removefog':
            raise ValueError('Optional package belongs to another mod')
        return meta.findtext('sources') == stamp


class FogPackageController(object):
    def __init__(self, config):
        self.config = config
        self.process = None
        self.token = None
        self.notice = None
        self.previous_error = False
        self.active = False
        self.desired = None
        self.revision = 0
        self.restart_requested = False

    def start(self):
        global _controller
        from helpers import getClientVersion

        from driftkings.common.utils import events
        from driftkings.core.callbacks import callbacks
        self.callbacks = callbacks
        self.root = os.path.abspath(os.getcwd())
        self.version = normalize_game_version(getClientVersion())
        if self.version is None:
            raise ValueError('Unknown client version for fog package')
        self.cache = os.path.join(self.root, 'mods', 'configs', 'driftkings', 'cache', 'fog')
        self.stage = os.path.join(self.cache, 'session-' + str(os.getpid()))
        self.target = os.path.join(self.root, 'mods', self.version, PACKAGE)
        self.active = True
        _controller = self
        self.event = events.LobbyView.populate.after.event
        self.event += self.lobby
        settings_service.onModSettingsChanged.connect(self.changed, BATTLE_PREFERENCES.NAME,
            (GLOBAL.ENABLED, BATTLE_PREFERENCES.REMOVE_FOG))
        self.previous_result()
        self.changed(None, {})

    def previous_result(self):
        if not os.path.isdir(self.cache):
            return
        results = []
        for name in os.listdir(self.cache):
            if not name.startswith('session-'):
                continue
            path = os.path.join(self.cache, name, 'result')
            if os.path.isfile(path):
                results.append((os.path.getmtime(path), path))
        if not results:
            return
        path = max(results)[1]
        if os.path.exists(path + '.reported'):
            return
        with open(path, 'rb') as stream:
            value = stream.read(4096).decode('utf-8-sig', 'replace')
        if value.startswith(self.version + ':error:'):
            LOG.error('Previous fog operation failed: %s', value)
            self.previous_error = True
        else:
            LOG.info('Previous fog operation: %s', value)
        with open(path + '.reported', 'wb') as stream:
            stream.write(b'1')

    def remove_stale_sessions(self, age=86400, limit=20):
        """Keep this session and the latest result; a helper still running keeps its files locked."""
        import time

        from driftkings.core.updater.results import remove_flat_directory
        sessions = []
        for name in os.listdir(self.cache):
            folder = os.path.join(self.cache, name)
            if name.startswith('session-') and os.path.isdir(folder):
                result = os.path.join(folder, 'result')
                sessions.append((os.path.getmtime(result) if os.path.isfile(result) else 0, folder))
        latest = max(sessions)[1] if sessions else None
        threshold = time.time() - age
        removed = 0
        for _, folder in sorted(sessions):
            if removed >= limit:
                break
            if folder in (self.stage, latest) or os.path.getmtime(folder) > threshold:
                continue
            try:
                remove_flat_directory(folder)
                removed += 1
            except Exception:
                LOG.debug('Kept fog session folder %s', folder, exc_info=True)

    def changed(self, component, changes):
        if not self.active:
            return
        desired = bool(self.config.data[GLOBAL.ENABLED] and self.config.data.get(BATTLE_PREFERENCES.REMOVE_FOG, False))
        try:
            if self.process is None:
                if desired and package_current(self.target, source_stamp(self.root)):
                    self.desired = desired
                    return
                if not desired and not os.path.exists(self.target):
                    self.desired = desired
                    return
            if self.desired == desired and self.process is not None and self.process.poll() is None:
                return
            self.schedule(desired)
        except Exception:
            LOG.exception('Could not schedule optional fog package')
            self.notice = 'UI_fog_error'
            self.notify()

    def schedule(self, desired):
        # ResMgr reads stay on the client thread. No Python installation is needed.
        if self.process is not None and self.process.poll() is not None:
            raise RuntimeError('Fog installer exited before the client')
        if self.process is None:
            binary = read_resource(RESOURCE)
            metadata = json.loads(read_resource(INFO).decode('utf-8'))
            if (metadata.get('schema') != 1 or metadata.get('size') != len(binary) or
                    not 0 < len(binary) <= 256 * 1024 or
                    hashlib.sha256(binary).hexdigest() != metadata.get('sha256')):
                raise ValueError('Fog helper identity mismatch')
            if not os.path.isdir(self.stage):
                os.makedirs(self.stage)
            from driftkings.core.updater import windows_files
            windows_files.initialize(read_resource, self.root)
            windows_files.safe_path(self.stage)
            try:
                self.remove_stale_sessions()
            except Exception:
                LOG.debug('Fog session cleanup skipped', exc_info=True)
            helper = os.path.join(self.stage, 'Driftkings.FogPackage.exe')
            descriptor = os.open(helper, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_BINARY', 0), 0o600)
            with os.fdopen(descriptor, 'wb') as output:
                output.write(binary)
                output.flush()
                os.fsync(output.fileno())
        # Persist the last applied selection, including toggles/profile changes.
        self.revision += 1
        if self.revision > 99999999:
            raise ValueError('Fog request revision limit')
        request = os.path.join(self.stage, 'request-%08d.%s' % (self.revision, 'on' if desired else 'off'))
        descriptor = os.open(request, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_BINARY', 0), 0o600)
        with os.fdopen(descriptor, 'wb') as output:
            output.flush()
            os.fsync(output.fileno())
        self.desired = desired
        if self.process is None:
            startup = subprocess.STARTUPINFO()
            startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startup.wShowWindow = 0
            self.process = subprocess.Popen([helper, str(os.getpid()), self.version, self.stage],
                shell=False, startupinfo=startup, creationflags=0x08000000)
        self.notice = 'UI_fog_restart_on' if desired else 'UI_fog_restart_off'
        LOG.info('Fog selection scheduled: enabled=%s client=%s stage=%s', desired, self.version, self.stage)
        if self.token is None:
            self.wait_ready(0)

    def wait_ready(self, attempt):
        self.token = None
        if not self.active:
            return
        if self.process.poll() is not None or attempt >= 600:
            LOG.error('Fog helper did not acknowledge scheduling: %s', self.stage)
            self.notice = 'UI_fog_error'
            self.restart_requested = False
            self.notify()
        elif os.path.isfile(os.path.join(self.stage, 'prepared')):
            self.notify()
            if self.restart_requested:
                self.finish_restart()
        else:
            self.token = self.callbacks.schedule(0.1, lambda: self.wait_ready(attempt + 1))

    def request_restart(self):
        if not self.active or self.process is None or self.process.poll() is not None:
            self.notice = 'UI_fog_error'
            self.notify()
            return False
        self.restart_requested = True
        if self.token is None:
            self.wait_ready(0)
        return True

    def finish_restart(self):
        import BigWorld
        path = os.path.join(self.stage, 'restart')
        try:
            BigWorld.savePreferences()
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_BINARY', 0), 0o600)
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(str(os.getpid()).encode('ascii'))
                stream.flush()
                os.fsync(stream.fileno())
            if self.process.poll() is not None:
                raise RuntimeError('Fog installer exited before coordinated restart')
            LOG.info('Coordinated fog restart confirmed; worker will reopen the client after installation')
            BigWorld.quit()
        except Exception:
            if os.path.exists(path):
                os.remove(path)
            LOG.exception('Could not request coordinated fog restart')
            self.notice = 'UI_fog_error'
            self.notify()
        finally:
            self.restart_requested = False

    def lobby(self, *args, **kwargs):
        self.notify()

    def notify(self):
        if not self.notice and not self.previous_error:
            return
        from driftkings.settings.panel import settings
        if not settings.started or settings.in_battle:
            return
        from gui.shared.personality import ServicesLocator
        from skeletons.gui.app_loader import GuiGlobalSpaceID
        if ServicesLocator.appLoader.getSpaceID() != GuiGlobalSpaceID.LOBBY:
            return
        from gui import SystemMessages
        if self.previous_error:
            SystemMessages.pushMessage(self.config.i18n['UI_fog_error'], type=SystemMessages.SM_TYPE.Information)
            self.previous_error = False
        if self.notice:
            SystemMessages.pushMessage(self.config.i18n[self.notice], type=SystemMessages.SM_TYPE.Information)
        self.notice = None

    def stop(self):
        global _controller
        if _controller is self:
            _controller = None
        self.active = False
        settings_service.onModSettingsChanged.disconnect(self.changed)
        if hasattr(self, 'event'):
            self.event -= self.lobby
        if self.token is not None:
            self.callbacks.cancel(self.token)
            self.token = None
        # The worker deliberately survives shutdown to apply the saved request.
