import asyncio
import weakref
from collections import defaultdict
from collections.abc import Callable
from functools import wraps
from types import MethodType
from typing import Any, TypeAlias
from weakref import WeakMethod, ref

from ..extras._async_helpers import is_async_function

Callback: TypeAlias = Callable[..., Any]

_event_registry: dict[str, weakref.WeakSet[Callback]] = defaultdict(weakref.WeakSet)


def clear_handlers_for_event(event_name: str) -> None:
    _event_registry.pop(event_name, None)


def clear_all() -> None:
    _event_registry.clear()


def _make_callback(name: str) -> Callable[[Any], None]:
    """Create an internal callback to remove dead handlers."""

    def callback(weak_method: Any) -> None:
        _event_registry[name].remove(weak_method)
        if not _event_registry[name]:
            del _event_registry[name]

    return callback


def set_handler(name: str, func: Callback) -> None:
    if isinstance(func, MethodType):
        _event_registry[name].add(WeakMethod(func, _make_callback(name)))
    else:
        _event_registry[name].add(ref(func, _make_callback(name)))


def dispatch_event(name: str, *args, **kwargs) -> Any | None:
    results = list()
    for func in _event_registry.get(name, []):
        if is_async_function(func):
            result = asyncio.run(func(*args, **kwargs))
        else:
            result = func(*args, **kwargs)
            results.append(result)
    if not results:
        return None
    return results[0] if len(results) == 1 else results


def event_handler(event_name: str) -> Callable[[Callback], Callback]:
    def decorator(callback: Callback) -> Callback:
        @wraps(callback)
        def wrapper(*args, **kwargs):
            return callback(*args, **kwargs)

        set_handler(event_name, wrapper)
        return wrapper

    return decorator
