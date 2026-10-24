import json
import os
import shutil
import tempfile
from support import RuntimeTest, game_source, module


class ProfileOptionsTests(RuntimeTest):
    def setUp(self):
        super(ProfileOptionsTests, self).setUp()
        path = os.path.join(os.path.dirname(__file__), '../../res/configs/driftkings/default/profile_ratings.json')
        with open(path, 'rb') as stream:
            self.defaults = json.loads(stream.read().decode('utf-8-sig'))


    def test_threshold_editing_rejects_invalid_limits_without_saving(self):
        api, _ = game_source('settings/definitions/lobby/profile_ratings.py', {
            'driftkings.settings.definitions.base': module(SectionDefinition=object),
        }, real=('driftkings.core.profile_ratings', 'driftkings.settings.controls_schema'))
        config = api['ProfileRatingsSettings']()
        for invalid in ('20,30', '20,20,40,50,60', '20,30,40,50,101', 'nan,30,40,50,60'):
            values = dict(self.defaults, survivalThresholds=invalid)
            with self.assertRaises(ValueError):
                config.normalize_changes(values, {'survivalThresholds': invalid})
            self.assertEqual(config.normalize_loaded(values)['survivalThresholds'], self.defaults['survivalThresholds'])
        valid = dict(self.defaults, survivalThresholds='10, 20, 35, 50, 70', receivedDamageThresholds='10,25,50,100,200')
        self.assertEqual(config.normalize_changes(valid, valid), valid)
        self.assertEqual(config.NAME, 'profile_ratings')
