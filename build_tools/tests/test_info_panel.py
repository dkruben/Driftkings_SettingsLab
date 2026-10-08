from settings_support import settings_globals
import ast
import re
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/scripts/client'))
from Driftkings.settings.settings_data import defaults
from Driftkings.settings.settings_data import SettingsData
from Driftkings.settings.service import SettingsService
from Driftkings._constants import INFO_PANEL, MINIMAP_PLUGINS
from Driftkings.core.overlay import OverlayScene, ElementType, Align


class Clock:
    def __init__(self):
        self.now = 0
        self.pending = {}
        self.sequence = 0

    def callback(self, delay, fn):
        self.sequence += 1
        self.pending[self.sequence] = (self.now + delay, fn)
        return self.sequence

    def cancelCallback(self, ident):
        del self.pending[ident]  # Detect cancellation of an already consumed ID.

    def advance(self, seconds):
        self.now += seconds
        for ident, (deadline, fn) in list(self.pending.items()):
            if deadline <= self.now:
                del self.pending[ident]
                fn()


class InfoPanelTests(unittest.TestCase):
    def setUp(self):
        tree = ast.parse((ROOT / 'source/scripts/client/Driftkings/battle/info_panel.py').read_text(encoding='utf-8'))
        nodes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name in ('DataConstants', 'InfoPanel')]
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in ('new__targetBlur', 'new__targetFocus'):
                node.decorator_list = []
                nodes.append(node)
        self.clock = Clock()
        self.config = types.SimpleNamespace(ID='InfoPanel', data=defaults('InfoPanel'))
        self.flash = Mock(active=True)
        self.vehicle = types.SimpleNamespace(publicInfo=types.SimpleNamespace(team=2), isAlive=lambda:True,
                                             typeDescriptor=types.SimpleNamespace(gun=types.SimpleNamespace(shots=[])))
        self.player = types.SimpleNamespace(team=1, getVehicleAttached=lambda:self.vehicle)
        self.held = False
        self.target = None
        self.ns = dict(config=self.config, BigWorld=self.clock, g_flash=self.flash, re=re, escape=escape,
                       getPlayer=lambda:self.player, getTarget=lambda:self.target,
                       checkKeys=lambda keys:self.held, TEMPLATE_INDEX_TO_KEY={0:'default',3:'full'},
                       PRESET_TEMPLATES={'default':'default','full':'fallback'})
        settings_globals(self.ns, 'battle.info_panel', 'views.battle.info_panel')
        self.service = self.ns['settings_service'] = SettingsService(SettingsData())
        self.ns['battleEvents'] = Mock()
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'InfoPanel','exec'),self.ns)
        self.panel = self.ns['InfoPanel']()
        self.ns['g_mod'] = self.panel
        self.panel._inBattle = True
        self.panel.setTextsFormatted = lambda:'tank'

    def show(self):
        self.panel.onUpdateVehicle(self.vehicle)
        self.assertTrue(self.panel.visible)

    def test_delay_starts_on_blur_and_repeated_blurs_do_not_extend_it(self):
        self.show()
        self.clock.advance(20)
        self.assertTrue(self.panel.visible)
        self.panel.onUpdateBlur()
        self.clock.advance(4)
        self.panel.onUpdateBlur()
        self.assertTrue(self.panel.visible)
        self.clock.advance(1)
        self.assertFalse(self.panel.visible)
        self.flash.setVisible.assert_called_with(False)
        self.assertIsNone(self.panel.timer)
        self.assertFalse(self.clock.pending)

    def test_reacquire_cancels_previous_deadline(self):
        self.show(); self.panel.onUpdateBlur(); self.clock.advance(4)
        self.show(); self.clock.advance(2)
        self.assertTrue(self.panel.visible)
        self.assertFalse(self.clock.pending)
        self.panel.onUpdateBlur(); self.clock.advance(5)
        self.assertFalse(self.panel.visible)

    def test_removed_or_dead_target_and_missing_attached_vehicle_still_hide(self):
        self.show()
        self.config.data['aliveOnly'] = True
        self.vehicle.isAlive = lambda:False
        self.player.getVehicleAttached = lambda:None
        original = Mock(return_value=73)
        self.assertEqual(self.ns['new__targetBlur'](original,self.player,None),73)
        self.clock.advance(5)
        self.assertFalse(self.panel.visible)
        original.assert_called_once_with(self.player,None)

    def test_filtered_focus_schedules_hide_and_zero_delay_is_immediate(self):
        self.show(); self.config.data['showFor'] = 1
        self.ns['new__targetFocus'](lambda *args:None,self.player,self.vehicle)
        self.clock.advance(5)
        self.assertFalse(self.panel.visible)
        self.show(); self.config.data['delay'] = 0
        self.panel.onUpdateBlur()
        self.assertFalse(self.panel.visible)
        self.assertFalse(self.clock.pending)

    def test_alt_self_information_ignores_blur_then_hides_on_release(self):
        self.held = True
        self.panel.keyPressed(types.SimpleNamespace(isKeyDown=lambda:True,isKeyUp=lambda:False))
        self.panel.onUpdateBlur(); self.clock.advance(10)
        self.assertTrue(self.panel.visible)
        self.assertFalse(self.clock.pending)
        self.held = False
        self.panel.keyPressed(types.SimpleNamespace(isKeyDown=lambda:False,isKeyUp=lambda:True))
        self.assertFalse(self.panel.visible)

    def test_end_cancels_timer_and_next_battle_starts_hidden(self):
        self.show(); self.panel.onUpdateBlur(); self.panel.onBattleEnded()
        self.assertFalse(self.clock.pending)
        self.panel.onBattleStarted(); self.clock.advance(10)
        self.assertFalse(self.panel.visible)

    def test_full_format_uses_supported_macros_and_keeps_unicode(self):
        text = self.panel.getText()
        self.assertIn('Penetração',text)
        self.assertIn('img://gui/maps/icons/vehicle/',text)
        macros = set(re.findall(r'\{\{([^{}]+)\}\}',text))
        self.assertFalse(macros - set(self.panel._macroHandlers))
        self.config.data['templatePreset'] = 0
        self.assertEqual(self.panel.getText(),'default')

    def test_content_notifications_preserve_blur_deadline_and_disconnect(self):
        self.panel.start(); self.panel.start()
        self.show(); self.panel.onUpdateBlur()
        timer = self.panel.timer
        self.clock.advance(3)
        self.flash.addText.reset_mock()
        self.service.apply(self.config, {'textLock':True, 'backgroundAlpha':0.5}, persist=False)
        self.flash.addText.assert_not_called()
        self.service.apply(self.config, {'formats':['new content']}, persist=False)
        self.flash.addText.assert_called_once_with('tank')
        self.assertEqual(self.panel.textFormats, 'new content')
        self.assertEqual(self.panel.timer, timer)
        self.clock.advance(2)
        self.assertFalse(self.panel.visible)
        self.panel.stop(); self.panel.stop()
        self.assertFalse(self.service.onModSettingsChanged._listeners)
        self.ns['battleEvents'].acquire.assert_called_once_with(self.panel)
        self.ns['battleEvents'].release.assert_called_once_with(self.panel)

    def test_hidden_content_changes_do_not_render_and_disable_cancels_pending_hide(self):
        self.panel.start()
        self.flash.addText.reset_mock()
        self.service.apply(self.config, {'formats':['hidden content']}, persist=False)
        self.flash.addText.assert_not_called()
        self.show(); self.panel.onUpdateBlur()
        self.service.apply(self.config, {'enabled':False}, persist=False)
        self.assertFalse(self.panel.visible)
        self.assertFalse(self.clock.pending)
        self.assertIsNone(self.panel.textFormats)
        self.panel.stop()


class InfoPanelHtmlTests(unittest.TestCase):
    def render(self, text, leading):
        path = ROOT / 'source/scripts/client/Driftkings/views/battle/info_panel.py'
        tree = ast.parse(path.read_text(encoding='utf-8'))
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'Flash')
        method = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == 'addText')
        settings = defaults('InfoPanel')
        settings['textFormat']['leading'] = leading
        config = types.SimpleNamespace(data=settings)
        ns = dict(re=re, escape=escape, _component=lambda:types.SimpleNamespace(config=config),
                  ElementType=types.SimpleNamespace(LABEL='label'))
        settings_globals(ns, 'battle.info_panel', 'views.battle.info_panel')
        exec(compile(ast.Module(body=[method], type_ignores=[]), str(path), 'exec'), ns)
        view = Mock()
        ns['addText'](view, text)
        return view.updateObject.call_args.args[1]['text']

    def test_old_spacing_and_extended_tags_are_compatible_without_config_replacement(self):
        html = self.render("<b>Tanque</b><BR>Casco:<tab>100<br/>Torre:<TAB/>80<br />Dano: 240", -12)
        self.assertIn("leading='0'", html)
        self.assertEqual(html.count('<br>'), 3)
        self.assertEqual(html.count('\t'), 2)
        self.assertIn('<b>Tanque</b>', html)

    def test_positive_spacing_images_and_column_stops_survive(self):
        text = "<img src='img://tank.png'><br/><textformat tabstops='[65,105,145]'>Penetração:<tab>230<tab>330</textformat>"
        html = self.render(text, 3)
        self.assertIn("leading='3.0'", html)
        self.assertIn("<img src='img://tank.png'>", html)
        self.assertIn("tabstops='[65,105,145]'", html)
        self.assertIn('Penetração:\t230\t330', html)

    def test_empty_content_remains_empty(self):
        self.assertEqual(self.render('', -12), '')


class InfoPanelViewSettingsTests(unittest.TestCase):
    def setUp(self):
        path = ROOT / 'source/scripts/client/Driftkings/views/battle/info_panel.py'
        tree = ast.parse(path.read_text(encoding='utf-8'))
        tree.body = [node for node in tree.body if isinstance(node, ast.ClassDef)]
        self.config = types.SimpleNamespace(ID='InfoPanel', data=defaults('InfoPanel'))
        self.scene = OverlayScene()
        self.resetters = set()
        ns = dict(re=re, escape=escape, _component=lambda:types.SimpleNamespace(config=self.config),
                  overlays=self.scene, ElementType=ElementType, Align=Align, g_guiResetters=self.resetters,
                  dependency=types.SimpleNamespace(descriptor=lambda _:None), ISettingsCore=object())
        settings_globals(ns, 'views.battle.info_panel')
        self.service = ns['settings_service'] = SettingsService(SettingsData())
        exec(compile(tree, str(path), 'exec'), ns)
        self.view = ns['Flash']()
        self.addCleanup(self.view.stopBattle)

    def test_text_style_reuses_raw_content_without_nested_wrappers_or_showing_hidden_panel(self):
        view = self.view
        view.startBattle(); view.startBattle()
        view.addText('Casco<BR>100')
        view.setVisible(True)
        for size in (18,20):
            self.service.apply(self.config, {'textFormat':{'size':size}}, persist=False)
            props = self.scene.elements['InfoPanel'][1]
            self.assertIn("size='%s'" % size, props['text'])
            self.assertEqual(props['text'].count('<textformat '),1)
            self.assertIn('Casco<br>100',props['text'])
        view.setVisible(False)
        self.service.apply(self.config, {'textFormat':{'size':22}}, persist=False)
        self.assertFalse(self.scene.elements['InfoPanel'][1]['visible'])
        view.stopBattle(); view.stopBattle()
        self.assertFalse(self.scene.elements)
        self.assertFalse(self.scene.updated.listeners)
        self.assertFalse(self.service.onModSettingsChanged._listeners)
        self.assertFalse(self.resetters)
        view.startBattle()
        self.assertEqual(view._text,'')
        self.assertEqual(self.scene.elements['InfoPanel'][1]['text'],'')

    def test_background_and_position_keep_text_and_ignore_other_modules(self):
        self.view.startBattle()
        self.view.addText('Veículo')
        original = self.scene.elements['InfoPanel'][1]['text']
        self.view.applyConfig = Mock(wraps=self.view.applyConfig)
        self.service.onModSettingsChanged.emit(MINIMAP_PLUGINS.NAME, {'textLock':True})
        self.view.applyConfig.assert_not_called()
        self.service.apply(self.config, {'textPosition':{'x':42}, 'textLock':True,
                          'backgroundEnabled':True, 'backgroundAlpha':0.4}, persist=False)
        self.view.applyConfig.assert_called_once()
        props = self.scene.elements['InfoPanel'][1]
        self.assertEqual(props['x'],42)
        self.assertFalse(props['drag'])
        self.assertEqual(props['customBackground']['alpha'],0.4)
        self.assertEqual(props['text'],original)
