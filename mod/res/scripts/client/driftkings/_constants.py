# -*- coding: utf-8 -*-
"""
Stable settings keys and UI aliases; no game imports.
NAME is the single configuration key for registry, defaults and translations.
"""
from collections import namedtuple

# Shared value records; safe to import outside the client.
MinMax = namedtuple('MinMax', ('min', 'max'))
ScreenBounds = namedtuple('ScreenBounds', ('x', 'y', 'width', 'height'))
MarksStatistics = namedtuple('MarksStatistics', ('next_percent', 'next_damage', 'damage20', 'damage40', 'damage55', 'damage65', 'damage85', 'damage95', 'damage100'))
BattleCurve = namedtuple('BattleCurve', ('levels', 'damages', 'statistics', 'target_damage', 'target_reachable', 'limit_reached'))
# Shared marks of excellence rules.
MARK_LEVELS = (0.0, 20.0, 40.0, 55.0, 65.0, 85.0, 95.0, 100.0)
MARK_THRESHOLDS = (65, 85, 95)
# Marks of excellence panels are shown only for tier 5 and above, where marks exist.
MARKS_MIN_TIER = 5
# Shared identifiers and policies, without resolving client-owned enums.
SETTINGS_MOD_ID = 'dk.settings'
# Random battles that update account statistics, including new/returning players.
STATISTICS_BATTLES = ('REGULAR', 'RANDOM_NP2', 'WINBACK')
# Shared ordered statistical and presentation contracts.
WN8_EXPECTED_FIELDS = ('wn8expDamage', 'wn8expFrag', 'wn8expSpot', 'wn8expDef', 'wn8expWinRate')
ROMAN_NUMERALS = ('I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII')


# Configuration namespaces; NAME and option spellings are persisted contracts.
class GLOBAL(object):
    ENABLED = 'enabled'
    X = 'x'
    Y = 'y'
    WIDTH = 'width'
    HEIGHT = 'height'
    ALPHA = 'alpha'
    COLOR = 'color'
    ALIGN_X = 'alignX'
    ALIGN_Y = 'alignY'
    TOP = 'top'
    BOTTOM = 'bottom'
    RIGHT = 'right'
    LEFT = 'left'
    DRAG = 'drag'
    LIMIT = 'limit'
    ZERO = 0
    ONE = 1


class GUN_TRAVERSE_LIMITS(object):
    NAME = 'gun_traverse_limits'
    VERTICAL = 'vertical'
    HORIZONTAL = 'horizontal'


class THIRD_PERSON_ZOOM(object):
    ARCADE = 'arcade'
    POSTMORTEM = 'postmortem'
    STRATEGIC = 'strategic'
    ARTY = 'arty'
    NAME = 'third_person_zoom'
    MODES = (ARCADE, POSTMORTEM, STRATEGIC, ARTY)


class PENETRATION_INDICATOR(object):
    NAME = 'penetration_indicator'
    DISPLAY_ON_ALLIES = 'displayOnAllies'
    MESSAGES = 'messages'
    POSITION = 'position'
    TEMPLATE = 'template'


class ARTILLERY_BLAST_RADIUS(object):
    NAME = 'artillery_blast_radius'
    BUTTON_SHOW_DOT = 'buttonShowDot'
    BUTTON_SHOW_SPLASH = 'buttonShowSplash'
    SHOW_SPLASH_ON_DEFAULT = 'showSplashOnDefault'
    SHOW_DOT_ON_DEFAULT = 'showDotOnDefault'
    SHOW_MODE_ARCADE = 'showModeArcade'
    SHOW_MODE_SNIPER = 'showModeSniper'
    SHOW_MODE_ARTY = 'showModeArty'
    MODEL_PATH_SPLASH = 'modelPathSplash'
    MODEL_PATH_DOT = 'modelPathDot'


class AUTOAIM_TARGET_INDICATOR(object):
    COLOR = 'color'
    NAME = 'autoaim_target_indicator'


class BATTLE_PERFORMANCE(object):
    NAME = 'battle_performance'
    COLOR_RATTING = 'colorRatting'
    FORMAT = 'format'
    TEXT_STYLE = 'textStyle'
    TEXT_LOCK = 'textLock'
    POSITION = 'position'
    TEXT_SHADOW = 'textShadow'
    BATTLE_RESULTS_WINDOW = 'battleResultsWindow'
    BATTLE_RESULTS_FORMAT = 'battleResultsFormat'


class BATTLE_PREFERENCES(object):
    NAME = 'battle_preferences'
    REMOVE_FOG = 'removeFog'
    CLIP_LOAD = 'clipLoad'
    DIRECTIVES_ONLY_FROM_STORAGE = 'directivesOnlyFromStorage'
    DISABLE_SOUND_COMMANDER = 'disableSoundCommander'
    FORMAT = 'format'
    IN_BATTLE = 'inBattle'
    LOAD_TXT = 'loadTxt'
    MAX_CHAT_LINES = 'maxChatLines'
    MUTE_TEAM_BASE_SOUND = 'muteTeamBaseSound'
    POSTMORTEM_TIPS = 'postmortemTips'
    SHOW_BATTLE_HINT = 'showBattleHint'
    SHOW_FRIENDS = 'showFriends'
    SHOW_POSTMORTEM_DOG_TAG = 'showPostmortemDogTag'
    STUN_SOUND = 'stunSound'
    SHOW_PLAYER_SATISFACTION_WIDGET = 'showPlayerSatisfactionWidget'
    ADD_ENEMY_NAME = 'addEnemyName'
    HIDE_HINT = 'hideHint'


class BATTLE_STATISTICS(object):
    NAME = 'battle_statistics'
    COLOR_RATING = 'colorRating'
    FORMAT = 'format'
    TEXT_LOCK = 'textLock'
    TEXT_POSITION = 'textPosition'
    TEXT_FORMAT = 'textFormat'


class AIMING_RETICLES(object):
    NAME = 'aiming_reticles'
    GUN_MARKER_MINIMUM_SIZE = 'gunMarkerMinimumSize'
    PERCENT_CORRECTION = 'percentCorrection'
    SHOW_CLIENT_AND_SERVER_RETICLE_BETA = 'showClientAndServerReticleBeta'
    SHOW_SERVER_SPG_STRATEGIC_RETICLE = 'showServerSpgStrategicReticle'
    SERVER_RETICLE_AIMING_CIRCLE_SHAPE = 'serverReticleAimingCircleShape'
    SERVER_RETICLE_AIMING_CIRCLE_OPACITY = 'serverReticleAimingCircleOpacity'
    SERVER_RETICLE_GUN_MARKER_SHAPE = 'serverReticleGunMarkerShape'
    SERVER_RETICLE_GUN_MARKER_OPACITY = 'serverReticleGunMarkerOpacity'


class AIMING_COUNTDOWN(object):
    NAME = 'aiming_countdown'
    RED = 'red'
    ORANGE = 'orange'
    YELLOW = 'yellow'
    GREEN = 'green'
    BLUE = 'blue'
    PURPLE = 'purple'
    TEMPLATE = 'template'


class TARGET_DISTANCE(object):
    NAME = 'target_distance'
    DISPLAY_MODE = 'displayMode'
    MARKER_TARGET = 'markerTarget'
    ANCHOR_POSITION = 'anchorPosition'
    LOCK_POSITION_OFFSETS = 'lockPositionOffsets'
    ANCHOR_HORIZONTAL_OFFSET = 'anchorHorizontalOffset'
    ANCHOR_VERTICAL_OFFSET = 'anchorVerticalOffset'
    DECIMAL_PRECISION = 'decimalPrecision'
    TEXT_SIZE = 'textSize'
    TEXT_COLOR = 'textColor'
    TEXT_ALPHA = 'textAlpha'
    DRAW_TEXT_SHADOW = 'drawTextShadow'


class SHELL_FLIGHT_TIME(object):
    NAME = 'shell_flight_time'
    SPG_ONLY = 'spgOnly'
    TEMPLATE = 'template'


class TARGET_INFORMATION(object):
    NAME = 'target_information'
    ALIVE_ONLY = 'aliveOnly'
    ALT_KEY = 'altKey'
    COMPARE_VALUES = 'compareValues'
    DELAY = 'delay'
    TEMPLATE_PRESET = 'templatePreset'
    FORMATS = 'formats'
    SHOW_FOR = 'showFor'
    TEXT_LOCK = 'textLock'
    TEXT_POSITION = 'textPosition'
    TEXT_FORMAT = 'textFormat'
    TEXT_SHADOW = 'textShadow'
    BACKGROUND_ENABLED = 'backgroundEnabled'
    BACKGROUND_ALPHA = 'backgroundAlpha'


class HIGH_CALIBER_PROGRESS(object):
    NAME = 'high_caliber_progress'
    BACK_GROUND_ENABLED = 'backGroundEnabled'
    TEXT_LOCK = 'textLock'
    HIGH_CALIBER_PROGRESS = 'mainGun'
    TEXT_POSITION = 'textPosition'


class BATTLE_MARKS_OF_EXCELLENCE(object):
    GAMEFACE = 'gameface'
    SHOW_MARKS = 'showMarks'
    SHOW_DELTA = 'showDelta'
    SHOW_DAMAGE = 'showDamage'
    SHOW_PROGRESS = 'showProgress'
    SHOW_TARGETS = 'showTargets'
    NAME = 'battle_marks_of_excellence'
    COLOR_RATING = 'colorRating'
    BUTTON_SIZE_UP = 'buttonSizeUp'
    BUTTON_SIZE_DOWN = 'buttonSizeDown'
    BUTTON_RESET = 'buttonReset'
    SHOW_IN_BATTLE = 'showInBattle'
    SHOW_IN_BATTLE_HALF_PERCENTS = 'showInBattleHalfPercents'
    SHOW_IN_REPLAY = 'showInReplay'
    REPLAY_BASE_PERCENT = 'replayBasePercent'
    REPLAY_BASE_DAMAGE = 'replayBaseDamage'
    SHOW_IN_STATISTIC = 'showInStatistic'
    BACKGROUND = 'background'
    PANEL = 'panel'
    BATTLE_MESSAGE_SIZE_IN_PERCENT = 'battleMessageSizeInPercent'


class MINIMAP_ENHANCEMENTS(object):
    LABEL_STATES = ('normal', 'alternative', 'dead', 'lost')
    LABEL_TEAM_KEYS = ('ally', 'enemy', 'squad', 'alternativeAlly', 'alternativeEnemy', 'alternativeSquad')
    LABEL_COLOR_KEYS = ('allyColor', 'enemyColor', 'squadColor', 'teamKillerColor', 'deadColor')
    PRESENTATION_SWITCHES = ('alternativeEnabled', 'zoom', 'center')
    LINE_MODES = ('client', 'on', 'off')
    HEALTH_MODES = ('value', 'percent', 'bar')
    NAME = 'minimap_enhancements'
    MINIMAP_SCHEMA = 'minimapSchema'
    PERMANENT_MINIMAP_DEATH = 'permanentMinimapDeath'
    YAW = 'yaw'
    SHOW_NAMES = 'showNames'
    VIEW_RADIUS = 'viewRadius'
    ZOOM_FACTOR = 'zoomFactor'
    ZOOM_FACTOR_MAX = 'zoomFactorMax'
    CHANGE_COLOR_CIRCLES = 'changeColorCircles'
    COLOR_DRAW_CIRCLE = 'colorDrawCircle'
    COLOR_MAX_VIEW_CIRCLE = 'colorMaxViewCircle'
    COLOR_MIN_SPOTTING_CIRCLE = 'colorMinSpottingCircle'
    COLOR_VIEW_CIRCLE = 'colorViewCircle'
    SHOW_LAST_POSITIONS = 'showLastPositions'
    LAST_POSITION_DURATION = 'lastPositionDuration'
    SHOW_VEHICLE_TYPES = 'showVehicleTypes'
    LABELS = 'labels'
    ICONS = 'icons'
    HEALTH = 'health'
    LOST_MARKER = 'lostMarker'
    MAP_SIZE = 'mapSize'
    NEARBY = 'nearby'
    CIRCLES = 'circles'
    EXTRA_CIRCLES = 'extraCircles'
    LINES = 'lines'
    ARTILLERY_AIM = 'artilleryAim'
    PRESENTATION = 'presentation'
    BUTTON = 'button'


class VEHICLE_HEALTH(object):
    NAME = 'vehicle_health'
    AVG_COLOR = 'avgColor'
    STYLE = 'style'
    STYLES = ('classic', 'bastion', 'vanguard', 'ion', 'minimal')


class TEAM_PANELS(object):
    MODES = ('none', 'short', 'medium', 'medium2', 'large')
    RATINGS = ('wn8', 'eff', 'wgr', 'winrate', 'xwn8', 'xeff')
    HP_VISIBILITIES = ('always', 'hold', 'never')
    NAME = 'team_panels'
    STATS_ENABLED = 'statsEnabled'
    COLOR_SCALE = 'colorScale'
    RATING = 'rating'
    PERFORMANCE = 'performance'
    HP_ENABLED = 'hpEnabled'
    HP_VISIBILITY = 'hpVisibility'
    HP_KEY = 'hpKey'
    SPOTTED_ENABLED = 'spottedEnabled'
    PLAYERS_PANEL = 'playersPanel'
    PROFILES = 'profiles'
    TEMPLATES = 'templates'
    LOADING = 'loading'
    TAB = 'tab'


class REPAIR_CONTROLS(object):
    NAME = 'repair_controls'
    BUTTON_CHASSIS = 'buttonChassis'
    BUTTON_REPAIR = 'buttonRepair'
    REMOVE_STUN = 'removeStun'
    EXTINGUISH_FIRE = 'extinguishFire'
    HEAL_CREW = 'healCrew'
    REPAIR_DEVICES = 'repairDevices'
    RESTORE_CHASSIS = 'restoreChassis'
    USE_GOLD_KITS = 'useGoldKits'
    REPAIR_PRIORITY = 'repairPriority'


class SERVER_TURRET_SYNC(object):
    NAME = 'server_turret_sync'
    ACTIVATE_MESSAGE = 'activateMessage'
    SERVER_TURRET = 'serverTurret'


class SIXTH_SENSE_ALERT(object):
    NAME = 'sixth_sense_alert'
    DEFAULT_ICON = 'defaultIcon'
    USER_ICON = 'userIcon'
    LAMP_SHOW_TIME = 'lampShowTime'
    PLAY_TICK_SOUND = 'playTickSound'
    USER_SOUND = 'userSound'
    DEFAULT_ICON_NAME = 'defaultIconName'
    SIXTH_SENSE_SOUND = 'sixthSenseSound'
    SHOW_TIMER = 'showTimer'
    SHOW_TIMER_GRAPHICS = 'showTimerGraphics'
    SHOW_TIMER_GRAPHICS_COLOR = 'showTimerGraphicsColor'
    SHOW_TIMER_GRAPHICS_RADIUS = 'showTimerGraphicsRadius'
    ICON_SIZE = 'iconSize'
    SPOTTED_MESSAGE = 'spottedMessage'
    HELP_MESSAGE = 'helpMessage'
    SPOTTED_TEXT = 'spottedText'
    DELAY = 'delay'


class ENEMY_SPOTTING_STATUS(object):
    NAME = 'enemy_spotting_status'
    SOUND = 'sound'
    ICON_SIZE_X = 'iconSizeX'
    ICON_SIZE_Y = 'iconSizeY'
    SOUND_SPOTTED = 'soundSpotted'
    SOUND_ASSIST = 'soundAssist'
    MESSAGE_COLOR_SPOTTED = 'messageColorSpotted'
    MESSAGE_COLOR_ASSIST_RADIO = 'messageColorAssistRadio'
    MESSAGE_COLOR_ASSIST_TRACK = 'messageColorAssistTrack'
    MESSAGE_COLOR_ASSIST_STUN = 'messageColorAssistStun'
    SPOTTED = 'Spotted'
    ASSIST_RADIO = 'AssistRadio'
    ASSIST_TRACK = 'AssistTrack'
    ASSIST_STUN = 'AssistStun'


class SNIPER_CAMERA(object):
    NAME = 'sniper_camera'
    NO_BINOCULARS = 'noBinoculars'
    NO_FLASH_BANG = 'noFlashBang'
    NO_SHOCK_WAVE = 'noShockWave'
    NO_SNIPER_DYNAMIC = 'noSniperDynamic'
    DISABLE_CAM_AFTER_SHOT = 'disableCamAfterShot'
    DISABLE_CAM_AFTER_SHOT_LATENCY = 'disableCamAfterShotLatency'
    DISABLE_CAM_AFTER_SHOT_SKIP_CLIP = 'disableCamAfterShotSkipClip'
    ZOOM_STEPS = 'zoomSteps'


class ACCOUNT_MANAGER(object):
    # Build tooling discovers canonical sections by their NAME attribute.
    NAME = 'account_manager'


class CLAN_REWARD_COLLECTION(object):
    NAME = 'clan_reward_collection'


class VEHICLE_CAROUSEL(object):
    ALPHA_FIELDS = ('backgroundAlpha', 'slotBackgroundAlpha', 'slotBorderAlpha', 'slotSelectedBorderAlpha', 'edgeFadeAlpha')
    SWITCHES = ('hideBuyTank', 'hideBuySlot', 'hideRestoreTank', 'showTotalSlots', 'showUsedSlots', 'enableLockBackground', 'suppressCarouselTooltips')
    FILTERS = ('params', 'bonus', 'favorite', 'elite', 'premium')
    CELL_BOUNDS = (('width', 80, 600), ('height', 35, 400), ('gap', 0, 40))
    NAME = 'vehicle_carousel'
    SORTING_CRITERIA = 'sortingCriteria'
    NATIONS_ORDER = 'nationsOrder'
    TYPES_ORDER = 'typesOrder'
    COLOR_RATING = 'colorRating'
    SHOW_ICONS = 'showIcons'
    CAROUSEL = 'carousel'


class CREW_MANAGEMENT(object):
    SHOW_CREW_PROGRESSION = 'showCrewProgression'
    SHOW_REMAINING_X_P = 'showRemainingXP'
    SHOW_ESTIMATED_BATTLES = 'showEstimatedBattles'
    SHOW_CREW_DETAILS = 'showCrewDetails'
    SHOW_CREW_TOOLTIPS = 'showCrewTooltips'
    SHOW_BARRACKS_PROGRESSION = 'showBarracksProgression'
    NAME = 'crew_management'
    CREW_AUTO_RETURN = 'crewAutoReturn'
    CREW_RETURN_BY_DEFAULT = 'crewReturnByDefault'
    AUTO_RETURN_DELAY = 'autoReturnDelay'
    SHOW_NOTIFICATIONS = 'showNotifications'
    EXCLUDE_PREMIUM_VEHICLES = 'excludePremiumVehicles'


class HANGAR_PREFERENCES(object):
    NAME = 'hangar_preferences'
    AUTO_LOGIN = 'autoLogin'
    SHOW_XP_TO_UNLOCK_VEH = 'showXpToUnlockVeh'
    SHOW_GENERAL_CHAT_BUTTON = 'showGeneralChatButton'
    SHOW_PROMO_PREM_VEHICLE = 'showPromoPremVehicle'
    SHOW_POP_UP_MESSAGES = 'showPopUpMessages'
    SHOW_UNREAD_COUNTER = 'showUnreadCounter'
    SHOW_RANKED_BATTLE_RESULTS = 'showRankedBattleResults'
    SHOW_BUTTON = 'showButton'
    SHOW_ACHIEVEMENT_POPUPS = 'showAchievementPopups'
    SHOW_ACHIEVEMENT_REWARD_WINDOW = 'showAchievementRewardWindow'
    SHOW_BATTLE_COUNT = 'showBattleCount'
    SHOW_DAILY_QUEST_WIDGET = 'showDailyQuestWidget'
    SHOW_PROGRESSIVE_DECALS_WINDOW = 'showProgressiveDecalsWindow'
    SHOW_EVENT_BANNER = 'showEventBanner'
    SHOW_EVENT_TOURNAMENT_WIDGET = 'showEventTournamentWidget'
    SHOW_HANGAR_PRESTIGE_WIDGET = 'showHangarPrestigeWidget'
    SHOW_PROFILE_PRESTIGE_WIDGET = 'showProfilePrestigeWidget'
    SHOW_BUTTON_COUNTERS = 'showButtonCounters'
    ALLOW_EXCHANGE_XPIN_TECH_TREE = 'allowExchangeXPInTechTree'
    ALLOW_CHANNEL_BUTTON_BLINKING = 'allowChannelButtonBlinking'
    LOOT_BOXES_WIDGET = 'lootBoxesWidget'
    HIDE_BTN_COUNTERS = 'hideBtnCounters'
    FIELD_MAIL = 'fieldMail'
    SHOW_BATTLE_PASS_WIDGET = 'showBattlePassWidget'
    BLOCK_VEHICLE_IF_LOW_AMMO = 'blockVehicleIfLowAmmo'
    LOW_AMMO_PERCENTAGE = 'lowAmmoPercentage'


class HANGAR_MARKS_OF_EXCELLENCE(object):
    GAMEFACE = 'gameface'
    NAME = 'hangar_marks_of_excellence'
    SHOW_IN_HANGAR = 'showInHangar'
    SHOW_IN_STATISTIC = 'showInStatistic'
    GOAL_SELECTION = 'goalSelection'
    HISTORY_BATTLES = 'historyBattles'
    SHOW_TOOLTIP_TARGETS = 'showTooltipTargets'
    COLOR_RATING = 'colorRating'


class TECH_TREE_MARKS_OF_EXCELLENCE(object):
    NAME = 'tech_tree_marks_of_excellence'
    COLOR_RATING = 'colorRating'
    SHOW_IN_TECH_TREE = 'showInTechTree'
    SHOW_IN_TECH_TREE_MARK_OF_GUN_PERCENT = 'showInTechTreeMarkOfGunPercent'
    SHOW_IN_TECH_TREE_MASTERY = 'showInTechTreeMastery'
    SHOW_IN_TECH_TREE_MARK_OF_GUN_TANK_NAME_COLORED = 'showInTechTreeMarkOfGunTankNameColored'
    BADGE_OFFSET_X = 'badgeOffsetX'
    BADGE_OFFSET_Y = 'badgeOffsetY'
    BADGE_FONT_SIZE = 'badgeFontSize'


class MAIN(object):
    NAME = 'main'
    # {'enabled': bool, 'formats': [field, ...]}; each field is positioned on the screen.
    CLOCK = 'clock'
    FORMATS = 'formats'


class SOUND_BANK_LOADER(object):
    NAME = 'sound_bank_loader'
    DEBUG = 'debug'


class GAME_LOG_MANAGER(object):
    NAME = 'game_log_manager'
    LOG_SWAPPER = 'logSwapper'
    WG_LOG_HIDE_CRITICS = 'wgLogHideCritics'
    WG_LOG_HIDE_BLOCK = 'wgLogHideBlock'
    WG_LOG_HIDE_ASSIST = 'wgLogHideAssist'


class PROFILE_RATINGS(object):
    NAME = 'profile_ratings'


class VEHICLE_MARKERS(object):
    RATINGS = ('wn8', 'wnx', 'eff')
    NAME = "vehicle_markers"
    # Persisted layout axes and document names shared by storage, settings and runtime.
    TEAMS = ('ally', 'enemy')
    STATES = ('alive', 'dead')
    MODES = ('normal', 'extended')
    STATE_KEYS = ('markersAliveNormal', 'markersAliveExtended', 'markersDeadNormal', 'markersDeadExtended')
    FILES = ('markers.json',) + tuple(key + '.json' for key in STATE_KEYS)


# Parent switch -> controls available only while it is enabled.
HANDLER_VALUES = {
    SIXTH_SENSE_ALERT.NAME: {
        SIXTH_SENSE_ALERT.DEFAULT_ICON: {SIXTH_SENSE_ALERT.DEFAULT_ICON_NAME: (True,), SIXTH_SENSE_ALERT.USER_ICON: (False,)},
        SIXTH_SENSE_ALERT.USER_SOUND: (SIXTH_SENSE_ALERT.SIXTH_SENSE_SOUND,),
        SIXTH_SENSE_ALERT.PLAY_TICK_SOUND: {SIXTH_SENSE_ALERT.SIXTH_SENSE_SOUND: (False,)},
        SIXTH_SENSE_ALERT.SHOW_TIMER_GRAPHICS: (SIXTH_SENSE_ALERT.SHOW_TIMER_GRAPHICS_COLOR, SIXTH_SENSE_ALERT.SHOW_TIMER_GRAPHICS_RADIUS),
        SIXTH_SENSE_ALERT.SPOTTED_MESSAGE: (SIXTH_SENSE_ALERT.SPOTTED_TEXT,),
    },
    BATTLE_MARKS_OF_EXCELLENCE.NAME: {
        BATTLE_MARKS_OF_EXCELLENCE.SHOW_TARGETS: ('gameface.showTargetDamage', 'gameface.showRequiredDamage'),
        BATTLE_MARKS_OF_EXCELLENCE.BACKGROUND: ('gameface.backgroundOpacity',)
    },
    TARGET_INFORMATION.NAME: {
        TARGET_INFORMATION.BACKGROUND_ENABLED: (TARGET_INFORMATION.BACKGROUND_ALPHA,)
    },
    CREW_MANAGEMENT.NAME: {
        CREW_MANAGEMENT.CREW_AUTO_RETURN: (CREW_MANAGEMENT.CREW_RETURN_BY_DEFAULT, CREW_MANAGEMENT.AUTO_RETURN_DELAY, CREW_MANAGEMENT.EXCLUDE_PREMIUM_VEHICLES)
    },
    HANGAR_PREFERENCES.NAME: {
        HANGAR_PREFERENCES.BLOCK_VEHICLE_IF_LOW_AMMO: (HANGAR_PREFERENCES.LOW_AMMO_PERCENTAGE,)
    },
    MINIMAP_ENHANCEMENTS.NAME: {
        MINIMAP_ENHANCEMENTS.SHOW_LAST_POSITIONS: (MINIMAP_ENHANCEMENTS.LAST_POSITION_DURATION, MINIMAP_ENHANCEMENTS.LOST_MARKER + '.showSeconds', MINIMAP_ENHANCEMENTS.LOST_MARKER + '.fade', MINIMAP_ENHANCEMENTS.LOST_MARKER + '.minimumAlpha'),
        MINIMAP_ENHANCEMENTS.CHANGE_COLOR_CIRCLES: (MINIMAP_ENHANCEMENTS.COLOR_DRAW_CIRCLE, MINIMAP_ENHANCEMENTS.COLOR_MAX_VIEW_CIRCLE, MINIMAP_ENHANCEMENTS.COLOR_MIN_SPOTTING_CIRCLE, MINIMAP_ENHANCEMENTS.COLOR_VIEW_CIRCLE),
        MINIMAP_ENHANCEMENTS.LABELS + '.customColors': tuple(MINIMAP_ENHANCEMENTS.LABELS + '.' + key for key in MINIMAP_ENHANCEMENTS.LABEL_COLOR_KEYS),
        MINIMAP_ENHANCEMENTS.NEARBY + '.enabled': tuple(MINIMAP_ENHANCEMENTS.NEARBY + '.' + key for key in ('range', 'distance', 'color', 'alpha')),
        MINIMAP_ENHANCEMENTS.LABELS + '.avoidOverlap': (MINIMAP_ENHANCEMENTS.LABELS + '.compactLength',),
        MINIMAP_ENHANCEMENTS.LOST_MARKER + '.fade': (MINIMAP_ENHANCEMENTS.LOST_MARKER + '.minimumAlpha',),
        MINIMAP_ENHANCEMENTS.LINES + '.customStyle': tuple(MINIMAP_ENHANCEMENTS.LINES + '.' + key for key in ('directionColor', 'sectorColor', 'alpha', 'geometry', 'thickness', 'dash', 'gap')),
        MINIMAP_ENHANCEMENTS.LINES + '.geometry': tuple(MINIMAP_ENHANCEMENTS.LINES + '.' + key for key in ('thickness', 'dash', 'gap')),
        MINIMAP_ENHANCEMENTS.PRESENTATION + '.alternativeEnabled': (MINIMAP_ENHANCEMENTS.BUTTON, MINIMAP_ENHANCEMENTS.ZOOM_FACTOR, MINIMAP_ENHANCEMENTS.ZOOM_FACTOR_MAX,
        MINIMAP_ENHANCEMENTS.PRESENTATION + '.zoom', MINIMAP_ENHANCEMENTS.PRESENTATION + '.center',
        MINIMAP_ENHANCEMENTS.PRESENTATION + '.alternativeAlpha', MINIMAP_ENHANCEMENTS.PRESENTATION + '.sizeIndex'),
        MINIMAP_ENHANCEMENTS.PRESENTATION + '.zoom': (MINIMAP_ENHANCEMENTS.ZOOM_FACTOR, MINIMAP_ENHANCEMENTS.ZOOM_FACTOR_MAX,
        MINIMAP_ENHANCEMENTS.PRESENTATION + '.center', MINIMAP_ENHANCEMENTS.PRESENTATION + '.sizeIndex'),
        MINIMAP_ENHANCEMENTS.HEALTH + '.visibility': dict((MINIMAP_ENHANCEMENTS.HEALTH + '.' + key, ('key', 'always')) for key in ('mode', 'x', 'y', 'width', 'height', 'fontSize')),
        MINIMAP_ENHANCEMENTS.HEALTH + '.mode': {
            MINIMAP_ENHANCEMENTS.HEALTH + '.width': ('bar',), MINIMAP_ENHANCEMENTS.HEALTH + '.height': ('bar',),
            MINIMAP_ENHANCEMENTS.HEALTH + '.fontSize': ('value', 'percent')
        }
    },
    TEAM_PANELS.NAME: {
        TEAM_PANELS.STATS_ENABLED: (TEAM_PANELS.RATING, TEAM_PANELS.COLOR_SCALE),
        TEAM_PANELS.HP_VISIBILITY: {TEAM_PANELS.HP_KEY: ('hold',)}
        },
    AIMING_RETICLES.NAME: {
        AIMING_RETICLES.SHOW_CLIENT_AND_SERVER_RETICLE_BETA: (
            AIMING_RETICLES.SERVER_RETICLE_AIMING_CIRCLE_SHAPE,
            AIMING_RETICLES.SERVER_RETICLE_AIMING_CIRCLE_OPACITY,
            AIMING_RETICLES.SERVER_RETICLE_GUN_MARKER_SHAPE,
            AIMING_RETICLES.SERVER_RETICLE_GUN_MARKER_OPACITY
        )
    },
    TECH_TREE_MARKS_OF_EXCELLENCE.NAME: {
        TECH_TREE_MARKS_OF_EXCELLENCE.SHOW_IN_TECH_TREE: (
            TECH_TREE_MARKS_OF_EXCELLENCE.SHOW_IN_TECH_TREE_MARK_OF_GUN_PERCENT,
            TECH_TREE_MARKS_OF_EXCELLENCE.SHOW_IN_TECH_TREE_MASTERY,
            TECH_TREE_MARKS_OF_EXCELLENCE.SHOW_IN_TECH_TREE_MARK_OF_GUN_TANK_NAME_COLORED,
            TECH_TREE_MARKS_OF_EXCELLENCE.BADGE_OFFSET_X, TECH_TREE_MARKS_OF_EXCELLENCE.BADGE_OFFSET_Y
        )
    },
    SNIPER_CAMERA.NAME: {
        SNIPER_CAMERA.DISABLE_CAM_AFTER_SHOT: (
            SNIPER_CAMERA.DISABLE_CAM_AFTER_SHOT_LATENCY,
            SNIPER_CAMERA.DISABLE_CAM_AFTER_SHOT_SKIP_CLIP
            )
    },
    BATTLE_PERFORMANCE.NAME: {
        BATTLE_PERFORMANCE.BATTLE_RESULTS_WINDOW: (BATTLE_PERFORMANCE.BATTLE_RESULTS_FORMAT,)
    },
}


# Flash component aliases shared by registration and controllers.
class BATTLE_ALIASES(object):
    DEBUG_PANEL = 'DriftkingsDebugPanel'
    TARGET_DISTANCE = 'DistanceMarkerView'
    SIXTH_SENSE_ALERT = 'SixthSenseView'
    MINIMAP = 'MinimapEnhancementsView'
    PLAYERS_PANEL = 'DriftkingsRatingScreens'
    OVERLAY = 'DriftkingsOverlay'
