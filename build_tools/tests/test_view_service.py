import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch
import unittest

ROOT = Path(__file__).resolve().parents[2]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


views = load('test_views', 'source/scripts/client/Driftkings/views/__init__.py')


class ViewServiceTests(unittest.TestCase):
    def test_service_publishes_once_and_rejects_duplicate_alias(self):
        registration, visibility = Mock(), Mock()
        service = views.BattleViews(registration, visibility)
        config = NS(data={'enabled': True})
        service.register('HUD', object, config)
        with self.assertRaises(ValueError):
            service.register('HUD', object, config)
        service.start(); service.start()
        registration.install.assert_called_once_with({'HUD': (object, config)})
        visibility.start.assert_called_once_with()
        service.stop(); service.stop()
        registration.uninstall.assert_called_once_with()
        visibility.stop.assert_called_once_with()

    def test_registration_uses_native_packages_and_preserves_other_mods(self):
        packages = {1: ['native'], 3: ['extension']}
        libraries = ['native.swf']
        patches = {
            'constants': NS(ARENA_GUI_TYPE=NS(RANGE=(1, 2))),
            'gui.override_scaleform_views_manager': NS(g_overrideScaleFormViewsConfig=NS(battlePackages=packages)),
            'gui.Scaleform.required_libraries_config': NS(BATTLE_REQUIRED_LIBRARIES=libraries),
        }
        owner = views.BattlePackageRegistration()
        with patch.dict('sys.modules', patches):
            owner.install({'HUD': (object, NS(data={}))})
            owner.install({'HUD': (object, NS(data={}))})
            self.assertEqual(libraries, ['native.swf', owner.SWF])
            self.assertTrue(all(value.count(owner.PACKAGE) == 1 for value in packages.values()))
            owner.uninstall()
            self.assertEqual(packages, {1: ['native'], 2: [], 3: ['extension']})
            self.assertEqual(libraries, ['native.swf'])
            self.assertFalse(views.BATTLE_COMPONENTS)


class NativeHandlerTests(unittest.TestCase):
    def setUp(self):
        self.pending = {}
        self.token = 0
        self.world = NS(callback=self.schedule, cancelCallback=lambda token: self.pending.pop(token))
        self.pages = {}
        owner = self
        class PackageBusinessHandler(object):
            def __init__(self, listeners, appNS=None, scope=None):
                self.listeners, self.appNS, self.scope = listeners, appNS, scope
            def init(self): pass
            def fini(self): self.listeners = ()
            def findViewByAlias(self, layer, alias): return owner.pages.get(alias)
        self.patches = {
            'BigWorld': self.world,
            'frameworks.wulf': NS(WindowLayer=NS(VIEW=1)),
            'gui.app_loader.settings': NS(APP_NAME_SPACE=NS(SF_BATTLE='battle')),
            'gui.Scaleform.daapi.settings.views': NS(
                VIEW_ALIAS=NS(BATTLE_PAGES=('classic',), COMP7_BATTLE_PAGE='comp7', COMP7_LIGHT_BATTLE_PAGE='comp7light'),
                VIEW_BATTLE_PAGE_ALIAS_BY_ARENA_GUI_TYPE={1: 'classic', 2: 'frontline', 3: 'whiteTiger'}),
            'gui.Scaleform.framework.package_layout': NS(PackageBusinessHandler=PackageBusinessHandler),
            'gui.shared': NS(EVENT_BUS_SCOPE=NS(BATTLE='battle')),
            'Driftkings.views': views,
        }
        self.patch = patch.dict('sys.modules', self.patches)
        self.patch.start(); self.addCleanup(self.patch.stop)
        views.BATTLE_COMPONENTS.clear()
        views.BATTLE_COMPONENTS.update({'HUD': (object, NS(data={'enabled': True})),
                                       'Disabled': (object, NS(data={'enabled': False}))})
        self.addCleanup(views.BATTLE_COMPONENTS.clear)
        self.module = load('test_native_handler', 'source/scripts/client/Driftkings/views/battle/handler.py')
        self.handler = self.module.BattleViewHandler()
        self.handler.init()
        self.addCleanup(self.handler.fini)

    def schedule(self, delay, callback):
        self.token += 1
        self.pending[self.token] = (delay, callback)
        return self.token

    def run_next(self):
        token = min(self.pending)
        delay, callback = self.pending.pop(token)
        callback()
        return delay

    def make_page(self):
        registered = set()
        return NS(_isDAAPIInited=lambda: True, registered=registered,
                  isFlashComponentRegistered=registered.__contains__,
                  flashObject=NS(as_DriftkingsCreate=Mock(side_effect=registered.update)))

    def test_page_event_waits_then_creates_enabled_components_once(self):
        self.handler.onPageLoading(NS(alias='classic'))
        self.assertEqual(self.run_next(), 0)
        page = self.pages['classic'] = self.make_page()
        self.assertEqual(self.run_next(), 0.1)
        page.flashObject.as_DriftkingsCreate.assert_called_once_with(['HUD'])
        self.assertFalse(self.pending)
        self.handler.onPageLoading(NS(alias='classic'))
        self.run_next()
        self.assertEqual(page.flashObject.as_DriftkingsCreate.call_count, 1)

    def test_mode_aliases_include_native_extensions_and_onslaught(self):
        self.assertEqual(set(self.module.battlePageAliases()),
                         {'classic', 'frontline', 'whiteTiger', 'comp7', 'comp7light'})
        self.assertEqual(self.handler.scope, 'battle')
        self.assertEqual(self.handler.appNS, 'battle')

    def test_page_replacement_cancels_old_request_and_uses_requested_alias(self):
        old = self.pages['classic'] = self.make_page()
        new = self.pages['comp7'] = self.make_page()
        self.handler.onPageLoading(NS(alias='classic'))
        self.handler.onPageLoading(NS(alias='comp7'))
        self.assertEqual(len(self.pending), 1)
        self.run_next()
        old.flashObject.as_DriftkingsCreate.assert_not_called()
        new.flashObject.as_DriftkingsCreate.assert_called_once_with(['HUD'])
        replacement = self.pages['comp7'] = self.make_page()
        self.handler.onPageLoading(NS(alias='comp7'))
        self.run_next()
        replacement.flashObject.as_DriftkingsCreate.assert_called_once_with(['HUD'])

    def test_library_unavailable_stops_after_bounded_retries(self):
        self.pages['classic'] = self.make_page()
        self.pages['classic'].flashObject = NS()
        self.handler.onPageLoading(NS(alias='classic'))
        with self.assertLogs('Driftkings.Views', level='WARNING'):
            for _ in range(80): self.run_next()
        self.assertFalse(self.pending)

    def test_fini_cancels_callbacks_and_late_callbacks_do_nothing(self):
        self.handler.onPageLoading(NS(alias='classic'))
        callback = next(iter(self.pending.values()))[1]
        self.handler.fini()
        self.assertFalse(self.pending)
        self.assertNotIn(self.handler, views.BATTLE_HANDLERS)
        callback()
        self.handler.onPageLoading(NS(alias='classic'))
        self.assertFalse(self.pending)

    def test_partial_creation_retries_only_missing_aliases(self):
        page = self.make_page()
        page.flashObject.as_DriftkingsCreate.side_effect = lambda aliases: page.registered.add('HUD')
        self.assertFalse(self.handler.onViewFound(page, ['HUD', 'Roster']))
        page.flashObject.as_DriftkingsCreate.side_effect = page.registered.update
        self.assertTrue(self.handler.onViewFound(page, ['HUD', 'Roster']))
        self.assertEqual(page.flashObject.as_DriftkingsCreate.call_args.args, (['Roster'],))

    def test_loading_restores_new_hud_components(self):
        page = self.make_page()
        page._isBattleLoading = True
        page._blToggling = {'native'}
        self.assertTrue(self.handler.onViewFound(page, ['HUD']))
        self.assertEqual(page._blToggling, {'native', 'HUD'})

    def test_package_exports_native_component_descriptors(self):
        package = load('test_battle_package', 'source/scripts/client/Driftkings/views/battle/__init__.py')
        framework = NS(ComponentSettings=lambda *args: args, ScopeTemplates=NS(DEFAULT_SCOPE='default'))
        with patch.dict('sys.modules', {'gui.Scaleform.framework': framework}):
            descriptors = package.getViewSettings()
        self.assertEqual([item[0] for item in descriptors], ['Disabled', 'HUD'])
        self.assertTrue(all(item[2] == 'default' for item in descriptors))
        self.assertEqual(package.getContextMenuHandlers(), ())


if __name__ == '__main__': unittest.main()
