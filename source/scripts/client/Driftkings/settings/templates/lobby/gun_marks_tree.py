# -*- coding: utf-8 -*-
from Driftkings._constants import MARKS_ON_GUN_TECH_TREE
from Driftkings.common import color_tables
from Driftkings.settings.template_schema import control, slider, options
from Driftkings.settings.templates.base import ComponentSettings


class MarksOnGunTechTreeSettings(ComponentSettings):
    COMPONENT = MARKS_ON_GUN_TECH_TREE.ID

    TRANSLATED_TITLE = False
    COLUMNS = (
        (
            options(MARKS_ON_GUN_TECH_TREE.COLOR_RATING, [table['ScaleColor'] for table in color_tables]),
            control(MARKS_ON_GUN_TECH_TREE.SHOW_IN_TECH_TREE),
            control(MARKS_ON_GUN_TECH_TREE.SHOW_IN_TECH_TREE_MARK_OF_GUN_PERCENT),
            control(MARKS_ON_GUN_TECH_TREE.SHOW_IN_TECH_TREE_MASTERY),
            control(MARKS_ON_GUN_TECH_TREE.SHOW_IN_TECH_TREE_MARK_OF_GUN_TANK_NAME_COLORED),
        ),
        (
            slider(MARKS_ON_GUN_TECH_TREE.BADGE_OFFSET_X, -300, 300, 1),
            slider(MARKS_ON_GUN_TECH_TREE.BADGE_OFFSET_Y, -100, 100, 1),
        ),
    )
