import asyncio
import os
import subprocess
from asyncio.streams import StreamReader
from asyncio.subprocess import Process
from collections import deque
from collections.abc import AsyncGenerator, Callable, Generator
from contextlib import asynccontextmanager, contextmanager
from io import StringIO
from logging import INFO
from pathlib import Path
from subprocess import CompletedProcess
from typing import Self, override

from ._base_command import BaseShellCommand
from ._common import DEFAULT_SHELL

EXIT_CODES: dict[int, str] = {
    0: "Success",
    1: "General error",
    2: "Misuse of shell command",
    126: "Command invoked cannot execute",
    127: "Command not found",
    128: "Invalid argument to exit",
    130: "Script terminated by Control-C",
    137: "Process killed by SIGKILL (9)",
    139: "Segmentation fault (core dumped)",
    143: "Process terminated by SIGTERM (15)",
    255: "Exit status out of range",
}


class FancyCompletedProcess(CompletedProcess[str]):
    def __init__(self, args, returncode, stdout=None, stderr=None):
        super().__init__(args=args, returncode=returncode, stdout=stdout, stderr=stderr)

    def __repr__(self):
        args = [
            f"args={self.args!r}",
            f"returncode={self.returncode!r}",
            f"exit_message={self.exit_message!r}",
            f"stdout={self.stdout!r}" if self.stdout is not None else "",
            f"stderr={self.stderr!r}" if self.stderr is not None else "",
        ]
        return f"{type(self).__name__}({', '.join(filter(None, args))})"

    @property
    def exit_message(self) -> str:
        """Get a human-readable message for the exit code"""
        return EXIT_CODES.get(self.returncode, EXIT_CODES.get(1, "Unknown error"))


class CommandList(deque[CompletedProcess[str]]):
    """A list to hold previous commands with their timestamps and results"""

    def __init__(self, maxlen=10, *args, **kwargs):
        super().__init__(maxlen=maxlen, *args, **kwargs)

    def add(self, command: CompletedProcess[str]) -> None:
        """Add a command to the list"""
        self.append(command)

    def get(self, index: int) -> CompletedProcess[str] | None:
        """Get a command by index"""
        return self[index] if 0 <= index < len(self) else None

    def get_most_recent(self) -> CompletedProcess[str] | None:
        """Get the most recent command"""
        return self[-1] if self else None


class SimpleShellSession:
    """Simple shell session using subprocess with command chaining"""

    def __init__(self, env=None, cwd=None, shell: str = DEFAULT_SHELL, logger=None, verbose: bool = False):
        self.shell: str = shell
        self.cwd: Path = Path.cwd() if cwd is None else Path(cwd)
        self.env: dict[str, str] = os.environ.copy() if env is None else env
        self.cmd_buffer: StringIO = StringIO()
        self.previous_commands: CommandList = CommandList()
        self.result: CompletedProcess[str] | None = None
        self.verbose: bool = verbose
        self.logger = self.set_logger(logger)

    def set_logger(self, passed_logger=None):
        """Set the logger for the session, defaulting to a base logger if none is provided"""
        from ...logging.loggers import VERBOSE, BaseLogger, SubConsoleLogger

        if passed_logger is not None:
            return passed_logger

        if BaseLogger.has_instance():
            logger = BaseLogger.get_instance().get_sub_logger(namespace="shell_session")
        else:
            temp = BaseLogger.get_instance(init=True)
            logger: SubConsoleLogger[BaseLogger] = temp.get_sub_logger(namespace="shell_session")
        if self.verbose:
            logger.set_sub_level(VERBOSE)
        else:
            logger.set_sub_level(INFO)
        return logger

    def add_to_env(self, env: dict[str, str], key: str | None = None, value=None) -> Self:
        """Populate the environment for the session"""
        _env = {}
        if isinstance(env, str) and key is not None and value is not None:
            _env[key] = value
        elif isinstance(env, dict):
            for k, v in env.items():
                _env[k] = v
        self.env.update(_env)
        return self

    def add(self, c: str | BaseShellCommand) -> Self:
        """Add a command to the current session, return self for chaining"""
        self.cmd_buffer.write(str(c))
        return self

    def amp(self, c: str | BaseShellCommand) -> Self:
        """Combine a command with the current session: &&, return self for chaining"""
        if self.empty_history:
            raise ValueError("No command to combine with")
        self.cmd_buffer.write(" && ")
        self.cmd_buffer.write(str(c))
        return self

    def piped(self, c: str | BaseShellCommand) -> Self:
        """Combine a command with the current session: |, return self for chaining"""
        if self.empty_history:
            raise ValueError("No command to pipe from")
        self.cmd_buffer.write(" | ")
        self.cmd_buffer.write(str(c))
        return self

    def _run(self, command: str) -> CompletedProcess[str] | Process:
        """Internal method to run the accumulated command"""
        self.logger.verbose(f"Executing: {command}")
        self.next_cmd()
        self.result = subprocess.run(
            command,
            shell=True,
            cwd=self.cwd,
            env=self.env,
            capture_output=True,
            text=True,
        )
        if self.result.returncode != 0:
            self.logger.error(f"Command failed with return code {self.result.returncode} {self.result.stderr.strip()}")

        self.reset_buffer()
        return self.result

    def run(self, cmd: str | BaseShellCommand | None = None, *args) -> CompletedProcess[str] | Process:
        """Run the accumulated command history"""
        if self.empty_history and cmd is None:
            raise ValueError("No commands to run")

        if self.has_history and cmd is not None:
            raise ValueError(
                "If you want to add a command to a chain, use `amp` instead of `run`, `run` is for executing the full command history"
            )

        if self.has_history and cmd is None:
            result = self._run(self.cmd)
        elif self.empty_history and cmd is not None:
            self.cmd_buffer.write(f"{cmd} ")
            if args:
                self.cmd_buffer.write(" ".join(map(str, args)))
            result = self._run(self.cmd)
        else:
            raise ValueError("Unexpected state")
        self.reset_buffer()
        return result

    @property
    def empty_history(self) -> bool:
        """Check if the command history is empty"""
        return not self.cmd_buffer.getvalue()

    @property
    def has_history(self) -> bool:
        """Check if there is any command in the history"""
        return not self.empty_history

    @property
    def cmd(self) -> str:
        """Return the combined command as a string"""
        if not self.cmd_buffer:
            raise ValueError("No commands have been run yet")
        full_command: str = f'{self.shell} -c "{self.cmd_buffer.getvalue()}"'
        return full_command

    @property
    def returncode(self) -> bool:
        """Return the last command's return code"""
        if self.result is None:
            raise ValueError("No command has been run yet")
        return self.result.returncode == 0

    @property
    def stdout(self) -> str:
        """Return the standard output of the last command"""
        if self.result is None:
            raise ValueError("No command has been run yet")
        return self.result.stdout.strip() if self.result.stdout is not None else "None"

    @property
    def stderr(self) -> str:
        """Return the standard error of the last command"""
        if self.result is None:
            raise ValueError("No command has been run yet")
        return self.result.stderr.strip() if self.result.stderr is not None else "None"

    @property
    def pretty_result(self) -> str:
        """Return a formatted string of the command result"""
        if self.result is None:
            raise ValueError("No command has been run yet")
        return (
            f"Command: {self.result.args}\n"
            f"Return Code: {self.result.returncode}\n"
            f"Standard Output: {self.result.stdout.strip()}\n"
            f"Standard Error: {self.result.stderr.strip()}\n"
        )

    def reset_buffer(self) -> None:
        """Reset the command buffer"""
        self.cmd_buffer.seek(0)
        self.cmd_buffer.truncate(0)

    def reset(self) -> None:
        """Reset the session state"""
        self.previous_commands.clear()
        self.result = None

    def next_cmd(self) -> None:
        """Store the current command in the history before running a new one"""
        if self.result is not None:
            self.previous_commands.add(command=self.result)
            self.result = None

    def get_cmd(self, index: int | None = None) -> CompletedProcess[str] | None:
        """Get a previous command by index or the most recent one if index is None"""
        if index is None:
            return self.previous_commands.get_most_recent()
        return self.previous_commands.get(index)

    def __enter__(self) -> Self:
        """Enter the context manager"""
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager"""
        self.reset()
        self.reset_buffer()


class AsyncShellSession(SimpleShellSession):
    """Shell session using Popen for more control over the subprocess"""

    def __init__(self, env=None, cwd=None, shell: str = DEFAULT_SHELL, logger=None, verbose: bool = False):
        super().__init__(env=env, cwd=cwd, shell=shell, logger=logger, verbose=verbose)
        self.process: Process | None = None
        self._callbacks: list[Callable[[CompletedProcess], None]] = []

    @override
    async def _run(self, command: str, **kwargs) -> Process:  # type: ignore[override]
        """Run the command using Popen for better control"""
        self.logger.verbose(f"Executing: {command}")
        self.next_cmd()
        self.process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.cwd,
            env=self.env,
            **kwargs,
        )
        return self.process

    @override
    async def run(self, cmd: str | BaseShellCommand | None = None, *args, **kwargs) -> Process:  # type: ignore[override]
        """Async version of run that returns Process for streaming"""
        if self.empty_history and cmd is None:
            raise ValueError("No commands to run")

        self.logger.debug(f"Running command: {cmd} with args: {args}")
        if self.has_history and cmd is not None:
            raise ValueError("Use `amp` to chain commands, not `run`")
        if self.has_history and cmd is None:
            command = self.cmd
        elif self.empty_history and cmd is not None:
            self.cmd_buffer.write(f"{cmd}")
            self.logger.info(f"{self.cmd_buffer.getvalue()}")
            if args:
                self.cmd_buffer.write(" ".join(map(str, args)))

            command = self.cmd
        else:
            raise ValueError("Unexpected state")
        process: Process = await self._run(command, **kwargs)
        return process

    async def communicate(self, stdin: str = "") -> CompletedProcess[str]:
        """Communicate with the process, sending input and waiting for completion"""
        if self.process is None:
            raise ValueError("No process has been started yet")
        stdout, stderr = await self.process.communicate(input=stdin.encode("utf-8"))
        return_code = await self.process.wait()

        self.result = FancyCompletedProcess(
            args=self.cmd,
            returncode=return_code,
            stdout=stdout.decode() if stdout else "",
            stderr=stderr.decode() if stderr else "",
        )

        if return_code != 0:
            self.logger.error(f"Command failed with return code {return_code} {stderr.strip()}")

        for callback in self._callbacks:
            callback(self.result)

        await self.after_process()
        return self.result

    @staticmethod
    async def read_stream(stream: StreamReader) -> AsyncGenerator[str, None]:
        while True:
            try:
                line: bytes = await stream.readline()
                if not line:  # EOF
                    break
                yield line.decode("utf-8").rstrip("\n")
            except Exception as e:
                break

    async def stream_stdout(self) -> AsyncGenerator[str, None]:
        """Stream output line by line as it comes"""
        if self.process is None:
            raise ValueError("No process has been started yet")
        if not self.process.stdout:
            raise ValueError("Process has no stdout")

        async for line in self.read_stream(self.process.stdout):
            yield line

    async def stream_stderr(self) -> AsyncGenerator[str, None]:
        """Stream error output line by line as it comes"""
        if self.process is None:
            raise ValueError("No process has been started yet")
        if not self.process.stderr:
            raise ValueError("Process has no stderr")
        async for line in self.read_stream(self.process.stderr):
            yield line

    async def after_process(self):
        """Run after process completion, can be overridden for custom behavior"""
        self.process = None
        self._callbacks.clear()
        self.reset_buffer()

    def on_completion(self, callback):
        """Add callback for when process completes"""
        self._callbacks.append(callback)

    @property
    def is_running(self) -> bool:
        """Check if process is still running"""
        return self.process is not None and self.process.returncode is None


@contextmanager
def shell_session(shell: str = DEFAULT_SHELL, **kwargs) -> Generator[SimpleShellSession, None, None]:
    """Context manager for simple shell sessions"""
    session = SimpleShellSession(shell=shell, **kwargs)
    try:
        yield session
    finally:
        pass


@asynccontextmanager
async def async_shell_session(shell: str = DEFAULT_SHELL, **kwargs) -> AsyncGenerator[AsyncShellSession, None]:
    """Asynchronous context manager for shell sessions"""
    session = AsyncShellSession(shell=shell, **kwargs)
    try:
        yield session
    finally:
        pass
