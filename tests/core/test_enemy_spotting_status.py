# -*- coding: utf-8 -*-
"""Spotting and assist messages from native player feedback events."""
import json
import os

from support import RuntimeTest, Settings, auto, game_source, module

ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
with open(os.path.join(ROOT, 'res', 'configs', 'driftkings', 'default', 'enemy_spotting_status.json'), 'rb') as stream:
    DEFAULTS = json.loads(stream.read().decode('utf-8-sig'))
EVENTS = auto('BattleFeedbackCommon.BATTLE_EVENT_TYPE')
DAMAGE = 'damage-efficiency'


class Event(object):
    def __init__(self, kind, target=7, damage=0):
        self.kind, self.target, self.damage = kind, target, damage

    def getBattleEventType(self):
        return self.kind

    def getTargetID(self):
        return self.target


class EnemySpottingStatusTests(RuntimeTest):
    def setUp(self):
        super(EnemySpottingStatusTests, self).setUp()
        self.data = dict(DEFAULTS)
        self.messages, self.sounds = [], []
        self.controlling = 1
        self.names = {7: module(playerName='Bob', vehicleName='T-34')}
        vehicle = module(vehicleType=module(iconPath='../maps/icons/vehicle/T-34.png'))
        session = module(
            shared=module(vehicleState=module(getControllingVehicleID=lambda: self.controlling)),
            getArenaDP=lambda: module(getVehicleInfo=lambda vehicleID: vehicle if vehicleID in self.names else None),
            getCtx=lambda: module(getPlayerFullNameParts=lambda vID: self.names[vID]))
        self.player = module(playerVehicleID=1, guiSessionProvider=session,
                             soundNotifications=module(play=self.sounds.append))
        efficiency = lambda event: module(getType=lambda: DAMAGE, getDamage=lambda: event.damage) if event.damage else None
        i18n = {'UI_setting_Spotted_text': 'Spotted:', 'UI_setting_AssistRadio_text': 'Radio:',
                'UI_setting_AssistTrack_text': 'Track:', 'UI_setting_AssistStun_text': 'Stun:'}
        self.api, self.hooks = game_source('battle/enemy_spotting_status.py', {
            'driftkings.game_constants': module(BATTLE_EVENT_TYPE=EVENTS,
                ASSIST_EVENTS=(EVENTS.RADIO_ASSIST, EVENTS.TRACK_ASSIST, EVENTS.STUN_ASSIST)),
            'driftkings.settings.service': Settings(self.data).service(),
            'driftkings.common.utils.wgutils': module(getPlayer=lambda: self.player),
            'driftkings.flash.battle.messages': module(sendPanelMessage=self.messages.append),
            'gui.shared.gui_items.Vehicle': module(
                getIconPath=lambda name: 'gui/maps/icons/vehicle/' + name.replace(':', '-', 1) + '.png',
                getContourIconPath=lambda name: 'gui/maps/icons/vehicle/contour/' + name.replace(':', '-', 1) + '.png'),
            'gui.battle_control.controllers.personal_efficiency_ctrl': module(
                _AGGREGATED_DAMAGE_EFFICIENCY_TYPES=(DAMAGE,), _createEfficiencyInfoFromFeedbackEvent=efficiency),
            'driftkings.settings.definitions.battle.enemy_spotting_status': module(
                EnemySpottingStatusSettings=lambda: module(i18n=i18n)),
        }, real=('driftkings._constants', 'driftkings.core.vehicle_images'))
        handlers = self.hooks.events['driftkings.core.battle_events.battleEvents.feedback']
        self.feedback = lambda *events: handlers[0](self.player, list(events))

    def test_spotting_message_uses_the_vehicle_icon_name_and_colour(self):
        self.feedback(Event(EVENTS.SPOTTED))
        icon = "<img src='img://gui/maps/icons/vehicle/T-34.png' width='47' height='16' />"
        self.assertEqual(self.messages, ["<font color='#FF69B5'>Spotted: %s[<b>T-34</b>]</font>" % icon])
        self.assertEqual(self.sounds, ['enemy_sighted_for_team'])

    def test_assists_add_damage_and_use_their_own_colour_and_sound(self):
        self.feedback(Event(EVENTS.RADIO_ASSIST, damage=150), Event(EVENTS.TRACK_ASSIST), Event(EVENTS.STUN_ASSIST, damage=40))
        self.assertTrue(self.messages[0].startswith("<font color='#28F09C'>Radio: "))
        self.assertTrue(self.messages[0].endswith('<b> +150</b></font>'))
        self.assertTrue(self.messages[1].startswith("<font color='#00FF00'>Track: "))
        self.assertNotIn('+', self.messages[1])
        self.assertTrue(self.messages[2].endswith('<b> +40</b></font>'))
        self.assertEqual(self.sounds, ['gun_intuition'] * 3)

    def test_name_macros_fall_back_to_the_icon(self):
        self.data['Spotted'] = '{names}|{full}|{icons_names}'
        self.data['sound'] = False
        self.names[7] = module(playerName='', vehicleName='T-34')
        self.feedback(Event(EVENTS.SPOTTED))
        icon = "<img src='img://gui/maps/icons/vehicle/T-34.png' width='47' height='16' />"
        self.assertEqual(self.messages, ["<font color='#FF69B5'>Spotted: %s|%s[<b>T-34</b>]|%s</font>" % (icon, icon, icon)])
        self.assertEqual(self.sounds, [])

    def test_other_events_vehicles_and_states_post_nothing(self):
        self.feedback(None, Event(EVENTS.DAMAGE), Event(EVENTS.SPOTTED, target=99))
        self.controlling = 2
        self.feedback(Event(EVENTS.SPOTTED))
        self.controlling = 1
        self.data['enabled'] = False
        self.feedback(Event(EVENTS.SPOTTED))
        self.assertEqual((self.messages, self.sounds), ([], []))

    def test_each_event_starts_with_fresh_macros(self):
        self.data['sound'] = False
        self.feedback(Event(EVENTS.SPOTTED), Event(EVENTS.SPOTTED))
        self.assertEqual(self.messages[0], self.messages[1])
