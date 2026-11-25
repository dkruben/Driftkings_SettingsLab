# -*- coding: utf-8 -*-
"""T-N2: native MainGun (High Caliber) presentation on the real MainGunAdapter and BattleCardAdapter contract.

Replaces the presentation checks of the removed OpenWG-era test: labels and formatting from the Portuguese
catalog, state labels, visibility guards, position guards and disposal. The damage projection itself stays
covered by tests/runtime/battle/test_high_caliber.py. Only game boundaries are stubbed.
"""
import json
import os

from support import ROOT, RuntimeTest, module, source


class Parent(object):
    child = None

    def getChildView(self, resource):
        return self.child


class Child(object):
    def __init__(self):
        self._lastPayload = None
        self._guiVisible = True
        self._cursorVisible = False
        self._ready = True
        self._attached = False
        self._lastVisible = None
        self.destroyed = False

    def setEnabled(self, value):
        pass

    def destroy(self):
        self.destroyed = True


class MainGunPresentationTests(RuntimeTest):
    def setUp(self):
        super(MainGunPresentationTests, self).setUp()
        self.constants = self.load('_constants')
        self.GLOBAL = self.constants.GLOBAL
        self.HC = self.constants.HIGH_CALIBER_PROGRESS
        with open(os.path.join(ROOT, 'res/configs/driftkings/default/high_caliber_progress.json'), 'rb') as stream:
            self.settings = json.load(stream)
        self.settings[self.GLOBAL.ENABLED] = True
        self.settings[self.HC.TEXT_LOCK] = False
        self.applied, self.published = [], []
        self.attached, self.detached = [], []
        with open(os.path.join(ROOT, 'mod/res/mods/driftkings/text/pt.yml'), 'rb') as stream:
            self.catalog = self.load('core.locale_catalog').parse_catalog(stream.read())['TEXT']
        self.labels = self.catalog['high_caliber_progress']
        self.mainGuns = module(payload={'state': 'progress', 'remaining': 1234, 'progress': 40,
                                        'visible': True, 'damage': 0})
        component = module(high_caliber_progress_settings=module(lang='pt', i18n=self.labels),
                           mainGuns=self.mainGuns)
        service = module(getComponentDict=lambda config: self.settings,
                         apply=lambda config, changes: self.applied.append(changes),
                         onModSettingsChanged=self.load('core.signals').Signal())
        common_deps = {
            'driftkings.settings.service': module(settings_service=service),
            'driftkings.gameface.payloads': module(
                publish_card=lambda child, payload: self.published.append((child, payload))),
            'driftkings.interface_catalog': module(gameface_spec=lambda feature: {
                'resource': 'maingun', 'transport': 'own_window'}),
            'driftkings.gameface.core': module(resource_id=lambda path: 42),
        }
        base = source('gameface/battle/common.py', common_deps)['BattleCardAdapter']
        deps = dict(common_deps)
        deps.update({
            'driftkings.gameface.battle.common': module(BattleCardAdapter=base),
            'driftkings._constants': self.constants,
            'driftkings.core.hud_visibility': module(hudVisibility=module(
                attach=lambda view: self.attached.append(view), detach=lambda view: self.detached.append(view))),
            'driftkings.views.marks_model': self.load('views.marks_model'),
            'importlib': module(import_module=lambda name: component),
        })
        self.adapter = source('gameface/battle/high_caliber_gameface.py', deps)['MainGunAdapter']()
        self.adapter.active = True
        self.adapter.onInstalled()

    def attach_card(self):
        parent, child = Parent(), Child()
        self.adapter.views[parent] = child
        parent.child = child
        self._keep = parent
        return child

    def last(self):
        return self.published[-1][1]

    def refresh_with(self, **payload):
        self.mainGuns.payload.update(payload)
        self.adapter.refresh()

    # Localised presentation

    def test_progress_state_formats_remaining_damage_with_the_catalog_labels(self):
        self.attach_card()
        self.adapter.refresh()
        published = self.last()
        self.assertEqual(published['primaryText'], u'1 234 HP')
        self.assertEqual(published['secondaryText'], self.labels['UI_hc_progress'])
        self.assertEqual(published['progressText'], u'40%')
        self.assertEqual(published['progressLabel'], self.labels['UI_hc_progressLabel'])

    def test_achieved_state_shows_the_damage_and_the_achieved_label(self):
        self.attach_card()
        self.refresh_with(state='achieved', damage=4000, progress=100, remaining=0)
        published = self.last()
        self.assertEqual(published['primaryText'], u'4 000 HP')
        self.assertEqual(published['secondaryText'], self.labels['UI_hc_achieved'])
        self.assertEqual(published['progressText'], u'100%')

    def test_unavailable_state_shows_the_unavailable_label_and_the_reason(self):
        self.attach_card()
        self.refresh_with(state='unavailable', reason='insufficient', remaining=0, progress=0)
        published = self.last()
        self.assertEqual(published['primaryText'], self.labels['UI_hc_unavailable'])
        self.assertEqual(published['secondaryText'], self.labels['UI_hc_insufficient'])

    def test_ineligible_reason_is_shown_for_an_unavailable_target(self):
        self.attach_card()
        self.refresh_with(state='unavailable', reason='ineligible', remaining=0, progress=0)
        self.assertEqual(self.last()['secondaryText'], self.labels['UI_hc_ineligible'])

    def test_stale_renderer_key_never_switches_off_the_presentation(self):
        self.attach_card()
        self.settings['renderer'] = 'legacy'
        self.adapter.refresh()
        self.assertTrue(self.last()['config']['visible'])

    # Visibility guards

    def test_card_is_visible_only_with_visible_payload_hud_and_enabled_setting(self):
        self.attach_card()
        self.adapter.refresh()
        self.assertTrue(self.last()['config']['visible'])
        self.refresh_with(visible=False)
        self.assertFalse(self.last()['config']['visible'])
        self.refresh_with(visible=True)
        self.adapter.setBattleHudVisible(False)
        self.assertFalse(self.last()['config']['visible'])
        self.adapter.setBattleHudVisible(True)
        self.settings[self.GLOBAL.ENABLED] = False
        self.adapter.refresh()
        self.assertFalse(self.last()['config']['visible'])

    def test_inactive_adapter_publishes_hidden(self):
        self.attach_card()
        self.adapter.active = False
        self.adapter.refresh()
        self.assertFalse(self.last()['config']['visible'])

    def test_hidden_card_cursor_refuses_drag_and_gui_visibility_hides_card(self):
        child = self.attach_card()
        child._cursorVisible = True
        self.adapter.refresh()
        self.assertTrue(self.last()['config']['draggable'])
        child._guiVisible = False
        self.adapter.refresh()
        self.assertFalse(self.last()['config']['visible'])
        self.assertFalse(self.last()['config']['draggable'])

    # Position guards

    def test_position_save_is_refused_while_text_is_locked(self):
        child = self.attach_card()
        child._cursorVisible = True
        self.settings[self.HC.TEXT_LOCK] = True
        self.adapter.savePosition(child, {'x': 10, 'y': 10, 'alignX': 'left'})
        self.assertEqual(self.applied, [])

    def test_position_save_is_refused_when_the_payload_is_not_visible(self):
        child = self.attach_card()
        child._cursorVisible = True
        self.mainGuns.payload['visible'] = False
        self.adapter.savePosition(child, {'x': 10, 'y': 10})
        self.assertEqual(self.applied, [])

    def test_unlocked_visible_drag_saves_a_clamped_position_with_its_anchor(self):
        child = self.attach_card()
        child._cursorVisible = True
        self.adapter.savePosition(child, {'x': 99999, 'y': -99999, 'alignX': 'left', 'alignY': 'top'})
        self.assertEqual(len(self.applied), 1)
        position = self.applied[-1][self.HC.TEXT_POSITION]
        self.assertEqual((position['x'], position['y']), (7680, -4320))
        self.assertEqual((position['alignX'], position['alignY']), ('left', 'top'))

    def test_draggable_follows_the_text_lock(self):
        child = self.attach_card()
        child._cursorVisible = True
        self.adapter.refresh()
        self.assertTrue(self.last()['config']['draggable'])
        self.settings[self.HC.TEXT_LOCK] = True
        self.adapter.refresh()
        self.assertFalse(self.last()['config']['draggable'])

    # Disposal

    def test_dispose_detaches_from_the_hud_and_releases_the_card(self):
        child = self.attach_card()
        self.adapter.dispose()
        self.assertEqual(self.detached, [self.adapter])
        self.assertTrue(child.destroyed)
        self.assertFalse(self.adapter.active)
        self.assertEqual(len(self.adapter.views), 0)
