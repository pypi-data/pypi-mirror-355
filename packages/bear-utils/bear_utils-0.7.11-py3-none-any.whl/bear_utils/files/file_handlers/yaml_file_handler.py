from pathlib import Path
from typing import Any, ClassVar

import yaml

from ._base_file_handler import FileHandler


class YamlFileHandler(FileHandler):
    """Class for handling .yaml/.yml files with read, write, and present methods"""

    valid_extensions: ClassVar[list[str]] = ["yaml", "yml"]

    @FileHandler.ValidateFileType
    def unsafe_read_file(self, file_path: Path, **kwargs) -> dict[str, Any]:
        """Read YAML file with potentially unsafe loader.

        WARNING: This method can execute arbitrary code and should only be used
        with trusted files.

        Args:
            file_path: Path to the YAML file
            **kwargs: Additional arguments passed to yaml.load

        Returns:
            Dictionary containing the parsed YAML data
        """
        try:
            super().read_file(file_path)
            with open(file_path, "r", encoding="utf-8") as file:
                return yaml.load(file, **kwargs)
        except Exception as e:
            raise ValueError(f"Error reading file: {e}")

    @FileHandler.ValidateFileType
    def read_file(self, file_path: Path) -> dict[str, Any]:
        try:
            super().read_file(file_path)
            with open(file_path, "r", encoding="utf-8") as file:
                return yaml.safe_load(file)
        except Exception as e:
            raise ValueError(f"Error reading file: {e}")

    @FileHandler.ValidateFileType
    def write_file(self, file_path: Path, data: dict[str, Any] | str, **kwargs) -> None:
        try:
            super().write_file(file_path, data)
            with open(file_path, "w", encoding="utf-8") as file:
                yaml.dump(data, file, default_flow_style=False, sort_keys=False, **kwargs)
        except Exception as e:
            raise ValueError(f"Error writing file: {e}")

    def present_file(self, data: dict[str, Any] | str, **kwargs) -> str:
        try:
            return yaml.dump(data, default_flow_style=False, sort_keys=False, **kwargs)
        except Exception as e:
            raise ValueError(f"Error presenting file: {e}")
