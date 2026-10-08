# -*- coding: utf-8 -*-
"""Window edit session: draft (view) -> applied (live mod values) -> saved (JSON).
Apply publishes drafts to the mods, Save persists applied values, Cancel drops
drafts since the last Apply, Discard also reverts applied values to the saved ones.
"""
import copy

from Driftkings.settings.panel import logger


class SaveError(IOError):
    def __init__(self, mods):
        IOError.__init__(self, 'Could not save: ' + ', '.join(mods))
        self.mods = mods


class EditSession(object):
    def __init__(self, registry):
        self.registry = registry
        self.drafts = {}
        self.history = []

    def _mod(self, mod_id):
        return self.registry.mods[mod_id]

    def value(self, mod_id, key):
        draft = self.drafts.get(mod_id, {})
        return draft[key] if key in draft else self._mod(mod_id).values[key]

    def values(self, mod_id):
        result = copy.deepcopy(self._mod(mod_id).values)
        result.update(copy.deepcopy(self.drafts.get(mod_id, {})))
        return result

    def set(self, mod_id, key, value):
        mod = self._mod(mod_id)
        control = mod.index.get(key)
        if control is None or not control.has_value:
            raise ValueError('Unknown setting: %s' % key)
        if key in self.disabled(mod_id):
            raise ValueError('Setting is disabled: %s' % key)
        normalized = control.validate(value)
        self.history.append(copy.deepcopy(self.drafts))
        self.history = self.history[-50:]
        draft = self.drafts.setdefault(mod_id, {})
        if normalized == mod.values[key]:
            draft.pop(key, None)
        else:
            draft[key] = normalized
        if not draft:
            self.drafts.pop(mod_id, None)
        return normalized

    def reset(self, mod_id):
        """Restore defaults of the mod in the draft; secrets are kept on purpose."""
        mod = self._mod(mod_id)
        self.history.append(copy.deepcopy(self.drafts))
        self.history = self.history[-50:]
        for control in mod.value_controls():
            if control.secret or control.id in self.disabled(mod_id):
                continue
            draft = self.drafts.setdefault(mod_id, {})
            if control.default == mod.values[control.id]:
                draft.pop(control.id, None)
            else:
                draft[control.id] = copy.deepcopy(control.default)
        if not self.drafts.get(mod_id):
            self.drafts.pop(mod_id, None)

    def undo(self):
        if self.history:
            self.drafts = self.history.pop()

    def cancel(self):
        self.history = []
        self.drafts.clear()

    def apply(self):
        changed = []
        for mod_id, values in self.drafts.items():
            if any(not self._mod(mod_id).index[key].enabled for key in values):
                raise ValueError('Draft contains disabled settings')
        for mod_id in sorted(self.drafts):
            if mod_id not in self.registry.mods:
                continue
            if any(not dep['installed'] for dep in self.registry.dependency_status(self._mod(mod_id))):
                raise ValueError('Missing mod dependency')
            if self.registry.apply_values(mod_id, self.drafts[mod_id]):
                changed.append(mod_id)
        self.drafts.clear()
        self.history = []
        return changed

    def save(self):
        self.apply()
        failed = []
        for mod_id, mod in sorted(self.registry.mods.items()):
            if mod.values != mod.saved:
                try:
                    self.registry.save(mod_id)
                except (IOError, OSError, ValueError):
                    failed.append(mod_id)
                    logger.exception('Could not save %s', mod_id)
        if failed:
            raise SaveError(failed)

    def discard(self):
        self.drafts.clear()
        for mod_id, mod in sorted(self.registry.mods.items()):
            reverted = dict((key, value) for key, value in mod.saved.items() if mod.values.get(key) != value)
            if reverted:
                self.registry.apply_values(mod_id, reverted)

    # State ------------------------------------------------------------------
    def changed_keys(self, mod_id):
        """Settings that differ from the saved file (applied or not)."""
        mod = self._mod(mod_id)
        return sorted(key for key in mod.saved if self.value(mod_id, key) != mod.saved[key])

    def pending_apply(self):
        return any(self.drafts.values())

    def unsaved(self):
        return any(self.changed_keys(mod_id) for mod_id in self.registry.mods)

    def disabled(self, mod_id):
        """Statically disabled controls and those whose dependencies are not met."""
        mod = self._mod(mod_id)
        result = {}
        if any(not dep['installed'] for dep in self.registry.dependency_status(mod)):
            return [c.id for c in mod.controls]

        def blocked(control, trail):
            if control.id in result:
                return result[control.id]
            state = not control.enabled
            for key, expected in control.depends_on.items():
                if state:
                    break
                target = mod.index[key]
                if target.id in trail:
                    state = True
                    break
                state = blocked(target, trail + (control.id,)) or self.value(mod_id, key) not in expected
            result[control.id] = state
            return state

        for control in mod.controls:
            blocked(control, ())
        return sorted(key for key, state in result.items() if state)
