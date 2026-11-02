# -*- coding: utf-8 -*-
"""Profile selection in the existing owned settings window."""
class ProfileSettings(object):
    NAME = 'driftkings'

    def __init__(self, loader, language='en'):
        from driftkings.i18n import TranslationCatalog
        self.i18n = TranslationCatalog(loader.root).section(self.NAME, language)
        self.loader = loader
        self.data = {}
        self.readData()

    def readData(self, *args):
        self.names = self.loader.profiles()
        self.data.clear()
        self.data.update(profile=self.loader.selected(), newProfile='')

    def getControlColumns(self):
        return (
            [
                {'type': 'Dropdown', 'varName': 'profile', 'text': self.i18n['UI_profile_select'],
                 'options': [{'label': name} for name in self.names], 'optionValues': self.names},
                {'type': 'TextInput', 'varName': 'newProfile', 'text': self.i18n['UI_profile_copy']}
            ],
            [
                {'type': 'Label', 'text': self.i18n['UI_profile_active'].format(self.loader.active)},
                {'type': 'Label', 'text': self.i18n['UI_profile_restart']}
            ]
        )

    def persist_values(self, values):
        name = values.get('newProfile', '').strip()
        if name:
            self.loader.clone(name)
        else:
            name = values.get('profile', self.data['profile'])
        self.loader.select(name)
        self.readData()
        return self.data

    def onPanelOpened(self):
        self.readData()

    def onPanelClosed(self):
        pass

    def getData(self):
        return self.data
