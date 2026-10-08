# -*- coding: utf-8 -*-
"""Wwise events only. Bank registration never loads or rewrites original banks."""


class SoundError(ValueError):
    def __init__(self, key):
        ValueError.__init__(self, key)
        self.key = key


class SoundManager(object):
    def __init__(self, factory=None):
        self.factory = factory
        self.banks = {}
        self.playing = {}

    def register(self, mod_id, bank, events, loaded=None, volume=None):
        if not bank.lower().endswith('.bnk') or not events or not all(isinstance(e, (str, type(u''))) and e for e in events):
            raise ValueError('Register a bank and named Wwise events')
        self.banks[mod_id] = {'bank': bank, 'events': tuple(events), 'loaded': loaded, 'volume': volume}

    def status(self, mod_id):
        bank = self.banks[mod_id]
        try:
            return bank['loaded']() if callable(bank['loaded']) else bank['loaded']
        except Exception:
            from Driftkings.settings.panel import logger
            logger.error('Could not query sound bank: %s', mod_id)
            return None

    def play(self, event, mod_id=None):
        candidates = [mod_id] if mod_id else list(self.banks)
        owner = next((key for key in candidates if key in self.banks and event in self.banks[key]['events']), None)
        if owner is None:
            raise SoundError('sound.eventMissing')
        if self.status(owner) is False:
            raise SoundError('sound.missing')
        self.stop(event)
        if self.factory is None:
            from SoundGroups import g_instance
            factory = g_instance.getSound2D
        else:
            factory = self.factory
        try:
            sound = factory(event)
            if sound is None:
                raise SoundError('sound.eventMissing')
            sound.play()
        except Exception:
            raise SoundError('sound.eventMissing')
        self.playing[event] = sound

    def stop(self, event=None):
        for name in [event] if event else list(self.playing):
            sound = self.playing.pop(name, None)
            if sound is not None:
                try:
                    sound.stop()
                except Exception:
                    from Driftkings.settings.panel import logger
                    logger.error('Could not stop preview event: %s', name)

    def set_volume(self, mod_id, value):
        callback = self.banks[mod_id]['volume']
        if not callable(callback) or not 0 <= value <= 100:
            raise ValueError('This mod does not expose volume control')
        callback(value)


sound_manager = SoundManager()
