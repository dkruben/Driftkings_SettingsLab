# -*- coding: utf-8 -*-
"""Profile selection in the existing owned settings window."""
class ProfileSettings(object):
    ID = 'Driftkings'

    def __init__(self, loader, language='en'):
        from Driftkings.i18n import TranslationCatalog
        self.i18n = TranslationCatalog(loader.root).section(self.ID, language)
        self.loader = loader
        self.data = {}
        self.readData()

    def readData(self, *args):
        self.names = self.loader.profiles()
        self.data = {'profile': self.loader.selected(), 'newProfile': ''}

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'column1': [
                {'type': 'Dropdown', 'varName': 'profile', 'text': self.i18n['UI_profile_select'], 'options': [{'label': name} for name in self.names], 'optionValues': self.names},
                {'type': 'TextInput', 'varName': 'newProfile', 'text': self.i18n['UI_profile_copy']}
            ],
            'column2': [
                {'type': 'Label', 'text': self.i18n['UI_profile_active'].format(self.loader.active)},
                {'type': 'Label', 'text': self.i18n['UI_profile_restart']}
            ]
        }

    def onApplySettings(self, values):
        name = values.get('newProfile', '').strip()
        if name:
            self.loader.clone(name)
        else:
            name = values.get('profile', self.data['profile'])
        self.loader.select(name)
        self.readData()

    def onPanelOpened(self):
        self.readData()

    def onPanelClosed(self):
        pass

    def getData(self):
        return self.data
