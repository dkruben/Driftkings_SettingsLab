# -*- coding: utf-8 -*-
"""Gameface presentation of DK Mod Settings: integrated settings window.

The window logic lives in Driftkings.settings.panel.presenter; this module only moves JSON
between the Wulf view models and the presenter.
"""
import json

import BigWorld
import Keys
from frameworks.wulf import ViewModel, ViewSettings, ViewFlags, WindowFlags, WindowLayer
from gui.impl.pub import ViewImpl
from gui.impl.pub.window_impl import WindowImpl
from skeletons.gui.app_loader import GuiGlobalSpaceID

from Driftkings.core.keyboard import keyboard
from Driftkings.core.keycodes import valid_key_code
from Driftkings.settings.panel import core_page, logger
from Driftkings.settings.panel.controls import is_text
from Driftkings.settings.panel.presenter import CORE_ID, MAX_REQUEST, Presenter
from Driftkings.ui.gameface import resource_id

WINDOW_RESOURCE = 'mods/Driftkings/DKModSettings/window'
_JSON = {'separators': (',', ':'), 'allow_nan': False}


class SettingsModel(ViewModel):
    __slots__ = ('onAction',)

    def __init__(self):
        super(SettingsModel, self).__init__(properties=2, commands=1)

    def _initialize(self):
        super(SettingsModel, self)._initialize()
        self._addStringProperty('schema', '{}')
        self._addStringProperty('state', '{}')
        self.onAction = self._addCommand('onAction')


class SettingsView(ViewImpl):
    def __init__(self, controller, presenter):
        self.controller = controller
        self.presenter = presenter
        self.live = False
        self.sentSchema = None
        self.sentRevision = None
        self.updaterState = None
        settings = ViewSettings(resource_id(WINDOW_RESOURCE))
        settings.flags = ViewFlags.VIEW
        settings.model = SettingsModel()
        super(SettingsView, self).__init__(settings)

    def _getEvents(self):
        return ((self.getViewModel().onAction, self.onAction),)

    def _onLoading(self, *args, **kwargs):
        super(SettingsView, self)._onLoading(*args, **kwargs)
        self.live = True
        self.controller.api.registry.subscribe(self.push)
        updater = getattr(self.controller.api, 'updater', None)
        if updater is not None:
            self.updaterState = updater.state
            self.updaterState.subscribe(self.push)
        self.push()

    def _finalize(self):
        self.live = False
        self.controller.api.registry.unsubscribe(self.push)
        if self.updaterState is not None:
            self.updaterState.unsubscribe(self.push)
            self.updaterState = None
        try:
            self.presenter.dispose()
        except Exception:
            logger.exception('Could not discard unsaved settings')
        self.presenter = None
        self.controller = None
        super(SettingsView, self)._finalize()

    def push(self):
        if not self.live:
            return
        revision = (self.presenter.registry.revision, self.controller.api.language)
        schema = json.dumps(self.presenter.schema(), **_JSON) if revision != self.sentRevision else self.sentSchema
        self.sentRevision = revision
        codes = set()
        for mod in self.presenter.registry.mods.values():
            for control in mod.controls:
                if control.type == 'hotkey':
                    for group in self.presenter.session.value(mod.id, control.id):
                        codes.update(group)
        self.presenter.key_names = dict((str(code), BigWorld.keyToString(code)) for code in codes)
        state = json.dumps(self.presenter.state(), **_JSON)
        with self.getViewModel().transaction() as model:
            # The schema is only resent when mods, controls or the language change.
            if schema != self.sentSchema:
                model._setString(0, schema)
                self.sentSchema = schema
            model._setString(1, state)

    def onAction(self, args):
        if not self.live:
            return
        try:
            raw = args.get('data') if isinstance(args, dict) else None
            if not is_text(raw) or len(raw) > MAX_REQUEST:
                raise ValueError('Invalid request')
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError('Invalid request')
        except ValueError:
            logger.warning('Rejected malformed settings request')
            return
        result = self.presenter.handle(data)
        if result.get('restart'):
            if result.get('restartReason') == 'updater':
                if not self.controller.restart(reason='updater'):
                    self.presenter._say('updates.restartBlocked')
                    self.push()
            else:
                self.controller.restart()
            return
        if result['close']:
            window = self.getParentWindow()
            if window is not None:
                window.destroy()
            return
        self.push()


class SettingsWindow(WindowImpl):
    def __init__(self, controller):
        self.controller = controller
        # Fullscreen like the client's notification windows: the view gets the whole client
        # area and the panel is laid out and sized by CSS, independent of resizeViewRem.
        flags = WindowFlags.WINDOW | WindowFlags.WINDOW_MODAL | WindowFlags.WINDOW_FULLSCREEN
        super(SettingsWindow, self).__init__(flags, content=SettingsView(controller, Presenter(controller.api)),
                                             layer=WindowLayer.TOP_WINDOW)

    def _finalize(self):
        if self.controller is not None:
            self.controller.windowClosed(self)
        self.controller = None
        super(SettingsWindow, self)._finalize()


class SettingsController(object):
    """Owns the single settings window; open() is safe to call anytime."""

    def __init__(self):
        self.api = None
        self.window = None
        self.space = None
        self.adapter = None

    def start(self, api):
        self.api = api
        api.window = self
        core_page.subscribe(self.onCoreChanged)
        keyboard.subscribe(self.onKey, interface=True)

    def stop(self):
        core_page.unsubscribe(self.onCoreChanged)
        keyboard.unsubscribe(self.onKey)
        self.close()
        if self.api is not None:
            self.api.window = None
            self.api.window_open = False

    @property
    def is_open(self):
        return self.window is not None

    def canOpen(self):
        if self.api is None:
            return False
        player = BigWorld.player()
        if self.space in (getattr(GuiGlobalSpaceID, 'BATTLE', -1), getattr(GuiGlobalSpaceID, 'REPLAY', -2)):
            return bool(player and getattr(player, 'arena', None) is not None)
        if self.space != GuiGlobalSpaceID.LOBBY:
            return False
        return bool(player and getattr(player, 'arena', None) is None and getattr(player, 'databaseID', None))

    def open(self, *args):
        if self.window is not None or not self.canOpen():
            return False
        try:
            self.api.in_battle = self.space != GuiGlobalSpaceID.LOBBY
            if self.adapter is not None:
                self.adapter.populate()
            self.window = SettingsWindow(self)
            self.api.window_open = True
            self.window.load()
            return True
        except Exception:
            self.window = None
            self.api.window_open = False
            if self.adapter is not None:
                self.adapter.dispose()
            logger.exception('Could not open the settings window')
            return False

    def close(self):
        window, self.window = self.window, None
        if window is not None:
            window.destroy()

    def restart(self, reason=None):
        # Recheck the actual context; never interrupt an active battle.
        player = BigWorld.player()
        if self.space != GuiGlobalSpaceID.LOBBY or (player and getattr(player, 'arena', None) is not None):
            return False
        if reason == 'updater':
            updater = getattr(self.api, 'updater', None)
            if updater is None or not updater.claim_restart():
                return False
        self.close()
        BigWorld.savePreferences()
        import WGC
        WGC.notifyRestart()
        BigWorld.restartGame()
        return True

    def windowClosed(self, window):
        if self.window is window:
            self.window = None
        if self.api is not None:
            self.api.window_open = False
        if self.adapter is not None:
            self.adapter.dispose()

    def onKey(self, event):
        if self.api is None:
            return
        presenter = self.window.content.presenter if self.window is not None else None
        if presenter is not None and presenter.capture:
            capture = presenter.capture
            if not valid_key_code(event.key):
                return
            modifiers = ((Keys.KEY_LCONTROL, Keys.KEY_RCONTROL),
                         (Keys.KEY_LSHIFT, Keys.KEY_RSHIFT), (Keys.KEY_LALT, Keys.KEY_RALT))
            if event.key == Keys.KEY_ESCAPE and event.isKeyDown():
                presenter.capture = None
            else:
                # A primary click belongs to the settings controls (Clear, Cancel,
                # another capture button). It must not end the active capture.
                if event.key == getattr(Keys, 'KEY_LEFTMOUSE', 256):
                    return
                is_modifier = any(event.key in group for group in modifiers)
                if is_modifier and not presenter.registry.mods[capture['mod']].index[capture['key']].metadata.get('allowModifierOnly', False):
                    return
                if is_modifier and event.isKeyDown():
                    self._modifierCapture = (capture, event.key)
                    return
                if not event.isKeyDown():
                    pending = getattr(self, '_modifierCapture', None)
                    if not is_modifier or pending is None or pending[0] is not capture or pending[1] != event.key:
                        return
                groups = [list(group) for group in modifiers if
                          any(BigWorld.isKeyDown(code) for code in group) or is_modifier and event.key in group]
                if not is_modifier:
                    groups.append([int(event.key)])
                try:
                    presenter.session.set(capture['mod'], capture['key'], groups)
                except ValueError:
                    presenter._say('invalidValue', 'error')
                else:
                    presenter.capture = None
            self._modifierCapture = None
            self.window.content.push()
            return
        if not event.isKeyDown():
            return
        shortcut = self.api.get(CORE_ID, 'openKey', [])
        if shortcut and event.key in shortcut[-1] and all(any(code == event.key or BigWorld.isKeyDown(code) for code in group) for group in shortcut):
            if presenter is None:
                self.open()
            else:
                result = presenter.handle({'action': 'close'})
                if result['close']:
                    self.close()
                elif self.window is not None:
                    self.window.content.push()

    def onContextEntered(self, space):
        self.space = space

    def onContextLeft(self, space):
        self.space = None
        self.close()

    def onCoreChanged(self, changes):
        if 'language' in changes and self.adapter is not None and self.window is not None:
            self.adapter.relabel()


controller = SettingsController()

