import atexit
import traceback
from datetime import datetime
from enum import Enum
from pathlib import Path
from sys import stderr, stdout
from typing import Any, Final, Literal, Self, TextIO, override

from .core import Foreground, Modifier
from .utils import clear_ansi

__all__ = ["LogLevel", "LogLevelLike", "Logger", "ColoredLogger"]

"""Type alias for a log level or a string representing a log level."""
type LogLevelLike = (
    LogLevel | Literal["verbose", "debug", "info", "warning", "error", "critical"]
)


class LogLevel(Enum):
    """Logging levels."""

    Verbose = "verbose"
    Debug = "debug"
    Info = "info"
    Warning = "warning"
    Error = "error"
    Critical = "critical"

    @classmethod
    def ensure(cls, level: LogLevelLike) -> Self:
        """
        Converts a string to a LogLevel if necessary.

        ### Args:
            level (LogLevelLike): The log level to convert.

        ### Returns:
            LogLevel: The log level.
        """
        if isinstance(level, str):
            return cls[level.title()]
        return level  # type: ignore


class Logger:
    """Logger class."""

    def log(
        self,
        message: str,
        /,
        level: LogLevelLike = LogLevel.Info,
        *,
        end: str = "\n",
        flush: bool = False,
    ) -> str:
        """
        Logs a message with the specified log level to the console.

        ### Args:
            message (str): The message to log.
            level (LogLevelLike, optional): The log level. Defaults to LogLevel.INFO.
            end (str, optional): The end to use. Defaults to "\n".

        ### Returns:
            str: The formatted, logged message.
        """
        file = self._get_file(message, level)
        formatted = self._format(message, level, end)

        if file:
            file.write(formatted)

            if flush:
                file.flush()

        return formatted

    def verbose(self, message: str, /) -> None:
        """
        Logs a message with LogLevel.VERBOSE to the console.

        ### Args:
            message (str): The message to log.
        """
        self.log(message, LogLevel.Verbose)

    def debug(self, message: str, /) -> None:
        """
        Logs a message with LogLevel.DEBUG to the console.

        ### Args:
            message (str): The message to log.
        """
        self.log(message, LogLevel.Debug)

    def info(self, message: str, /) -> None:
        """
        Logs a message with LogLevel.INFO to the console.

        ### Args:
            message (str): The message to log.
        """
        self.log(message, LogLevel.Info)

    def warning(self, message: Warning | str, /) -> None:
        """
        Logs a message with LogLevel.WARNING to the console.

        ### Args:
            message (str): The message to log.
        """
        self.log(str(message), LogLevel.Warning)

    def error(self, message: Exception | str, /) -> None:
        """
        Logs a message with LogLevel.ERROR to the console.

        ### Args:
            message (Exception | str): The message or exception to log.
        """
        self.log(str(message), LogLevel.Error)

    def critical(self, message: Exception | str, /) -> None:
        """
        Logs a message with LogLevel.CRITICAL to the console.

        ### Args:
            message (Exception | str): The message or exception to log.
        """
        self.log(str(message), LogLevel.Critical)

    def _get_file(
        self, message: str, level: LogLevelLike = LogLevel.Info, /
    ) -> TextIO | None:
        """
        Gets the file to write the log message to based on message or log level.\n
        Can be overriden to write to a different file for different messages or log levels.\n
        If None, the message will not be logged.\n
        By default, uses stderr if the level is error or critical, and stdout otherwise. `message` is unused.

        ### Args:
            message (str): The message being logged.
            level (LogLevelLike, optional): The log level. Defaults to LogLevel.INFO.

        ### Returns:
            TextIO | None: The file to write the log message to. If None, the message will not be logged.
        """
        return (
            stderr
            if LogLevel.ensure(level) in (LogLevel.Error, LogLevel.Critical)
            else stdout
        )

    def _format(
        self, message: str, level: LogLevelLike = LogLevel.Info, /, end: str = "\n"
    ) -> str:
        """
        Formats the log message with the specified log level.\n
        Can be overriden to provide different formatting styles based on the log level.

        ### Args:
            message (str): The message to format.
            level (LogLevelLike, optional): The log level. Defaults to LogLevel.INFO.

        ### Returns:
            str: The formatted log message.
        """
        return f"[{LogLevel.ensure(level).name}] {message}{end}"


class ColoredLogger(Logger):
    """An example of how to override the Logger class to provide colored logging with timestamps and stack information."""

    _color_mapping: Final = {
        LogLevel.Verbose: Foreground.CYAN,
        LogLevel.Debug: Foreground.GREEN,
        LogLevel.Info: Foreground.WHITE,
        LogLevel.Warning: Foreground.make_rgb(255, 164, 0),  # orange
        LogLevel.Error: Foreground.RED,
        LogLevel.Critical: Foreground.RED,
    }

    _modifier_mapping: Final = {
        LogLevel.Verbose: Modifier.ITALIC,
        LogLevel.Debug: Modifier.ITALIC,
        LogLevel.Info: Modifier.NONE,
        LogLevel.Warning: Modifier.BOLD,
        LogLevel.Error: Modifier.BOLD,
        LogLevel.Critical: Modifier.INVERSE,
    }

    @override
    def _format(
        self, message: str, level: LogLevelLike = LogLevel.Info, /, end: str = "\n"
    ) -> str:
        frame = traceback.extract_stack(limit=5)[0]

        level = LogLevel.ensure(level)
        dt = datetime.now().strftime("%Y-%m-%d｜%H:%M:%S")
        file = Path(frame.filename or "").stem
        loc = frame.lineno or 0

        return (
            f"{Foreground.CYAN}({dt}){Modifier.RESET} "
            f"{Foreground.YELLOW}[{file}@L{loc}]{Modifier.RESET} "
            f"{self._modifier_mapping[level]}{self._color_mapping[level]}{super()._format(message, level)}{Modifier.RESET}"
        )


class ColoredFileLogger(ColoredLogger):
    """A logger that logs to a file and optionally to the terminal."""

    def __init__(self, file: TextIO, /, log_to_terminal: bool = True) -> None:
        self._file = file
        self.log_to_terminal = log_to_terminal

        atexit.register(self.close)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    @classmethod
    def from_path(cls, path: Path | str, /, encoding: str = "utf-8") -> Self:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return cls(open(path, mode="w+", encoding=encoding))

    @property
    def file(self) -> TextIO | None:
        return self._file

    @file.setter
    def file(self, value: TextIO) -> None:
        self.close()
        self._file = value

    @property
    def is_open(self) -> bool:
        return not self.is_closed

    @property
    def is_closed(self) -> bool:
        return self._file is None or self._file.closed

    @override
    def log(
        self,
        message: str,
        /,
        level: LogLevelLike = LogLevel.Info,
        *,
        end: str = "\n",
        flush: bool = False,
    ) -> str:
        formatted = super().log(message, level, end=end, flush=flush)

        if self.is_open:
            self._file.write(clear_ansi(formatted))  # type: ignore

            if flush:
                self._file.flush()  # type: ignore

        return formatted

    @override
    def _get_file(
        self, message: str, level: LogLevelLike = LogLevel.Info, /
    ) -> TextIO | None:
        return super()._get_file(message, level) if self.log_to_terminal else None

    def close(self) -> None:
        if self.is_closed:
            return

        self._file.close()  # type: ignore
        self._file = None
