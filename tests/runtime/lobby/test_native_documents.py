# -*- coding: utf-8 -*-
"""The existing context-owned views publish native models without importing OpenWG."""
from support import RuntimeTest, module, source
from test_native_clock import Model


class NativeDocumentModelsTests(RuntimeTest):
    def test_twenty_native_models_keep_payload_identity_and_commands_without_openwg(self):
        catalog = self.load('interface_catalog')
        imports, injections = [], []

        class NativeModel(Model):
            def __init__(self, properties=0, commands=0):
                self.commands, self.names = commands, []
                super(NativeModel, self).__init__(properties=properties, commands=commands)

            def _addCommand(self, name):
                self.names.append(name)
                return super(NativeModel, self)._addCommand(name)

        class Dependencies(dict):
            def __contains__(self, name):
                imports.append(name)
                return super(Dependencies, self).__contains__(name)

        dependencies = Dependencies({
            'frameworks.wulf': module(ViewModel=NativeModel), 'gui.impl.gen': module(R=None),
            'driftkings.interface_catalog': catalog,
            'openwg_gameface': module(gf_mod_inject=lambda *a, **k: injections.append(a))})
        core = source('gameface/core.py', dependencies)
        self.assertNotIn('openwg_gameface', imports)
        own = source('gameface/battle/own_window.py', {
            'frameworks.wulf': module(ViewModel=NativeModel),
            'driftkings.gameface.core': module(**core)})
        names = [name for name, spec in catalog.GAMEFACE.items() if spec['owner'] is not None]
        self.assertEqual(len(names), 20)
        classes = []
        for name in names:
            commands = (('onOpen',) if name == 'DriftkingsFooterLauncher' else
                        ('onPerformance',) if name == 'DriftkingsRatingPlayers' else ())
            transport = catalog.GAMEFACE[name]['transport']
            factory = own['payload_model'] if transport == 'own_window' else (
                core['payload_model'] if transport == 'native_document' else core['native_payload_model'])
            model_type = factory(name, commands)
            classes.append(model_type)
            model = model_type()
            self.assertEqual((model.properties, model.commands), (2, len(commands)))
            self.assertEqual(model.fields['payload'], '{}')
            self.assertEqual(model.fields['DriftkingsUI'].fields, {'name': name})
            self.assertEqual(model.names, list(commands))
        self.assertEqual(injections, [])
        self.assertNotIn('openwg_gameface', imports)
        self.assertEqual(len(set(classes)), 20)
