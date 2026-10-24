# -*- coding: utf-8 -*-
"""Shared lifecycle for owned Gameface children of the native battle HUD."""
import weakref

from driftkings.settings.service import settings_service
from driftkings.views.hangar.common import publish_card


class BattleCardAdapter(object):
    def __init__(self, feature, namespace, log, title, active=False):
        self.feature = feature
        self.namespace = namespace
        self.log = log
        self.title = title
        self.active = active
        self.visible = True
        self.hudVisible = True
        self.views = weakref.WeakKeyDictionary()
        self.installed = False

    def install(self):
        if self.installed:
            return
        from frameworks.wulf import ViewModel
        from gui.impl.battle.random.hud import RandomHUDView
        from gui.impl.pub.view_component import ViewComponent
        from gui.shared import EVENT_BUS_SCOPE, events

        from driftkings.core.hooks import override
        from driftkings.interface_catalog import gameface_spec
        from driftkings.ui.gameface import attach_assets, resource_id
        adapter = self

        class BattleCardModel(ViewModel):
            def __init__(self):
                super(BattleCardModel, self).__init__(properties=3, commands=1)

            def _initialize(self):
                super(BattleCardModel, self)._initialize()
                self._addStringProperty('payload', '{}')
                self.onSavePosition = self._addCommand('onSavePosition')
                attach_assets(self, adapter.feature)

        class BattleCardView(ViewComponent):
            def __init__(self, resource):
                self._lastPayload = None
                self._guiVisible = True
                self._cursorVisible = False
                self._ready = False
                self._attached = False
                self._lastVisible = None
                super(BattleCardView, self).__init__(layoutID=resource, model=BattleCardModel)

            def _onLoaded(self, *args, **kwargs):
                super(BattleCardView, self)._onLoaded(*args, **kwargs)
                import GUI
                self._cursorVisible = bool(GUI.mcursor().visible)
                self._ready = True
                adapter.log.info('Gameface battle panel loaded')
                adapter.refresh()

            def _getEvents(self):
                return tuple(super(BattleCardView, self)._getEvents()) + (
                    (self.getViewModel().onSavePosition, self._savePosition),)

            def _savePosition(self, args):
                adapter.savePosition(self, args)

            def _getListeners(self):
                return tuple(super(BattleCardView, self)._getListeners()) + (
                    (events.GameEvent.GUI_VISIBILITY, self._visibility, EVENT_BUS_SCOPE.BATTLE),
                    (events.GameEvent.SHOW_CURSOR, self._showCursor, EVENT_BUS_SCOPE.GLOBAL),
                    (events.GameEvent.HIDE_CURSOR, self._hideCursor, EVENT_BUS_SCOPE.GLOBAL))

            def _showCursor(self, event):
                self._cursorVisible = True
                adapter.refresh()

            def _hideCursor(self, event):
                self._cursorVisible = False
                adapter.refresh()

            def _visibility(self, event):
                self._guiVisible = bool(event.ctx['visible'])
                adapter.refresh()

            def _finalize(self):
                self._ready = False
                for parent, child in list(adapter.views.items()):
                    if child is self:
                        adapter.views.pop(parent, None)
                super(BattleCardView, self)._finalize()

        def children(original, parent, *args, **kwargs):
            native = original(parent, *args, **kwargs)
            result = dict.fromkeys(native) if isinstance(native, tuple) else dict(native)
            try:
                resource = resource_id(gameface_spec(adapter.feature)['resource'])
                if resource == -1:
                    adapter.log.warning('%s battle resource is unavailable', adapter.title)
                    return result
                if resource in result:
                    adapter.log.warning('%s battle resource already has an owner', adapter.title)
                    return result
                def create():
                    child = BattleCardView(resource)
                    adapter.views[parent] = child
                    adapter.log.info('Gameface battle panel created')
                    return child
                result[resource] = create
            except Exception:
                adapter.log.exception('Could not attach %s Gameface battle panel', adapter.title)
            return result

        # The shared installer still declares this hook on behalf of its feature.
        setattr(children, '__module__', self.__class__.__module__)
        override(RandomHUDView, '_getChildComponents')(children)
        self.connectSignals()
        self.installed = True
        self.onInstalled()

    def connectSignals(self):
        settings_service.onModSettingsChanged.connect(self.onSettingsChanged, self.namespace)

    def disconnectSignals(self):
        settings_service.onModSettingsChanged.disconnect(self.onSettingsChanged)

    def onInstalled(self):
        pass

    def beforeDispose(self):
        pass

    def dispose(self):
        self.beforeDispose()
        self.disconnectSignals()
        resource = self.resourceID()
        for parent, child in list(self.views.items()):
            if parent.getChildView(resource) is child:
                child.setEnabled(False)
                child.destroy()
        self.views.clear()
        self.installed = False

    def resourceID(self):
        from driftkings.interface_catalog import gameface_spec
        from driftkings.ui.gameface import resource_id
        return resource_id(gameface_spec(self.feature)['resource'])

    def savePosition(self, child, args):
        raise NotImplementedError

    def onSettingsChanged(self, *args):
        self.refresh()

    def setBattleHudVisible(self, visible):
        self.hudVisible = visible
        self.refresh()

    def setupSize(self, *args):
        self.refresh()

    def setVisible(self, visible):
        if self.visible != visible:
            self.visible = visible
            self.refresh()

    def publish(self, payload, config, enabled):
        resource = self.resourceID()
        for parent, child in list(self.views.items()):
            # Native child preparation can run before setChildView has returned.
            # Do not mistake a not-yet-attached child for an external replacement.
            if not child._ready:
                continue
            current = parent.getChildView(resource)
            if current is None and not child._attached:
                continue
            if current is not child:
                self.views.pop(parent, None)
                continue
            child._attached = True
            outgoing = dict(payload)
            outgoing['config'] = dict(config, visible=bool(enabled and child._guiVisible),
                                      draggable=bool(enabled and child._guiVisible and child._cursorVisible
                                                     and not config.get('locked', True)))
            try:
                publish_card(child, outgoing)
                visible = outgoing['config']['visible']
                if visible != child._lastVisible:
                    self.log.info('Gameface battle panel visible=%s state=%s', visible, outgoing.get('state'))
                    child._lastVisible = visible
            except Exception:
                self.log.exception('Could not publish %s battle data', self.title)
