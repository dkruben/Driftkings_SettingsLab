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
