from driftkings import VERSION
from driftkings.settings.panel.api import SettingsAPI  # noqa: E402
from driftkings.settings.panel.controls import DefinitionError  # noqa: E402
from driftkings.settings.panel.registry import DuplicateModError, UnknownModError  # noqa: E402

settings = SettingsAPI()

__all__ = ('settings', 'VERSION', 'DefinitionError', 'DuplicateModError', 'UnknownModError')
