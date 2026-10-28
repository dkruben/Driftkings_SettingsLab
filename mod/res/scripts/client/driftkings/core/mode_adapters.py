# -*- coding: utf-8 -*-
"""Team panel support per battle mode; no game imports.

A mode without an adapter is left to the native client: no roster is drawn,
no panel mode is forced and native hooks only pass through.
"""
from collections import namedtuple

# Native PLAYERS_PANEL_STATE profiles of the classic panel (settings_data.PROFILES).
CLASSIC_PANEL_MODES = ('none', 'short', 'medium', 'medium2', 'large')
# order: 'native' follows the statistics exchange (captureOrder); 'mod' sorts the
# roster here, for modes whose exchange is incomplete.
ModeAdapter = namedtuple('ModeAdapter', ('mode', 'loading', 'panel', 'tab', 'enemies', 'team_size',
                                         'panel_modes', 'order'))

ADAPTERS = {
    'random': ModeAdapter('random', loading=True, panel=True, tab=True, enemies=True, team_size=15,
                          panel_modes=CLASSIC_PANEL_MODES, order='native'),
    # HWPlayersPanel (allies only, no panel modes), Gameface loading and TabScreen.
    # The panel AS3 layout is not in the reference sources, so nothing is drawn
    # over it until the alignment is validated in game.
    'halloween': ModeAdapter('halloween', loading=False, panel=False, tab=False, enemies=False, team_size=5,
                             panel_modes=(), order='mod'),
}


def adapter_for(mode):
    return ADAPTERS.get(mode)
