# -*- coding: utf-8 -*-
"""PlayerPanelPro robustness: macro hotkeys, statistics retries and the session cache."""
import time
try:
    import Queue as queue
except ImportError:
    import queue

from support import RuntimeTest, module, source


class HotkeyFieldTests(RuntimeTest):
    def setUp(self):
        super(HotkeyFieldTests, self).setUp()
        self.constants = self.load('_constants')
        self.roster = self.load('core.panel_model').Roster()

    def test_non_numeric_hotkey_is_treated_as_no_hotkey(self):
        panels = self.constants.TEAM_PANELS
        data = {panels.TEMPLATES: {}, panels.HP_ENABLED: True}
        values = {'xvm-stat': 'stat'}
        for code in ('', 'ALT', None):
            settings = {'extraFieldsLeft': [{'id': 'extra', 'format': 'text', 'hotKeyCode': code}]}
            result = self.roster.screen(settings, values, data, 'Left')
            self.assertEqual([field['format'] for field in result['fields']], ['text'])

    def test_numeric_hotkey_still_follows_the_key(self):
        panels = self.constants.TEAM_PANELS
        data = {panels.TEMPLATES: {}, panels.HP_ENABLED: True}
        settings = {'extraFieldsLeft': [{'format': 'text', 'hotKeyCode': '56', 'onHold': True}]}
        self.assertEqual(self.roster.screen(settings, {'xvm-stat': ''}, data, 'Left')['fields'], [])
        self.roster.key(184, True)
        self.assertEqual(len(self.roster.screen(settings, {'xvm-stat': ''}, data, 'Left')['fields']), 1)


class StatisticsRequestTests(RuntimeTest):
    def setUp(self):
        super(StatisticsRequestTests, self).setUp()
        colors = self.load('common.utils.colorratting')
        self.settings = {'enabled': True, 'statsEnabled': True, 'colorScale': 0,
                         'performance': {'cacheEnabled': False, 'cacheExpiry': 3600,
                                         'minBattlesToShow': 0, 'requestTimeout': 1}}
        self.player = module(arena=module(vehicles={7: {'accountDBID': 1001, 'vehicleType': None}}))
        self.scheduled = []
        api = source('core/player_ratings.py', {
            'urllib2': module(), 'Queue': queue,
            'gui.battle_control.arena_info.interfaces': module(IArenaVehiclesController=object),
            'gui.battle_control.arena_info.settings': module(ARENA_LISTENER_SCOPE=module(VEHICLES=2)),
            'gui.battle_control.battle_constants': module(BATTLE_CTRL_ID=module(MOD=19)),
            'gui.shared.gui_items.Vehicle': module(getVehicleClassTag=lambda value: None),
            'gui.shared.personality': module(ServicesLocator=object()),
            'helpers': module(dependency=module(descriptor=lambda value: None)),
            'messenger': module(g_settings=object()),
            'skeletons.gui.battle_session': module(IBattleSessionProvider=object),
            'driftkings._constants': module(GLOBAL=module(ENABLED='enabled'), TEAM_PANELS=module(
                PERFORMANCE='performance', STATS_ENABLED='statsEnabled', COLOR_SCALE='colorScale')),
            'driftkings.common.utils.wgutils': module(getPlayer=lambda: self.player),
            'driftkings.common.utils.colorratting': module(getStatisticColor=colors.getStatisticColor),
            'driftkings.core.callbacks': module(callback=lambda delay, fn: self.scheduled.append(fn) or len(self.scheduled),
                                                cancelCallback=lambda handle: None),
            'driftkings.core.hooks': module(override=lambda *args: None),
            'driftkings.settings.service': module(settings_service=module(getComponentDict=lambda config: self.settings)),
            'driftkings.stats.vehinfo': module(calculateXvmScale=lambda metric, value: value,
                                               getVehicleInfoData=lambda value: None, scaleValuesInstance=object())})
        class ImmediateThread(object):
            def __init__(self, target, args):
                self.target, self.args = target, args

            def setDaemon(self, value):
                pass

            def start(self):
                self.target(*self.args)

        api['threading'] = module(Thread=ImmediateThread)
        self.api = api
        self.stats = api['Statistics']()
        self.requests = []
        self.stats.applyPlayerStats = lambda info, tanks: None
        # Record requests instead of reaching the network from a worker thread.
        self.stats.loadPlayerStats = lambda ids, generation, tanks: self.requests.append(list(ids))

    def answer(self, info):
        generation = self.stats._generation
        self.stats._responses.put((generation, ['1001'], info, dict((key, []) for key in info)))
        self.stats._responses.put((generation, None, None, None))
        self.stats.pollStats()

    def test_accounts_without_data_wait_before_a_retry(self):
        self.stats.loadStats()
        self.assertEqual(self.requests, [['1001']])
        self.answer({'1001': None})
        self.assertEqual(self.stats._workers, 0)
        self.stats.loadStats()
        self.assertEqual(len(self.requests), 1)
        self.stats._attempts['1001'] -= self.api['RETRY_SECONDS'] + 1
        self.stats.loadStats()
        self.assertEqual(len(self.requests), 2)

    def test_answered_accounts_are_not_fetched_again_without_the_cache(self):
        self.stats.loadStats()
        self.answer({'1001': {'statistics': {}}})
        self.stats._attempts['1001'] -= self.api['RETRY_SECONDS'] + 1
        self.stats.loadStats()
        self.assertEqual(len(self.requests), 1)
        self.stats.reset()
        self.stats.loadStats()
        self.assertEqual(len(self.requests), 2)

    def test_polling_stops_once_workers_finish(self):
        self.stats.loadStats()
        polls = len(self.scheduled)
        self.answer({'1001': None})
        self.assertEqual(len(self.scheduled), polls)

    def test_failed_requests_retry_soon_during_loading(self):
        self.stats.loadStats()
        self.answer({})
        # A timeout or API error is not a closed profile: retry within seconds.
        retry = self.scheduled[-1]
        self.assertEqual(retry, self.stats.retryStats)
        self.stats._attempts['1001'] -= self.api['FAILED_RETRY_SECONDS']
        retry()
        self.assertEqual(self.requests, [['1001'], ['1001']])
        self.assertIsNone(self.stats._retry)

    def test_cache_drops_expired_entries_and_keeps_the_newest(self):
        self.settings['performance']['cacheEnabled'] = True
        now = time.time()
        limit = self.api['CACHE_LIMIT']
        for index in range(limit + 5):
            self.stats.statsCache[str(index)] = {}
            self.stats.cacheTimestamp[str(index)] = now - index
        self.stats.statsCache['old'] = {}
        self.stats.cacheTimestamp['old'] = now - 4000
        self.stats.pruneCache()
        self.assertEqual(len(self.stats.statsCache), limit)
        self.assertNotIn('old', self.stats.statsCache)
        self.assertIn('0', self.stats.statsCache)
        self.assertNotIn(str(limit + 4), self.stats.statsCache)
        self.assertEqual(set(self.stats.statsCache), set(self.stats.cacheTimestamp))
        self.settings['performance']['cacheEnabled'] = False
        self.stats.pruneCache()
        self.assertEqual((self.stats.statsCache, self.stats.cacheTimestamp), ({}, {}))


    def test_arena_listener_requests_statistics_on_vehicle_updates(self):
        listener = self.api['ArenaStatsListener'](self.stats)
        self.assertEqual((listener.getControllerID(), listener.getCtrlScope()), (19, 2))
        listener.invalidateArenaInfo()
        self.assertEqual(self.requests, [['1001']])
        self.stats._pending.clear(); self.stats._attempts.clear()
        listener.addVehicleInfo(None, None)
        self.assertEqual(len(self.requests), 2)

    def test_arena_listener_follows_the_battle_session(self):
        events = []
        session = module(onBattleSessionStart=Hook(), onBattleSessionStop=Hook(),
                         addArenaCtrl=lambda ctrl: events.append(('add', ctrl)) or True,
                         removeArenaCtrl=lambda ctrl: events.append(('remove', ctrl)))
        self.api['Statistics'].sessionProvider = session
        self.stats.start()
        session.onBattleSessionStart.fire()
        session.onBattleSessionStop.fire()
        self.stats.stop()
        self.assertEqual([kind for kind, ctrl in events], ['add', 'remove'])
        self.assertEqual((session.onBattleSessionStart.handlers, session.onBattleSessionStop.handlers), ([], []))

class KeyStateTests(RuntimeTest):
    def setUp(self):
        super(KeyStateTests, self).setUp()
        constants = self.load('_constants')
        self.down = set()
        self.modes = []
        self.data = {constants.TEAM_PANELS.PLAYERS_PANEL: {'altMode': 'large'}}
        settings_data = module(PROFILES=('none', 'short', 'medium', 'medium2', 'large'),
                               profile_for_mode=lambda mode: 'large')
        api = source('views/battle/player_ratings.py', {
            'driftkings.settings.service': module(settings_service=module(getComponentDict=lambda config: self.data),
                                                 SettingsChanges=None, changed_paths=None, affects=None),
            'BigWorld': module(isKeyDown=lambda code: code in self.down),
            'realm': module(CURRENT_REALM='EU'),
            'driftkings.meta.battle.players_panel': module(PlayersPanelMeta=object),
            'gui.Scaleform.daapi.view.battle.classic.players_panel': module(PlayersPanel=object),
            'gui.Scaleform.daapi.view.meta.BattleStatisticDataControllerMeta': module(BattleStatisticDataControllerMeta=object),
            'gui.shared': module(g_eventBus=None, events=None, EVENT_BUS_SCOPE=None),
            'driftkings.core.hooks': module(override=None),
            'driftkings.core.battle_events': module(battleEvents=None),
            'driftkings.settings.settings_data': settings_data,
            'driftkings.common.utils.colorratting': module(getStatisticColor=None),
        })
        self.view = api['RatingViews'](module(), None)
        self.view.active = True
        self.view.baseMode = 1
        self.view.refresh = lambda *args: None
        self.view.setMode = self.modes.append

    def press(self, code, down):
        (self.down.add if down else self.down.discard)(code)
        self.view.key(module(key=code, isKeyDown=lambda: down))

    def test_lost_alt_release_is_recovered(self):
        self.press(56, True)
        self.assertTrue(self.view.alt)
        # Alt+Tab or the settings window swallow the key-up event.
        self.down.discard(56)
        self.view.releaseKeys()
        self.assertFalse(self.view.alt)
        self.assertNotIn(56, self.view.model.keys)
        self.assertEqual(self.modes, [4, 1])

    def test_releasing_alt_over_the_panel_keeps_it_expanded(self):
        self.press(56, True)
        self.view.hover(True)
        self.press(56, False)
        self.assertEqual(self.modes, [4, 4])
        self.view.hover(False)
        self.assertEqual(self.modes[-1], 1)


class BattleModeTests(RuntimeTest):
    """EU bonus types: bot-filled randoms count for statistics; extension modes are events."""
    NAMES = {'UNKNOWN': 0, 'REGULAR': 1, 'TRAINING': 2, 'EVENT_BATTLES': 9, 'EPIC_BATTLE': 27, 'COMP7': 43,
             'WINBACK': 44, 'RANDOM_NP2': 46, 'HALLOWEEN': 101, 'LAST_STAND': 107}

    def setUp(self):
        super(BattleModeTests, self).setUp()
        capabilities = self.load('core.battle_capabilities')
        names = dict(self.NAMES, RANGE=tuple(self.NAMES.values()), RANDOM_RANGE=(1, 46))
        constants = module(ARENA_BONUS_TYPE=module(**names))
        self.bonus = None
        self.context = capabilities.BattleCapabilities(
            player=lambda: module(arena=module(bonusType=self.bonus)), session=lambda: None,
            modules={'constants': constants})
        self.policy = self.load('core.battle_policy').BattlePolicy(self.context)

    def at(self, name):
        self.bonus = self.NAMES[name]
        return self.context

    def test_bot_randoms_count_as_statistics_battles(self):
        for name in ('REGULAR', 'RANDOM_NP2', 'WINBACK'):
            context = self.at(name)
            self.assertTrue(context.is_statistics_battle(), name)
            self.assertTrue(context.is_random(), name)
            self.assertFalse(context.is_event_mode(), name)
            self.assertTrue(self.policy.decision('battle_marks_of_excellence')[0], name)

    def test_event_modes_are_restricted_and_standard_modes_are_not(self):
        for name in ('HALLOWEEN', 'LAST_STAND', 'EVENT_BATTLES'):
            context = self.at(name)
            self.assertTrue(context.is_event_mode(), name)
            self.assertEqual(self.policy.decision('high_caliber_progress'), (False, 'requires_statistics_battle'))
        for name in ('TRAINING', 'EPIC_BATTLE', 'COMP7', 'UNKNOWN'):
            self.assertFalse(self.at(name).is_event_mode(), name)


class EventPanelTests(RuntimeTest):
    def setUp(self):
        super(EventPanelTests, self).setUp()
        panels = self.load('_constants').TEAM_PANELS
        self.roster = self.load('core.panel_model').Roster()
        self.data = {panels.STATS_ENABLED: True, panels.PERFORMANCE: {'minBattlesToShow': 0},
                     panels.SPOTTED_ENABLED: True, panels.RATING: 'wn8', panels.COLOR_SCALE: 0,
                     panels.TEMPLATES: {}, panels.HP_ENABLED: True}
        self.stats = {'battles': 12000, 'wn8': 2469, 'winrate': 57, 't-battles': 120, 't-winrate': 53}
        self.vehicle = {'name': 'Player', 'clanAbbrev': 'CL', 'team': 1, 'isAlive': True}

    def values(self):
        return self.roster.values(5, self.vehicle, self.stats, 1, 1, self.data,
                                  lambda kind, value, scale: '#5A3175')

    def test_event_mode_keeps_wn8_colour_but_hides_numbers(self):
        normal = self.values()
        self.assertEqual((normal['r'], normal['xvm-stat'], normal['stat-color']), (2469, 'stat', 'stat'))
        self.roster.restricted = True
        event = self.values()
        for key in ('r', 'wn8', 'winrate', 'battles', 'kb', 't-battles', 't-winrate'):
            self.assertIsNone(event[key], key)
        self.assertEqual((event['xvm-stat'], event['stat-color'], event['c:r']), ('', 'stat', '#5A3175'))
        self.assertEqual((event['name'], event['nick']), ('Player', 'Player [CL]'))

    def test_event_mode_hides_hp_fields_but_keeps_the_row(self):
        settings = {'showUnavailable': False, 'extraFieldsLeft': [{'id': 'hpBar', 'format': 'hp'},
                                                                  {'id': 'extra', 'format': 'text'}]}
        self.assertEqual(len(self.roster.screen(settings, self.values(), self.data, 'Left')['fields']), 2)
        self.roster.restricted = True
        result = self.roster.screen(settings, self.values(), self.data, 'Left')
        self.assertTrue(result['enabled'])
        self.assertEqual([field['id'] for field in result['fields']], ['extra'])


class MacroValidationTests(RuntimeTest):
    def test_default_large_panel_formats_use_only_known_macros(self):
        import json, os
        issues = self.load('settings.panel_validation').macro_issues
        path = os.path.join(os.path.dirname(__file__), '..', '..', 'res', 'configs', 'driftkings', 'default',
                            'team_panels', 'panellarge.json')
        with open(path, 'rb') as stream:
            data = json.loads(stream.read().decode('utf-8'))
        for key in ('nickFormatLeft', 'nickFormatRight', 'vehicleFormatLeft', 'vehicleFormatRight'):
            self.assertEqual(issues(data[key], {}), [], key)


class Hook(object):
    def __init__(self):
        self.handlers = []

    def __iadd__(self, handler):
        self.handlers.append(handler)
        return self

    def __isub__(self, handler):
        self.handlers.remove(handler)
        return self

    def fire(self):
        for handler in list(self.handlers):
            handler()


class BattleFeedbackTests(RuntimeTest):
    """Battle events come from the session's native feedback controller, not a PlayerAvatar hook."""

    def setUp(self):
        super(BattleFeedbackTests, self).setUp()
        self.hooks = []
        self.feedback = module(onPlayerFeedbackReceived=Hook())
        self.field = module(onSpottedStatusChanged=Hook())
        self.session = module(onBattleSessionStart=Hook(), onBattleSessionStop=Hook(), shared=module(feedback=None),
                              dynamic=module(battleField=self.field))
        api = source('core/battle_events.py', {
            'Avatar': module(PlayerAvatar=object), 'Vehicle': module(Vehicle=object),
            'VehicleGunRotator': module(VehicleGunRotator=object),
            'driftkings.core.hooks': module(override=lambda cls, name, handler: self.hooks.append(name)),
            'driftkings.core.keyboard': module(keyboard=module(subscribe=lambda fn: None, unsubscribe=lambda fn: None)),
            'driftkings.ui': module(g_events=module(onBattleLoaded=Hook())),
            'helpers': module(dependency=module(instance=lambda iface: self.session)),
            'skeletons.gui.battle_session': module(IBattleSessionProvider=object),
            'BigWorld': module(player=lambda: 'avatar'),
        })
        self.events = api['BattleEvents']()

    def test_feedback_follows_the_battle_session(self):
        received = []
        self.events.feedback.connect(lambda avatar, events: received.append((avatar, events)))
        self.events.acquire('owner')
        self.assertNotIn('onBattleEvents', self.hooks)
        self.session.shared.feedback = self.feedback
        self.session.onBattleSessionStart.fire()
        for handler in self.feedback.onPlayerFeedbackReceived.handlers:
            handler(['event'])
        self.assertEqual(received, [('avatar', ['event'])])
        self.session.onBattleSessionStop.fire()
        self.assertEqual(self.feedback.onPlayerFeedbackReceived.handlers, [])
        self.events.release('owner')
        self.assertEqual(self.session.onBattleSessionStart.handlers, [])

    def test_spotted_status_comes_from_the_battle_field_controller(self):
        seen = []
        self.events.visibility.connect(lambda vehicleID, visible: seen.append((vehicleID, visible)))
        self.events.acquire('owner')
        self.assertNotIn('_setInAoI', self.hooks)
        self.session.onBattleSessionStart.fire()
        vo = lambda vehicleID, status: (0, module(vehicleID=vehicleID, spottedStatus=status))
        for handler in self.field.onSpottedStatusChanged.handlers:
            handler([vo(5, 1), vo(6, 2), vo(7, 0)], None)
        self.assertEqual(seen, [(5, True), (6, False)])
        self.events.release('owner')
        self.assertEqual(self.field.onSpottedStatusChanged.handlers, [])
