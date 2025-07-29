from pathlib import Path
from typing import Any, ClassVar

from ._base_file_handler import FileHandler


class TextFileHandler(FileHandler):
    """Class for handling .txt files with read, write, and present methods"""

    valid_extensions: ClassVar[list[str]] = ["txt"]

    @FileHandler.ValidateFileType
    def read_file(self, file_path: Path) -> str:
        try:
            super().read_file(file_path)
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        except Exception as e:
            raise ValueError(f"Error reading file: {e}")

    @FileHandler.ValidateFileType
    def write_file(self, file_path: Path, data: dict[str, Any] | str, **kwargs) -> None:
        try:
            super().write_file(file_path, data)
            if not isinstance(data, str):
                raise ValueError("Data must be a string for text files")

            with open(file_path, "w", encoding="utf-8") as file:
                file.write(data)
        except Exception as e:
            raise ValueError(f"Error writing file: {e}")

    def present_file(self, data: dict[str, Any] | str, **kwargs) -> str:
        raise NotImplementedError("Presenting text files is not implemented. Not needed.")
