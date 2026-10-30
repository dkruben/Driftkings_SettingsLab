# -*- coding: utf-8 -*-
"""Native Flash battle message transport."""
from functools import partial

import BigWorld

from driftkings.core.callbacks import callback


def sendPanelMessage(text='', colour='Green', panel='Player'):
    """
    This function sends a message to the specified panel in the game interface.
    :param text: The text of the message.
    :param colour: The color of the message. Default is 'Green'.
    :param panel: The panel to display the message in. Default is 'Player'.
    :return: None
    The panel can be one of the following:
        - 'Player': The player's message panel.
        - 'Vehicle': The vehicle's message panel.
        - 'VehicleError': The vehicle error message panel.
    The color can be one of the following:
        - 'Red': Red color.
        - 'Purple': Purple color.
        - 'Green': Green color.
        - 'Gold': Gold color.
        - 'Yellow': Yellow color.
        - 'Self': Self color.
    """
    arena = getattr(BigWorld.player(), 'arena', None)
    if arena is not None:
        _sendPanelMessage(text, colour, panel, arena)


def _sendPanelMessage(text, colour, panel, arena):
    # A delayed message belongs to its original battle, never the next one.
    if getattr(BigWorld.player(), 'arena', None) is not arena:
        return
    from gui.Scaleform.framework import WindowLayer
    from gui.shared.personality import ServicesLocator
    app = ServicesLocator.appLoader.getDefBattleApp()
    battle_page = app.containerManager.getContainer(WindowLayer.VIEW).getView() if app is not None else None
    if battle_page is not None:
        getattr(battle_page.components['battle%sMessages' % panel], 'as_show%sMessageS' % colour, None)(None, text)
    else:
        callback(0.5, partial(_sendPanelMessage, text, colour, panel, arena))


