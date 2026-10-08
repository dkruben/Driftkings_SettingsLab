from settings_support import settings_globals
import ast
import copy
import json
import sys
import unittest
import weakref
import tempfile
from unittest.mock import patch
from pathlib import Path
from types import SimpleNamespace as NS

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/scripts/client'))
from Driftkings.core import minimap as policy

SOURCE = ROOT / 'source/scripts/client/Driftkings/battle/minimap.py'


def component_class(name, namespace):
    tree = ast.parse(SOURCE.read_text(encoding='utf-8-sig'))
    node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name)
    settings_globals(namespace, 'battle.minimap')
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), 'exec'), namespace)
    return namespace[name]


class PersonalEntriesPlugin:
    def __init__(self):
        self._PersonalEntriesPlugin__circlesVisibilityState = 0
        self._PersonalEntriesPlugin__circlesID = 42
        self.calls = []
        self._arenaVisitor = NS(getVehicleCircularAoiRadius=lambda: 777,
                                getVisibilityMaxRadius=lambda: 600,
                                getVisibilityMinRadius=lambda: 65)
    def _invoke(self, *args): self.calls.append(args)
    def _canShowDrawRangeCircle(self): return False
    def _canShowMaxViewRangeCircle(self): return True
    def _canShowMinSpottingRangeCircle(self): return True
    def _canShowViewRangeCircle(self): return True
    def _getViewRangeRadius(self): return 510
    def __addDrawRangeCircle(self): self.calls.append('native')
    def __showDirectionLine(self): self.calls.append('line')
    def __hideDirectionLine(self): self.calls.append('hide')
    def __setupYawLimit(self): self.calls.append('sector')
    def __clearYawLimit(self): self.calls.append('clear')


class Entry:
    def __init__(self): self.active = False; self.alive = True; self.spotted = False
    def getID(self): return 101
    def isAlive(self): return self.alive
    def isInAoI(self): return self.spotted
    def isEnemy(self): return True
    def isActive(self): return self.active
    def getMatrix(self): return object()
    def setActive(self, value):
        changed = self.active != value
        self.active = value
        return changed


class ArenaVehiclesPlugin:
    def __init__(self, *args, **kwargs):
        self._ArenaVehiclesPlugin__showDestroyEntries = False
        self._ArenaVehiclesPlugin__isDestroyImmediately = False
        self._entries = {7: Entry()}
        self._arenaDP = NS(getVehicleInfo=lambda id: None)
        self.calls = []
    def start(self): pass
    def stop(self): pass
    def _hideVehicle(self, entry): entry.active = False
    def _showVehicle(self, vehicleID, location): self._entries[vehicleID].spotted = True
    def _setActive(self, id, value): self.calls.append((id, value))
    def _getDisplayedName(self, info): return 'native name'
    def __setActive(self, entry, active): entry.setActive(active)
    def _setVehicleInfo(self, *args): pass
    def _getGuiPropsName(self, props): return props
    def _onVehicleHealthChanged(self, *args): pass


class MinimapTests(unittest.TestCase):
    def setUp(self):
        self.data = {}
        from Driftkings.settings.minimap_store import FILES
        for filename in FILES:
            self.data.update(json.loads((ROOT/'res/configs/Driftkings/default/minimap_plugins'/filename).read_text(encoding='utf-8')))

    def test_labels_alternative_dead_lost_utf8_and_truncation(self):
        values = {'vehicle': 'Tigre II', 'name': 'Joao123456', 'state': 'alive'}
        labels = policy.defaults()['labels']
        self.assertEqual(policy.label(labels, values), 'Tigre II')
        self.assertIn('Joao123456', policy.label(labels, values, True))
        labels['lost'] = 'Last: {{vehicle}}'
        values['state'] = 'lost'
        self.assertEqual(policy.label(labels, values, True), 'Last: Tigre II')
        self.assertEqual(policy.render('{{name%.5s}}', values), 'Joa..')
        self.assertEqual(policy.render('{{name}}', {'name': 'João'.encode()}), 'João')
        self.assertNotIn('<', policy.render('{{name}}', {'name': '<font>x</font>'}))
        labels['enabled'] = False
        self.assertEqual(policy.label(labels, values), '')

    def test_aim_catalog_assets_and_legacy_path_roundtrip(self):
        from Driftkings.settings.minimap_store import MinimapStore, split, FILES
        self.assertEqual(len(policy.ARTILLERY_AIMS), 7)
        for path in policy.ARTILLERY_AIMS:
            self.assertTrue((ROOT/'res/res'/path).read_bytes().startswith(b'\x89PNG\r\n\x1a\n'))
        with tempfile.TemporaryDirectory() as folder:
            self.data['artilleryAim']['src'] = 'gui/maps/Driftkings/Minimap/MinimapAim.png'
            for name, part in zip(FILES, split(self.data)):
                (Path(folder)/name).write_text(json.dumps(part))
            store = MinimapStore(folder)
            loaded = store.load(self.data)
            self.assertEqual(loaded['artilleryAim']['src'], policy.ARTILLERY_AIMS[0])
            for path in list(policy.ARTILLERY_AIMS) + ['gui/custom/aim.png']:
                loaded['artilleryAim']['src'] = path
                store.save(loaded)
                self.assertEqual(store.load(self.data)['artilleryAim']['src'], path)
                self.assertIn(path, policy.artillery_aim_choices(path))

    def test_validation_and_preserved_color_options(self):
        policy.validate(self.data)
        self.data['colorDrawCircle'] = '123456'
        self.data['circles']['draw']['mode'] = 'on'
        policy.validate(self.data)
        self.assertEqual(self.data['colorDrawCircle'], '123456')
        for key, value in [('zoomFactor', float('nan')), ('zoomFactorMax', 99), ('lastPositionDuration', -1)]:
            broken = copy.deepcopy(self.data); broken[key] = value
            with self.assertRaises(ValueError): policy.validate(broken)
        self.data['circles']['draw']['mode'] = 'maybe'
        with self.assertRaises(ValueError): policy.validate(self.data)

    def personal(self):
        ns = dict(plugins=NS(PersonalEntriesPlugin=PersonalEntriesPlugin), config=NS(data=self.data),
                  policy=policy, PERSONAL=weakref.WeakSet(), VIEWS=[], hexToDecimal=lambda x:int(x,16),
                  CIRCLE_TYPE=NS(DRAW_RANGE=1, MAX_VIEW_RANGE=2, MIN_SPOTTING_RANGE=4, VIEW_RANGE=8),
                  CIRCLE_STYLE=NS(COLOR=NS(DRAW_RANGE=1, MAX_VIEW_RANGE=2, MIN_SPOTTING_RANGE=3, VIEW_RANGE=4)),
                  VIEW_RANGE_CIRCLES_AS3_DESCR=NS(AS_ADD_MAX_DRAW_CIRCLE='draw',AS_ADD_MAX_VIEW_CIRCLE='max',AS_ADD_MIN_SPOTTING_CIRCLE='near',AS_ADD_DYN_CIRCLE='view'))
        return component_class('PersonalEntriesPlugin', ns)

    def test_artillery_aim_defaults_and_validation(self):
        self.assertEqual(self.data['artilleryAim'], policy.defaults()['artilleryAim'])
        policy.validate(self.data)
        for key, value in [('enabled', 'true'), ('scale', 0), ('scale', 201),
                           ('scale', float('nan')), ('alpha', -1), ('alpha', 101),
                           ('src', ''), ('src', None), ('src', 'image.jpg'),
                           ('src', 'image\n.png')]:
            broken = copy.deepcopy(self.data)
            broken['artilleryAim'][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                policy.validate(broken)
        for path in ('gui/maps/aim.png', 'img://gui/maps/aim.png'):
            self.data['artilleryAim']['src'] = path
            policy.validate(self.data)

    def test_circles_follow_mode_radii_and_do_not_duplicate(self):
        plugin = self.personal()()
        for method in ('Draw', 'MaxView', 'MinSpotting', 'View'):
            getattr(plugin, '_PersonalEntriesPlugin__add%sRangeCircle' % method)()
        self.assertEqual([call[-1] for call in plugin.calls], [777,600,65,510])
        plugin._PersonalEntriesPlugin__addDrawRangeCircle()
        self.assertEqual(len(plugin.calls),4)
        self.assertFalse(plugin._canShowDrawRangeCircle())
        self.data['circles']['draw']['mode']='on'
        self.assertTrue(plugin._canShowDrawRangeCircle())
        self.data['enabled']=False
        self.assertFalse(plugin._canShowDrawRangeCircle())
        plugin._PersonalEntriesPlugin__addDrawRangeCircle()
        self.assertEqual(plugin.calls[-1], 'native')

    def test_special_mode_super_chain_and_lines(self):
        class EventPersonal(PersonalEntriesPlugin):
            def _canShowDrawRangeCircle(self): return True
        combined = type('Combined', (self.personal(), EventPersonal), {})
        plugin = combined()
        self.assertTrue(plugin._canShowDrawRangeCircle())
        self.data['lines']['direction']='off'
        plugin._PersonalEntriesPlugin__showDirectionLine()
        self.assertEqual(plugin.calls[-1], 'hide')
        self.data['enabled']=False
        plugin._PersonalEntriesPlugin__showDirectionLine()
        self.assertEqual(plugin.calls[-1], 'line')

    def arena(self):
        cancelled=[]
        ns=dict(plugins=NS(ArenaVehiclesPlugin=ArenaVehiclesPlugin),config=NS(data=self.data),controller=NS(minimapZoom=False),
                policy=policy,VEHICLES=weakref.WeakSet(),BigWorld=NS(time=lambda:100),
                callback=lambda *args: 12,cancelCallback=cancelled.append)
        return component_class('ArenaVehiclesPlugin',ns),cancelled

    def test_last_position_expiry_respotted_and_callback_cleanup(self):
        cls,cancelled=self.arena(); plugin=cls();plugin.start();entry=plugin._entries[7]
        plugin._hideVehicle(entry)
        self.assertTrue(entry.active)
        self.assertEqual(plugin._lastPositionCallback,12)
        plugin._showVehicle(7,None)
        self.assertFalse(plugin._lastPositions)
        entry.spotted=False
        self.data['lastPositionDuration']=0
        plugin._hideVehicle(entry);plugin.updateLastPositions()
        self.assertFalse(entry.active)
        self.assertFalse(plugin._lastPositions)
        plugin._ArenaVehiclesPlugin__setActive(entry, True)
        self.assertFalse(entry.active)
        plugin._hideVehicle(entry);plugin.stop()
        self.assertIn(12,cancelled)
        self.assertFalse(plugin._lastPositions)

    def test_disabling_restores_native_last_position_state(self):
        cls,_=self.arena();plugin=cls();plugin.start();entry=plugin._entries[7]
        plugin._hideVehicle(entry);self.assertTrue(entry.active)
        self.data['enabled']=False;plugin.refreshLabels()
        self.assertFalse(entry.active)
        self.assertFalse(plugin._lastPositions)

    def test_health_events_unknown_damage_death_respawn_and_deduplication(self):
        received = []
        ns = dict(plugins=NS(ArenaVehiclesPlugin=ArenaVehiclesPlugin), config=NS(data=self.data),controller=NS(minimapZoom=False),
                  policy=policy, VEHICLES=weakref.WeakSet(), VIEWS=[NS(onVehicleData=received.append)],
                  BigWorld=NS(time=lambda:100), callback=lambda *args:12, cancelCallback=lambda *args:None)
        plugin = component_class('ArenaVehiclesPlugin', ns)()
        entry = plugin._entries[7]
        info = NS(vehicleID=7, team=2, player=NS(name='Player'), isAlive=lambda:entry.alive,
                  getDisplayedName=lambda:'Tank', vehicleType=NS(compactDescr=45, maxHealth=1000, level=8, classTag='heavyTank'))
        plugin._arenaDP = NS(getVehicleInfo=lambda id:info, getPlayerGuiProps=lambda *args:'enemy')
        self.data['labels']['enemy'] = '{{vehicle}} {{hp}}/{{maxHp}}'
        plugin.refreshLabel(7, entry)
        self.assertEqual(received[-1]['text'], 'Tank --/1000')
        self.assertEqual(received[-1]['hp'], '--')
        self.assertEqual(received[-1]['guiLabel'], 'enemy')
        plugin._onVehicleHealthChanged(7, 700, 1000)
        self.assertEqual(received[-1]['percent'],70)
        self.assertEqual(received[-1]['text'],'Tank 700/1000')
        count=len(received)
        plugin._onVehicleHealthChanged(7,700,1000)
        self.assertEqual(len(received),count)
        plugin._onVehicleHealthChanged(7,1200,1000)
        self.assertEqual(len(received),count)
        entry.alive=False; plugin.refreshLabel(7,entry)
        self.assertEqual(received[-1]['hp'],0)
        entry.alive=True; plugin.refreshLabel(7,entry)
        self.assertEqual(received[-1]['hp'],'--')
        plugin._onVehicleHealthChanged(7,900,1000)
        info.vehicleType.compactDescr=46;plugin.refreshLabel(7,entry)
        self.assertEqual(received[-1]['hp'],'--')
        entry.alive=False;plugin.refreshLabel(7,entry)
        entry.alive=True;plugin._onVehicleHealthChanged(7,1000,1000);plugin.refreshLabel(7,entry)
        self.assertEqual(received[-1]['hp'],1000)

    def test_lost_marker_countdown_does_not_prevent_expiry(self):
        cls,_=self.arena();plugin=cls();plugin.start();entry=plugin._entries[7]
        self.data['lostMarker'].update(showSeconds=True,fade=True)
        self.data['lastPositionDuration']=0
        plugin._hideVehicle(entry);plugin.updateLastPositions()
        self.assertFalse(entry.active)
        self.assertFalse(plugin._lastPositions)

    def test_group_formats_and_health_macro_unknowns(self):
        labels=self.data['labels'];labels['squad']='Squad {{name}} {{hpPercent}}%'
        values=dict(name='Friend',vehicle='Tank',group='squad',state='alive',**policy.health_values(500,1000))
        self.assertEqual(policy.label(labels,values),'Squad Friend 50%')
        labels['alternativeSquad']='{{vehicle}} {{hp}}'
        self.assertEqual(policy.label(labels,values,True),'Tank 500')
        self.assertEqual(policy.health_values(None,1000)['hp'],'--')

    def test_split_settings_migration_roundtrip_and_rollback(self):
        from Driftkings.settings.loader import SettingsLoader
        from Driftkings.settings.settings_data import defaults
        from Driftkings.settings.store import SettingsStore
        from Driftkings.settings.minimap_store import FILES
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'default').mkdir()
            old=(ROOT/'build_tools/tests/fixtures/minimap_plugins_legacy.json').read_bytes()
            legacy=root/'default/minimap_plugins.json';legacy.write_bytes(old)
            loader=SettingsLoader(temporary)
            data=loader.load('MinimapPlugins',defaults('MinimapPlugins'))
            folder=root/'default/minimap_plugins'
            self.assertTrue(all((folder/name).is_file() for name in FILES))
            self.assertEqual(legacy.read_bytes(),old)
            data['health']['visibility']='key';loader.save('MinimapPlugins',data)
            self.assertEqual(loader.load('MinimapPlugins',defaults('MinimapPlugins'))['health']['visibility'],'key')
            before={name:(folder/name).read_bytes() for name in FILES}
            original=SettingsStore.write;failed=[]
            def fail_once(store,value):
                if store.path.endswith('minimap_lines.json') and not failed:
                    failed.append(True);raise IOError('simulated publication failure')
                return original(store,value)
            data['health']['visibility']='always'
            with patch.object(SettingsStore,'write',fail_once),self.assertRaises(IOError):
                loader.save('MinimapPlugins',data)
            self.assertEqual({name:(folder/name).read_bytes() for name in FILES},before)
            loader.clone('test_copy')
            self.assertTrue((root/'test_copy/minimap_plugins/minimap_labels.json').is_file())

    def test_extended_validation(self):
        for section,key,value in [('health','visibility','sometimes'),('icons','scale',0),
                                  ('mapSize','fontSize',100),('labels','align','up'),('lines','gap',0)]:
            broken=copy.deepcopy(self.data);broken[section][key]=value
            with self.assertRaises(ValueError):policy.validate(broken)
        self.data['extraCircles']=[dict(radius=100,color='FFFFFF',alpha=70,thickness=1,dash=0,gap=5,vehicleClass='SPG')]
        policy.validate(self.data)
        self.data['extraCircles'][0]['radius']=float('nan')
        with self.assertRaises(ValueError):policy.validate(self.data)

    def test_range_events_preserve_native_invocation_and_track_dynamic_radius(self):
        plugin=self.personal()()
        plugin._invoke(42,'as_initArenaSize',1200,800)
        plugin._invoke(42,'as_addDynamicViewRange',0xABCDEF,80,420)
        plugin._invoke(42,'as_updateDynRange',460)
        self.assertEqual(plugin._ranges['width'],1200)
        self.assertEqual(plugin._ranges['circles']['view'],dict(color=0xABCDEF,alpha=80,radius=460))
        self.assertEqual(plugin.calls[-1],(42,'as_updateDynRange',460))
        plugin._invoke(42,'as_delDynRange')
        self.assertFalse(plugin._ranges['circles'])


if __name__ == '__main__': unittest.main()
