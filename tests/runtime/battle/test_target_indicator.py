# -*- coding: utf-8 -*-
"""Targets can temporarily lack metadata or loaded collision bounds."""
from support import RuntimeTest, module, source


class FixedPublicInfo(object):
    """Client mapping protocol: indexed fields, without dict methods."""
    def __init__(self, fields):
        self.fields = fields

    def __getitem__(self, key):
        return self.fields[key]


class TargetIndicatorTests(RuntimeTest):
    def setUp(self):
        super(TargetIndicatorTests, self).setUp()
        class Vehicle(object):
            isStarted = True
            inWorld = True
            isHidden = False
            publicInfo = {'team': 2}
            typeDescriptor = None
            def isAlive(self):
                return True
        self.vehicle = Vehicle()
        self.player = module(isObserver=lambda: False, isVehicleAlive=True,
                             autoAimVehicle=self.vehicle, team=1)
        constants = self.load('_constants')
        api = source('battle/autoaim_target_indicator.py', {
            'BigWorld': module(), 'Math': module(),
            'AvatarInputHandler': module(cameras=module()),
            'Vehicle': module(Vehicle=Vehicle),
            'driftkings._constants': constants,
            'driftkings.core.battle_events': module(battleEvents=module()),
            'driftkings.core.callbacks': module(callback=None, cancelCallback=None),
            'driftkings.flash.core': module(Align=None, ElementType=None, overlays=None),
            'driftkings.settings.service': module(settings_service=module(
                getComponentDict=lambda config: {'enabled': True})),
            'driftkings.settings.definitions.battle.autoaim_target_indicator': module(
                AutoaimTargetIndicatorSettings=lambda: module(NAME='target')),
        })
        self.controller = api['controller']

    def test_missing_public_info_hides_box(self):
        self.vehicle.publicInfo = None
        self.assertIsNone(self.controller.targetBounds(self.player))

    def test_missing_descriptor_hides_box(self):
        self.assertIsNone(self.controller.targetBounds(self.player))

    def test_enemy_fixed_public_info_needs_no_dict_methods(self):
        self.vehicle.publicInfo = FixedPublicInfo({'team': 2})
        self.assertIsNone(self.controller.targetBounds(self.player))

    def test_allied_fixed_public_info_is_rejected_before_geometry(self):
        class UnavailableDescriptor(object):
            @property
            def hull(self):
                raise AssertionError('Allied geometry must not be inspected')
        self.vehicle.typeDescriptor = UnavailableDescriptor()
        self.vehicle.publicInfo = FixedPublicInfo({'team': self.player.team})
        self.assertIsNone(self.controller.targetBounds(self.player))

    def test_missing_or_unknown_team_hides_box(self):
        for info in ({}, FixedPublicInfo({}), FixedPublicInfo({'team': None})):
            self.vehicle.publicInfo = info
            self.assertIsNone(self.controller.targetBounds(self.player))

    def test_missing_or_incomplete_bounds_hide_box(self):
        for bounds in (None, (), (object(),)):
            self.vehicle.typeDescriptor = module(hull=module(hitTester=module(bbox=bounds)))
            self.assertIsNone(self.controller.targetBounds(self.player))
