# -*- coding: utf-8 -*-
"""Mod registry: declarations, live values, persistence and change notifications."""
import copy
import re

from Driftkings.settings.panel import logger
from Driftkings.settings.panel.controls import (Control, DefinitionError, DEFAULT_COLOR_PRESETS, check_text, is_number,
                                                is_text, options_list, resolve_text)
from Driftkings.settings.panel.storage import ConfigReadError

MOD_ID_PATTERN = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$')
DEFAULT_ICON = 'puzzle'
STATUS_ACTIVE, STATUS_CONFIG_ERROR, STATUS_ERROR = 'active', 'configError', 'error'


class DuplicateModError(DefinitionError):
    pass


class UnknownModError(KeyError):
    pass


class ModHandle(object):
    """Object returned to a mod author; declares controls and exposes live values."""

    def __init__(self, registry, definition, values=None):
        self._registry = registry
        self._mod = definition
        self._action_values = values

    @property
    def id(self):
        return self._mod.id

    @property
    def values(self):
        return copy.deepcopy(self._mod.values if self._action_values is None else self._action_values)

    def get(self, setting_id, default=None):
        return self.values.get(setting_id, default)

    def __getitem__(self, setting_id):
        return self.values[setting_id]

    def on_change(self, callback):
        """callback(changes) after Apply/Save/Discard; changes maps setting id to its new value."""
        if not callable(callback):
            raise DefinitionError('on_change requires a callable')
        if callback not in self._mod.listeners:
            self._mod.listeners.append(callback)
        return callback

    def remove_listener(self, callback):
        if callback in self._mod.listeners:
            self._mod.listeners.remove(callback)

    # Value controls -------------------------------------------------------
    def add_switch(self, id, label=None, default=False, **options):
        return self._add('switch', id, label, default, options)

    def add_checkbox(self, id, label=None, default=False, **options):
        return self._add('checkbox', id, label, default, options)

    def add_dropdown(self, id, label=None, values=None, default=None, **options):
        choices = options_list(values if values is not None else options.pop('options', None) or [])
        if default is None and choices:
            default = choices[0][0]
        return self._add('dropdown', id, label, default, options, options=choices)

    def add_slider(self, id, label=None, min_value=0, max_value=100, default=None, step=1, unit=None, **options):
        return self._add('slider', id, label, min_value if default is None else default, options,
                         minimum=min_value, maximum=max_value, step=step, unit=unit)

    def add_number(self, id, label=None, min_value=-1000000, max_value=1000000, default=0, step=1, unit=None, **options):
        return self._add('number', id, label, default, options, minimum=min_value, maximum=max_value, step=step, unit=unit)

    def add_text(self, id, label=None, default=u'', max_length=256, placeholder=None, **options):
        return self._add('text', id, label, default, options, max_length=max_length,
                         placeholder=check_text(placeholder, 'placeholder') if placeholder is not None else None)

    def add_password(self, id, label=None, max_length=512, placeholder=None, **options):
        """Secret value: stored separately, masked in the view and never logged."""
        return self._add('password', id, label, u'', options, max_length=max_length,
                         placeholder=check_text(placeholder, 'placeholder') if placeholder is not None else None)

    def add_color(self, id, label=None, default='#D98219', presets=None, **options):
        presets = DEFAULT_COLOR_PRESETS if presets is None else presets
        return self._add('color', id, label, default, options, presets=[(value, check_text(name, 'preset'))
                                                                     for value, name in presets])

    def add_hotkey(self, id, label=None, default=None, **options):
        return self._add('hotkey', id, label, default or [], options)

    def add_multiselect(self, id, label=None, values=None, default=None, **options):
        return self._add('multiselect', id, label, default or [], options, options=options_list(values or []))

    def add_textarea(self, id, label=None, default=u'', **options):
        return self._add('textarea', id, label, default, options)

    def add_file(self, id, label=None, default=u'', **options):
        from Driftkings.settings.panel.locales import translations
        options.setdefault('description', translations('pathHelp'))
        return self._add('file', id, label, default, options)

    def add_directory(self, id, label=None, default=u'', **options):
        from Driftkings.settings.panel.locales import translations
        options.setdefault('description', translations('pathHelp'))
        return self._add('directory', id, label, default, options)

    def add_sound_preview(self, id, label=None, event=None, **options):
        from Driftkings.settings.panel.sound import sound_manager
        from Driftkings.settings.panel.locales import translations
        self.add_button(id, label or translations('sound.play'), callback=lambda handle: sound_manager.play(event, self.id), **options)
        return self.add_button(id + '_stop', translations('sound.stop'), callback=lambda handle: sound_manager.stop(event), **options)

    # Layout and actions ---------------------------------------------------
    def add_section(self, label, id=None, **options):
        return self._add('section', id or self._mod.auto_id('section'), label, None, options)

    def add_label(self, text, id=None, **options):
        return self._add('label', id or self._mod.auto_id('label'), text, None, options)

    def add_separator(self, id=None, **options):
        return self._add('separator', id or self._mod.auto_id('separator'), u'', None, options)

    def add_button(self, id, label=None, callback=None, text=None, **options):
        """callback(handle) runs in Python; return text to show it as a message."""
        return self._add('button', id, label, None, options, callback=callback,
                         text=check_text(text, 'text') if text is not None else None)

    def _add(self, kind, control_id, label, default, common, **attributes):
        tooltip = common.pop('tooltip', None)
        if tooltip is not None and common.get('description') is None:
            common['description'] = tooltip
        known = ('description', 'order', 'depends_on', 'enabled', 'visible', 'keywords', 'column', 'tab')
        unknown = sorted(set(common) - set(known))
        if unknown:
            raise DefinitionError('%s: unknown option(s) %s' % (control_id, ', '.join(unknown)))
        control = Control(kind, control_id, label=label, default=default, **common)
        for name, value in attributes.items():
            setattr(control, name, value)
        if kind == 'text' or kind == 'password':
            if not is_number(control.max_length) or not 1 <= control.max_length <= 4096:
                raise DefinitionError('%s: max_length must be between 1 and 4096' % control_id)
        self._registry._add_control(self._mod, control.finalize())
        return self


class ModDefinition(object):
    def __init__(self, mod_id, name, version, author, description, icon, order, file_name):
        self.id = mod_id
        self.name = name
        self.version = version
        self.author = author
        self.description = description
        self.icon = icon
        self.order = order
        self.file_name = file_name
        self.controls = []
        self.index = {}
        self.values = {}
        self.saved = {}
        self.stored = {}
        self.secrets = {}
        self.listeners = []
        self.status = STATUS_ACTIVE
        self.error = None
        self.external_apply = None
        self.category = None
        self.dependencies = []
        self._auto = 0

    def auto_id(self, prefix):
        self._auto += 1
        return '%s_%d' % (prefix, self._auto)

    def value_controls(self):
        return [control for control in self.controls if control.has_value]

    def defaults(self):
        return dict((control.id, copy.deepcopy(control.default)) for control in self.value_controls())


def _file_name(mod_id):
    name = mod_id.split('.')[-1] if mod_id.lower().startswith('dk.') else mod_id
    return re.sub(r'[^A-Za-z0-9_-]', '_', name).lower()


class ModRegistry(object):
    def __init__(self, store=None):
        self.store = store
        self.mods = {}
        self.language = 'en'
        self.listeners = []
        self.revision = 0

    # Registration ----------------------------------------------------------
    def register_mod(self, mod_id=None, name=None, version=u'', author=u'', description=u'', icon=None,
                     order=None, config_file=None, id=None):
        mod_id = mod_id if mod_id is not None else id
        if not is_text(mod_id) or not MOD_ID_PATTERN.match(mod_id):
            raise DefinitionError('Invalid mod id %r' % (mod_id,))
        mod_id = str(mod_id)
        if mod_id in self.mods:
            raise DuplicateModError('Mod already registered: ' + mod_id)
        file_name = config_file or _file_name(mod_id)
        if any(mod.file_name == file_name for mod in self.mods.values()):
            raise DuplicateModError('Configuration file already used by another mod: ' + file_name)
        for field, value in (('version', version), ('author', author)):
            if not is_text(value):
                raise DefinitionError('%s must be text' % field)
        definition = ModDefinition(mod_id, check_text(name if name is not None else mod_id, 'name'), version, author, check_text(description, 'description'), icon or DEFAULT_ICON, order if is_number(order) else 1000, file_name)
        self._load(definition)
        self.mods[mod_id] = definition
        logger.info('Registered mod: %s', mod_id)
        self._notify_structure()
        return ModHandle(self, definition)

    def mod(self, mod_id):
        try:
            return ModHandle(self, self.mods[mod_id])
        except KeyError:
            raise UnknownModError(mod_id)

    def unregister_mod(self, mod_id):
        if self.mods.pop(mod_id, None) is not None:
            self._notify_structure()

    # Module-level shortcuts: settings.add_switch(mod_id=..., setting_id=...).
    def _shortcut(kind):
        def method(self, mod_id, setting_id=None, *args, **kwargs):
            if setting_id is not None:
                kwargs['id'] = setting_id
            return getattr(self.mod(mod_id), 'add_' + kind)(*args, **kwargs)
        method.__name__ = 'add_' + kind
        return method

    add_switch = _shortcut('switch')
    add_checkbox = _shortcut('checkbox')
    add_dropdown = _shortcut('dropdown')
    add_slider = _shortcut('slider')
    add_number = _shortcut('number')
    add_text = _shortcut('text')
    add_password = _shortcut('password')
    add_color = _shortcut('color')
    add_button = _shortcut('button')
    add_sound_preview = _shortcut('sound_preview')
    add_hotkey = _shortcut('hotkey')
    add_multiselect = _shortcut('multiselect')
    add_textarea = _shortcut('textarea')
    add_file = _shortcut('file')
    add_directory = _shortcut('directory')
    del _shortcut

    def get(self, mod_id, setting_id, default=None):
        mod = self.mods.get(mod_id)
        return copy.deepcopy(mod.values.get(setting_id, default)) if mod is not None else default

    def ordered(self):
        return sorted(self.mods.values(), key=lambda mod: (mod.order, resolve_text(mod.name, self.language).lower()))

    def dependency_status(self, mod):
        result = []
        for requirement in mod.dependencies:
            key = requirement.get('id') if isinstance(requirement, dict) else requirement
            minimum = requirement.get('min_version') if isinstance(requirement, dict) else None
            target = self.mods.get(key)
            available = target is not None
            if available and minimum:
                def version(value):
                    parts = value.split('.')
                    return tuple(int(part) for part in parts) if all(part.isdigit() for part in parts) else ()
                available = bool(version(target.version)) and version(target.version) >= version(minimum)
            result.append({'id': key, 'installed': available, 'minimum': minimum})
        return result

    def subscribe(self, callback):
        """Structure listeners (the open window) are told when mods or controls are added."""
        if callback not in self.listeners:
            self.listeners.append(callback)

    def unsubscribe(self, callback):
        if callback in self.listeners:
            self.listeners.remove(callback)

    def _notify_structure(self):
        self.revision += 1
        for callback in tuple(self.listeners):
            try:
                callback()
            except Exception:
                logger.exception('Settings window update failed')

    # Values ------------------------------------------------------------------
    def _load(self, mod):
        if self.store is None:
            return
        try:
            mod.stored = self.store.read(mod.file_name)
        except ConfigReadError as error:
            mod.stored = {}
            mod.status, mod.error = STATUS_CONFIG_ERROR, str(error)
            logger.error('Invalid configuration, defaults are used and the file is preserved: %s', error)
        try:
            mod.secrets = self.store.read(mod.file_name, secret=True)
        except ConfigReadError:
            mod.secrets = {}
            # The file name is safe to log; the content is never logged.
            logger.error('Invalid secrets file for %s; secrets were not loaded', mod.id)

    def _add_control(self, mod, control):
        if control.id in mod.index:
            raise DefinitionError('%s: duplicate setting id %s' % (mod.id, control.id))
        unknown = [key for key in control.depends_on if key not in mod.index or not mod.index[key].has_value]
        if unknown:
            raise DefinitionError('%s: depends_on refers to undeclared setting(s) %s' % (control.id, ', '.join(unknown)))
        if control.order is None:
            control.order = len(mod.controls)
        mod.controls.append(control)
        mod.controls.sort(key=lambda item: item.order)
        mod.index[control.id] = control
        if control.has_value:
            source = mod.secrets if control.secret else mod.stored
            value = control.default
            if control.id in source:
                try:
                    value = control.validate(source[control.id])
                except ValueError as error:
                    logger.warning('%s.%s: stored value rejected (%s); default used', mod.id, control.id,
                                   'hidden' if control.secret else error)
            mod.values[control.id] = copy.deepcopy(value)
            mod.saved[control.id] = copy.deepcopy(value)
        self._notify_structure()

    def apply_values(self, mod_id, values):
        """Validate and publish values to the mod; returns the changed subset."""
        mod = self.mods[mod_id]
        normalized = {}
        for key, value in values.items():
            control = mod.index.get(key)
            if control is None or not control.has_value:
                raise ValueError('Unknown setting: %s.%s' % (mod_id, key))
            normalized[key] = control.validate(value)
        changes = dict((key, value) for key, value in normalized.items() if mod.values.get(key) != value)
        if not changes:
            return {}
        if mod.external_apply is not None:
            mod.external_apply(copy.deepcopy(changes))
        mod.values.update(copy.deepcopy(changes))
        if mod.external_apply is not None:
            mod.saved = copy.deepcopy(mod.values)
        self._dispatch(mod, changes)
        return changes

    def _dispatch(self, mod, changes):
        for callback in tuple(mod.listeners):
            try:
                callback(copy.deepcopy(changes))
            except Exception as error:
                mod.status, mod.error = STATUS_ERROR, 'on_change failed'
                logger.error('%s: on_change callback failed (%s)', mod.id, type(error).__name__)

    def save(self, mod_id):
        """Persist live values; unknown keys already in the file are retained."""
        mod = self.mods[mod_id]
        if mod.external_apply is not None:
            mod.saved = copy.deepcopy(mod.values)
            return
        public = dict(mod.stored)
        secrets = dict(mod.secrets)
        for control in mod.value_controls():
            (secrets if control.secret else public)[control.id] = copy.deepcopy(mod.values[control.id])
        if self.store is not None:
            self.store.write(mod.file_name, public)
            if any(control.secret for control in mod.value_controls()):
                self.store.write(mod.file_name, secrets, secret=True)
        mod.stored, mod.secrets = public, secrets
        mod.saved = copy.deepcopy(mod.values)
        if mod.status == STATUS_CONFIG_ERROR:
            mod.status, mod.error = STATUS_ACTIVE, None
        logger.info('Settings saved: %s', mod_id)

    def run_button(self, mod_id, setting_id, values=None):
        mod = self.mods[mod_id]
        control = mod.index.get(setting_id)
        if control is None or control.type != 'button':
            raise ValueError('Unknown action')
        if control.callback is None:
            return None
        result = control.callback(ModHandle(self, mod, values))
        return result if is_text(result) else None
