# -*- coding: utf-8 -*-
"""Minimap policy (ranges, validation, labels, colours) and the four-document settings store."""
import json
import os
import shutil
import sys
import tempfile
import types

from support import CLIENT, RuntimeTest, module, source

ROOT = os.path.join(os.path.dirname(__file__), '..', '..', 'res', 'configs', 'driftkings', 'default', 'minimap_enhancements')


def defaults():
    data = {}
    for name in ('minimap.json', 'minimap_labels.json', 'minimap_circles.json', 'minimap_lines.json'):
        with open(os.path.join(ROOT, name), 'rb') as stream:
            data.update(json.loads(stream.read().decode('utf-8-sig')))
    return data


class MinimapPolicyTests(RuntimeTest):
    def setUp(self):
        super(MinimapPolicyTests, self).setUp()
        self.policy = self.load('core.minimap')

    def shot(self, cd, distance):
        return module(shell=module(compactDescr=cd), maxDistance=distance)

    def test_shell_range_follows_the_selected_shell(self):
        descriptor = module(gun=module(shots=[self.shot(1, 720.0), self.shot(2, 1250.0)]), shot=self.shot(1, 720.0))
        self.assertEqual(self.policy.shell_range(descriptor, 2), 1250.0)
        self.assertEqual(self.policy.shell_range(descriptor, 1), 720.0)
        # Unknown or missing shell: the active shot of the descriptor.
        self.assertEqual(self.policy.shell_range(descriptor, 99), 720.0)
        self.assertIsNone(self.policy.shell_range(None, 1))

    def test_defaults_enable_hull_line_marks_and_shell_circle(self):
        data = defaults()
        self.policy.validate(data)
        self.assertTrue(data['lines']['hull'])
        self.assertEqual(data['lines']['marks'], 100)
        self.assertEqual(data['circles']['shell']['mode'], 'on')

    def test_html_map_size_and_shadow_validation(self):
        data = defaults()
        self.policy.validate(data)
        self.assertIn('<font', data['mapSize']['format'])
        for key, value in (('alpha', 101), ('width', 0), ('offsetX', -301), ('shadow', False)):
            broken = defaults()
            broken['mapSize'][key] = value
            self.assertRaises(ValueError, self.policy.validate, broken)
        data['mapSize']['shadow']['color'] = 'invalid'
        self.assertRaises(ValueError, self.policy.validate, data)

    def test_invalid_new_options_are_rejected(self):
        for section, key, value in (('lines', 'hull', 'yes'), ('lines', 'marks', 600), ('lines', 'hullColor', 'green')):
            data = defaults()
            data[section][key] = value
            self.assertRaises(ValueError, self.policy.validate, data)
        data = defaults()
        data['circles']['shell']['mode'] = 'client'
        self.assertRaises(ValueError, self.policy.validate, data)
        data = defaults()
        del data['circles']['shell']
        self.assertRaises(ValueError, self.policy.validate, data)

    def test_groups_follow_native_gui_properties(self):
        group = self.policy.vehicle_group
        self.assertEqual([group('ally', False), group('teamKiller', False), group('squadman', False), group('enemy', True)],
                         ['ally', 'teamKiller', 'squad', 'enemy'])
        # A squadmate is never an enemy; a missing label falls back to the side.
        self.assertEqual((group(None, True), group('', False)), ('enemy', 'ally'))

    def test_team_colors_come_from_the_shared_scheme(self):
        system = self.load('common.utils.color_rating_data').system_colors
        color = self.policy.team_color
        self.assertEqual(color('enemy', 'dead'), system['enemy_dead'])
        self.assertEqual(color('squad', 'alive'), system['squadman_alive'])
        self.assertEqual(color('teamKiller', 'dead'), system['teamKiller_dead'])
        # Lost vehicles keep the alive colour; the icon is desaturated instead.
        self.assertEqual(color('ally', 'lost'), system['ally_alive'])

    def test_palettes_share_the_tables_that_do_not_depend_on_the_rating(self):
        data = self.load('common.utils.color_rating_data')
        for key, table in (('system', data.system_colors), ('vtype', data.vehicle_type_colors),
                           ('totalHP', data.total_hp_colors), ('damage', data.damage_colors)):
            self.assertTrue(data.noob_meter_colors[key] is data.driftkings_colors[key] is data.wot_life_colors[key] is table, key)

    def test_dead_and_lost_options_are_validated(self):
        for section, key, value in (('icons', 'deadAlpha', 150), ('lostMarker', 'desaturate', -1),
                                    ('labels', 'teamColors', 1), ('labels', 'teamKillerColor', 'blue')):
            data = defaults()
            data[section][key] = value
            self.assertRaises(ValueError, self.policy.validate, data)

    def test_vehicle_names_cover_tag_and_display_name(self):
        names = self.policy.vehicle_names('germany:G04_PzVI_Tiger_I', 'Tiger I')
        self.assertEqual(names, ['germany-g04_pzvi_tiger_i', 'g04_pzvi_tiger_i', 'tiger i'])
        self.assertEqual(self.policy.vehicle_names('', None), [])

    def test_state_scales_nearby_and_vehicle_circles_are_validated(self):
        data = defaults()
        data['extraCircles'] = [{'radius': 445, 'alpha': 60, 'color': 'FFFFFF', 'thickness': 1, 'dash': 0,
                                 'gap': 5, 'vehicleClass': 'all', 'vehicle': 'Tiger I'}]
        self.policy.validate(data)
        for section, key, value in (('icons', 'deadScale', 0.1), ('icons', 'lostScale', 4), ('lines', 'triangleAlpha', 120),
                                    ('lines', 'directionAlpha', -5), ('nearby', 'range', 'radar'),
                                    ('nearby', 'distance', 10), ('nearby', 'enabled', 'yes'), ('nearby', 'color', 'red')):
            broken = defaults()
            broken[section][key] = value
            self.assertRaises(ValueError, self.policy.validate, broken)
        data['extraCircles'][0]['vehicle'] = 'x' * 65
        self.assertRaises(ValueError, self.policy.validate, data)

    def test_last_positions_use_a_dull_team_colour(self):
        lost = defaults()['lostMarker']
        self.assertEqual(lost['style'], 'tint')
        self.assertEqual(self.policy.marker_color('enemy', 'lost', lost), '#' + lost['enemyColor'])
        self.assertEqual(self.policy.marker_color('squad', 'lost', lost), '#' + lost['squadColor'])
        self.assertEqual(self.policy.marker_color('teamKiller', 'lost', lost), '#' + lost['allyColor'])
        # Spotted and destroyed vehicles keep the team scheme; grey style keeps the alive colour.
        self.assertEqual(self.policy.marker_color('enemy', 'dead', lost), self.policy.team_color('enemy', 'dead'))
        grey = dict(lost, style='grey')
        self.assertEqual(self.policy.marker_color('enemy', 'lost', grey), self.policy.team_color('enemy', 'alive'))

    def test_lost_style_and_colours_are_validated(self):
        for key, value in (('style', 'blue'), ('enemyColor', 'red'), ('allyColor', None)):
            data = defaults()
            data['lostMarker'][key] = value
            self.assertRaises(ValueError, self.policy.validate, data)

    def test_labels_render_plain_text_with_limits(self):
        render = self.policy.render
        self.assertEqual(render(u'{{vehicle}} {{name%.6s}}', {'vehicle': 'T-34', 'name': 'LongPlayerName'}), u'T-34 Long..')
        # Unknown macros stay, missing values are empty and player HTML is stripped.
        self.assertEqual(render(u'{{unknown}}|{{hp}}', {}), u'{{unknown}}|')
        self.assertEqual(render(u'{{name}}', {'name': '<b>x</b>'}), u'bx/b')
        self.assertEqual(render(b'{{level}}', {'level': 8}), u'8')
        self.assertEqual(len(render(u'x' * 400, {})), 256)

    def test_label_template_follows_state_group_and_alternative_mode(self):
        options = dict(defaults()['labels'], enemy=u'E {{vehicle}}', alternativeEnemy=u'',
                       dead=u'D {{vehicle}}', lost=u'L {{lostSeconds}}')
        values = {'vehicle': 'IS-7', 'name': 'Player', 'group': 'enemy', 'lostSeconds': 12}
        label = self.policy.label
        self.assertEqual(label(options, dict(values, state='alive')), u'E IS-7')
        # An empty group template falls back to the general alternative one.
        self.assertEqual(label(options, dict(values, state='alive'), alternative=True), u'IS-7 \u00b7 Player')
        self.assertEqual(label(options, dict(values, state='dead')), u'D IS-7')
        self.assertEqual(label(options, dict(values, state='lost'), alternative=True), u'L 12')
        self.assertEqual(label(dict(options, enabled=False), dict(values, state='alive')), u'')

    def test_health_values_reject_unknown_or_inconsistent_health(self):
        health = self.policy.health_values
        self.assertEqual(health(750, 1500), {'hp': 750, 'maxHp': 1500, 'hpPercent': 50})
        self.assertEqual(health(-20, 1500)['hp'], 0)
        self.assertEqual(health(None, 1500), {'hp': '--', 'maxHp': 1500, 'hpPercent': '--'})
        self.assertEqual(health(2000, 1500)['hpPercent'], '--')
        self.assertEqual(health(10, 0)['maxHp'], '--')

    def test_visibility_modes_and_artillery_aim_choices(self):
        visible = self.policy.visible
        self.assertEqual([visible('client', True), visible('client', False), visible('on', False), visible('off', True)],
                         [True, False, True, False])
        self.assertEqual(self.policy.artillery_aim_choices('gui/maps/custom.png')[-1], 'gui/maps/custom.png')
        self.assertEqual(len(self.policy.artillery_aim_choices(self.policy.ARTILLERY_AIMS[3])), 7)


class MinimapStoreTests(RuntimeTest):
    def setUp(self):
        super(MinimapStoreTests, self).setUp()
        self.root = tempfile.mkdtemp(prefix='dk-minimap-test-')
        self.addCleanup(shutil.rmtree, self.root)
        # Real imports for the stores: source() runs Python 2.7 in restricted mode, without file access.
        package = types.ModuleType('driftkings.settings')
        package.__path__ = [os.path.join(CLIENT, 'settings')]
        sys.modules['driftkings.settings'] = package
        store = self.load('settings.store')
        sys.modules['driftkings.settings.loader'] = module(validate_types=source('settings/loader.py', {
            'driftkings.settings.settings_data': module(SettingsData=object, user_settings={}, part_name=lambda value: value),
            'driftkings.settings.default_values': module(SELECTOR={'loadConfig': 'default'}),
            'driftkings.settings.sections': module(previous_name=None, previous_sections=None, section_aliases=None),
            'driftkings.settings.store': store})['validate_types'])
        self.api = vars(self.load('settings.minimap_store'))
        self.store = self.api['MinimapStore'](self.root)

    def read(self, name):
        with open(os.path.join(self.root, name), 'rb') as stream:
            return json.loads(stream.read().decode('utf-8'))

    def test_first_load_writes_four_documents_split_by_section(self):
        data = self.store.load(defaults())
        self.assertEqual(sorted(os.listdir(self.root)), sorted(self.api['FILES']))
        self.assertEqual(set(self.read('minimap_labels.json')), set(('labels', 'health', 'lostMarker')))
        self.assertEqual(set(self.read('minimap_circles.json')), set(('circles', 'extraCircles')))
        self.assertEqual(set(self.read('minimap_lines.json')), set(('lines',)))
        self.assertNotIn('labels', self.read('minimap.json'))
        self.assertEqual(data, defaults())

    def test_legacy_map_caption_keeps_text_style_and_offsets(self):
        self.store.load(defaults())
        data = self.read('minimap.json')
        data['mapSize'] = dict(enabled=True, color='FFCC66', fontSize=11,
                               format='{{cellsize}}0 m', x=5, y=-5)
        with open(os.path.join(self.root, 'minimap.json'), 'wb') as stream:
            stream.write(json.dumps(data).encode('utf-8'))
        size = self.store.load(defaults())['mapSize']
        self.assertEqual(size['format'], '<font size="11" color="#FFCC66">{{cellsize}}0 m</font>')
        self.assertEqual((size['offsetX'], size['offsetY']), (5, -5))
        self.assertNotIn('fontSize', size)
        self.assertEqual(size['width'], 100)

    def test_saved_values_survive_a_reload_without_rewriting_resource_paths(self):
        self.store.load(defaults())
        changed = defaults()
        changed['lastPositionDuration'] = 30
        changed['lostMarker']['style'] = 'grey'
        self.store.save(changed)
        labels = self.read('minimap_labels.json')
        labels['labels']['normal'] = u'{{name}}'
        main = self.read('minimap.json')
        main['artilleryAim']['src'] = 'gui/maps/driftkings/minimap/minimapaim.png'
        for name, document in (('minimap_labels.json', labels), ('minimap.json', main)):
            with open(os.path.join(self.root, name), 'wb') as stream:
                stream.write(json.dumps(document).encode('utf-8'))
        data = self.api['MinimapStore'](self.root).load(defaults())
        self.assertEqual(data['lastPositionDuration'], 30)
        self.assertEqual(data['lostMarker']['style'], 'grey')
        self.assertEqual(data['labels']['normal'], u'{{name}}')
        self.assertEqual(data['artilleryAim']['src'], 'gui/maps/driftkings/minimap/minimapaim.png')

    def test_invalid_values_are_never_published(self):
        self.store.load(defaults())
        before = self.read('minimap_labels.json')
        broken = defaults()
        broken['lostMarker']['style'] = 'blue'
        self.assertRaises(ValueError, self.store.save, broken)
        self.assertEqual(self.read('minimap_labels.json'), before)
