from support import RuntimeTest, game_source, module


class SyncEvent(object):
    def __init__(self):
        self.handlers = []

    def __iadd__(self, handler):
        self.handlers.append(handler)
        return self

    def __isub__(self, handler):
        self.handlers.remove(handler)
        return self

    def fire(self):
        for handler in list(self.handlers):
            handler('dossier', {})


class CarouselSyncTests(RuntimeTest):
    def test_dossier_sync_between_hangar_views_invalidates_cached_statistics(self):
        class ControllerBase(object):
            def __init__(self):
                self.views = {}

        event = SyncEvent()
        service = module(onModSettingsChanged=module(connect=lambda *a: None, disconnect=lambda *a: None))
        api, _ = game_source('gameface/hangar/vehicle_carousel.py', {
            'driftkings.gameface.hangar.common': module(HangarController=ControllerBase,
                install_card=lambda *a: None, card_payload=None, publish_card=None),
            'driftkings.interface_catalog': module(gameface_spec=lambda name: {'resource': 'mods/driftkings/vehicle_carousel/model'}),
            'driftkings.settings.service': module(settings_service=service, affects=None),
            'gui.shared.personality': module(ServicesLocator=module(itemsCache=module(onSyncCompleted=event))),
        })
        cache = {123: {'battles': 18}}
        api['_component'] = lambda: module(g_data=module(invalidate=cache.clear))
        controller = api['CarouselController']()
        controller.start()
        event.fire()  # No hangar view exists while returning from battle.
        self.assertEqual(cache, {})
        cache[123] = {'battles': 19}
        refreshed = []
        controller.views['hangar'] = module(refresh=lambda: refreshed.append(dict(cache)))
        event.fire()
        self.assertEqual(refreshed, [{}])  # Invalidate before publishing cards/sort values.
        controller.stop()
        self.assertEqual(event.handlers, [])
