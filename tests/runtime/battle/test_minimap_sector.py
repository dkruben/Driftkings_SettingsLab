# -*- coding: utf-8 -*-
"""Minimap gun-arc sector: Python yaw limits and the geometry of the Flash overlay.

The Flash part cannot run outside the game, so it is checked as a model of the exact maths in
``minimaplines.as`` plus the native ``ViewPointMinimapEntry`` convention (read from the bundled
SWC bytecode): ``sectorLeft/Right.rotation = yawLimit - 180`` while the camera line is drawn
toward local -y. Final visual acceptance still needs the client.
"""
import math
import os
import re
import unittest

from support.minimap import MinimapFixture

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
LINES_AS = os.path.join(ROOT, 'flash_source', 'battle', 'src', 'driftkings', 'battle', 'components',
                        'minimap', 'minimaplines.as')
UI_AS = os.path.join(os.path.dirname(LINES_AS), 'minimapenhancementsui.as')
YAW_CORRECTION_ANGLE = 180.0


def heading(rotation_deg, art_deg):
    """Compass-style heading (degrees, 0 = up, clockwise) of art that points ``art_deg`` before rotation."""
    return (rotation_deg + art_deg) % 360.0


def overlay_rotation(placeholder_deg, rotation_offset=0.0):
    """minimaplines.as copies the native rotation and adds an offset in radians."""
    rad = math.radians(placeholder_deg)
    m_a, m_b = math.cos(rad), math.sin(rad)
    return math.degrees(math.atan2(m_b, m_a) + rotation_offset) % 360.0


class SectorGeometryTests(unittest.TestCase):
    # Local -y (up) is 0 degrees; the native sector art points down (+y), i.e. 180 degrees.
    LINE_ART = 0.0
    NATIVE_SECTOR_ART = 180.0
    OVERLAY_ART = 0.0  # mapgeometry.line() draws toward -y

    def native_sector_heading(self, yaw):
        return heading(yaw - YAW_CORRECTION_ANGLE, self.NATIVE_SECTOR_ART)

    def overlay_sector_heading(self, yaw):
        placeholder = yaw - YAW_CORRECTION_ANGLE
        return heading(overlay_rotation(placeholder, math.pi), self.OVERLAY_ART)

    def test_native_sector_points_where_the_yaw_limit_says(self):
        for yaw in (-90, -35, 0, 20, 90):
            self.assertAlmostEqual(self.native_sector_heading(yaw), yaw % 360.0)

    def test_camera_line_overlay_matches_native(self):
        for rotation in (-90, -35, 0, 20, 90, 180):
            self.assertAlmostEqual(heading(overlay_rotation(rotation), self.OVERLAY_ART),
                                   heading(rotation, self.LINE_ART))

    def test_sector_overlay_matches_native_sector(self):
        """Both sector edges compensate the native art orientation, including asymmetric limits."""
        for yaw in (-90, -35, 0, 20, 90):
            self.assertAlmostEqual(self.overlay_sector_heading(yaw), self.native_sector_heading(yaw))

    def test_flash_source_applies_rotation_offset_only_to_sector_edges(self):
        """Keep the model tied to the renderer and the camera/sector call sites."""
        with open(LINES_AS, 'rb') as handle:
            text = handle.read().decode('utf-8')
        self.assertIn('rotationOffset:Number = 0', text)
        self.assertTrue(re.search(r'angle:Number\s*=\s*Math\.atan2\(m\.b, m\.a\)\s*\+\s*rotationOffset\s*;', text))
        self.assertTrue(re.search(r'cosine:Number\s*=\s*Math\.cos\(angle\),\s*sine:Number\s*=\s*Math\.sin\(angle\)\s*;', text))
        self.assertIn('new Matrix(cosine, sine, -sine, cosine, m.tx, m.ty)', text)
        with open(UI_AS, 'rb') as handle:
            ui = handle.read().decode('utf-8')
        for edge in ('sectorLeft', 'sectorRight'):
            self.assertIn('lines.line(point.%s, options, options.lines.sectorColor, false, 100, Math.PI)' % edge, ui)
        self.assertIn('lines.line(camera.directionLinePlaceholder, options, options.lines.directionColor, true, Number(options.lines.directionAlpha))', ui)


class YawLimitsTests(unittest.TestCase):
    """_refreshYawLimits on the plugin subclass, with an asymmetric-limit vehicle."""

    def setUp(self):
        # Reuse the native-plugin stubs of the minimap battle tests without re-running its tests.
        base = MinimapFixture('setUp')
        base.setUp()
        self.addCleanup(base.doCleanups)
        base.onRanges = lambda ranges: None
        self.api, self.arena, self.info, self.data = base.api, base.arena, base.info, base.data
        self.cleared = []
        plugin = self.api['PersonalEntriesPlugin']()
        plugin._arenaDP = self.arena
        plugin._PersonalEntriesPlugin__yawLimits = None
        plugin._PersonalEntriesPlugin__clearYawLimit = lambda: self.cleared.append(True)
        self.personal = plugin
        self.info.isSPG = lambda: False
        self.info.vehicleType.iconName = 'ussr-R01_IS'
        self.info.vehicleType.shortName = 'IS'
        self.info.vehicleType.turretYawLimits = (math.radians(-20), math.radians(45))
        self.data.update(yaw=True)

    def limits(self):
        return self.personal._PersonalEntriesPlugin__yawLimits

    def test_limits_keep_order_sign_and_degrees(self):
        self.personal._refreshYawLimits()
        left, right = self.limits()
        self.assertAlmostEqual(left, -20.0)
        self.assertAlmostEqual(right, 45.0)
        self.assertEqual(len(self.cleared), 1)

    def test_unchanged_limits_do_not_clear_the_native_sector(self):
        self.personal._refreshYawLimits()
        self.personal._refreshYawLimits()
        self.assertEqual(len(self.cleared), 1)

    def test_disabled_yaw_hides_limits_except_for_spg(self):
        self.data['yaw'] = False
        self.personal._refreshYawLimits()
        self.assertIsNone(self.limits())
        self.info.isSPG = lambda: True
        self.personal._refreshYawLimits()
        self.assertEqual(len(self.limits()), 2)

    def test_vehicle_without_limits_has_none(self):
        self.info.vehicleType.turretYawLimits = None
        self.personal._refreshYawLimits()
        self.assertIsNone(self.limits())


if __name__ == '__main__':
    unittest.main()
