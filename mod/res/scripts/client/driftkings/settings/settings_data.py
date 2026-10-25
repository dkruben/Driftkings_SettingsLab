# -*- coding: utf-8 -*-
"""Settings metadata and access to JSON-generated component defaults."""
import copy

from driftkings._constants import (AIMING_COUNTDOWN, AIMING_RETICLES, ARTILLERY_BLAST_RADIUS, AUTOAIM_TARGET_INDICATOR,
                                   BATTLE_MARKS_OF_EXCELLENCE, BATTLE_PERFORMANCE, BATTLE_PREFERENCES,
                                   BATTLE_STATISTICS, CLAN_REWARD_COLLECTION, CREW_MANAGEMENT, ENEMY_SPOTTING_STATUS,
                                   GAME_LOG_MANAGER, GLOBAL, GUN_TRAVERSE_LIMITS, HANGAR_MARKS_OF_EXCELLENCE,
                                   HANGAR_PREFERENCES, HIGH_CALIBER_PROGRESS, MAIN, MINIMAP_ENHANCEMENTS,
                                   PENETRATION_INDICATOR, REPAIR_CONTROLS, SERVER_TURRET_SYNC, SHELL_FLIGHT_TIME,
                                   SIXTH_SENSE_ALERT, SNIPER_CAMERA, SOUND_BANK_LOADER, TARGET_DISTANCE,
                                   TARGET_INFORMATION, TEAM_PANELS, TECH_TREE_MARKS_OF_EXCELLENCE, THIRD_PERSON_ZOOM,
                                   VEHICLE_CAROUSEL, VEHICLE_HEALTH)
from driftkings.settings.default_values import DEFAULTS
from driftkings.settings.sections import section_name

# Only the field names are policy; key bindings come from the JSON.
HOTKEY_FIELDS = {
    ARTILLERY_BLAST_RADIUS.NAME: (ARTILLERY_BLAST_RADIUS.BUTTON_SHOW_DOT, ARTILLERY_BLAST_RADIUS.BUTTON_SHOW_SPLASH),
    TARGET_INFORMATION.NAME: (TARGET_INFORMATION.ALT_KEY,),
    BATTLE_MARKS_OF_EXCELLENCE.NAME: (BATTLE_MARKS_OF_EXCELLENCE.BUTTON_SIZE_UP,
                           BATTLE_MARKS_OF_EXCELLENCE.BUTTON_SIZE_DOWN, BATTLE_MARKS_OF_EXCELLENCE.BUTTON_RESET),
    MINIMAP_ENHANCEMENTS.NAME: (MINIMAP_ENHANCEMENTS.BUTTON,),
    REPAIR_CONTROLS.NAME: (REPAIR_CONTROLS.BUTTON_REPAIR, REPAIR_CONTROLS.BUTTON_CHASSIS),
}
HOTKEYS = dict((component, dict((key, copy.deepcopy(DEFAULTS[component][key])) for key in fields))
               for component, fields in HOTKEY_FIELDS.items())
PROFILES = ('none', 'short', 'medium', 'medium2', 'large')


def defaults(component):
    return copy.deepcopy(DEFAULTS[section_name(component)])


def default_keys(component):
    return copy.deepcopy(HOTKEYS.get(section_name(component), {}))


def part_name(component):
    return section_name(component)


def profile_for_mode(mode):
    # Native EU PLAYERS_PANEL_STATE, including variants without badges.
    return {0: 'none', 1: 'short', 20: 'short', 2: 'medium', 5: 'medium',
            3: 'medium2', 21: 'medium2', 4: 'large', 6: 'large'}.get(mode, 'large')


class SettingsData(object):
    """Shared access to the same live dictionaries used by feature controllers."""
    def __init__(self):
        self.configs = {}

    def register(self, config):
        self.configs[part_name(config.NAME)] = config

    def __getattr__(self, name):
        config = self.configs.get(name)
        if config is None:
            raise AttributeError(name)
        return config.data


user_settings = SettingsData()

# Controllers verified to read or refresh these values during battle.
BATTLE_EDITABLE = frozenset((AUTOAIM_TARGET_INDICATOR.NAME, TARGET_INFORMATION.NAME, TEAM_PANELS.NAME))
# Application timing follows the readers/callbacks in each controller. Unknown
# options retain the safe restart policy; paths allow different nested options.
LIVE = 'live'
NEXT_BATTLE = 'battle'
NEXT_VIEW = 'view'
RESTART = 'restart'
APPLY_TIMING = {
    AUTOAIM_TARGET_INDICATOR.NAME: {'*': LIVE},  # native-target box reads current settings
    TARGET_INFORMATION.NAME: {'*': LIVE, GLOBAL.ENABLED: NEXT_BATTLE},
    TEAM_PANELS.NAME: {'*': LIVE, GLOBAL.ENABLED: NEXT_BATTLE},
    HIGH_CALIBER_PROGRESS.NAME: {GLOBAL.ENABLED: LIVE, HIGH_CALIBER_PROGRESS.BACK_GROUND_ENABLED: LIVE, HIGH_CALIBER_PROGRESS.TEXT_LOCK: LIVE, HIGH_CALIBER_PROGRESS.TEXT_POSITION: LIVE, 'background.alpha': LIVE, 'gameface': LIVE, 'mainGun': LIVE},
    BATTLE_STATISTICS.NAME: {GLOBAL.ENABLED: LIVE, BATTLE_STATISTICS.FORMAT: LIVE, BATTLE_STATISTICS.COLOR_RATING: LIVE, BATTLE_STATISTICS.TEXT_LOCK: LIVE, BATTLE_STATISTICS.TEXT_POSITION: LIVE},
    BATTLE_PERFORMANCE.NAME: {GLOBAL.ENABLED: NEXT_BATTLE, BATTLE_PERFORMANCE.TEXT_LOCK: LIVE, BATTLE_PERFORMANCE.POSITION: LIVE, BATTLE_PERFORMANCE.COLOR_RATTING: LIVE, BATTLE_PERFORMANCE.FORMAT: LIVE, BATTLE_PERFORMANCE.BATTLE_RESULTS_WINDOW: NEXT_VIEW, BATTLE_PERFORMANCE.BATTLE_RESULTS_FORMAT: NEXT_VIEW},
    VEHICLE_HEALTH.NAME: {'*': LIVE, GLOBAL.ENABLED: NEXT_BATTLE},
    'vehicle_markers': {'*': NEXT_BATTLE},
    # Views/cameras are constructed again when entering battle.
    PENETRATION_INDICATOR.NAME: {'*': NEXT_BATTLE},
    ARTILLERY_BLAST_RADIUS.NAME: {'*': NEXT_BATTLE},
    # Arcade camera base dictionaries are shared and cleared only on first use.
    THIRD_PERSON_ZOOM.NAME: {'*': RESTART},
    AIMING_COUNTDOWN.NAME: {'*': NEXT_BATTLE},
    SHELL_FLIGHT_TIME.NAME: {'*': NEXT_BATTLE},
    TARGET_DISTANCE.NAME: {'*': NEXT_BATTLE},
    SIXTH_SENSE_ALERT.NAME: {'*': NEXT_BATTLE},
    AIMING_RETICLES.NAME: {'*': NEXT_BATTLE},
    MINIMAP_ENHANCEMENTS.NAME: {'*': NEXT_BATTLE},
    BATTLE_PREFERENCES.NAME: {'*': NEXT_BATTLE, BATTLE_PREFERENCES.REMOVE_FOG: RESTART},
    BATTLE_MARKS_OF_EXCELLENCE.NAME: {'*': NEXT_BATTLE, 'gameface': LIVE, 'panel': LIVE,
        BATTLE_MARKS_OF_EXCELLENCE.BATTLE_MESSAGE_SIZE_IN_PERCENT: LIVE,
        BATTLE_MARKS_OF_EXCELLENCE.BACKGROUND: LIVE,
        'showMarks': LIVE, 'showDelta': LIVE, 'showDamage': LIVE,
        'showProgress': LIVE, 'showTargets': LIVE},
    GUN_TRAVERSE_LIMITS.NAME: {'*': NEXT_BATTLE},
    ENEMY_SPOTTING_STATUS.NAME: {'*': NEXT_BATTLE},
    SERVER_TURRET_SYNC.NAME: {'*': NEXT_BATTLE},
    REPAIR_CONTROLS.NAME: {'*': NEXT_BATTLE},
    GAME_LOG_MANAGER.NAME: {'*': LIVE},  # filters/routing read on each new log entry
    CREW_MANAGEMENT.NAME: {'*': NEXT_VIEW},  # vehicle selection/crew action
    CLAN_REWARD_COLLECTION.NAME: {'*': NEXT_VIEW},
    VEHICLE_CAROUSEL.NAME: {'*': LIVE},  # controller.onApplySettings
    HANGAR_MARKS_OF_EXCELLENCE.NAME: {'*': LIVE},
    TECH_TREE_MARKS_OF_EXCELLENCE.NAME: {'*': LIVE},
    HANGAR_PREFERENCES.NAME: {'*': NEXT_VIEW, HANGAR_PREFERENCES.LOW_AMMO_PERCENTAGE: LIVE, HANGAR_PREFERENCES.SHOW_BATTLE_PASS_WIDGET: LIVE, 'showBuyPremiumButton': RESTART, 'showPremiumShopButton': NEXT_VIEW, 'showReferralButton': NEXT_VIEW, 'showWotPlusButton': RESTART, 'premiumTime': RESTART, HANGAR_PREFERENCES.HIDE_BTN_COUNTERS: LIVE},
    # The camera-change listener caches these values only at construction.
    SNIPER_CAMERA.NAME: {SNIPER_CAMERA.NO_BINOCULARS: NEXT_BATTLE, SNIPER_CAMERA.NO_SNIPER_DYNAMIC: NEXT_BATTLE, SNIPER_CAMERA.ZOOM_STEPS: NEXT_BATTLE, SNIPER_CAMERA.NO_FLASH_BANG: LIVE, SNIPER_CAMERA.NO_SHOCK_WAVE: LIVE},
    SOUND_BANK_LOADER.NAME: {'*': RESTART},
    MAIN.NAME: {'*': LIVE},  # the clock view republishes its formats on change
    'driftkings': {'*': RESTART},  # selected configuration profile
}


def application_timing(component, field):
    if isinstance(field, (tuple, list)):
        field = '.'.join(str(part) for part in field)
    policy = APPLY_TIMING.get(component, {})
    # Specific child paths take precedence over a parent group and '*'.
    while field:
        if field in policy:
            return policy[field]
        field = field.rsplit('.', 1)[0] if '.' in field else ''
    return policy.get('*', RESTART)


