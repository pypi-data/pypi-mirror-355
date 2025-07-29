from typing import Self

from .shell._base_command import BaseShellCommand


class OPShellCommand(BaseShellCommand):
    """OP command for running 1Password CLI commands"""

    command_name = "op"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def read(cls, *args, **kwargs) -> Self:
        """Create a read command for 1Password"""
        return cls.sub("read", *args, **kwargs)


class UVShellCommand(BaseShellCommand):
    """UV command for running Python scripts with uv"""

    command_name = "uv"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def pip(cls, s="", *args, **kwargs) -> Self:
        """Create a piped command for uv"""
        if s:
            return cls.sub(f"pip {s}", *args, **kwargs)
        return cls.sub("pip", *args, **kwargs)


class MaskShellCommand(BaseShellCommand):
    """Mask command for running masked commands"""

    command_name = "mask"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def maskfile(cls, maskfile, *args, **kwargs) -> Self:
        """Create a maskfile command with the specified maskfile"""
        return cls.sub("--maskfile", *args, **kwargs).value(maskfile)

    @classmethod
    def init(cls, *args, **kwargs) -> Self:
        """Create an init command for mask"""
        return cls.sub("init", *args, **kwargs)


__all__ = [
    "MaskShellCommand",
    "OPShellCommand",
    "UVShellCommand",
]
