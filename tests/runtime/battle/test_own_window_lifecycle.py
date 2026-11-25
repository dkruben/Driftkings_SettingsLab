# -*- coding: utf-8 -*-
"""T-N3: pending attachment, delayed attachment, foreign replacement and HUD visibility for owned window cards.

Exercises the shared BattleCardAdapter publish contract (gameface/battle/common.py) that every card hosted by the
owned window uses. Hosting is registered the way own_window.py does it (adapter.views[host] = child). The
window's own creation and loading path is covered by tests/runtime/battle/test_own_battle_window.py.
"""
from support import RuntimeTest, module, source


class Host(object):
    """The shared battle window: one view per card resource id."""
    def __init__(self):
        self.children = {}

    def getChildView(self, resource):
        return self.children.get(resource)


class Child(object):
    """A hosted native card, in the state BattleCardView keeps."""
    def __init__(self):
        self._lastPayload = None
        self._guiVisible = True
        self._cursorVisible = False
        self._ready = False
        self._attached = False
        self._lastVisible = None
        self.destroyed = False

    def setEnabled(self, value):
        pass

    def destroy(self):
        self.destroyed = True


RESOURCES = {'featureA': 42, 'featureB': 43}


class Logger(object):
    def info(self, *args, **kwargs):
        pass

    def debug(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass

    def exception(self, *args, **kwargs):
        pass


class OwnWindowLifecycleTests(RuntimeTest):
    def setUp(self):
        super(OwnWindowLifecycleTests, self).setUp()
        self.published = []
        self.signal = self.load('core.signals').Signal()
        base = source('gameface/battle/common.py', {
            'driftkings.gameface.payloads': module(
                publish_card=lambda child, payload: self.published.append((child, payload))),
            'driftkings.settings.service': module(settings_service=module(onModSettingsChanged=self.signal)),
            'driftkings.interface_catalog': module(gameface_spec=lambda feature: {'resource': feature,
                                                                                  'transport': 'own_window'}),
            'driftkings.gameface.core': module(resource_id=lambda path: RESOURCES[path]),
        })['BattleCardAdapter']
        class Card(base):
            def __init__(self, feature):
                super(Card, self).__init__(feature, 'owned', Logger(), feature, active=True)

            def refresh(self):
                self.publish({'state': self.feature}, {'locked': False},
                             self.active and self.visible and self.hudVisible)

        self.Card = Card
        self.host = Host()
        self.cards = []

    def hosted(self, feature, ready=True, attach=True):
        """Create a card, register its host and child the way own_window.py does."""
        card = self.Card(feature)
        child = Child()
        child._ready = ready
        if attach:
            self.host.children[RESOURCES[feature]] = child
        card.views[self.host] = child
        self.cards.append(card)
        return card, child

    def last_for(self, child):
        for owner, payload in reversed(self.published):
            if owner is child:
                return payload
        return None

    # Pending and delayed attachment

    def test_child_not_yet_ready_publishes_nothing_even_when_attached(self):
        card, child = self.hosted('featureA', ready=False)
        card.refresh()
        self.assertEqual(self.published, [])
        self.assertFalse(child._attached)

    def test_delayed_attachment_publishes_once_the_host_returns_the_child(self):
        card, child = self.hosted('featureA', ready=True, attach=False)
        card.refresh()
        self.assertEqual(self.published, [])
        self.assertIn(self.host, card.views)
        self.host.children[42] = child
        card.refresh()
        self.assertEqual(len(self.published), 1)
        self.assertTrue(child._attached)
        self.assertTrue(self.published[-1][1]['config']['visible'])

    def test_foreign_replacement_drops_the_view_without_destroying_either_child(self):
        card, child = self.hosted('featureA')
        card.refresh()
        foreign = Child()
        self.host.children[42] = foreign
        card.refresh()
        self.assertNotIn(self.host, card.views)
        self.assertEqual(self.last_for(foreign), None)
        card.dispose()
        self.assertFalse(child.destroyed)
        self.assertFalse(foreign.destroyed)

    # HUD and card visibility

    def test_hud_visibility_hides_an_owned_card_and_restores_it(self):
        card, child = self.hosted('featureA')
        card.refresh()
        self.assertTrue(self.last_for(child)['config']['visible'])
        card.setBattleHudVisible(False)
        self.assertFalse(self.last_for(child)['config']['visible'])
        card.setBattleHudVisible(True)
        self.assertTrue(self.last_for(child)['config']['visible'])

    def test_card_gui_visibility_hides_the_card_even_with_the_hud_visible(self):
        card, child = self.hosted('featureA')
        card.refresh()
        child._guiVisible = False
        card.refresh()
        self.assertFalse(self.last_for(child)['config']['visible'])
        self.assertTrue(card.hudVisible)

    def test_cards_sharing_one_window_keep_independent_hud_visibility(self):
        first, first_child = self.hosted('featureA')
        second, second_child = self.hosted('featureB')
        first.refresh()
        second.refresh()
        first.setBattleHudVisible(False)
        self.assertFalse(self.last_for(first_child)['config']['visible'])
        self.assertTrue(self.last_for(second_child)['config']['visible'])

    def test_inactive_card_publishes_hidden_and_disposed_card_publishes_nothing(self):
        card, child = self.hosted('featureA')
        card.active = False
        card.refresh()
        self.assertFalse(self.last_for(child)['config']['visible'])
        card.active = True
        card.dispose()
        count = len(self.published)
        card.refresh()
        self.assertEqual(len(self.published), count)
