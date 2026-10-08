# -*- coding: utf-8 -*-
from Driftkings._constants import GLOBAL, OWN_HEALTH
from Driftkings.settings.template_schema import slider
from Driftkings.settings.templates.base import ComponentSettings


class OwnHealthSettings(ComponentSettings):
    COMPONENT = OWN_HEALTH.ID

    TRANSLATED_TITLE = True
    COLUMNS = (
        (
            slider(GLOBAL.X, -2000, 2000, 1, '{{value}}%s' % ' px'),
            slider(GLOBAL.Y, -2000, 2000, 1, '{{value}}%s' % ' px'),
        ),
        (
        ),
    )
