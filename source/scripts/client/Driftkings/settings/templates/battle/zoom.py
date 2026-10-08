# -*- coding: utf-8 -*-
from Driftkings._constants import ZOOM_EXTENDED
from Driftkings.settings.template_schema import control, slider
from Driftkings.settings.templates.base import ComponentSettings


class ZoomExtendedSettings(ComponentSettings):
    COMPONENT = ZOOM_EXTENDED.ID

    TRANSLATED_TITLE = True
    COLUMNS = (
        (
            control(ZOOM_EXTENDED.NO_BINOCULARS),
            control(ZOOM_EXTENDED.NO_FLASH_BANG),
            control(ZOOM_EXTENDED.NO_SHOCK_WAVE),
            control(ZOOM_EXTENDED.NO_SNIPER_DYNAMIC),
        ),
        (
            control(ZOOM_EXTENDED.DISABLE_CAM_AFTER_SHOT),
            slider(ZOOM_EXTENDED.DISABLE_CAM_AFTER_SHOT_LATENCY, 1.0, 20.0, 1.0, '{{value}} x'),
            control(ZOOM_EXTENDED.DISABLE_CAM_AFTER_SHOT_SKIP_CLIP),
        ),
    )
