# -*- coding: utf-8 -*-
"""Python defaults, selected profile and per-feature JSON persistence."""
import copy
import json
from driftkings.logger import get_logger
import math
import os
import re
import shutil
import tempfile

from driftkings.settings.default_values import SELECTOR
from driftkings.settings.sections import previous_name, previous_sections, section_aliases
from driftkings.settings.settings_data import SettingsData, user_settings, part_name
from driftkings.settings.store import SettingsStore, merge, recover_file, read_object

try:
    string_types = (basestring,)
    number_types = (int, long, float)
except NameError:
    string_types = (str,)
    number_types = (int, float)

LOG = get_logger('Driftkings.Settings')
# Features removed from the mod; their files are never read again.
REMOVED_SECTIONS = ('safe_shot',)


def validate_types(defaults, values, path=''):
    """Keep extra user keys; reject malformed known options without rewriting them."""
    if not isinstance(values, dict):
        raise ValueError('Expected an object: ' + path)
    for key, default in defaults.items():
        if key not in values or default is None:
            continue
        value = values[key]
        name = path + '.' + str(key) if path else str(key)
        if isinstance(default, dict):
            validate_types(default, value, name)
        elif type(default) is bool:
            if type(value) is not bool:
                raise ValueError('Expected a boolean: ' + name)
        elif isinstance(default, number_types):
            if isinstance(value, bool) or not isinstance(value, number_types):
                raise ValueError('Expected a number: ' + name)
            if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                raise ValueError('Expected a finite number: ' + name)
        elif isinstance(default, string_types):
            if not isinstance(value, string_types):
                raise ValueError('Expected text: ' + name)
        elif isinstance(default, (tuple, list)) and not isinstance(value, (tuple, list)):
            raise ValueError('Expected a list: ' + name)


# The earlier flat clock options, first in hangar_preferences and briefly in main.
OLD_CLOCK_OPTIONS = ('clock', 'clockBackground', 'clockX', 'clockY', 'clockScale', 'customClockText')
OLD_CLOCK_TEXT = ("<font face='$FieldFont'><textformat leading='-38'><font size='36'>%H:%M</font><br></textformat>"
                  "<textformat rightMargin='85' leading='-2'>%A<br><font size='15'>%d %b %Y</font></textformat></font>")
# Comments allowed in hand-written clock JSON; quoted strings are kept as written.
JSON_COMMENTS = re.compile(r'("(?:\\.|[^"\\])*")|//[^\r\n]*|/\*[\s\S]*?\*/')


def clock_formats(text, x, y):
    """Clock fields from an earlier text: a JSON list of fields, or one text field at the old position."""
    parsed = text if isinstance(text, (dict, list)) else None
    if parsed is None and isinstance(text, string_types):
        clean = JSON_COMMENTS.sub(lambda match: match.group(1) or '', text)
        if clean.strip()[:1] in ('{', '['):
            try:
                parsed = json.loads(clean)
            except ValueError:
                return None
    if parsed is not None:
        formats = parsed.get('formats') if isinstance(parsed, dict) else parsed
        return formats if isinstance(formats, list) else None
    if not isinstance(text, string_types) or not text.strip():
        return None
    return [{'x': x, 'y': y, 'screenHAlign': 'right', 'width': 240, 'height': 100,
             'textFormat': {'align': 'right'}, 'format': text}]


def migrate_main_options(values, hangar_path):
    """Convert earlier clock options into main's clock object; hangar_preferences.json is never rewritten.

    An untouched shipped clock keeps the current default fields; scale and background are retired.
    """
    if isinstance(values.get('clock'), dict):
        return values
    old = dict((key, values.pop(key)) for key in OLD_CLOCK_OPTIONS if key in values)
    if not old and os.path.isfile(hangar_path):
        hangar = read_object(hangar_path)
        old = dict((key, hangar[key]) for key in OLD_CLOCK_OPTIONS if key in hangar)
    clock = {}
    if type(old.get('clock')) is bool:
        clock['enabled'] = old['clock']
    text, x, y = old.get('customClockText'), old.get('clockX', -100), old.get('clockY', 80)
    if not (text == OLD_CLOCK_TEXT and x == -100 and y == 80):
        formats = clock_formats(text, x, y)
        if formats is not None:
            clock['formats'] = formats
    if clock:
        values['clock'] = clock
    return values


def migrate_values(component, values):
    """Normalize legacy representation before validating against current defaults."""
    if component == 'third_person_zoom':
        from driftkings.core.camera_settings import migrate
        values = migrate(values)
    elif component == 'sniper_camera':
        values.pop('dynamicZoom', None)
    if component == 'hangar_marks_of_excellence':
        card = values.get('card')
        if isinstance(card, dict):
            color = card.get('backgroundColor')
            if isinstance(color, number_types) and not isinstance(color, bool) and 0 <= color <= 0xFFFFFF and int(color) == color:
                card['backgroundColor'] = '#%06X' % int(color)
    return values


class SettingsLoader(object):
    def __init__(self, root, settings=None):
        self.root = os.path.abspath(root)
        self.settings = settings or SettingsData()
        self.defaults = {}
        self._active = None

    def directory(self, name):
        if not isinstance(name, string_types) or not re.match(r'^[A-Za-z0-9_-]{1,64}\Z', name):
            raise ValueError('Profile names may contain letters, digits, _ and -')
        if name.upper() in ('CON', 'PRN', 'AUX', 'NUL') or re.match(r'^(COM|LPT)[0-9]\Z', name.upper()):
            raise ValueError('Reserved profile name: ' + name)
        target = os.path.realpath(os.path.join(self.root, name))
        if not os.path.normcase(target).startswith(os.path.normcase(os.path.realpath(self.root)) + os.sep):
            raise ValueError('Profile path is outside the configuration directory')
        return target

    def selected(self):
        path = os.path.join(self.root, 'load.json')
        recover_file(path)
        if not os.path.isfile(path):
            name = SELECTOR['loadConfig']
            self.directory(name)
            return name
        name = read_object(path).get('loadConfig')
        self.directory(name)
        return name

    @property
    def active(self):
        if self._active is None:
            self._active = self.selected()
            selector = os.path.join(self.root, 'load.json')
            if not os.path.isfile(selector):
                SettingsStore(selector).write({'loadConfig': self._active})
        return self._active

    def select(self, name):
        # Pin the running session before changing the next-start selector.
        current = self.active
        path = self.directory(name)
        if not os.path.isdir(path):
            raise ValueError('Configuration profile does not exist: ' + name)
        SettingsStore(os.path.join(self.root, 'load.json')).write({'loadConfig': name})
        return current != name

    def profiles(self):
        names = set((self.active, self.selected()))
        if os.path.isdir(self.root):
            for name in os.listdir(self.root):
                try:
                    folder = self.directory(name)
                except ValueError:
                    continue
                if not os.path.isdir(folder):
                    continue
                entries = os.listdir(folder)
                # Python 2 list comprehensions leak their variables; keep the folder name intact.
                known = [section + '.json' for key in self.settings.configs for section in (key,) + previous_sections(key)]
                if any(key in entries for key in known) or any(key in entries for section in ('team_panels', 'vehicle_carousel', 'minimap_enhancements') for key in (section,) + previous_sections(section)):
                    names.add(name)
        return sorted(names)

    def clone(self, name):
        target = self.directory(name)
        if os.path.exists(target):
            raise ValueError('Profile already exists: ' + name)
        source = self.directory(self.active)
        if not os.path.isdir(source):
            raise ValueError('The current profile has not been loaded')
        staging = tempfile.mkdtemp(prefix='.profile-', dir=self.root)
        try:
            for directory, dirs, files in os.walk(source):
                dirs[:] = [item for item in dirs if not item.startswith('.') and not os.path.islink(os.path.join(directory, item))]
                for filename in files:
                    if filename.startswith('.') or not filename.endswith('.json'):
                        continue
                    path = os.path.join(directory, filename)
                    if os.path.islink(path):
                        continue
                    destination = os.path.join(staging, os.path.relpath(path, source))
                    SettingsStore(destination).write(read_object(path))
            os.rename(staging, target)
        finally:
            if os.path.isdir(staging):
                shutil.rmtree(staging)
        return name

    def path(self, component):
        return os.path.join(self.directory(self.active), part_name(component) + '.json')

    def previous_path(self, component, directory=False):
        profile = self.directory(self.active)
        for name in previous_sections(component) + (previous_name(component),):
            path = os.path.join(profile, name + ('' if directory else '.json'))
            if directory:
                if os.path.isdir(path):
                    return path
            else:
                recover_file(path)
                if os.path.isfile(path):
                    return path
        return None

    def migrate_directory(self, component, target, factory, defaults=None):
        source = self.previous_path(component, directory=True)
        if source is None:
            return False
        profile = self.directory(self.active)
        staging = tempfile.mkdtemp(prefix='.rename-', dir=profile)
        try:
            # Recover transactions before copying; never move/remove the old profile.
            factory(source).recover()
            for directory, dirs, files in os.walk(source):
                dirs[:] = [name for name in dirs if not os.path.islink(os.path.join(directory, name))]
                for name in files:
                    path = os.path.join(directory, name)
                    if not name.endswith('.json') or os.path.islink(path):
                        continue
                    destination = os.path.join(staging, os.path.relpath(path, source))
                    SettingsStore(destination).write(read_object(path))
            store = factory(staging)
            if defaults is None:
                store.load()
            else:
                store.load(defaults)
            os.rename(staging, target)
        finally:
            if os.path.isdir(staging):
                shutil.rmtree(staging)
        return True

    def discard_previous(self, component):
        """Remove the renamed files and folders of a component once its own store exists."""
        profile = self.directory(self.active)
        if not (os.path.isfile(self.path(component)) or os.path.isdir(os.path.join(profile, component))):
            return
        for name in previous_sections(component) + (previous_name(component),):
            if name == component:
                continue
            path = os.path.join(profile, name)
            try:
                for document in (path + '.json', path + '.json.previous'):
                    if os.path.isfile(document) and not os.path.islink(document):
                        os.remove(document)
                if name in previous_sections(component) and os.path.isdir(path) and not os.path.islink(path):
                    remove_settings_folder(path)
            except (IOError, OSError, ValueError):
                LOG.warning('Could not remove previous settings %s', path, exc_info=True)

    def discard_removed(self):
        profile = self.directory(self.active)
        for name in REMOVED_SECTIONS:
            path = os.path.join(profile, name + '.json')
            try:
                if os.path.isfile(path) and not os.path.islink(path):
                    os.remove(path)
            except (IOError, OSError):
                LOG.warning('Could not remove settings of a removed feature %s', path, exc_info=True)

    def load(self, component, defaults, legacy=None):
        component = part_name(component)
        values = self._load(component, defaults, legacy)
        # Migrated and written: the previous copy is no longer a needed backup.
        self.discard_previous(component)
        return values

    def _load(self, component, defaults, legacy=None):
        if component not in self.defaults:
            self.defaults[component] = copy.deepcopy(defaults)
        defaults = self.defaults[component]
        if component == 'minimap_enhancements':
            from driftkings.settings.minimap_store import MinimapStore
            directory = os.path.join(self.directory(self.active), part_name(component))
            if not os.path.isdir(directory):
                self.migrate_directory(component, directory, MinimapStore, defaults)
            if os.path.isdir(directory):
                MinimapStore(directory).recover()
                if os.path.isfile(os.path.join(directory, 'minimap.json')):
                    return MinimapStore(directory).load(defaults)
        path = self.path(component)
        recover_file(path)
        if os.path.isfile(path):
            values = migrate_values(component, read_object(path))
            if component == 'main':
                # The installer may create main.json with only its switch.
                values = migrate_main_options(values, self.path('hangar_preferences'))
        else:
            old_path = self.previous_path(component)
            values = read_object(old_path) if old_path else None
            if values is None and self.active == 'default':
                central = SettingsStore(os.path.join(self.root, 'driftkings.json')).read()['components']
                values = central.get(component)
                if values is None:
                    values = next((central[name] for name in section_aliases(component) if name in central), None)
                if values is None:
                    values = legacy() if legacy else {}
            if component == 'profile_ratings' and not values:
                from driftkings.core.profile_ratings import migrate_profile_options
                previous = self.path('hangar_preferences')
                if os.path.isfile(previous):
                    values = migrate_profile_options(read_object(previous))
            if component == 'main':
                values = migrate_main_options(values or {}, self.path('hangar_preferences'))
            values = migrate_values(component, {} if values is None else values)
            validate_types(defaults, values, component)
            values = merge(defaults, values)
            SettingsStore(path).write(values)
        validate_types(defaults, values, component)
        if component == 'minimap_enhancements':
            from driftkings.settings.minimap_store import MinimapStore
            # Keep the previous single file untouched as a migration backup.
            initial = merge(defaults, values)
            if not initial.get('minimapSchema'):
                for item in initial['circles'].values():
                    item['alpha'] = initial['alpha']
                initial['minimapSchema'] = 1
            return MinimapStore(directory).load(initial)
        return merge(defaults, values)

    def save(self, component, values):
        component = part_name(component)
        if component == 'minimap_enhancements':
            from driftkings.settings.minimap_store import MinimapStore
            directory = os.path.join(self.directory(self.active), part_name(component))
            validate_types(self.defaults.get(component, {}), values, component)
            return MinimapStore(directory).save(values)
        path = self.path(component)
        recover_file(path)
        previous = read_object(path) if os.path.isfile(path) else {}
        candidate = merge(previous, values)
        validate_types(self.defaults.get(component, {}), candidate, component)
        SettingsStore(path).write(candidate)
        return copy.deepcopy(candidate)

    def split_store(self, component, factory, files, legacy_directory):
        component = part_name(component)
        store = self._split_store(component, factory, files, legacy_directory)
        self.discard_previous(component)
        return store

    def _split_store(self, component, factory, files, legacy_directory):
        target = os.path.join(self.directory(self.active), part_name(component))
        def create(directory, migrating=False):
            if component == 'team_panels':
                return factory(directory, legacy_root=self.root if migrating and self.active == 'default' else False)
            return factory(directory)
        if os.path.isdir(target):
            return create(target)
        if self.migrate_directory(component, target, create):
            return create(target)
        profile = self.directory(self.active)
        if not os.path.isdir(profile):
            os.makedirs(profile)
        staging = tempfile.mkdtemp(prefix='.settings-', dir=profile)
        try:
            if self.active == 'default':
                migration_files = tuple(files) + (('.transaction.json',) if component == 'team_panels' else ())
                if component == 'team_panels':
                    from driftkings.settings.team_panel_store import LEGACY_FILES
                    migration_files += LEGACY_FILES
                for name in migration_files:
                    source = os.path.join(legacy_directory, name)
                    recover_file(source)
                    if os.path.isfile(source):
                        SettingsStore(os.path.join(staging, name)).write(read_object(source))
            # Use each feature's own validator and existing split-file migration.
            create(staging, True).load()
            os.rename(staging, target)
        finally:
            if os.path.isdir(staging):
                shutil.rmtree(staging)
        return create(target)


def remove_settings_folder(path):
    """Delete a previous settings folder only when it holds nothing but JSON documents."""
    for directory, dirs, files in os.walk(path):
        for name in dirs + files:
            if os.path.islink(os.path.join(directory, name)):
                raise ValueError('Link in previous settings folder')
        for name in files:
            if not (name.endswith('.json') or name.endswith('.json.previous')):
                raise ValueError('Unexpected file in previous settings folder: ' + name)
    shutil.rmtree(path)


settings_loader = SettingsLoader('./mods/configs/driftkings', user_settings)
