"""Pure build/contract tests. No game process, network, Inno or Windows required."""
import builtins
import copy
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import types
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools.build_installer import definitions, generate_components, partial_choices, prepare_payload, supported_realms, attach_installer
from build_tools.generate_ui_catalog import installer_catalog
from build_tools.modpack import create as create_modpack
from build_tools.validate_build_data import build_plan, client_realm


from support.build_assets import png


class GeneratorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for relative in ('res/configs/driftkings', 'installer/setup'):
            shutil.copytree(ROOT / relative, self.root / relative,
                            ignore=shutil.ignore_patterns('*.png', '*.bmp', '*.ico') if relative == 'installer/setup' else None)
        for relative in ('build_data/build_config.json', 'build_data/components.json',
                         'mod/res/scripts/client/driftkings/_constants.py',
                         'mod/res/mods/driftkings/text/en.yml', 'mod/res/mods/driftkings/text/pt.yml'):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, path)

    def test_installer_attachment_updates_release_inventory_and_checksums(self):
        folder = self.root / 'release'
        folder.mkdir()
        manifest = {'version': '1.0.0-beta.1', 'gameVersion': '2.4.1.0'}
        (folder / 'release.json').write_text(json.dumps(manifest))
        report = dict(status='success', mode='release', publishable=True, version=manifest['version'],
                      gameVersion=manifest['gameVersion'], artifacts={'release.json': {}})
        (folder / 'build-report.json').write_text(json.dumps(report))
        installer = self.root / 'Driftkings-1.0.0-beta.1-WoT-2.4.1.0-Setup.exe'
        installer.write_bytes(b'MZtest installer')
        attached = attach_installer(folder, installer)
        report = json.loads((folder / 'build-report.json').read_text())
        self.assertEqual(report['artifacts'][installer.name]['sha256'], hashlib.sha256(attached.read_bytes()).hexdigest())
        sums = (folder / 'SHA256SUMS.txt').read_text().splitlines()
        self.assertEqual(len(sums), 3)
        for line in sums:
            checksum, name = line.split('  ', 1)
            self.assertEqual(checksum, hashlib.sha256((folder / name).read_bytes()).hexdigest())
        with self.assertRaisesRegex(ValueError, 'filename'):
            attach_installer(folder, folder / 'wrong.exe')

    def test_every_top_level_enabled_has_translated_labels_group_and_real_path(self):
        choices = installer_catalog(self.root)
        expected = {path.stem for path in (self.root / 'res/configs/driftkings/default').glob('*.json')
                    if 'enabled' in json.loads(path.read_text())}
        self.assertEqual({entry['key'] for entry in choices}, expected)
        self.assertNotIn('sound_bank_loader', expected)
        for entry in choices:
            self.assertTrue((self.root / 'res/configs/driftkings' / entry['file']).is_file())
            for lang in ('en', 'pt'):
                self.assertTrue(entry['labels'][lang])
                self.assertTrue(entry['descriptions'][lang])
                self.assertTrue(entry['group_labels'][lang])

    def test_missing_label_fails_instead_of_using_internal_name(self):
        path = self.root / 'mod/res/mods/driftkings/text/pt.yml'
        text = path.read_text(encoding='utf-8')
        # Remove the actual first description; leave a valid catalog document.
        import re
        text, count = re.subn(r'(^[a-z_]+\.UI_description: )[^\n]+', r'\1""', text, count=1, flags=re.M)
        self.assertEqual(count, 1)
        path.write_text(text, encoding='utf-8')
        # The first section may not be an enabled choice, so remove all descriptions.
        text = re.sub(r'(^[a-z_]+\.UI_description: )[^\n]+', r'\1""', text, flags=re.M)
        path.write_text(text, encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Missing installer label'):
            installer_catalog(self.root)

    def test_generated_pascal_names_match_real_json_and_choices_are_not_payload_conditions(self):
        out = self.root / 'generated'
        components, options, presets = generate_components(self.root, out)
        script = (out / 'components.generated.iss').read_text(encoding='utf-8-sig')
        self.assertEqual(len(presets), 0)
        self.assertEqual([(entry['component'], entry['key']) for entry in options], [('sixth_sense_alert', 'userSound')])
        for entry in components:
            self.assertIn('Name: "' + entry['group'] + '\\' + entry['key'] + '"', script)
            self.assertIn("'" + entry['file'].replace('/', '\\') + "'", script)
        self.assertIn('function ChoiceSelected', script)
        self.assertIn('WizardIsTaskSelected', script)
        self.assertNotIn('Source:', script)
        self.assertNotIn('Source:', (out / 'previews.generated.iss').read_text(encoding='utf-8-sig'))
        first = (out / 'components.generated.iss').read_bytes()
        generate_components(self.root, out)
        self.assertEqual((out / 'components.generated.iss').read_bytes(), first)

    def test_recommended_and_two_disabled_choices_only_generate_minimal_differences(self):
        components, options, _ = definitions(self.root)
        selected = {entry['key'] for entry in components if entry['default']}
        extras = {entry['component'] + '_' + entry['key'] for entry in options if entry['default']}
        self.assertEqual(partial_choices(components, options, selected, extras), {})
        selected.difference_update(('clan_reward_collection', 'game_log_manager'))
        self.assertEqual(partial_choices(components, options, selected, extras), {
            'default/clan_reward_collection.json': {'enabled': False}, 'default/game_log_manager.json': {'enabled': False}})
        selected.add('sixth_sense_alert')
        documents = partial_choices(components, options, selected, set())
        self.assertEqual(documents['default/sixth_sense_alert.json'], {'userSound': False})

    def test_optional_preview_and_branding_are_detected_without_a_second_component_list(self):
        preview = self.root / 'installer/setup/assets/previews/clan_reward_collection.png'
        preview.write_bytes(png())
        branding = self.root / 'installer/setup/assets/branding/wizard-large.png'
        branding.write_bytes(png())
        out = self.root / 'generated'
        generate_components(self.root, out)
        self.assertIn('preview_clan_reward_collection.png', (out / 'previews.generated.iss').read_text(encoding='utf-8-sig'))
        self.assertIn('WizardImageFile=', (out / 'branding.generated.iss').read_text(encoding='utf-8-sig'))
        self.assertNotIn('SetupIconFile=', (out / 'branding.generated.iss').read_text(encoding='utf-8-sig'))

    def test_declarative_options_and_presets_reject_unknown_or_non_boolean_keys(self):
        path = self.root / 'installer/setup/options.json'
        value = json.loads(path.read_text())
        value['options'][0]['key'] = 'sixthSenseSound'
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, 'not a boolean'):
            definitions(self.root)
        value['options'][0]['key'] = 'userSound'
        path.write_text(json.dumps(value))
        path = self.root / 'installer/setup/presets.json'
        path.write_text(json.dumps({'presets': [{'key': 'owner_choice', 'labels': {'en': 'Owner choice', 'pt': 'Escolha do autor'},
                                                'disabled': ['clan_reward_collection']}]}))
        components, options, presets = generate_components(self.root, self.root / 'generated')
        self.assertEqual(presets[0]['disabled'], ['clan_reward_collection'])
        script = (self.root / 'generated/components.generated.iss').read_text(encoding='utf-8-sig')
        line = next(line for line in script.splitlines() if 'Name: "hangar\\clan_reward_collection"' in line)
        self.assertNotIn('owner_choice', line)
        path.write_text(json.dumps({'presets': [{'key': 'bad', 'labels': {'en': 'Bad', 'pt': 'InvÃ¡lido'}, 'disabled': ['unknown']}]}))
        with self.assertRaisesRegex(ValueError, 'Unknown or duplicate disabled'):
            definitions(self.root)

    def test_missing_artifacts_never_produce_a_payload(self):
        out = self.root / 'generated'
        out.mkdir()
        with self.assertRaises(OSError):
            prepare_payload(self.root, self.root / 'missing', out)
        self.assertFalse((out / 'payload.generated.iss').exists())

    def test_payload_is_verified_fixed_and_independent_of_presets(self):
        artifacts = self.root / 'artifacts'
        artifacts.mkdir()
        (artifacts / 'dependencies').mkdir()
        config = json.loads((self.root / 'build_data/build_config.json').read_text())
        game = config['game']['version']
        version = '1.0.0'
        names = ('driftkings.wotmod', 'first.wotmod', 'second.wotmod')
        defaults = io.BytesIO()
        with zipfile.ZipFile(defaults, 'w') as archive:
            archive.writestr('mods/configs/driftkings/default/example.json', b'{}')
        distribution = artifacts / ('Driftkings-%s-WoT-%s.zip' % (version, game))
        with zipfile.ZipFile(distribution, 'w') as archive:
            for name in names:
                data = name.encode('ascii')
                source = artifacts / ('' if name == names[0] else 'dependencies') / name
                source.write_bytes(data)
                archive.writestr('mods/' + game + '/' + name, data)
            archive.writestr('INSTALL.txt', b'instructions')
            archive.writestr('Driftkings-defaults.zip', defaults.getvalue())
        modpack = create_modpack(artifacts, version, 'stable', game, {'mods/configs/driftkings/default/example.json': b'{}'})
        code = (artifacts / names[0]).read_bytes()
        manifest = dict(version=version, channel='stable', gameVersion=game, size=len(code), sha256=hashlib.sha256(code).hexdigest(),
                        schema=2, modpack=modpack)
        (artifacts / 'release.json').write_text(json.dumps(manifest))
        (artifacts / 'modpack.json').write_text(json.dumps(modpack))
        inputs = {path.relative_to(self.root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in (self.root / 'res/configs/driftkings').rglob('*.json')}
        (artifacts / 'build-report.json').write_text(json.dumps(dict(status='success', version=version, realm='EU', inputs=inputs)))
        out = self.root / 'generated'
        generate_components(self.root, out)
        prepare_payload(self.root, artifacts, out)
        payload = (out / 'payload.generated.iss').read_bytes()
        script = payload.decode('utf-8-sig')
        metadata = (out / 'metadata.generated.iss').read_text(encoding='utf-8-sig')
        self.assertIn('#define SupportedRealms "|EU|NA|ASIA|"', metadata)
        self.assertIn('#define SupportedRealmsText "EU, NA, ASIA"', metadata)
        self.assertEqual(script.count('Source:'), 3)
        self.assertNotIn('Components:', script)
        self.assertNotIn('Tasks:', script)
        self.assertIn('onlyifdoesntexist', script)
        self.assertIn('ExistingDependenciesError', script)
        self.assertIn('VerifyInstalledPayload', script)
        self.assertNotIn('.bnk', script)
        (self.root / 'installer/setup/presets.json').write_text(json.dumps({'presets': [{
            'key': 'owner_choice', 'labels': {'en': 'Owner', 'pt': 'Autor'}, 'disabled': ['clan_reward_collection']}]}))
        generate_components(self.root, out)
        prepare_payload(self.root, artifacts, out)
        self.assertEqual((out / 'payload.generated.iss').read_bytes(), payload)
        (artifacts / 'dependencies/first.wotmod').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'Invalid installer payload'):
            prepare_payload(self.root, artifacts, out)

    def test_supported_realms_are_validated(self):
        config = json.loads((self.root / 'build_data/build_config.json').read_text())
        self.assertEqual(supported_realms(config), ['EU', 'NA', 'ASIA'])
        for invalid in (None, [], ['NA', 'NA'], ['na'], ['NA', 1]):
            config['game']['supported_realms'] = invalid
            with self.assertRaisesRegex(ValueError, 'Invalid supported_realms'):
                supported_realms(config)

    def test_any_supported_client_realm_can_build(self):
        config = json.loads((self.root / 'build_data/build_config.json').read_text())
        self.assertEqual([client_realm(text, config) for text in ('EU', ' na ', 'ASIA', 'SEA')], ['EU', 'NA', 'ASIA', 'ASIA'])
        for text in ('RU', '', None):
            with self.assertRaisesRegex(ValueError, 'Unsupported game realm'):
                client_realm(text, config)

    def test_build_contract_keeps_machine_paths_local(self):
        config = json.loads((ROOT / 'build_data/build_config.json').read_text())
        self.assertNotIn('root', config['game'])
        self.assertNotIn('realm', config['game'])
        self.assertNotIn('root', config['reference'])
        self.assertNotIn('source_root', json.loads((ROOT / 'build_data/defaults_snapshot.json').read_text()))
        config['game']['root'] = 'C:/Games/World_of_Tanks'
        (self.root / 'build_data/build_config.json').write_text(json.dumps(config))
        with self.assertRaisesRegex(ValueError, 'toolchain.local.json'):
            build_plan(self.root)

    def test_runtime_loader_merges_partial_file_without_rewriting_it(self):
        client = ROOT / 'mod/res/scripts/client/driftkings'
        def load(relative, dependencies=None):
            dependencies = dict(dependencies or {})
            if 'driftkings.common.utils.compat' not in dependencies and relative != 'common/utils/compat.py':
                dependencies['driftkings.common.utils.compat'] = load('common/utils/compat.py')
            def importing(name, globals=None, locals=None, fromlist=(), level=0):
                return dependencies[name] if name in dependencies else builtins.__import__(name, globals, locals, fromlist, level)
            namespace = {'__name__': '_installer_test', '__builtins__': dict(vars(builtins), __import__=importing)}
            eval(compile((client / relative).read_bytes(), str(client / relative), 'exec'), namespace)
            return types.SimpleNamespace(**{key: value for key, value in namespace.items() if not key.startswith('__')})
        filesystem = load('common/utils/filesystem.py')
        store = load('settings/store.py', {'driftkings.common.utils.filesystem': filesystem})
        sections = load('settings/sections.py', {'driftkings._constants': load('_constants.py')})
        loader = load('settings/loader.py', {
            'driftkings.logger': load('logger.py'),
            'driftkings.settings.settings_data': types.SimpleNamespace(SettingsData=object, user_settings={}, part_name=lambda value: value),
            'driftkings.settings.default_values': types.SimpleNamespace(SELECTOR={'loadConfig': 'default'}),
            'driftkings.settings.sections': sections, 'driftkings.settings.store': store})
        folder = self.root / 'profile'
        (folder / 'default').mkdir(parents=True)
        path = folder / 'default/clan_reward_collection.json'
        original = b'{"enabled": false}'
        path.write_bytes(original)
        (folder / 'load.json').write_text('{"loadConfig":"default"}')
        defaults = json.loads((ROOT / 'res/configs/driftkings/default/clan_reward_collection.json').read_text())
        value = loader.SettingsLoader(str(folder), settings=object()).load('clan_reward_collection', defaults)
        expected = copy.deepcopy(defaults)
        expected['enabled'] = False
        self.assertEqual(value, expected)
        self.assertEqual(path.read_bytes(), original)

    def test_runtime_loader_ignores_and_preserves_old_settings(self):
        client = ROOT / 'mod/res/scripts/client/driftkings'
        def load(relative, dependencies=None):
            dependencies = dict(dependencies or {})
            if 'driftkings.common.utils.compat' not in dependencies and relative != 'common/utils/compat.py':
                dependencies['driftkings.common.utils.compat'] = load('common/utils/compat.py')
            def importing(name, globals=None, locals=None, fromlist=(), level=0):
                return dependencies[name] if name in dependencies else builtins.__import__(name, globals, locals, fromlist, level)
            namespace = {'__name__': '_installer_test', '__builtins__': dict(vars(builtins), __import__=importing)}
            eval(compile((client / relative).read_bytes(), str(client / relative), 'exec'), namespace)
            return types.SimpleNamespace(**{key: value for key, value in namespace.items() if not key.startswith('__')})
        filesystem = load('common/utils/filesystem.py')
        store = load('settings/store.py', {'driftkings.common.utils.filesystem': filesystem})
        sections = load('settings/sections.py', {'driftkings._constants': load('_constants.py')})
        loader = load('settings/loader.py', {
            'driftkings.logger': load('logger.py'),
            'driftkings.settings.settings_data': types.SimpleNamespace(SettingsData=object, user_settings={}, part_name=lambda value: value),
            'driftkings.settings.default_values': types.SimpleNamespace(SELECTOR={'loadConfig': 'default'}),
            'driftkings.settings.sections': sections, 'driftkings.settings.store': store})
        folder = self.root / 'migration'
        profile = folder / 'default'
        profile.mkdir(parents=True)
        (folder / 'load.json').write_text('{"loadConfig":"default"}')
        (profile / 'auto_claim_clan.json').write_text('{"enabled": false}')
        (profile / 'safe_shot.json').write_text('{}')
        (profile / 'own_notes.json').write_text('{}')
        kept = profile / 'carousel_stats'
        kept.mkdir()
        (kept / 'carousel.json').write_text('{}')
        (kept / 'readme.txt').write_text('user file')
        defaults = json.loads((ROOT / 'res/configs/driftkings/default/clan_reward_collection.json').read_text())
        settings = loader.SettingsLoader(str(folder), settings=object())
        value = settings.load('clan_reward_collection', defaults)
        self.assertEqual(value, defaults)
        self.assertTrue((profile / 'clan_reward_collection.json').is_file())
        self.assertTrue((profile / 'auto_claim_clan.json').is_file())
        self.assertTrue((profile / 'safe_shot.json').is_file())
        self.assertTrue((profile / 'own_notes.json').is_file())
        self.assertTrue((kept / 'readme.txt').is_file())

