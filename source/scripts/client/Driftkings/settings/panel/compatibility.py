# -*- coding: utf-8 -*-
"""Adapt component control declarations to the owned Gameface panel."""
import copy
import hashlib
import re

from Driftkings.settings.dependencies import option_dependencies
from Driftkings.settings.panel import logger
from Driftkings.settings.panel.controls import Control, text_type
from Driftkings.settings.panel.registry import ModDefinition
from Driftkings.settings.settings_data import BATTLE_EDITABLE, application_timing, LIVE, RESTART


def plain(value):
    if isinstance(value, bytes):
        value = value.decode('utf-8', 'replace')
    if isinstance(value, dict):
        value = value.get('body', value.get('header', ''))
    value = text_type(value or '')
    value = re.sub(r'<br\s*/?>|\{/(?:HEADER|BODY|NOTE|ATTENTION)\}', '\n', value)
    return re.sub(r'<[^>]*>|\{/?(?:HEADER|BODY|NOTE|ATTENTION)\}', '', value).strip()


def template_category(config):
    """Classify by template origin, not by a hardcoded list of components."""
    explicit = getattr(config, 'SETTINGS_CATEGORY', None)
    if explicit:
        return explicit
    module = type(config).__module__.split('.')
    if 'templates' in module:
        scope = module[module.index('templates') + 1:]
        return {'battle': 'battle', 'lobby': 'hangar', 'components': 'general'}.get(scope[0] if scope else '', 'general')
    return 'system' if type(config).__module__ == 'Driftkings.settings.profiles' else 'general'


class TemplateAdapter(object):
    def __init__(self, api, registry):
        self.api, self.registry = api, registry
        self.mapping = {}
        self.initial = {}
        self.timings = {}
        self.configs = []

    def populate(self):
        for key in list(self.mapping):
            self.api.registry.mods.pop(key, None)
        self.mapping.clear()
        self.timings.clear()
        self.configs = []
        for config, fields, defaults, block in self.registry.entries.values():
            if self.api.in_battle and config.ID not in BATTLE_EDITABLE:
                continue
            if config not in self.configs:
                self.configs.append(config)
                try:
                    if not self.api.in_battle:
                        config.onPanelOpened()
                except Exception:
                    logger.exception('Could not prepare settings: %s', config.ID)
        for key in sorted(self.registry.entries):
            if self.api.in_battle and self.registry.entries[key][0].ID not in BATTLE_EDITABLE:
                continue
            try:
                self._register(key)
            except Exception:
                # One broken template cannot hide the remaining mods.
                logger.exception('Could not adapt settings: %s', key)
        self.registry.isOpen = True

    def _register(self, key):
        config = self.registry.entries[key][0]
        if hasattr(config, 'loadLang'):
            preference = self.api.get('dk.settings', 'language', 'auto')
            config.lang = self.api.client_language if preference == 'auto' else preference
            config.loadLang()
        data = self.registry.describe(key)
        mod_id = 'legacy.' + key
        mod = ModDefinition(mod_id, plain(data['title']), '', 'DriftKingsMods', '', 'puzzle', 1000, None)
        mod.category = template_category(config)
        mod.restart_key = key
        config = self.registry.entries[key][0]
        mod.name = plain(config.i18n.get('UI_description', data['title']))
        if ':' in key:
            mod.name += ' / ' + key.split(':', 1)[1]
        names, originals, timings, alpha_paths = {}, {}, {}, {}
        kinds = {
            'CheckBox': 'checkbox',
            'Dropdown': 'dropdown',
            'RadioButtonGroup': 'dropdown',
            'Slider': 'slider',
            'NumericStepper': 'slider',
            'TextInput': 'text',
            'ColorChoice': 'color',
            'HotKey': 'hotkey',
            'Label': 'label',
            'Empty': 'separator'
        }
        for index, item in enumerate(data['controls']):
            kind = kinds.get(item['type'])
            if kind is None:
                raise ValueError('Unsupported template control: ' + item['type'])
            source = item.get('varName')
            control_id = 'field_' + hashlib.sha1(plain(source).encode('utf-8')).hexdigest()[:16] if source is not None else 'layout_' + str(index)
            if source is not None and source in names:
                continue
            control = Control(kind, control_id, plain(item.get('text', source)), description=plain(item.get('tooltip')), column=item.get('column', -1), tab=plain(item.get('tab')) or None,
                              metadata={'sourceType': item['type']})
            hints = item.get('metadata', {})
            if hints:
                from Driftkings.settings.panel.controls import check_metadata
                metadata = dict(hints)
                alpha_path = metadata.pop('alphaPath', None)
                if alpha_path is not None:
                    alpha_paths[control_id] = alpha_path
                control.metadata.update(check_metadata(metadata))
            if source is not None:
                timing = application_timing(config.ID, item.get('path', [source]))
                timings[source] = timing
                control.metadata['applyTiming'] = timing
                hint = self.api.strings.get('applyTiming.' + timing, '')
                control.description = '\n'.join(value for value in (control.description, hint) if value)
                if self.api.in_battle and timing != LIVE:
                    control.enabled = False
                control.default = copy.deepcopy(data['defaults'][source])
                originals[control_id] = source
                names[source] = control_id
                if source == 'enabled':
                    mod.enabled_key = control_id
            if kind == 'dropdown':
                control.options = [(i, plain(o.get('label', i))) for i, o in enumerate(item['options'])]
                if item.get('previewImage'):
                    from Driftkings.settings.panel.media import resource_image
                    control.preview = {'kind': 'image', 'images': [resource_image(o.get('image', '')) for o in item['options']]}
            elif kind in ('slider', 'number'):
                current = data['values'][source]
                extent = max(100, abs(current) * 2, abs(control.default) * 2)
                control.minimum = min(item.get('minimum', -extent if current < 0 or control.default < 0 else 0), current, control.default)
                control.maximum = max(item.get('maximum', extent), current, control.default)
                if control.minimum == control.maximum:
                    control.maximum += 1
                control.step = item.get('snapInterval', 0.01 if isinstance(current, float) else 1)
                numeric_format = item.get('format', '')
                if numeric_format.startswith('{{value}}'):
                    control.unit = numeric_format[len('{{value}}'):].strip()
            elif kind == 'color':
                from Driftkings.settings.panel.controls import DEFAULT_COLOR_PRESETS
                control.presets = DEFAULT_COLOR_PRESETS
            elif kind == 'text' and source is not None:
                value = data['values'][source]
                if item.get('previewImage') or (isinstance(value, (str, text_type)) and value.lower().endswith(('.png', '.jpg', '.jpeg')) and '{{' not in value):
                    control.preview = {'kind': 'image'}
            control.finalize()
            mod.controls.append(control)
            mod.index[control_id] = control
            if control.has_value:
                mod.values[control_id] = control.validate(data['values'][source])
            if item.get('button') is not None:
                button = Control('button', 'action_' + str(index), plain(item.get('button')))
                button.column = control.column
                button.callback = self._button(key, source, mod, control_id)
                mod.controls.append(button)
                mod.index[button.id] = button
        for color_key, alpha_path in alpha_paths.items():
            # Resolve only explicitly declared fields, never infer/migrate JSON.
            alpha_key = names.get(alpha_path)
            if alpha_key is None or mod.index[alpha_key].type not in ('slider', 'number'):
                raise ValueError('alphaPath must name a declared numeric field')
            mod.index[color_key].metadata['alphaKey'] = alpha_key
        if key == 'SixthSense' and 'sixthSenseSound' in names:
            from Driftkings.settings.panel.locales import translations
            mod.category = translations('sound.name')
            mod.icon = 'speaker'
            play = Control('button', 'soundPreview', translations('sound.play'), column=0)
            events = next(item['optionValues'] for item in data['controls'] if item.get('varName') == 'sixthSenseSound')
            play.callback = self._sound_preview(names['sixthSenseSound'], events)
            stop = Control('button', 'soundStop', translations('sound.stop'), column=1)
            from Driftkings.settings.panel.sound import sound_manager
            sound_manager.register(mod_id, 'driftkings_sixthsense.bnk', events)
            stop.callback = lambda handle: sound_manager.stop()
            mod.index[names['sixthSenseSound']].preview = {'kind': 'audio', 'play': play.id, 'stop': stop.id}
            for button in (play, stop):
                button.visible = False
                mod.controls.append(button)
                mod.index[button.id] = button
        for child, parents in option_dependencies(config.ID, data['controls']).items():
            for parent, accepted in parents.items():
                # The selector is also used for auditioning before enabling
                # the sound in battle. This does not change userSound itself.
                if key == 'SixthSense' and child == 'sixthSenseSound' and parent == 'userSound':
                    continue
                mod.index[names[child]].depends_on[names[parent]] = accepted
        mod.saved = copy.deepcopy(mod.values)
        self.initial.setdefault(key, copy.deepcopy(data['values']))
        mod.external_apply = lambda values: self.apply(key, mod, originals, values)
        self.mapping[mod_id] = (key, originals)
        self.timings[key] = timings
        self.api.registry.mods[mod_id] = mod

    def _button(self, key, source, mod, control_id):
        return lambda handle: self.registry.button(key, source, handle.get(control_id))

    def _sound_preview(self, field, events):
        def play(handle):
            from Driftkings.settings.panel.sound import sound_manager
            event = events[handle.get(field)]
            sound_manager.stop()
            sound_manager.play(event, handle.id)
        return play

    def apply(self, key, mod, originals, changes):
        values = copy.deepcopy(mod.values)
        values.update(changes)
        current = self.registry.describe(key)['values']
        for field, source in originals.items():
            value = values[field]
            if mod.index[field].type == 'color':
                previous = current[source]
                value = ('0x' + value[1:]) if previous.startswith('0x') else value if previous.startswith('#') else value[1:]
            current[source] = value
        self.registry.apply(key, current)
        # Callbacks may normalize values (e.g. profile cloning clears newProfile).
        current = self.registry.describe(key)['values']
        baseline = self.initial[key]
        if any(self.timings[key].get(field, RESTART) == RESTART and value != baseline.get(field)
               for field, value in current.items()):
            self.api.restart_required.add(key)
        else:
            self.api.restart_required.discard(key)
        # The settings service persists through each component owner.

    def relabel(self):
        # Refresh language only: retain edits, saved values and callbacks.
        for mod_id, (key, originals) in list(self.mapping.items()):
            old = self.api.registry.mods[mod_id]
            try:
                self._register(key)
                fresh = self.api.registry.mods[mod_id]
                old.name = fresh.name
                old.category = fresh.category
                for control in old.controls:
                    updated = fresh.index.get(control.id)
                    if updated is not None:
                        control.label, control.description = updated.label, updated.description
                        control.tab = updated.tab
                        control.metadata = copy.deepcopy(updated.metadata)
                        if control.options is not None:
                            control.options = updated.options
            except Exception:
                logger.exception('Could not translate settings: %s', key)
            finally:
                self.api.registry.mods[mod_id] = old
        self.api.registry._notify_structure()

    def dispose(self):
        self.registry.isOpen = False
        for config in self.configs:
            try:
                config.onPanelClosed()
            except Exception:
                logger.exception('Could not release settings: %s', config.ID)
        self.configs = []
