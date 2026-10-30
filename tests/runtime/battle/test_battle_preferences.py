# -*- coding: utf-8 -*-
"""Battle preferences: a disabled module is native, and each option changes only its own target."""
import json
import os

from support import RuntimeTest, Settings, game_source, module

ROOT = os.path.join(os.path.dirname(__file__), '..', '..', '..')
with open(os.path.join(ROOT, 'res', 'configs', 'driftkings', 'default', 'battle_preferences.json'), 'rb') as stream:
    DEFAULTS = json.loads(stream.read().decode('utf-8-sig'))
# Every option set to the value that changes the client.
ACTIVE = dict(hideHint=True, disableSoundCommander=True, showPostmortemDogTag=False, showBattleHint=True,
              postmortemTips=False, stunSound=True, muteTeamBaseSound=True, maxChatLines=2, showPlayerSatisfactionWidget=False,
              addEnemyName=True, clipLoad=True, showFriends=True, directivesOnlyFromStorage=True)


class Native(object):
    def __init__(self, result='native'):
        self.calls, self.result = [], result

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.result


class BattlePreferencesTests(RuntimeTest):
    def setUp(self):
        super(BattlePreferencesTests, self).setUp()
        self.data = dict(DEFAULTS, **ACTIVE)
        self.scheduled, self.square = [], 'E5'
        arena = module(vehicles={1: {'name': 'Bob', 'vehicleType': module(type=module(shortUserString='T-34'))}})
        self.player = module(arena=arena)
        wg = module(getPlayer=lambda: self.player, isReplay=lambda: False,
                    square_position=module(getSquarePosition=lambda: self.square))
        deps = {
            'driftkings.settings.service': Settings(self.data).service(),
            'driftkings.common.utils.wgutils': wg,
            'driftkings.core.callbacks': module(callback=lambda delay, function: self.scheduled.append(function)),
        }
        self.api, self.hooks = game_source('battle/battle_preferences.py', deps,
                                          real=('driftkings._constants', 'driftkings.common.utils.formatting'))
        deps['driftkings.core.hooks'] = self.hooks
        bridge, _ = game_source('flash/battle/preferences_hooks.py', deps, real=('driftkings._constants',))
        bridge['install'](self.api['config'], self.api['_getAttackerName'])

    def wrap(self, *spec, **kwargs):
        # spec is (target, method, *args); keyword arguments go to the wrapper.
        native = kwargs.pop('native', None) or Native()
        return self.hooks.get(spec[0], spec[1])(native, *spec[2:], **kwargs), native

    def test_player_identity_is_left_to_the_team_panels(self):
        # Badges, prestige, clan and anonymous names are options of the team panels, in the shared settings.
        targets = set(target for target, name in self.hooks.overrides)
        self.assertFalse(targets & set(('VehicleArenaInfoVO', 'PlayerInfoVO')))

    def test_arena_border_preserves_rgb_channels_and_alpha(self):
        for value, expected in (('#000000', (0, 0, 0, 1)), ('#FFFFFF', (1, 1, 1, 1)),
                                ('#123456', (18 / 255.0, 52 / 255.0, 86 / 255.0, 1))):
            self.data['enabled'] = True
            self.data['color'] = value
            result, _ = self.wrap('ArenaBorderController', '_ArenaBorderController__getCurrentColor', object(), False)
            self.assertEqual(result, expected)

    def test_disabled_module_leaves_every_wrapper_native(self):
        self.data['enabled'] = False
        stun = self.api['VEHICLE_VIEW_STATE'].STUN
        cases = [('BattleHintPanel', '_initPlugins', (module(_plugins=None),), {}),
                 ('SpecialSoundCtrl', '__setSpecialVoiceByTankmen', ('ctrl',), {}),
                 ('SpecialSoundCtrl', '__setSpecialVoiceByCommanderSkinID', ('ctrl',), {}),
                 ('_ClientArenaVisitor', 'hasDogTag', ('visitor',), {}),
                 ('SharedPage', '_switchToPostmortem', ('page',), {}),
                 ('TimersPanel', '__playStunSoundIfNeed', ('panel',), {}),
                 ('_EquipmentZoneSoundPlayer', '_onVehicleStateUpdated', ('player', stun, 5), {}),
                 ('BattleTeamsBasesController', '__playCaptureSound', ('ctrl',), {}),
                 ('ShowRateSatisfactionCmp', '_convert', ('cmp', 1, None), {}),
                 ('DamageLogPanel', '_addToTopLog', ('log', 10, 'a', 'b', 'T-34', 'AP', 'bg'), {}),
                 ('DamageLogPanel', '_addToBottomLog', ('log', 10, 'a', 'b', 'T-34', 'AP', 'bg'), {})]
        for target, name, args, kwargs in cases:
            result, native = self.wrap(target, name, *args, **dict(kwargs))
            # _switchToPostmortem wraps a method without a return value.
            if name != '_switchToPostmortem':
                self.assertEqual(result, 'native', name)
            self.assertEqual(len(native.calls), 1, name)
            called_args, called_kwargs = native.calls[0]
            if name in ('_addToTopLog', '_addToBottomLog'):
                called_args = called_args[:7]
            self.assertEqual((called_args, called_kwargs), (args, kwargs), name)
        result, _ = self.wrap('SharedPage', 'as_onPostmortemActiveS', 'page', True)
        hints = {'tip': 1}
        result, _ = self.wrap('plugins', 'createPlugins', native=Native(hints))
        self.assertEqual(result, {'tip': 1})
        result, _ = self.wrap('messenger_view', '_makeSettingsVO', 'view', native=Native({'numberOfMessagesInHistory': 10}))
        self.assertEqual(result['numberOfMessagesInHistory'], 10)
        _, native = self.wrap('PlayerAvatar', 'handleKey', module(isVehicleAlive=True), True, 1, 0)
        self.assertEqual(self.scheduled, [])

    def test_hints_voices_dog_tag_and_postmortem_options(self):
        plugins = module(stopped=[], stop=lambda: plugins.stopped.append('stop'), fini=lambda: plugins.stopped.append('fini'))
        panel = module(_plugins=plugins)
        result, native = self.wrap('BattleHintPanel', '_initPlugins', panel)
        self.assertEqual((result, panel._plugins, plugins.stopped, native.calls), (None, None, ['stop', 'fini'], []))
        self.assertIs(self.wrap('SpecialSoundCtrl', '__setSpecialVoiceByTankmen', 'ctrl')[0], False)
        self.assertIs(self.wrap('_ClientArenaVisitor', 'hasDogTag', 'visitor')[0], False)
        self.assertEqual(self.wrap('plugins', 'createPlugins', native=Native({'tip': 1}))[0], {})
        _, native = self.wrap('SharedPage', 'as_onPostmortemActiveS', 'page', True)
        self.assertEqual(native.calls, [(('page', False), {})])
        self.assertEqual(self.wrap('SharedPage', '_switchToPostmortem', 'page')[1].calls, [])
        self.data['postmortemTips'] = True
        _, native = self.wrap('SharedPage', 'as_onPostmortemActiveS', 'page', True)
        self.assertEqual(native.calls, [(('page', True), {})])
        # The full statistics always request the quest data.
        _, native = self.wrap('BattleStatisticsDataController', 'as_setQuestsInfoS', 'ctrl', {'q': 1}, False)
        self.assertEqual(native.calls, [(('ctrl', {'q': 1}, True), {})])

    def test_sounds_are_muted_only_for_their_own_events(self):
        stun = self.api['VEHICLE_VIEW_STATE'].STUN
        self.assertIsNone(self.wrap('TimersPanel', '__playStunSoundIfNeed', 'panel')[0])
        self.assertEqual(self.wrap('_EquipmentZoneSoundPlayer', '_onVehicleStateUpdated', 'p', stun, 5)[1].calls, [])
        other = self.api['VEHICLE_VIEW_STATE'].HEALTH
        self.assertEqual(len(self.wrap('_EquipmentZoneSoundPlayer', '_onVehicleStateUpdated', 'p', other, 5)[1].calls), 1)
        self.assertEqual(self.wrap('BattleTeamsBasesController', '__playCaptureSound', 'ctrl')[1].calls, [])
        self.data['muteTeamBaseSound'] = False
        self.assertEqual(len(self.wrap('BattleTeamsBasesController', '__playCaptureSound', 'ctrl')[1].calls), 1)

    def test_chat_history_and_satisfaction_widget(self):
        self.assertEqual(self.wrap('messenger_view', '_makeSettingsVO', 'v', native=Native({}))[0], {'numberOfMessagesInHistory': 2})
        self.assertIs(self.wrap('ShowRateSatisfactionCmp', '_convert', 'cmp', 1, None)[0], False)

    def test_damage_log_names_the_attacker_when_the_vehicle_is_known(self):
        _, native = self.wrap('DamageLogPanel', '_addToTopLog', 'log', 10, 'a', 'b', 'T-34', 'AP', 'bg')
        self.assertEqual(native.calls[0][0][4], 'T-34 | Bob')
        _, native = self.wrap('DamageLogPanel', '_addToBottomLog', 'log', 10, 'a', 'b', 'IS-7', 'AP', 'bg')
        self.assertEqual(native.calls[0][0][4], 'IS-7 | Unknown')
        self.player = module()
        _, native = self.wrap('DamageLogPanel', '_addToTopLog', 'log', 10, 'a', 'b', 'T-34', 'AP', 'bg')
        self.assertEqual(native.calls[0][0][4], 'T-34 | Unknown')

    def avatar(self, alive=True, time_left=3.2, ammo=True):
        sent = []
        state = module(getTimeLeft=lambda: time_left) if time_left is not None else None
        shared = module(ammo=module(getGunReloadingState=lambda: state) if ammo else None,
                        chatCommands=module(proto=module(arenaChat=module(broadcast=lambda text, flags: sent.append(text))),
                                            handleChatCommand=lambda name: sent.append(('command', name))))
        return module(isVehicleAlive=alive, guiSessionProvider=module(shared=shared)), sent

    def test_reload_message_formats_position_and_rounded_seconds(self):
        avatar, sent = self.avatar()
        self.api['onReload'](avatar)
        self.assertEqual(sent, ['Reloading at E5, for 4 seconds.'])
        self.data['loadTxt'] = '{pos}: {load}s'
        avatar, sent = self.avatar(time_left=None)
        self.api['onReload'](avatar)
        self.assertEqual(sent, ['E5: 0s'])
        # A broken template is sent as written rather than raising in battle.
        self.data['loadTxt'] = 'Broken {missing'
        avatar, sent = self.avatar()
        self.api['onReload'](avatar)
        self.assertEqual(sent, ['Broken {missing'])
        self.data['loadTxt'] = ''
        avatar, sent = self.avatar()
        self.api['onReload'](avatar)
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0][0], 'command')
        for avatar, sent in (self.avatar(alive=False), self.avatar(ammo=False)):
            self.api['onReload'](avatar)
            self.assertEqual(sent, [])

    def test_partial_clip_key_schedules_the_reload_message(self):
        mapping = self.api['CommandMapping']
        mapping.g_instance = module(isFired=lambda command, key: key == 30)
        native = Native()
        self.hooks.get('PlayerAvatar', 'handleKey')(native, module(isVehicleAlive=True), True, 30, 0)
        self.assertEqual(len(self.scheduled), 1)
        self.assertEqual(len(native.calls), 1)
        self.hooks.get('PlayerAvatar', 'handleKey')(native, module(isVehicleAlive=True), False, 30, 0)
        self.hooks.get('PlayerAvatar', 'handleKey')(native, module(isVehicleAlive=True), True, 31, 0)
        self.data['clipLoad'] = False
        self.hooks.get('PlayerAvatar', 'handleKey')(native, module(isVehicleAlive=True), True, 30, 0)
        self.assertEqual(len(self.scheduled), 1)

    def test_friends_are_marked_from_the_contact_cache(self):
        self.api['_cache'].update((5,))
        vo = module(isPremiumIGR=False)
        self.hooks.get('VehicleTypeInfoVO', '__init__')(Native(), vo, accountDBID=5)
        self.assertTrue(vo.isPremiumIGR)
        stranger = module(isPremiumIGR=False)
        self.hooks.get('VehicleTypeInfoVO', 'update')(Native(), stranger, accountDBID=6)
        self.assertFalse(stranger.isPremiumIGR)

    def booster_vehicle(self, count, auto=False, locked=False, **flags):
        booster = module(inventoryCount=count, userName='Directive')
        return module(isLocked=locked, userName='Tank', isAutoBattleBoosterEquip=lambda: auto,
                      battleBoosters=module(installed=module(getItems=lambda: [booster])), **flags)

    def test_directives_follow_the_storage_only_for_regular_vehicles(self):
        changes = []
        self.api['changeValue'] = lambda vehicle, value: changes.append((vehicle.userName, value))
        self.api['onVehicleChanged'](self.booster_vehicle(2))
        self.api['onVehicleChanged'](self.booster_vehicle(0, auto=True))
        self.api['onVehicleChanged'](self.booster_vehicle(2, auto=True))
        self.assertEqual(changes, [('Tank', True), ('Tank', False)])
        for vehicle in (self.booster_vehicle(2, locked=True), self.booster_vehicle(2, isOnlyForEpicBattles=True), None):
            self.api['onVehicleChanged'](vehicle)
        self.data['enabled'] = False
        self.api['onVehicleChanged'](self.booster_vehicle(2))
        self.assertEqual(len(changes), 2)

    def test_border_uses_the_configured_colour(self):
        red, green, blue, alpha = self.hooks.get('ArenaBorderController', '_ArenaBorderController__getCurrentColor')(Native(), 'ctrl', False)
        self.assertEqual((round(red * 255), round(green * 255), round(blue * 255), alpha), (249, 48, 248, 1.0))
