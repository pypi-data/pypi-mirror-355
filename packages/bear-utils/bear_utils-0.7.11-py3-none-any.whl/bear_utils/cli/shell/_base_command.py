from typing import ClassVar, Generic, Self, TypeVar

T = TypeVar("T", bound=str)


class BaseShellCommand(Generic[T]):
    """Base class for typed shell commands compatible with session systems"""

    command_name: ClassVar[str] = ""

    def __init__(self, *args, **kwargs):
        self.sub_command: str = kwargs.get("sub_command", "")
        self.args = args
        self.kwargs = kwargs
        self.suffix = kwargs.get("suffix", "")
        self.result = None

    def __str__(self) -> str:
        """String representation of the command"""
        return self.cmd

    def value(self, v: str) -> Self:
        """Add value to the export command"""
        self.suffix: str = v
        return self

    @classmethod
    def adhoc(cls, name: T, *args, **kwargs) -> "BaseShellCommand[T]":
        """
        Create an ad-hoc command class for a specific command

        Args:
            name (str): The name of the command to create

        Returns:
            BaseShellCommand: An instance of the ad-hoc command class.
        """
        AdHocCommand = type(
            f"AdHoc{name.title()}Command",
            (cls,),
            {"command_name": name},
        )
        return AdHocCommand(*args, **kwargs)

    @classmethod
    def sub(cls, s: str, *args, **kwargs) -> Self:
        """Set a sub-command for the shell command"""
        return cls(sub_command=s, *args, **kwargs)

    @property
    def cmd(self) -> str:
        """Return the full command as a string"""
        cmd_parts = [self.command_name, self.sub_command] + list(self.args)
        joined = " ".join(cmd_parts).strip()
        if self.suffix:
            return f"{joined} {self.suffix}"
        return joined

    def do(self) -> Self:
        """Run the command using subprocess"""
        from ._base_shell import shell_session

        with shell_session() as session:
            session.add(str(self))
            self.result = session.run()
        return self

    def get(self) -> str:
        """Get the result of the command execution"""
        if self.result is None:
            self.do()
        if self.result is None:
            raise RuntimeError("Command execution failed for some reason.")
        return str(self.result.stdout).strip()
