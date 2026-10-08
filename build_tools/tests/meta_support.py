"""Run real meta class bodies with only native dependencies substituted."""
import ast
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]


class NativeComponent:
    def __init__(self):
        self.ready = True
        self.disposals = 0

    def create(self):
        self._populate()

    def _populate(self):
        pass

    def _dispose(self):
        self.disposals += 1
        self.ready = False

    def _isDAAPIInited(self):
        return self.ready


def meta_namespace(visibility=None):
    from Driftkings.settings.service import settings_service
    namespace = {'BaseDAAPIComponent': NativeComponent,
                 'settings_service': settings_service,
                 'dependency': NS(descriptor=lambda _: None),
                 'IBattleSessionProvider': object, 'ISettingsCore': object,
                 'hudVisibility': visibility if visibility is not None else Mock()}
    folder = ROOT / 'source/scripts/client/Driftkings/meta/battle'
    paths = [folder/'base.py'] + sorted(path for path in folder.glob('*.py') if path.name != 'base.py')
    for path in paths:
        tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        tree.body = [node for node in tree.body if isinstance(node, ast.ClassDef)]
        exec(compile(tree, str(path), 'exec'), namespace)
    return namespace
