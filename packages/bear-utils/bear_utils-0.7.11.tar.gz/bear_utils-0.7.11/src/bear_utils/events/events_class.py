from collections.abc import Callable
from typing import Any

from .events_module import clear_all as _clear_all
from .events_module import clear_handlers_for_event as _clear_handlers_for_event
from .events_module import dispatch_event as _dispatch_event
from .events_module import event_handler as _event_handler
from .events_module import set_handler as _set_handler

Callback = Callable[..., Any]


class Events:
    """Simple wrapper exposing :mod:`events_module` functionality as methods."""

    # Method names mirror functions from ``events_module`` for familiarity

    def event_handler(self, event_name: str, func: Callback | None = None):
        """Register ``func`` as a handler for ``event_name``.

        Can be used as a decorator when ``func`` is omitted."""

        if func is None:
            return _event_handler(event_name)
        _set_handler(event_name, func)
        return func

    def dispatch_event(self, event_name: str, *args, **kwargs) -> Any | None:
        """Dispatch ``event_name`` to all subscribed handlers."""

        return _dispatch_event(event_name, *args, **kwargs)

    def set_handler(self, event_name: str, func: Callback) -> None:
        """Register ``func`` as a handler for ``event_name``."""

        _set_handler(event_name, func)

    def clear_handlers_for_event(self, event_name: str) -> None:
        """Remove all handlers associated with ``event_name``."""

        _clear_handlers_for_event(event_name)

    def clear_all(self) -> None:
        """Remove all registered event handlers."""

        _clear_all()

    subscribe = event_handler
    publish = dispatch_event


__all__ = ["Events"]
