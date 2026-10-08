# -*- coding: utf-8 -*-
"""Stable settings keys and UI aliases; no game imports.

ID preserves registry/i18n keys; NAME identifies the JSON section.
"""


class GLOBAL(object):
    ENABLED = 'enabled'
    X = 'x'
    Y = 'y'
    FONT = 'font'
    WIDTH = 'width'
    HEIGHT = 'height'
    ALPHA = 'alpha'
    COLOR = 'color'
    ALIGN = 'align'
    ALIGN_X = 'alignX'
    ALIGN_Y = 'alignY'
    TOP = 'top'
    BOTTOM = 'bottom'
    RIGHT = 'right'
    LEFT = 'left'
    CENTER = 'center'
    DISTANCE = 'distance'
    ANGLE = 'angle'
    SIZE = 'size'
    BLUR_X = 'blurX'
    BLUR_Y = 'blurY'
    STRENGTH = 'strength'
    SHADOW = 'shadow'
    QUALITY = 'quality'
    LEADING = 'leading'
    VISIBLE = 'visible'
    DRAG = 'drag'
    BORDER = 'border'
    INDEX = 'index'
    ZERO = 0
    ONE = 1
    LINE = '_'
    EMPTY_LYNE = '  '
    IMAGE = 'image'
    BLUR = 'blur'


class AIMING_ANGLES(object):
    ID = 'AimingAngles'
    NAME = 'aiming_angles'
    VERTICAL = 'vertical'
    HORIZONTAL = 'horizontal'


class ARCADE_ZOOM(object):
    ID = 'ArcadeZoom'
    NAME = 'arcade_zoom'
    MAX = 'max'
    MIN = 'min'
    SCROLL_SENSITIVITY = 'scrollSensitivity'
    START_DEAD_DIST = 'startDeadDist'


class ARMOR_CALCULATOR(object):
    ID = 'ArmorCalculator'
    NAME = 'armor_calculator'
    DISPLAY_ON_ALLIES = 'displayOnAllies'
    MESSAGES = 'messages'
    POSITION = 'position'
    TEMPLATE = 'template'


class ARTY_SPLASH(object):
    ID = 'ArtySplash'
    NAME = 'arty_splash'
    BUTTON_SHOW_DOT = 'buttonShowDot'
    BUTTON_SHOW_SPLASH = 'buttonShowSplash'
    SHOW_SPLASH_ON_DEFAULT = 'showSplashOnDefault'
    SHOW_DOT_ON_DEFAULT = 'showDotOnDefault'
    SHOW_MODE_ARCADE = 'showModeArcade'
    SHOW_MODE_SNIPER = 'showModeSniper'
    SHOW_MODE_ARTY = 'showModeArty'
    MODEL_PATH_SPLASH = 'modelPathSplash'
    MODEL_PATH_DOT = 'modelPathDot'


class AUTO_AIM_OPTIMIZE(object):
    ID = 'AutoAimOptimize'
    NAME = 'auto_aim_optimize'
    ANGLE = 'angle'
    CATCH_HIDDEN_TARGET = 'catchHiddenTarget'
    DISABLE_ARTY_MODE = 'disableArtyMode'


class BATTLE_EFFICIENCY(object):
    ID = 'BattleEfficiency'
    NAME = 'battle_efficiency'
    COLOR_RATTING = 'colorRatting'
    FORMAT = 'format'
    TEXT_STYLE = 'textStyle'
    TEXT_LOCK = 'textLock'
    POSITION = 'position'
    TEXT_SHADOW = 'textShadow'
    BATTLE_RESULTS_WINDOW = 'battleResultsWindow'
    BATTLE_RESULTS_FORMAT = 'battleResultsFormat'


class BATTLE_OPTIONS(object):
    ID = 'BattleOptions'
    NAME = 'battle_options'
    CLIP_LOAD = 'clipLoad'
    DIRECTIVES_ONLY_FROM_STORAGE = 'directivesOnlyFromStorage'
    DISABLE_SOUND_COMMANDER = 'disableSoundCommander'
    FORMAT = 'format'
    HIDE_BADGES = 'hideBadges'
    HIDE_BATTLE_PRESTIGE = 'hideBattlePrestige'
    HIDE_CLAN_NAME = 'hideClanName'
    IN_BATTLE = 'inBattle'
    LOAD_TXT = 'loadTxt'
    MAX_CHAT_LINES = 'maxChatLines'
    MUTE_TEAM_BASE_SOUND = 'muteTeamBaseSound'
    POSTMORTEM_TIPS = 'postmortemTips'
    SHOW_ANONYMOUS = 'showAnonymous'
    SHOW_BATTLE_HINT = 'showBattleHint'
    SHOW_FRIENDS = 'showFriends'
    SHOW_POSTMORTEM_DOG_TAG = 'showPostmortemDogTag'
    STUN_SOUND = 'stunSound'
    SHOW_PLAYER_SATISFACTION_WIDGET = 'showPlayerSatisfactionWidget'
    ADD_ENEMY_NAME = 'addEnemyName'
    HIDE_HINT = 'hideHint'


class BATTLE_STAT(object):
    ID = 'BattleStat'
    NAME = 'battle_stat'
    COLOR_RATING = 'colorRating'
    FORMAT = 'format'
    TEXT_LOCK = 'textLock'
    TEXT_POSITION = 'textPosition'
    TEXT_SHADOW = 'textShadow'
    TEXT_FORMAT = 'textFormat'


class DISPERSION_CIRCLE(object):
    ID = 'DispersionCircle'
    NAME = 'dispersion_circle'
    SHOW_CLIENT_AND_SERVER_RETICLE = 'showClientAndServerReticle'
    GUN_MARKER_MINIMUM_SIZE = 'gunMarkerMinimumSize'
    PERCENT_CORRECTION = 'percentCorrection'
    SHOW_CLIENT_AND_SERVER_RETICLE_BETA = 'showClientAndServerReticleBeta'
    SHOW_SERVER_SPG_STRATEGIC_RETICLE = 'showServerSpgStrategicReticle'
    SERVER_RETICLE_AIMING_CIRCLE_SHAPE = 'serverReticleAimingCircleShape'
    SERVER_RETICLE_AIMING_CIRCLE_OPACITY = 'serverReticleAimingCircleOpacity'
    SERVER_RETICLE_GUN_MARKER_SHAPE = 'serverReticleGunMarkerShape'
    SERVER_RETICLE_GUN_MARKER_OPACITY = 'serverReticleGunMarkerOpacity'


class DISPERSION_TIMER(object):
    ID = 'DispersionTimer'
    NAME = 'dispersion_timer'
    RED = 'red'
    ORANGE = 'orange'
    YELLOW = 'yellow'
    GREEN = 'green'
    BLUE = 'blue'
    PURPLE = 'purple'
    TEMPLATE = 'template'


class DISTANCE_MARKER(object):
    ID = 'DistanceMarker'
    NAME = 'distance_marker'
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


class FLIGHT_TIMER(object):
    ID = 'FlightTimer'
    NAME = 'flight_timer'
    SPG_ONLY = 'spgOnly'
    TEMPLATE = 'template'


class INFO_PANEL(object):
    ID = 'InfoPanel'
    NAME = 'info_panel'
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


class MAIN_GUN(object):
    ID = 'MainGun'
    NAME = 'main_gun'
    BACK_GROUND_ENABLED = 'backGroundEnabled'
    TEXT_LOCK = 'textLock'
    FORMAT = 'format'
    BACKGROUND = 'background'
    MAIN_GUN = 'mainGun'
    SHADOW = 'shadow'
    TEXT_POSITION = 'textPosition'


class MARKS_ON_GUN_BATTLE(object):
    ID = 'MarksOnGunBattle'
    NAME = 'marks_on_gun_battle'
    COLOR_RATING = 'colorRating'
    BUTTON_SHOW = 'buttonShow'
    BUTTON_SIZE_UP = 'buttonSizeUp'
    BUTTON_SIZE_DOWN = 'buttonSizeDown'
    BUTTON_RESET = 'buttonReset'
    SHOW_IN_BATTLE = 'showInBattle'
    SHOW_IN_BATTLE_HALF_PERCENTS = 'showInBattleHalfPercents'
    SHOW_IN_REPLAY = 'showInReplay'
    SHOW_IN_STATISTIC = 'showInStatistic'
    SHOW_IN_HANGAR = 'showInHangar'
    BACKGROUND = 'background'
    PANEL_SIZE = 'panelSize'
    PANEL = 'panel'
    BATTLE_MESSAGE = 'battleMessage'
    BATTLE_MESSAGE_ALT = 'battleMessageAlt'
    BATTLE_MESSAGE_STATUS_UP = 'battleMessage{status}Up'
    BATTLE_MESSAGE_C_STATUS_UP = 'battleMessage{c_status}Up'
    BATTLE_MESSAGE_STATUS_DOWN = 'battleMessage{status}Down'
    BATTLE_MESSAGE_C_STATUS_DOWN = 'battleMessage{c_status}Down'
    BATTLE_MESSAGE_STATUS_UNKNOWN = 'battleMessage{status}Unknown'
    BATTLE_MESSAGE_C_STATUS_UNKNOWN = 'battleMessage{c_status}Unknown'
    BATTLE_MESSAGE_BATTLE_MARK_OF_GUN = 'battleMessage{battleMarkOfGun}'
    BATTLE_MESSAGE_C_BATTLE_MARK_OF_GUN = 'battleMessage{c_battleMarkOfGun}'
    BATTLE_MESSAGE_CURRENT_MARK_OF_GUN = 'battleMessage{currentMarkOfGun}'
    BATTLE_MESSAGE_C_CURRENT_MARK_OF_GUN = 'battleMessage{c_currentMarkOfGun}'
    BATTLE_MESSAGE_NEXT_MARK_OF_GUN = 'battleMessage{nextMarkOfGun}'
    BATTLE_MESSAGE_C_NEXT_MARK_OF_GUN = 'battleMessage{c_nextMarkOfGun}'
    BATTLE_MESSAGE_DAMAGE_CURRENT = 'battleMessage{damageCurrent}'
    BATTLE_MESSAGE_C_DAMAGE_CURRENT = 'battleMessage{c_damageCurrent}'
    BATTLE_MESSAGE_DAMAGE_CURRENT_PERCENT = 'battleMessage{damageCurrentPercent}'
    BATTLE_MESSAGE_C_DAMAGE_CURRENT_PERCENT = 'battleMessage{c_damageCurrentPercent}'
    BATTLE_MESSAGE_DAMAGE_NEXT_PERCENT = 'battleMessage{damageNextPercent}'
    BATTLE_MESSAGE_C_DAMAGE_NEXT_PERCENT = 'battleMessage{c_damageNextPercent}'
    BATTLE_MESSAGE_DAMAGE_TO_MARK65 = 'battleMessage{damageToMark65}'
    BATTLE_MESSAGE_C_DAMAGE_TO_MARK65 = 'battleMessage{c_damageToMark65}'
    BATTLE_MESSAGE_DAMAGE_TO_MARK85 = 'battleMessage{damageToMark85}'
    BATTLE_MESSAGE_C_DAMAGE_TO_MARK85 = 'battleMessage{c_damageToMark85}'
    BATTLE_MESSAGE_DAMAGE_TO_MARK95 = 'battleMessage{damageToMark95}'
    BATTLE_MESSAGE_C_DAMAGE_TO_MARK95 = 'battleMessage{c_damageToMark95}'
    BATTLE_MESSAGE_DAMAGE_TO_MARK100 = 'battleMessage{damageToMark100}'
    BATTLE_MESSAGE_C_DAMAGE_TO_MARK100 = 'battleMessage{c_damageToMark100}'
    BATTLE_MESSAGE_DAMAGE_TO_MARK_INFO = 'battleMessage{damageToMarkInfo}'
    BATTLE_MESSAGE_C_DAMAGE_TO_MARK_INFO = 'battleMessage{c_damageToMarkInfo}'
    BATTLE_MESSAGE_DAMAGE_TO_MARK_INFO_LEVEL = 'battleMessage{damageToMarkInfoLevel}'
    BATTLE_MESSAGE_C_DAMAGE_TO_MARK_INFO_LEVEL = 'battleMessage{c_damageToMarkInfoLevel}'
    BATTLE_MESSAGE_SIZE_IN_PERCENT = 'battleMessageSizeInPercent'
    BATTLE_MESSAGE_ASSIST_SPOT = 'battleMessage{assistSpot}'
    BATTLE_MESSAGE_ASSIST_TRACK = 'battleMessage{assistTrack}'
    BATTLE_MESSAGE_ASSIST_SPAM = 'battleMessage{assistSpam}'
    UI = 'UI'


class MINIMAP_PLUGINS(object):
    ID = 'MinimapPlugins'
    NAME = 'minimap_plugins'
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
    CIRCLES = 'circles'
    EXTRA_CIRCLES = 'extraCircles'
    LINES = 'lines'
    ARTILLERY_AIM = 'artilleryAim'
    PRESENTATION = 'presentation'
    BUTTON = 'button'


class OWN_HEALTH(object):
    ID = 'OwnHealth'
    NAME = 'own_health'
    AVG_COLOR = 'avgColor'
    COLORS = 'colors'


class PLAYER_PANEL_PRO(object):
    ID = 'PlayerPanelPro'
    NAME = 'player_panel_pro'
    STATS_ENABLED = 'statsEnabled'
    COLOR_SCALE = 'colorScale'
    RATING = 'rating'
    PERFORMANCE = 'performance'
    HP_ENABLED = 'hpEnabled'
    HP_VISIBILITY = 'hpVisibility'
    HP_KEY = 'hpKey'
    SPOTTED_ENABLED = 'spottedEnabled'
    SCHEMA_VERSION = 'schemaVersion'
    PLAYERS_PANEL = 'playersPanel'
    PROFILES = 'profiles'
    TEMPLATES = 'templates'
    LOADING = 'loading'
    TAB = 'tab'


class REPAIR_EXTENDED(object):
    ID = 'RepairExtended'
    NAME = 'repair_extended'
    BUTTON_CHASSIS = 'buttonChassis'
    BUTTON_REPAIR = 'buttonRepair'
    AUTO_REPAIR = 'autoRepair'
    REMOVE_STUN = 'removeStun'
    EXTINGUISH_FIRE = 'extinguishFire'
    HEAL_CREW = 'healCrew'
    REPAIR_DEVICES = 'repairDevices'
    RESTORE_CHASSIS = 'restoreChassis'
    USE_GOLD_KITS = 'useGoldKits'
    TIMER_MIN = 'timerMin'
    TIMER_MAX = 'timerMax'
    REPAIR_PRIORITY = 'repairPriority'


class SAFE_SHOT(object):
    ID = 'SafeShot'
    NAME = 'safe_shot'
    WASTE_SHOT_BLOCK = 'wasteShotBlock'
    TEAM_SHOT_BLOCK = 'teamShotBlock'
    TEAM_KILLER_SHOT_UNBLOCK = 'teamKillerShotUnblock'
    DEAD_SHOT_BLOCK = 'deadShotBlock'
    DEAD_SHOT_BLOCK_TIME_OUT = 'deadShotBlockTimeOut'
    DISABLE_KEY = 'disableKey'
    ACTIVATE_MESSAGE = 'activateMessage'
    TRIGGER_MESSAGE = 'triggerMessage'
    CLIENT_MESSAGES = 'clientMessages'
    CHAT_MESSAGES = 'chatMessages'


class SERVER_TURRET_EXTENDED(object):
    ID = 'ServerTurretExtended'
    NAME = 'server_turret_extended'
    ACTIVATE_MESSAGE = 'activateMessage'
    FIX_ACCURACY_IN_MOVE = 'fixAccuracyInMove'
    SERVER_TURRET = 'serverTurret'
    FIX_WHEEL_CRUISE_CONTROL = 'fixWheelCruiseControl'
    AUTO_ACTIVATE_WHEEL_MODE = 'autoActivateWheelMode'
    MAX_WHEEL_MODE = 'maxWheelMode'
    BUTTON_AUTO_MODE = 'buttonAutoMode'
    BUTTON_MAX_MODE = 'buttonMaxMode'


class SIXTH_SENSE(object):
    ID = 'SixthSense'
    NAME = 'sixth_sense'
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


class SPOTTED_EXTENDED_LIGHT(object):
    ID = 'SpottedExtendedLight'
    NAME = 'spotted_extended_light'
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


class ZOOM_EXTENDED(object):
    ID = 'ZoomExtended'
    NAME = 'zoom_extended'
    NO_BINOCULARS = 'noBinoculars'
    NO_FLASH_BANG = 'noFlashBang'
    NO_SHOCK_WAVE = 'noShockWave'
    NO_SNIPER_DYNAMIC = 'noSniperDynamic'
    DISABLE_CAM_AFTER_SHOT = 'disableCamAfterShot'
    DISABLE_CAM_AFTER_SHOT_LATENCY = 'disableCamAfterShotLatency'
    DISABLE_CAM_AFTER_SHOT_SKIP_CLIP = 'disableCamAfterShotSkipClip'
    DYNAMIC_ZOOM = 'dynamicZoom'
    ZOOM_STEPS = 'zoomSteps'


class ACCOUNT_MANAGER(object):
    ID = 'AccountManager'
    NAME = 'account_manager'


class AUTO_CLAIM_CLAN(object):
    ID = 'AutoClaimClan'
    NAME = 'auto_claim_clan'


class CAROUSEL_STATS(object):
    ID = 'CarouselStats'
    NAME = 'carousel_stats'
    SORTING_CRITERIA = 'sortingCriteria'
    NATIONS_ORDER = 'nationsOrder'
    TYPES_ORDER = 'typesOrder'
    COLOR_RATING = 'colorRating'
    SHOW_ICONS = 'showIcons'
    CAROUSEL = 'carousel'


class CREW_SETTINGS(object):
    ID = 'CrewSettings'
    NAME = 'crew_settings'
    CREW_AUTO_RETURN = 'crewAutoReturn'
    CREW_RETURN_BY_DEFAULT = 'crewReturnByDefault'
    AUTO_RETURN_DELAY = 'autoReturnDelay'
    SHOW_NOTIFICATIONS = 'showNotifications'
    EXCLUDE_PREMIUM_VEHICLES = 'excludePremiumVehicles'


class HANGAR_OPTIONS(object):
    ID = 'HangarOptions'
    NAME = 'hangar_options'
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
    CLOCK = 'clock'
    CLOCK_STYLE = 'clockStyle'
    CLOCK_X = 'clockX'
    CLOCK_Y = 'clockY'
    CLOCK_SCALE = 'clockScale'
    CLOCK_SECONDS = 'clockSeconds'
    CLOCK24_HOUR = 'clock24Hour'
    SHOW_BATTLE_PASS_WIDGET = 'showBattlePassWidget'
    BLOCK_VEHICLE_IF_LOW_AMMO = 'blockVehicleIfLowAmmo'
    LOW_AMMO_PERCENTAGE = 'lowAmmoPercentage'
    CUSTOM_CLOCK_FORMAT = 'customClockFormat'
    TEXT = 'text'
    CUSTOM_CLOCK_TEXT = 'customClockText'
    PANEL = 'panel'


class MARKS_ON_GUN_HANGAR(object):
    ID = 'MarksOnGunHangar'
    NAME = 'marks_on_gun_hangar'
    SHOW_IN_HANGAR = 'showInHangar'
    SHOW_IN_STATISTIC = 'showInStatistic'
    TEXT_LOCK = 'textLock'
    GOAL_SELECTION = 'goalSelection'
    COMPACT_MODE = 'compactMode'
    HISTORY_BATTLES = 'historyBattles'
    SHOW_TOOLTIP_TARGETS = 'showTooltipTargets'
    COLOR_RATING = 'colorRating'
    STAR_ANIMATION_WINDOW = 'starAnimationWindow'
    PANEL = 'panel'
    CARD = 'card'


class MARKS_ON_GUN_TECH_TREE(object):
    ID = 'MarksOnGunTechTree'
    NAME = 'marks_on_gun_tech_tree'
    COLOR_RATING = 'colorRating'
    SHOW_IN_TECH_TREE = 'showInTechTree'
    SHOW_IN_TECH_TREE_MARK_OF_GUN_PERCENT = 'showInTechTreeMarkOfGunPercent'
    SHOW_IN_TECH_TREE_MASTERY = 'showInTechTreeMastery'
    SHOW_IN_TECH_TREE_MARK_OF_GUN_TANK_NAME_COLORED = 'showInTechTreeMarkOfGunTankNameColored'
    BADGE_OFFSET_X = 'badgeOffsetX'
    BADGE_OFFSET_Y = 'badgeOffsetY'
    BADGE_FONT_SIZE = 'badgeFontSize'


class BANKS_LOADER(object):
    ID = 'BanksLoader'
    NAME = 'banks_loader'
    DEFAULT_POOL = 'defaultPool'
    LOW_ENGINE_POOL = 'lowEnginePool'
    MEMORY_LIMIT = 'memoryLimit'
    STREAMING_POOL = 'streamingPool'
    IOPOOL_SIZE = 'IOPoolSize'
    MAX_VOICES = 'max_voices'
    DEBUG = 'debug'


class LOGS_SWAPPER(object):
    ID = 'LogsSwapper'
    NAME = 'logs_swapper'
    LOG_SWAPPER = 'logSwapper'
    WG_LOG_HIDE_CRITICS = 'wgLogHideCritics'
    WG_LOG_HIDE_BLOCK = 'wgLogHideBlock'
    WG_LOG_HIDE_ASSIST = 'wgLogHideAssist'


# Activation is owned by component_list.py; this is the settings catalogue.
CONFIG_SECTIONS = (
    AIMING_ANGLES,
    ARCADE_ZOOM,
    ARMOR_CALCULATOR,
    ARTY_SPLASH,
    AUTO_AIM_OPTIMIZE,
    BATTLE_EFFICIENCY,
    BATTLE_OPTIONS,
    BATTLE_STAT,
    DISPERSION_CIRCLE,
    DISPERSION_TIMER,
    DISTANCE_MARKER,
    FLIGHT_TIMER,
    INFO_PANEL,
    MAIN_GUN,
    MARKS_ON_GUN_BATTLE,
    MINIMAP_PLUGINS,
    OWN_HEALTH,
    PLAYER_PANEL_PRO,
    REPAIR_EXTENDED,
    SAFE_SHOT,
    SERVER_TURRET_EXTENDED,
    SIXTH_SENSE,
    SPOTTED_EXTENDED_LIGHT,
    ZOOM_EXTENDED,
    ACCOUNT_MANAGER,
    AUTO_CLAIM_CLAN,
    CAROUSEL_STATS,
    CREW_SETTINGS,
    HANGAR_OPTIONS,
    MARKS_ON_GUN_HANGAR,
    MARKS_ON_GUN_TECH_TREE,
    BANKS_LOADER,
    LOGS_SWAPPER,
)
CONFIG_BY_ID = dict((section.ID, section) for section in CONFIG_SECTIONS)


# Parent switch -> controls available only while it is enabled.
HANDLER_VALUES = {
    SIXTH_SENSE.ID: {
        SIXTH_SENSE.DEFAULT_ICON: {SIXTH_SENSE.DEFAULT_ICON_NAME: (True,), SIXTH_SENSE.USER_ICON: (False,)},
        SIXTH_SENSE.USER_SOUND: (SIXTH_SENSE.SIXTH_SENSE_SOUND,),
        SIXTH_SENSE.PLAY_TICK_SOUND: {SIXTH_SENSE.SIXTH_SENSE_SOUND: (False,)},
        SIXTH_SENSE.SHOW_TIMER_GRAPHICS: (SIXTH_SENSE.SHOW_TIMER_GRAPHICS_COLOR,
                                        SIXTH_SENSE.SHOW_TIMER_GRAPHICS_RADIUS),
        SIXTH_SENSE.SPOTTED_MESSAGE: (SIXTH_SENSE.SPOTTED_TEXT,),
    },
    SAFE_SHOT.ID: {
        SAFE_SHOT.DEAD_SHOT_BLOCK: (SAFE_SHOT.DEAD_SHOT_BLOCK_TIME_OUT,),
        SAFE_SHOT.TEAM_SHOT_BLOCK: (SAFE_SHOT.TEAM_KILLER_SHOT_UNBLOCK,)},
    INFO_PANEL.ID: {INFO_PANEL.BACKGROUND_ENABLED: (INFO_PANEL.BACKGROUND_ALPHA,)},
    REPAIR_EXTENDED.ID: {REPAIR_EXTENDED.AUTO_REPAIR: (REPAIR_EXTENDED.TIMER_MIN, REPAIR_EXTENDED.TIMER_MAX)},
    CREW_SETTINGS.ID: {CREW_SETTINGS.CREW_AUTO_RETURN: (
        CREW_SETTINGS.CREW_RETURN_BY_DEFAULT, CREW_SETTINGS.AUTO_RETURN_DELAY,
        CREW_SETTINGS.EXCLUDE_PREMIUM_VEHICLES)},
    HANGAR_OPTIONS.ID: {
        HANGAR_OPTIONS.CLOCK: (HANGAR_OPTIONS.CLOCK_STYLE, HANGAR_OPTIONS.CLOCK_X, HANGAR_OPTIONS.CLOCK_Y,
                              HANGAR_OPTIONS.CLOCK_SCALE, HANGAR_OPTIONS.CLOCK_SECONDS, HANGAR_OPTIONS.CLOCK24_HOUR),
        HANGAR_OPTIONS.BLOCK_VEHICLE_IF_LOW_AMMO: (HANGAR_OPTIONS.LOW_AMMO_PERCENTAGE,)},
    MINIMAP_PLUGINS.ID: {
        MINIMAP_PLUGINS.SHOW_LAST_POSITIONS: (MINIMAP_PLUGINS.LAST_POSITION_DURATION,
            MINIMAP_PLUGINS.LOST_MARKER + '.showSeconds', MINIMAP_PLUGINS.LOST_MARKER + '.fade',
            MINIMAP_PLUGINS.LOST_MARKER + '.minimumAlpha'),
        MINIMAP_PLUGINS.CHANGE_COLOR_CIRCLES: (
            MINIMAP_PLUGINS.COLOR_DRAW_CIRCLE, MINIMAP_PLUGINS.COLOR_MAX_VIEW_CIRCLE,
            MINIMAP_PLUGINS.COLOR_MIN_SPOTTING_CIRCLE, MINIMAP_PLUGINS.COLOR_VIEW_CIRCLE),
        MINIMAP_PLUGINS.LABELS + '.customColors': tuple(MINIMAP_PLUGINS.LABELS + '.' + key
            for key in ('allyColor', 'enemyColor', 'squadColor', 'deadColor')),
        MINIMAP_PLUGINS.LABELS + '.avoidOverlap': (MINIMAP_PLUGINS.LABELS + '.compactLength',),
        MINIMAP_PLUGINS.LOST_MARKER + '.fade': (MINIMAP_PLUGINS.LOST_MARKER + '.minimumAlpha',),
        MINIMAP_PLUGINS.LINES + '.customStyle': tuple(MINIMAP_PLUGINS.LINES + '.' + key
            for key in ('directionColor', 'sectorColor', 'alpha', 'geometry', 'length', 'thickness', 'dash', 'gap')),
        MINIMAP_PLUGINS.LINES + '.geometry': tuple(MINIMAP_PLUGINS.LINES + '.' + key
            for key in ('length', 'thickness', 'dash', 'gap')),
        MINIMAP_PLUGINS.PRESENTATION + '.alternativeEnabled': (
            MINIMAP_PLUGINS.BUTTON, MINIMAP_PLUGINS.ZOOM_FACTOR, MINIMAP_PLUGINS.ZOOM_FACTOR_MAX,
            MINIMAP_PLUGINS.PRESENTATION + '.zoom', MINIMAP_PLUGINS.PRESENTATION + '.center',
            MINIMAP_PLUGINS.PRESENTATION + '.alternativeAlpha', MINIMAP_PLUGINS.PRESENTATION + '.sizeIndex'),
        MINIMAP_PLUGINS.PRESENTATION + '.zoom': (MINIMAP_PLUGINS.ZOOM_FACTOR, MINIMAP_PLUGINS.ZOOM_FACTOR_MAX,
            MINIMAP_PLUGINS.PRESENTATION + '.center', MINIMAP_PLUGINS.PRESENTATION + '.sizeIndex'),
        MINIMAP_PLUGINS.HEALTH + '.visibility': dict((MINIMAP_PLUGINS.HEALTH + '.' + key, ('key', 'always'))
            for key in ('mode', 'x', 'y', 'width', 'height', 'fontSize')),
        MINIMAP_PLUGINS.HEALTH + '.mode': {
            MINIMAP_PLUGINS.HEALTH + '.width': ('bar',), MINIMAP_PLUGINS.HEALTH + '.height': ('bar',),
            MINIMAP_PLUGINS.HEALTH + '.fontSize': ('value', 'percent')}},
    PLAYER_PANEL_PRO.ID: {
        PLAYER_PANEL_PRO.STATS_ENABLED: (PLAYER_PANEL_PRO.RATING, PLAYER_PANEL_PRO.COLOR_SCALE),
        PLAYER_PANEL_PRO.HP_VISIBILITY: {PLAYER_PANEL_PRO.HP_KEY: ('hold',)}},
    SERVER_TURRET_EXTENDED.ID: {SERVER_TURRET_EXTENDED.FIX_WHEEL_CRUISE_CONTROL: (
        SERVER_TURRET_EXTENDED.BUTTON_AUTO_MODE, SERVER_TURRET_EXTENDED.BUTTON_MAX_MODE,
        SERVER_TURRET_EXTENDED.MAX_WHEEL_MODE, SERVER_TURRET_EXTENDED.AUTO_ACTIVATE_WHEEL_MODE)},
    DISPERSION_CIRCLE.ID: {DISPERSION_CIRCLE.SHOW_CLIENT_AND_SERVER_RETICLE_BETA: (
        DISPERSION_CIRCLE.SERVER_RETICLE_AIMING_CIRCLE_SHAPE, DISPERSION_CIRCLE.SERVER_RETICLE_AIMING_CIRCLE_OPACITY,
        DISPERSION_CIRCLE.SERVER_RETICLE_GUN_MARKER_SHAPE, DISPERSION_CIRCLE.SERVER_RETICLE_GUN_MARKER_OPACITY)},
    MARKS_ON_GUN_TECH_TREE.ID: {MARKS_ON_GUN_TECH_TREE.SHOW_IN_TECH_TREE: (
        MARKS_ON_GUN_TECH_TREE.SHOW_IN_TECH_TREE_MARK_OF_GUN_PERCENT,
        MARKS_ON_GUN_TECH_TREE.SHOW_IN_TECH_TREE_MASTERY,
        MARKS_ON_GUN_TECH_TREE.SHOW_IN_TECH_TREE_MARK_OF_GUN_TANK_NAME_COLORED,
        MARKS_ON_GUN_TECH_TREE.BADGE_OFFSET_X, MARKS_ON_GUN_TECH_TREE.BADGE_OFFSET_Y)},
    ZOOM_EXTENDED.ID: {ZOOM_EXTENDED.DISABLE_CAM_AFTER_SHOT: (
        ZOOM_EXTENDED.DISABLE_CAM_AFTER_SHOT_LATENCY, ZOOM_EXTENDED.DISABLE_CAM_AFTER_SHOT_SKIP_CLIP)},
    BATTLE_EFFICIENCY.ID: {BATTLE_EFFICIENCY.BATTLE_RESULTS_WINDOW: (BATTLE_EFFICIENCY.BATTLE_RESULTS_FORMAT,)},
}


class BATTLE_ALIASES(object):
    ARMOR_CALCULATOR = 'ArmorCalculatorView'
    DISPERSION_TIMER = 'DispersionTimerView'
    DISTANCE_MARKER = 'DistanceMarkerView'
    FLIGHT_TIMER = 'FlightTimerView'
    OWN_HEALTH = 'OwnHealthView'
    SIXTH_SENSE = 'SixthSenseView'
    MINIMAP = 'MinimapCentredView'
    PLAYERS_PANEL = 'DriftkingsRatingScreens'
    OVERLAY = 'DriftkingsOverlay'
