import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'source/scripts/client'))
from Driftkings.settings.panel.api import SettingsAPI, migrate_preferences
from Driftkings.settings.panel.storage import ConfigStore
from Driftkings.settings.panel.compatibility import TemplateAdapter
from Driftkings.settings.panel.presenter import Presenter
from Driftkings.settings.registry import SettingsRegistry
from Driftkings.settings.settings_data import application_timing, requires_restart, LIVE, NEXT_BATTLE, NEXT_VIEW, RESTART


class IntegratedSettingsTests(unittest.TestCase):
    def test_migration_preserves_profiles_overrides_and_existing_preferences(self):
        with tempfile.TemporaryDirectory() as temporary:
            old, new = Path(temporary)/'old', Path(temporary)/'new'
            ConfigStore(str(old)).write('dk_settings', {'language': 'pt'})
            ConfigStore(str(new)).write('dk_settings', {'language': 'en'})
            ConfigStore(str(old/'profiles')).write('replay', {'format': 'dk.settings.profile'})
            ConfigStore(str(old/'locales')).write('pt', {'title': 'Personalizado'})
            (old/'profiles'/'broken.json').write_text('invalid')
            migrate_preferences(str(new), str(old))
            self.assertEqual(ConfigStore(str(new)).read('dk_settings'), {'language': 'en'})
            self.assertEqual(ConfigStore(str(new/'profiles')).read('replay'), {'format': 'dk.settings.profile'})
            self.assertEqual(ConfigStore(str(new/'locales')).read('pt'), {'title': 'Personalizado'})
            self.assertFalse((new/'profiles'/'broken.json').exists())
            self.assertEqual((old/'profiles'/'broken.json').read_text(), 'invalid')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.api = SettingsAPI(self.temp.name)
        self.api.start('pt')
        self.values, self.defaults, self.configs = {}, {}, {}
        self.legacy = Mock(entries={})
        self.legacy.describe.side_effect = self.describe
        self.legacy.apply.side_effect = lambda key, values:self.values[key].update(values)
        self.adapter = TemplateAdapter(self.api, self.legacy)

    def add(self, name):
        self.values[name] = dict(enabled=True, angle=1.3)
        self.defaults[name] = copy.deepcopy(self.values[name])
        self.configs[name] = NS(ID=name, i18n={'UI_description': name},
                               onPanelOpened=Mock(), onPanelClosed=Mock())
        self.legacy.entries[name] = (self.configs[name], None, {}, None)

    def describe(self, key):
        return dict(title=key, values=copy.deepcopy(self.values[key]), defaults=self.defaults[key], controls=[
            dict(type='CheckBox', varName='enabled', text='Enabled'),
            dict(type='Slider', varName='angle', text='Angle', minimum=0, maximum=90, snapInterval=.1)])

    def field(self, name, key):
        return next(field for field, original in self.adapter.mapping['legacy.'+name][1].items() if original == key)

    def test_battle_only_exposes_supported_modules_and_does_not_reload_game_state(self):
        for name in ('AutoAimOptimize','InfoPanel','MainGun','Driftkings'):
            self.add(name)
        self.api.in_battle = True
        self.adapter.populate()
        self.assertEqual(set(self.adapter.mapping), {'legacy.AutoAimOptimize', 'legacy.InfoPanel'})
        for config in self.configs.values():
            config.onPanelOpened.assert_not_called()
        presenter = Presenter(self.api)
        locked = self.field('InfoPanel', 'enabled')
        presenter.handle(dict(action='set', mod='legacy.InfoPanel', key=locked, value=False))
        self.assertFalse(presenter.session.drafts)
        angle = self.field('AutoAimOptimize', 'angle')
        presenter.handle(dict(action='set', mod='legacy.AutoAimOptimize', key=angle, value=2))
        presenter.handle(dict(action='apply'))
        self.assertEqual(self.values['AutoAimOptimize']['angle'], 2)
        self.assertFalse(self.api.restart_required)

    def test_reset_and_forged_drafts_cannot_bypass_battle_restrictions(self):
        self.add('InfoPanel'); self.api.in_battle = True; self.adapter.populate()
        p = Presenter(self.api)
        locked = self.field('InfoPanel', 'enabled')
        p.session.reset('legacy.InfoPanel')
        self.assertNotIn(locked, p.session.drafts.get('legacy.InfoPanel', {}))
        p.session.drafts['legacy.InfoPanel'] = {locked: False}
        p.handle(dict(action='apply'))
        self.legacy.apply.assert_not_called()

    def test_restart_prompt_follows_save_can_be_deferred_and_tracks_reverts(self):
        self.add('ZoomExtended'); self.adapter.populate()
        p = Presenter(self.api)
        enabled = self.field('ZoomExtended','enabled')
        p.handle(dict(action='set',mod='legacy.ZoomExtended',key=enabled,value=False))
        result = p.handle(dict(action='save'))
        self.assertFalse(result['close'])
        self.assertTrue(p.state()['restartPrompt'])
        self.assertEqual(self.api.restart_required, {'ZoomExtended'})
        self.assertTrue(p.handle(dict(action='restart', choice='later'))['close'])
        self.adapter.dispose(); self.adapter.populate()
        p = Presenter(self.api)
        p.handle(dict(action='set', mod='legacy.ZoomExtended', key=enabled, value=True))
        p.handle(dict(action='apply'))
        self.assertFalse(self.api.restart_required)
        self.assertFalse(p.restart_prompt)

    def test_timing_distinguishes_runtime_callbacks_new_views_and_startup_caches(self):
        for component, field, expected in (
                ('MainGun', 'textLock', LIVE), ('MainGun', ['background', 'alpha'], LIVE),
                ('MainGun', ['background', 'image'], RESTART),
                ('CarouselStats', ['carousel', 'rows'], LIVE),
                ('HangarOptions', 'clockScale', LIVE), ('HangarOptions', 'showEventBanner', NEXT_VIEW),
                ('InfoPanel', 'enabled', NEXT_BATTLE), ('PlayerPanelPro', 'enabled', NEXT_BATTLE),
                ('OwnHealth', 'enabled', NEXT_BATTLE), ('FlightTimer', 'enabled', NEXT_BATTLE),
                ('ZoomExtended', 'disableCamAfterShotLatency', RESTART),
                ('ZoomExtended', 'noFlashBang', LIVE), ('ArcadeZoom', 'min', RESTART),
                ('BattleStat', 'textFormat', RESTART), ('BattleStat', 'format', LIVE),
                ('UnknownModule', 'enabled', RESTART)):
            with self.subTest(component=component, field=field):
                self.assertEqual(application_timing(component, field), expected)
                self.assertEqual(requires_restart(component, field), expected == RESTART)

    def test_live_and_next_battle_options_save_without_restart_and_have_hints(self):
        for name in ('MainGun', 'InfoPanel', 'FlightTimer'):
            self.add(name)
        self.adapter.populate()
        p = Presenter(self.api)
        for name in ('MainGun', 'InfoPanel', 'FlightTimer'):
            key = self.field(name, 'enabled')
            control = self.api.registry.mods['legacy.'+name].index[key]
            self.assertIn(self.api.strings['applyTiming.' + application_timing(name, 'enabled')], control.description)
            p.handle(dict(action='set', mod='legacy.'+name, key=key, value=False))
        self.assertTrue(p.handle(dict(action='save'))['close'])
        self.assertFalse(self.api.restart_required)

    def test_paths_drive_policy_even_when_control_has_a_different_ui_name(self):
        self.add('MainGun')
        self.values['MainGun']['opacity'] = 100
        self.defaults['MainGun']['opacity'] = 100
        describe = self.describe
        def mapped(key):
            result = describe(key)
            result['controls'].append(dict(type='Slider', varName='opacity', path=['background', 'alpha'],
                                            text='Opacity', minimum=0, maximum=100))
            return result
        self.legacy.describe.side_effect = mapped
        self.adapter.populate()
        p = Presenter(self.api)
        p.handle(dict(action='set', mod='legacy.MainGun', key=self.field('MainGun', 'opacity'), value=50))
        p.handle(dict(action='apply'))
        self.assertEqual(self.values['MainGun']['opacity'], 50)
        self.assertFalse(self.api.restart_required)

    def test_normalized_noop_does_not_request_restart(self):
        self.add('ZoomExtended'); self.adapter.populate()
        # A callback rejects/normalizes the value back to the existing setting.
        self.legacy.apply.side_effect = lambda key, values: None
        p = Presenter(self.api)
        p.handle(dict(action='set', mod='legacy.ZoomExtended', key=self.field('ZoomExtended', 'enabled'), value=False))
        p.handle(dict(action='apply'))
        self.assertFalse(self.api.restart_required)

    def test_real_registry_saves_decimal_slider_with_integer_default(self):
        config = NS(ID='CarouselStats', i18n={}, data={'scale': 1, 'rows': 2},
                    onPanelOpened=lambda: None, onPanelClosed=lambda: None)
        config.createTemplate = lambda: dict(column1=[
            dict(type='Slider', varName='scale', minimum=.1, maximum=4, snapInterval=.1),
            dict(type='Slider', varName='rows', minimum=0, maximum=4, snapInterval=1)])
        saved = Path(self.temp.name)/'carousel.json'
        def apply(changes):
            config.data.update(changes)
            saved.write_text(json.dumps(config.data))
        config.onApplySettings = apply
        registry = SettingsRegistry()
        registry.register(config)
        self.adapter = TemplateAdapter(self.api, registry)
        self.adapter.populate()
        presenter = Presenter(self.api)
        for scale in (1.3, 3, 1.7):
            presenter.handle(dict(action='set', mod='legacy.CarouselStats',
                                 key=self.field('CarouselStats', 'scale'), value=scale))
            presenter.handle(dict(action='apply'))
            self.assertEqual(config.data['scale'], scale)
            self.assertEqual(json.loads(saved.read_text())['scale'], scale)
        for patch in ({'scale': 1.3, 'rows': 2.5}, {'scale': 4.1, 'rows': 2}):
            with self.assertRaises(ValueError):
                registry.apply('CarouselStats', patch)
        self.assertEqual(config.data, {'scale': 1.7, 'rows': 2})

    def test_restart_requires_pending_prompt_saved_changes_and_hangar(self):
        p = Presenter(self.api)
        self.assertNotIn('restart', p.handle(dict(action='restart', choice='now')))
        self.api.restart_required.add('MainGun')
        p.restart_prompt = True; self.api.in_battle = True
        self.assertNotIn('restart', p.handle(dict(action='restart', choice='now')))
        self.api.in_battle = False
        self.assertTrue(p.handle(dict(action='restart', choice='now'))['restart'])

    def test_battle_profile_requests_cannot_load_hangar_settings(self):
        self.api.in_battle = True
        p = Presenter(self.api)
        p.profiles.load = Mock()
        p.handle(dict(action='profile',operation='load',name='example'))
        p.profiles.load.assert_not_called()

    def test_framework_is_internal_and_game_entrypoint_remains_single(self):
        client = ROOT/'source/scripts/client'
        self.assertFalse((client/'dk_settings').exists())
        self.assertFalse((client/'Driftkings/components/settings_window.py').exists())
        self.assertTrue((client/'Driftkings/settings/settings_data.py').exists())
        self.assertFalse([p for p in (client/'Driftkings').rglob('*.py') if p.stem[0].isupper()])
