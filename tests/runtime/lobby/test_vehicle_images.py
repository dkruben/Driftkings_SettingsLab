# -*- coding: utf-8 -*-
from support import RuntimeTest


class VehicleImageTests(RuntimeTest):
    def setUp(self):
        super(VehicleImageTests, self).setUp()
        self.resolve = self.load('core.vehicle_images').resolve_vehicle_images

    def test_halloween_paths_come_from_native_catalogue(self):
        calls = []
        def icon(name):
            calls.append(name)
            return 'halloween|gui/maps/icons/vehicle/uk-GB24_Centurion_Mk3_HW_BOT.png'
        text = "Name<img src='img://gui/maps/icons/vehicle/uk-GB24_Centurion_Mk3_HW_BOT.png' width='80'>"
        result = self.resolve(text, icon, lambda name: self.fail('wrong icon kind'))
        self.assertEqual(calls, ['uk:GB24_Centurion_Mk3_HW_BOT'])
        self.assertEqual(result, text.replace('img://gui/', 'img://halloween|gui/'))

    def test_contour_and_relative_native_path(self):
        text = '<img height="24" src="img://gui/maps/icons/vehicle/contour/usa-A35_Pershing_HW_BOT.png" />'
        result = self.resolve(text, lambda name: self.fail('wrong icon kind'),
                              lambda name: '../maps/icons/vehicle/contour/unknown.png')
        self.assertEqual(result, text.replace('usa-A35_Pershing_HW_BOT', 'unknown'))

    def test_missing_image_removes_only_image_tag(self):
        text = "Tank<img src='img://gui/maps/icons/vehicle/unknown-event.png'> HP 100"
        self.assertEqual(self.resolve(text, lambda name: '', lambda name: ''), 'Tank HP 100')

    def test_unrelated_and_already_resolved_images_are_preserved(self):
        text = "<img src='img://halloween|gui/maps/icons/vehicle/bot.png'><img src='img://gui/maps/icons/other.png'>"
        def unexpected(name):
            self.fail('unrelated image resolved')
        self.assertEqual(self.resolve(text, unexpected, unexpected), text)
