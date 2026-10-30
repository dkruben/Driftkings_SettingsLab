# -*- coding: utf-8 -*-
"""Core startup: lobby components are not imported when the client opens a replay."""
from support import RuntimeTest, module, source

NAMES = ('battle.minimap_enhancements', 'components.account_manager', 'components.sound_bank_loader',
         'lobby.hangar_preferences', 'lobby.vehicle_carousel')


class CoreStartupTests(RuntimeTest):
    def setUp(self):
        super(CoreStartupTests, self).setUp()
        self.api = source('core/__init__.py', {})
        self.imported, self.started = [], []

    def importer(self, name):
        self.imported.append(name)
        return module(init=lambda: self.started.append(name))

    def core(self, replay):
        core = self.api['Core'](names=NAMES, importer=self.importer, services=[], hook_manager=module(
            current=None, activate=lambda owner: None, deactivate=lambda owner: None, discard=lambda owner: None),
            context_factory=lambda owners: module(start=lambda: None, stop=lambda: None), replay=replay)
        core.start()
        return core

    def test_replay_skips_lobby_and_login_components(self):
        core = self.core(True)
        self.assertEqual(self.imported, ['driftkings.battle.minimap_enhancements', 'driftkings.components.sound_bank_loader'])
        self.assertEqual(self.started, self.imported)
        self.assertEqual(sorted(core.disabled), ['components.account_manager', 'lobby.hangar_preferences', 'lobby.vehicle_carousel'])
        self.assertEqual(set(core.disabled.values()), set(['Not used in replays']))

    def test_normal_session_loads_everything(self):
        core = self.core(False)
        self.assertEqual(len(self.imported), len(NAMES))
        self.assertEqual(core.disabled, {})

    def test_lobby_only_rule(self):
        lobby_only = self.api['lobby_only']
        self.assertTrue(lobby_only('lobby.crew_management') and lobby_only('components.account_manager'))
        self.assertFalse(lobby_only('components.battle_performance') or lobby_only('battle.team_panels'))
