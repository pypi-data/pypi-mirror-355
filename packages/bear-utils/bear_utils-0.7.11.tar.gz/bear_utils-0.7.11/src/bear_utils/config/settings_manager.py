import atexit
from argparse import Namespace
from contextlib import contextmanager
from pathlib import Path
from shelve import Shelf
from typing import Any

from singleton_base.singleton_base_new import SingletonBase


def get_bear_config_path() -> Path:
    """Get the path to the bear configuration path"""
    path = Path.home() / ".config" / "bear_utils"
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    return path


def get_config_file_path(filename: str) -> Path:
    """Get the path to a specific configuration file in the bear configuration path"""
    config_path = get_bear_config_path()
    return config_path / filename


class SettingsCache(Namespace):
    """A Namespace to hold settings in memory."""

    def __init__(self):
        super().__init__()

    def clear(self):
        """Clear the settings cache."""
        self.__dict__.clear()

    def set(self, key: str, value):
        """Set a value in the settings cache."""
        setattr(self, key, value)

    def get(self, key: str, default=None):
        """Get a value from the settings cache."""
        return getattr(self, key, default)

    def has(self, key: str) -> bool:
        """Check if a key exists in the settings cache."""
        return hasattr(self, key)


class SettingsManager:
    settings_name: str
    shelf: Shelf
    settings_cache: SettingsCache

    def __init__(self, settings_name: str):
        object.__setattr__(self, "settings_name", settings_name)
        object.__setattr__(self, "settings_cache", SettingsCache())
        object.__setattr__(self, "shelf", self._open())
        object.__setattr__(self, "_initialized", True)

        atexit.register(self.close)
        self._load_existing_settings()

    def __getattr__(self, key: str):
        """Handle dot notation access for settings."""
        if key.startswith("_"):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{key}'")
        return self.get(key)

    def __setattr__(self, key: str, value):
        """Handle dot notation assignment for settings."""
        if not hasattr(self, "_initialized"):
            object.__setattr__(self, key, value)
            return

        if key in ["settings_name", "settings_cache", "shelf"] or key.startswith("_"):
            raise AttributeError(f"Cannot modify '{key}' after initialization")

        self.set(key, value)

    def get(self, key: str, default=None):
        """Get a setting value by key with optional default."""
        try:
            if self.settings_cache.has(key):
                return self.settings_cache.get(key, default)
            elif self._shelf_has(key):
                return self.shelf[key]
            else:
                return default
        except Exception as e:
            return default

    def set(self, key: str, value):
        """Set a setting value by key."""
        self.shelf[key] = value
        self.settings_cache.set(key, value)

    def has(self, key: str) -> bool:
        """Check if a setting exists by key."""
        return self.settings_cache.has(key) or self._shelf_has(key)

    def _shelf_has(self, key: str) -> bool:
        """Check if a setting exists by key."""
        return key in self.shelf

    def open(self):
        object.__setattr__(self, "shelf", self._open())
        self._load_existing_settings()

    def _open(self) -> Shelf:
        """Open the settings file."""
        import shelve

        try:
            shelf: Shelf[Any] = shelve.open(get_config_file_path(self.settings_name))
            return shelf
        except Exception as e:
            raise RuntimeError(f"Warning: Could not open settings file '{self.settings_name}': {e}")

    def _load_existing_settings(self):
        """Load existing settings from shelf into namespace."""
        for key in self.shelf:
            if not self.settings_cache.has(key):
                self.settings_cache.set(key, self.shelf[key])

    def close(self):
        """Close the settings file."""
        if self.shelf is not None:
            self.shelf.close()
        if self.settings_cache is not None:
            self.settings_cache.clear()

    def destroy_settings(self) -> bool:
        """Delete the settings file, a bit nuclear and will require calling open() again."""
        file_path = get_config_file_path(self.settings_name)
        if file_path.exists():
            self.close()
            file_path.unlink()
            self.settings_cache.clear()
            object.__setattr__(self, "shelf", None)
            return True
        return False

    def __del__(self):
        """Destructor to ensure the shelf is closed."""
        self.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __contains__(self, key: str) -> bool:
        """Check if a setting exists."""
        return self.has(key)

    def keys(self) -> list[str]:
        """Get all setting keys."""
        return list(vars(self.settings_cache).keys())

    def items(self):
        """Get all setting key-value pairs."""
        for key in self.keys():
            yield key, self.settings_cache.get(key)

    def values(self):
        """Get all setting values."""
        for key in self.keys():
            yield self.settings_cache.get(key)

    def __repr__(self):
        """String representation of the SettingsManager."""
        return f"<SettingsManager settings_name='{self.settings_name}'>"

    def __str__(self):
        """String representation of the SettingsManager."""
        return f"SettingsManager for '{self.settings_name}' with {len(self.keys())} settings."

    def __len__(self):
        """Get the number of settings."""
        return len(self.keys())


class SettingsSupervisor(SingletonBase):
    def __init__(self):
        self._settings_managers = {}

    def _get_instance(self, settings_name: str) -> SettingsManager:
        """Get or create a SettingsManager instance."""
        if settings_name in self._settings_managers:
            return self._settings_managers[settings_name]
        return SettingsManager(settings_name)


def get_settings_manager(settings_name: str) -> SettingsManager:
    """Get the SettingsManager instance for a given settings name."""
    supervisor: SettingsSupervisor = SettingsSupervisor.get_instance(init=True)
    return supervisor._get_instance(settings_name)


@contextmanager
def settings(settings_name: str):
    """Context manager for SettingsManager."""
    sm: SettingsManager = get_settings_manager(settings_name)
    try:
        yield sm
    finally:
        sm.close()


__all__: list[str] = ["SettingsManager", "settings", "get_settings_manager"]

# if __name__ == "__main__":
#     with settings("example_settings") as sm:
#         sm.sample_setting = "This is a sample setting"
#         print(sm.sample_setting)
#         print(sm.keys())
#         for key, value in sm.items():
#             print("This is items()")
#             print(f"Key: {key}, Value: {value}")
#         for value in sm.values():
#             print("This is values()")
#             print(value)
#         print(len(sm))
#         print(sm)
#         if sm.destroy_settings():
#             print("Settings destroyed successfully.")
#         sm.open()
#         print(sm.keys())
#         sm.test = "Test setting"
#         print(len(sm))
