# -*- coding: utf-8 -*-
from Driftkings._constants import DISTANCE_MARKER
from Driftkings.settings.template_schema import control, slider, options
from Driftkings.settings.templates.base import ComponentSettings


class DistanceMarkerSettings(ComponentSettings):
    COMPONENT = DISTANCE_MARKER.ID

    TRANSLATED_TITLE = False
    COLUMNS = (
        (
            options(DISTANCE_MARKER.DISPLAY_MODE, ['always', 'onAltPressed']),
            options(DISTANCE_MARKER.MARKER_TARGET, ['allyAndEnemy', 'onlyEnemy']),
            options(DISTANCE_MARKER.ANCHOR_POSITION, ['tankMarker', 'tankCenter', 'tankBottom']),
            control(DISTANCE_MARKER.LOCK_POSITION_OFFSETS),
            slider(DISTANCE_MARKER.ANCHOR_HORIZONTAL_OFFSET, -150, 150, 1),
            slider(DISTANCE_MARKER.ANCHOR_VERTICAL_OFFSET, -150, 150, 1),
        ),
        (
            slider(DISTANCE_MARKER.DECIMAL_PRECISION, 0, 3, 1),
            slider(DISTANCE_MARKER.TEXT_SIZE, 6, 24, 1),
            control(DISTANCE_MARKER.TEXT_COLOR, 'ColorChoice'),
            slider(DISTANCE_MARKER.TEXT_ALPHA, 0.0, 1.0, 0.01),
            control(DISTANCE_MARKER.DRAW_TEXT_SHADOW),
        ),
    )
