# -*- coding: utf-8 -*-
"""Shared battle notifications. Wrappers preserve the original game calls.

Player feedback and enemy spotted status come from the session's native feedback and
battle field controllers. The GUI start/stop
wrappers stay: no client event fires at the same moment (onBattleSessionStart is before
the space and input handler exist, onAvatarReady only when loading ends).
"""
from Avatar import PlayerAvatar
from Vehicle import Vehicle
from VehicleGunRotator import VehicleGunRotator

from driftkings.core.hooks import override
from driftkings.core.keyboard import keyboard
from driftkings.core.signals import Signal
from driftkings.logger import get_logger
from driftkings.ui import g_events

LOG = get_logger('Driftkings.BattleEvents')


class BattleEvents(object):
    def __init__(self):
        self.healthBefore = Signal()
        self.healthDetailed = Signal()
        self.appearanceDetailed = Signal()
        self.feedback = Signal()
        self.dispersion = Signal()
        self.loaded = Signal()
        self.started = Signal()
        self.ended = Signal()
        self.appeared = Signal()
        self.health = Signal()
        self.visibility = Signal()
        self.killed = Signal()
        self.key = Signal()
        self.owners = set()
        self.arena = None
        self.hooked = False
        self.bound = False
        self.session = None
        self.feedbackCtrl = None
        self.battleFieldCtrl = None

    def acquire(self, owner):
        if owner in self.owners:
            return
        first = not self.owners
        self.owners.add(owner)
        if not first:
            return
        try:
            if not self.hooked:
                override(PlayerAvatar, '_PlayerAvatar__startGUI', self.startGUI)
                override(PlayerAvatar, '_PlayerAvatar__destroyGUI', self.destroyGUI)
                override(PlayerAvatar, 'vehicle_onAppearanceReady', self.appearanceReady)
                override(Vehicle, 'onHealthChanged', self.healthChanged)
                override(VehicleGunRotator, 'updateRotationAndGunMarker', self.dispersionChanged)
                self.hooked = True
            g_events.onBattleLoaded += self.onLoaded
            self.bound = True
            keyboard.subscribe(self.onKey)
            self.bindSession()
        except Exception:
            self.release(owner)
            raise

    def release(self, owner):
        if owner not in self.owners:
            return
        self.owners.remove(owner)
        if not self.owners:
            self.detachArena()
            self.unbindSession()
            if self.bound:
                g_events.onBattleLoaded -= self.onLoaded
                self.bound = False
            keyboard.unsubscribe(self.onKey)

    def detachArena(self):
        if self.arena is not None:
            self.arena.onVehicleKilled -= self.onKilled
            self.arena = None

    def bindSession(self):
        from helpers import dependency
        from skeletons.gui.battle_session import IBattleSessionProvider
        session = dependency.instance(IBattleSessionProvider)
        session.onBattleSessionStart += self.attachFeedback
        session.onBattleSessionStop += self.detachFeedback
        self.session = session
        # Acquired during a battle: the session already started.
        self.attachFeedback()

    def unbindSession(self):
        self.detachFeedback()
        if self.session is not None:
            self.session.onBattleSessionStart -= self.attachFeedback
            self.session.onBattleSessionStop -= self.detachFeedback
            self.session = None

    def attachFeedback(self):
        self.detachFeedback()
        shared = getattr(self.session, 'shared', None)
        ctrl = getattr(shared, 'feedback', None) if shared is not None else None
        if ctrl is not None:
            ctrl.onPlayerFeedbackReceived += self.onPlayerFeedback
            self.feedbackCtrl = ctrl
        dynamic = getattr(self.session, 'dynamic', None)
        field = getattr(dynamic, 'battleField', None) if dynamic is not None else None
        if field is not None:
            field.onSpottedStatusChanged += self.onSpottedStatus
            self.battleFieldCtrl = field

    def detachFeedback(self):
        if self.feedbackCtrl is not None:
            self.feedbackCtrl.onPlayerFeedbackReceived -= self.onPlayerFeedback
            self.feedbackCtrl = None
        if self.battleFieldCtrl is not None:
            self.battleFieldCtrl.onSpottedStatusChanged -= self.onSpottedStatus
            self.battleFieldCtrl = None

    def onSpottedStatus(self, updated, arenaDP=None):
        # VehicleSpottedStatus: 1 spotted, 2 lost; 0 (default/dead) is left to 'killed'.
        if not self.owners:
            return
        for flags, vo in updated:
            status = getattr(vo, 'spottedStatus', 0)
            if status in (1, 2):
                self.visibility.emit(vo.vehicleID, status == 1)

    def onPlayerFeedback(self, events):
        # Same (avatar, events) shape as before; events are PlayerFeedbackEvent objects
        # already filtered by the client for the controlled vehicle.
        if self.owners:
            import BigWorld
            self.feedback.emit(BigWorld.player(), events)

    def start(self):
        self.acquire(self)

    def stop(self):
        for owner in tuple(self.owners):
            self.release(owner)
        for name in ('started', 'ended', 'loaded', 'appeared', 'health', 'visibility',
                     'killed', 'key', 'dispersion', 'healthBefore', 'healthDetailed',
                     'appearanceDetailed', 'feedback'):
            getattr(self, name).clear()

    def startGUI(self, original, avatar, *args, **kwargs):
        if not self.owners:
            return original(avatar, *args, **kwargs)
        from driftkings.common.utils import events
        events.PlayerAvatar.startGUI.before.event(avatar, *args, **kwargs)
        result = original(avatar, *args, **kwargs)
        arena = getattr(avatar, 'arena', None)
        if arena is not self.arena:
            self.detachArena()
            self.arena = arena
            if arena is not None:
                arena.onVehicleKilled += self.onKilled
        self.started.emit()
        events.PlayerAvatar.startGUI.after.event(avatar, *args, **kwargs)
        return result

    def destroyGUI(self, original, avatar, *args, **kwargs):
        if not self.owners:
            return original(avatar, *args, **kwargs)
        from driftkings.common.utils import events
        events.PlayerAvatar.destroyGUI.before.event(avatar, *args, **kwargs)
        self.ended.emit()
        try:
            result = original(avatar, *args, **kwargs)
        finally:
            self.detachArena()
        events.PlayerAvatar.destroyGUI.after.event(avatar, *args, **kwargs)
        return result

    def appearanceReady(self, original, avatar, vehicle, *args, **kwargs):
        result = original(avatar, vehicle, *args, **kwargs)
        if self.owners:
            self.appeared.emit(vehicle.id)
            self.appearanceDetailed.emit(avatar, vehicle, *args, **kwargs)
        return result

    def healthChanged(self, original, vehicle, health, *args, **kwargs):
        if self.owners:
            self.healthBefore.emit(vehicle, health, *args, **kwargs)
        result = original(vehicle, health, *args, **kwargs)
        if self.owners:
            self.health.emit(vehicle.id, health)
            self.healthDetailed.emit(vehicle, health, *args, **kwargs)
        return result

    def dispersionChanged(self, original, rotator, *args, **kwargs):
        result = original(rotator, *args, **kwargs)
        if self.owners:
            self.dispersion.emit(rotator)
        return result

    def onLoaded(self, *args):
        self.loaded.emit()

    def onKilled(self, targetID, *args):
        self.killed.emit(targetID)

    def onKey(self, event):
        if self.owners:
            self.key.emit(event)


battleEvents = BattleEvents()
