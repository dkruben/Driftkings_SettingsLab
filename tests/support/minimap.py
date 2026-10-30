# -*- coding: utf-8 -*-
"""Minimap vehicles plugin: last positions, expiry, spotting again and labels, on a stub of the native plugin."""
import copy
import weakref

from support import RuntimeTest, module, source
from support.minimap_defaults import defaults


class Entry(object):
    def __init__(self, entryID, enemy=True):
        self.entryID = entryID
        self.enemy = enemy
        self.alive = True
        self.inAoI = True
        self.active = True

    def getID(self):
        return self.entryID

    def isEnemy(self):
        return self.enemy

    def isAlive(self):
        return self.alive

    def isInAoI(self):
        return self.inAoI

    def isActive(self):
        return self.active

    def getMatrix(self):
        return object()

    def setActive(self, active):
        changed = self.active != active
        self.active = active
        return changed


class MinimapFixture(RuntimeTest):
    def setUp(self):
        super(MinimapFixture, self).setUp()
        self.now = 100.0
        self.data = dict(copy.deepcopy(defaults()), enabled=True)
        self.callbacks = []
        self.published = []
        test = self

        class NativeVehicles(object):
            def __init__(self, *args, **kwargs):
                self._entries = {}
                self._arenaDP = test.arena
                self._ArenaVehiclesPlugin__showDestroyEntries = False
                self._ArenaVehiclesPlugin__isDestroyImmediately = False
                self.invoked = []
                self.activated = []

            def start(self):
                pass

            def stop(self):
                pass

            def _showVehicle(self, vehicleID, location):
                self._entries[vehicleID].inAoI = True

            def _hideVehicle(self, entry):
                entry.inAoI = False

            def _setInAoI(self, entry, isInAoI):
                entry.inAoI = isInAoI

            def _setActive(self, entryID, active):
                self.activated.append((entryID, active))

            def _invoke(self, entryID, method, *args):
                self.invoked.append((entryID, method) + args)

            def _setVehicleInfo(self, vehicleID, entry, vInfo, guiProps, isSpotted=False):
                pass

            def _getGuiPropsName(self, props):
                return props

        NativeVehicles.__name__ = 'ArenaVehiclesPlugin'
        class NativePersonal(object):
            def _calcCircularVisionRadius(self):
                return 445

        signal = module(connect=lambda *args: None, disconnect=lambda *args: None)
        service = module(onModSettingsChanged=signal, getComponentDict=lambda config: self.data)
        self.info = module(isAlive=lambda: True, team=2, player=module(name='Enemy'), getDisplayedName=lambda: 'IS-7',
                           vehicleType=module(level=10, classTag='heavyTank', maxHealth=2400, compactDescr=1))
        self.arena = module(getVehicleInfo=lambda vehicleID=None: self.info,
                            getPlayerGuiProps=lambda vehicleID, team: 'enemy')
        policy = self.load('core.minimap')
        deps = {
            'BigWorld': module(time=lambda: self.now),
            'account_helpers.settings_core': module(settings_constants=module()),
            'gui.Scaleform.daapi.view.battle.shared.minimap': module(plugins=module(
                ArenaVehiclesPlugin=NativeVehicles, PersonalEntriesPlugin=NativePersonal)),
            'gui.Scaleform.daapi.view.battle.shared.minimap.component': module(MinimapComponent=object),
            'gui.Scaleform.daapi.view.battle.shared.minimap.settings': module(
                CIRCLE_TYPE=module(), CIRCLE_STYLE=module(), VIEW_RANGE_CIRCLES_AS3_DESCR=module()),
            'helpers': module(dependency=module(descriptor=lambda interface: None)),
            'skeletons.gui.battle_session': module(IBattleSessionProvider=object),
            'driftkings.common.utils.formatting': module(hexToDecimal=lambda value: value),
            'driftkings.common.utils.wgutils': module(hasCompetingMarkers=lambda: False, getBattleTypes=lambda: ()),
            'driftkings.common.utils.game': module(checkKeys=lambda keys: False),
            'driftkings.core': module(minimap=policy),
            'driftkings.core.callbacks': module(callback=lambda delay, function: self.callbacks.append(function) or len(self.callbacks),
                                                cancelCallback=lambda handle: None),
            'driftkings.core.hooks': module(override=lambda *args: (lambda function: function)),
            'driftkings.core.keyboard': module(keyboard=module(subscribe=lambda handler: None, unsubscribe=lambda handler: None)),
            'driftkings.settings.service': module(settings_service=service),
            'driftkings.ui.common.events': module(g_events=module(onAltKey=lambda pressed: None)),
            'driftkings.settings.definitions.battle.minimap_enhancements': module(MinimapEnhancementsSettings=object),
            'driftkings.flash.battle.minimap_enhancements': module(MinimapEnhancementsView=object),
        }
        self.api = source('flash/battle/minimap_plugins.py', deps)
        self.api['configure'](object(), module(minimapZoom=False), weakref.WeakSet(), weakref.WeakSet(), weakref.WeakSet())
        self.api['VIEWS'].add(self)
        self.plugin = self.api['ArenaVehiclesPlugin']()
        self.plugin.start()
        self.entry = Entry(7)
        self.plugin._entries[5] = self.entry

    def onVehicleData(self, payload):
        self.published.append(payload)

    def tick(self, seconds):
        self.now += seconds
        pending, self.callbacks[:] = list(self.callbacks), []
        for function in pending:
            function()
