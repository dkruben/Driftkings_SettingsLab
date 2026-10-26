# -*- coding: utf-8 -*-
"""XVM-style marker files map onto the runtime profiles with XVM's own geometry."""
import copy
import json
import os

from support import ROOT, RuntimeTest

DIRECTORY = os.path.join(ROOT, 'res', 'configs', 'driftkings', 'default', 'vehicle_markers')


class VehicleMarkersXvmTests(RuntimeTest):
    def setUp(self):
        super(VehicleMarkersXvmTests, self).setUp()
        self.xvm = self.load('core.vehicle_markers.xvm')
        documents = {}
        for name in self.xvm.FILES:
            with open(os.path.join(DIRECTORY, name), 'rb') as stream:
                documents[name] = json.loads(stream.read().decode('utf-8'))
        self.documents = documents
        self.data = self.xvm.join(documents)

    def profiles(self, data=None):
        prepared = self.load('core.vehicle_markers.config').prepare(copy.deepcopy(data or self.data))
        return prepared['customFields']['profiles']

    def test_files_follow_xvm_layout_without_xmqp(self):
        self.assertEqual(sorted(os.listdir(DIRECTORY)), sorted(self.xvm.FILES))
        markers = self.documents['markers.json']['markers']
        self.assertEqual(markers['enemy']['dead']['extended'], '${markersDeadExtended.json:enemy}')
        text = json.dumps(self.documents)
        self.assertNotIn('xmqp', text.lower())
        self.assertNotIn('x-spotted', text)
        normal = self.documents['markersAliveNormal.json']
        self.assertEqual(normal['ally']['textFields'], ['${def.tankName}', '${def.playerName}', '${def.tankHp}', '${def.rating}'])
        self.assertEqual(normal['enemy']['textFields'], ['${def.tankName}', '${def.tankHp}', '${def.rating}', '${def.position}'])
        self.assertEqual(normal['ally']['damageText'], {'$ref': {'path': 'def.damageText'}})

    def test_defaults_keep_xvm_layout_and_eu_customizations(self):
        normal = self.documents['markersAliveNormal.json']
        self.assertEqual(normal['ally']['healthBar']['width'], 70)
        self.assertEqual(normal['ally']['healthBar']['damage']['color'], '{{c:dmg}}')
        self.assertEqual(normal['def']['rating']['textFormat']['font'], 'XVMSymbol')
        self.assertIn('<b>!</b>', normal['def']['rating']['format'])
        self.assertEqual(normal['def']['tankName']['format'], '{{vehicle}}{{turret}}')
        self.assertEqual(self.documents['markersAliveExtended.json']['def']['hpPercent']['format'], '{{hp-ratio}}% / {{hp-max}}')

    def test_text_fields_use_xvm_boxes_anchored_by_alignment(self):
        profile = self.profiles()['enemy']['alive']['normal']
        names = [field['name'] for field in profile['fields']]
        # The EU layout disables the distance field in normal mode.
        self.assertEqual(names, ['Tank name', 'Tank HP', 'Rating', 'position'])
        tank = profile['fields'][0]
        self.assertEqual((tank['x'], tank['y'], tank['width'], tank['height']), (-70, -51, 140, 100))
        # The HP text sits inside the bar (-33..-21) and the tank name just above it.
        bar = profile['healthBar']
        self.assertEqual(profile['fields'][1]['y'], -35)
        self.assertTrue(bar['y'] - 3 <= profile['fields'][1]['y'] <= bar['y'])
        self.assertLessEqual(tank['y'] + 15, bar['y'])
        rating = profile['fields'][2]
        # The right-aligned box ends at the configured anchor; use the client font.
        self.assertEqual((rating['x'], rating['align']), (-160, 'right'))
        self.assertIn('<b>!</b>', rating['format'])
        self.assertEqual(rating['textFormat']['font'], '$FieldFont')
        self.assertEqual(rating['textFormat']['color'], '{{c:xr|#999999}}')
        self.assertEqual(profile['fields'][3]['shadow']['color'], '{{c:system}}')

    def test_damage_health_bar_and_native_flags(self):
        profile = self.profiles()['ally']['alive']['normal']
        damage = profile['damageText']
        self.assertEqual((damage['x'], damage['y'], damage['width']), (-100, -66, 200))
        self.assertEqual((damage['duration'], damage['rise']), (2, 40))
        self.assertEqual(damage['format'], '{{dmg}}')
        self.assertEqual(damage['textFormat']['color'], '{{c:dmg}}')
        for source in ('player', 'squad', 'other'):
            self.assertTrue(damage['sources'][source]['enabled'])
        bar = profile['healthBar']
        self.assertEqual((bar['x'], bar['y'], bar['width'], bar['height']), (-36, -31, 70, 12))
        self.assertEqual(bar['border'], {'color': '#000000', 'alpha': 35, 'width': 1})
        self.assertEqual((bar['fill']['alpha'], bar['damage']['color'], bar['damage']['duration']), (50, '{{c:dmg}}', 1))
        self.assertFalse(bar['gradient']['enabled'])
        self.assertEqual(profile['native']['hp'], 'hidden')
        self.assertFalse(profile['native']['vehicleName'])
        dead = self.profiles()['ally']['dead']['normal']
        self.assertFalse(dead['healthBar']['enabled'])
        self.assertEqual(dead['fields'], [])

    def test_icons_follow_xvm_positions(self):
        icons = self.profiles()['enemy']['alive']['normal']['icons']
        self.assertEqual((icons['class']['containerX'], icons['class']['containerY']), (0, -16))
        self.assertFalse(icons['class']['showSpeaker'])
        self.assertTrue(icons['level']['enabled'])
        self.assertEqual((icons['actionMarker']['y'], icons['hoverMarker']['y']), (-86, -92))
        self.assertEqual(icons['hoverMarker']['glow'], {'enabled': True, 'x': 0, 'y': 150, 'alpha': 50})
        self.assertEqual((icons['damageIndicator']['x'], icons['damageIndicator']['y']), (53, -27))
        self.assertEqual((icons['damageIndicatorText']['x'], icons['damageIndicatorText']['y']), (67, -41))
        self.assertEqual(icons['vehicle']['tint'], {'color': '{{c:system}}', 'amount': 0})

    def test_distance_offsets_speaker_and_hidden_indicator_text(self):
        data = copy.deepcopy(self.data)
        block = data['markersAliveNormal']['enemy']
        block['vehicleDist'] = dict(block['vehicleDist'], enabled=True)
        block['vehicleIcon'].update(offsetX=4, offsetY=-2, showSpeaker=True)
        block['damageIndicator']['showText'] = False
        block['contourIcon'].update(enabled=True, color='0xFF0000', amount=60)
        profile = self.profiles(data)['enemy']['alive']['normal']
        distance = profile['fields'][-1]
        self.assertEqual(distance['format'], '{{alive&&distance?{{distance}}m|}}')
        self.assertEqual((distance['x'], distance['y'], distance['width']), (-50, -84, 100))
        self.assertEqual((profile['icons']['class']['containerX'], profile['icons']['class']['containerY']), (4, -18))
        self.assertTrue(profile['icons']['class']['showSpeaker'])
        self.assertFalse(profile['icons']['damageIndicatorText']['enabled'])
        self.assertEqual(profile['icons']['vehicle']['tint'], {'color': '0xFF0000', 'amount': 60})
        self.assertTrue(profile['native']['vehicleIcon'])

    def test_wiring_can_reuse_another_state_and_rejects_unknown_files(self):
        data = copy.deepcopy(self.data)
        data['markers']['enemy']['dead']['extended'] = '${markersAliveExtended.json:ally}'
        profile = self.profiles(data)['enemy']['dead']['extended']
        self.assertEqual([field['name'] for field in profile['fields']], ['Player name', 'Percent of HP', 'Rating'])
        for wiring in ('${markersOther.json:ally}', '${markersAliveNormal.json:squad}', 7):
            data['markers']['ally']['alive']['normal'] = wiring
            with self.assertRaises(ValueError):
                self.profiles(data)

    def test_switched_off_markers_keep_native_presentation(self):
        data = copy.deepcopy(self.data)
        data['enabled'] = False
        prepared = self.load('core.vehicle_markers.config').prepare(data)
        self.assertFalse(prepared['enabled'])
        self.assertFalse(prepared['markers']['enabled'])
        self.assertIsNone(prepared['customFields']['profiles']['ally']['alive']['normal']['fields'])

    def test_general_settings_split_and_join_without_loss(self):
        files = dict(self.xvm.split(self.data))
        self.assertEqual(files['markers.json'], self.documents['markers.json'])
        self.assertEqual(self.xvm.join(files), self.data)

    def test_flash_never_uses_replace_callbacks(self):
        # Scaleform inserts the callback's source text instead of calling it.
        import re
        for folder, _, names in os.walk(os.path.join(ROOT, 'flash_source')):
            for name in names:
                if name.endswith('.as'):
                    with open(os.path.join(folder, name), 'rb') as stream:
                        text = stream.read().decode('utf-8')
                    self.assertIsNone(re.search(r'\.replace\([^\n]*,\s*function\b', text), name)

    def test_null_options_are_unset_like_missing_ones(self):
        # XVM treats null as "not set"; the settings window preview does the same, so the battle must agree.
        xvm = self.xvm
        self.assertEqual(xvm.health_bar({'x': None, 'y': None, 'width': None, 'height': None, 'alpha': None,
                                         'border': None, 'fill': None, 'damage': None}, False), xvm.health_bar({}, False))
        self.assertEqual(xvm.health_bar({'border': {'alpha': None, 'size': None}, 'fill': {'alpha': None},
                                         'damage': {'alpha': None, 'fade': None}}, True), xvm.health_bar({}, True))
        nulls = dict((key, None) for key in ('x', 'y', 'offsetX', 'offsetY', 'alpha', 'enabled'))
        self.assertEqual(xvm.icons({'vehicleIcon': nulls, 'damageIndicator': dict(nulls, showText=None),
                                    'levelIcon': None, 'hoverMarker': {'glow': None}}),
                         xvm.icons({'levelIcon': {'enabled': False}}))
        field = dict((key, None) for key in ('x', 'y', 'width', 'height', 'align', 'alpha', 'enabled', 'format', 'name'))
        self.assertEqual(xvm.text_field(field), xvm.text_field({}))
        self.assertEqual(xvm.damage_text(dict(field, speed=None, maxRange=None, damageMessage=None, blowupMessage=None)),
                         xvm.damage_text({}))
        data = copy.deepcopy(self.data)
        data['markersAliveNormal']['ally'] = {'textFields': None}
        self.assertEqual(xvm.adapt(data)['customFields']['ally']['alive']['normal'], [])

    def test_private_font_aliases_use_client_glyphs_and_preserve_custom_text(self):
        for font in ('xvm', 'XVMSymbol'):
            field = self.xvm.text_field({'format': '&#x115; <b>!</b>', 'textFormat': {'font': font}})
            self.assertEqual(field['format'], u'\u2022 <b>!</b>')
            self.assertEqual(field['textFormat']['font'], '$FieldFont')
