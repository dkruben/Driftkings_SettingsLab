# -*- coding: utf-8 -*-
"""Battle mode classification: Halloween is its own mode, every other mode keeps its class."""
from support import RuntimeTest, module


# EU 2.4.1.1 values; HALLOWEEN* are injected by the halloween extension.
NAMES = {'UNKNOWN': 0, 'REGULAR': 1, 'TRAINING': 2, 'EVENT_BATTLES': 9, 'EPIC_BATTLE': 27, 'COMP7': 43,
         'WINBACK': 44, 'RANDOM_NP2': 46, 'HALLOWEEN': 101, 'HALLOWEEN_MEDIUM': 102, 'HALLOWEEN_HARD': 103,
         'LAST_STAND': 107, 'BATTLE_ROYALE_SOLO': 29}
HALLOWEEN = ('HALLOWEEN', 'HALLOWEEN_MEDIUM', 'HALLOWEEN_HARD')


class BattleModeTests(RuntimeTest):
    def setUp(self):
        super(BattleModeTests, self).setUp()
        self.capabilities = self.load('core.battle_capabilities')
        self.bonus = None

    def context(self, names=NAMES):
        enum = module(**dict(names, RANGE=tuple(names.values()), RANDOM_RANGE=(1, 46)))
        return self.capabilities.BattleCapabilities(
            player=lambda: module(arena=module(bonusType=self.bonus)), session=lambda: None,
            modules={'constants': module(ARENA_BONUS_TYPE=enum)})

    def mode(self, value, names=NAMES):
        self.bonus = value
        return self.context(names).current_mode()

    def test_halloween_difficulties_are_their_own_mode(self):
        for name in HALLOWEEN:
            self.bonus = NAMES[name]
            context = self.context()
            self.assertEqual(context.current_mode(), 'halloween', name)
            self.assertTrue(context.is_halloween(), name)
            # Halloween stays an event mode with restricted numbers and no statistics features.
            self.assertTrue(context.is_event_mode(), name)
            self.assertTrue(context.is_special(), name)
            self.assertFalse(context.is_statistics_battle(), name)
            self.assertFalse(context.is_random(), name)

    def test_halloween_values_are_recognised_when_the_names_are_missing(self):
        names = dict((key, value) for key, value in NAMES.items() if not key.startswith('HALLOWEEN'))
        for value in (101, 102, 103):
            self.assertEqual(self.mode(value, names), 'halloween', value)

    def test_other_modes_keep_their_classification(self):
        expected = {'REGULAR': 'random', 'RANDOM_NP2': 'random', 'WINBACK': 'random', 'COMP7': 'comp7',
                    'EPIC_BATTLE': 'frontline', 'EVENT_BATTLES': 'event', 'TRAINING': 'special',
                    'LAST_STAND': 'special', 'BATTLE_ROYALE_SOLO': 'special', 'UNKNOWN': 'unknown'}
        for name, mode in expected.items():
            self.assertEqual(self.mode(NAMES[name]), mode, name)
            self.assertFalse(self.context().is_halloween(), name)
        self.assertEqual(self.mode(250), 'unknown')

    def test_outside_battle_is_never_halloween(self):
        context = self.capabilities.BattleCapabilities(player=lambda: module(arena=None), session=lambda: None,
                                                       modules={'constants': module(ARENA_BONUS_TYPE=module(**NAMES))})
        self.assertFalse(context.is_halloween())
        self.assertNotEqual(context.current_mode(), 'halloween')
