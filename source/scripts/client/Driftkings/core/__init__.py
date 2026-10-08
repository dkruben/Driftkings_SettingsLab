# -*- coding: utf-8 -*-
import importlib
import logging

LOG = logging.getLogger('Driftkings.Loader')


class Core(object):
    def __init__(self, names=None, importer=None, services=None, hook_manager=None, context_factory=None):
        if names is None:
            from Driftkings.component_list import COMPONENTS
            names = COMPONENTS
        self.names = tuple(names)
        self.groups = dict((scope, tuple(name for name in self.names if name.startswith(scope + '.')))
                           for scope in ('components', 'battle', 'lobby'))
        if hook_manager is None and importer is None:
            from Driftkings.core.hooks import hooks
            hook_manager = hooks
        self.contexts = None
        self.hooks = hook_manager
        self.importer = importer or importlib.import_module
        self.modules = []
        self.started = False
        self.closed = False
        self.failures = []
        if services is None:
            if context_factory is None:
                from Driftkings.core.contexts import Contexts
                context_factory = Contexts
            from Driftkings.views import BattleViews
            from Driftkings.views.hangar.windows import WindowViews
            from Driftkings.settings import SettingsService
            from Driftkings.core.keyboard import keyboard
            from Driftkings.core.callbacks import callbacks
            from Driftkings.core.updater import UpdaterService
            services = (keyboard, callbacks, WindowViews(), BattleViews(), SettingsService(), UpdaterService())
        self.services = tuple(services)
        self.context_factory = context_factory
        self.initialized = []
        self.cleaned = set()


    def start(self):
        if self.started or self.closed:
            return
        self.started = True
        for name in self.names:
            try:
                if self.hooks is not None:
                    self.hooks.current = 'Driftkings.' + name
                module = self.importer('Driftkings.' + name)
                self.modules.append((name, module))
            except Exception:
                self.failures.append(name)
                LOG.exception('Could not import component %s', name)
                if self.hooks is not None:
                    self.hooks.deactivate('Driftkings.' + name)
            finally:
                if self.hooks is not None:
                    self.hooks.current = None
        for service in self.services:
            try:
                if hasattr(service, 'registerModule'):
                    for name, module in self.modules:
                        service.registerModule(module)
                if hasattr(service, 'register'):
                    for name, module in self.modules:
                        for definition in getattr(module, 'getBattleViews', lambda: ())():
                            service.register(*definition)
                service.start()
            except Exception:
                self.failures.append(service.__class__.__name__)
                LOG.exception('Could not start Core service')
        for name, module in self.modules:
            try:
                if self.hooks is not None:
                    self.hooks.current = 'Driftkings.' + name
                    self.hooks.activate('Driftkings.' + name)
                callback = getattr(module, 'init', None)
                if callback is not None:
                    callback()
                self.initialized.append((name, module))
            except Exception:
                self.failures.append(name)
                LOG.exception('Could not initialize component %s', name)
                self._stopComponent(name, module)
            finally:
                if self.hooks is not None:
                    self.hooks.current = None
        if self.context_factory is not None:
            try:
                owners = self.initialized + [(service.__class__.__name__, service) for service in self.services
                                             if hasattr(service, 'onContextEntered')]
                self.contexts = self.context_factory(owners)
                self.contexts.start()
            except Exception:
                self.failures.append('Contexts')
                LOG.exception('Could not start Core contexts')
        if self.failures:
            LOG.warning('Initialized %d/%d components; %d failures',len(self.initialized), len(self.names), len(self.failures))

    def stop(self):
        if self.closed:
            return
        self.closed = True
        if self.contexts is not None:
            try:
                self.contexts.stop()
            except Exception:
                LOG.exception('Could not stop Core contexts')
        for name, module in reversed(self.modules):
            self._stopComponent(name, module)
        for service in reversed(self.services):
            try:
                service.stop()
            except Exception:
                LOG.exception('Could not stop Core service')
        self.modules = []
        self.started = False

    def _stopComponent(self, name, module):
        if name in self.cleaned:
            return
        self.cleaned.add(name)
        if self.hooks is not None:
            self.hooks.deactivate('Driftkings.' + name)
        try:
            callback = getattr(module, 'fini', None)
            if callback is not None:
                callback()
        except Exception:
            LOG.exception('Could not shut down component %s', name)
        finally:
            # Remove any declarations made during a failed component's cleanup.
            if self.hooks is not None:
                self.hooks.deactivate('Driftkings.' + name)
