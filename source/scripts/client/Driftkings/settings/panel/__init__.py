from Driftkings import VERSION

from Driftkings.settings.panel.api import SettingsAPI  # noqa: E402
from Driftkings.settings.panel.controls import DefinitionError  # noqa: E402
from Driftkings.settings.panel.registry import DuplicateModError, UnknownModError  # noqa: E402

settings = SettingsAPI()

__all__ = ('settings', 'VERSION', 'DefinitionError', 'DuplicateModError', 'UnknownModError')
