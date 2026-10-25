# -*- coding: utf-8 -*-
from driftkings.common.utils.color_rating_data import color_tables
from driftkings.core.vehicle_markers.colors import normalize, palette
from driftkings.core.vehicle_markers.config import prepare
from driftkings.settings.controls_schema import field
from driftkings.settings.definitions.base import SectionDefinition
from driftkings.settings.vehicle_markers_store import FILES, VehicleMarkersStore


class VehicleMarkersSettings(SectionDefinition):
    NAME = 'vehicle_markers'
    STORAGE_CLASS = VehicleMarkersStore
    STORAGE_FILES = FILES

    def normalize_loaded(self, values):
        prepare(values)
        return values

    def normalize_changes(self, values, changes):
        return self.normalize_loaded(values)

    def getControlColumns(self):
        items = [field(['debug'], self.i18n['UI_debug'], tooltip=self.i18n['UI_debug_tip'])]
        items.append(field(['colorRating'], self.i18n['UI_setting_colorRating_text'], 'Dropdown',
                           choices=range(len(color_tables)), choice_labels=[table['ScaleColor'] for table in color_tables],
                           tooltip=self.i18n['UI_setting_colorRating_tooltip']))
        for key in ('markers', 'customFields', 'colors', 'healthBar', 'damageText', 'icons'):
            items.append(field([key], self.i18n['UI_' + key], 'TextArea', jsonValue=True,
                               maxLength=65536, tooltip=self.i18n['UI_' + key + '_tip']))
        return (items, [])

    def getPanelPreview(self):
        labels = dict((key[11:], value) for key, value in self.i18n.items() if key.startswith('UI_preview_'))
        labels['colorRating'] = self.i18n['UI_setting_colorRating_text']
        palettes = []
        for index, table in enumerate(color_tables):
            shared = palette(index)
            palettes.append({'name': table['ScaleColor'], 'colors': normalize({}, shared['colors']),
                             'damageColors': shared['damageColors']})
        return {'kind': 'vehicleMarkers', 'labels': labels,
                'palettes': palettes,
                'tank': 'coui://gui/maps/shop/vehicles/600x450/A12_T32.png'}
