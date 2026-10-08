import ast
from copy import deepcopy
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/scripts/client'))
from settings_support import settings_globals
from Driftkings.settings.settings_data import defaults


def load(name, namespace):
    path = ROOT / ('source/scripts/client/Driftkings/battle/' + name + '.py')
    tree = ast.parse(path.read_text(encoding='utf-8'))
    tree.body = [n for n in tree.body if isinstance(n, ast.ClassDef) or
                 isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and
                 n.targets[0].id in ('SOUND_LIST', 'GENERATOR', 'SUPPORTED_EVENTS')]
    settings_globals(namespace, 'battle.' + name)
    exec(compile(tree, str(path), 'exec'), namespace)
    return namespace


class BattleSettingsControllersTests(unittest.TestCase):
    def safe(self):
        cfg = NS(ID='SafeShot', data=defaults('SafeShot'), i18n={
            'UI_triggerText_enabled': 'on', 'UI_triggerText_disabled': 'off'})
        player = NS(team=1, guiSessionProvider=NS(getArenaDP=lambda:NS(isTeamKiller=lambda _:False)))
        ns = load('safe_shot', dict(override=Mock(), FragsCollectableStats=object, PlayerAvatar=object,
            keyboard=Mock(), getPlayer=lambda:player, getTarget=lambda:None, checkKeys=lambda _:True,
            serverTime=lambda:10, sendPanelMessage=Mock(), sendChatMessage=Mock(), support=Mock()))
        return cfg, ns, ns['SafeShotController'](cfg)

    def test_safe_shot_lifecycle_keeps_runtime_state_out_of_config(self):
        cfg, ns, controller = self.safe()
        before = deepcopy(cfg.data)
        controller.start_battle(); controller.start_battle()
        ns['keyboard'].subscribe.assert_called_once_with(controller.keyPressed)
        controller.keyPressed(NS(isKeyDown=lambda:True))
        self.assertFalse(controller.isKeyPressed)
        controller.deadDict[22] = 10
        native = Mock()
        controller.new__destroyGUI(native, object())
        native.assert_called_once()
        ns['keyboard'].unsubscribe.assert_called_once_with(controller.keyPressed)
        self.assertEqual(controller.deadDict, {})
        self.assertTrue(controller.isKeyPressed)
        self.assertFalse(controller._battleStarted)
        self.assertEqual(cfg.data, before)
        self.assertFalse(hasattr(cfg, 'deadDict'))
        controller.endBattle()
        ns['keyboard'].unsubscribe.assert_called_once()

    def test_safe_shot_uses_live_settings_and_preserves_native_shoot_arguments(self):
        cfg, ns, controller = self.safe()
        service = ns['settings_service']
        service.apply(cfg, {'enabled':True, 'wasteShotBlock':True}, persist=False)
        self.assertFalse(controller.isShotAllowed())
        shoot = Mock(); avatar=object()
        controller.new__shoot(shoot, avatar, True)
        shoot.assert_not_called()
        service.apply(cfg, {'enabled':False}, persist=False)
        controller.new__shoot(shoot, avatar, True)
        shoot.assert_called_once_with(avatar, True)
        dual = Mock()
        controller.new__shootDualGun(dual, avatar, 3, True, False)
        dual.assert_called_once_with(avatar, 3, True, False)
        service.apply(cfg, {'enabled':True}, persist=False)
        controller.isEventBattle = True
        self.assertTrue(controller.isShotAllowed())

    def test_spotted_messages_reset_per_event_and_read_current_config(self):
        cfg = NS(ID='SpottedExtendedLight', data=defaults('SpottedExtendedLight'),
                 i18n={'UI_setting_Spotted_text':'Detected'})
        cfg.data.update(enabled=True, sound=True, Spotted='{names}')
        types = NS(SPOTTED=1, RADIO_ASSIST=2, TRACK_ASSIST=3, STUN_ASSIST=4)
        vehicle = NS(vehicleType=NS(iconPath='../tank.png'))
        session = NS(shared=NS(vehicleState=NS(getControllingVehicleID=lambda:9)),
            getArenaDP=lambda:NS(getVehicleInfo=lambda _:vehicle),
            getCtx=lambda:NS(getPlayerFullNameParts=lambda vID:NS(playerName='Player'+str(vID),vehicleName='Tank')))
        player = NS(playerVehicleID=9, guiSessionProvider=session, soundNotifications=Mock())
        ns = load('spotted_light', dict(BATTLE_EVENT_TYPE=types, getPlayer=lambda:player,
            _createEfficiencyInfoFromFeedbackEvent=lambda event:None,
            feedback_events=NS(PlayerFeedbackEvent=NS(fromDict=lambda value:value)),
            sendPanelMessage=Mock()))
        controller = ns['SpottedLightController'](cfg)
        before = deepcopy(cfg.data)
        event = lambda ident:NS(getBattleEventType=lambda:1,getTargetID=lambda:ident)
        controller.postMessage([event(1), event(2)])
        messages=[call.args[0] for call in ns['sendPanelMessage'].call_args_list]
        self.assertIn('Player1', messages[0]); self.assertNotIn('Player1', messages[1])
        self.assertIn('Player2', messages[1])
        self.assertEqual(player.soundNotifications.play.call_count, 2)
        self.assertEqual(cfg.data, before)
        self.assertFalse(hasattr(cfg, 'format_str'))
        ns['settings_service'].apply(cfg, {'Spotted':'{vehicles}', 'sound':False}, persist=False)
        controller.postMessage([event(3)])
        self.assertIn('Tank', ns['sendPanelMessage'].call_args.args[0])
        self.assertNotIn('Player3', ns['sendPanelMessage'].call_args.args[0])
        self.assertEqual(player.soundNotifications.play.call_count, 2)
        ns['settings_service'].apply(cfg, {'enabled':False}, persist=False)
        controller.postMessage([event(4)])
        self.assertEqual(ns['sendPanelMessage'].call_count, 3)
