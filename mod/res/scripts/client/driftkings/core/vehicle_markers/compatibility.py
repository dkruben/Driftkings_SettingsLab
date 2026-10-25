# -*- coding: utf-8 -*-
"""Conservative scope for the first independent EU marker release."""
# Values confirmed in the pinned EU 2.4.1 constants: random and training.
SUPPORTED_GUI_TYPES = (1, 2)


def supported(manager_name, gui_type):
    return manager_name == 'MarkersManager' and gui_type in SUPPORTED_GUI_TYPES


def manager_supported(manager):
    import BigWorld
    player = BigWorld.player()
    arena = getattr(player, 'arena', None)
    return supported(type(manager).__name__, getattr(arena, 'guiType', None))
