from support import RuntimeTest, Settings, game_source, module


class ProfileRatingTests(RuntimeTest):
    def setUp(self):
        super(ProfileRatingTests, self).setUp()
        self.settings = {'enabled': True}
        self.api, _ = game_source('gameface/lobby/profile_ratings.py', {
            'driftkings.settings.service': Settings(self.settings).service(),
        }, real=('driftkings.common.utils.colorratting',))
        self.stats = module(getBattlesCount=lambda: 51000, getAvgDamage=lambda: 1800,
                            getWinsEfficiency=lambda: 0.5686)
        self.model = module(getBattlesLeftCount=lambda: 0, getIsWTREnabled=lambda: True,
                            getPersonalScore=lambda: 5517, getPrevPersonalScore=lambda: 5100)
        self.presenter = module(_SummaryView__dossier=module(getRandomStats=lambda: self.stats),
                                viewModel=self.model)

    def test_uses_raw_stats_and_correct_rating_metric(self):
        actual = self.api['colors'](self.presenter)
        color = self.api['getStatisticColor']
        self.assertEqual(actual['wins'], color('winrate', 56.86))
        self.assertEqual(actual['battles'], color('battles', 51000))
        self.assertEqual(actual['damage'], color('avgDamage', 1800))
        self.assertEqual(actual['rating'], color('wtr', 5517))
        self.model.getIsWTREnabled = lambda: False
        self.assertEqual(self.api['colors'](self.presenter)['rating'], color('wgr', 5517))
        self.assertFalse(set(actual) & {'assistance', 'blocked', 'maxDamage', 'maxExperience'})

    def test_disabled_missing_data_and_unqualified_rating(self):
        self.settings['enabled'] = False
        self.assertEqual(self.api['colors'](self.presenter), {})
        self.settings['enabled'] = True
        self.settings['summaryColors'] = False
        self.assertEqual(self.api['colors'](self.presenter), {})
        self.settings['summaryColors'] = True
        self.assertIn('rating', self.api['colors'](self.presenter))
        self.model.getBattlesLeftCount = lambda: 5
        self.assertNotIn('rating', self.api['colors'](self.presenter))
        self.presenter._SummaryView__dossier = None
        self.assertEqual(self.api['colors'](self.presenter), {})

    def test_native_presenter_without_weakrefs_and_child_cleanup(self):
        import json
        import weakref
        Summary = type('SummaryView', (object,), {'__slots__': ('parentView',)})
        presenter = Summary()
        with self.assertRaises(TypeError):
            weakref.ref(presenter)
        payloads = []

        class ChildBase(object):
            def __init__(self, **kwargs):
                pass

            def getViewModel(self):
                return module(_setString=lambda index, value: payloads.append(json.loads(value)))

            def _finalize(self):
                pass

        Main = type('AchievementMainView', (object,), {})
        api, hooks = game_source('gameface/lobby/profile_ratings.py', {
            'driftkings.settings.service': Settings(self.settings).service(),
            'frameworks.wulf': module(ViewModel=object),
            'gui.impl.pub.view_component': module(ViewComponent=ChildBase),
            'gui.impl.lobby.achievements.achievements_main_view': module(AchievementMainView=Main),
            'gui.impl.lobby.achievements.summary.summary_view': module(SummaryView=Summary),
            'driftkings.gameface.core': module(attach_assets=lambda *args: None, resource_id=lambda key: 123),
            'driftkings.interface_catalog': module(gameface_spec=lambda name: {'resource': 'test'}),
        })
        api['colors'] = lambda current: {'wins': '#00CC00'} if self.settings['enabled'] else {}
        api['install']()
        children = {}
        parent = module(currentPresenter=presenter, getChildView=lambda key: children.get(key),
                        setChildView=lambda key, child: children.update({key: child}))
        presenter.parentView = parent
        hooks.get('AchievementMainView', '_onLoading')(lambda *args: None, parent)
        child = children[123]
        self.assertIs(child.presenter, presenter)
        self.assertEqual(payloads[-1], {'wins': '#00CC00'})
        self.settings['enabled'] = False
        child.refresh()
        self.assertEqual(payloads[-1], {})
        child._finalize()
        self.assertIsNone(child.presenter)
