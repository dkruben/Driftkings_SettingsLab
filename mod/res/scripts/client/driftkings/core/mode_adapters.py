# -*- coding: utf-8 -*-
"""Team panel support per battle mode; no game imports.

A mode without an adapter is left to the native client: no roster is drawn,
no panel mode is forced and native hooks only pass through.
"""
from collections import namedtuple

from driftkings._constants import TEAM_PANELS

# Native PLAYERS_PANEL_STATE profiles of the classic panel (settings_data.PROFILES).
CLASSIC_PANEL_MODES = TEAM_PANELS.MODES
# tab: which TAB view gets the roster ('classic' TabView, 'halloween' TabScreen) or None.
# order: 'native' follows the statistics exchange (captureOrder); 'mod' sorts the
# roster here, for modes whose exchange is incomplete.
# event_numbers: show numeric statistics although the mode is an event mode.
ModeAdapter = namedtuple('ModeAdapter', ('mode', 'loading', 'panel', 'tab', 'enemies', 'team_size',
                                         'panel_modes', 'order', 'event_numbers'))

ADAPTERS = {
    # RANDOM_RANGE includes EPIC_RANDOM (30 vs 30) besides the 15 vs 15 randoms.
    'random': ModeAdapter('random', loading=True, panel=True, tab='classic', enemies=True, team_size=30,
                          panel_modes=CLASSIC_PANEL_MODES, order='native', event_numbers=False),
    # HWPlayersPanel (allies only, no panel modes), Gameface loading and TabScreen.
    # The panel AS3 layout is not in the reference sources, so nothing is drawn
    # over it until the alignment is validated in game. The TAB gets a separate
    # allies table with numeric statistics, beside the native content.
    'halloween': ModeAdapter('halloween', loading=False, panel=False, tab='halloween', enemies=False, team_size=5,
                             panel_modes=(), order='mod', event_numbers=True),
}


def adapter_for(mode):
    return ADAPTERS.get(mode)


# Native battle class order (gui.shared.gui_items.Vehicle.VEHICLE_BATTLE_TYPES_ORDER).
CLASS_ORDER = ('heavyTank', 'mediumTank', 'AT-SPG', 'lightTank', 'SPG')


def _class_index(tags):
    return next((index for index, tag in enumerate(CLASS_ORDER) if tag in tags), len(CLASS_ORDER))


def sort_key(vehicle):
    """Halloween's HWSortKey: team, alive first, class, vehicle name, player name."""
    descriptor = getattr(vehicle.get('vehicleType'), 'type', None)
    return (vehicle.get('team', 0), not vehicle.get('isAlive', True),
            _class_index(getattr(descriptor, 'tags', ()) or ()),
            (getattr(descriptor, 'shortUserString', '') or '').upper(), (vehicle.get('name', '') or '').upper())


def roster_order(vehicles):
    return [ident for ident, _ in sorted(vehicles.items(), key=lambda item: (sort_key(item[1]), item[0]))]
