# -*- coding: utf-8 -*-
"""Run the actual roster pipeline with engine boundaries stubbed."""
import ast
import copy
import os

from support import CLIENT, ROOT, RuntimeTest, module, source


def literal_assignment(relative, name):
    with open(os.path.join(CLIENT, *relative.split('/')), 'rb') as stream:
        tree = ast.parse(stream.read())
    return next(ast.literal_eval(node.value) for node in tree.body
                if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == name
                                                       for target in node.targets))


class PanelLocalizationTests(RuntimeTest):
    def locale(self, code):
        with open(os.path.join(ROOT, 'mod/res/mods/driftkings/text', code + '.yml'), 'rb') as stream:
            return self.load('core.locale_catalog').parse_catalog(stream.read())

    def setUp(self):
        super(PanelLocalizationTests, self).setUp()
        with open(os.path.join(CLIENT, '_constants.py'), 'rb') as stream:
            tree = ast.parse(stream.read())
        panel = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'TEAM_PANELS')
        keys = dict((node.targets[0].id, ast.literal_eval(node.value)) for node in panel.body
                    if isinstance(node, ast.Assign))
        constants = module(TEAM_PANELS=module(**keys), GLOBAL=module(ENABLED='enabled'),
                           BATTLE_ALIASES=module(PLAYERS_PANEL='testRoster'))
        profiles = ('none', 'short', 'medium', 'medium2', 'large')
        settings_data = module(PROFILES=profiles, defaults=lambda name: {}, profile_for_mode=lambda name: name)
        store = source('settings/team_panel_store.py', {
            'driftkings.core.keycodes': module(valid_key_code=lambda key: True),
            'driftkings.settings.panel_validation': module(macro_issues=lambda text: []),
            'driftkings.settings.settings_data': settings_data,
            'driftkings.settings.store': module(merge=None, JsonDocuments=object, read_object=None),
        })
        self.roster = source('core/panel_model.py', {
            'driftkings._constants': constants,
            'driftkings.settings.team_panel_store': module(resolve_fields=store['resolve_fields']),
        })['Roster']
        self.data = copy.deepcopy(literal_assignment('settings/default_values.py', 'DEFAULTS')['team_panels'])
        screen = {'enabled': True, 'showUnavailable': True,
                  'format': '{{region}} / {{i18n:Destroyed}}',
                  'extraFieldsLeft': [{'format': '{{l10n:Destroyed}}'}],
                  'extraFieldsRight': []}
        self.data['profiles'] = {'large': screen}
        self.data['loading'] = copy.deepcopy(screen)
        self.data['tab'] = copy.deepcopy(screen)
        self.config = module(i18n={'UI_panel_destroyed': 'Destroyed'})
        self.player = module(playerVehicleID=1, team=1,
                             arena=module(guiType=1, statistics={}, vehicles={1: {
                                 'name': 'Example', 'team': 1, 'accountDBID': 1500000000,
                                 'isAlive': False}}))
        self.api = source('views/battle/player_ratings.py', {
            'driftkings._constants': constants,
            'driftkings.settings.service': module(settings_service=module(getComponentDict=lambda config: self.data),
                                                 SettingsChanges=lambda *args: (), changed_paths=lambda *args: (),
                                                 affects=lambda *args: True),
            'BigWorld': module(player=lambda: self.player),
            'realm': module(CURRENT_REALM='EU'),
            'driftkings.meta.battle.players_panel': module(PlayersPanelMeta=object),
            'gui.Scaleform.daapi.view.battle.classic.players_panel': module(PlayersPanel=object),
            'gui.Scaleform.daapi.view.meta.BattleStatisticDataControllerMeta': module(BattleStatisticDataControllerMeta=object),
            'gui.shared': module(g_eventBus=None, events=None, EVENT_BUS_SCOPE=None),
            'driftkings.core.hooks': module(override=None),
            'driftkings.core.battle_events': module(battleEvents=None),
            'driftkings.core.panel_model': module(Roster=self.roster),
            'driftkings.settings.settings_data': settings_data,
            'driftkings.common.utils.colorratting': module(getStatisticColor=lambda *args: '#FFFFFF'),
        })
        self.view = self.api['RatingViews'](self.config, module(getPlayersInfo=lambda ident: {}))

    def test_region_uses_client_realm_for_all_three_screens_and_cached_rows(self):
        # This account ID belongs to NA; it must not override the client's realm.
        for region in ('EU', 'NA', 'ASIA', 'CT'):
            self.api['CURRENT_REALM'] = region
            row = self.view.rows()[0]
            for screen in (row['panels']['large'], row['loading'], row['tab']):
                self.assertEqual(screen['format'], region + ' / Destroyed')
            self.assertIs(self.view.rows()[0], row)

    def test_language_changes_invalidate_cached_screens_and_extra_fields(self):
        self.view.rows()
        for language in ('pt', 'de', 'fr', 'ru', 'ja', 'en'):
            text = self.locale(language)['TEXT']['team_panels']['UI_panel_destroyed']
            self.config.i18n['UI_panel_destroyed'] = text
            row = self.view.rows()[0]
            for screen in (row['panels']['large'], row['loading'], row['tab']):
                self.assertEqual(screen['format'], 'EU / ' + text)
                self.assertEqual(screen['fields'][0]['format'], text)

    def test_every_catalog_has_a_translation_and_unknown_macro_falls_back_to_its_name(self):
        for filename in os.listdir(os.path.join(ROOT, 'mod/res/mods/driftkings/text')):
            if not filename.endswith('.yml'):
                continue
            text = self.locale(filename[:-4])['TEXT']['team_panels']['UI_panel_destroyed']
            self.assertTrue(text.strip(), filename)
        result = self.roster().screen({'format': '{{l10n:Unknown}}'}, {'xvm-stat': ''},
                                      {'templates': {}}, 'Left')
        self.assertEqual(result['format'], 'Unknown')

    def test_default_hp_image_selects_existing_assets_for_all_team_and_colorblind_states(self):
        import json
        with open(os.path.join(ROOT, 'res/configs/driftkings/default/team_panels/playerspanel.json'), 'rb') as stream:
            document = json.loads(stream.read().decode('utf-8'))
        field = document['templates']['hpBar']
        self.assertEqual(field['height'], 24)
        macros = self.load('core.panel_macros').Macros
        for ally, blind, filename in ((True, False, 'hp_alive_l.png'), (True, True, 'hp_alive_l.png'),
                                      (False, False, 'hp_alive_r.png'), (False, True, 'hp_alive_r_cb.png')):
            path = macros({'ally': ally, 'colorblind': blind}).render(field['src'], html=False)
            self.assertTrue(path.endswith('/' + filename), path)
            self.assertTrue(os.path.isfile(os.path.join(ROOT, 'mod/res', path[len('img://'):])))

    def test_colorblind_image_macro_updates_all_cached_screens_when_mode_changes(self):
        for key in ('loading', 'tab'):
            self.data[key]['format'] = '{{colorblind?purple|red}}'
        self.data['profiles']['large']['format'] = '{{colorblind?purple|red}}'
        self.data['profiles']['large']['extraFieldsLeft'] = [{'src': 'hp_{{colorblind?cb|normal}}.png'}]
        blind = [False]
        self.view.view = module(isColorBlind=lambda: blind[0])
        first = self.view.rows()[0]
        self.assertEqual(first['panels']['large']['fields'][0]['src'], 'hp_normal.png')
        for mode in (True, False):
            blind[0] = mode
            row = self.view.rows()[0]
            for screen in (row['panels']['large'], row['loading'], row['tab']):
                self.assertEqual(screen['format'], 'purple' if mode else 'red')
            self.assertEqual(row['panels']['large']['fields'][0]['src'], 'hp_cb.png' if mode else 'hp_normal.png')

    def test_settings_are_reread_only_after_a_change_signal(self):
        first = self.view.rows()[0]['panels']['large']['format']
        self.data['profiles']['large']['format'] = 'Changed'
        # No deep comparison per tick: the cached screen stays until the settings signal.
        self.assertEqual(self.view.rows()[0]['panels']['large']['format'], first)
        self.view.stats._appliedCache = {}
        self.view.onSettingsChanged('team_panels', ())
        self.assertEqual(self.view.rows()[0]['panels']['large']['format'], 'Changed')
