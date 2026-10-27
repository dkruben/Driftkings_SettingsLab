# -*- coding: utf-8 -*-
"""Native Flash battle message transport."""
from functools import partial

from BigWorld import callback


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
    from gui.Scaleform.framework import WindowLayer
    from gui.shared.personality import ServicesLocator
    battle_page = ServicesLocator.appLoader.getDefBattleApp().containerManager.getContainer(WindowLayer.VIEW).getView()
    if battle_page is not None:
        getattr(battle_page.components['battle%sMessages' % panel], 'as_show%sMessageS' % colour, None)(None, text)
    else:
        callback(0.5, partial(sendPanelMessage, text, colour, panel))


