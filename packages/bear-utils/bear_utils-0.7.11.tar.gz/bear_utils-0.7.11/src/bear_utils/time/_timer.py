from collections.abc import Callable
from contextlib import contextmanager
from functools import wraps

from ..logging import ConsoleLogger
from ._time_class import EpochTimestamp


def create_timer(**defaults):
    """A way to set defaults for a frequently used timer decorator."""

    def timer_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            defaults["name"] = func.__name__
            with timer(**defaults):
                return func(*args, **kwargs)

        return wrapper

    return timer_decorator


@contextmanager
def timer(**kwargs):
    data: TimerData = kwargs.get("data", None) or TimerData(kwargs=kwargs)
    data.start()
    try:
        yield data
    finally:
        data.stop()


class TimerData:
    def __init__(self, **kwargs):
        self.name: str = kwargs.get("name", "Default Timer")
        self.start_time: EpochTimestamp = EpochTimestamp(0)
        self.end_time: EpochTimestamp = EpochTimestamp(0)
        self._raw_elapsed_time: EpochTimestamp = EpochTimestamp(0)
        self.console: ConsoleLogger | None = self.get_console(kwargs.get("output", False))
        self.callback: Callable | None = kwargs.get("callback", None)
        self._style: str = kwargs.get("style", "bold green")

    def get_console(self, to_console: bool) -> ConsoleLogger | None:
        if to_console:
            try:
                console = ConsoleLogger.get_instance()  # will crash if nothing else has initialized ConsoleLogger
            except RuntimeError:
                console = ConsoleLogger()
            return console

    def start(self):
        self.start_time = EpochTimestamp.now()

    def send_callback(self):
        if self.callback is not None:
            self.callback(self)

    def stop(self):
        self.end_time = EpochTimestamp.now()
        self._raw_elapsed_time = EpochTimestamp(self.end_time - self.start_time)
        if self.callback:
            self.send_callback()
        if self.console:
            self.console.print(f"[{self.name}] Elapsed time: {self.elapsed_seconds:.2f} seconds", style=self._style)

    @property
    def elapsed_milliseconds(self) -> int:
        if self._raw_elapsed_time:
            return self._raw_elapsed_time.to_milliseconds
        return -1

    @property
    def elapsed_seconds(self) -> int:
        if self._raw_elapsed_time:
            return self._raw_elapsed_time.to_seconds
        return -1


__all__ = ["TimerData"]
