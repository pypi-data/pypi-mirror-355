import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

ConfigType = TypeVar("ConfigType", bound=BaseModel)

# TODO: Get around to potentially using this, right now it is just masturbation


class ConfigManager(Generic[ConfigType]):
    def __init__(self, config_model: type[ConfigType], config_path: Path | None = None, env: str = "dev") -> None:
        self._model = config_model
        self._config_path = config_path or Path("config")
        self._env = env
        self._config: ConfigType | None = None

    def _get_env_overrides(self) -> dict[str, Any]:
        """Convert environment variables to nested dictionary structure."""
        env_config: dict[str, Any] = {}

        for key, value in os.environ.items():
            if not key.startswith("APP_"):
                continue

            # Convert APP_DATABASE_HOST to ['database', 'host']
            parts = key.lower().replace("app_", "").split("_")

            # Build nested dictionary
            current = env_config
            for part in parts[:-1]:
                current = current.setdefault(part, {})
            current[parts[-1]] = value

        return env_config

    @lru_cache
    def load(self) -> ConfigType:
        # Load order (later overrides earlier):
        # 1. default.yaml
        # 2. {env}.yaml
        # 3. local.yaml (gitignored)
        # 4. environment variables
        config_data: dict[str, Any] = {}

        # for config_file in [
        #     self._config_path / "default.yaml",
        #     self._config_path / f"{self._env}.yaml",
        #     self._config_path / "local.yaml",
        # ]:
        #     if config_file.exists():
        #         with open(config_file) as f:
        #             config_data.update(yaml.safe_load(f))

        config_data.update(self._get_env_overrides())

        return self._model.model_validate(config_data)

    @property
    def config(self) -> ConfigType:
        if self._config is None:
            self._config = self.load()
        return self._config


# Example usage:
# class DatabaseConfig(BaseModel):
#     host: str
#     port: int
#     username: str
#     password: str
#     database: str


# class AppConfig(BaseModel):
#     database: DatabaseConfig
#     environment: str
#     debug: bool = False
#     logging_mode: str = "console"
#     log_level: str = "INFO"


# config_manager = ConfigManager[AppConfig](
#     config_model=AppConfig,
#     config_path=Path("config"),
#     env="development",
# )

# Access config
# db_config = config_manager.config.database
