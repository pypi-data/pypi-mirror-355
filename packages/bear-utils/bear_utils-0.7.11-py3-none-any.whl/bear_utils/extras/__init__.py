from ._tools import ClipboardManager, clear_clipboard, copy_to_clipboard, fmt_header, paste_from_clipboard
from .platform_utils import OS, get_platform, is_linux, is_macos, is_windows
from .wrappers.add_methods import add_comparison_methods

__all__ = [
    "OS",
    "get_platform",
    "is_linux",
    "is_macos",
    "is_windows",
    "ClipboardManager",
    "copy_to_clipboard",
    "paste_from_clipboard",
    "clear_clipboard",
    "fmt_header",
    "add_comparison_methods",
]
