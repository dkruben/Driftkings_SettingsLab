# -*- coding: utf-8 -*-
"""View-independent window logic: JSON schema/state for Gameface and action handling.

schema changes only when mods, controls or the language change; state changes on
every edit, so the view can patch values without rebuilding the DOM.
"""
from Driftkings.settings.panel import logger
from Driftkings.settings.panel.controls import resolve_text
from Driftkings.settings.panel.session import EditSession, SaveError
from Driftkings.settings.panel.sound import SoundError

MAX_REQUEST = 2097152
CORE_ID = 'dk.settings'


class Presenter(object):
    def __init__(self, api):
        self.api = api
        self.registry = api.registry
        self.session = EditSession(api.registry)
        self.selected = None
        self.confirming = False
        self.restart_prompt = False
        self.close_after_restart = False
        self.message = None
        self._sequence = 0
        self.capture = None
        self.key_names = {}
        self.profile_text = ''
        from Driftkings.settings.panel.profiles import Profiles
        self.profiles = Profiles(api)
        from Driftkings.settings.panel.media import ImagePreviews
        self.image_previews = ImagePreviews()

    # Payloads -----------------------------------------------------------
    def schema(self):
        language = self.api.language
        from Driftkings.settings.panel.sound import sound_manager
        mods = []
        for mod in self.registry.ordered():
            from Driftkings.settings.panel.layout import balance_columns
            balance_columns(mod.controls)
            mods.append({
                'id': mod.id,
                'name': resolve_text(mod.name, language),
                'version': mod.version,
                'author': mod.author,
                'description': resolve_text(mod.description, language),
                'icon': mod.icon,
                'soundBank': sound_manager.banks.get(mod.id, {}).get('bank'),
                'category': resolve_text(mod.category, language) if mod.category else '',
                'dependencies': self.registry.dependency_status(mod),
                'controls': [control.describe(language) for control in mod.controls if control.visible],
            })
        return {'language': language, 'labels': self.api.strings, 'mods': mods}

    def state(self):
        mods = self.registry.mods
        if self.selected not in mods:
            ordered = self.registry.ordered()
            self.selected = ordered[0].id if ordered else None
        values, secrets, changed, disabled, status, compatibility_warnings = {}, {}, {}, {}, {}, {}
        from Driftkings.core.mod_compatibility import compatibility, CONFIRMED_CONFLICT
        for mod_id, mod in mods.items():
            component = mod.restart_key.split(':', 1)[0]
            warnings = compatibility.warnings_for(component)
            for warning in warnings:
                key = 'compatibility.confirmed' if warning['status'] == CONFIRMED_CONFLICT else 'compatibility.possible'
                warning['text'] = self.api.strings.get(key, warning['text']).format(integration=warning['integration'], component=component)
            compatibility_warnings[mod_id] = warnings
            current = self.session.values(mod_id)
            for control in mod.value_controls():
                if control.secret:
                    # The view never receives a stored secret, only whether one exists.
                    if current[control.id]:
                        secrets.setdefault(mod_id, []).append(control.id)
                    current[control.id] = u''
            values[mod_id] = current
            changed[mod_id] = self.session.changed_keys(mod_id)
            disabled[mod_id] = self.session.disabled(mod_id)
            status[mod_id] = {'status': mod.status, 'enabled': bool(current.get(getattr(mod, 'enabled_key', 'enabled'), True)),
                              'restartRequired': mod.restart_key in self.api.restart_required}
        previews = {}
        if self.selected in mods:
            for control in mods[self.selected].value_controls():
                if not control.preview or control.preview.get('kind') != 'image' or control.secret:
                    continue
                value = values[self.selected][control.id]
                images = control.preview.get('images')
                path = images[value] if images is not None and isinstance(value, int) and 0 <= value < len(images) else '' if images is not None else value
                previews[control.id] = self.image_previews.resolve(path)
        return {'selected': self.selected, 'compatibilityWarnings': compatibility_warnings, 'previews': previews, 'values': values, 'secrets': secrets, 'changed': changed,
                'disabled': disabled, 'status': status, 'pending': self.session.pending_apply(),
                'unsaved': self.session.unsaved(), 'confirm': self.confirming, 'message': self.message,
                'restartPrompt': self.restart_prompt, 'restartRequired': sorted(self.api.restart_required),
                'inBattle': self.api.in_battle,
                'theme': self.theme(), 'canUndo': bool(self.session.history), 'capture': self.capture,
                'keyNames': self.key_names, 'profiles': self.profiles.names(), 'profileText': self.profile_text,
                'diagnostics': self.diagnostics() if self.registry.get(CORE_ID, 'debug', False) else None}

    def diagnostics(self):
        from Driftkings.settings.panel import VERSION
        from Driftkings.settings.panel.sound import sound_manager
        return {'framework': VERSION, 'registeredMods': len(self.registry.mods),
                'viewModel': 'active', 'game': getattr(self.api, 'client_version', ''),
                'soundBanks': [{'mod': key, 'bank': data['bank'], 'loaded': sound_manager.status(key)}
                               for key, data in sound_manager.banks.items()]}

    def theme(self):
        from Driftkings.settings.panel.themes import describe
        return describe(self.session.values(CORE_ID)) if CORE_ID in self.registry.mods else {'accent': '#D98219'}

    def _say(self, key, kind='info'):
        self._sequence += 1
        self.message = {'id': self._sequence, 'kind': kind, 'text': self.api.strings.get(key, key)}

    def _say_text(self, text, kind='info'):
        self._sequence += 1
        self.message = {'id': self._sequence, 'kind': kind, 'text': text}

    # Actions --------------------------------------------------------------
    def handle(self, data):
        """Returns {'close': bool}; never raises for bad requests."""
        result = {'close': False}
        if not isinstance(data, dict):
            return result
        action = data.get('action')
        try:
            handler = getattr(self, '_on_' + str(action), None) if action else None
            if handler is None:
                raise ValueError('Unknown action: %r' % (action,))
            handler(data, result)
            if action != 'capture':
                self.capture = None
        except SoundError as error:
            self._say(error.key, 'error')
        except ValueError as error:
            logger.debug('Rejected settings request')
            self._say('invalidValue', 'error')
        except Exception as error:
            logger.error('Settings action failed (%s)', type(error).__name__)
            self._say('actionFailed', 'error')
        return result

    def _require_mod(self, data):
        mod_id = data.get('mod')
        if mod_id not in self.registry.mods:
            raise ValueError('Unknown mod')
        return mod_id

    def _on_select(self, data, result):
        from Driftkings.settings.panel.sound import sound_manager
        sound_manager.stop()
        self.selected = self._require_mod(data)

    def _on_set(self, data, result):
        mod_id = self._require_mod(data)
        if 'value' not in data:
            raise ValueError('Missing value')
        if 'alpha' not in data:
            self.session.set(mod_id, data.get('key'), data['value'])
        else:
            mod = self.registry.mods[mod_id]
            control = mod.index.get(data.get('key'))
            if control is None or control.type != 'color' or not control.metadata.get('allowAlpha'):
                raise ValueError('Alpha is not enabled')
            alpha_key = control.metadata.get('alphaKey')
            alpha_control = mod.index.get(alpha_key)
            if alpha_key == control.id or alpha_control is None or alpha_control.type not in ('slider', 'number'):
                raise ValueError('Invalid alpha association')
            changes = [(control.id, control.validate(data['value'])),
                       (alpha_key, alpha_control.validate(data['alpha']))]
            disabled = self.session.disabled(mod_id)
            if any(key in disabled for key, value in changes):
                raise ValueError('Setting is disabled')
            scale_max = {'percent': 100, 'normalized': 1, 'byte': 255}[control.metadata.get('alphaScale', 'percent')]
            if not 0 <= data['alpha'] <= scale_max:
                raise ValueError('Alpha outside its scale')
            changes = [(key, value) for key, value in changes if self.session.value(mod_id, key) != value]
            # Reuse the first snapshot produced by EditSession.set. Keep its
            # existing history limit, including when two sets cross that limit.
            previous_history = self.session.history[:]
            first = None
            try:
                for key, value in changes:
                    self.session.set(mod_id, key, value)
                    if first is None:
                        first = self.session.history[-1]
                if first is not None:
                    self.session.history = (previous_history + [first])[-50:]
            except Exception:
                if first is not None:
                    self.session.drafts = first
                self.session.history = previous_history
                raise
        preview = self.registry.mods[mod_id].index[data['key']].preview
        if preview and preview.get('kind') == 'audio':
            from Driftkings.settings.panel.sound import sound_manager
            sound_manager.stop()

    def _on_reset_theme(self, data, result):
        import copy
        self.session.history.append(copy.deepcopy(self.session.drafts))
        self.session.history = self.session.history[-50:]
        mod = self.registry.mods[CORE_ID]
        for key in ('theme', 'accent', 'background', 'textColor', 'secondary', 'border', 'hover', 'opacity', 'sidebarOpacity', 'uiScale', 'fontSize', 'sectionFontSize'):
            self.session.drafts.setdefault(CORE_ID, {})[key] = copy.deepcopy(mod.index[key].default)

    def _on_reset(self, data, result):
        from Driftkings.settings.panel.sound import sound_manager
        sound_manager.stop()
        self.session.reset(self._require_mod(data))
        self._say('resetDone')

    def _on_cancel(self, data, result):
        from Driftkings.settings.panel.sound import sound_manager
        sound_manager.stop()
        self.session.cancel()

    def _on_apply(self, data, result):
        self.api.apply_session(self.session)
        self._say('applied')
        self.restart_prompt = bool(self.api.restart_required)

    def _on_save(self, data, result):
        if self._save():
            self._close_or_restart(result)

    def _close_or_restart(self, result):
        self.restart_prompt = bool(self.api.restart_required)
        self.close_after_restart = True
        result['close'] = not self.restart_prompt

    def _on_restart(self, data, result):
        if not self.restart_prompt:
            raise ValueError('No restart request pending')
        choice = data.get('choice')
        if choice == 'now':
            if self.api.in_battle or self.session.unsaved() or not self.api.restart_required:
                raise ValueError('Restart is not available')
            result['restart'] = True
            result['close'] = True
        elif choice == 'later':
            result['close'] = self.close_after_restart
        else:
            raise ValueError('Unknown restart choice')
        self.restart_prompt = False
        self.close_after_restart = False

    def _save(self):
        try:
            self.api.save_session(self.session)
        except SaveError:
            self._say('saveFailed', 'error')
            return False
        self._say('saved')
        return True

    def _on_close(self, data, result):
        if self.session.unsaved():
            self.confirming = True
        else:
            result['close'] = True

    def _on_confirm(self, data, result):
        choice = data.get('choice')
        self.confirming = False
        if choice == 'save':
            if self._save():
                self._close_or_restart(result)
        elif choice == 'discard':
            self.api.discard_session(self.session)
            result['close'] = True
        elif choice != 'stay':
            raise ValueError('Unknown choice')

    def _on_button(self, data, result):
        mod_id = self._require_mod(data)
        if data.get('key') in self.session.disabled(mod_id):
            raise ValueError('Action is disabled')
        text = self.registry.run_button(mod_id, data.get('key'), self.session.values(mod_id))
        if text:
            self._say_text(text)

    def _on_undo(self, data, result):
        from Driftkings.settings.panel.sound import sound_manager
        sound_manager.stop()
        self.session.undo()

    def _on_capture(self, data, result):
        mod = self._require_mod(data)
        key = data.get('key')
        if self.registry.mods[mod].index[key].type != 'hotkey' or key in self.session.disabled(mod):
            raise ValueError('Invalid hotkey')
        self.capture = {'mod': mod, 'key': key}

    def _on_profile(self, data, result):
        if self.api.in_battle:
            raise ValueError('Profiles can only be changed in the hangar')
        action, name = data.get('operation'), data.get('name')
        if action in ('create', 'duplicate'):
            if name in self.profiles.names():
                raise ValueError('Profile already exists')
            self.profiles.save(name, self.session)
        elif action == 'load':
            self.profiles.load(name, self.session)
        elif action == 'rename':
            self.profiles.rename(name, data.get('target'))
        elif action == 'delete':
            self.profiles.delete(name)
        elif action == 'export':
            import json
            from Driftkings.settings.panel.storage import ConfigStore
            import os
            exported = self.profiles.export(self.session)
            ConfigStore(os.path.join(self.api.root, 'exports')).write('dk_settings_profile', exported)
            self.profile_text = json.dumps(exported, ensure_ascii=False, indent=2)
        elif action == 'import':
            import json
            self.profiles.stage(self.session, json.loads(data.get('text', '')))
        else:
            raise ValueError('Unknown profile action')
        self._say('profileDone')

    def dispose(self):
        """Window closed by the game (context change): unsaved edits are discarded."""
        from Driftkings.settings.panel.sound import sound_manager
        sound_manager.stop()
        self.image_previews.clear()
        if self.session.drafts or self.session.unsaved():
            self.api.discard_session(self.session)
