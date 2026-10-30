# -*- coding: utf-8 -*-
"""UI contracts shared by runtime, Flash generation and resource validation.
Technical aliases are independent of settings section names. Importing this
catalog performs no engine initialization and creates no views.
"""
FLASH_LIBRARY = 'driftkingsbattle.swf'
FLASH_COMPONENTS = {
    'ArmorCalculatorView': {
        'as3': 'driftkings.battle.components.armor_calculator.armorcalculatorui',
        'component': 'battle.penetration_indicator',
        'python': 'driftkings.flash.battle.penetration_indicator.ArmorCalculator',
        'section': 'penetration_indicator',
        'surfaces': ['battle']
    },
    'DispersionTimerView': {
        'as3': 'driftkings.battle.components.dispersion_timer.dispersiontimerui',
        'component': 'battle.aiming_countdown',
        'python': 'driftkings.flash.battle.aiming_countdown.DispersionTimer',
        'section': 'aiming_countdown',
        'surfaces': ['battle']
    },
    'DistanceMarkerView': {
        'as3': 'driftkings.battle.components.distance_marker.distancemarkerui',
        'component': 'battle.target_distance',
        'python': 'driftkings.flash.battle.target_distance.DistanceMarkerView',
        'section': 'target_distance',
        'surfaces': ['battle']
    },
    'DriftkingsDebugPanel': {
        'as3': 'driftkings.battle.components.debug_panel.debugpanelui',
        'component': 'battle.battle_preferences',
        'python': 'driftkings.flash.battle.debug_panel.DebugPanelView',
        'section': 'battle_preferences',
        'surfaces': ['battle']
    },
    'DriftkingsOverlay': {
        'as3': 'driftkings.battle.components.overlay.overlayui',
        'component': None,
        'python': 'driftkings.flash.battle.overlay.OverlayView',
        'section': None,
        'surfaces': ['battle']
    },
    'DriftkingsRatingScreens': {
        'as3': 'driftkings.battle.components.ratings.ratingscreens',
        'component': 'battle.team_panels',
        'python': 'driftkings.flash.battle.player_ratings.RatingViews',
        'section': 'team_panels',
        'surfaces': ['battle', 'ratings']
    },
    'FlightTimerView': {
        'as3': 'driftkings.battle.components.flight_timer.flighttimerui',
        'component': 'battle.shell_flight_time',
        'python': 'driftkings.flash.battle.shell_flight_time.FlightTime',
        'section': 'shell_flight_time',
        'surfaces': ['battle']
    },
    'MinimapEnhancementsView': {
        'as3': 'driftkings.battle.components.minimap.minimapenhancementsui',
        'component': 'battle.minimap_enhancements',
        'python': 'driftkings.flash.battle.minimap_enhancements.MinimapEnhancementsView',
        'section': 'minimap_enhancements',
        'surfaces': ['battle']
    },
    'SixthSenseView': {
        'as3': 'driftkings.battle.components.sixth_sense.sixthsenseui',
        'component': 'battle.sixth_sense_alert',
        'python': 'driftkings.flash.battle.sixth_sense_alert.SixthSense',
        'section': 'sixth_sense_alert',
        'surfaces': ['battle']
    }
}
# Gameface features are defined in the catalog to allow for validation and discovery of available features.
# The catalog is used by the runtime to determine which features are available and to load the appropriate resources.
# Each feature has a context, layout, owner, python module, resource path, scripts, section, and styles.
GAMEFACE = {
    'DriftkingsProfileRatings': {
        'context': 'hangar',
        'layout': 'coui://gui/gameface/mods/driftkings/profile_ratings/model.html',
        'owner': '__dkProfileRatings',
        'python': 'driftkings.gameface.lobby.profile_ratings',
        'resource': 'mods/driftkings/profile_ratings/model',
        'scripts': ['coui://gui/gameface/mods/driftkings/profile_ratings/ratings.js'],
        'section': 'profile_ratings',
        'styles': []
    },
    'DriftkingsOwnHealth': {
        'context': 'battle',
        'layout': 'coui://gui/gameface/mods/driftkings/vehicle_health/model.html',
        'owner': '__dkOwnHealth',
        'python': 'driftkings.gameface.battle.vehicle_health',
        'resource': 'mods/driftkings/vehicle_health/model',
        'scripts': ['coui://gui/gameface/mods/driftkings/shared/marks_panel.js', 'coui://gui/gameface/mods/driftkings/shared/health_bar.js', 'coui://gui/gameface/mods/driftkings/vehicle_health/vehicle_health.js'],
        'section': 'vehicle_health',
        'styles': ['coui://gui/gameface/mods/driftkings/shared/health_bar.css', 'coui://gui/gameface/mods/driftkings/vehicle_health/vehicle_health.css']},
    'DriftkingsMainGun': {
        'context': 'battle',
        'layout': 'coui://gui/gameface/mods/driftkings/high_caliber_gameface/model.html',
        'owner': '__dkMainGun',
        'python': 'driftkings.gameface.battle.high_caliber_gameface',
        'resource': 'mods/driftkings/high_caliber_gameface/model',
        'scripts': ['coui://gui/gameface/mods/driftkings/shared/marks_panel.js', 'coui://gui/gameface/mods/driftkings/high_caliber_gameface/main_gun.js'],
        'section': 'high_caliber_progress',
        'styles': ['coui://gui/gameface/mods/driftkings/high_caliber_gameface/main_gun.css']
    },
    'DriftkingsCrewDetails': {
        'context': 'hangar',
        'layout': 'coui://gui/gameface/mods/driftkings/crew_details/model.html',
        'owner': '__dkCrewDetails',
        'python': 'driftkings.gameface.lobby.crew_details',
        'resource': 'mods/driftkings/crew_details/model',
        'scripts': ['coui://gui/gameface/mods/driftkings/crew_details/details.js'],
        'section': 'crew_management',
        'styles': ['coui://gui/gameface/mods/driftkings/crew_details/details.css']
    },
    'DriftkingsCrewProgression': {
        'context': 'hangar',
        'layout': 'coui://gui/gameface/mods/driftkings/crew_progression/model.html',
        'owner': '__dkCrewProgression',
        'python': 'driftkings.gameface.lobby.crew_progression',
        'resource': 'mods/driftkings/crew_progression/model',
        'scripts': ['coui://gui/gameface/mods/driftkings/crew_progression/crew.js'],
        'section': 'crew_management',
        'styles': []
    },
    'DriftkingsAccountManager': {
        'context': 'window',
        'layout': 'coui://gui/gameface/mods/driftkings/account_manager/window.html',
        'owner': None,
        'python': 'driftkings.gameface.lobby.account_manager',
        'resource': 'mods/driftkings/account_manager/window',
        'scripts': ['coui://gui/gameface/mods/driftkings/account_manager/accounts.js'],
        'section': 'hangar_preferences',
        'styles': ['coui://gui/gameface/mods/driftkings/account_manager/accounts.css']
    },
    'driftkingsbattleEfficiency': {
        'context': 'results',
        'layout': 'coui://gui/gameface/mods/driftkings/battle_performance/model.html',
        'owner': '__dkBattleEfficiency',
        'python': 'driftkings.gameface.lobby.battle_performance',
        'resource': 'mods/driftkings/battle_performance/model',
        'scripts': ['coui://gui/gameface/mods/driftkings/shared/flash_text.js', 'coui://gui/gameface/mods/driftkings/battle_performance/results.js'],
        'section': 'battle_performance',
        'styles': ['coui://gui/gameface/mods/driftkings/battle_performance/results.css']
    },
    'DriftkingsCarouselStats': {
        'context': 'hangar',
        'layout': 'coui://gui/gameface/mods/driftkings/vehicle_carousel/model.html',
        'owner': '__dkCarouselStats',
        'python': 'driftkings.gameface.lobby.vehicle_carousel',
        'resource': 'mods/driftkings/vehicle_carousel/model',
        'scripts': ['coui://gui/gameface/mods/driftkings/vehicle_carousel/carousel_native.js', 'coui://gui/gameface/mods/driftkings/vehicle_carousel/carousel_layout.js', 'coui://gui/gameface/mods/driftkings/vehicle_carousel/carousel.js'],
        'section': 'vehicle_carousel',
        'styles': ['coui://gui/gameface/mods/driftkings/vehicle_carousel/carousel.css']
    },
    'DriftkingsModSettings': {
        'context': 'window',
        'layout': 'coui://gui/gameface/mods/driftkings/settings_window/window.html',
        'owner': None,
        'python': 'driftkings.gameface.lobby.settings_window',
        'resource': 'mods/driftkings/settings_window/window',
        'scripts': ['coui://gui/gameface/mods/driftkings/settings_window/js/core.js', 'coui://gui/gameface/mods/driftkings/settings_window/js/assets.js',
                    'coui://gui/gameface/mods/driftkings/settings_window/js/bridge.js', 'coui://gui/gameface/mods/driftkings/settings_window/js/layer.js',
                    'coui://gui/gameface/mods/driftkings/settings_window/js/colors.js', 'coui://gui/gameface/mods/driftkings/settings_window/js/color_picker.js',
                    'coui://gui/gameface/mods/driftkings/settings_window/js/controls.js', 'coui://gui/gameface/mods/driftkings/settings_window/js/vehicle_markers_model.js',
                    'coui://gui/gameface/mods/driftkings/settings_window/js/markers.js', 'coui://gui/gameface/mods/driftkings/settings_window/js/minimap.js',
                    'coui://gui/gameface/mods/driftkings/settings_window/js/richtext.js', 'coui://gui/gameface/mods/driftkings/shared/health_bar.js', 'coui://gui/gameface/mods/driftkings/settings_window/js/hud.js',
                    'coui://gui/gameface/mods/driftkings/settings_window/js/carousel.js', 'coui://gui/gameface/mods/driftkings/settings_window/js/app.js'],
        'section': 'driftkings',
        'styles': ['coui://gui/gameface/mods/driftkings/shared/fonts.css', 'coui://gui/gameface/mods/driftkings/shared/health_bar.css', 'coui://gui/gameface/mods/driftkings/settings_window/css/panel.css', 'coui://gui/gameface/mods/driftkings/settings_window/css/color_picker.css']
    },
    'DriftkingsHangarClock': {
        'context': 'hangar',
        'layout': 'coui://gui/gameface/mods/driftkings/main/clock.html',
        'owner': '__dkHangarClock',
        'python': 'driftkings.gameface.lobby.main',
        'resource': 'mods/driftkings/main/clock',
        'scripts': ['coui://gui/gameface/mods/driftkings/main/clock.js'],
        'section': 'main',
        'styles': ['coui://gui/gameface/mods/driftkings/main/clock.css']
    },
    'DriftkingsHangarHeaderOptions': {
        'context': 'header',
        'layout': 'coui://gui/gameface/mods/driftkings/hangar_preferences/header_options.html',
        'owner': '__dkHangarHeaderOptions',
        'python': 'driftkings.gameface.lobby.hangar_preferences',
        'resource': 'mods/driftkings/hangar_preferences/header_options',
        'scripts': ['coui://gui/gameface/mods/driftkings/hangar_preferences/header_options.js'],
        'section': 'hangar_preferences',
        'styles': []
    },
    'DriftkingsMarksOnGunBattle': {
        'context': 'battle',
        'layout': 'coui://gui/gameface/mods/driftkings/battle_marks_of_excellence/model.html',
        'owner': '__dkBattleMarks',
        'python': 'driftkings.gameface.battle.battle_marks_of_excellence',
        'resource': 'mods/driftkings/battle_marks_of_excellence/model',
        'scripts': ['coui://gui/gameface/mods/driftkings/shared/marks_panel.js', 'coui://gui/gameface/mods/driftkings/battle_marks_of_excellence/marks.js'],
        'section': 'battle_marks_of_excellence',
        'styles': ['coui://gui/gameface/mods/driftkings/shared/marks_panel.css', 'coui://gui/gameface/mods/driftkings/battle_marks_of_excellence/marks.css']
    },
    'DriftkingsMarksOnGunHangar': {
        'context': 'hangar',
        'layout': 'coui://gui/gameface/mods/driftkings/hangar_marks_of_excellence/model.html',
        'owner': '__dkHangarMarks',
        'python': 'driftkings.gameface.lobby.hangar_marks_of_excellence',
        'resource': 'mods/driftkings/hangar_marks_of_excellence/model',
        'scripts': ['coui://gui/gameface/mods/driftkings/shared/marks_panel.js', 'coui://gui/gameface/mods/driftkings/hangar_marks_of_excellence/marks.js'],
        'section': 'hangar_marks_of_excellence',
        'styles': ['coui://gui/gameface/mods/driftkings/shared/marks_panel.css', 'coui://gui/gameface/mods/driftkings/hangar_marks_of_excellence/marks.css']
    },
    'DriftkingsMarksOnGunTechTree': {
        'context': 'tech_tree',
        'layout': 'coui://gui/gameface/mods/driftkings/tech_tree_marks_of_excellence/model.html',
        'owner': '__dkTechMarks',
        'python': 'driftkings.gameface.lobby.tech_tree_marks_of_excellence',
        'resource': 'mods/driftkings/tech_tree_marks_of_excellence/model',
        'scripts': ['coui://gui/gameface/mods/driftkings/tech_tree_marks_of_excellence/marks.js'],
        'section': 'tech_tree_marks_of_excellence',
        'styles': ['coui://gui/gameface/mods/driftkings/shared/marks_tokens.css', 'coui://gui/gameface/mods/driftkings/tech_tree_marks_of_excellence/marks.css']},
    'DriftkingsRatingPlayers': {
        'context': 'tab',
        'layout': 'coui://gui/gameface/mods/driftkings/panel_gameface/model.html',
        'owner': '__dkPlayerRatings',
        'python': 'driftkings.gameface.battle.panel_gameface',
        'resource': 'mods/driftkings/panel_gameface/model',
        'scripts': ['coui://gui/gameface/mods/driftkings/panel_gameface/rating_text.js', 'coui://gui/gameface/mods/driftkings/panel_gameface/rating_rows.js', 'coui://gui/gameface/mods/driftkings/panel_gameface/halloween_tab.js', 'coui://gui/gameface/mods/driftkings/panel_gameface/ratings.js'],
        'section': 'team_panels',
        'styles': []
    }
}


# Gameface features are defined in the catalog to allow for validation and discovery of available features.
def gameface_spec(name):
    if name not in GAMEFACE:
        raise ValueError('Unknown Driftkings Gameface feature: ' + name)
    return GAMEFACE[name]


# Technical aliases are independent of settings section names. Importing this catalog performs no engine initialization and creates no views.
def surface_aliases(aliases, surface):
    return [alias for alias in aliases if alias in FLASH_COMPONENTS and surface in FLASH_COMPONENTS[alias]['surfaces']]


# Technical aliases are independent of settings section names. Importing this catalog performs no engine initialization and creates no views.
def selected_components(definitions, surface='battle'):
    return [alias for alias in surface_aliases(sorted(definitions), surface)
            if definitions[alias][1].data.get('enabled', True)]
