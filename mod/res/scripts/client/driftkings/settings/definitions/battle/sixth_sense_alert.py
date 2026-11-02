# -*- coding: utf-8 -*-
import ResMgr

from driftkings._constants import SIXTH_SENSE_ALERT
from driftkings.settings.controls_schema import control, images, label, metadata, options, slider
from driftkings.settings.definitions.base import SectionDefinition


class SixthSenseAlertSettings(SectionDefinition):
    NAME = SIXTH_SENSE_ALERT.NAME

    TRANSLATED_TITLE = True

    def getControlColumns(self):
        infoSLabel = label('infoSpottedMessage')
        infoTimerLabel = label('timerSettings')
        from driftkings.settings.panel.media import SIXTH_SENSE_EVENTS
        sounds = list(SIXTH_SENSE_EVENTS)
        if self.data[SIXTH_SENSE_ALERT.SIXTH_SENSE_SOUND] not in sounds:
            sounds.append(self.data[SIXTH_SENSE_ALERT.SIXTH_SENSE_SOUND])
        sound = options(SIXTH_SENSE_ALERT.SIXTH_SENSE_SOUND,
                        [self.i18n.get('UI_sound_' + event, event) for event in sounds])
        sound = metadata(sound, optionValues=sounds)
        icons = self.sixthSenseIconsNamesList()
        icon = images(SIXTH_SENSE_ALERT.DEFAULT_ICON_NAME, icons)
        icon = metadata(icon, optionValues=[int(name[:-4]) for name in icons])

        return (
            [
                control(SIXTH_SENSE_ALERT.DEFAULT_ICON),
                icon,
                metadata(control(SIXTH_SENSE_ALERT.USER_ICON, 'TextInput'), previewImage=True),
                slider(SIXTH_SENSE_ALERT.ICON_SIZE, 50, 180, 10, '{{value}} px'),
                infoTimerLabel,
                control(SIXTH_SENSE_ALERT.SHOW_TIMER),
                control(SIXTH_SENSE_ALERT.SHOW_TIMER_GRAPHICS),
                control(SIXTH_SENSE_ALERT.SHOW_TIMER_GRAPHICS_COLOR, 'ColorChoice'),
                slider(SIXTH_SENSE_ALERT.SHOW_TIMER_GRAPHICS_RADIUS, 20, 100, 5, '{{value}} px'),
            ],
            [
                control(SIXTH_SENSE_ALERT.USER_SOUND),
                sound,
                control(SIXTH_SENSE_ALERT.PLAY_TICK_SOUND),
                slider(SIXTH_SENSE_ALERT.LAMP_SHOW_TIME, 2.0, 15.0, 1.0, '{{value}} sec'),
                infoSLabel,
                control(SIXTH_SENSE_ALERT.SPOTTED_MESSAGE),
                control(SIXTH_SENSE_ALERT.HELP_MESSAGE),
                control(SIXTH_SENSE_ALERT.SPOTTED_TEXT, 'TextInput', 300),
                slider(SIXTH_SENSE_ALERT.DELAY, 1.0, 10.0, 1.0, '{{value}} sec')
            ]
        )


    @staticmethod
    def sixthSenseIconsNamesList():
        directory = 'gui/maps/icons/sixthsense/'
        folder = ResMgr.openSection(directory)
        # The battle Flash uses the stored numeric filename, not the list index.
        names = set('%d.png' % index for index in range(10))
        if folder is not None:
            names.update(name for name in folder.keys() if name.endswith('.png') and name[:-4].isdigit())
        return sorted(names, key=lambda name: int(name[:-4]))
