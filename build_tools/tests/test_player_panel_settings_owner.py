import ast
import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT / 'source/scripts/client'
sys.path.insert(0, str(CLIENT))
from Driftkings._constants import GLOBAL, PLAYER_PANEL_PRO
from Driftkings.settings.loader import SettingsLoader
from Driftkings.settings.player_panel_store import PlayerPanelStore, FILES
from Driftkings.settings.service import SettingsService, affects
from Driftkings.settings.settings_data import SettingsData
from Driftkings.settings.store import merge


def load_class(path, name, ns):
    tree = ast.parse((CLIENT / 'Driftkings' / path).read_text(encoding='utf-8-sig'))
    tree.body = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == name]
    exec(compile(tree, path, 'exec'), ns)
    return ns[name]


class Signal:
    def __init__(self): self.callbacks = []
    def connect(self, fn): self.callbacks.append(fn)
    def disconnect(self, fn): self.callbacks.remove(fn)


class PlayerPanelSettingsOwnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.loader = SettingsLoader(self.tmp.name)
        self.service = SettingsService(SettingsData())
        # PlayerPanelPro uses native key codes in JSON; no legacy hotkey fields.
        def hotkeys(data, keys, mode): self.assertEqual(keys, {})
        ns = dict(ComponentSettings=object, PLAYER_PANEL_PRO=PLAYER_PANEL_PRO, copy=copy, json=json,
                  settings_loader=self.loader, PlayerPanelStore=PlayerPanelStore, FILES=FILES,
                  merge=merge, processHotKeys=hotkeys)
        cls = load_class('settings/templates/battle/players_panel.py', 'PlayerPanelProSettings', ns)
        self.owner = cls()
        self.owner.ID = PLAYER_PANEL_PRO.ID
        self.owner.configPath = str(Path(self.tmp.name) / 'legacy')
        self.owner.defaultKeys = {}
        self.owner.data = self.owner.loadDataJson()
        self.notifications = []
        self.service.onModSettingsChanged.connect(lambda component, changes:self.notifications.append(changes), PLAYER_PANEL_PRO)

    def test_split_json_decoding_hp_toggle_and_notification_after_successful_save(self):
        original = self.owner.data
        changes = self.service.apply(self.owner, {'hpVisibility':'never', 'hpKey':[[35]],
            'profiles':{'medium2':{'standardFields':'["frags", "vehicle"]'}},
            'tab':{'extraFieldsLeft':'[{"format":"{{hp}}"}]'}})
        self.assertIs(self.owner.data, original)
        self.assertFalse(self.owner.data['hpEnabled'])
        self.assertEqual(self.owner.data['tab']['extraFieldsLeft'], [{'format':'{{hp}}'}])
        self.assertEqual(self.owner.loadDataJson(), self.owner.data)
        self.assertEqual(len(self.notifications), 1)
        self.assertEqual(changes['hpKey'], [[35]])
        self.service.apply(self.owner, {'hpVisibility':'hold'})
        self.assertTrue(self.owner.data['hpEnabled'])
        self.assertEqual(self.owner.loadDataJson()['hpVisibility'], 'hold')

    def test_invalid_edits_and_failed_publication_leave_memory_files_and_listeners_unchanged(self):
        before = copy.deepcopy(self.owner.data)
        path = Path(self.owner.profileStore().directory)
        files = {name:(path / name).read_bytes() for name in FILES}
        for values in ({'tab':{'extraFieldsLeft':'invalid json'}}, {'hpVisibility':'invalid'},
                       {'profiles':{'medium2':{'extraFieldsRight':[{'ref':'missing-template'}]}}}):
            with self.assertRaises(ValueError): self.service.apply(self.owner, values)
            self.assertEqual(self.owner.data, before)
            self.assertEqual({name:(path/name).read_bytes() for name in FILES}, files)
        with patch.object(PlayerPanelStore, 'publish', side_effect=IOError('simulated failure')):
            with self.assertRaises(IOError): self.service.apply(self.owner, {'rating':'eff'})
        self.assertEqual(self.owner.data, before)
        self.assertEqual(self.notifications, [])
        self.assertEqual(self.owner.loadDataJson(), before)

    def roster(self):
        battle = NS(**{name:Signal() for name in ('started','loaded','ended','health','appeared','visibility','killed','key')})
        battle.acquire = Mock(); battle.release = Mock()
        ns = dict(settings_service=self.service, PLAYER_PANEL_PRO=PLAYER_PANEL_PRO, GLOBAL=GLOBAL,
                  affects=affects, battleEvents=battle, g_eventBus=Mock(),
                  events=NS(ComponentEvent=NS(COMPONENT_REGISTERED='registered')),
                  EVENT_BUS_SCOPE=NS(GLOBAL='global'), override=Mock(),
                  PlayersPanel=object, BattleStatisticDataControllerMeta=object)
        cls = load_class('views/battle/player_ratings.py', 'RatingViews', ns)
        roster = cls.__new__(cls)
        roster.config = self.owner; roster.active = False
        roster.stats = NS(_appliedCache={'player':42})
        roster.lastRequest = 99; roster.refresh = Mock(); roster.end = Mock()
        gameface = NS(GamefaceLoading=Mock())
        with patch.dict(sys.modules, {'Driftkings.views.battle.panel_gameface':gameface}):
            roster.start(); roster.start()
        self.addCleanup(roster.stop)
        self.assertEqual(battle.acquire.call_count, 1)
        roster.refresh.reset_mock()
        return roster, battle, gameface

    def test_visual_notifications_refresh_once_preserve_stats_cache_for_layout_and_stop_cleanly(self):
        roster, battle, gameface = self.roster()
        self.service.apply(self.owner, {'tab':{'nameFieldOffsetXLeft':12}})
        roster.refresh.assert_called_once()
        self.assertEqual(roster.lastRequest, 99)
        self.assertEqual(roster.stats._appliedCache, {'player':42})
        self.service.apply(self.owner, {'tab':{'nameFieldOffsetXLeft':12}})
        roster.refresh.assert_called_once()
        self.service.onModSettingsChanged.emit('own_health', {'enabled':False})
        roster.refresh.assert_called_once()
        self.service.apply(self.owner, {'colorScale':self.owner.data['colorScale']+1})
        self.assertEqual(roster.stats._appliedCache, {})
        self.assertEqual(roster.lastRequest, 0)
        self.assertEqual(roster.refresh.call_count, 2)
        roster.stop(); roster.stop()
        battle.release.assert_called_once_with(roster)
        self.assertEqual(battle.health.callbacks, [])
        self.service.apply(self.owner, {'tab':{'nameFieldOffsetXLeft':24}})
        self.assertEqual(roster.refresh.call_count, 2)
        with patch.dict(sys.modules, {'Driftkings.views.battle.panel_gameface':gameface}): roster.start()
        roster.refresh.reset_mock()
        self.service.apply(self.owner, {'statsEnabled':False})
        roster.refresh.assert_called_once()


if __name__ == '__main__': unittest.main()
