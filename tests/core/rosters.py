# -*- coding: utf-8 -*-
"""Fake arenas and a RatingViews harness for the team panels, without the game."""
import copy

from support import module, source

CLASSES = ('heavyTank', 'mediumTank', 'AT-SPG', 'lightTank', 'SPG')


def vehicle_type(name, tag, level=10, health=2000, descr=1):
    descriptor = module(tags=frozenset((tag,)), userString=name, shortUserString=name,
                        name='nation:' + name, compactDescr=descr)
    return module(level=level, maxHealth=health, type=descriptor)


def player(name, team, dbid, tag='mediumTank', vehicle=None, alive=True):
    return {'name': name, 'clanAbbrev': '', 'team': team, 'isAlive': alive, 'accountDBID': dbid,
            'vehicleType': vehicle_type(vehicle or name + '_tank', tag, descr=dbid or 1)}


def battle(allies, enemies):
    """allies/enemies vs allies/enemies: one account per player, the own vehicle is 1."""
    vehicles = {}
    for team, count in ((1, allies), (2, enemies)):
        for index in range(count):
            ident = 1 if team == 1 and index == 0 else team * 100 + index + 1
            tag = CLASSES[index % len(CLASSES)]
            vehicles[ident] = player('P%d_%02d' % (team, index), team, team * 10000 + index + 1, tag)
    return vehicles


def halloween(bots=8):
    """5 player allies, an allied bot, enemy bots and a boss: mode entities have accountDBID 0."""
    vehicles = {1: player('Zed', 1, 5001, 'mediumTank', vehicle='Leopard'),
                2: player('anna', 1, 5002, 'heavyTank', vehicle='Maus'),
                3: player('Bob', 1, 5003, 'heavyTank', vehicle='Maus', alive=False),
                4: player('carl', 1, 5004, 'lightTank', vehicle='Bat'),
                5: player('Dora', 1, 5005, 'heavyTank', vehicle='E100'),
                6: player('Ally Bot', 1, 0, 'AT-SPG', vehicle='Pumpkin')}
    for index in range(bots):
        vehicles[200 + index] = player('Bot %d' % index, 2, 0, CLASSES[index % len(CLASSES)])
    vehicles[300] = player('Boss', 2, 0, 'heavyTank', vehicle='Headless')
    return vehicles


class Stats(object):
    """Statistics service stand-in: accounts with an ID have ratings, mode entities none."""
    def __init__(self, vehicles):
        self.info = dict((str(v['accountDBID']), {'battles': 5000, 'wn8': 1800, 'winrate': 52})
                         for v in vehicles.values() if v['accountDBID'] > 0)
        self._appliedCache = {}
        self.loads = 0

    def getPlayersInfo(self, accountDBID):
        return self.info.get(str(accountDBID), None)

    def loadStats(self):
        self.loads += 1

    def reset(self):
        pass


class Harness(object):
    """Runs the real flash/battle/player_ratings.py over a fake arena and battle mode."""
    def __init__(self, test, vehicles, mode, own=1):
        self.test = test
        self.mode = mode
        self.data = copy.deepcopy(test.load('settings.default_values').DEFAULTS['team_panels'])
        self.arena = module(vehicles=vehicles, statistics={}, guiType=1)
        self.player = module(arena=self.arena, playerVehicleID=own, team=vehicles[own]['team'])
        self.callbacks = []
        self.sent = []
        self.gameface = []
        capabilities = module(current_mode=lambda: self.mode, is_event_mode=lambda: self.mode != 'random')
        events = module(**dict((name, module(connect=lambda *args: None, disconnect=lambda *args: None))
                               for name in ('started', 'loaded', 'ended', 'health', 'appeared', 'visibility',
                                            'killed', 'key')))
        events.acquire = events.release = lambda owner: None
        bigworld = module(player=lambda: self.player, time=lambda: 100.0, entity=lambda ident: None,
                          callback=lambda delay, fn: self.callbacks.append(fn) or len(self.callbacks),
                          cancelCallback=lambda handle: None, isKeyDown=lambda code: False)
        self.api = source('flash/battle/player_ratings.py', {
            'driftkings.settings.service': module(settings_service=module(getComponentDict=lambda config: self.data),
                                                  SettingsChanges=lambda data, paths: None,
                                                  changed_paths=lambda old, new: (),
                                                  affects=lambda changes, *keys: True),
            'BigWorld': bigworld,
            'realm': module(CURRENT_REALM='NA'),
            'driftkings.flash.battle.meta.players_panel': module(PlayersPanelMeta=object),
            'gui.Scaleform.daapi.view.battle.classic.players_panel': module(PlayersPanel=object),
            'gui.Scaleform.daapi.view.meta.BattleStatisticDataControllerMeta': module(
                BattleStatisticDataControllerMeta=object),
            'gui.shared': module(g_eventBus=None, events=None, EVENT_BUS_SCOPE=None),
            'driftkings.core.hooks': module(override=lambda *args: None),
            'driftkings.core.battle_capabilities': module(battle_capabilities=capabilities),
            'driftkings.core.battle_events': module(battleEvents=events),
            'driftkings.common.utils.colorratting': module(getStatisticColor=lambda kind, value, scale: '#5A3175'),
        })
        self.stats = Stats(vehicles)
        self.views = self.api['RatingViews'](module(i18n={'UI_panel_destroyed': 'Destroyed'}), self.stats)
        self.views.active = True
        harness = self
        self.view = module(_isDAAPIInited=lambda: True, as_setRosterS=self.sent.append,
                           isColorBlind=lambda: False)
        self.views.view = self.view
        self.views.gameface = module(active_screens=lambda: set(), update=lambda enabled, rows:
                                     harness.gameface.append((enabled, rows)), clear=lambda: None)

    def tick(self):
        self.views.tick()
        return self.sent[-1] if self.sent else None
