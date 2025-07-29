"""
Settings loader for Enlil framework.
"""
import os
import importlib

ENVIRONMENT_VARIABLE = "ENLIL_SETTINGS_MODULE"

class Settings:
    def __init__(self):
        self._settings_module = None

    def _setup(self):
        """Load settings module specified in ENLIL_SETTINGS_MODULE."""
        settings_module = os.environ.get(ENVIRONMENT_VARIABLE)
        if not settings_module:
            raise ImportError(
                "Settings cannot be imported because environment variable "
                f"{ENVIRONMENT_VARIABLE} is undefined."
            )

        try:
            self._settings_module = importlib.import_module(settings_module)
        except ImportError as e:
            raise ImportError(
                f"Could not import settings '{settings_module}': {e}"
            )

    def __getattr__(self, name):
        """Return the value of a setting."""
        if self._settings_module is None:
            self._setup()
        return getattr(self._settings_module, name)

settings = Settings()