# -*- coding: utf-8 -*-
"""Penetration indicator: armour numbers along the shot; the marker colour comes from the client."""
from support import RuntimeTest, Settings, game_source, module, stub


def plate(name, armor, dist=0.0, damage=0.0, once=False, kind=1, cos=1.0):
    return module(compName=name, dist=dist, hitAngleCos=cos,
                  matInfo=module(armor=armor, kind=kind, useHitAngle=True, vehicleDamageFactor=damage, collideOnceOnly=once))


def shell(kind='ARMOR_PIERCING', mechanics='LEGACY', loss=0.0, shield=False, caliber=100):
    return module(kind=kind, caliber=caliber,
                  type=module(mechanics=mechanics, piercingPowerLossFactorByDistance=loss, shieldPenetration=shield))


class NativePlugin(object):
    """Client ShotResultIndicatorPlugin: colours come from its resolver and the player's team."""
    def __init__(self, parentObj):
        self._parentObj = parentObj
        self._ShotResultIndicatorPlugin__isEnabled = True
        self._ShotResultIndicatorPlugin__playerTeam = 1
        self._ShotResultIndicatorPlugin__piercingMultiplier = 1.5
        self._ShotResultIndicatorPlugin__colors = {'pierced': 'green', 'not': 'red'}
        self._ShotResultIndicatorPlugin__cache = {'arcade': None}
        self.requests = []
        test = self

        class Resolver(object):
            @staticmethod
            def getShotResult(marker, team, multiplier):
                test.requests.append((team, multiplier))
                return marker.result
        self._ShotResultIndicatorPlugin__shotResultResolver = Resolver

    def _getShotResult(self, gunMarkerState, supportMarkersInfo):
        return self._getShotResolverResult(gunMarkerState)

    def start(self):
        pass


class PenetrationIndicatorTests(RuntimeTest):
    def setUp(self):
        super(PenetrationIndicatorTests, self).setUp()
        self.data = {'enabled': True, 'displayOnAllies': False}
        self.colors, self.armor = [], []
        deps = {
            'driftkings.settings.service': Settings(self.data).service(),
            'driftkings.game_constants': module(SHELL_TYPES=module(HIGH_EXPLOSIVE='HIGH_EXPLOSIVE'),
                                                SHELL_MECHANICS_TYPE=module(MODERN='MODERN')),
            'gui.Scaleform.daapi.view.battle.shared.crosshair': module(plugins=stub('plugins', ShotResultIndicatorPlugin=NativePlugin)),
            'driftkings.ui': module(g_events=module(onMarkerColorChanged=self.colors.append, onArmorChanged=self.armor.append)),
        }
        self.api, _ = game_source('battle/penetration_indicator.py', deps, real=('driftkings._constants',))
        bridge, self.hooks = game_source('flash/batalha/penetration_hooks.py', deps, real=('driftkings._constants',))
        bridge['configure'](self.api['config'], self.api['_ShotResult'], self.api['_ShotResultAll'])
        self.api['ShotResultIndicatorPlugin'] = bridge['ShotResultIndicatorPlugin']
        self.shot = self.api['_ShotResult']
        # Native helpers of _CrosshairShotResults, reduced to their armour inputs.
        self.shot._computePenetrationArmor = classmethod(lambda cls, shell, cos, mat: mat.armor / cos)
        self.shot._shouldRicochet = classmethod(lambda cls, shell, cos, mat: cos < 0.3)
        self.shot._SHELL_EXTRA_DATA = {'ARMOR_PIERCING': module(hasPenetrationLoss=False),
                                       'HOLLOW_CHARGE': module(hasPenetrationLoss=True)}

    def test_spaced_and_main_armour_add_up_until_the_damaging_plate(self):
        data = self.shot._computeArmorDefault(
            [plate('screen', 20), plate('hull', 100, damage=1.0), plate('behind', 500, damage=1.0)], shell(), 200.0, None)
        self.assertEqual(data, (120, 200, 100, False, False))
        # Only non-damaging plates: no damage.
        self.assertTrue(self.shot._computeArmorDefault([plate('screen', 20)], shell(), 200.0, None)[4])

    def test_ricochet_and_once_only_materials(self):
        data = self.shot._computeArmorDefault([plate('hull', 100, damage=1.0, cos=0.2)], shell(), 200.0, None)
        self.assertTrue(data[3])
        data = self.shot._computeArmorDefault(
            [plate('track', 20, once=True), plate('track', 20, once=True), plate('hull', 50, damage=1.0)], shell(), 200.0, None)
        self.assertEqual(data[0], 70)

    def test_heat_jet_loses_power_after_the_first_plate(self):
        heat = shell(kind='HOLLOW_CHARGE', loss=0.5)
        data = self.shot._computeArmorDefault([plate('screen', 20, dist=1.0), plate('hull', 100, dist=1.52, damage=1.0)], heat, 300.0, None)
        # The jet starts 0.02 m behind the screen (armour * 0.001) and travels 0.5 m.
        self.assertEqual(data[:2], (120, 225))

    def test_modern_he_loses_power_on_shields(self):
        he = shell(kind='HIGH_EXPLOSIVE', mechanics='MODERN', shield=True)
        self.assertTrue(self.shot._isModernMechanics(he))
        self.assertEqual(self.shot._computeArmorModernHE([plate('screen', 10), plate('hull', 40, damage=1.0)], he, 100.0, None),
                         (50, 70, 100, False, False))
        # Each shield costs three times its own armour, not the running total.
        data = self.shot._computeArmorModernHE([plate('a', 10, kind=1), plate('b', 10, kind=2), plate('hull', 5, damage=1.0)], he, 100.0, None)
        self.assertEqual(data[:2], (25, 40))

    def plugin(self):
        parent = module(setGunMarkerColor=lambda markerType, color: True)
        plugin = self.api['ShotResultIndicatorPlugin'](parent)
        resolver = plugin._ShotResultIndicatorPlugin__resolver
        resolver._getShotResult = classmethod(lambda cls, marker, multiplier, player: (80, 120, 100, False, False))
        return plugin

    def test_marker_colour_comes_from_the_client_resolver(self):
        plugin = self.plugin()
        plugin._ShotResultIndicatorPlugin__onGunMarkerStateChanged('arcade', module(result='pierced'), None)
        # The player's team is excluded and the gun's piercing multiplier is used, as in the client.
        self.assertEqual(plugin.requests, [(1, 1.5)])
        self.assertEqual((self.colors, self.armor), (['green'], [(80, 120, 100, False, False)]))
        plugin._ShotResultIndicatorPlugin__onGunMarkerStateChanged('arcade', module(result='not'), None)
        self.assertEqual(self.colors, ['green', 'red'])

    def test_allies_are_resolved_when_the_option_is_on(self):
        self.data['displayOnAllies'] = True
        plugin = self.plugin()
        plugin._ShotResultIndicatorPlugin__onGunMarkerStateChanged('arcade', module(result='pierced'), None)
        self.assertEqual(plugin.requests, [(0, 1.5)])

    def test_indicator_plugin_is_installed_only_when_enabled(self):
        create = self.hooks.get('plugins', 'createPlugins')
        self.assertIn('shotResultIndicator', create(lambda *args: {}))
        self.data['enabled'] = False
        self.assertNotIn('shotResultIndicator', create(lambda *args: {}))
