# -*- coding: utf-8 -*-
"""MainGun HUD presentation. All targets and states arrive from the battle component."""
from importlib import import_module

from driftkings._constants import GLOBAL, HIGH_CALIBER_PROGRESS
from driftkings.core.hud_visibility import hudVisibility
from driftkings.gameface.battle.common import BattleCardAdapter
from driftkings.logger import get_logger
from driftkings.settings.service import settings_service
from driftkings.views.marks_model import moved_panel, number_locale

LOG = get_logger('Driftkings.MainGunBattle')
FEATURE = 'DriftkingsMainGun'


def _component():
    return import_module('driftkings.battle.high_caliber_progress')


class MainGunAdapter(BattleCardAdapter):
    def __init__(self):
        super(MainGunAdapter, self).__init__(FEATURE, HIGH_CALIBER_PROGRESS, LOG, 'MainGun', active=True)

    def onInstalled(self):
        hudVisibility.attach(self)

    def beforeDispose(self):
        self.active = False
        hudVisibility.detach(self)

    def savePosition(self, child, args):
        settings = settings_service.getComponentDict(_component().config)
        if (not self.active or not self.hudVisible or not child._guiVisible
                or not child._cursorVisible or settings.get('textLock', False)
                or not _component().mainGuns.payload.get('visible')):
            return
        panel = moved_panel(settings[HIGH_CALIBER_PROGRESS.TEXT_POSITION], args)
        if panel is None:
            return
        settings_service.apply(_component().config, {HIGH_CALIBER_PROGRESS.TEXT_POSITION: panel})

    def refresh(self):
        settings = settings_service.getComponentDict(_component().config)
        config = dict(settings.get('gameface', {}))
        config.update(settings[HIGH_CALIBER_PROGRESS.TEXT_POSITION])
        config.update(locked=settings['textLock'],
                      backgroundColor='#0f1216',
                      backgroundOpacity=max(0, min(1, settings['background']['alpha'] / 100.0))
                      if settings['backGroundEnabled'] else 0)
        payload = dict(_component().mainGuns.payload)
        enabled = bool(self.active and self.visible and self.hudVisible and settings[GLOBAL.ENABLED]
                       and payload.get('visible'))
        labels = _component().config.i18n
        unavailable = payload.get('state') == 'unavailable'
        value = payload.get('damage', 0) if payload.get('state') == 'achieved' else payload.get('remaining', 0)
        group = number_locale(_component().config.lang)['groupSeparator']
        payload.update(config=config,
                       primaryText=labels['UI_hc_unavailable'] if unavailable else
                       u'{:,}'.format(int(value)).replace(',', group) + ' HP',
                       secondaryText=labels['UI_hc_' + (payload.get('reason') or payload.get('state', 'progress'))],
                       progressText=u'%d%%' % payload.get('progress', 0),
                       progressLabel=labels['UI_hc_progressLabel'])
        self.publish(payload, config, enabled)
