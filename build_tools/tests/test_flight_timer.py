import ast
import sys
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'source/scripts/client'))
from Driftkings._constants import FLIGHT_TIMER, GLOBAL

class FlightTimerTests(unittest.TestCase):
    def test_marker_state_and_legacy_vector_produce_same_time(self):
        path=Path(__file__).resolve().parents[2]/'source/scripts/client/Driftkings/views/battle/flight_timer.py'
        tree=ast.parse(path.read_text(encoding='utf-8'))
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='FlightTime')
        method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__onGunMarkerStateChanged')
        tree.body=[method]
        speed=NS(flatDistTo=lambda zero:100.0)
        ns={'getPlayer':lambda:NS(gunRotator=NS(getCurShotPosition=lambda:(object(),speed))),
            'VectorConstant':NS(Vector3Zero=object()), 'FLIGHT_TIMER':FLIGHT_TIMER}
        exec(compile(tree,'FlightTimer.py','exec'),ns)
        view=NS(macrosDict={},as_flightTimeS=Mock(),isFlightTimeEnabled=lambda:True,
                getSettings=lambda:{'template':'%(flightTime).1f'})
        position=NS(flatDistTo=lambda origin:500.0)
        handler=ns['__onGunMarkerStateChanged']
        for marker in (position,NS(position=position)):
            handler(view,None,marker)
            self.assertEqual(view.macrosDict['flightTime'],5.0)
            view.as_flightTimeS.assert_called_with('5.0')
        handler(view,None,NS(position=None))
        view.as_flightTimeS.assert_called_with('')

    def test_disabled_and_spg_only_keep_settings_but_do_not_calculate_time(self):
        path = Path(__file__).resolve().parents[2]/'source/scripts/client/Driftkings/views/battle/flight_timer.py'
        tree = ast.parse(path.read_text(encoding='utf-8'))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'FlightTime')
        tree.body = [n for n in cls.body if isinstance(n, ast.FunctionDef) and
                     n.name in ('isFlightTimeEnabled', '__onGunMarkerStateChanged')]
        player = Mock(side_effect=AssertionError('Disabled timer accessed gun rotator'))
        namespace = {'getPlayer': player, 'FLIGHT_TIMER':FLIGHT_TIMER, 'GLOBAL':GLOBAL}
        exec(compile(tree, str(path), 'exec'), namespace)
        view = NS(settings={'enabled':False, 'spgOnly':False}, isSPG=lambda:False, as_flightTimeS=Mock())
        view.getSettings = lambda: view.settings
        view.isFlightTimeEnabled = lambda: namespace['isFlightTimeEnabled'](view)
        for enabled, spg_only in ((False,False), (True,True)):
            view.settings.update(enabled=enabled, spgOnly=spg_only)
            namespace['__onGunMarkerStateChanged'](view, None, object())
            view.as_flightTimeS.assert_called_with('')
        player.assert_not_called()
        view.isSPG = lambda: True
        self.assertTrue(view.isFlightTimeEnabled())
        view.settings.update(enabled=False)
        self.assertFalse(view.isFlightTimeEnabled())
