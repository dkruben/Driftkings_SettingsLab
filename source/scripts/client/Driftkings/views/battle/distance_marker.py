# -*- coding: utf-8 -*-
from Driftkings._constants import DISTANCE_MARKER
from Driftkings.settings.service import settings_service
"""Presentation adapter for DistanceMarker; gameplay state stays in its component."""
from Driftkings._constants import BATTLE_ALIASES
import BigWorld
import GUI
import Keys
import Math
from Event import EventManager, Event
from Driftkings.core.keyboard import keyboard
from Driftkings.core.hud_visibility import hudVisibility
from Driftkings.meta.battle.distance_marker import DistanceMarkerMeta
from Driftkings.common import logWarning

from importlib import import_module


def _component():
    # Resolve live state after component initialization; avoid circular imports.
    return import_module('Driftkings.battle.distance_marker')


def serializeConfigParams():
    textColor = settings_service.getComponentDict(_component().config)[DISTANCE_MARKER.TEXT_COLOR]
    if isinstance(textColor, str):
        if textColor.startswith('#'):
            textColor = textColor[1:]
        hex_color = '0x' + textColor
    else:
        r, g, b = textColor
        hex_color = '0x{:02X}{:02X}{:02X}'.format(r, g, b)
    return {
        'decimalPrecision': settings_service.getComponentDict(_component().config)[DISTANCE_MARKER.DECIMAL_PRECISION],
        'textSize': settings_service.getComponentDict(_component().config)[DISTANCE_MARKER.TEXT_SIZE],
        'textColor': hex_color,  # Send properly formatted hex color
        'textAlpha': settings_service.getComponentDict(_component().config)[DISTANCE_MARKER.TEXT_ALPHA],
        'drawTextShadow': settings_service.getComponentDict(_component().config)[DISTANCE_MARKER.DRAW_TEXT_SHADOW]
    }


class _SimpleDictPool(object):
    def __init__(self):
        self.pool = []

    def __getitem__(self, item):
        return self.pool[item]

    def ensureLength(self, length):
        lackingCount = length - len(self.pool)
        if lackingCount <= 0:
            return
        for i in range(lackingCount):
            self.pool.append({})


ALIAS = BATTLE_ALIASES.DISTANCE_MARKER
_view = None


class DistanceMarkerView(DistanceMarkerMeta):
    def _populate(self):
        super(DistanceMarkerView, self)._populate()
        global _view
        _view = self
        self.as_applyConfigS(serializeConfigParams())

    def _dispose(self):
        global _view
        if _view is self:
            _view = None
        super(DistanceMarkerView, self)._dispose()

    def py_requestFrameData(self):
        controller = _component().g_distanceMarker
        if controller is not None:
            return controller.py_requestFrameData()
        width, height = GUI.screenResolution()
        return {'screenWidth': width, 'screenHeight': height, 'observedVehicles': []}


class DistanceMarkerController(object):
    """Marker data/keyboard controller; the shared library owns the display."""
    _eventManager = EventManager()
    onMouseEvent = Event(_eventManager)

    def __init__(self, vehicleMarkerClass):
        self._vehicleMarkerClass = vehicleMarkerClass
        self._currentHorizontalAnchorOffset = settings_service.getComponentDict(_component().config)[DISTANCE_MARKER.ANCHOR_HORIZONTAL_OFFSET]
        self._currentVerticalAnchorOffset = -1 * settings_service.getComponentDict(_component().config)[DISTANCE_MARKER.ANCHOR_VERTICAL_OFFSET]
        self._wereOffsetsEdited = False
        self._isDisplayingMarkers = settings_service.getComponentDict(_component().config)[DISTANCE_MARKER.DISPLAY_MODE] == 0
        self._isMarkerDragging = False
        anchorPosition = settings_service.getComponentDict(_component().config)[DISTANCE_MARKER.ANCHOR_POSITION]
        if anchorPosition == 0:
            self._markerPositionProvider = self._vehicleMarkerPositionProvider
        elif anchorPosition == 1:
            self._markerPositionProvider = self._vehicleCenterPositionProvider
        else:
            self._markerPositionProvider = self._vehicleBottomPositionProvider
        self._currentViewProjectionMatrix = Math.Matrix()
        self._tempMatrix = Math.Matrix()
        self._emptyList = []
        self._dictPool = _SimpleDictPool()
        screenResolution = GUI.screenResolution()
        self._currentScreenWidth = screenResolution[0]
        self._currentScreenHeight = screenResolution[1]
        self._currentFrameData = {'screenWidth': self._currentScreenWidth, 'screenHeight': self._currentScreenHeight, 'observedVehicles': self._emptyList}
        keyboard.subscribe(self._onKey)
        serializedConfig = serializeConfigParams()
        if _view is not None:
            _view.as_applyConfigS(serializedConfig)

    def close(self):
        if self._isMarkerDragging:
            self.onMouseEvent -= self._onMarkerDragging
            self._isMarkerDragging = False
        keyboard.unsubscribe(self._onKey)
        if self._wereOffsetsEdited:
            settings_service.apply(_component().config, {DISTANCE_MARKER.ANCHOR_HORIZONTAL_OFFSET: self._currentHorizontalAnchorOffset}, persist=False)
            settings_service.apply(_component().config, {DISTANCE_MARKER.ANCHOR_VERTICAL_OFFSET: -1 * self._currentVerticalAnchorOffset}, persist=False)

    def as_isPointInMarker(self, mouseX, mouseY):
        if _view is not None:
            return _view.as_isPointInMarkerS(mouseX, mouseY)
        return False

    def _onKey(self, event):
        if event.isKeyDown():
            self._onKeyDown(event)
        else:
            self._onKeyUp(event)

    def _onKeyUp(self, event):
        if settings_service.getComponentDict(_component().config)[DISTANCE_MARKER.DISPLAY_MODE] == 1:
            self._isDisplayingMarkers = event.isAltDown()
        if self._isMarkerDragging and self._isLeftMouseButton(event):
            self._isMarkerDragging = False
            self.onMouseEvent -= self._onMarkerDragging

    def _onKeyDown(self, event):
        if settings_service.getComponentDict(_component().config)[DISTANCE_MARKER.DISPLAY_MODE] == 1:
            self._isDisplayingMarkers = event.isAltDown()
        cursor = GUI.mcursor()
        isOffsetChangeAllowed = not settings_service.getComponentDict(_component().config)[DISTANCE_MARKER.LOCK_POSITION_OFFSETS]
        if self._isDisplayingMarkers and isOffsetChangeAllowed and event.isCtrlDown() and self._isLeftMouseButton(
                event) and cursor.inWindow and cursor.inFocus:
            mouseX, mouseY = cursor.position
            screenX, screenY = self._toScreenPixelPosition(mouseX, mouseY)
            if self.as_isPointInMarker(screenX, screenY):
                self._isMarkerDragging = True
                self.onMouseEvent += self._onMarkerDragging

    @staticmethod
    def _isLeftMouseButton(event):
        return event.isMouseButton() and event.key == Keys.KEY_LEFTMOUSE

    def _onMarkerDragging(self, dx, dy):
        self._currentHorizontalAnchorOffset += dx
        self._currentVerticalAnchorOffset += dy
        self._wereOffsetsEdited = True

    def py_requestFrameData(self):
        try:
            screenResolution = GUI.screenResolution()
            self._currentFrameData['screenWidth'] = self._currentScreenWidth = screenResolution[0]
            self._currentFrameData['screenHeight'] = self._currentScreenHeight = screenResolution[1]
            self._currentFrameData['observedVehicles'] = self._emptyList
            return self._requestFrameData()
        except Exception as e:
            logWarning(_component().config.ID, 'Occurred on requesting frame data by DistanceMarkerController, safely skipping frame rendering: {}', e, exc_info=True)
            self._currentFrameData['observedVehicles'] = self._emptyList
            return self._currentFrameData

    def _requestFrameData(self):
        if not self._isDisplayingMarkers or not hudVisibility.visible:
            return self._currentFrameData
        player = BigWorld.player()
        if player is None:
            return self._currentFrameData
        avatarInputHandler = player.inputHandler
        if avatarInputHandler is not None and not avatarInputHandler.isGuiVisible:
            return self._currentFrameData
        currentVehicleID = -1
        currentVehicle = player.getVehicleAttached()
        if self._isVehicleSafeToUse(currentVehicle):
            currentVehicleID = currentVehicle.id
            playerPositionProvider = currentVehicle.matrix
        elif BigWorld.camera() is not None:
            playerPositionProvider = BigWorld.camera().matrix
        else:
            return self._currentFrameData
        self._tempMatrix.set(playerPositionProvider)
        currentPlayerPosition = self._tempMatrix.translation
        self._updateViewProjectionMatrix()
        vehicles = BigWorld.player().vehicles
        self._dictPool.ensureLength(len(vehicles))
        # Performance improvement: Use list comprehension with pre-filtering
        observed_vehicles = []
        for poolIndex, vehicle in enumerate(vehicles):
            if self._shouldDisplayForVehicle(vehicle, currentVehicleID):
                vehicle_data = self._serializeObservedVehicle(currentPlayerPosition, vehicle, self._dictPool[poolIndex])
                observed_vehicles.append(vehicle_data)

        self._currentFrameData['observedVehicles'] = observed_vehicles
        return self._currentFrameData

    def _shouldDisplayForVehicle(self, vehicle, currentVehicleID):
        if not self._isVehicleSafeToUse(vehicle) or vehicle.id == currentVehicleID:
            return False
        if not vehicle.isAlive():
            return False
        if settings_service.getComponentDict(_component().config)[DISTANCE_MARKER.MARKER_TARGET] == 0:
            return True
        return BigWorld.player().team != vehicle.publicInfo['team']

    @staticmethod
    def _isVehicleSafeToUse(vehicle):
        return vehicle is not None and getattr(vehicle, 'isStarted', False)

    def _updateViewProjectionMatrix(self):
        proj = BigWorld.projection()
        aspect = BigWorld.getAspectRatio()
        self._currentViewProjectionMatrix.perspectiveProjection(proj.fov, aspect, proj.nearPlane, proj.farPlane)
        self._currentViewProjectionMatrix.preMultiply(BigWorld.camera().matrix)

    def _serializeObservedVehicle(self, currentPlayerPosition, vehicle, pooledVehicleDict):
        self._tempMatrix.set(vehicle.matrix)
        vehiclePosition = self._tempMatrix.translation
        currentDistance = (vehiclePosition - currentPlayerPosition).length
        markerPosition3d = self._markerPositionProvider(vehicle)
        projectedMarkerPosition2d, isPointOnScreen = self._projectPointWithVisibilityResult(markerPosition3d)
        x, y = self._toScreenPixelPosition(projectedMarkerPosition2d.x, projectedMarkerPosition2d.y)
        pooledVehicleDict['id'] = str(vehicle.id)
        pooledVehicleDict['currentDistance'] = currentDistance
        pooledVehicleDict['x'] = x + self._currentHorizontalAnchorOffset
        pooledVehicleDict['y'] = y + self._currentVerticalAnchorOffset
        pooledVehicleDict['isVisible'] = isPointOnScreen
        return pooledVehicleDict

    def _vehicleMarkerPositionProvider(self, vehicle):
        try:
            vehicleMarkerMatrixProvider = self._vehicleMarkerClass.fetchMatrixProvider(vehicle)
            self._tempMatrix.set(vehicleMarkerMatrixProvider)
            return self._tempMatrix.translation
        except Exception as e:
            logWarning(_component().config.ID, 'Error in _vehicleMarkerPositionProvider: {}'.format(e))
            return self._vehicleCenterPositionProvider(vehicle)

    def _vehicleCenterPositionProvider(self, vehicle):
        self._tempMatrix.set(vehicle.matrix)
        vehicleCenterPosition = self._tempMatrix.translation
        vehicleCenterPosition.y += 2.0
        return vehicleCenterPosition

    def _vehicleBottomPositionProvider(self, vehicle):
        self._tempMatrix.set(vehicle.matrix)
        vehicleCenterPosition = self._tempMatrix.translation
        vehicleCenterPosition.y -= 1.0
        return vehicleCenterPosition

    def _projectPointWithVisibilityResult(self, point):
        posInClip = Math.Vector4(point.x, point.y, point.z, 1)
        posInClip = self._currentViewProjectionMatrix.applyV4Point(posInClip)
        if point.lengthSquared != 0.0:
            visible = posInClip.w > 0 and -1 <= posInClip.x / posInClip.w <= 1 and -1 <= posInClip.y / posInClip.w <= 1
        else:
            visible = False
        if posInClip.w != 0:
            posInClip = posInClip.scale(1 / posInClip.w)
        return posInClip, visible

    def _toScreenPixelPosition(self, x, y):
        normalizedX = 0.5 + 0.5 * x
        normalizedY = 0.5 - 0.5 * y
        return normalizedX * self._currentScreenWidth, normalizedY * self._currentScreenHeight
