# -*- coding: utf-8 -*-
"""Clan rewards: free claims stay independent; Tour Coin purchases need an explicit True in the stored settings.

Every web request goes to a fake controller that only records it. No test sends a real purchase or touches an account.
"""
import ast
import json
import os

from support import RuntimeTest, game_source, module

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
PURCHASE = 'purchaseProgression'
CLAIM = ('claim',)


class _Config(object):
    NAME = 'clan_reward_collection'


class _Response(object):
    def __init__(self, success):
        self.success = success

    def isSuccess(self):
        return self.success

    def getCode(self):
        return 0


class _Web(object):
    def __init__(self):
        self.requests = []
        self.next_success = True

    def sendRequest(self, ctx):
        self.requests.append(ctx)
        success, self.next_success = self.next_success, True
        return _Response(success)


def _driver(function):
    """Runs a yield-based process synchronously: every yielded value is sent straight back."""
    def run(*args, **kwargs):
        generator = function(*args, **kwargs)
        try:
            yielded = next(generator)
            while True:
                yielded = generator.send(yielded)
        except StopIteration:
            return None
    return run


class ClanRewardConsentTests(RuntimeTest):
    def setUp(self):
        super(ClanRewardConsentTests, self).setUp()
        self.values = {'enabled': True, 'claimRewards': True}
        self.currencies = {}
        self.messages = []
        self.web = _Web()
        self.cache = module(isInClan=True)
        self.service = module(getComponentDict=lambda config: dict(self.values),
                              onModSettingsChanged=module(connect=lambda *args: None,
                                                          disconnect=lambda *args: None))
        self.api, _ = game_source('lobby/clan_reward_collection.py', stubs=self._stubs(),
                                  real=('driftkings._constants',))
        self.api['settings_service'] = self.service
        self.api['g_clanCache'] = self.cache
        self.api['SystemMessages'] = module(pushMessage=lambda text, type=None: self.messages.append(text),
                                            SM_TYPE=module(Error='error'))
        self.component = self.api['AutoClaimClanReward'](_Config())
        self.component._AutoClaimClanReward__webController = self.web
        self.component._AutoClaimClanReward__itemsCache = module(
            items=module(stats=module(dynamicCurrencies=self.currencies)))
        self.component._AutoClaimClanReward__cachedSettingsData = module(
            enabled=True, points={'1': module(price=40), '2': module(price=60)})

    def _stubs(self):
        return {
            'adisp': module(adisp_process=_driver),
            'gui': module(SystemMessages=module()),
            'gui.clans.clan_cache': module(g_clanCache=module()),
            'gui.clans.data_wrapper.clan_supply': module(
                DataNames=module(QUESTS_INFO='quests', QUESTS_INFO_POST='quests_post',
                                 PROGRESSION_PROGRESS='progress', PROGRESSION_SETTINGS='settings'),
                PointStatus=module(AVAILABLE='available', PURCHASED='purchased'),
                QuestStatus=module(REWARD_AVAILABLE='reward_available', REWARD_PENDING='reward_pending',
                                   COMPLETE='complete')),
            'gui.impl': module(backport=module(text=lambda value: 'text')),
            'gui.impl.gen': module(R=module()),
            'gui.shared.money': module(Currency=module(TOUR_COIN='tourCoin')),
            'gui.wgcg.clan_supply.contexts': module(
                ClaimRewardsCtx=lambda: CLAIM,
                PurchaseProgressionStageCtx=lambda stageID, price: ('purchase', stageID, price)),
            'gui.wgnc': module(g_wgncEvents=module()),
            'gui.wgnc.settings': module(WGNC_DATA_PROXY_TYPE=module(CLAN_SUPPLY_QUEST_UPDATE='quest_update')),
            'helpers': module(dependency=module(descriptor=lambda iface: None)),
            'skeletons.gui.app_loader': module(GuiGlobalSpaceID=module(LOBBY='lobby')),
            'skeletons.gui.shared': module(IItemsCache=None),
            'skeletons.gui.shared.utils': module(IHangarSpace=None),
            'skeletons.gui.web': module(IWebController=None),
            'driftkings.settings.definitions.lobby.clan_reward_collection': module(
                ClanRewardCollectionSettings=lambda: _Config()),
            'driftkings.settings.service': module(settings_service=self.service),
        }

    # helpers ------------------------------------------------------------------
    def set_values(self, **changes):
        self.values.update(changes)

    def set_balance(self, amount):
        self.currencies['tourCoin'] = amount

    def progression(self, first_status='available'):
        return module(points={'1': module(status=first_status), '2': module(status='locked')})

    def quests(self, status='reward_available'):
        return module(quests=[module(status=status)])

    def purchases(self):
        return [ctx for ctx in self.web.requests if ctx[0] == 'purchase']

    def claims(self):
        return [ctx for ctx in self.web.requests if ctx == CLAIM]

    # defaults and migration ---------------------------------------------------
    def test_json_default_keeps_purchases_off(self):
        path = os.path.join(ROOT, 'res', 'configs', 'driftkings', 'default', 'clan_reward_collection.json')
        with open(path) as stream:
            defaults = json.load(stream)
        self.assertIs(defaults[PURCHASE], False)
        # Phase 11.6: free collection is opt-in; purchases stay separately off.
        self.assertIs(defaults['enabled'], False)

    def test_python_fallback_keeps_purchases_off(self):
        path = os.path.join(ROOT, 'mod', 'res', 'scripts', 'client', 'driftkings', 'settings', 'default_values.py')
        with open(path) as stream:
            tree = ast.parse(stream.read())
        table = None
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(getattr(target, 'id', None) == 'DEFAULTS'
                                                     for target in node.targets):
                table = ast.literal_eval(node.value)
        self.assertIsNotNone(table)
        self.assertIs(table['clan_reward_collection'][PURCHASE], False)

    def test_definition_exposes_an_independent_purchase_switch(self):
        namespace, _ = game_source('settings/definitions/lobby/clan_reward_collection.py',
                                   stubs={'driftkings.settings.controls_schema':
                                          module(control=lambda key, **kwargs: ('control', key)),
                                          'driftkings.settings.definitions.base':
                                          module(SectionDefinition=object)},
                                   real=('driftkings._constants',))
        columns = namespace['ClanRewardCollectionSettings'].COLUMNS
        self.assertEqual(columns[0], (('control', PURCHASE),))
        self.assertEqual(columns[1], ())

    def test_older_profile_without_the_key_cannot_authorise_spending(self):
        self.set_balance(100)
        self.assertFalse(self.component.purchasesAuthorised())
        self.component.parseProgression(self.progression())
        self.assertEqual(self.purchases(), [])

    # consent ------------------------------------------------------------------
    def test_explicit_false_blocks_purchases(self):
        self.set_values(**{PURCHASE: False})
        self.set_balance(100)
        self.component.parseProgression(self.progression())
        self.assertEqual(self.purchases(), [])

    def test_only_a_boolean_true_authorises_purchases(self):
        self.set_balance(100)
        for value in ('yes', 'true', 1, 0, None, [], {}):
            self.set_values(**{PURCHASE: value})
            self.assertFalse(self.component.purchasesAuthorised(), repr(value))
            self.component.parseProgression(self.progression())
        self.assertEqual(self.purchases(), [])

    def test_explicit_true_buys_only_the_next_affordable_stage(self):
        self.set_values(**{PURCHASE: True})
        self.set_balance(100)
        self.component.parseProgression(self.progression())
        self.assertEqual(self.purchases(), [('purchase', 1, 40)])

    def test_insufficient_balance_sends_nothing_even_when_authorised(self):
        self.set_values(**{PURCHASE: True})
        self.set_balance(10)
        self.component.parseProgression(self.progression())
        self.assertEqual(self.purchases(), [])

    def test_no_available_stage_sends_nothing(self):
        self.set_values(**{PURCHASE: True})
        self.set_balance(100)
        self.component.parseProgression(self.progression(first_status='purchased'))
        self.assertEqual(self.purchases(), [])

    def test_purchase_in_flight_blocks_a_second_request(self):
        self.set_values(**{PURCHASE: True})
        self.set_balance(100)
        self.component._AutoClaimClanReward__purchase_started = True
        self.component.parseProgression(self.progression())
        self.assertEqual(self.purchases(), [])

    def test_failed_purchase_clears_the_flag_and_reports_once(self):
        self.capture_log('Driftkings.lobby.clan_reward_collection')
        self.set_values(**{PURCHASE: True})
        self.set_balance(100)
        self.web.next_success = False
        self.component.parseProgression(self.progression())
        self.assertEqual(self.purchases(), [('purchase', 1, 40)])
        self.assertFalse(self.component._AutoClaimClanReward__purchase_started)
        self.assertEqual(len(self.messages), 1)

    def test_consent_is_read_when_the_purchase_happens(self):
        self.set_balance(100)
        self.component.parseProgression(self.progression())
        self.assertEqual(self.purchases(), [])
        self.set_values(**{PURCHASE: True})
        self.component.parseProgression(self.progression())
        self.assertEqual(self.purchases(), [('purchase', 1, 40)])

    # free rewards stay independent ----------------------------------------------
    def test_free_claims_work_with_purchases_off(self):
        self.set_values(**{PURCHASE: False})
        self.set_balance(100)
        self.component.parseQuests(self.quests())
        self.assertEqual(self.claims(), [CLAIM])
        self.assertEqual(self.purchases(), [])

    def test_disabling_purchases_does_not_stop_free_claims(self):
        self.set_values(**{PURCHASE: True})
        self.set_balance(100)
        self.set_values(**{PURCHASE: False})
        self.component.parseQuests(self.quests())
        self.assertEqual(self.claims(), [CLAIM])

    def test_section_off_stops_claims_and_purchases(self):
        self.set_values(enabled=False, **{PURCHASE: True})
        self.set_balance(100)
        self.component.onModSettingsChanged(None, {})
        self.component._AutoClaimClanReward__onDataReceived('quests', self.quests())
        self.component._AutoClaimClanReward__onDataReceived('progress', self.progression())
        self.assertEqual(self.web.requests, [])

    def test_section_on_with_purchases_off_claims_but_never_buys(self):
        self.set_values(enabled=True, **{PURCHASE: False})
        self.set_balance(100)
        self.component.onModSettingsChanged(None, {})
        self.component._AutoClaimClanReward__onDataReceived('quests', self.quests())
        self.component._AutoClaimClanReward__onDataReceived('progress', self.progression())
        self.assertEqual(self.claims(), [CLAIM])
        self.assertEqual(self.purchases(), [])
