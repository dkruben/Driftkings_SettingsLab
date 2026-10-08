# -*- coding: utf-8 -*-
"""Single source of defaults for every Driftkings component (no client imports)."""
import copy
import re

from Driftkings._constants import (
    ACCOUNT_MANAGER, AIMING_ANGLES, ARCADE_ZOOM, ARMOR_CALCULATOR,
    ARTY_SPLASH, AUTO_AIM_OPTIMIZE, AUTO_CLAIM_CLAN, BANKS_LOADER,
    BATTLE_EFFICIENCY, BATTLE_OPTIONS, BATTLE_STAT, CAROUSEL_STATS,
    CONFIG_BY_ID, CREW_SETTINGS, DISPERSION_CIRCLE, DISPERSION_TIMER,
    DISTANCE_MARKER, FLIGHT_TIMER, GLOBAL, HANGAR_OPTIONS,
    INFO_PANEL, LOGS_SWAPPER, MAIN_GUN, MARKS_ON_GUN_BATTLE,
    MARKS_ON_GUN_HANGAR, MARKS_ON_GUN_TECH_TREE, MINIMAP_PLUGINS, OWN_HEALTH,
    PLAYER_PANEL_PRO, REPAIR_EXTENDED, SAFE_SHOT, SERVER_TURRET_EXTENDED,
    SIXTH_SENSE, SPOTTED_EXTENDED_LIGHT, ZOOM_EXTENDED,)

DEFAULTS = {
    AIMING_ANGLES.ID: {
        GLOBAL.ENABLED: True,
        AIMING_ANGLES.VERTICAL: 0,
        AIMING_ANGLES.HORIZONTAL: 0
    },
    ARCADE_ZOOM.ID: {
        GLOBAL.ENABLED: False,
        ARCADE_ZOOM.MAX: 160.0,
        ARCADE_ZOOM.MIN: 4.0,
        ARCADE_ZOOM.SCROLL_SENSITIVITY: 6.0,
        ARCADE_ZOOM.START_DEAD_DIST: 20.0
    },
    ARMOR_CALCULATOR.ID: {
        GLOBAL.ENABLED: True,
        ARMOR_CALCULATOR.DISPLAY_ON_ALLIES: False,
        ARMOR_CALCULATOR.MESSAGES: {
            'green': "<font size='20' color='#66FF33'>Breaking through.</font>",
            'normal': 'Easy To Penetrate :)',
            'orange': "<font size='20' color='#FF9900'>Switch to Gold.</font>",
            'purple': "<font size='20' color='#6F6CD3'>Your time has come.</font>",
            'red': "<font size='20' color='#FF0000'>Try hard, your time has come.</font>",
            'yellow': "<font size='20' color='#FAF829'>Switch to Gold.</font>"
        },
        ARMOR_CALCULATOR.POSITION: {'x': 0, 'y': 40},
        ARMOR_CALCULATOR.TEMPLATE: "<p align='center'>%(ricochet)s %(noDamage)s<br><font color='%(color)s'>%(countedArmor)d | %(piercingPower)d</font></p>"
    },
    ARTY_SPLASH.ID: {
        GLOBAL.ENABLED: True,
        ARTY_SPLASH.BUTTON_SHOW_DOT: ['KEY_C', ['KEY_LALT', 'KEY_RALT']],
        ARTY_SPLASH.BUTTON_SHOW_SPLASH: ['KEY_Z', ['KEY_LALT', 'KEY_RALT']],
        ARTY_SPLASH.SHOW_SPLASH_ON_DEFAULT: True,
        ARTY_SPLASH.SHOW_DOT_ON_DEFAULT: True,
        ARTY_SPLASH.SHOW_MODE_ARCADE: False,
        ARTY_SPLASH.SHOW_MODE_SNIPER: True,
        ARTY_SPLASH.SHOW_MODE_ARTY: True,
        ARTY_SPLASH.MODEL_PATH_SPLASH: 'objects/artySplash.model',
        ARTY_SPLASH.MODEL_PATH_DOT: 'objects/artyDot.model'
    },
    AUTO_AIM_OPTIMIZE.ID: {
        GLOBAL.ENABLED: True,
        AUTO_AIM_OPTIMIZE.ANGLE: 1.3,
        AUTO_AIM_OPTIMIZE.CATCH_HIDDEN_TARGET: True,
        AUTO_AIM_OPTIMIZE.DISABLE_ARTY_MODE: True
    },
    BATTLE_EFFICIENCY.ID: {
        GLOBAL.ENABLED: True,
        BATTLE_EFFICIENCY.COLOR_RATTING: 0,
        BATTLE_EFFICIENCY.FORMAT: "WN8: <font color='{c:wn8}'>{wn8}</font> EFF: <font color='{c:eff}'>{eff}</font>DIFF: <font color='{c:diff}'>{diff}</font>",
        BATTLE_EFFICIENCY.TEXT_STYLE: {GLOBAL.FONT: '$TitleFont', GLOBAL.COLOR: '#FFFFFF', GLOBAL.SIZE: 16, GLOBAL.ALIGN: GLOBAL.CENTER},
        BATTLE_EFFICIENCY.TEXT_LOCK: False,
        BATTLE_EFFICIENCY.POSITION: {GLOBAL.X: 125, GLOBAL.Y: 36},
        BATTLE_EFFICIENCY.TEXT_SHADOW: {GLOBAL.ENABLED: True, GLOBAL.DISTANCE: 0, GLOBAL.ANGLE: 90, GLOBAL.COLOR: '#000000', GLOBAL.ALPHA: 0.8, GLOBAL.BLUR_X: 2, GLOBAL.BLUR_Y: 2, GLOBAL.STRENGTH: 2, GLOBAL.QUALITY: 4},
        BATTLE_EFFICIENCY.BATTLE_RESULTS_WINDOW: True,
        BATTLE_EFFICIENCY.BATTLE_RESULTS_FORMAT: "<textformat leading='-2' tabstops='[0, 300]'>\t<font color='#FFFFFF' size='15'>{mapName} | {battleType} | WN8:<font color='{c:wn8}'>{wn8}</font> | EFF:<font color='{c:eff}'>{eff}</font> | Xte:<font color='{c:xte}'>{xte}</font></font></textformat>"
    },
    BATTLE_OPTIONS.ID: {
        GLOBAL.ENABLED: True,
        BATTLE_OPTIONS.CLIP_LOAD: True,
        GLOBAL.COLOR: 'FF002A',
        BATTLE_OPTIONS.DIRECTIVES_ONLY_FROM_STORAGE: False,
        BATTLE_OPTIONS.DISABLE_SOUND_COMMANDER: False,
        BATTLE_OPTIONS.FORMAT: "<font face='$FieldFont' size='16' color='#FFFFFF'>%H:%M:%S</font>",
        BATTLE_OPTIONS.HIDE_BADGES: False,
        BATTLE_OPTIONS.HIDE_BATTLE_PRESTIGE: False,
        BATTLE_OPTIONS.HIDE_CLAN_NAME: False,
        BATTLE_OPTIONS.IN_BATTLE: True,
        BATTLE_OPTIONS.LOAD_TXT: 'Reloading at {pos}, for {load} seconds.',
        BATTLE_OPTIONS.MAX_CHAT_LINES: 6,
        BATTLE_OPTIONS.MUTE_TEAM_BASE_SOUND: False,
        BATTLE_OPTIONS.POSTMORTEM_TIPS: True,
        BATTLE_OPTIONS.SHOW_ANONYMOUS: False,
        BATTLE_OPTIONS.SHOW_BATTLE_HINT: False,
        BATTLE_OPTIONS.SHOW_FRIENDS: False,
        BATTLE_OPTIONS.SHOW_POSTMORTEM_DOG_TAG: True,
        BATTLE_OPTIONS.STUN_SOUND: False,
        BATTLE_OPTIONS.SHOW_PLAYER_SATISFACTION_WIDGET: False,
        BATTLE_OPTIONS.ADD_ENEMY_NAME: True,
        BATTLE_OPTIONS.HIDE_HINT: True
    },
    BATTLE_STAT.ID: {
        GLOBAL.ENABLED: True,
        BATTLE_STAT.COLOR_RATING: 0,
        BATTLE_STAT.FORMAT: '{header}: {allyChance} {compareSign} {enemyChance}',
        BATTLE_STAT.TEXT_LOCK: False,
        BATTLE_STAT.TEXT_POSITION: {GLOBAL.ALIGN_X: GLOBAL.RIGHT, GLOBAL.ALIGN_Y: GLOBAL.TOP, GLOBAL.X: -250, GLOBAL.Y: 443},
        BATTLE_STAT.TEXT_SHADOW: {GLOBAL.ENABLED: True, GLOBAL.DISTANCE: 0, GLOBAL.ANGLE: 90, GLOBAL.COLOR: '#000000', GLOBAL.ALPHA: 1, GLOBAL.BLUR_X: 2, GLOBAL.BLUR_Y: 2, GLOBAL.STRENGTH: 100, GLOBAL.QUALITY: 1},
        BATTLE_STAT.TEXT_FORMAT: {GLOBAL.FONT: '$FieldFont', GLOBAL.SIZE: 16, 'bold': False, 'italic': False, GLOBAL.COLOR: '#DBD7D2'}
    },
    DISPERSION_CIRCLE.ID: {
        GLOBAL.ENABLED: True,
        DISPERSION_CIRCLE.SHOW_CLIENT_AND_SERVER_RETICLE: False,
        DISPERSION_CIRCLE.GUN_MARKER_MINIMUM_SIZE: 0,
        DISPERSION_CIRCLE.PERCENT_CORRECTION: 100,
        DISPERSION_CIRCLE.SHOW_CLIENT_AND_SERVER_RETICLE_BETA: False,
        DISPERSION_CIRCLE.SHOW_SERVER_SPG_STRATEGIC_RETICLE: False,
        DISPERSION_CIRCLE.SERVER_RETICLE_AIMING_CIRCLE_SHAPE: 0,
        DISPERSION_CIRCLE.SERVER_RETICLE_AIMING_CIRCLE_OPACITY: 50,
        DISPERSION_CIRCLE.SERVER_RETICLE_GUN_MARKER_SHAPE: 0,
        DISPERSION_CIRCLE.SERVER_RETICLE_GUN_MARKER_OPACITY: 50
    },
    DISPERSION_TIMER.ID: {
        GLOBAL.ENABLED: True,
        GLOBAL.ALIGN: 'left',
        DISPERSION_TIMER.RED: 'FE0E00',
        DISPERSION_TIMER.ORANGE: 'FE7903',
        DISPERSION_TIMER.YELLOW: 'F8F400',
        DISPERSION_TIMER.GREEN: 'A6FFA6',
        DISPERSION_TIMER.BLUE: '02C9B3',
        DISPERSION_TIMER.PURPLE: 'D042F3',
        DISPERSION_TIMER.TEMPLATE: "<font color='#%(color)s'>%(timer).1fs. - %(percent)d%%</font>",
        GLOBAL.X: 60,
        GLOBAL.Y: 110,
        GLOBAL.ALIGN_X: GLOBAL.CENTER,
        GLOBAL.ALIGN_Y: GLOBAL.CENTER
    },
    DISTANCE_MARKER.ID: {
        GLOBAL.ENABLED: True,
        DISTANCE_MARKER.DISPLAY_MODE: 0,
        DISTANCE_MARKER.MARKER_TARGET: 1,
        DISTANCE_MARKER.ANCHOR_POSITION: 0,
        DISTANCE_MARKER.LOCK_POSITION_OFFSETS: False,
        DISTANCE_MARKER.ANCHOR_HORIZONTAL_OFFSET: 24,
        DISTANCE_MARKER.ANCHOR_VERTICAL_OFFSET: 16,
        DISTANCE_MARKER.DECIMAL_PRECISION: 0,
        DISTANCE_MARKER.TEXT_SIZE: 11,
        DISTANCE_MARKER.TEXT_COLOR: 'FFFFFF',
        DISTANCE_MARKER.TEXT_ALPHA: 1.0,
        DISTANCE_MARKER.DRAW_TEXT_SHADOW: True
    },
    FLIGHT_TIMER.ID: {
        GLOBAL.ENABLED: True,
        GLOBAL.ALIGN: GLOBAL.LEFT,
        FLIGHT_TIMER.SPG_ONLY: False,
        FLIGHT_TIMER.TEMPLATE: "<font color='#f5ff8f'>%(flightTime).1fs. - %(distance)dm.</font>",
        GLOBAL.X: 100,
        GLOBAL.Y: 100,
        GLOBAL.ALIGN_X: GLOBAL.CENTER,
        GLOBAL.ALIGN_Y: GLOBAL.CENTER
    },
    INFO_PANEL.ID: {
        GLOBAL.ENABLED: True,
        INFO_PANEL.ALIVE_ONLY: False,
        INFO_PANEL.ALT_KEY: ['KEY_LALT'],
        INFO_PANEL.COMPARE_VALUES: {
            'equal': {GLOBAL.COLOR: '#FFFFFF', 'delim': '='},
            'lessThan': {GLOBAL.COLOR: '#00FF00', 'delim': '&lt;'},
            'moreThan': {GLOBAL.COLOR: '#FF0000', 'delim': '&gt;'}
        },
        INFO_PANEL.DELAY: 5,
        INFO_PANEL.TEMPLATE_PRESET: 3,
        INFO_PANEL.FORMATS: [
            "{{vehicle_name}}<br/>{{gun_reload_equip}} s"
            "<br/><img src='img://gui/maps/icons/vehicle/{{icon_system_name}}.png'>"
            "<br/><textformat tabstops='[95]'>Massa: {{vehicle_weight}} t<tab>Visão: {{vision_radius}} m</textformat>"
            "<br/><textformat tabstops='[65,105,145]'>Casco:<tab>{{armor_hull_front}}<tab>{{armor_hull_side}}<tab>{{armor_hull_back}}</textformat>"
            "<br/><textformat tabstops='[65,105,145]'>Torre:<tab>{{armor_turret_front}}<tab>{{armor_turret_side}}<tab>{{armor_turret_back}}</textformat>"
            "<br/><textformat tabstops='[65,105,145]'>Tipo:<tab>{{shell_type_1}}<tab>{{shell_type_2}}<tab>{{shell_type_3}}</textformat>"
            "<br/><textformat tabstops='[65,105,145]'>Penetração:<tab>{{shell_power_1}}<tab>{{shell_power_2}}<tab>{{shell_power_3}}</textformat>"
            "<br/><textformat tabstops='[65,105,145]'>Dano:<tab>{{shell_damage_1}}<tab>{{shell_damage_2}}<tab>{{shell_damage_3}}</textformat>"
        ],
        INFO_PANEL.SHOW_FOR: 0,
        INFO_PANEL.TEXT_LOCK: False,
        INFO_PANEL.TEXT_POSITION: {GLOBAL.X: -110, GLOBAL.Y: 150, 'alignX': GLOBAL.CENTER, 'alignY': GLOBAL.CENTER, GLOBAL.WIDTH: 250, GLOBAL.HEIGHT: 250},
        INFO_PANEL.TEXT_FORMAT: {GLOBAL.FONT: '$FieldFont', GLOBAL.SIZE: 14, GLOBAL.COLOR: '#FCFCFC', GLOBAL.ALIGN: GLOBAL.LEFT, GLOBAL.LEADING: 0},
        INFO_PANEL.TEXT_SHADOW: {GLOBAL.ALPHA: 0.8, GLOBAL.ANGLE: 90, GLOBAL.BLUR_X: 5, GLOBAL.BLUR_Y: 5, GLOBAL.COLOR: '#000000', GLOBAL.DISTANCE: 1, GLOBAL.QUALITY: 2, GLOBAL.STRENGTH: 2},
        INFO_PANEL.BACKGROUND_ENABLED: False,
        INFO_PANEL.BACKGROUND_ALPHA: 0.78
    },
    MAIN_GUN.ID: {
        GLOBAL.ENABLED: True,
        MAIN_GUN.BACK_GROUND_ENABLED: False,
        MAIN_GUN.TEXT_LOCK: False,
        MAIN_GUN.FORMAT: '<font size="16" face="$FieldFont"><b>{mainGun}</b></font>',
        MAIN_GUN.BACKGROUND: {GLOBAL.WIDTH: 200, GLOBAL.HEIGHT: 50, GLOBAL.ALPHA: 80, GLOBAL.IMAGE: '../maps/Driftkings/MainGun/bg.png'},
        MAIN_GUN.MAIN_GUN: {
            GLOBAL.ENABLED: True,
            'dynamic': True,
            'format': "{mainGunIcon}{mainGunDoneIcon}{mainGunFailureIcon} <font color='#E0E06D'>{mainGun}</font>",
            'mainGunDoneIcon': "<img src='img://gui/maps/icons/library/done.png' width='32' height='32' vspace='-8'>",
            'mainGunFailureIcon': "<img src='img://gui/maps/icons/library/icon_alert_32x32.png' width='32' height='32' vspace='-8'>",
            'mainGunIcon': "<img src='img://gui/maps/icons/achievement/32x32/mainGun.png' width='32' height='32' vspace='-8'>"
        },
        MAIN_GUN.SHADOW: {GLOBAL.ENABLED: True, GLOBAL.DISTANCE: GLOBAL.ZERO, GLOBAL.ANGLE: 90, GLOBAL.COLOR: '#000000', GLOBAL.ALPHA: 0.8, GLOBAL.BLUR_X: 2, GLOBAL.BLUR_Y: 2, GLOBAL.STRENGTH: 2, GLOBAL.QUALITY: 4},
        MAIN_GUN.TEXT_POSITION: {GLOBAL.ALIGN_X: GLOBAL.LEFT, GLOBAL.ALIGN_Y: GLOBAL.TOP, GLOBAL.X: 200, GLOBAL.Y: 200}
    },
    MARKS_ON_GUN_BATTLE.ID: {
        'displayMode': 0, 'showMarks': True, 'showDelta': True,
        'showDamage': True, 'showProgress': True, 'showTargets': True,
        GLOBAL.ENABLED: True,
        MARKS_ON_GUN_BATTLE.COLOR_RATING: 0,
        MARKS_ON_GUN_BATTLE.BUTTON_SHOW: ['KEY_NUMPAD9', ['KEY_LALT', 'KEY_RALT']],
        MARKS_ON_GUN_BATTLE.BUTTON_SIZE_UP: ['KEY_PGUP', ['KEY_LALT', 'KEY_RALT']],
        MARKS_ON_GUN_BATTLE.BUTTON_SIZE_DOWN: ['KEY_PGDN', ['KEY_LALT', 'KEY_RALT']],
        MARKS_ON_GUN_BATTLE.BUTTON_RESET: ['KEY_DELETE', ['KEY_LCONTROL', 'KEY_RCONTROL'], ['KEY_LSHIFT', 'KEY_RSHIFT']],
        MARKS_ON_GUN_BATTLE.SHOW_IN_BATTLE: False,
        MARKS_ON_GUN_BATTLE.SHOW_IN_BATTLE_HALF_PERCENTS: False,
        MARKS_ON_GUN_BATTLE.SHOW_IN_REPLAY: True,
        MARKS_ON_GUN_BATTLE.SHOW_IN_STATISTIC: True,
        MARKS_ON_GUN_BATTLE.SHOW_IN_HANGAR: True,
        GLOBAL.FONT: '$FieldFont',
        MARKS_ON_GUN_BATTLE.BACKGROUND: True,
        MARKS_ON_GUN_BATTLE.PANEL_SIZE: {'widthAlt': 183.0, 'heightAlt': 80.0, 'widthNormal': 183.0, 'heightNormal': 50.0},
        MARKS_ON_GUN_BATTLE.PANEL: {
            GLOBAL.INDEX: 10000, GLOBAL.X: 230.0, GLOBAL.Y: -226.0, GLOBAL.WIDTH: 183.0,
            GLOBAL.HEIGHT: 50.0, GLOBAL.DRAG: True, GLOBAL.BORDER: True, 'alignX': GLOBAL.LEFT,
            'alignY': GLOBAL.BOTTOM, GLOBAL.VISIBLE: True, GLOBAL.ALPHA: 1.0,
            GLOBAL.SHADOW: {GLOBAL.DISTANCE: GLOBAL.ZERO, GLOBAL.ANGLE: GLOBAL.ZERO, GLOBAL.COLOR: GLOBAL.ZERO, GLOBAL.ALPHA: 90, GLOBAL.BLUR_X: GLOBAL.ONE, GLOBAL.BLUR_Y: GLOBAL.ONE, GLOBAL.STRENGTH: 3000, GLOBAL.QUALITY: GLOBAL.ONE}
        },
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE: '<font size="14">{currentMarkOfGun}</font> <font size="10">{damageCurrentPercent}</font><font size="14"> ~ {c_nextMarkOfGun}</font> <font size="10">{c_damageNextPercent}</font><BR><font size="20">{c_battleMarkOfGun}{status}</font><font size="14">{c_damageCurrent}</font>',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_ALT: '<font size="14">{currentMarkOfGun}</font> <font size="10">{damageCurrentPercent}</font><font size="14"> ~ {c_nextMarkOfGun}</font> <font size="10">{c_damageNextPercent}</font><BR><font size="20">{c_battleMarkOfGun}{status}</font><font size="14">{c_damageCurrent}</font><BR>{c_damageToMark65}{c_damageToMark85}<BR>{c_damageToMark95}{c_damageToMark100}',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_STATUS_UP: '<img src="img://gui/maps/icons/messenger/status/24x24/chat_icon_user_is_online.png" vspace="-5"/> ',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_C_STATUS_UP: '+',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_STATUS_DOWN: '<img src="img://gui/maps/icons/messenger/status/24x24/chat_icon_user_is_busy.png" vspace="-5"/>',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_C_STATUS_DOWN: '-',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_STATUS_UNKNOWN: '<img src="img://gui/maps/icons/messenger/status/24x24/chat_icon_user_is_busy_violet.png" vspace="-5"/>',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_C_STATUS_UNKNOWN: '~',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_BATTLE_MARK_OF_GUN: '%.2f%%',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_C_BATTLE_MARK_OF_GUN: '%s',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_CURRENT_MARK_OF_GUN: '%.2f%%',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_C_CURRENT_MARK_OF_GUN: '%s',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_NEXT_MARK_OF_GUN: '%.1f%%',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_C_NEXT_MARK_OF_GUN: '%s',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_DAMAGE_CURRENT: '[<b>%.0f</b>]',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_C_DAMAGE_CURRENT: '%s',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_DAMAGE_CURRENT_PERCENT: '[<b>%.0f</b>]',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_C_DAMAGE_CURRENT_PERCENT: '%s',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_DAMAGE_NEXT_PERCENT: '[<b>%.0f</b>]',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_C_DAMAGE_NEXT_PERCENT: '%s',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_DAMAGE_TO_MARK65: '<b>65%%:%.0f</b>, ',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_C_DAMAGE_TO_MARK65: '%s',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_DAMAGE_TO_MARK85: '<b>85%%:%.0f</b>',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_C_DAMAGE_TO_MARK85: '%s',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_DAMAGE_TO_MARK95: '<b>95%%:%.0f</b>, ',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_C_DAMAGE_TO_MARK95: '%s',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_DAMAGE_TO_MARK100: '<b>100%%:%.0f</b>',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_C_DAMAGE_TO_MARK100: '%s',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_DAMAGE_TO_MARK_INFO: '%s',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_C_DAMAGE_TO_MARK_INFO: '%s',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_DAMAGE_TO_MARK_INFO_LEVEL: '%s%%',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_C_DAMAGE_TO_MARK_INFO_LEVEL: '%s',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_SIZE_IN_PERCENT: 100,
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_ASSIST_SPOT: '<img src="img://gui/maps/icons/library/efficiency/48x48/detection.png" width="16" height="16" vspace="-5"/>',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_ASSIST_TRACK: '<img src="img://gui/maps/icons/library/efficiency/48x48/immobilized.png" width="16" height="16" vspace="-5"/>',
        MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_ASSIST_SPAM: '<img src="img://gui/maps/icons/library/efficiency/48x48/stun.png" width="16" height="16" vspace="-5"/>',
        MARKS_ON_GUN_BATTLE.UI: 10
    },
    MINIMAP_PLUGINS.ID: {
        GLOBAL.ENABLED: True,
        MINIMAP_PLUGINS.MINIMAP_SCHEMA: GLOBAL.ZERO,
        MINIMAP_PLUGINS.PERMANENT_MINIMAP_DEATH: False,
        MINIMAP_PLUGINS.YAW: True,
        MINIMAP_PLUGINS.SHOW_NAMES: True,
        MINIMAP_PLUGINS.VIEW_RADIUS: True,
        MINIMAP_PLUGINS.ZOOM_FACTOR: 1.1,
        MINIMAP_PLUGINS.ZOOM_FACTOR_MAX: 2.0,
        MINIMAP_PLUGINS.BUTTON: ['KEY_LCONTROL'],
        GLOBAL.ALPHA: 90,
        MINIMAP_PLUGINS.CHANGE_COLOR_CIRCLES: True,
        MINIMAP_PLUGINS.COLOR_DRAW_CIRCLE: '2B28D1',
        MINIMAP_PLUGINS.COLOR_MAX_VIEW_CIRCLE: 'E02810',
        MINIMAP_PLUGINS.COLOR_MIN_SPOTTING_CIRCLE: '35DE46',
        MINIMAP_PLUGINS.COLOR_VIEW_CIRCLE: 'FF7FFF',
        MINIMAP_PLUGINS.SHOW_LAST_POSITIONS: True,
        MINIMAP_PLUGINS.LAST_POSITION_DURATION: 30,
        MINIMAP_PLUGINS.SHOW_VEHICLE_TYPES: True,
        MINIMAP_PLUGINS.LABELS: {
            GLOBAL.ENABLED: True, 'normal': '{{vehicle}}', 'alternative': '{{vehicle}} · {{name%.16s}}', 'dead': '{{vehicle}}', 'lost': '{{vehicle}}',
            'fontSize': 10, GLOBAL.ALPHA: 100, GLOBAL.X: 0, GLOBAL.Y: 0, GLOBAL.ALIGN: GLOBAL.LEFT, GLOBAL.SHADOW: True, 'customColors': False,
            'allyColor': '80D639', 'enemyColor': 'F05050', 'squadColor': 'FFB964', 'deadColor': '999999', 'ally': '', 'enemy': '', 'squad': '',
            'alternativeAlly': '', 'alternativeEnemy': '', 'alternativeSquad': '', 'avoidOverlap': False, 'compactLength': 14
        },
        MINIMAP_PLUGINS.ICONS: {'scale': 1.0, GLOBAL.ALPHA: 100, 'selfScale': 1.0, 'selfAlpha': 100, 'selfColor': 'FFFFFF'},
        MINIMAP_PLUGINS.HEALTH: {'visibility': 'never', 'mode': 'value', GLOBAL.X: 0, GLOBAL.Y: 12, GLOBAL.WIDTH: 30, GLOBAL.HEIGHT: 3, 'fontSize': 9},
        MINIMAP_PLUGINS.LOST_MARKER: {'showSeconds': False, 'fade': False, 'minimumAlpha': 25},
        MINIMAP_PLUGINS.MAP_SIZE: {GLOBAL.ENABLED: False, GLOBAL.X: 5, GLOBAL.Y: 5, 'fontSize': 11, GLOBAL.COLOR: 'FFFFFF', 'format': '{{width}} x {{height}} m'},
        MINIMAP_PLUGINS.CIRCLES: {
            'draw': {'mode': 'client', GLOBAL.ALPHA: 90, 'thickness': 1, 'dash': 0, 'gap': 5},
            'maxView': {'mode': 'client', GLOBAL.ALPHA: 90, 'thickness': 1, 'dash': 0, 'gap': 5},
            'proximity': {'mode': 'client', GLOBAL.ALPHA: 90, 'thickness': 1, 'dash': 0, 'gap': 5},
            'view': {'mode': 'client', GLOBAL.ALPHA: 90, 'thickness': 1, 'dash': 0, 'gap': 5}
        },
        MINIMAP_PLUGINS.EXTRA_CIRCLES: [],
        MINIMAP_PLUGINS.LINES: {'direction': 'client', 'sector': 'client', 'customStyle': False, 'directionColor': 'F2BB35', 'sectorColor': 'FFFFFF', 'alpha': 80, 'geometry': False, 'thickness': 1, 'length': 500, 'dash': 18, 'gap': 5},
        MINIMAP_PLUGINS.ARTILLERY_AIM: {GLOBAL.ENABLED: True, 'scale': 50, 'src': 'gui/maps/Driftkings/Minimap/MinimapAim_0.png', GLOBAL.ALPHA: 100},
        MINIMAP_PLUGINS.PRESENTATION: {'alternativeEnabled': True, 'zoom': True, GLOBAL.CENTER: True, 'sizeIndex': 5, 'backgroundAlpha': 100, 'normalAlpha': 100, 'alternativeAlpha': 100}
    },
    OWN_HEALTH.ID: {
        GLOBAL.ENABLED: True,
        GLOBAL.X: 0,
        GLOBAL.Y: -55,
        GLOBAL.ALIGN_X: GLOBAL.CENTER,
        GLOBAL.ALIGN_Y: GLOBAL.BOTTOM,
        OWN_HEALTH.AVG_COLOR: {'brightness': 0.9, 'saturation': 0.7},
        OWN_HEALTH.COLORS: {'ally': '#60CB00', 'bgColor': '#000000', 'enemy': '#ED070A', 'enemyColorBlind': '#6F6CD3'}
    },
    PLAYER_PANEL_PRO.ID: {
        GLOBAL.ENABLED: True,
        PLAYER_PANEL_PRO.STATS_ENABLED: True,
        PLAYER_PANEL_PRO.COLOR_SCALE: 0,
        PLAYER_PANEL_PRO.RATING: 'wn8',
        PLAYER_PANEL_PRO.PERFORMANCE: {'cacheEnabled': True, 'cacheExpiry': 3600, 'minBattlesToShow': 10, 'requestTimeout': 5, 'diagnostics': False},
        PLAYER_PANEL_PRO.HP_ENABLED: True,
        PLAYER_PANEL_PRO.HP_VISIBILITY: 'always',
        PLAYER_PANEL_PRO.HP_KEY: [[56, 184]],
        PLAYER_PANEL_PRO.SPOTTED_ENABLED: True,
        PLAYER_PANEL_PRO.SCHEMA_VERSION: 2,
        PLAYER_PANEL_PRO.PLAYERS_PANEL: {GLOBAL.ENABLED: True, GLOBAL.ALPHA: 80, 'iconAlpha': 100, 'removeSelectedBackground': False, 'removePanelsModeSwitcher': False, 'removeHealthPoints': True, 'startMode': 'medium2', 'altMode': None, 'showUnavailable': True},
        PLAYER_PANEL_PRO.PROFILES: {
            'none': {
                GLOBAL.ENABLED: True,
                'expandAreaWidth': 230,
                'layout': 'vertical',
                'fixedPosition': False,
                'inviteIndicatorAlpha': 100,
                'inviteIndicatorX': 0,
                'inviteIndicatorY': 0,
                'extraFields': {
                    'leftPanel': {GLOBAL.X: GLOBAL.ZERO, GLOBAL.Y: 65, GLOBAL.WIDTH: 350, GLOBAL.HEIGHT: 25, 'formats': []},
                     'rightPanel': {GLOBAL.X: GLOBAL.ZERO, GLOBAL.Y: 65, GLOBAL.WIDTH: 350, GLOBAL.HEIGHT: 25, 'formats': []}
                }
            },
            'short': {
                GLOBAL.ENABLED: True,
                'standardFields': ['frags'],
                'expandAreaWidth': 230,
                'removeSquadIcon': False,
                'squadIconAlpha': 100,
                'vehicleIconOffsetXLeft': GLOBAL.ZERO,
                'vehicleIconOffsetXRight': GLOBAL.ZERO,
                'vehicleLevelOffsetXLeft': GLOBAL.ZERO,
                'vehicleLevelOffsetXRight': GLOBAL.ZERO,
                'vehicleLevelAlpha': 100,
                'fragsOffsetXLeft': GLOBAL.ZERO,
                'fragsOffsetXRight': GLOBAL.ZERO,
                'fragsWidth': 24,
                'fragsFormatLeft': '{{frags}}',
                'fragsFormatRight': '{{frags}}',
                'fragsShadowLeft': None,
                'fragsShadowRight': None,
                'badgeOffsetXLeft': GLOBAL.ZERO,
                'badgeOffsetXRight': GLOBAL.ZERO,
                'badgeWidth': 24,
                'badgeAlpha': '{{alive?100|70}}',
                'nickOffsetXLeft': GLOBAL.ZERO,
                'nickOffsetXRight': GLOBAL.ZERO,
                'nickMinWidth': 46,
                'nickMaxWidth': 158,
                'nickFormatLeft': "<font face='$FieldFont' size='{{xvm-stat?13|0}}' color='{{c:xr}}' alpha='{{alive?#FF|#80}}'>{{r}}</font> {{name%.{{anonym?13|15}}s~..}}{{anonym? <font face='$FieldFont' size='19'>*</font>}}<font alpha='#A0'>{{clan}}</font>",
                'nickFormatRight': "<font alpha='#A0'>{{clan}}</font>{{name%.15s~..}} <font face='$FieldFont' size='{{xvm-stat?13|0}}' color='{{c:xr}}' alpha='{{alive?#FF|#80}}'>{{r}}</font>",
                'nickShadowLeft': None,
                'nickShadowRight': None,
                'prestigeOffsetXLeft': GLOBAL.ZERO,
                'prestigeOffsetXRight': GLOBAL.ZERO,
                'vehicleOffsetXLeft': GLOBAL.ZERO,
                'vehicleOffsetXRight': GLOBAL.ZERO,
                'vehicleWidth': 72,
                'vehicleFormatLeft': '{{vehicle}}',
                'vehicleFormatRight': '{{vehicle}}',
                'vehicleShadowLeft': None,
                'vehicleShadowRight': None,
                'removeSpottedIndicator': True,
                'spottedIndicatorAlpha': 100,
                'spottedIndicatorOffsetX': GLOBAL.ZERO,
                'spottedIndicatorOffsetY': GLOBAL.ZERO,
                'fixedPosition': False,
                'extraFieldsLeft': [{'ref': 'hpBarBg'}, {'ref': 'hpBar'}, {'ref': 'hp'}],
                'extraFieldsRight': [{'ref': 'hpBarBg'}, {'ref': 'hpBar'}, {'ref': 'hp'}, {'ref': 'enemySpottedMarker'}]
            },
            'medium': {
                'enabled': True,
                'standardFields': ['frags', 'badge', 'nick'],
                'expandAreaWidth': 230,
                'removeSquadIcon': False,
                'squadIconAlpha': 100,
                'vehicleIconOffsetXLeft': GLOBAL.ZERO,
                'vehicleIconOffsetXRight': GLOBAL.ZERO,
                'vehicleLevelOffsetXLeft': GLOBAL.ZERO,
                'vehicleLevelOffsetXRight': GLOBAL.ZERO,
                'vehicleLevelAlpha': 100,
                'fragsOffsetXLeft': GLOBAL.ZERO,
                'fragsOffsetXRight': GLOBAL.ZERO,
                'fragsWidth': 24,
                'fragsFormatLeft': '{{frags}}',
                'fragsFormatRight': '{{frags}}',
                'fragsShadowLeft': None,
                'fragsShadowRight': None,
                'badgeOffsetXLeft': GLOBAL.ZERO,
                'badgeOffsetXRight': GLOBAL.ZERO,
                'badgeWidth': 24,
                'badgeAlpha': '{{alive?100|70}}',
                'nickOffsetXLeft': GLOBAL.ZERO,
                'nickOffsetXRight': GLOBAL.ZERO,
                'nickMinWidth': 46,
                'nickMaxWidth': 158,
                'nickFormatLeft': "<font color='{{c:xr}}' alpha='{{alive?#FF|#80}}'>{{name%.{{anonym?10|12}}s~..}}</font>{{anonym?<font face='$FieldFont' size='19'>*</font>}} <font alpha='#A0'>{{clan}}</font>",
                'nickFormatRight': "<font alpha='#A0'>{{clan}}</font> <font color='{{c:xr}}' alpha='{{alive?#FF|#80}}'>{{name%.12s~..}}</font>",
                'nickShadowLeft': None,
                'nickShadowRight': None,
                'vehicleOffsetXLeft': GLOBAL.ZERO,
                'vehicleOffsetXRight': GLOBAL.ZERO,
                'vehicleWidth': 72,
                'vehicleFormatLeft': "<font color='{{c:xr}}' alpha='{{alive?#FF|#80}}'>{{vehicle}}</font>",
                'vehicleFormatRight': "<font color='{{c:xr}}' alpha='{{alive?#FF|#80}}'>{{vehicle}}</font>",
                'vehicleShadowLeft': None,
                'vehicleShadowRight': None,
                'removeSpottedIndicator': True,
                'spottedIndicatorAlpha': 100,
                'spottedIndicatorOffsetX': GLOBAL.ZERO,
                'spottedIndicatorOffsetY': GLOBAL.ZERO,
                'fixedPosition': False,
                'extraFieldsLeft': [{'ref': 'hpBarBg'}, {'ref': 'hpBar'}, {'ref': 'hp'}],
                'extraFieldsRight': [{'ref': 'hpBarBg'}, {'ref': 'hpBar'}, {'ref': 'hp'}, {'ref': 'enemySpottedMarker'}]
            },
            'medium2': {
                'enabled': True,
                'standardFields': ['frags', 'vehicle'],
                'expandAreaWidth': 230,
                'removeSquadIcon': False,
                'squadIconAlpha': 100,
                'vehicleIconOffsetXLeft': GLOBAL.ZERO,
                'vehicleIconOffsetXRight': GLOBAL.ZERO,
                'vehicleLevelOffsetXLeft': GLOBAL.ZERO,
                'vehicleLevelOffsetXRight': GLOBAL.ZERO,
                'vehicleLevelAlpha': 100,
                'fragsOffsetXLeft': GLOBAL.ZERO,
                'fragsOffsetXRight': GLOBAL.ZERO,
                'fragsWidth': 24,
                'fragsFormatLeft': '{{frags}}',
                'fragsFormatRight': '{{frags}}',
                'fragsShadowLeft': None,
                'fragsShadowRight': None,
                'badgeOffsetXLeft': GLOBAL.ZERO,
                'badgeOffsetXRight': GLOBAL.ZERO,
                'badgeWidth': 24,
                'badgeAlpha': '{{alive?100|70}}',
                'nickOffsetXLeft': GLOBAL.ZERO,
                'nickOffsetXRight': GLOBAL.ZERO,
                'nickMinWidth': 46,
                'nickMaxWidth': 158,
                'nickFormatLeft': "<font color='{{c:xr}}' alpha='{{alive?#FF|#80}}'>{{name%.{{anonym?10|12}}s~..}}{{anonym?<font face='$FieldFont' size='19'>*</font>}}</font> <font alpha='#A0'>{{clan}}</font>",
                'nickFormatRight': "<font alpha='#A0'>{{clan}}</font> <font color='{{c:xr}}' alpha='{{alive?#FF|#80}}'>{{name%.12s~..}}</font>",
                'nickShadowLeft': None,
                'nickShadowRight': None,
                'prestigeOffsetXLeft': GLOBAL.ZERO,
                'prestigeOffsetXRight': GLOBAL.ZERO,
                'vehicleOffsetXLeft': GLOBAL.ZERO,
                'vehicleOffsetXRight': GLOBAL.ZERO,
                'vehicleWidth': 72,
                'vehicleFormatLeft': "<font color='{{c:xr}}' alpha='{{alive?#FF|#80}}'>{{vehicle}}</font>",
                'vehicleFormatRight': "<font color='{{c:xr}}' alpha='{{alive?#FF|#80}}'>{{vehicle}}</font>",
                'vehicleShadowLeft': None,
                'vehicleShadowRight': None,
                'removeSpottedIndicator': True,
                'spottedIndicatorAlpha': 100,
                'spottedIndicatorOffsetX': GLOBAL.ZERO,
                'spottedIndicatorOffsetY': GLOBAL.ZERO,
                'fixedPosition': False,
                'extraFieldsLeft': [{'ref': 'hpBarBg'}, {'ref': 'hpBar'}, {'ref': 'hp'}],
                'extraFieldsRight': [{'ref': 'hpBarBg'}, {'ref': 'hpBar'}, {'ref': 'hp'}, {'ref': 'enemySpottedMarker'}]
            },
            'large': {
                GLOBAL.ENABLED: True,
                'standardFields': ['frags', 'badge', 'nick', 'vehicle'],
                'removeSquadIcon': False,
                'squadIconAlpha': 100,
                'vehicleIconOffsetXLeft': GLOBAL.ZERO,
                'vehicleIconOffsetXRight': GLOBAL.ZERO,
                'vehicleLevelOffsetXLeft': GLOBAL.ZERO,
                'vehicleLevelOffsetXRight': GLOBAL.ZERO,
                'vehicleLevelAlpha': 100,
                'fragsOffsetXLeft': GLOBAL.ZERO,
                'fragsOffsetXRight': GLOBAL.ZERO,
                'fragsWidth': 24,
                'fragsFormatLeft': '{{frags}}',
                'fragsFormatRight': '{{frags}}',
                'fragsShadowLeft': None,
                'fragsShadowRight': None,
                'badgeOffsetXLeft': GLOBAL.ZERO,
                'badgeOffsetXRight': GLOBAL.ZERO,
                'badgeWidth': 24,
                'badgeAlpha': '{{alive?100|70}}',
                'nickOffsetXLeft': GLOBAL.ZERO,
                'nickOffsetXRight': GLOBAL.ZERO,
                'nickMinWidth': 46,
                'nickMaxWidth': 158,
                'nickFormatLeft': "<font face='$FieldFont' size='{{xvm-stat?13|0}}' color='{{c:xr}}' alpha='{{alive?#FF|#80}}'>{{r|{{r_size>2?----|--}}}}</font> {{name%.{{anonym?12|{{xvm-stat?{{r_size>2?10|13}}|15}}}}s~..}}{{anonym? <font face='$FieldFont' size='13'>*</font>}}<font alpha='#A0'>{{clan}}</font>",
                'nickFormatRight': "<font alpha='#A0'>{{clan}}</font>{{name%.{{xvm-stat?{{r_size>2?10|13}}|15}}s~..}} <font face='$FieldFont' size='{{xvm-stat?13|0}}' color='{{c:xr}}' alpha='{{alive?#FF|#80}}'>{{r|{{r_size>2?----|--}}}}</font>",
                'nickShadowLeft': None,
                'nickShadowRight': None,
                'prestigeOffsetXLeft': GLOBAL.ZERO,
                'prestigeOffsetXRight': GLOBAL.ZERO,
                'vehicleOffsetXLeft': GLOBAL.ZERO,
                'vehicleOffsetXRight': GLOBAL.ZERO,
                'vehicleWidth': 72,
                'vehicleFormatLeft': '{{vehicle}}',
                'vehicleFormatRight': '{{vehicle}}',
                'vehicleShadowLeft': None,
                'vehicleShadowRight': None,
                'removeSpottedIndicator': True,
                'spottedIndicatorAlpha': 100,
                'spottedIndicatorOffsetX': GLOBAL.ZERO,
                'spottedIndicatorOffsetY': GLOBAL.ZERO,
                'fixedPosition': False,
                'extraFieldsLeft': [{'ref': 'hpBarBg'}, {'ref': 'hpBar'}, {'ref': 'hp'}],
                'extraFieldsRight': [{'ref': 'hpBarBg'}, {'ref': 'hpBar'}, {'ref': 'hp'}, {'ref': 'enemySpottedMarker'}]
            }
        },
        PLAYER_PANEL_PRO.TEMPLATES: {
            'enemySpottedMarker': {GLOBAL.ENABLED: '{{.spottedEnabled}}', GLOBAL.X: -38, GLOBAL.Y: GLOBAL.ZERO, GLOBAL.WIDTH: 22, GLOBAL.HEIGHT: 22, 'bindToIcon': True, 'src': 'img://gui/maps/Driftkings/PlayerPanelPro/spotted/{{alive?{{spotted|neverSeen}}|dead}}.png'},
            'hpBarBg': {GLOBAL.X: '{{ally?76|80}}', GLOBAL.Y: 4, GLOBAL.WIDTH: 70, GLOBAL.HEIGHT: 12, 'bindToIcon': True, 'src': 'img://gui/maps/Driftkings/PlayerPanelPro/hp/hp_bg.png'},
            'hpBar': {GLOBAL.ENABLED: '{{hp>0?true|false}}', GLOBAL.X: '{{ally?75|79}}', GLOBAL.Y: 3, GLOBAL.WIDTH: '{{hp-ratio:72}}', GLOBAL.HEIGHT: 14, 'bindToIcon': True, 'src': 'img://gui/maps/Driftkings/PlayerPanelPro/hp/hp_alive_{{ally?l|r}}.png'},
            'hp': {
                'bindToIcon': True,
                GLOBAL.X: '{{ally?75|79}}',
                GLOBAL.WIDTH: 72,
                GLOBAL.Y: 3,
                'textFormat': {GLOBAL.FONT: '$FieldFont', GLOBAL.SIZE: 11, GLOBAL.COLOR: '#FFFFFF', GLOBAL.ALIGN: GLOBAL.CENTER},
                'format': '{{hp}}/{{hp-max}}',
                'shadow': {GLOBAL.ENABLED: True, GLOBAL.COLOR: '#000000', GLOBAL.ALPHA: 90, GLOBAL.BLUR: 2, GLOBAL.STRENGTH: 2, GLOBAL.DISTANCE: 0, GLOBAL.ANGLE: 0}
            }
        },
        PLAYER_PANEL_PRO.LOADING: {
            'clockFormat': 'H:i:s',
            'removeSquadIcon': False,
            'removeRankBadgeIcon': False,
            'removeTesterIcon': False,
            'removePrestigeLevel': False,
            'vehicleIconAlpha': 100,
            'removeVehicleLevel': False,
            'removeVehicleTypeIcon': False,
            'nameFieldShowBorder': False,
            'vehicleFieldShowBorder': False,
            'squadIconOffsetXLeft': GLOBAL.ZERO,
            'squadIconOffsetXRight': GLOBAL.ZERO,
            'nameFieldOffsetXLeft': GLOBAL.ZERO,
            'nameFieldWidthDeltaLeft': GLOBAL.ZERO,
            'nameFieldOffsetXRight': GLOBAL.ZERO,
            'nameFieldWidthDeltaRight': GLOBAL.ZERO,
            'vehicleFieldOffsetXLeft': 26,
            'vehicleFieldWidthDeltaLeft': GLOBAL.ZERO,
            'vehicleFieldOffsetXRight': 23,
            'vehicleFieldWidthDeltaRight': GLOBAL.ZERO,
            'vehicleIconOffsetXLeft': 23,
            'vehicleIconOffsetXRight': 20,
            'darkenNotReadyIcon': True,
            'formatLeftNick': "{{name%.15s~..}} <font alpha='#A0'>{{clan}}</font>",
            'formatRightNick': "<font alpha='#A0'>{{clan}}</font> {{name%.15s~..}} ",
            'formatLeftVehicle': "{{vehicle}}<font face='$FieldFont' size='{{xvm-stat?13|0}}'> <font color='{{c:kb}}'>{{kb%2d~k|--k}}</font> <font color='{{c:xr}}'>{{r}}</font> <font color='{{c:winrate}}'>{{winrate%2d~%|--%}}</font></font>",
            'formatRightVehicle': "<font face='$FieldFont' size='{{xvm-stat?13|0}}'><font color='{{c:winrate}}'>{{winrate%2d~%|--%}}</font> <font color='{{c:xr}}'>{{r}}</font> <font color='{{c:kb}}'>{{kb%2d~k|--k}}</font> </font>{{vehicle}}",
            'extraFieldsLeft': [],
            'extraFieldsRight': [],
            GLOBAL.ENABLED: True,
            'showUnavailable': True
        },
        PLAYER_PANEL_PRO.TAB: {
            'removeSquadIcon': False,
            'removeRankBadgeIcon': False,
            'removeTesterIcon': False,
            'removePrestigeLevel': True,
            'vehicleIconAlpha': 100,
            'removeVehicleLevel': False,
            'removeVehicleTypeIcon': False,
            'removePlayerStatusIcon': False,
            'nameFieldShowBorder': False,
            'vehicleFieldShowBorder': False,
            'fragsFieldShowBorder': False,
            'squadIconOffsetXLeft': -1,
            'squadIconOffsetXRight': 0,
            'nameFieldOffsetXLeft': -15,
            'nameFieldOffsetXRight': -15,
            'nameFieldWidthLeft': 200,
            'nameFieldWidthRight': 200,
            'vehicleFieldOffsetXLeft': 55,
            'vehicleFieldOffsetXRight': 36,
            'vehicleFieldWidthLeft': 160,
            'vehicleFieldWidthRight': 160,
            'vehicleIconOffsetXLeft': 31,
            'vehicleIconOffsetXRight': 27,
            'prestigeOffsetXLeft': 26,
            'prestigeOffsetXRight': 26,
            'fragsFieldOffsetXLeft': 19,
            'fragsFieldOffsetXRight': 15,
            'fragsFieldWidthLeft': 30,
            'fragsFieldWidthRight': 30,
            'formatLeftNick': "{{name%.{{anonym?13|15}}s~..}}{{anonym?<font face='$FieldFont' size='13'><b>*</b></font>}} <font alpha='#A0'>{{clan}}</font>",
            'formatRightNick': "<font alpha='#A0'>{{clan}}</font> {{name%.15s~..}} ",
            'formatLeftVehicle': "{{vehicle}}<font face='$FieldFont' size='{{xvm-stat?13|0}}'> <font color='{{c:kb}}'>{{kb%2d~k|--k}}</font> <font color='{{c:xr}}'>{{r}}</font><font color='{{c:winrate}}'>{{winrate%2d~%|--%}}</font></font>",
            'formatRightVehicle': "<font face='$FieldFont' size='{{xvm-stat?13|0}}'><font color='{{c:winrate}}'>{{winrate%2d~%|--%}}</font> <font color='{{c:xr}}'>{{r}}</font> <font color='{{c:kb}}'>{{kb%2d~k|--k}}</font></font>{{vehicle}}",
            'formatLeftFrags': '{{frags}}',
            'formatRightFrags': '{{frags}}',
            'extraFieldsLeft': [],
            'extraFieldsRight': [],
            GLOBAL.ENABLED: True,
            'showUnavailable': True
        }
    },
    REPAIR_EXTENDED.ID: {
        GLOBAL.ENABLED: True,
        REPAIR_EXTENDED.BUTTON_CHASSIS: [['KEY_LALT', 'KEY_RALT']],
        REPAIR_EXTENDED.BUTTON_REPAIR: ['KEY_SPACE'],
        REPAIR_EXTENDED.AUTO_REPAIR: True,
        REPAIR_EXTENDED.REMOVE_STUN: True,
        REPAIR_EXTENDED.EXTINGUISH_FIRE: True,
        REPAIR_EXTENDED.HEAL_CREW: True,
        REPAIR_EXTENDED.REPAIR_DEVICES: True,
        REPAIR_EXTENDED.RESTORE_CHASSIS: False,
        REPAIR_EXTENDED.USE_GOLD_KITS: True,
        REPAIR_EXTENDED.TIMER_MIN: 0.3,
        REPAIR_EXTENDED.TIMER_MAX: 0.8,
        REPAIR_EXTENDED.REPAIR_PRIORITY: {
            'lightTank': {'medkit': ['driver', 'commander', 'gunner', 'loader'], 'repairkit': ['engine', 'ammoBay', 'gun', 'turretRotator', 'fuelTank']},
            'mediumTank': {'medkit': ['loader', 'driver', 'commander', 'gunner'], 'repairkit': ['turretRotator', 'engine', 'ammoBay', 'gun', 'fuelTank']},
            'heavyTank': {'medkit': ['commander', 'loader', 'gunner', 'driver'], 'repairkit': ['turretRotator', 'ammoBay', 'engine', 'gun', 'fuelTank']},
            'SPG': {'medkit': ['commander', 'loader', 'gunner', 'driver'],
            'repairkit': ['ammoBay', 'engine', 'gun', 'turretRotator', 'fuelTank']},
            'AT-SPG': {'medkit': ['loader', 'gunner', 'commander', 'driver'], 'repairkit': ['ammoBay', 'gun', 'engine', 'turretRotator', 'fuelTank']},
            'AllAvailableVariables': {'medkit': ['commander', 'gunner', 'driver', 'radioman', 'loader'], 'repairkit': ['engine', 'ammoBay', 'gun', 'turretRotator', 'chassis', 'surveyingDevice', 'radio', 'fuelTank', 'wheel']}
        }
    },
    SAFE_SHOT.ID: {
        GLOBAL.ENABLED: True,
        SAFE_SHOT.WASTE_SHOT_BLOCK: False,
        SAFE_SHOT.TEAM_SHOT_BLOCK: True,
        SAFE_SHOT.TEAM_KILLER_SHOT_UNBLOCK: False,
        SAFE_SHOT.DEAD_SHOT_BLOCK: True,
        SAFE_SHOT.DEAD_SHOT_BLOCK_TIME_OUT: 2,
        SAFE_SHOT.DISABLE_KEY: ['KEY_Q'],
        SAFE_SHOT.ACTIVATE_MESSAGE: True,
        SAFE_SHOT.TRIGGER_MESSAGE: True,
        SAFE_SHOT.CLIENT_MESSAGES: {'wasteShotBlockedMessage': 'Waste shot blocked!', 'teamShotBlockedMessage': 'Team shot blocked!', 'deadShotBlockedMessage': 'Dead shot blocked!'},
        SAFE_SHOT.CHAT_MESSAGES: '[{name} - {vehicle}], get out of the way!'
    },
    SERVER_TURRET_EXTENDED.ID: {
        GLOBAL.ENABLED: True,
        SERVER_TURRET_EXTENDED.ACTIVATE_MESSAGE: False,
        SERVER_TURRET_EXTENDED.FIX_ACCURACY_IN_MOVE: True,
        SERVER_TURRET_EXTENDED.SERVER_TURRET: False,
        SERVER_TURRET_EXTENDED.FIX_WHEEL_CRUISE_CONTROL: True,
        SERVER_TURRET_EXTENDED.AUTO_ACTIVATE_WHEEL_MODE: True,
        SERVER_TURRET_EXTENDED.MAX_WHEEL_MODE: True,
        SERVER_TURRET_EXTENDED.BUTTON_AUTO_MODE: ['KEY_R', ['KEY_LALT', 'KEY_RALT']],
        SERVER_TURRET_EXTENDED.BUTTON_MAX_MODE: ['KEY_R', ['KEY_LCONTROL', 'KEY_RCONTROL']]
    },
    SIXTH_SENSE.ID: {
        GLOBAL.ENABLED: True,
        SIXTH_SENSE.DEFAULT_ICON: True,
        SIXTH_SENSE.USER_ICON: 'mods/configs/Driftkings/SixthSense/SixthSenseIcon.png',
        SIXTH_SENSE.LAMP_SHOW_TIME: 10,
        SIXTH_SENSE.PLAY_TICK_SOUND: False,
        SIXTH_SENSE.USER_SOUND: True,
        SIXTH_SENSE.DEFAULT_ICON_NAME: GLOBAL.ZERO,
        SIXTH_SENSE.SIXTH_SENSE_SOUND: 'SixthSense_06',
        SIXTH_SENSE.SHOW_TIMER: True,
        SIXTH_SENSE.SHOW_TIMER_GRAPHICS: True,
        SIXTH_SENSE.SHOW_TIMER_GRAPHICS_COLOR: 'FFFFFF',
        SIXTH_SENSE.SHOW_TIMER_GRAPHICS_RADIUS: 45,
        SIXTH_SENSE.ICON_SIZE: 90,
        SIXTH_SENSE.SPOTTED_MESSAGE: True,
        SIXTH_SENSE.HELP_MESSAGE: False,
        SIXTH_SENSE.SPOTTED_TEXT: "I'm Spotted at %(pos)s!",
        SIXTH_SENSE.DELAY: 4
    },
    SPOTTED_EXTENDED_LIGHT.ID: {
        GLOBAL.ENABLED: True,
        SPOTTED_EXTENDED_LIGHT.SOUND: True,
        SPOTTED_EXTENDED_LIGHT.ICON_SIZE_X: 47,
        SPOTTED_EXTENDED_LIGHT.ICON_SIZE_Y: 16,
        SPOTTED_EXTENDED_LIGHT.SOUND_SPOTTED: 'enemy_sighted_for_team',
        SPOTTED_EXTENDED_LIGHT.SOUND_ASSIST: 'gun_intuition',
        SPOTTED_EXTENDED_LIGHT.MESSAGE_COLOR_SPOTTED: 'FF69B5',
        SPOTTED_EXTENDED_LIGHT.MESSAGE_COLOR_ASSIST_RADIO: '28F09C',
        SPOTTED_EXTENDED_LIGHT.MESSAGE_COLOR_ASSIST_TRACK: '00FF00',
        SPOTTED_EXTENDED_LIGHT.MESSAGE_COLOR_ASSIST_STUN: '00FFFF',
        SPOTTED_EXTENDED_LIGHT.SPOTTED: '{icons}{vehicles}',
        SPOTTED_EXTENDED_LIGHT.ASSIST_RADIO: '{icons}{vehicles}{damage}',
        SPOTTED_EXTENDED_LIGHT.ASSIST_TRACK: '{icons}{vehicles}{damage}',
        SPOTTED_EXTENDED_LIGHT.ASSIST_STUN: '{icons}{vehicles}{damage}'
    },
    ZOOM_EXTENDED.ID: {
        GLOBAL.ENABLED: True,
        ZOOM_EXTENDED.NO_BINOCULARS: False,
        ZOOM_EXTENDED.NO_FLASH_BANG: False,
        ZOOM_EXTENDED.NO_SHOCK_WAVE: False,
        ZOOM_EXTENDED.NO_SNIPER_DYNAMIC: False,
        ZOOM_EXTENDED.DISABLE_CAM_AFTER_SHOT: False,
        ZOOM_EXTENDED.DISABLE_CAM_AFTER_SHOT_LATENCY: 0.5,
        ZOOM_EXTENDED.DISABLE_CAM_AFTER_SHOT_SKIP_CLIP: True,
        ZOOM_EXTENDED.DYNAMIC_ZOOM: {GLOBAL.ENABLED: False, 'stepsOnly': False},
        ZOOM_EXTENDED.ZOOM_STEPS: {GLOBAL.ENABLED: True, 'steps': [4.0, 6.0, 8.0, 12.0, 16.0, 25.0, 30.0]}
    },
    ACCOUNT_MANAGER.ID: {},
    AUTO_CLAIM_CLAN.ID: {GLOBAL.ENABLED: True},
    CAROUSEL_STATS.ID: {
        GLOBAL.ENABLED: True,
        CAROUSEL_STATS.COLOR_RATING: GLOBAL.ZERO,
        CAROUSEL_STATS.SHOW_ICONS: True,
        CAROUSEL_STATS.CAROUSEL: {
            'backgroundAlpha': 55,
            'cellType': 'normal',
            'edgeFadeAlpha': 78,
            'enableLockBackground': False,
            'filters': {
                'bonus': {GLOBAL.ENABLED: True}, 'elite': {GLOBAL.ENABLED: True},
                'favorite': {GLOBAL.ENABLED: True},
                'params': {GLOBAL.ENABLED: True},
                'premium': {GLOBAL.ENABLED: True}
            },
            'filtersPadding': {'horizontal': 11, 'vertical': 13},
            'hideBuySlot': True,
            'hideBuyTank': False,
            'hideRestoreTank': True,
            'nations_order': ['ussr', 'germany', 'usa', 'china', 'france', 'uk', 'japan', 'czech', 'poland', 'sweden', 'italy'],
            'rows': 2,
            'scrollingSpeed': 1,
            'showTotalSlots': True,
            'showUsedSlots': True,
            'slotBackgroundAlpha': 100,
            'slotBorderAlpha': 89,
            'slotSelectedBorderAlpha': 100,
            'sorting_criteria': ['nation', 'type', 'level'],
            'suppressCarouselTooltips': False,
            'types_order': ['lightTank', 'mediumTank', 'heavyTank', 'AT-SPG', 'SPG'],
            'normal': {
                'textFieldShadow': {GLOBAL.ENABLED: True, GLOBAL.COLOR: '#000000', GLOBAL.ALPHA: 80, GLOBAL.BLUR: 2, GLOBAL.STRENGTH: 2, GLOBAL.DISTANCE: 0, GLOBAL.ANGLE: 0},
                'extraFields': [
                    {GLOBAL.X: 140, GLOBAL.Y: 18, GLOBAL.ALPHA: '{{v.battles?100|0}}', 'format': "<img src='mods/Driftkings/Carroucel/battles.png' width='13' height='13'>", GLOBAL.SHADOW: '$ref:textFieldShadow'},
                    {GLOBAL.X: 140, GLOBAL.Y: 15, GLOBAL.ALIGN: GLOBAL.RIGHT, 'format': "<font face='mono' size='12' color='{{v.c_battles}}'><b>{{v.battles}}</b></font>", GLOBAL.SHADOW: '$ref:textFieldShadow'},
                    {GLOBAL.X: 140, GLOBAL.Y: 33, GLOBAL.ALPHA: '{{v.winrate?100|0}}', 'format': "<img src='mods/Driftkings/Carroucel/wins.png' width='13' height='13'>", GLOBAL.SHADOW: '$ref:textFieldShadow'},
                    {GLOBAL.X: 140, GLOBAL.Y: 30, GLOBAL.ALIGN: GLOBAL.RIGHT, 'format': "<b><font face='mono' size='12' color='{{v.c_winrate|#CFCFCF}}'>{{v.winrate%2d~%}}</font></b>", GLOBAL.SHADOW: '$ref:textFieldShadow'},
                    {GLOBAL.X: 0,   GLOBAL.Y: 33, GLOBAL.ALPHA: '{{v.hitsRatio?100|0}}', 'format': "<font face='mono' size='14' color='#00AAFF'>&#x25CE;</font>", GLOBAL.SHADOW: '$ref:textFieldShadow'},
                    {GLOBAL.X: 15,  GLOBAL.Y: 35, GLOBAL.ALIGN: GLOBAL.LEFT, 'format': "<b><font face='mono' size='11'color='{{v.c_hitsRatio}}'>{{v.hitsRatio%2d~%}}</font></b>", GLOBAL.SHADOW: '$ref:textFieldShadow'},
                    {GLOBAL.X: 0,   GLOBAL.Y: 63, GLOBAL.ALPHA: '{{v.tfb?100|0}}', 'format': "<img src='mods/Driftkings/Carroucel/damage.png' width='18' height='18'>", GLOBAL.SHADOW: '$ref:textFieldShadow'},
                    {GLOBAL.X: 19,  GLOBAL.Y: 63, GLOBAL.ALIGN: GLOBAL.LEFT, 'format': "<font face='mono' size='12' color='{{v.c_wn8effd}}'><b>{{v.tdb%d}}</b></font> <font size='12' color='#CFCFCF'>{{v.tfb?/|}}{{v.tfb?{{v.wn8expd%d}}|}}</font>", GLOBAL.SHADOW: '$ref:textFieldShadow'},
                    {GLOBAL.X: 152, GLOBAL.Y: 63, GLOBAL.ALIGN: GLOBAL.RIGHT, 'format': '[{{v.battletiermin}}-{{v.battletiermax}}]', GLOBAL.SHADOW: '$ref:textFieldShadow'},
                    {GLOBAL.X: 1,   GLOBAL.Y: 12, 'format': "<img src='{{icon:mastery}}' width='23' height='23'>", GLOBAL.SHADOW: '$ref:textFieldShadow'},
                    {GLOBAL.X: 140, GLOBAL.Y: 45, GLOBAL.WIDTH: 14, GLOBAL.HEIGHT: 14, GLOBAL.ALPHA: '{{v.marksOnGun?100|0}}', 'format': "<img src='{{icon:marksOnGun}}' width='14' height='14'>"},
                    {GLOBAL.X: 140, GLOBAL.Y: 45, GLOBAL.ALIGN: GLOBAL.RIGHT, 'format': "<font size='12' color='{{v.c_damageRating}}'><b>{{v.damageRating%4.01f~%}}</b></font>", GLOBAL.SHADOW: '$ref:textFieldShadow'},
                    {GLOBAL.X: 1,   GLOBAL.Y: 1, 'layer': 'substrate', GLOBAL.WIDTH: 160, GLOBAL.HEIGHT: 100, 'bgColor': '#0A0A0A'},
                    {GLOBAL.ENABLED: True, GLOBAL.X: 2, GLOBAL.Y: 2, 'layer': 'substrate', GLOBAL.WIDTH: 160, GLOBAL.HEIGHT: 100, GLOBAL.ALPHA: '{{v.selected?100|0}}', 'format': "<img src='mods/Driftkings/Carroucel/{{v.c_type}}.png' width='154' height='94'>"}
                ],
                'fields': {
                    'flag': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100, 'scale': 1},
                    'tankIcon': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100, 'scale': 1},
                    'tankType': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100, 'scale': 1},
                    'level': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100, 'scale': 1},
                    'xp': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100, 'scale': 1},
                    'tankName': {GLOBAL.ENABLED: True,'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100, 'scale': 1, 'textFormat': {}, GLOBAL.SHADOW: {}},
                    'rentInfo': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100, 'scale': 1, 'textFormat': {}, GLOBAL.SHADOW: {}},
                    'info': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100, 'scale': 1, 'textFormat': {}, GLOBAL.SHADOW: {}},
                    'infoImg': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100, 'scale': 1},
                    'infoBuy': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100, 'scale': 1, 'textFormat': {}, GLOBAL.SHADOW: {}},
                    'clanLock': {GLOBAL.ENABLED:True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100},
                    'price': {GLOBAL.ENABLED:True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100},
                    'actionPrice': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA:100},
                    'favorite': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100, 'scale': 1},
                    'crystalsBorder': {GLOBAL.ENABLED: True, GLOBAL.ALPHA: 100},
                    'crystalsIcon': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100},
                    'coreBorder': {GLOBAL.ENABLED: True, GLOBAL.ALPHA: 100},
                    'stats': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100, 'textFormat': {}, GLOBAL.SHADOW: {}},
                    'progressionPoints': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100, 'scale': 1}
                },
                'gap': 10,
                GLOBAL.HEIGHT: 140,
                GLOBAL.WIDTH: 210
            },
            'small': {
                'textFieldShadow': {GLOBAL.ENABLED: True, GLOBAL.COLOR: '#000000', GLOBAL.ALPHA: 80, GLOBAL.BLUR: 2, GLOBAL.STRENGTH: 2, GLOBAL.DISTANCE: 0, GLOBAL.ANGLE: 0},
                'extraFields': [
                    {GLOBAL.X: 1, GLOBAL.Y: 1, 'layer': 'substrate', GLOBAL.WIDTH: 160, GLOBAL.HEIGHT: 35, 'bgColor': '#0A0A0A'},
                    {GLOBAL.ENABLED: True, GLOBAL.X: 4, GLOBAL.Y: 14, GLOBAL.WIDTH: 23, GLOBAL.HEIGHT: 23, 'src': '{{icon:mastery}}'},
                    {GLOBAL.ENABLED: True, GLOBAL.X: 159, GLOBAL.Y: 14, GLOBAL.ALIGN: GLOBAL.RIGHT, 'format': "<font face='$FieldFont' size='15' color='{{v.premium?#FFA759|#C8C8B5}}'>{{v.name}}</font>", GLOBAL.SHADOW: {'$ref': 'textFieldShadow', GLOBAL.COLOR: '{{v.premium?0xFC3700|0xC8C8B5}}', GLOBAL.ALPHA: '{{v.premium?85|35}}', GLOBAL.BLUR: '{{v.premium?10|8}}'}},
                    {GLOBAL.ENABLED: True, GLOBAL.X: 24, GLOBAL.Y: 16, 'format': "<b><font face='$FieldFont' size='12' color='{{v.c_winrate|#C8C8B5}}'>{{v.winrate%2d~%}}</font></b>", GLOBAL.SHADOW: '$ref:textFieldShadow'}
                ],
                'fields': {
                    'flag': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100, 'scale': 1},
                    'tankIcon': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100, 'scale': 1},
                    'tankType': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100, 'scale': 1},
                    'level': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100, 'scale': 1},
                    'xp': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100, 'scale': 1},
                    'tankName': {GLOBAL.ENABLED: False, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100, 'scale': 1, 'textFormat': {}, GLOBAL.SHADOW: {}},
                    'info': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100, 'scale': 1, 'textFormat': {}, GLOBAL.SHADOW: {}},
                    'infoImg': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100, 'scale': 1},
                    'infoBuy': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100, 'scale': 1, 'textFormat': {}, GLOBAL.SHADOW: {}},
                    'clanLock': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100, 'scale': 1},
                    'price': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100, 'scale': 1},
                    'actionPrice': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100, 'scale': 1},
                    'favorite': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100, 'scale': 1},
                    'crystalsBorder': {GLOBAL.ENABLED: True, GLOBAL.ALPHA: 100},
                    'crystalsIcon': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100},
                    'coreBorder': {GLOBAL.ENABLED: True, GLOBAL.ALPHA: 100},
                    'stats': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100, 'scale': 1, 'textFormat': {}, 'shadow': {}},
                    'progressionPoints': {GLOBAL.ENABLED: True, 'dx': 0, 'dy': 0, GLOBAL.ALPHA: 100, 'scale': 1}
                },
                'gap': 10,
                GLOBAL.HEIGHT: 70,
                GLOBAL.WIDTH: 160
            }
        }
    },
    CREW_SETTINGS.ID: {
        GLOBAL.ENABLED: True,
        CREW_SETTINGS.CREW_AUTO_RETURN: False,
        CREW_SETTINGS.CREW_RETURN_BY_DEFAULT: False,
        CREW_SETTINGS.AUTO_RETURN_DELAY: 1.5,
        CREW_SETTINGS.SHOW_NOTIFICATIONS: True,
        CREW_SETTINGS.EXCLUDE_PREMIUM_VEHICLES: False
    },
    HANGAR_OPTIONS.ID: {
        GLOBAL.ENABLED: True,
        HANGAR_OPTIONS.AUTO_LOGIN: True,
        HANGAR_OPTIONS.SHOW_XP_TO_UNLOCK_VEH: False,
        HANGAR_OPTIONS.SHOW_GENERAL_CHAT_BUTTON: True,
        HANGAR_OPTIONS.SHOW_PROMO_PREM_VEHICLE: False,
        HANGAR_OPTIONS.SHOW_POP_UP_MESSAGES: False,
        HANGAR_OPTIONS.SHOW_UNREAD_COUNTER: True,
        HANGAR_OPTIONS.SHOW_RANKED_BATTLE_RESULTS: False,
        HANGAR_OPTIONS.SHOW_BUTTON: False,
        HANGAR_OPTIONS.SHOW_ACHIEVEMENT_POPUPS: False,
        HANGAR_OPTIONS.SHOW_ACHIEVEMENT_REWARD_WINDOW: True,
        HANGAR_OPTIONS.SHOW_BATTLE_COUNT: True,
        HANGAR_OPTIONS.SHOW_DAILY_QUEST_WIDGET: False,
        HANGAR_OPTIONS.SHOW_PROGRESSIVE_DECALS_WINDOW: False,
        HANGAR_OPTIONS.SHOW_EVENT_BANNER: True,
        HANGAR_OPTIONS.SHOW_EVENT_TOURNAMENT_WIDGET: True,
        HANGAR_OPTIONS.SHOW_HANGAR_PRESTIGE_WIDGET: False,
        HANGAR_OPTIONS.SHOW_PROFILE_PRESTIGE_WIDGET: True,
        HANGAR_OPTIONS.SHOW_BUTTON_COUNTERS: True,
        HANGAR_OPTIONS.ALLOW_EXCHANGE_XPIN_TECH_TREE: True,
        HANGAR_OPTIONS.ALLOW_CHANNEL_BUTTON_BLINKING: True,
        HANGAR_OPTIONS.LOOT_BOXES_WIDGET: False,
        HANGAR_OPTIONS.HIDE_BTN_COUNTERS: False,
        HANGAR_OPTIONS.FIELD_MAIL: True,
        HANGAR_OPTIONS.CLOCK: True,
        HANGAR_OPTIONS.CLOCK_STYLE: 0,
        HANGAR_OPTIONS.CLOCK_X: -40,
        HANGAR_OPTIONS.CLOCK_Y: 55,
        HANGAR_OPTIONS.CLOCK_SCALE: 100,
        HANGAR_OPTIONS.CLOCK_SECONDS: True,
        HANGAR_OPTIONS.CLOCK24_HOUR: True,
        HANGAR_OPTIONS.SHOW_BATTLE_PASS_WIDGET: True,
        HANGAR_OPTIONS.BLOCK_VEHICLE_IF_LOW_AMMO: False,
        HANGAR_OPTIONS.LOW_AMMO_PERCENTAGE: 20,
        HANGAR_OPTIONS.CUSTOM_CLOCK_FORMAT: False,
        HANGAR_OPTIONS.TEXT: "<font face='$FieldFont' color='#959688'><textformat leading='-38'><font size='32'><tab>%H:%M:%S</font><br></textformat><textformat rightMargin='85' leading='-2'>%A<br><font size='15'>%d %b %Y</font></textformat></font>",
        HANGAR_OPTIONS.CUSTOM_CLOCK_TEXT: "<font face='$FieldFont' color='#FF9900'><textformat leading='-38'><font size='32'><tab>%H:%M:%S</font><br></textformat><textformat rightMargin='85' leading='-2'>%A<br><font size='15'>%d %b %Y</font></textformat></font>",
        HANGAR_OPTIONS.PANEL: {'position': {GLOBAL.X: -40.0, GLOBAL.Y: 55.0}, GLOBAL.WIDTH: 210, GLOBAL.HEIGHT: 50, GLOBAL.SHADOW: {GLOBAL.DISTANCE: 0, GLOBAL.ANGLE: 0, GLOBAL.STRENGTH: 0.5, GLOBAL.QUALITY: 3}, GLOBAL.ALIGN_X: GLOBAL.RIGHT, GLOBAL.ALIGN_Y: GLOBAL.TOP}
    },
    MARKS_ON_GUN_HANGAR.ID: {
        GLOBAL.ENABLED: True,
        MARKS_ON_GUN_HANGAR.SHOW_IN_HANGAR: True,
        MARKS_ON_GUN_HANGAR.SHOW_IN_STATISTIC: True,
        MARKS_ON_GUN_HANGAR.TEXT_LOCK: False,
        MARKS_ON_GUN_HANGAR.GOAL_SELECTION: 0,
        MARKS_ON_GUN_HANGAR.COMPACT_MODE: False,
        MARKS_ON_GUN_HANGAR.HISTORY_BATTLES: 10,
        MARKS_ON_GUN_HANGAR.SHOW_TOOLTIP_TARGETS: True,
        MARKS_ON_GUN_HANGAR.COLOR_RATING: 0,
        MARKS_ON_GUN_HANGAR.STAR_ANIMATION_WINDOW: 5.0,
        MARKS_ON_GUN_HANGAR.PANEL: {GLOBAL.X: 215.0, GLOBAL.Y: -246.0, GLOBAL.WIDTH: 362.0, GLOBAL.HEIGHT: 186.0, GLOBAL.ALIGN_X: GLOBAL.LEFT, GLOBAL.ALIGN_Y: GLOBAL.BOTTOM},
        MARKS_ON_GUN_HANGAR.CARD: {'backgroundColor': 0x121518, 'backgroundAlpha': 0.75, 'outlineColor': 0xFFFFFF, 'headerColor': '#D98219', 'titleColor': '#E8E4DA', 'mutedColor': '#969BA3', 'lineColor': '#969BA3', 'accentColor': '#D98219', 'accentSoftColor': '#4A3319', 'warningColor': '#E05454'}
    },
    MARKS_ON_GUN_TECH_TREE.ID: {
        GLOBAL.ENABLED: True,
        MARKS_ON_GUN_TECH_TREE.COLOR_RATING: GLOBAL.ZERO,
        MARKS_ON_GUN_TECH_TREE.SHOW_IN_TECH_TREE: True,
        MARKS_ON_GUN_TECH_TREE.SHOW_IN_TECH_TREE_MARK_OF_GUN_PERCENT: True,
        MARKS_ON_GUN_TECH_TREE.SHOW_IN_TECH_TREE_MASTERY: True,
        MARKS_ON_GUN_TECH_TREE.SHOW_IN_TECH_TREE_MARK_OF_GUN_TANK_NAME_COLORED: False,
        MARKS_ON_GUN_TECH_TREE.BADGE_OFFSET_X: 115,
        MARKS_ON_GUN_TECH_TREE.BADGE_OFFSET_Y: 0,
        MARKS_ON_GUN_TECH_TREE.BADGE_FONT_SIZE: 14
    },
    BANKS_LOADER.ID: {
        BANKS_LOADER.DEFAULT_POOL: 36,
        BANKS_LOADER.LOW_ENGINE_POOL: 10,
        BANKS_LOADER.MEMORY_LIMIT: 250,
        BANKS_LOADER.STREAMING_POOL: 8,
        BANKS_LOADER.IOPOOL_SIZE: 8,
        BANKS_LOADER.MAX_VOICES: 110,
        BANKS_LOADER.DEBUG: False
    },
    LOGS_SWAPPER.ID: {
        GLOBAL.ENABLED: True,
        LOGS_SWAPPER.LOG_SWAPPER: True,
        LOGS_SWAPPER.WG_LOG_HIDE_CRITICS: True,
        LOGS_SWAPPER.WG_LOG_HIDE_BLOCK: True,
        LOGS_SWAPPER.WG_LOG_HIDE_ASSIST: True
    }
}

HOTKEYS = {ARTY_SPLASH.ID: {ARTY_SPLASH.BUTTON_SHOW_DOT: ['KEY_C', ['KEY_LALT', 'KEY_RALT']], ARTY_SPLASH.BUTTON_SHOW_SPLASH: ['KEY_Z', ['KEY_LALT', 'KEY_RALT']]},
 INFO_PANEL.ID: {INFO_PANEL.ALT_KEY: ['KEY_LALT']},
 MARKS_ON_GUN_BATTLE.ID: {
     MARKS_ON_GUN_BATTLE.BUTTON_SHOW: ['KEY_NUMPAD9', ['KEY_LALT', 'KEY_RALT']],
     MARKS_ON_GUN_BATTLE.BUTTON_SIZE_UP: ['KEY_PGUP', ['KEY_LALT', 'KEY_RALT']],
     MARKS_ON_GUN_BATTLE.BUTTON_SIZE_DOWN: ['KEY_PGDN', ['KEY_LALT', 'KEY_RALT']],
     MARKS_ON_GUN_BATTLE.BUTTON_RESET: ['KEY_DELETE', ['KEY_LCONTROL', 'KEY_RCONTROL'], ['KEY_LSHIFT', 'KEY_RSHIFT']]
 },
 MINIMAP_PLUGINS.ID: {MINIMAP_PLUGINS.BUTTON: ['KEY_LCONTROL']},
 REPAIR_EXTENDED.ID: {REPAIR_EXTENDED.BUTTON_REPAIR: ['KEY_SPACE'], REPAIR_EXTENDED.BUTTON_CHASSIS: [['KEY_LALT', 'KEY_RALT']]},
 SAFE_SHOT.ID: {SAFE_SHOT.DISABLE_KEY: ['KEY_Q']},
 SERVER_TURRET_EXTENDED.ID: {SERVER_TURRET_EXTENDED.BUTTON_AUTO_MODE: ['KEY_R', ['KEY_LALT', 'KEY_RALT']], SERVER_TURRET_EXTENDED.BUTTON_MAX_MODE: ['KEY_R', ['KEY_LCONTROL', 'KEY_RCONTROL']]}}
PROFILES = ('none', 'short', 'medium', 'medium2', 'large')


def defaults(component):
    return copy.deepcopy(DEFAULTS[component])


def default_keys(component):
    return copy.deepcopy(HOTKEYS.get(component, {}))


def part_name(component):
    section = CONFIG_BY_ID.get(component)
    if section is not None:
        return section.NAME
    if not re.match(r'^[A-Za-z][A-Za-z0-9_]*\Z', component):
        raise ValueError('Invalid settings component: ' + component)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', component).lower()


def profile_for_mode(mode):
    # Native EU PLAYERS_PANEL_STATE, including variants without badges.
    return {0: 'none', 1: 'short', 20: 'short', 2: 'medium', 5: 'medium',
            3: 'medium2', 21: 'medium2', 4: 'large', 6: 'large'}.get(mode, 'large')


class SettingsData(object):
    """Shared access to the same live dictionaries used by feature controllers."""
    def __init__(self):
        self.configs = {}

    def register(self, config):
        self.configs[part_name(config.ID)] = config

    def __getattr__(self, name):
        config = self.configs.get(name)
        if config is None:
            raise AttributeError(name)
        return config.data


user_settings = SettingsData()

# Controllers verified to read or refresh these values during battle.
BATTLE_EDITABLE = frozenset((AUTO_AIM_OPTIMIZE.ID, SAFE_SHOT.ID, INFO_PANEL.ID, PLAYER_PANEL_PRO.ID))
# Application timing follows the readers/callbacks in each controller. Unknown
# options retain the safe restart policy; paths allow different nested options.
LIVE = 'live'
NEXT_BATTLE = 'battle'
NEXT_VIEW = 'view'
RESTART = 'restart'
APPLY_TIMING = {
    AUTO_AIM_OPTIMIZE.ID: {'*': LIVE},  # lock request reads the current dictionary
    SAFE_SHOT.ID: {'*': LIVE},        # shot handler reads the current dictionary
    INFO_PANEL.ID: {'*': LIVE, GLOBAL.ENABLED: NEXT_BATTLE},
    PLAYER_PANEL_PRO.ID: {'*': LIVE, GLOBAL.ENABLED: NEXT_BATTLE},
    MAIN_GUN.ID: {GLOBAL.ENABLED: LIVE, MAIN_GUN.BACK_GROUND_ENABLED: LIVE, MAIN_GUN.TEXT_LOCK: LIVE, MAIN_GUN.TEXT_POSITION: LIVE, 'background.alpha': LIVE},
    BATTLE_STAT.ID: {GLOBAL.ENABLED: LIVE, BATTLE_STAT.FORMAT: LIVE, BATTLE_STAT.COLOR_RATING: LIVE, BATTLE_STAT.TEXT_LOCK: LIVE, BATTLE_STAT.TEXT_POSITION: LIVE},
    BATTLE_EFFICIENCY.ID: {GLOBAL.ENABLED: NEXT_BATTLE, BATTLE_EFFICIENCY.TEXT_LOCK: LIVE, BATTLE_EFFICIENCY.POSITION: LIVE, BATTLE_EFFICIENCY.COLOR_RATTING: LIVE, BATTLE_EFFICIENCY.FORMAT: LIVE, BATTLE_EFFICIENCY.BATTLE_RESULTS_WINDOW: NEXT_VIEW, BATTLE_EFFICIENCY.BATTLE_RESULTS_FORMAT: NEXT_VIEW},
    OWN_HEALTH.ID: {'*': LIVE, GLOBAL.ENABLED: NEXT_BATTLE},
    # Views/cameras are constructed again when entering battle.
    ARMOR_CALCULATOR.ID: {'*': NEXT_BATTLE},
    ARTY_SPLASH.ID: {'*': NEXT_BATTLE},
    # Arcade camera base dictionaries are shared and cleared only on first use.
    ARCADE_ZOOM.ID: {'*': RESTART},
    DISPERSION_TIMER.ID: {'*': NEXT_BATTLE},
    FLIGHT_TIMER.ID: {'*': NEXT_BATTLE},
    DISTANCE_MARKER.ID: {'*': NEXT_BATTLE},
    SIXTH_SENSE.ID: {'*': NEXT_BATTLE},
    DISPERSION_CIRCLE.ID: {'*': NEXT_BATTLE},
    MINIMAP_PLUGINS.ID: {'*': NEXT_BATTLE},
    BATTLE_OPTIONS.ID: {'*': NEXT_BATTLE},
    MARKS_ON_GUN_BATTLE.ID: {'*': NEXT_BATTLE},
    AIMING_ANGLES.ID: {'*': NEXT_BATTLE},
    SPOTTED_EXTENDED_LIGHT.ID: {'*': NEXT_BATTLE},
    SERVER_TURRET_EXTENDED.ID: {'*': NEXT_BATTLE},
    REPAIR_EXTENDED.ID: {'*': NEXT_BATTLE},
    LOGS_SWAPPER.ID: {'*': LIVE},  # filters/routing read on each new log entry
    CREW_SETTINGS.ID: {'*': NEXT_VIEW},  # vehicle selection/crew action
    AUTO_CLAIM_CLAN.ID: {'*': NEXT_VIEW},
    ACCOUNT_MANAGER.ID: {'*': NEXT_VIEW},  # next login window
    CAROUSEL_STATS.ID: {'*': LIVE},  # controller.onApplySettings
    MARKS_ON_GUN_HANGAR.ID: {'*': LIVE},
    MARKS_ON_GUN_TECH_TREE.ID: {'*': LIVE},
    HANGAR_OPTIONS.ID: {'*': NEXT_VIEW, HANGAR_OPTIONS.LOW_AMMO_PERCENTAGE: LIVE, HANGAR_OPTIONS.SHOW_BATTLE_PASS_WIDGET: LIVE, HANGAR_OPTIONS.CLOCK: LIVE, HANGAR_OPTIONS.CLOCK_STYLE: LIVE, HANGAR_OPTIONS.CLOCK_X: LIVE, HANGAR_OPTIONS.CLOCK_Y: LIVE, HANGAR_OPTIONS.CLOCK_SCALE: LIVE, HANGAR_OPTIONS.CLOCK_SECONDS: LIVE, HANGAR_OPTIONS.CLOCK24_HOUR: LIVE},
    # The camera-change listener caches these values only at construction.
    ZOOM_EXTENDED.ID: {ZOOM_EXTENDED.NO_BINOCULARS: NEXT_BATTLE, ZOOM_EXTENDED.NO_SNIPER_DYNAMIC: NEXT_BATTLE, ZOOM_EXTENDED.ZOOM_STEPS: NEXT_BATTLE, ZOOM_EXTENDED.NO_FLASH_BANG: LIVE, ZOOM_EXTENDED.NO_SHOCK_WAVE: LIVE},
    BANKS_LOADER.ID: {'*': RESTART},
    'Driftkings': {'*': RESTART},  # selected configuration profile
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


def requires_restart(component, field):
    return application_timing(component, field) == RESTART
