# -*- coding: utf-8 -*-
"""Small client helpers. Resource and replay dependencies are loaded on demand."""
import math
import os

import BigWorld

_xvm_installed = None
_battle_types = None


def create_range(obj, names):
    return tuple(getattr(obj, name) for name in names if hasattr(obj, name))


def getBattleTypes():
    global _battle_types
    if _battle_types is not None:
        return _battle_types
    from constants import ARENA_GUI_TYPE
    _battle_types = create_range(ARENA_GUI_TYPE, (
        'COMP7', 'EPIC_BATTLE', 'EPIC_RANDOM', 'EPIC_RANDOM_TRAINING',
        'FORT_BATTLE_2', 'MAPBOX', 'RANDOM', 'RANKED', 'SORTIE_2',
        'TOURNAMENT_COMP7', 'TRAINING', 'UNKNOWN', 'WINBACK'))
    return _battle_types


def isXvmInstalled():
    global _xvm_installed
    if _xvm_installed is None:
        _xvm_installed = _findXvm()
    return _xvm_installed


def _findXvm():
    import ResMgr
    cwd = os.getcwdu() if hasattr(os, 'getcwdu') else os.getcwd()
    paths = ResMgr.openSection(os.path.join(cwd, 'paths.xml'))
    if paths is None or paths['Paths'] is None:
        return False
    for section in paths['Paths'].values():
        if './mods/' in section.asString:
            mods = os.path.realpath(os.path.join(cwd, os.path.normpath(section.asString)))
            xfw = os.path.exists(os.path.join(mods, 'com.modxvm.xfw'))
            xvm = os.path.exists(os.path.join(cwd, 'res_mods', 'mods', 'xfw_packages', 'xvm_main'))
            return xfw and xvm
    return False


def isReplay():
    """
    Check if the current session is a replay.
    bool: True if in replay mode, False otherwise.
    """
    from BattleReplay import isLoading, isPlaying
    return isPlaying() or isLoading()


def getPlayer():
    """
    Get the current player entity.
    object: The player entity.
    """
    return BigWorld.player()


def getTarget():
    """
    Get the current target entity.
    object: The target entity or None if no target.
    """
    return BigWorld.target()


def getEntity(entityID):
    """
    Get an entity by its ID.
    entityID (int): The entity ID to look up.
    object: The entity or None if not found.
    """
    return BigWorld.entity(entityID)


class SquarePosition(object):
    """
    Class to determine the grid square position of the player on the map.
    """

    def __call__(self):
        """
        Calculate the current square position of the player.
        str: The grid square position in format 'A1', 'B2', etc.
        """
        return self.getSquarePosition()

    @staticmethod
    def clamp(val, v_max):
        """
        Clamp a value between a minimum and maximum.
        val: The value to clamp
        v_max: The maximum allowed value
        float: The clamped value
        """
        v_min = 0.1
        return v_min if (val < v_min) else v_max if (val > v_max) else val

    @staticmethod
    def pos2name(pos):
        """
        Convert a position tuple to a grid square name.
        pos: Tuple containing (x, y) position
        str: Grid square name (e.g. 'A1', 'B2')
        """
        squareName = 'KJHGFEDCBA'
        linesName = '1234567890'
        return '{}{}'.format(squareName[int(pos[1]) - 1], linesName[int(pos[0]) - 1])

    def getSquarePosition(self):
        """
        Get the current square position of the player.
        str: The grid square position
        """
        import Math
        player = getPlayer()
        boundingBox = player.arena.arenaType.boundingBox
        position = BigWorld.entities[player.playerVehicleID].position
        positionRect = Math.Vector2(position[0], position[2])
        bottomLeft, upperRight = boundingBox
        spaceSize = upperRight - bottomLeft
        relPos = positionRect - bottomLeft
        relPos[0] = self.clamp(relPos[0], spaceSize[0])
        relPos[1] = self.clamp(relPos[1], spaceSize[1])
        return self.pos2name((math.ceil(relPos[0] / spaceSize[0] * 10), math.ceil(relPos[1] / spaceSize[1] * 10)))


square_position = SquarePosition()
