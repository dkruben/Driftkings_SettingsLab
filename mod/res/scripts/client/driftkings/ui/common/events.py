from Event import SafeEvent
from gui.shared.personality import ServicesLocator
from skeletons.gui.app_loader import GuiGlobalSpaceID


class Events(object):
    def __init__(self):
        self.onBattleLoaded = SafeEvent()
        self.onAltKey = SafeEvent()
        self.onMarkerColorChanged = SafeEvent()
        self.onArmorChanged = SafeEvent()
        self._appLoader = None

    def start(self):
        if self._appLoader is not None:
            return
        loader = ServicesLocator.appLoader
        loader.onGUISpaceEntered += self.onGUISpaceEntered
        self._appLoader = loader

    def stop(self):
        if self._appLoader is None:
            return
        self._appLoader.onGUISpaceEntered -= self.onGUISpaceEntered
        self._appLoader = None

    def onGUISpaceEntered(self, spaceID):
        if spaceID == GuiGlobalSpaceID.BATTLE:
            self.onBattleLoaded()


g_events = Events()
