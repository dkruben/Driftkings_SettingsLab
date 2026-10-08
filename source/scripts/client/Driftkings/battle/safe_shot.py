# -*- coding: utf-8 -*-
from Avatar import PlayerAvatar
from gui.Scaleform.daapi.view.battle.classic.stats_exchange import FragsCollectableStats

from Driftkings._constants import GLOBAL, SAFE_SHOT
from Driftkings.common import getPlayer, getTarget, serverTime, checkKeys, sendPanelMessage, sendChatMessage
from Driftkings.core.callbacks import callback
from Driftkings.core.hooks import override
from Driftkings.core.keyboard import keyboard
from Driftkings.settings.service import settings_service
from Driftkings.settings.templates.battle.safe_shot import SafeShotSettings as Settings


class SafeShotController(object):
    def __init__(self, config):
        self.config = config
        self.isEventBattle = False
        self.deadDict = {}
        self.isKeyPressed = True
        self._battleStarted = False
        # overrides methods
        override(FragsCollectableStats, 'addVehicleStatusUpdate', self.new__addVehicleStatusUpdate)
        override(PlayerAvatar, 'shoot', self.new__shoot)
        override(PlayerAvatar, 'shootDualGun', self.new__shootDualGun)
        override(PlayerAvatar, 'onBecomePlayer', self.new__onBecomePlayer)
        override(PlayerAvatar, '_PlayerAvatar__destroyGUI', self.new__destroyGUI)
        override(PlayerAvatar, '_PlayerAvatar__startGUI', self.new__startGUI)


    def isShotAllowed(self):
        if not (settings_service.getComponentDict(self.config)[GLOBAL.ENABLED] and self.isKeyPressed and not self.isEventBattle):
            return True
        target = getTarget()
        player = getPlayer()
        if target is None or player is None:
            if settings_service.getComponentDict(self.config)[SAFE_SHOT.WASTE_SHOT_BLOCK]:
                sendPanelMessage(settings_service.getComponentDict(self.config)[SAFE_SHOT.CLIENT_MESSAGES]['wasteShotBlockedMessage'], 'Yellow')
                return False
        elif hasattr(target.publicInfo, 'team'):
            if settings_service.getComponentDict(self.config)[SAFE_SHOT.TEAM_SHOT_BLOCK] and (player.team == target.publicInfo.team) and target.isAlive():
                if not (settings_service.getComponentDict(self.config)[SAFE_SHOT.TEAM_KILLER_SHOT_UNBLOCK] and player.guiSessionProvider.getArenaDP().isTeamKiller(target.id)):
                    sendChatMessage(settings_service.getComponentDict(self.config)[SAFE_SHOT.CHAT_MESSAGES].replace('{name}', target.publicInfo.name).replace('{vehicle}', target.typeDescriptor.type.shortUserString), 1, 2)
                    sendPanelMessage(settings_service.getComponentDict(self.config)[SAFE_SHOT.CLIENT_MESSAGES]['teamShotBlockedMessage'], 'Yellow')
                    return False
            elif settings_service.getComponentDict(self.config)[SAFE_SHOT.DEAD_SHOT_BLOCK] and (not target.isAlive()) and ((settings_service.getComponentDict(self.config)[SAFE_SHOT.DEAD_SHOT_BLOCK_TIME_OUT] == 0) or ((serverTime() - self.deadDict.get(target.id, 0)) < settings_service.getComponentDict(self.config)[SAFE_SHOT.DEAD_SHOT_BLOCK_TIME_OUT])):
                sendPanelMessage(settings_service.getComponentDict(self.config)[SAFE_SHOT.CLIENT_MESSAGES]['deadShotBlockedMessage'], 'Yellow')
                return False
        return True

    def start_battle(self):
        if self._battleStarted:
            return
        self._battleStarted = True
        self.isKeyPressed = True
        keyboard.subscribe(self.keyPressed)

    def endBattle(self):
        if not self._battleStarted:
            return
        self._battleStarted = False
        keyboard.unsubscribe(self.keyPressed)

    def keyPressed(self, event):
        if not settings_service.getComponentDict(self.config)[GLOBAL.ENABLED]:
            return
        if checkKeys(settings_service.getComponentDict(self.config)[SAFE_SHOT.DISABLE_KEY]) and event.isKeyDown():
            self.isKeyPressed = not self.isKeyPressed
            if settings_service.getComponentDict(self.config)[SAFE_SHOT.TRIGGER_MESSAGE]:
                sendPanelMessage(self.config.i18n['UI_triggerText_enabled'] if self.isKeyPressed else self.config.i18n['UI_triggerText_disabled'], 'Green' if self.isKeyPressed else 'Red')

    def new__addVehicleStatusUpdate(self, func, orig, vInfoVO):
        func(orig, vInfoVO)
        if not vInfoVO.isAlive() and settings_service.getComponentDict(self.config)[GLOBAL.ENABLED] and settings_service.getComponentDict(self.config)[SAFE_SHOT.DEAD_SHOT_BLOCK]:
            self.deadDict.update({vInfoVO.vehicleID: serverTime()})

    def new__shoot(self, func, orig, isRepeat=False):
        if self.isShotAllowed():
            func(orig, isRepeat)

    def new__shootDualGun(self, func, orig, chargeActionType, isPrepared=False, isRepeat=False):
        if self.isShotAllowed():
            func(orig, chargeActionType, isPrepared, isRepeat)

    def new__onBecomePlayer(self, func, orig):
        func(orig)
        self.isEventBattle = getPlayer().guiSessionProvider.arenaVisitor.gui.isEventBattle()

    def new__startGUI(self, func, *args):
        func(*args)
        self.start_battle()
        support.start_battle()

    def new__destroyGUI(self, func, orig, *args):
        func(orig, *args)
        self.endBattle()
        self.isEventBattle = False
        self.isKeyPressed = True
        self.deadDict.clear()


class Support(object):
    @staticmethod
    def message():
        sendPanelMessage(config.i18n['UI_battle_activateMessage'])

    def start_battle(self):
        if settings_service.getComponentDict(config)[GLOBAL.ENABLED] and settings_service.getComponentDict(config)[SAFE_SHOT.ACTIVATE_MESSAGE]:
            callback(5.0, self.message)


config = Settings()
controller = SafeShotController(config)
support = Support()


def fini():
    controller.endBattle()
