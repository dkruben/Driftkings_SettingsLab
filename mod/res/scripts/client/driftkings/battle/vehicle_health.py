# -*- coding: utf-8 -*-
"""Own vehicle health as a Gameface bar in the native battle HUD.

Battle pages without that HUD (Halloween, Fort Rush) show no bar."""
from driftkings.common.utils import events
from driftkings.core.battle_capabilities import battle_capabilities
from driftkings.core.hooks import on_event
from driftkings.gameface.battle.vehicle_health import OwnHealthAdapter
from driftkings.logger import get_logger
from driftkings.settings.definitions.battle.vehicle_health import VehicleHealthSettings

LOG = get_logger('Driftkings.OwnHealth')
vehicle_health_settings = VehicleHealthSettings()
g_gameface = None


class HealthTracker(object):
    """Health, battle period and camera state of the controlled vehicle while the Gameface bar is in use."""

    # Prepara o estado e as referências de barra de vida do veículo.
    def __init__(self):
        self.state = {'current': 0, 'maximum': 0, 'alive': True, 'battle': False}
        self.listener = None
        self._vehicleState = None
        self._inputHandler = None
        self._started = False

    # Repõe os valores de vida e o estado de apresentação do veículo.
    def reset(self):
        self.state = {'current': 0, 'maximum': 0, 'alive': True, 'battle': False}

    # Ativa o acompanhamento de barra de vida do veículo.
    def start(self, listener):
        from gui.battle_control import avatar_getter
        from PlayerEvents import g_playerEvents

        from driftkings.game_constants import ARENA_PERIOD
        if self._started:
            return
        self._started = True
        self.listener = listener
        self.reset()
        arena = avatar_getter.getArena()
        self.state['battle'] = getattr(arena, 'period', None) == ARENA_PERIOD.BATTLE
        g_playerEvents.onArenaPeriodChange += self.onArenaPeriodChange
        handler = avatar_getter.getInputHandler()
        if handler is not None and hasattr(handler, 'onCameraChanged'):
            handler.onCameraChanged += self.onCameraChanged
            self._inputHandler = handler
        session = battle_capabilities.session()
        ctrl = getattr(getattr(session, 'shared', None), 'vehicleState', None)
        if ctrl is not None:
            ctrl.onVehicleControlling += self.onVehicleControlling
            ctrl.onVehicleStateUpdated += self.onVehicleStateUpdated
            self._vehicleState = ctrl
            vehicle = ctrl.getControllingVehicle()
            if vehicle is not None:
                self.onVehicleControlling(vehicle)
        self.changed()

    # Desativa o acompanhamento de barra de vida do veículo e liberta as subscrições.
    def stop(self):
        from PlayerEvents import g_playerEvents
        if not self._started:
            return
        self._started = False
        g_playerEvents.onArenaPeriodChange -= self.onArenaPeriodChange
        if self._inputHandler is not None:
            self._inputHandler.onCameraChanged -= self.onCameraChanged
            self._inputHandler = None
        if self._vehicleState is not None:
            self._vehicleState.onVehicleControlling -= self.onVehicleControlling
            self._vehicleState.onVehicleStateUpdated -= self.onVehicleStateUpdated
            self._vehicleState = None
        self.reset()
        self.listener = None

    # Notifica o adaptador visual de que os dados de vida mudaram.
    def changed(self):
        if self.listener is not None:
            self.listener.refresh()

    # Valida e atualiza os pontos de vida do veículo controlado.
    def setHealth(self, health):
        if not isinstance(health, (int, long, float)):
            return
        health = max(0, int(health))
        self.state['current'] = health
        self.state['maximum'] = max(self.state['maximum'], health)
        self.state['alive'] = health > 0
        self.changed()

    # Atualiza a vida máxima e o estado ao mudar de veículo controlado.
    def onVehicleControlling(self, vehicle):
        if vehicle is None:
            return
        self.state['maximum'] = getattr(vehicle, 'maxHealth', 0) or 0
        self.setHealth(getattr(vehicle, 'health', 0))

    # Encaminha as alterações nativas do estado de vida do veículo.
    def onVehicleStateUpdated(self, state, value):
        from gui.battle_control.battle_constants import VEHICLE_VIEW_STATE
        if state == VEHICLE_VIEW_STATE.HEALTH:
            self.setHealth(value)

    # Atualiza o estado de batalha usado na apresentação da barra.
    def onArenaPeriodChange(self, period, *_):
        from driftkings.game_constants import ARENA_PERIOD
        self.state['battle'] = period == ARENA_PERIOD.BATTLE
        self.changed()

    # Adapta a visibilidade da barra ao modo da câmara e ao estado do jogador.
    def onCameraChanged(self, ctrlMode, *_, **__):
        from driftkings.game_constants import CTRL_MODE_NAME

        # Camera modes after the own vehicle is destroyed.
        dead = (CTRL_MODE_NAME.KILL_CAM, CTRL_MODE_NAME.POSTMORTEM, CTRL_MODE_NAME.DEATH_FREE_CAM,
                CTRL_MODE_NAME.RESPAWN_DEATH, CTRL_MODE_NAME.VEHICLES_SELECTION, CTRL_MODE_NAME.LOOK_AT_KILLER)
        self.state['alive'] = ctrlMode not in dead and self.state['current'] > 0
        self.changed()


tracker = HealthTracker()


# Inicia o módulo de barra de vida do veículo quando a interface de batalha está disponível.
@on_event(events.PlayerAvatar.startGUI.after)
def new_startGUI(*args):
    if g_gameface is None:
        return
    if not battle_capabilities.has_gameface_hud():
        LOG.info('Own health bar unavailable: this battle page has no Gameface HUD')
        return
    LOG.info('Own health uses the Gameface battle HUD')
    tracker.start(g_gameface)
    g_gameface.startBattle()


# Encerra o módulo de barra de vida do veículo quando a interface de batalha é destruída.
@on_event(events.PlayerAvatar.destroyGUI.before)
def new_destroyGUI(*args):
    tracker.stop()
    if g_gameface is not None:
        g_gameface.stopBattle()


# Inicializa o módulo de barra de vida do veículo.
def init():
    global g_gameface
    if g_gameface is None:
        g_gameface = OwnHealthAdapter()
        g_gameface.install()


# Liberta os recursos do módulo de barra de vida do veículo.
def fini():
    global g_gameface
    tracker.stop()
    if g_gameface is not None:
        g_gameface.dispose()
        g_gameface = None
