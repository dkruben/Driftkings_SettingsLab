from support import RuntimeTest, Settings, game_source, module


class VehicleListColorsTests(RuntimeTest):
    def setUp(self):
        super(VehicleListColorsTests, self).setUp()
        self.settings = {'enabled': True, 'vehicleColors': True}
        self.api, _ = game_source('flash/lobby/profile_statistics.py', {
            'driftkings.settings.service': Settings(self.settings).service(),
        }, real=('driftkings.common.utils.colorratting', 'driftkings.core.profile_ratings'))
        self.row = module(name='renderer0', data=module(id=123),
                          vehicleTF=module(textColor=1), battlesTF=module(textColor=2),
                          winsTF=module(textColor=3))
        content = module(numChildren=1, getChildAt=lambda index: self.row)
        decoration = module()
        listing = module(numChildren=2, getChildAt=lambda index: (content, decoration)[index])
        self.view = module(isActive=True,
                           flashObject=module(listComponent=module(techniqueList=listing)),
                           _dkVehicleOriginalColors={},
                           _dkVehicleColors={123: {'vehicleTF': 100, 'battlesTF': 200, 'winsTF': 300}})

    def test_native_fields_colored_and_restored_when_disabled(self):
        self.api['paint_vehicle_list'](self.view)
        self.assertEqual((self.row.vehicleTF.textColor, self.row.battlesTF.textColor,
                          self.row.winsTF.textColor), (100, 200, 300))
        self.settings['vehicleColors'] = False
        self.api['paint_vehicle_list'](self.view)
        self.assertEqual((self.row.vehicleTF.textColor, self.row.battlesTF.textColor,
                          self.row.winsTF.textColor), (1, 2, 3))

    def test_recycled_renderer_does_not_keep_previous_vehicle_colors(self):
        self.api['paint_vehicle_list'](self.view)
        self.row.data.id = 456
        self.view._dkVehicleColors[456] = {'battlesTF': 400, 'winsTF': 500}
        self.api['paint_vehicle_list'](self.view)
        self.assertEqual((self.row.vehicleTF.textColor, self.row.battlesTF.textColor,
                          self.row.winsTF.textColor), (1, 400, 500))

    def test_inactive_view_is_not_painted(self):
        self.view.isActive = False
        self.api['paint_vehicle_list'](self.view)
        self.assertEqual(self.row.vehicleTF.textColor, 1)
        self.assertEqual(self.view._dkVehicleOriginalColors, {})
