import threading
from logging import addLevelName
from typing import Literal

ERROR: Literal[40] = 40
WARNING: Literal[30] = 30
WARN: Literal[30] = WARNING
INFO: Literal[20] = 20
DEBUG: Literal[10] = 10
NOTSET: Literal[0] = 0

_levelToName = {
    ERROR: "ERROR",
    WARNING: "WARNING",
    INFO: "INFO",
    DEBUG: "DEBUG",
    NOTSET: "NOTSET",
}
_nameToLevel = {
    "ERROR": ERROR,
    "WARN": WARNING,
    "WARNING": WARNING,
    "INFO": INFO,
    "DEBUG": DEBUG,
    "NOTSET": NOTSET,
}

_lock = threading.RLock()


def lvl_exists(level: int | str) -> bool:
    """Check if a logging level already exists."""
    with _lock:
        level = check_level(level, fail=False)
        return level in _levelToName


def add_level_name(level: int, name: str) -> None:
    """Add a custom logging level name."""
    with _lock:
        if level in _levelToName:
            raise ValueError(f"Level {level} already exists with name {_levelToName[level]}")
        _levelToName[level] = name.upper()
        _nameToLevel[name.upper()] = level
        addLevelName(level, name)


def check_level(level: int | str, fail: bool = True) -> int:
    """Validate and normalize logging level to integer."""
    if isinstance(level, str) and level.upper() in _nameToLevel:
        return _nameToLevel[level.upper()]
    if isinstance(level, int) and level in _levelToName:
        return level
    if fail:
        if not isinstance(level, (int, str)):
            raise TypeError(f"Level must be int or str, got {type(level).__name__}: {level!r}")
        raise ValueError(f"Invalid logging level: {level!r}. Valid levels are: {list(_nameToLevel.keys())}")
    return 999  # Return a high value to indicate invalid level
