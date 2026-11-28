# -*- coding: utf-8 -*-
"""Phase 11.6 approved distributed defaults, and preservation of existing explicit choices.

Every file is written to a temporary directory; no game configuration or account file is touched.
"""
import copy
import os
import shutil
import tempfile

from support import ROOT, RuntimeTest, module


# Approved first-installation values (component, dotted path, value). Unlisted values keep their defaults.
APPROVED = (
    ('main', 'clock.formats.0.textFormat.color', '#D8D5CD'),
    ('battle_performance', 'format', "WN8: <font color='{c:wn8}'>{wn8}</font>"),
    ('battle_performance', 'textLock', True),
    ('battle_performance', 'textStyle.size', 14),
    ('account_manager', 'enabled', False),
    ('game_log_manager', 'logSwapper', False),
    ('game_log_manager', 'enabled', True),
    ('repair_controls', 'enabled', False),
    ('sniper_camera', 'zoomSteps.steps', [2.0, 4.0, 8.0, 16.0, 25.0]),
    ('third_person_zoom', 'enabled', False),
    ('target_distance', 'lockPositionOffsets', True),
    ('target_information', 'enabled', False),
    ('battle_marks_of_excellence', 'gameface.locked', True),
    ('battle_marks_of_excellence', 'gameface.showTargetDamage', True),
    ('battle_marks_of_excellence', 'showTargets', True),
    ('vehicle_health', 'style', 7),
    ('high_caliber_progress', 'enabled', False),
    ('battle_statistics', 'enabled', False),
    ('enemy_spotting_status', 'sound', False),
    ('sixth_sense_alert', 'userSound', False),
    ('sixth_sense_alert', 'iconSize', 80),
    ('battle_preferences', 'inBattle', False),
    ('battle_preferences', 'removeFog', False),
    ('clan_reward_collection', 'enabled', False),
    ('clan_reward_collection', 'purchaseProgression', False),
    ('hangar_preferences', 'autoLogin', False),
    ('hangar_preferences', 'showXpToUnlockVeh', True),
    ('hangar_preferences', 'showPromoPremVehicle', False),
    ('crew_management', 'crewAutoReturn', False),
    ('crew_management', 'crewReturnByDefault', False),
    ('profile_ratings', 'showUnavailableWN8', False),
    ('tech_tree_marks_of_excellence', 'showInTechTreeMarkOfGunTankNameColored', False),
    ('hangar_marks_of_excellence', 'gameface.showAdvancedStatistics', False),
)

# Components whose loader file is one JSON object; used for the fresh-profile and existing-profile checks.
FILE_SECTIONS = ('main', 'battle_performance', 'game_log_manager', 'account_manager', 'repair_controls',
                 'sniper_camera', 'third_person_zoom', 'target_distance', 'target_information',
                 'battle_marks_of_excellence', 'vehicle_health', 'high_caliber_progress', 'battle_statistics',
                 'enemy_spotting_status', 'sixth_sense_alert', 'battle_preferences', 'clan_reward_collection',
                 'hangar_preferences', 'crew_management', 'profile_ratings', 'tech_tree_marks_of_excellence',
                 'hangar_marks_of_excellence')


def read_path(document, path):
    value = document
    for part in path.split('.'):
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


class ApprovedDefaultsTests(RuntimeTest):
    def setUp(self):
        super(ApprovedDefaultsTests, self).setUp()
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        self.defaults = self.load('settings.default_values').DEFAULTS
        self.store = self.load('settings.store').SettingsStore
        self.merge = self.load('settings.store').merge
        self.loader_class = self.load('settings.loader').SettingsLoader

    def loader(self):
        return self.loader_class(self.root, settings=module(configs=self.defaults))

    def write(self, relative, value):
        path = os.path.join(self.root, relative)
        self.store(path).write(value)
        return path

    # 1. Fresh configuration receives the approved defaults.
    def test_fresh_profile_receives_approved_values(self):
        loader = self.loader()
        for component in FILE_SECTIONS:
            loaded = loader.load(component, self.defaults[component])
            self.assertEqual(loaded, self.defaults[component], component)
        for component, path, expected in APPROVED:
            self.assertEqual(read_path(self.defaults[component], path), expected, component + ' ' + path)
        self.assertEqual(len(self.defaults['main']['clock']['formats']), 1)

    # 2 and 3. An existing complete configuration keeps its explicit values, including formats and colours.
    def test_existing_explicit_values_are_preserved(self):
        custom = copy.deepcopy(self.defaults['battle_performance'])
        custom.update(format='custom {wn8}', enabled=False)
        custom['position'] = {'x': 5, 'y': 6}
        custom['textStyle'] = dict(custom['textStyle'], size=20, color='#123456')
        self.write('default/battle_performance.json', custom)
        loaded = self.loader().load('battle_performance', self.defaults['battle_performance'])
        self.assertEqual(loaded['format'], 'custom {wn8}')
        self.assertFalse(loaded['enabled'])
        self.assertEqual(loaded['position'], {'x': 5, 'y': 6})
        self.assertEqual(loaded['textStyle']['size'], 20)
        self.assertEqual(loaded['textStyle']['color'], '#123456')

    # 4 and 5. A partial configuration receives defaults only for missing values.
    def test_partial_configuration_receives_only_missing_defaults(self):
        self.write('default/battle_preferences.json', {'inBattle': True, 'maxChatLines': 9})
        loaded = self.loader().load('battle_preferences', self.defaults['battle_preferences'])
        self.assertTrue(loaded['inBattle'])
        self.assertEqual(loaded['maxChatLines'], 9)
        self.assertEqual(loaded['showFriends'], self.defaults['battle_preferences']['showFriends'])
        self.assertEqual(loaded['removeFog'], False)

    def test_explicit_opt_in_survives_new_opt_in_defaults(self):
        self.write('default/account_manager.json', {'enabled': True})
        self.write('default/clan_reward_collection.json', {'enabled': True, 'claimRewards': True,
                                                   'purchaseProgression': True})
        self.assertTrue(self.loader().load('account_manager', self.defaults['account_manager'])['enabled'])
        clan = self.loader().load('clan_reward_collection', self.defaults['clan_reward_collection'])
        self.assertTrue(clan['purchaseProgression'])

    # 6. Lists are replaced as a whole: an existing carousel extraFields array is never mixed with defaults.
    def test_user_lists_replace_default_lists(self):
        normal = self.defaults['vehicle_carousel']['carousel']['normal']
        user_fields = [{'format': 'custom', 'x': 1, 'y': 2}]
        merged = self.merge(normal, {'extraFields': user_fields})
        self.assertEqual(merged['extraFields'], user_fields)
        self.assertEqual(len(normal['extraFields']), 14)
        self.assertEqual(self.merge(normal, {})['extraFields'], normal['extraFields'])

    def test_carousel_disabled_entries_are_explicit(self):
        items = self.defaults['vehicle_carousel']['carousel']['normal']['extraFields']
        disabled = [index for index, item in enumerate(items) if item.get('enabled') is False]
        self.assertEqual(disabled, [0, 1, 4, 5, 8])
        self.assertEqual(len(items), 14)
        self.assertIn('{{v.tdb%d}}', items[7]['format'])
        self.assertNotIn('wn8expd', items[7]['format'])

    # 7. Customised marker definitions and references remain intact.
    def test_marker_rating_definition_is_kept_for_customisation(self):
        normal = self.defaults['vehicle_markers']['markersAliveNormal']
        self.assertFalse(normal['def']['rating']['enabled'])
        self.assertIn('${def.rating}', normal['ally']['textFields'])
        self.assertIn('${def.rating}', normal['enemy']['textFields'])
        extended = self.defaults['vehicle_markers']['markersAliveExtended']
        self.assertTrue(extended['def']['rating']['enabled'])

    # 8. Reset to defaults uses the approved values.
    def test_reset_source_returns_approved_values(self):
        settings_data = self.load('settings.settings_data')
        reset = settings_data.defaults('battle_preferences')
        self.assertFalse(reset['inBattle'])
        reset['inBattle'] = True
        self.assertFalse(settings_data.defaults('battle_preferences')['inBattle'])
        self.assertFalse(self.defaults['battle_preferences']['inBattle'])

    # 9. Account and sensitive data are never written outside the temporary directory.
    def test_loading_defaults_writes_only_to_the_temporary_root(self):
        loader = self.loader()
        for component in FILE_SECTIONS:
            loader.load(component, self.defaults[component])
        for directory, _, files in os.walk(self.root):
            for name in files:
                self.assertTrue(os.path.abspath(os.path.join(directory, name)).startswith(os.path.abspath(self.root)))

    # 10. Existing fog and purchase-consent protections keep their values.
    def test_protected_consent_defaults_remain_off(self):
        self.assertFalse(self.defaults['battle_preferences']['removeFog'])
        self.assertFalse(self.defaults['clan_reward_collection']['purchaseProgression'])

    def test_profiles_remain_available(self):
        profiles = self.defaults['team_panels']['profiles']
        self.assertEqual(sorted(profiles), ['large', 'medium', 'medium2', 'none', 'short'])

    # Phase 11.6 cleanup: keys with no consumer and the superseded top-level minimap copy are gone.
    def test_obsolete_configuration_is_removed(self):
        self.assertNotIn('compareValuesColor', self.defaults['battle_statistics'])
        tech_tree = self.defaults['tech_tree_marks_of_excellence']
        for key in ('techTreeHeight', 'techTreeWidth', 'techTreeX', 'techTreeY'):
            self.assertNotIn(key, tech_tree)
        self.assertFalse(os.path.exists(os.path.join(ROOT, 'res', 'configs', 'driftkings', 'default',
                                                     'minimap_enhancements.json')))
        self.assertIn('enabled', self.defaults['minimap_enhancements'])
