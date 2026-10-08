from settings_support import settings_globals
"""Window lifecycle contract: Wulf position is a read-only property."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
import weakref
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]


class NativeWindow:
    def __init__(self, flags, **kwargs):
        self.native_position = (0, 0)
        self.move = Mock(side_effect=self._move)
        self.center = Mock()
        self.native_finalized = False

    @property
    def position(self):
        return self.native_position

    def _move(self, x, y):
        self.native_position = (x, y)

    def _onReady(self):
        pass

    def _finalize(self):
        self.native_finalized = True


def window_class():
    source = ROOT / 'source/scripts/client/Driftkings/views/hangar/account_manager.py'
    tree = ast.parse(source.read_text(encoding='utf8'))
    tree.body = [item for item in tree.body if isinstance(item, ast.ClassDef) and item.name == 'AccountsWindow']
    namespace = {'WindowImpl': NativeWindow, 'AccountsView': Mock(),
                 'WindowFlags': SimpleNamespace(WINDOW=1, WINDOW_MODAL=4096),
                 'WindowLayer': SimpleNamespace(WINDOW=7, TOP_WINDOW=10)}
    settings_globals(namespace, 'components.account_manager')
    exec(compile(tree, str(source), 'exec'), namespace)
    return namespace['AccountsWindow']


class AccountWindowTests(unittest.TestCase):
    def setUp(self):
        self.controller = SimpleNamespace(launcher=None, window=None, launcherPosition=lambda: None)
        self.Window = window_class()

    def test_constructor_preserves_native_read_only_position(self):
        window = self.Window(self.controller, launcher=True)
        self.assertEqual(window.position, (0, 0))
        window.move.assert_not_called()

    def test_early_layout_is_applied_on_ready_and_later_layout_moves_window(self):
        window = self.Window(self.controller, launcher=True)
        window.place(1052, 790)
        window.move.assert_not_called()
        window._onReady()
        self.assertEqual(window.position, (1052, 790))
        window.place(900, 600)
        self.assertEqual(window.position, (900, 600))
        window.center.assert_not_called()

    def test_main_window_centers_and_late_layout_does_not_move_disposed_window(self):
        window = self.Window(self.controller)
        self.controller.window = window
        window.place()
        window.center.assert_not_called()
        window._onReady()
        window.center.assert_called_once_with()
        window._finalize()
        self.assertIsNone(self.controller.window)
        self.assertTrue(window.native_finalized)
        window.place()
        window.center.assert_called_once_with()

    def test_old_launcher_disposal_preserves_replacement(self):
        old = self.Window(self.controller, launcher=True)
        replacement = self.Window(self.controller, launcher=True)
        self.controller.launcher = replacement
        old._finalize()
        self.assertIs(self.controller.launcher, replacement)

    def test_native_form_anchor_overrides_estimated_frontend_coordinates(self):
        self.controller.launcherPosition = lambda: (987, 612)
        window = self.Window(self.controller, launcher=True)
        window.place(1052, 798)
        window._onReady()
        self.assertEqual(window.position, (987, 612))


class LoginOnlyTests(unittest.TestCase):
    def setUp(self):
        source = ROOT / 'source/scripts/client/Driftkings/components/account_manager.py'
        tree = ast.parse(source.read_text(encoding='utf8'))
        tree.body = [item for item in tree.body if (isinstance(item, ast.ClassDef) and item.name == 'AccountsManagerController')
                     or (isinstance(item, ast.FunctionDef) and item.name in ('onContextEntered', 'onContextLeft'))]
        self.ns = {'weakref': weakref, 'LoginView': object, 'override': Mock(), 'callback': Mock(return_value=123),
                   'cancelCallback': Mock(), 'config': SimpleNamespace(data={'enabled': True}),
                   'GuiGlobalSpaceID': SimpleNamespace(LOGIN=2, LOBBY=3)}
        settings_globals(self.ns, 'components.account_manager')
        exec(compile(tree, str(source), 'exec'), self.ns)
        self.controller = self.ns['AccountsManagerController']()
        self.ns['controller'] = self.controller
        self.controller.active = True
        self.login = SimpleNamespace()

    def test_hangar_blocks_launcher_and_open_even_with_login_reference(self):
        self.controller.login = lambda: self.login
        self.controller.space = 3
        self.controller.scheduleLauncher()
        self.ns['callback'].assert_not_called()
        self.controller.showLauncher()
        self.controller.open()
        self.assertIsNone(self.controller.launcher)
        self.assertIsNone(self.controller.window)

    def test_leaving_login_closes_views_and_cancels_pending_creation(self):
        self.controller.login = lambda: self.login
        self.ns['onContextEntered'](2)
        self.ns['callback'].assert_called_once()
        launcher, window = Mock(), Mock()
        self.controller.launcher, self.controller.window = launcher, window
        self.ns['onContextEntered'](3)
        launcher.destroy.assert_called_once()
        window.destroy.assert_called_once()
        self.ns['cancelCallback'].assert_called_once_with(123)
        self.assertFalse(self.controller.canLogin())

    def test_anchor_tracks_native_keyboard_and_submit_positions(self):
        form = SimpleNamespace(parent=SimpleNamespace(x=960, y=700),
                               keyboardLang=SimpleNamespace(x=88), submit=SimpleNamespace(x=-75, y=98, width=150))
        self.login.flashObject = SimpleNamespace(loginViewStack=SimpleNamespace(currentView=form))
        self.controller.login = lambda: self.login
        self.controller.space = 2
        self.assertEqual(self.controller.launcherPosition(), (1048, 798))
        form.parent.x, form.parent.y, form.submit.y = 1280, 848, 78
        self.assertEqual(self.controller.launcherPosition(), (1368, 926))
        del form.keyboardLang
        self.assertEqual(self.controller.launcherPosition(), (1367, 926))
        self.login.flashObject.loginViewStack.currentView = None
        self.assertIsNone(self.controller.launcherPosition())


if __name__ == '__main__':
    unittest.main()
