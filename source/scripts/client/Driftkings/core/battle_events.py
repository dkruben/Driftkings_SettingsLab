# -*- coding: utf-8 -*-
"""Shared battle notifications. Wrappers preserve the original game calls."""
import logging

from Avatar import PlayerAvatar
from Vehicle import Vehicle
from VehicleGunRotator import VehicleGunRotator
from gui.Scaleform.daapi.view.battle.shared.minimap.plugins import ArenaVehiclesPlugin

from Driftkings.common.utils.monkeypatch import override
from Driftkings.core.keyboard import keyboard
from Driftkings.ui import g_events

LOG = logging.getLogger('Driftkings.BattleEvents')


class Signal(object):
    def __init__(self):
        self.listeners = []

    def connect(self, callback):
        if callback not in self.listeners:
            self.listeners.append(callback)

    def disconnect(self, callback):
        if callback in self.listeners:
            self.listeners.remove(callback)

    def emit(self, *args):
        for callback in tuple(self.listeners):
            try:
                callback(*args)
            except Exception:
                LOG.exception('Battle event handler failed')


class BattleEvents(object):
    def __init__(self):
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

    def acquire(self, owner):
        if owner in self.owners:
            return
        if not self.owners:
            if not self.hooked:
                override(PlayerAvatar, '_PlayerAvatar__startGUI', self.startGUI)
                override(PlayerAvatar, '_PlayerAvatar__destroyGUI', self.destroyGUI)
                override(PlayerAvatar, 'vehicle_onAppearanceReady', self.appearanceReady)
                override(Vehicle, 'onHealthChanged', self.healthChanged)
                override(ArenaVehiclesPlugin, '_setInAoI', self.visibilityChanged)
                override(VehicleGunRotator, 'updateRotationAndGunMarker', self.dispersionChanged)
                self.hooked = True
            g_events.onBattleLoaded += self.onLoaded
            keyboard.subscribe(self.onKey)
        self.owners.add(owner)

    def release(self, owner):
        if owner not in self.owners:
            return
        self.owners.remove(owner)
        if not self.owners:
            self.detachArena()
            g_events.onBattleLoaded -= self.onLoaded
            keyboard.unsubscribe(self.onKey)

    def detachArena(self):
        if self.arena is not None:
            self.arena.onVehicleKilled -= self.onKilled
            self.arena = None

    def startGUI(self, original, avatar, *args, **kwargs):
        result = original(avatar, *args, **kwargs)
        if self.owners:
            arena = getattr(avatar, 'arena', None)
            if arena is not self.arena:
                self.detachArena()
                self.arena = arena
                if arena is not None:
                    arena.onVehicleKilled += self.onKilled
            self.started.emit()
        return result

    def destroyGUI(self, original, avatar, *args, **kwargs):
        if self.owners:
            self.ended.emit()
            self.detachArena()
        return original(avatar, *args, **kwargs)

    def appearanceReady(self, original, avatar, vehicle, *args, **kwargs):
        result = original(avatar, vehicle, *args, **kwargs)
        if self.owners:
            self.appeared.emit(vehicle.id)
        return result

    def healthChanged(self, original, vehicle, health, *args, **kwargs):
        result = original(vehicle, health, *args, **kwargs)
        if self.owners:
            self.health.emit(vehicle.id, health)
        return result

    def visibilityChanged(self, original, plugin, entry, visible, *args, **kwargs):
        result = original(plugin, entry, visible, *args, **kwargs)
        if self.owners:
            for vehicleID, candidate in plugin._entries.items():
                if candidate == entry:
                    self.visibility.emit(vehicleID, visible)
                    break
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
