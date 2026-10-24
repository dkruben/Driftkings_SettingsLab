# -*- coding: utf-8 -*-
"""Flash rendering for aiming angles; coordinates are supplied by the controller."""
from account_helpers.settings_core import settings_constants
from gui.shared.personality import ServicesLocator

from driftkings._constants import GLOBAL, GUN_TRAVERSE_LIMITS
from driftkings.core.overlay import Align, ElementType, overlays
from driftkings.settings.service import settings_service


class AimingAnglesView(object):
    def __init__(self, config):
        self.config = config
        self._uiCreated = False

    def createUI(self):
        if self._uiCreated:
            return
        overlays.create(self.config.NAME, ElementType.PANEL, {'x': 0, 'y': 0, 'alignX': Align.CENTER, 'alignY': Align.CENTER, 'width': 0, 'height': 0, 'limit': False})
        overlays.create(self.config.NAME + '.L', ElementType.IMAGE, {'alignX': Align.CENTER, 'alignY': Align.CENTER, 'limit': False})
        overlays.create(self.config.NAME + '.R', ElementType.IMAGE, {'alignX': Align.CENTER, 'alignY': Align.CENTER, 'limit': False})
        overlays.create(self.config.NAME + '.lo', ElementType.IMAGE, {'x': 0, 'alignX': Align.CENTER, 'alignY': Align.CENTER, 'limit': False})
        overlays.create(self.config.NAME + '.hi', ElementType.IMAGE, {'x': 0, 'alignX': Align.CENTER, 'alignY': Align.CENTER, 'limit': False})
        self._uiCreated = True

    def updateHor(self):
        if not self._uiCreated:
            return
        rotation = 0
        if self.aimMode == 'str':
            if ServicesLocator.settingsCore.getSetting(settings_constants.SPGAim.SPG_STRATEGIC_CAM_MODE) == 0:
                rotation = self.rotation
        overlays.update(self.config.NAME, {'rotation': rotation}, {'duration': 0.05})
        settings = settings_service.getComponentDict(self.config)
        marker = settings[GUN_TRAVERSE_LIMITS.HORIZONTAL] if settings[GLOBAL.ENABLED] else 0
        if not marker:
            overlays.update(self.config.NAME + '.L', {'image': ''})
            overlays.update(self.config.NAME + '.R', {'image': ''})
            return
        y = self.aim_y()
        L = self.anglesAiming_left()
        R = self.anglesAiming_right()
        overlays.update(self.config.NAME + '.L', {'x': L, 'y': y, 'image': '../aimingangles/%s/left%s.png' % (marker, ('_limit' if L > -5 else ''))}, {'duration': 0.05})
        overlays.update(self.config.NAME + '.R', {'x': R, 'y': y, 'image': '../aimingangles/%s/right%s.png' % (marker, ('_limit' if R < 5 else ''))}, {'duration': 0.05})

    def ON_ANGLES_AIMING(self):
        if not self._uiCreated:
            return
        self.updateHor()
        settings = settings_service.getComponentDict(self.config)
        marker = settings[GUN_TRAVERSE_LIMITS.VERTICAL] if settings[GLOBAL.ENABLED] else 0
        if not marker:
            overlays.update(self.config.NAME + '.lo', {'image': ''})
            overlays.update(self.config.NAME + '.hi', {'image': ''})
            return
        lo = self.anglesAiming_bottom(12)
        hi = self.anglesAiming_top(-12)
        overlays.update(self.config.NAME + '.lo', {
            'y': lo, 'alpha': max(350 - lo, 0) / 100.0, 'image': '../aimingangles/%s/bottom%s.png' % (
                marker, ('_limit' if not int(lo - self.yVert - 12) else ''))}, {'duration': 0.05})
        overlays.update(self.config.NAME + '.hi', {
            'y': hi, 'alpha': max(350 + hi, 0) / 100.0, 'image': '../aimingangles/%s/top%s.png' % (
                marker, ('_limit' if not int(hi - self.yVert + 12) else ''))}, {'duration': 0.05})

    def destroyUI(self):
        if not self._uiCreated:
            return
        self._uiCreated = False
        for suffix in ('.L', '.R', '.lo', '.hi', ''):
            overlays.remove(self.config.NAME + suffix)
