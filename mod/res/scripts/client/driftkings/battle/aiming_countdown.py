# -*- coding: utf-8 -*-
"""Aiming countdown beside the crosshair, as a Gameface text in the native battle HUD.

Battle pages without that HUD (Halloween, Fort Rush) show no text."""
from driftkings.common.utils import events
from driftkings.core.battle_capabilities import battle_capabilities
from driftkings.core.hooks import on_event
from driftkings.gameface.battle.reticle_texts import AimingCountdownAdapter
from driftkings.settings.definitions.battle.aiming_countdown import AimingCountdownSettings

aiming_countdown_settings = AimingCountdownSettings()
g_gameface = None


@on_event(events.PlayerAvatar.startGUI.after)
def new_startGUI(*args):
    if g_gameface is not None and battle_capabilities.has_gameface_hud():
        g_gameface.startBattle()


@on_event(events.PlayerAvatar.destroyGUI.before)
def new_destroyGUI(*args):
    if g_gameface is not None:
        g_gameface.stopBattle()


def init():
    global g_gameface
    if g_gameface is None:
        g_gameface = AimingCountdownAdapter()
        g_gameface.install()


def fini():
    global g_gameface
    if g_gameface is not None:
        g_gameface.dispose()
        g_gameface = None
