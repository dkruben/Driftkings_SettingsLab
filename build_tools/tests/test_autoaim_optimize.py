from settings_support import settings_globals
import ast
import math
import sys
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/scripts/client'))


class Vector:
    def __init__(self, x=0, y=0, z=0):
        self.x, self.y, self.z = x, y, z

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, value):
        return Vector(self.x * value, self.y * value, self.z * value)

    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z

    @property
    def lengthSquared(self):
        return self.dot(self)

    def normalise(self):
        size = math.sqrt(self.lengthSquared)
        self.x, self.y, self.z = self.x / size, self.y / size, self.z / size


class Vehicles(dict):
    def iteritems(self):
        return iter(self.items())


class Settings:
    def __init__(self):
        self.data = dict(enabled=True, angle=1.3, catchHiddenTarget=True, disableArtyMode=True)


class AutoAimTests(unittest.TestCase):
    def setUp(self):
        self.entities = {}
        self.camera = Mock(getWorldRayAndPoint=lambda *args:(Vector(0, 0, 1), Vector(0, 2, 0)))
        self.world = Mock()
        self.world.wg_collideSegment.return_value = None
        self.strategic = type('Strategic', (), {})
        self.arty = type('Arty', (), {})
        self.ns = dict(math=math, BigWorld=self.world, cameras=self.camera, Settings=Settings,
                       Math=NS(Matrix=lambda position:NS(applyPoint=lambda point:position + point)),
                       getEntity=self.entities.get, StrategicControlMode=self.strategic, ArtyControlMode=self.arty,
                       CommandMapping=NS(CMD_CM_LOCK_TARGET='lock', CMD_CM_LOCK_TARGET_OFF='off',
                                         g_instance=NS(isFired=lambda command, key:command == key)),
                       ServicesLocator=NS(appLoader=NS(getDefBattleApp=lambda:object())))
        path = ROOT / 'source/scripts/client/Driftkings/battle/auto_aim.py'
        tree = ast.parse(path.read_text(encoding='utf-8'))
        nodes = [node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))]
        for node in nodes:
            node.decorator_list = []
        settings_globals(self.ns, 'battle.auto_aim')
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), self.ns)
        self.config = Settings()
        self.controller = self.ns['AutoAimController'](self.config)
        self.ns['controller'] = self.controller
        self.own = NS(position=Vector(), isAlive=lambda:True)
        self.player = NS(team=1, spaceID=1, isObserver=lambda:False, arena=NS(vehicles=Vehicles()),
                         getVehicleAttached=lambda:self.own, _PlayerAvatar__autoAimVehID=0)
        def native(player, target=None, magnetic=False):
            player._PlayerAvatar__autoAimVehID = 0 if target is None or target.id == player._PlayerAvatar__autoAimVehID else target.id
        self.native = Mock(side_effect=native)
        self.player.autoAim = lambda target=None, magnetic=False:self.ns['new_autoAim'](self.native, self.player, target, magnetic)
        self.world.player.return_value = self.player
        self.world.target.return_value = None

    def tank(self, ident, x=0, z=30, team=2):
        position = Vector(x, 0, z)
        vehicle = NS(id=ident, position=position, matrix=position, isStarted=True, isAlive=lambda:True,
                     typeDescriptor=NS(chassis=NS(hullPosition=Vector()),
                                       hull=NS(hitTester=NS(bbox=(Vector(-1, 1, -2), Vector(1, 3, 2), None)))))
        self.entities[ident] = vehicle
        self.player.arena.vehicles[ident] = dict(team=team, isAlive=True)
        return vehicle

    def press(self, target=None, mode=None):
        def key_handler(*args, **kwargs):
            self.player.autoAim(target)
            return 'native controls preserved'
        return self.controller.handleKey(key_handler, mode or object(), True, 'lock', 0)

    def test_runtime_lock_state_does_not_enter_settings(self):
        before = dict(self.config.data)
        self.tank(1)
        self.press()
        self.assertEqual(self.config.data, before)
        self.assertFalse(hasattr(self.config, 'optimizedTargetID'))
        self.assertIs(self.controller.config, self.config)

    def test_locks_hull_in_cone_even_when_tracks_are_outside(self):
        target = self.tank(1)
        self.assertEqual(self.press(), 'native controls preserved')
        self.assertEqual(self.player._PlayerAvatar__autoAimVehID, target.id)
        self.assertFalse(self.controller.lockRequest)
        self.native.assert_called_once_with(self.player, target, False)

    def test_closest_to_crosshair_wins_even_when_further_away(self):
        self.tank(1, x=.5, z=30)
        target = self.tank(2, x=.1, z=60)
        self.assertIs(self.controller.findTarget(self.player), target)

    def test_visible_candidate_is_considered_after_blocked_best_candidate(self):
        self.tank(1, z=30)
        target = self.tank(2, x=.1, z=60)
        self.config.data['catchHiddenTarget'] = False
        self.world.wg_collideSegment.side_effect = lambda space, start, end, mask: object() if end.z == 30 else None
        self.assertIs(self.controller.findTarget(self.player), target)

    def test_angle_changes_apply_in_current_battle(self):
        target = self.tank(1, x=1, z=30)
        self.assertIsNone(self.controller.findTarget(self.player))
        self.config.ID = 'AutoAimOptimize'
        self.ns['settings_service'].apply(self.config, {'angle': 3}, persist=False)
        self.assertIs(self.controller.findTarget(self.player), target)

    def test_allies_dead_missing_unstarted_and_behind_are_ignored(self):
        self.tank(1, team=1)
        self.tank(2).isAlive = lambda:False
        self.tank(3).isStarted = False
        self.tank(4, z=-30)
        self.tank(5)
        del self.entities[5]
        self.assertIsNone(self.controller.findTarget(self.player))

    def test_no_target_and_direct_target_and_unlock_keep_native_behavior(self):
        self.press()
        self.assertEqual(self.player._PlayerAvatar__autoAimVehID, 0)
        target = self.tank(1, x=20)
        self.press(target)
        self.assertEqual(self.player._PlayerAvatar__autoAimVehID, 1)
        self.press()
        self.assertEqual(self.player._PlayerAvatar__autoAimVehID, 0)

    def test_unrelated_autoaim_calls_do_not_acquire_targets(self):
        self.tank(1)
        self.player.autoAim(None)
        self.assertEqual(self.player._PlayerAvatar__autoAimVehID, 0)

    def test_magnetic_key_release_does_not_cancel_optimized_lock(self):
        target = self.tank(1)
        self.press()
        self.controller.handleKey(lambda *args:self.player.autoAim(target, magnetic=True), object(), False, 'lock', 0)
        self.assertEqual(self.player._PlayerAvatar__autoAimVehID, 1)
        self.native.assert_called_once_with(self.player, target, False)
        self.assertIsNone(self.controller.optimizedTargetID)

    def test_disabled_and_arty_modes_leave_control_to_game(self):
        self.tank(1)
        self.config.data['enabled'] = False
        self.press()
        self.assertEqual(self.player._PlayerAvatar__autoAimVehID, 0)
        self.config.data['enabled'] = True
        self.press(mode=self.strategic())
        self.assertEqual(self.player._PlayerAvatar__autoAimVehID, 0)
        self.config.data['disableArtyMode'] = False
        self.controller.handleKey(lambda *args:False, self.arty(), True, 'lock', 0)
        self.assertEqual(self.player._PlayerAvatar__autoAimVehID, 1)

    def test_dead_player_and_observer_do_not_acquire(self):
        self.tank(1)
        self.own.isAlive = lambda:False
        self.assertIsNone(self.controller.findTarget(self.player))
        self.own.isAlive = lambda:True
        self.player.isObserver = lambda:True
        self.assertIsNone(self.controller.findTarget(self.player))

    def test_native_rejection_and_consumed_key_are_respected(self):
        self.tank(1)
        self.native.side_effect = None  # Client disallows auto-aim in this mode.
        self.press()
        self.assertEqual(self.player._PlayerAvatar__autoAimVehID, 0)
        self.assertIsNone(self.controller.optimizedTargetID)
        self.config.data['disableArtyMode'] = False
        self.native.reset_mock()
        self.controller.handleKey(lambda *args:True, self.arty(), True, 'lock', 0)
        self.native.assert_not_called()

    def test_exception_in_native_handler_does_not_leave_lock_request_enabled(self):
        with self.assertRaises(RuntimeError):
            self.controller.handleKey(Mock(side_effect=RuntimeError), object(), True, 'lock', 0)
        self.assertFalse(self.controller.lockRequest)
