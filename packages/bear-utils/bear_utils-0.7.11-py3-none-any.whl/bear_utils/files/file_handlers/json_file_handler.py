import json
from pathlib import Path
from typing import Any, ClassVar

from ._base_file_handler import FileHandler


class JsonFileHandler(FileHandler):
    """Class for handling JSON files with read, write, and present methods"""

    valid_extensions: ClassVar[list[str]] = ["json"]

    @FileHandler.ValidateFileType
    def read_file(self, file_path: Path, **kwargs) -> dict[str, Any]:
        try:
            super().read_file(file_path)
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file, **kwargs)
        except Exception as e:
            raise ValueError(f"Error reading file: {e}")

    @FileHandler.ValidateFileType
    def write_file(self, file_path: Path, data: dict[str, Any] | str, **kwargs) -> None:
        try:
            super().write_file(file_path, data)
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(
                    data,
                    file,
                    indent=kwargs.pop("indent", 4),
                    **kwargs,
                )
        except Exception as e:
            raise ValueError(f"Error writing file: {e}")

    def present_file(self, data: dict[str, Any] | str, **kwargs) -> str:
        try:
            return json.dumps(
                data,
                indent=kwargs.pop("indent", 4),
                **kwargs,
            )
        except Exception as e:
            raise ValueError(f"Error presenting file: {e}")
