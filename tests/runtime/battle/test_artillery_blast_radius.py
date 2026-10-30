# -*- coding: utf-8 -*-
"""Artillery blast radius: shown only for SPG high explosive shells in the chosen camera modes."""
import json
import os

from support import RuntimeTest, Settings, game_source, module

ROOT = os.path.join(os.path.dirname(__file__), '..', '..', '..')
with open(os.path.join(ROOT, 'res', 'configs', 'driftkings', 'default', 'artillery_blast_radius.json'), 'rb') as stream:
    DEFAULTS = json.loads(stream.read().decode('utf-8-sig'))
MODES = module(ARCADE='arcade', SNIPER='sniper', STRATEGIC='strategic', ARTY='arty')


class Marker(object):
    def __init__(self, data, position):
        self.path = data['path']
        self.cleared = False
        self.model = module(visible=False, scale=None, position=None,
                            root=module(attach=lambda area: None, detach=lambda area: None))

    def clear(self):
        self.cleared = True


class ArtilleryBlastRadiusTests(RuntimeTest):
    def setUp(self):
        super(ArtilleryBlastRadiusTests, self).setUp()
        self.data = dict(DEFAULTS)
        self.keys, self.messages = set(), []
        self.mode, self.kind, self.tag, self.marker = 'strategic', 'HIGH_EXPLOSIVE', 'SPG', [(1, 2, 3)]
        area = lambda: module(setup=lambda *args: None, enableAccurateCollision=lambda value: None,
                              updateHeights=lambda: None, attached=True)
        self.api, _ = game_source('battle/artillery_blast_radius.py', {
            'driftkings.settings.service': Settings(self.data).service(),
            'BigWorld': module(Model=module(), PyTerrainSelectedArea=area, player=lambda: None),
            'AvatarInputHandler.aih_global_binding': module(CTRL_MODE_NAME=MODES),
            'gui.shared.gui_items': module(Vehicle=module(getVehicleClassTag=lambda tags: self.tag)),
            'gui.shared.gui_items.Vehicle': module(VEHICLE_CLASS_NAME=module(SPG='SPG')),
            'driftkings.common.utils.exceptions': module(log_exceptions=lambda function: function),
            'driftkings.common.utils.game': module(checkKeys=lambda keys: str(keys) in self.keys),
            'driftkings.flash.battle.messages': module(sendPanelMessage=lambda text, color: self.messages.append(color)),
            'driftkings.common.utils.wgutils': module(getPlayer=lambda: self.player()),
            'driftkings.ui.common.markers': module(StaticWorldObjectMarker3D=Marker),
            'driftkings.settings.definitions.battle.artillery_blast_radius': module(
                ArtilleryBlastRadiusSettings=lambda: module(i18n={'UI_artySplash_messageSplashOn': 'on', 'UI_artySplash_messageSplashOff': 'off',
                                                                  'UI_artySplash_messageDotOn': 'on', 'UI_artySplash_messageDotOff': 'off'})),
        }, real=('driftkings._constants',))
        self.controller = self.api['controller']
        self.controller.startBattle()
        self.addCleanup(self.controller.stopBattle)

    def player(self):
        descriptor = module(type=module(tags=()), shot=module(shell=module(kind=self.kind, type=module(explosionRadius=4.5))))
        return module(spaceID=1, vehicleTypeDescriptor=descriptor, getVehicleDescriptor=lambda: descriptor,
                      gunRotator=module(markerInfo=self.marker), inputHandler=module(ctrlModeName=self.mode))

    def visible(self):
        self.controller.player = self.player()
        self.controller.working()
        return self.controller.modelSplash.model.visible, self.controller.modelDot.model.visible

    def test_splash_follows_the_marker_with_the_shell_radius(self):
        self.assertEqual(self.visible(), (True, True))
        model = self.controller.modelSplash.model
        self.assertEqual((model.scale, model.position), ((4.5, 4.5, 4.5), (1, 2, 3)))
        self.assertEqual(self.controller.modelDot.model.scale, (0.5, 0.5, 0.5))

    def test_hidden_for_other_shells_classes_and_unselected_modes(self):
        for change in (dict(kind='ARMOR_PIERCING'), dict(tag='heavyTank'), dict(mode='arcade'), dict(mode='sniper'), dict(marker=None)):
            saved = dict((key, getattr(self, key)) for key in change)
            self.__dict__.update(change)
            self.assertEqual(self.visible(), (False, False), change)
            self.__dict__.update(saved)
            self.assertEqual(self.visible(), (True, True))
        self.data['showModeArcade'] = True
        self.mode = 'arcade'
        self.assertEqual(self.visible(), (True, True))
        self.data['enabled'] = False
        self.assertEqual(self.visible(), (False, False))

    def test_keys_toggle_and_keep_each_model(self):
        event = module(isKeyDown=lambda: True)
        self.keys.add(str(self.data['buttonShowSplash']))
        self.controller.injectButton(event)
        self.assertEqual(self.messages, ['Red'])
        # The choice survives the next marker update instead of the default.
        self.assertEqual(self.visible(), (False, True))
        self.controller.injectButton(event)
        self.assertEqual(self.visible(), (True, True))

    def test_stop_clears_the_models(self):
        splash, dot = self.controller.modelSplash, self.controller.modelDot
        self.controller.stopBattle()
        self.assertTrue(splash.cleared and dot.cleared)
        self.assertIsNone(self.controller.modelSplash)
        self.controller.working()
