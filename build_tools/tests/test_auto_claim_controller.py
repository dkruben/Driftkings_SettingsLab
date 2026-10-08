import ast
from copy import deepcopy
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/scripts/client'))
from Driftkings._constants import AUTO_CLAIM_CLAN, GLOBAL, MINIMAP_PLUGINS
from Driftkings.settings.service import SettingsService
from Driftkings.settings.settings_data import SettingsData, defaults


class Event:
    def __init__(self): self.handlers = []
    def __iadd__(self, handler): self.handlers.append(handler); return self
    def __isub__(self, handler): self.handlers.remove(handler); return self
    def emit(self, *args):
        for handler in tuple(self.handlers): handler(*args)


class AutoClaimControllerTests(unittest.TestCase):
    def setUp(self):
        self.config = NS(ID=AUTO_CLAIM_CLAN.ID, data=defaults(AUTO_CLAIM_CLAN.ID))
        self.config.data['enabled'] = True
        self.service = SettingsService(SettingsData())
        self.space, self.proxy, self.received = Event(), Event(), Event()
        self.web = NS(sendRequest=Mock(return_value='pending'))
        self.items = NS(items=NS(stats=NS(dynamicCurrencies={'tour':100})))
        self.quests = NS(quests=[NS(status='available')])
        self.progress = NS(points={})
        self.options = NS(enabled=True, points={})
        self.provider = NS(onDataReceived=self.received,
            getQuestsInfo=lambda:NS(data=self.quests),
            getProgressionProgress=lambda:NS(data=self.progress),
            getProgressionSettings=lambda:NS(data=self.options))
        self.clan = NS(isInClan=True, clanSupplyProvider=self.provider)
        dependencies = {'web':self.web, 'items':self.items, 'space':NS(onSpaceCreate=self.space)}
        ns = dict(settings_service=self.service, GLOBAL=GLOBAL, AUTO_CLAIM_CLAN=AUTO_CLAIM_CLAN,
            dependency=NS(descriptor=lambda key:dependencies[key]), IWebController='web', IItemsCache='items',
            IHangarSpace='space', adisp_process=lambda fn:fn, g_clanCache=self.clan,
            g_wgncEvents=NS(onProxyDataItemShowByDefault=self.proxy),
            DataNames=NS(QUESTS_INFO='quests', QUESTS_INFO_POST='post', PROGRESSION_PROGRESS='progress', PROGRESSION_SETTINGS='options'),
            PointStatus=NS(AVAILABLE='available', PURCHASED='purchased'), QuestStatus=NS(COMPLETE='complete'),
            REWARD_STATUS_OK=('available','pending'), SKIP_LEVELS=(5,10,15,20), Currency=NS(TOUR_COIN='tour'),
            WGNC_DATA_PROXY_TYPE=NS(CLAN_SUPPLY_QUEST_UPDATE='quest'), ClaimRewardsCtx=lambda:'claim')
        path = ROOT / 'source/scripts/client/Driftkings/lobby/auto_claim_clan.py'
        tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        tree.body = [node for node in tree.body if isinstance(node, ast.ClassDef)]
        exec(compile(tree, str(path), 'exec'), ns)
        self.controller = ns['AutoClaimClanReward'](self.config)

    def test_lobby_subscriptions_and_live_toggle_do_not_change_preferences(self):
        c = self.controller
        before = deepcopy(self.config.data)
        claim = Mock()
        c._AutoClaimClanReward__claimRewards = claim
        c.subscribe(); c.subscribe()
        self.assertEqual([len(event.handlers) for event in (self.space,self.proxy,self.received)], [1,1,1])
        self.space.emit()
        claim.assert_called_once()
        self.assertEqual(self.config.data, before)
        self.service.apply(self.config, {'enabled':False}, persist=False)
        self.received.emit('quests', self.quests)
        claim.assert_called_once()
        self.service.apply(self.config, {'enabled':True}, persist=False)
        self.received.emit('quests', self.quests)
        self.assertEqual(claim.call_count, 2)
        c.unsubscribe(); c.unsubscribe()
        self.assertEqual([len(event.handlers) for event in (self.space,self.proxy,self.received)], [0,0,0])
        self.assertEqual(self.service.onModSettingsChanged._listeners, [])
        self.space.emit()
        self.assertEqual(claim.call_count, 2)
        c.subscribe()
        self.space.emit()
        self.assertEqual(claim.call_count, 3)

    def test_other_modules_and_non_clan_accounts_do_not_trigger_collection(self):
        c = self.controller
        c.subscribe()
        c._AutoClaimClanReward__claimRewards = Mock()
        self.clan.isInClan = False
        self.space.emit()
        self.received.emit('quests', self.quests)
        c._AutoClaimClanReward__claimRewards.assert_not_called()
        self.clan.isInClan = True
        self.config.data['enabled'] = False
        self.service.onModSettingsChanged.emit(MINIMAP_PLUGINS.NAME, {'enabled':False})
        self.assertTrue(c._AutoClaimClanReward__enabled)
        self.service.onModSettingsChanged.emit(AUTO_CLAIM_CLAN.NAME, {'enabled':False})
        self.assertFalse(c._AutoClaimClanReward__enabled)

    def test_progression_preserves_skipped_stages_and_currency_limit(self):
        c = self.controller
        c.updateCache()
        purchase = Mock()
        c._AutoClaimClanReward__claimProgression = purchase
        self.options.points = {'5':NS(price=20), '6':NS(price=120)}
        self.progress.points = {'5':NS(status='available'), '6':NS(status='available')}
        c.parseProgression(self.progress)
        purchase.assert_not_called()
        self.items.items.stats.dynamicCurrencies['tour'] = 150
        c.parseProgression(self.progress)
        purchase.assert_called_once_with(6,120)
        self.progress.points['20'] = NS(status='purchased')
        c.parseProgression(self.progress)
        self.assertEqual(purchase.call_args.args, (5,20))

    def test_pending_reward_request_blocks_duplicates_and_releases_on_completion(self):
        c = self.controller
        pending = c._AutoClaimClanReward__claimRewards()
        self.assertEqual(next(pending), 'pending')
        self.assertTrue(c._AutoClaimClanReward__claim_started)
        duplicate = Mock()
        c._AutoClaimClanReward__claimRewards = duplicate
        c.parseQuests(self.quests)
        duplicate.assert_not_called()
        with self.assertRaises(StopIteration): pending.send(NS(isSuccess=lambda:True))
        self.assertFalse(c._AutoClaimClanReward__claim_started)
        c.parseQuests(self.quests)
        duplicate.assert_called_once()


if __name__ == '__main__':
    unittest.main()
