# -*- coding: utf-8 -*-
"""Characterize failures; scenario B now verifies the authorized F4-G3.2 repair.

AS3 case A is STATIC_RISK/UNVERIFIED_AVM2. Python cases execute real source
against deterministic boundaries; none establish observed CT failure rates.
"""
import os
import re

from support import ROOT, RuntimeTest, game_source, module, source
from support.rosters import Harness, battle


class Signal(object):
    def __init__(self, strict=False):
        self.handlers = []
        self.strict = strict
        self.removals = []
        self.deliveries = []

    def __iadd__(self, handler):
        if handler not in self.handlers:
            self.handlers.append(handler)
        return self

    def __isub__(self, handler):
        self.removals.append(handler)
        if handler in self.handlers:
            self.handlers.remove(handler)
        elif self.strict:
            raise ValueError('handler was never subscribed')
        return self

    def emit(self, *args):
        for handler in list(self.handlers):
            self.deliveries.append(handler)
            handler(*args)


class Owners(object):
    """Fixed iteration order to expose the first failure, not a WeakSet model."""
    def __init__(self):
        self.items = []

    def add(self, owner):
        if owner not in self.items:
            self.items.append(owner)

    def discard(self, owner):
        if owner in self.items:
            self.items.remove(owner)

    def __iter__(self):
        return iter(list(self.items))


class Meta(object):
    def __init__(self, *args):
        self.ready = False
        self.populates = 0
        self.disposes = 0
        self.sent = []
        self.flashObject = module(as_minimapCamera=self.sent.append)

    def _populate(self):
        self.ready = True
        self.populates += 1

    def _dispose(self):
        self.ready = False
        self.disposes += 1

    def _isDAAPIInited(self):
        return self.ready

    def as_applyConfigS(self, config):
        self.config = config

    def as_setRosterS(self, payload):
        self.sent.append(payload)


class FlashFailureCharacterizationTests(RuntimeTest):
    def setUp(self):
        super(FlashFailureCharacterizationTests, self).setUp()
        self.logs = self.capture_log('Driftkings.Views')

    def test_A_static_factory_orders_add_before_registration_without_rollback(self):
        # Deliberately no fake Python factory: this does not execute AS3/AVM2.
        path = os.path.join(ROOT, 'flash_source', 'battle', 'src', 'driftkings',
                            'battle', 'factory', 'ComponentFactory.as')
        with open(path, 'rb') as stream:
            text = stream.read().decode('utf-8')
        text = re.sub(r'//[^\n]*|/\*[\s\S]*?\*/', '', text)
        sequence = ('ComponentCatalog.classes(surface)', 'new type()',
                    'hud.battlePage = host as BaseBattlePage',
                    'host.addChild(component)', 'host.registerFlashComponentS(component, alias)')
        positions = [text.index(item) for item in sequence]
        self.assertEqual(positions, sorted(positions))
        self.assertIsNone(re.search(r'\b(try|catch|finally)\b|removeChild|unregisterFlashComponent', text))

    def registry_environment(self):
        libraries = ['native.swf']
        packages = {1: ['native.package']}
        api = source('flash/battle/registry.py', {
            'constants': module(ARENA_GUI_TYPE=module(RANGE=(1,))),
            'gui.override_scaleform_views_manager': module(
                g_overrideScaleFormViewsConfig=module(battlePackages=packages)),
            'gui.Scaleform.required_libraries_config': module(BATTLE_REQUIRED_LIBRARIES=libraries)})
        owners = Owners()
        api['BATTLE_HANDLERS'] = owners
        fault, cancelled = [False], []

        def cancel(token):
            cancelled.append(token)
            if fault[0] and (fault[0] is True or token in fault[0]):
                raise RuntimeError('controlled backend cancellation failure')

        class BusinessHandler(object):
            def __init__(self, *args, **kwargs):
                pass
            def init(self):
                pass
            def fini(self):
                pass

        handlers = source('flash/battle/handler.py', {
            'BigWorld': module(cancelCallback=cancel),
            'frameworks.wulf': module(WindowLayer=module(VIEW=1)),
            'gui.app_loader.settings': module(APP_NAME_SPACE=module(SF_BATTLE=1)),
            'gui.Scaleform.daapi.settings.views': module(VIEW_ALIAS=module(BATTLE_PAGES=('page',)),
                                                       VIEW_BATTLE_PAGE_CONFIG_BY_ARENA_GUI_TYPE={}),
            'gui.Scaleform.framework.package_layout': module(PackageBusinessHandler=BusinessHandler),
            'gui.shared': module(EVENT_BUS_SCOPE=module(BATTLE=1)),
            'driftkings.flash.battle.registry': module(BATTLE_COMPONENTS=api['BATTLE_COMPONENTS'],
                                                      BATTLE_HANDLERS=owners),
            'driftkings.interface_catalog': self.load('interface_catalog'),
            'driftkings.logger': self.load('logger')})
        state = module(active=False, stopped=0)
        def start():
            state.active = True
        def stop():
            state.active = False
            state.stopped += 1
        registration = api['BattlePackageRegistration']()
        service = api['BattleViews'](registration, module(start=start, stop=stop))
        service.start()
        api['BATTLE_COMPONENTS']['sample'] = ('view', 'config')
        return module(api=api, owners=owners, handler=handlers['BattleViewHandler'], fault=fault,
                      cancelled=cancelled, service=service, registration=registration,
                      visibility=state, libraries=libraries, packages=packages)

    def test_B_close_failure_cleans_independent_resources_and_service_retries(self):
        # Original G3.1: only token 11 attempted; both handlers/registrations and
        # visibility survived, and a second service.stop was inert (progress §27).
        e = self.registry_environment()
        first, second = e.handler(), e.handler()
        first.init()
        second.init()
        first.pending, second.pending = 11, 22
        first.pageAlias = 'page'
        e.fault[0] = set((11,))
        self.assertRaises(RuntimeError, e.service.stop)
        self.assertFalse(e.service.active)
        self.assertTrue(self.logs)  # Failure is logged, not reported as success.
        self.assertFalse(first.active)
        self.assertFalse(second.active)
        self.assertEqual((first.pending, second.pending), (11, None))
        self.assertEqual(e.owners.items, [first])
        self.assertEqual(e.cancelled, [11, 22])
        self.assertFalse(e.visibility.active)
        self.assertEqual(e.visibility.stopped, 1)
        self.assertEqual(e.libraries, ['native.swf'])
        self.assertEqual(e.packages[1], ['native.package'])
        self.assertEqual(e.api['BATTLE_COMPONENTS'], {})
        self.assertTrue(e.service._pendingStop)
        self.assertIn(first, e.registration.pendingHandlers)
        self.assertRaises(RuntimeError, e.service.start)
        self.assertRaises(RuntimeError, e.service.stop)
        self.assertEqual(e.cancelled, [11, 22, 11])
        self.assertEqual(e.visibility.stopped, 1)
        e.fault[0] = False
        e.service.stop()
        self.assertEqual((first.pending, second.pending), (None, None))
        self.assertIsNone(first.pageAlias)
        self.assertEqual(e.owners.items, [])
        self.assertFalse(e.registration.pendingHandlers)
        self.assertFalse(e.service._pendingStop)
        self.assertEqual(e.cancelled, [11, 22, 11, 11])
        self.assertEqual(e.visibility.stopped, 1)
        e.service.stop()
        self.assertEqual(e.cancelled, [11, 22, 11, 11])
        self.assertEqual(e.visibility.stopped, 1)

    def test_B_all_failed_handlers_remain_retryable_and_late_discovery_is_inert(self):
        e = self.registry_environment()
        first, second = e.handler(), e.handler()
        first.init()
        second.init()
        first.pending, second.pending = 11, 22
        e.fault[0] = True
        self.assertRaises(RuntimeError, e.service.stop)
        self.assertEqual(e.cancelled, [11, 22])
        self.assertEqual(set(e.registration.pendingHandlers), set((first, second)))
        self.assertFalse(first.active)
        self.assertFalse(second.active)
        # Simulate a WeakSet no longer providing the failed owner. The registry
        # must keep its own strong reference for retry, not rely on the engine.
        e.owners.discard(first)
        first._findPage()
        self.assertIsNone(first.pending)  # delivered callback consumes its token
        e.fault[0] = False
        e.service.stop()
        self.assertFalse(e.registration.pendingHandlers)
        self.assertFalse(e.service._pendingStop)
        self.assertEqual(e.cancelled, [11, 22, 22])
        self.assertFalse(e.visibility.active)

    def test_B_normal_service_stop_preserves_order_and_is_repeatable(self):
        e = self.registry_environment()
        handler = e.handler()
        handler.init()
        handler.pending = 31
        events = []
        uninstall, hide = e.registration.uninstall, e.service.visibility.stop
        def remove():
            events.append('uninstall')
            uninstall()
        def stop_visibility():
            self.assertEqual(e.api['BATTLE_COMPONENTS'], {})
            events.append('hide')
            hide()
        e.registration.uninstall = remove
        e.service.visibility.stop = stop_visibility
        e.service.stop()
        e.service.stop()
        self.assertEqual(events, ['uninstall', 'hide'])
        self.assertEqual(e.cancelled, [31])
        self.assertFalse(e.service.active)
        self.assertFalse(e.service._pendingStop)
        self.assertEqual(e.owners.items, [])

    def test_B_visibility_failure_retries_only_visibility_and_propagates(self):
        e = self.registry_environment()
        events, fault = [], [True]
        uninstall, hide = e.registration.uninstall, e.service.visibility.stop
        error = RuntimeError('controlled visibility stop failure')
        def remove():
            events.append('uninstall')
            uninstall()
        def stop_visibility():
            events.append('hide')
            if fault[0]:
                raise error
            hide()
        e.registration.uninstall = remove
        e.service.visibility.stop = stop_visibility
        with self.assertRaises(RuntimeError) as raised:
            e.service.stop()
        self.assertIs(raised.exception, error)
        self.assertTrue(e.service._pendingStop)
        fault[0] = False
        e.service.stop()
        e.service.stop()
        self.assertEqual(events, ['uninstall', 'hide', 'hide'])
        self.assertFalse(e.visibility.active)
        self.assertFalse(e.service._pendingStop)

    def test_B_failed_start_cleanup_is_retryable_without_restarting_visibility(self):
        cls = self.load('flash.battle.registry').BattleViews
        events, fault = [], [True]
        def install(definitions):
            events.append('install')
            raise ValueError('controlled install failure')
        def uninstall():
            events.append('uninstall')
            if fault[0]:
                raise RuntimeError('controlled uninstall failure')
        service = cls(module(install=install, uninstall=uninstall),
                      module(start=lambda: events.append('show'), stop=lambda: events.append('hide')))
        self.assertRaises(RuntimeError, service.start)
        self.assertEqual(events, ['show', 'install', 'uninstall', 'hide'])
        self.assertFalse(service.active)
        self.assertTrue(service._pendingStop)
        fault[0] = False
        service.stop()
        service.stop()
        self.assertEqual(events, ['show', 'install', 'uninstall', 'hide', 'uninstall'])
        self.assertFalse(service._pendingStop)

    def test_B_normal_close_is_repeatable_and_late_discovery_is_inert(self):
        e = self.registry_environment()
        handler = e.handler()
        handler.init()
        handler.pending = 31
        old_discovery = handler._findPage
        handler.close()
        handler.close()
        old_discovery()  # Would require game discovery dependencies if not protected.
        self.assertEqual(e.cancelled, [31])
        self.assertIsNone(handler.pending)
        self.assertFalse(handler.active)
        self.assertNotIn(handler, e.owners.items)

    def roster(self):
        h = Harness(self, battle(1, 1), 'random')
        h.api['PlayersPanelMeta'] = Meta
        owner = h.api['RatingViews'](h.views.config, h.stats)
        refreshes = []
        owner.refresh = lambda *args: refreshes.append(owner.view)
        return owner, refreshes

    def test_C1_old_width_callback_cannot_mutate_current_owner(self):
        # G3.1 originally reproduced widths=(123,456) here; see progress section 27.
        owner, refreshes = self.roster()
        old, current = owner.screenClass(), owner.screenClass()
        old._populate()
        late_width = old.reportWidths
        current._populate()
        old._dispose()
        widths = owner.model.widths
        late_width(123, 456)
        self.assertEqual(owner.model.widths, widths)
        self.assertIs(owner.view, current)
        self.assertTrue(current.ready)

    def test_C1_old_screen_callback_cannot_refresh_replacement_or_ended_owner(self):
        # Previously changed visibleScreens and called refresh even after end().
        owner, refreshes = self.roster()
        old, current = owner.screenClass(), owner.screenClass()
        old._populate()
        late_screens = old.reportScreens
        current._populate()
        old._dispose()
        screens, count = set(owner.visibleScreens), len(refreshes)
        late_screens(False, True, False)
        self.assertEqual(owner.visibleScreens, screens)
        self.assertEqual(len(refreshes), count)
        owner.end()
        late_screens(True, False, False)
        self.assertIsNone(owner.view)
        self.assertEqual(owner.visibleScreens, set(('panel', 'loading', 'tab')))
        self.assertEqual(len(refreshes), count)

    def test_C1_current_callbacks_remain_legitimate_during_view_transition(self):
        owner, refreshes = self.roster()
        view = owner.screenClass()
        view._populate()
        candidate = owner.screenClass()  # Construction does not transfer ownership.
        modes = []
        owner.active = True
        owner.setMode = modes.append
        view.reportWidths(123, 456)
        view.reportScreens(False, True, False)
        view.hoverPanel(True)
        self.assertEqual(owner.model.widths, (123, 456))
        self.assertEqual(owner.visibleScreens, set(('loading',)))
        self.assertTrue(owner.hovered)
        self.assertEqual(modes, [4])
        self.assertIs(refreshes[-1], view)
        self.assertIs(owner.view, view)
        candidate._dispose()  # Disposing an unpopulated candidate also leaves owner intact.
        self.assertIs(owner.view, view)
        view.reportScreens(True, False, True)
        self.assertEqual(owner.visibleScreens, set(('panel', 'tab')))

    def test_C1_all_old_callbacks_rejected_after_replacement_and_repeated_end(self):
        owner, refreshes = self.roster()
        old, current = owner.screenClass(), owner.screenClass()
        old._populate()
        callbacks = (lambda: old.reportState('stale'), lambda: old.hoverPanel(True),
                     lambda: old.reportWidths(999, 888),
                     lambda: old.reportScreens(False, False, False),
                     lambda: old.reportPerformance('stale performance'))
        calls = []
        owner.hover = calls.append
        records = self.capture_log('Driftkings.PlayerPanelPro', level=20)
        current._populate()
        records[:] = []
        for ended in (False, True):
            if ended:
                owner.end()
                owner.end()
            widths, screens, count = owner.model.widths, set(owner.visibleScreens), len(refreshes)
            for callback in callbacks:
                callback()
            self.assertEqual(owner.model.widths, widths)
            self.assertEqual(owner.visibleScreens, screens)
            self.assertEqual(len(refreshes), count)
            self.assertEqual(calls, [])
            self.assertEqual(records, [])
        old._dispose()
        old._dispose()
        current._dispose()
        self.assertIsNone(owner.view)

    def test_C1_callbacks_after_current_dispose_are_inert_and_new_view_can_bind(self):
        owner, refreshes = self.roster()
        first = owner.screenClass()
        first._populate()
        first._dispose()
        widths, count = owner.model.widths, len(refreshes)
        first.reportWidths(1, 2)
        first.reportScreens(False, False, False)
        self.assertEqual(owner.model.widths, widths)
        self.assertEqual(len(refreshes), count)
        owner.end()
        second = owner.screenClass()
        second._populate()
        first.reportWidths(9, 9)
        first._dispose()
        self.assertIs(owner.view, second)
        second.reportWidths(3, 4)
        second.reportScreens(False, False, True)
        self.assertEqual(owner.model.widths, (3, 4))
        self.assertEqual(owner.visibleScreens, set(('tab',)))
        self.assertIs(refreshes[-1], second)

    def test_C1_current_diagnostics_callbacks_keep_their_public_behavior(self):
        h = Harness(self, battle(1, 1), 'random')
        h.api['PlayersPanelMeta'] = Meta
        h.data['performance']['diagnostics'] = True
        owner = h.api['RatingViews'](h.views.config, h.stats)
        records = self.capture_log('Driftkings.PlayerPanelPro', level=20)
        view = owner.screenClass()
        view._populate()
        records[:] = []
        view.reportState('current')
        view.reportPerformance('current performance')
        self.assertEqual([r.getMessage() for r in records],
                         ['Roster v2: current', 'Performance Flash: current performance'])
        owner.end()
        records[:] = []
        view.reportState('old')
        view.reportPerformance('old performance')
        self.assertEqual(records, [])

    def test_C1_real_refresh_schedules_only_current_view_and_stops_after_end(self):
        h = Harness(self, battle(1, 1), 'random')
        h.api['PlayersPanelMeta'] = Meta
        owner = h.api['RatingViews'](h.views.config, h.stats)
        owner.active = True
        old, current = owner.screenClass(), owner.screenClass()
        old._populate()
        self.assertEqual(len(h.callbacks), 1)
        owner.callback = None  # Deterministic completion of the first scheduling slot.
        current._populate()
        self.assertEqual(len(h.callbacks), 2)
        owner.callback = None
        old.reportScreens(False, False, False)
        self.assertEqual(len(h.callbacks), 2)
        self.assertIsNone(owner.callback)
        current.reportScreens(True, False, False)
        self.assertEqual(len(h.callbacks), 3)
        owner.end()
        owner.end()
        self.assertEqual(h.cancelled, [3])
        widths, screens = owner.model.widths, set(owner.visibleScreens)
        current.reportWidths(333, 444)
        current.reportScreens(False, False, False)
        current.hoverPanel(True)
        self.assertEqual(owner.model.widths, widths)
        self.assertEqual(owner.visibleScreens, screens)
        self.assertFalse(owner.hovered)
        self.assertEqual(len(h.callbacks), 3)
        self.assertIsNone(owner.callback)

    def distance(self):
        component = module(g_distanceMarker=None)
        api, _ = game_source('flash/battle/target_distance.py', {
            'driftkings.flash.battle.meta.distance_marker': module(DistanceMarkerMeta=Meta),
            'GUI': module(screenResolution=lambda: (1920, 1080))}, real=('driftkings._constants',))
        api['_component'] = lambda: component
        api['serializeConfigParams'] = lambda: {}
        return api, component

    def test_C2_old_distance_view_reads_new_controller_without_sender_guard(self):
        api, component = self.distance()
        payload, reads = {'arena': 'A'}, []
        component.g_distanceMarker = module(py_requestFrameData=lambda: reads.append('A') or payload)
        old = api['DistanceMarkerView']()
        old._populate()
        self.assertIs(old.py_requestFrameData(), payload)
        late = old.py_requestFrameData
        old._dispose()
        current = api['DistanceMarkerView']()
        new_payload = {'arena': 'B'}
        component.g_distanceMarker = module(py_requestFrameData=lambda: reads.append('B') or new_payload)
        current._populate()
        self.assertIs(late(), new_payload)
        self.assertIs(api['_view'], current)
        self.assertEqual(reads, ['A', 'B'])
        self.assertEqual(new_payload, {'arena': 'B'})  # Read forwarding; no mutation by view.
        old._dispose()
        self.assertIs(api['_view'], current)

    def test_C2_no_controller_returns_empty_frame_even_for_disposed_view(self):
        api, component = self.distance()
        view = api['DistanceMarkerView']()
        view._populate()
        view._dispose()
        self.assertEqual(view.py_requestFrameData(), {
            'screenWidth': 1920, 'screenHeight': 1080, 'observedVehicles': []})

    def minimap(self, strict=False):
        a = module(onCameraChanged=Signal(strict), ctrlModeName='strategic')
        b = module(onCameraChanged=Signal(strict), ctrlModeName='strategic')
        current, cancelled, fault = [a], [], [False]
        ctrl = module(_active=False, minimapZoom=False, deactivations=0)
        def activate():
            ctrl._active = True
        def deactivate():
            ctrl.deactivations += 1
            if fault[0]:
                raise RuntimeError('controlled controller deactivation failure')
            ctrl._active = False
        ctrl.activate, ctrl.deactivate = activate, deactivate
        component = module(minimap_settings=module(NAME='minimap_enhancements'), VIEWS=set(),
                           VEHICLES=set(), PERSONAL=set(), controller=ctrl)
        events = module(onAltKey=Signal(strict))
        meta = source('flash/battle/meta/minimap.py', {
            'driftkings.flash.battle.meta.base': module(BattleMeta=Meta)})['MinimapMeta']
        api, _ = game_source('flash/battle/minimap_enhancements.py', {
            'driftkings.game_constants': module(CTRL_MODE_NAME=module(STRATEGIC='strategic', ARTY='arty')),
            'driftkings.flash.battle.meta.minimap': module(MinimapMeta=meta),
            'gui.battle_control.avatar_getter': module(getInputHandler=lambda: current[0]),
            'driftkings.core.battle_policy': module(battle_policy=module(decision=lambda name: (True, 'test'))),
            'driftkings.ui.common.events': module(g_events=events),
            'driftkings.core.callbacks': module(callback=lambda *args: 99, cancelCallback=cancelled.append)})
        api['_component'] = lambda: component
        view = api['MinimapEnhancementsView']()
        # Isolate camera ownership from unrelated geometry/settings; real populate/dispose run.
        view.onAltKey = lambda pressed: None
        view._populate()
        return module(view=view, a=a, b=b, current=current, component=component,
                      events=events, cancelled=cancelled, fault=fault)

    def test_D_handler_replacement_retains_A_listener_with_permissive_removal(self):
        e = self.minimap()
        self.assertEqual(e.a.onCameraChanged.handlers, [e.view.onCameraChanged])
        e.current[0] = e.b
        before = list(e.view.sent)
        e.view._dispose()
        self.assertEqual(e.a.onCameraChanged.handlers, [e.view.onCameraChanged])
        self.assertEqual(e.b.onCameraChanged.removals, [e.view.onCameraChanged])
        self.assertFalse(e.view.ready)
        e.a.onCameraChanged.emit('arty')
        self.assertEqual(len(e.a.onCameraChanged.deliveries), 1)
        self.assertEqual(e.view.sent, before)  # Real meta's DAAPI availability guard protects send.

    def test_D_strict_missing_handler_removal_interrupts_base_disposal(self):
        e = self.minimap(strict=True)
        e.current[0] = e.b
        self.assertRaises(ValueError, e.view._dispose)
        self.assertTrue(e.view.ready)
        self.assertEqual(e.view.disposes, 0)
        self.assertEqual(e.a.onCameraChanged.handlers, [e.view.onCameraChanged])
        e.a.onCameraChanged.emit('arty')
        self.assertEqual(e.view.sent[-1], True)

    def test_D_unchanged_handler_releases_subscription_normally(self):
        e = self.minimap()
        e.view._dispose()
        self.assertEqual(e.a.onCameraChanged.handlers, [])
        e.a.onCameraChanged.emit('arty')
        self.assertEqual(e.a.onCameraChanged.deliveries, [])
        self.assertFalse(e.view.ready)

    def test_E_deactivation_failure_leaves_alt_camera_and_base_cleanup_pending(self):
        e = self.minimap()
        e.view._releaseCallback = 99
        e.fault[0] = True
        self.assertRaises(RuntimeError, e.view._dispose)
        self.assertEqual(e.cancelled, [99])
        self.assertIsNone(e.view._releaseCallback)
        self.assertNotIn(e.view, e.component.VIEWS)
        self.assertTrue(e.component.controller._active)
        self.assertIn(e.view.onAltKey, e.events.onAltKey.handlers)
        self.assertIn(e.view.onCameraChanged, e.a.onCameraChanged.handlers)
        self.assertTrue(e.view.ready)
        e.fault[0] = False
        e.view._dispose()
        self.assertEqual(e.cancelled, [99])
        self.assertEqual(e.component.controller.deactivations, 2)
        self.assertEqual(e.events.onAltKey.handlers, [])
        self.assertEqual(e.a.onCameraChanged.handlers, [])
        self.assertFalse(e.view.ready)

    def test_E_sixth_sound_failure_prevents_signal_and_base_cleanup_until_retry(self):
        constants = self.load('_constants')
        events = module(onRoundFinished=Signal(), onObservedByEnemy=Signal())
        vehicle, devices = module(onVehicleStateUpdated=Signal()), module(onDescriptorDevicesChanged=Signal())
        class SixthMeta(Meta):
            def getSettings(self):
                return {constants.SIXTH_SENSE_ALERT.PLAY_TICK_SOUND: False}
        api, _ = game_source('flash/battle/sixth_sense_alert.py', {
            'driftkings.flash.battle.meta.sixth_sense': module(SixthSenseMeta=SixthMeta),
            'gui.battle_control.battle_constants': module(VEHICLE_VIEW_STATE=module(
                SWITCHING=1, RESPAWNING=2, DESTROYED=3, CREW_DEACTIVATED=4)),
            'PlayerEvents': module(g_playerEvents=events),
            'SoundGroups': module(g_instance=None)}, real=('driftkings._constants',))
        component = module(g_view=None)
        api['_component'] = lambda: component
        view = api['SixthSense']()
        view.sessionProvider = module(isReplayPlaying=False,
                                      shared=module(vehicleState=vehicle, optionalDevices=devices))
        view._populate()
        fault, stops = [True], []
        def stop():
            stops.append('attempt')
            if fault[0]:
                raise RuntimeError('controlled sound stop failure')
        view._SixthSense__sounds['sound'] = module(stop=stop)
        self.assertRaises(RuntimeError, view._dispose)
        self.assertIsNone(component.g_view)
        self.assertFalse(view.iconReady)
        self.assertTrue(view.ready)
        self.assertEqual(len(view._SixthSense__sounds), 1)
        self.assertIn(view._onRoundFinished, events.onRoundFinished.handlers)
        self.assertIn(view._onVehicleStateUpdated, vehicle.onVehicleStateUpdated.handlers)
        fault[0] = False
        view._dispose()
        self.assertEqual(stops, ['attempt', 'attempt'])
        self.assertEqual(view._SixthSense__sounds, {})
        self.assertEqual(events.onRoundFinished.handlers, [])
        self.assertEqual(events.onObservedByEnemy.handlers, [])
        self.assertEqual(vehicle.onVehicleStateUpdated.handlers, [])
        self.assertEqual(devices.onDescriptorDevicesChanged.handlers, [])
        self.assertFalse(view.ready)
