# -*- coding: utf-8 -*-
"""Client-owned enums; keep engine-free constants in _constants."""
from aih_constants import CTRL_MODE_NAME, GUN_MARKER_TYPE, SHOT_RESULT
from BattleFeedbackCommon import BATTLE_EVENT_TYPE
from constants import ARENA_PERIOD, SHELL_MECHANICS_TYPE, SHELL_TYPES

# Native feedback event groups; no settings keys or UI aliases belong here.
ASSIST_EVENTS = (
    BATTLE_EVENT_TYPE.RADIO_ASSIST, BATTLE_EVENT_TYPE.TRACK_ASSIST,
    BATTLE_EVENT_TYPE.STUN_ASSIST,
)

DAMAGE_EVENTS = frozenset(ASSIST_EVENTS + (
    BATTLE_EVENT_TYPE.DAMAGE,
    BATTLE_EVENT_TYPE.TANKING, BATTLE_EVENT_TYPE.RECEIVED_DAMAGE,
))
