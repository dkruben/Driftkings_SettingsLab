# -*- coding: utf-8 -*-
from driftkings._constants import CREW_MANAGEMENT
from driftkings.settings.controls_schema import control, slider
from driftkings.settings.definitions.base import SectionDefinition


class CrewManagementSettings(SectionDefinition):
    NAME = CREW_MANAGEMENT.NAME

    TRANSLATED_TITLE = True
    COLUMNS = ((control(CREW_MANAGEMENT.CREW_AUTO_RETURN), control(CREW_MANAGEMENT.CREW_RETURN_BY_DEFAULT),
                slider(CREW_MANAGEMENT.AUTO_RETURN_DELAY, 0.5, 5.0, 0.5), control(CREW_MANAGEMENT.SHOW_NOTIFICATIONS),
                ), (control(CREW_MANAGEMENT.EXCLUDE_PREMIUM_VEHICLES), control(CREW_MANAGEMENT.SHOW_CREW_PROGRESSION),
                    control(CREW_MANAGEMENT.SHOW_REMAINING_X_P), control(CREW_MANAGEMENT.SHOW_ESTIMATED_BATTLES),
                    control(CREW_MANAGEMENT.SHOW_CREW_DETAILS), control(CREW_MANAGEMENT.SHOW_CREW_TOOLTIPS),
                    control(CREW_MANAGEMENT.SHOW_BARRACKS_PROGRESSION)),)
