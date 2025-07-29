"""
Logger adapter module that provides an alternative to SubLogger using standard library tools.

This implementation shows how to use LoggerAdapter and contextvars to maintain
all the functionality of the existing SubLogger while reducing complexity.
"""

from typing import Any, Generic, TypeVar

from ._base_logger import BaseLogger

T = TypeVar("T", bound=BaseLogger)

class SubConsoleLogger(Generic[T]):
    """
    Enhanced logger adapter that supports style-based logging and namespace prefixing.

    This class provides an alternative to the SubLogger implementation while
    maintaining compatibility with the existing ConsoleLogger.
    """

    logger: T
    _level: int
    namespace: str
    extra: dict[str, Any] | None
    log_level: int
    # fmt: off
    def __init__(self, logger: T, namespace: str, **kwargs) -> None: ...
    def set_sub_level(self, level: int) -> None: ...
    def success(self, msg: object, *args, **kwargs) -> None: ...
    def failure(self, msg: object, *args, **kwargs) -> None: ...
    def verbose(self, msg: object, *args, **kwargs) -> None: ...
    def info(self, msg: object, *args, **kwargs) -> None: ...
    def debug(self, msg: object, *args, **kwargs) -> None: ...
    def warning(self, msg: object, *args, **kwargs) -> None: ...
    def error(self, msg: object, *args, **kwargs) -> None: ...
    def print(self, msg: object, end: str = "\n", exc_info: Any = None, extra: dict | None = None, *args, **kwargs: Any) -> None | str: ...
    def __repr__(self) -> str: ...
