# -*- coding: utf-8 -*-
"""Aiming countdown, shell flight time and penetration texts beside the crosshair in Gameface."""
from support import RuntimeTest, Settings, game_source, module, source

STRATEGIC = 3


class Event(object):
    def __init__(self):
        self.handlers = []

    def __iadd__(self, handler):
        self.handlers.append(handler)
        return self

    def __isub__(self, handler):
        self.handlers.remove(handler)
        return self

    def __call__(self, *args):
        for handler in list(self.handlers):
            handler(*args)


class ReticleTextTests(RuntimeTest):
    def setUp(self):
        super(ReticleTextTests, self).setUp()
        self.data = {
            'aiming_countdown': {'enabled': True, 'x': 60, 'y': 110, 'align': 'left', 'template': "<font color='%(color)s'>%(timer).1fs - %(percent)d%%</font>",
                                 'red': '#FE0E00', 'orange': '#FE7903', 'yellow': '#F8F400', 'green': '#A6FFA6', 'blue': '#02C9B3', 'purple': '#D042F3'},
            'penetration_indicator': {'enabled': True, 'position': {'x': 0, 'y': 40}, 'messages': {'green': 'Go'},
                                      'template': "%(ricochet)s<br><font color='%(color)s'>%(countedArmor)d | %(piercingPower)d</font>"},
        }
        configs = dict((name, module(NAME=name, i18n={'UI_colors': {'green': '#66FF33'}, 'UI_ricochet': 'RICOCHET', 'UI_noDamage': 'NO DAMAGE'}))
                       for name in self.data)
        components = {'driftkings.battle.aiming_countdown': module(aiming_countdown_settings=configs['aiming_countdown']),
                      'driftkings.battle.penetration_indicator': module(penetration_indicator_settings=configs['penetration_indicator'])}
        self.applied = []

        class Service(object):
            def getComponentDict(service, config):
                return self.data[config.NAME]

            def apply(service, config, values):
                self.applied.append((config.NAME, values))

        self.crosshair = module(onCrosshairPositionChanged=Event(), onCrosshairViewChanged=Event(), onGunMarkerStateChanged=Event(),
                                getSize=lambda: (1920, 1080), getPosition=lambda: self.position, getViewID=lambda: self.view)
        self.position, self.view = (960, 600), 1
        self.dispersion = []
        self.armor, self.colors = Event(), Event()
        self.api, _ = game_source('gameface/battle/reticle_texts.py', {
            'importlib': module(import_module=lambda name: components[name]),
            'driftkings.settings.service': module(settings_service=Service()),
            'driftkings.views.marks_model': self.load('views.marks_model'),
            'driftkings.core.hud_visibility': module(hudVisibility=module(attach=lambda view: None, detach=lambda view: None)),
            'driftkings.gameface.battle.common': module(BattleCardAdapter=self.load('gameface.battle.common').BattleCardAdapter),
            'helpers': module(dependency=module(instance=lambda skeleton: module(shared=module(crosshair=self.crosshair)))),
            'gui.battle_control': module(avatar_getter=module(getInputHandler=lambda: None)),
            'gui.battle_control.battle_constants': module(CROSSHAIR_VIEW_ID=module(STRATEGIC=STRATEGIC)),
            'driftkings.core.battle_events': module(battleEvents=module(dispersion=module(
                connect=self.dispersion.append, disconnect=self.dispersion.remove))),
            'driftkings.core.aiming_timing': self.load('core.aiming_timing'),
            'driftkings.ui.common.events': module(g_events=module(onArmorChanged=self.armor, onMarkerColorChanged=self.colors)),
            'driftkings.game_constants': module(CTRL_MODE_NAME=module(KILL_CAM='kill', POSTMORTEM='postmortem', DEATH_FREE_CAM='free',
                                                                     RESPAWN_DEATH='respawn', VEHICLES_SELECTION='select', LOOK_AT_KILLER='killer')),
        }, real=('driftkings._constants',))

    def adapter(self, name):
        adapter = self.api[name]()
        adapter.published = []
        adapter.publish = lambda payload, config, enabled: adapter.published.append((payload, config, enabled))
        return adapter

    def rotator(self, angle, aiming=2.0):
        return module(dispersionAngle=angle, _avatar=module(vehicleTypeDescriptor=module(gun=module(aimingTime=aiming))))

    def test_countdown_follows_the_crosshair_with_the_settings_offset(self):
        adapter = self.adapter('AimingCountdownAdapter')
        adapter.startBattle()
        self.assertEqual(self.dispersion, [adapter.updateDispersion])
        # Nothing to show until the gun reports a dispersion.
        self.assertFalse(adapter.published[-1][2])
        adapter.updateDispersion(self.rotator(0.5))
        payload, config, enabled = adapter.published[-1]
        self.assertTrue(enabled)
        self.assertEqual((payload['anchorX'], round(payload['anchorY'], 4)), (0.5, round(600 / 1080.0, 4)))
        self.assertEqual(config, {'x': 60, 'y': 110, 'align': 'left', 'locked': False})
        # The first reading is the smallest angle seen, so the gun counts as fully aimed.
        self.assertEqual(payload['text'], "<font color='#D042F3'>0.0s - 100%</font>")
        # The strategic view aims at the screen centre.
        self.view = STRATEGIC
        self.crosshair.onCrosshairViewChanged(STRATEGIC)
        self.assertEqual((adapter.published[-1][0]['anchorX'], adapter.published[-1][0]['anchorY']), (0.5, 0.5))
        adapter.stopBattle()
        self.assertEqual(self.dispersion, [])
        self.assertFalse(adapter.published[-1][2])

    def test_countdown_colour_thresholds(self):
        color = self.api['AimingCountdownAdapter'].color
        settings = self.data['aiming_countdown']
        self.assertEqual([color(settings, value) for value in (0, 20, 40, 60, 80, 95)],
                         ['#FE0E00', '#FE7903', '#F8F400', '#A6FFA6', '#02C9B3', '#D042F3'])

    def test_countdown_clears_after_death_and_when_disabled(self):
        adapter = self.adapter('AimingCountdownAdapter')
        adapter.startBattle()
        adapter.updateDispersion(self.rotator(0.5))
        adapter.onCameraChanged('postmortem')
        self.assertEqual(adapter.text, '')
        adapter.updateDispersion(self.rotator(0.5))
        self.assertEqual(adapter.text, '')
        adapter.onCameraChanged('arcade')
        adapter.updateDispersion(self.rotator(0.5))
        self.data['aiming_countdown']['enabled'] = False
        adapter.refresh()
        self.assertFalse(adapter.published[-1][2])

    def test_penetration_text_is_centred_on_its_position_offset(self):
        adapter = self.adapter('PenetrationAdapter')
        adapter.startBattle()
        self.colors('green')
        self.armor((80, 120, 100, True, False))
        payload, config, enabled = adapter.published[-1]
        self.assertTrue(enabled)
        self.assertEqual(payload['text'], "RICOCHET<br><font color='#66FF33'>80 | 120</font>")
        self.assertEqual(config, {'x': 0, 'y': 40, 'align': 'center', 'locked': False})
        self.armor(None)
        self.assertFalse(adapter.published[-1][2])

    def child(self, cursor=True, gui=True):
        return module(_cursorVisible=cursor, _guiVisible=gui)

    def test_dragged_offset_is_saved_to_each_module(self):
        countdown, penetration = self.adapter('AimingCountdownAdapter'), self.adapter('PenetrationAdapter')
        countdown.startBattle()
        penetration.startBattle()
        countdown.savePosition(self.child(), {'x': 75.6, 'y': -2500})
        penetration.savePosition(self.child(), {'x': -12, 'y': 52})
        self.assertEqual(self.applied, [('aiming_countdown', {'x': 76, 'y': -2000}),
                                        ('penetration_indicator', {'position': {'x': -12, 'y': 52}})])

    def test_offset_is_not_saved_without_the_battle_cursor(self):
        adapter = self.adapter('AimingCountdownAdapter')
        adapter.savePosition(self.child(), {'x': 1, 'y': 1})
        adapter.startBattle()
        adapter.savePosition(self.child(cursor=False), {'x': 1, 'y': 1})
        adapter.savePosition(self.child(gui=False), {'x': 1, 'y': 1})
        adapter.savePosition(self.child(), {'x': 'bad', 'y': 1})
        adapter.savePosition(self.child(), None)
        self.assertEqual(self.applied, [])


class ReticleEntryPointTests(RuntimeTest):
    def test_texts_start_only_on_pages_with_the_gameface_hud(self):
        for name, adapter in (('aiming_countdown', 'AimingCountdownAdapter'), ('shell_flight_time', 'FlightTimeAdapter')):
            started = []
            hud = [True]
            fake = type(adapter, (object,), {'install': lambda self: None, 'dispose': lambda self: None,
                                              'startBattle': lambda self: started.append('start'),
                                              'stopBattle': lambda self: started.append('stop')})
            api, hooks = game_source('battle/%s.py' % name, {
                'driftkings.gameface.battle.reticle_texts': module(**{adapter: fake}),
                'driftkings.core.battle_capabilities': module(battle_capabilities=module(has_gameface_hud=lambda: hud[0])),
            }, real=('driftkings._constants',))
            self.assertIn(name + '_settings', api)
            api['init']()
            api['new_startGUI']()
            hud[0] = False
            api['new_startGUI']()
            api['new_destroyGUI']()
            self.assertEqual(started, ['start', 'stop'], name)
            api['fini']()
            self.assertIsNone(api['g_gameface'])


class QuietVisibilityTests(RuntimeTest):
    def test_texts_that_follow_the_aim_log_only_their_first_visibility_change(self):
        api, _ = game_source('gameface/battle/common.py', {
            'driftkings.gameface.payloads': module(publish_card=lambda child, payload: None),
            'driftkings.settings.service': module(settings_service=None)})
        for quiet, expected in ((False, ['info'] * 3), (True, ['info', 'debug', 'debug'])):
            calls = []
            log = module(info=lambda *args: calls.append('info'), debug=lambda *args: calls.append('debug'))
            adapter = type('Card', (api['BattleCardAdapter'],), {'QUIET_VISIBILITY': quiet})('Card', 'card', log, 'Card')
            child = module(_ready=True, _attached=True, _guiVisible=True, _cursorVisible=False, _lastVisible=None)
            parent = module(getChildView=lambda resource: child)
            adapter.views = {parent: child}
            adapter.resourceID = lambda: 7
            for enabled in (True, False, True):
                adapter.publish({}, {}, enabled)
            self.assertEqual(calls, expected, quiet)


class PenetrationSettingsTests(RuntimeTest):
    def setUp(self):
        super(PenetrationSettingsTests, self).setUp()
        api = source('settings/definitions/battle/penetration_indicator.py', {
            'driftkings._constants': self.load('_constants'),
            'driftkings.settings.controls_schema': self.load('settings.controls_schema'),
            'driftkings.settings.definitions.base': module(SectionDefinition=object),
        })
        self.definition = api['PenetrationIndicatorSettings']()
        self.definition.data = {'position': {'x': -12, 'y': 52}}

    def test_position_sliders_edit_the_dragged_offset(self):
        columns = self.definition.getControlColumns()
        sliders = dict((item['varName'], item) for item in columns[1])
        self.assertEqual(sliders['positionX']['path'], ['position', 'x'])
        self.assertEqual(sliders['positionY']['path'], ['position', 'y'])
        self.assertIn('template', [item['varName'] for item in columns[0]])
        values = self.definition.normalize_changes({'position': {'x': -12, 'y': 52}, 'positionX': 30.0}, {'positionX': 30.0})
        self.assertEqual(values, {'position': {'x': 30, 'y': 52}})
