# -*- coding: utf-8 -*-
"""Escolha do apresentador e limpeza do painel entre batalhas normais e eventos."""
from support import Event, RuntimeTest, Settings, game_source, module


class Presenter(object):
    def __init__(self):
        self.active = False
        self.starts = 0
        self.stops = 0
        self.shown = False

    def startBattle(self):
        self.active = True
        self.starts += 1

    def stopBattle(self):
        self.active = False
        self.stops += 1

    def show(self, shown):
        self.shown = shown


class TargetInformationTests(RuntimeTest):
    def setUp(self):
        super(TargetInformationTests, self).setUp()
        self.native = True
        self.fallbacks = []
        self.feedback = Event()

        def fallback():
            panel = Presenter()
            self.fallbacks.append(panel)
            return panel

        self.api, _ = game_source('battle/target_information.py', {
            'xml.sax.saxutils': module(escape=lambda value: value),
            'driftkings.settings.service': Settings({'enabled': False}).service(),
            'driftkings.core.battle_capabilities': module(battle_capabilities=module(has_gameface_hud=lambda: self.native)),
            'BigWorld': module(player=lambda: module(guiSessionProvider=module(
                shared=module(feedback=module(onVehicleFeedbackReceived=self.feedback))))),
            'driftkings.gameface.battle.screen_texts': module(TargetInformationAdapter=Presenter),
            'driftkings.flash.battle.target_information': module(Flash=fallback),
        }, real=('driftkings._constants',))

    def test_native_hud_does_not_create_a_flash_panel(self):
        panel = self.api['g_mod']
        panel.onBattleStarted()
        panel.onBattleStarted()
        self.assertIs(self.api['g_panel'], self.api['g_gameface'])
        self.assertEqual(self.fallbacks, [])
        self.assertEqual(self.api['g_gameface'].starts, 1)
        panel.onBattleEnded()
        self.assertFalse(self.api['g_gameface'].active)

    def test_event_fallback_is_stopped_before_the_next_native_battle(self):
        panel = self.api['g_mod']
        self.native = False
        panel.onBattleStarted()
        fallback = self.fallbacks[0]
        self.assertIs(self.api['g_panel'], fallback)
        panel.onBattleEnded()
        self.assertFalse(fallback.active)
        self.native = True
        panel.onBattleStarted()
        self.assertIs(self.api['g_panel'], self.api['g_gameface'])
        self.assertEqual(len(self.fallbacks), 1)
        panel.hide()
        self.assertFalse(self.api['g_gameface'].shown)
        panel.onBattleEnded()

    def test_preset_labels_come_from_the_yaml_catalog(self):
        import io
        import os
        import re
        from support import ROOT
        path = os.path.join(ROOT, 'mod', 'res', 'mods', 'driftkings', 'text', 'en.yml')
        with io.open(path, encoding='utf-8') as stream:
            catalog = dict(re.findall(r'^target_information\.(\w+): "(.*)"$', stream.read(), re.M))
        self.api['target_information_settings'] = module(i18n=catalog)
        expand = self.api['DataConstants'].expandI18n
        for name, template in self.api['PRESET_TEMPLATES'].items():
            keys = re.findall(r'\{\{i18n:(\w+)\}\}', template)
            self.assertTrue(keys, name)
            self.assertEqual([key for key in keys if key not in catalog], [], name)
            self.assertNotIn('{{i18n:', expand(template), name)
        self.assertIn('Reload (base)', expand(self.api['PRESET_TEMPLATES']['default']))
        classic = expand(self.api['PRESET_TEMPLATES']['classic'])
        self.assertEqual(self.api['TEMPLATE_INDEX_TO_KEY'][self.api['CLASSIC_PRESET']], 'classic')
        self.assertIn('{{gun_reload_equip}} s', classic)
        self.assertIn("<img src='img://gui/maps/icons/vehicle/{{icon_system_name}}.png'>", classic)
        self.assertIn("<textformat tabstops='[85,125,165]'>Type:<tab>{{shell_type_1}}<tab>{{shell_type_2}}"
                      "<tab>{{shell_type_3}}</textformat>", classic)
        self.assertIn('Damage:<tab>{{shell_damage_1}}', classic)

    def test_translated_text_is_not_expanded_again(self):
        self.api['target_information_settings'] = module(i18n={'loop': '{{i18n:loop}}', 'hp': 'PV'})
        expand = self.api['DataConstants'].expandI18n
        self.assertEqual(expand('{{i18n:loop}} {{i18n:hp}} {{l10n:missing}}'), '{{i18n:loop}} PV missing')


class TargetInformationSettingsTests(RuntimeTest):
    def setUp(self):
        super(TargetInformationSettingsTests, self).setUp()
        from support import source
        self.api = source('settings/definitions/battle/target_information.py', {
            'driftkings._constants': self.load('_constants'),
            'driftkings.settings.controls_schema': self.load('settings.controls_schema'),
            'driftkings.settings.definitions.base': module(SectionDefinition=object)})
        self.settings = self.api['TargetInformationSettings']()

    def test_only_the_retired_default_card_moves_to_the_classic_preset(self):
        retired = [u"Massa: {{vehicle_weight}} t"]
        self.api['RETIRED_DEFAULT_FORMATS'] = self.api['_formats_digest'](retired)
        values = self.settings.normalize_loaded({'formats': list(retired), 'templatePreset': 3})
        self.assertEqual(values['formats'], [])
        self.assertEqual(values['templatePreset'], 7)
        edited = [u"Peso: {{vehicle_weight}} t"]
        values = self.settings.normalize_loaded({'formats': list(edited), 'templatePreset': 3})
        self.assertEqual(values['formats'], edited)
        self.assertEqual(values['templatePreset'], 3)
        self.assertEqual(self.settings.normalize_loaded({'formats': []})['formats'], [])
