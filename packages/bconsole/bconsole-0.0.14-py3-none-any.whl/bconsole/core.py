from __future__ import annotations

from abc import ABC, ABCMeta, abstractmethod
from re import findall as find_all
from sys import stdin, stdout
from typing import Any, Final, Literal, NoReturn, TextIO, final, override

__all__ = [
    "TerminalColor",
    "Foreground",
    "Background",
    "Modifier",
    "Cursor",
    "Erase",
]

_ESC = "\033"


class _ImmutableMeta(type):
    """Metaclass for immutable classes. Does not prevent the addition of new attributes."""

    @final
    def __setattr__(cls, name: str, value: Any) -> None:
        if name in cls.__dict__:
            raise AttributeError(f"Cannot reassign constant {name!r}")
        super().__setattr__(name, value)

    @final
    def __delattr__(cls, name: str) -> NoReturn:
        raise AttributeError(f"Cannot delete attribute {name!r}")


class _ABCImmutableMeta(ABCMeta, _ImmutableMeta):
    """Metaclass for immutable ABCs."""


class TerminalColor(ABC, metaclass=_ABCImmutableMeta):
    """Abstract class for terminal colors."""

    @staticmethod
    @abstractmethod
    def make_rgb(r: int, g: int, b: int, /) -> str:
        """
        Creates a True Color Escape Code Sequence for the terminal color using the RGB values provided.\n
        Note that this functionality is not supported by all terminals.

        ### Args:
            r (int): red channel
            g (int): green channel
            b (int): blue channel

        ### Returns:
            str: Escape Code Sequence
        """
        raise NotImplementedError()

    @final
    @staticmethod
    def make(code: int, /) -> str:
        """
        Creates an Escape Code Sequence for the terminal color using the ANSI Code provided.

        ### Args:
            code (int): code

        ### Returns:
            str: Escape Code Sequence
        """
        return f"{_ESC}[{code}m"

    @final
    @staticmethod
    def colorize(text: str, color: str) -> str:
        """
        Colorizes the specified text with the specified color.

        ### Args:
            text (str): The text to colorize.
            color (str): The color to use.

        ### Returns:
            str: The colorized text.
        """
        return f"{color}{text}{Modifier.RESET}"


@final
class Foreground(TerminalColor):
    """Foreground colors."""

    BLACK: Final = f"{_ESC}[30m"
    RED: Final = f"{_ESC}[31m"
    GREEN: Final = f"{_ESC}[32m"
    YELLOW: Final = f"{_ESC}[33m"
    BLUE: Final = f"{_ESC}[34m"
    MAGENTA: Final = f"{_ESC}[35m"
    CYAN: Final = f"{_ESC}[36m"
    WHITE: Final = f"{_ESC}[37m"

    @override
    @staticmethod
    def make_rgb(r: int, g: int, b: int, /) -> str:
        return f"{_ESC}[38;2;{r};{g};{b}m"


@final
class Background(TerminalColor):
    """Background colors."""

    BLACK: Final = f"{_ESC}[40m"
    RED: Final = f"{_ESC}[41m"
    GREEN: Final = f"{_ESC}[42m"
    YELLOW: Final = f"{_ESC}[43m"
    BLUE: Final = f"{_ESC}[44m"
    MAGENTA: Final = f"{_ESC}[45m"
    CYAN: Final = f"{_ESC}[46m"
    WHITE: Final = f"{_ESC}[47m"

    @override
    @staticmethod
    def make_rgb(r: int, g: int, b: int, /) -> str:
        return f"{_ESC}[48;2;{r};{g};{b}m"


@final
class Modifier(metaclass=_ImmutableMeta):
    """Color/Graphics modifiers."""

    NONE: Final = f"{_ESC}[0m"
    RESET: Final = f"{_ESC}[0m"
    BOLD: Final = f"{_ESC}[1m"
    DIM: Final = f"{_ESC}[2m"
    FAINT: Final = f"{_ESC}[2m"
    ITALIC: Final = f"{_ESC}[3m"
    UNDERLINE: Final = f"{_ESC}[4m"
    BLINK: Final = f"{_ESC}[5m"
    INVERSE: Final = f"{_ESC}[7m"
    HIDDEN: Final = f"{_ESC}[8m"
    INVISIBLE: Final = f"{_ESC}[8m"
    STRIKETHROUGH: Final = f"{_ESC}[9m"


@final
class Cursor(metaclass=_ImmutableMeta):
    """Cursor movement codes."""

    HOME: Final = f"{_ESC}[H"
    UP: Final = f"{_ESC}[1A"
    DOWN: Final = f"{_ESC}[1B"
    RIGHT: Final = f"{_ESC}[1C"
    LEFT: Final = f"{_ESC}[1D"

    @staticmethod
    def get_pos(file_in: TextIO = stdin, file_out: TextIO = stdout) -> tuple[int, int]:
        """
        Gets the current cursor position.\n
        Note that this functionality is not supported by all terminals.

        ### Args:
            file_in (TextIO, optional): The file to read the response from. Defaults to stdin.
            file_out (TextIO, optional): The file to write to. Defaults to stdout.

        ### Returns:
            tuple[int, int]: The current cursor position.
        """
        file_out.write(f"{_ESC}[6n")
        file_out.flush()

        buf = ""
        while (c := file_in.read(1)) != "R":
            buf += c

        return tuple(map(int, find_all(r"\d+", buf)))  # type: ignore

    @staticmethod
    def set_pos(column: int, line: int, /) -> str:
        """
        Returns the escape code sequence necessary to set the cursor position to the specified column and line.\n
        Note that this functionality is not supported by all terminals.

        ### Args:
            column (int): The column to move to.
            line (int): The line to move to.

        ### Returns:
            str: Escape Code Sequence
        """
        return f"{_ESC}[{line};{column}H"

    @staticmethod
    def up(lines: int = 1, /) -> str:
        """
        Moves cursor up by the number of lines provided.

        ### Args:
            lines (int, optional): Number of lines to move. Defaults to 1.

        ### Returns:
            str: Escape Code Sequence
        """
        return f"{_ESC}[{lines}1A"

    @staticmethod
    def down(lines: int = 1, /) -> str:
        """
        Moves cursor down by the number of lines provided.

        ### Args:
            lines (int, optional): Number of lines to move. Defaults to 1.

        ### Returns:
            str: Escape Code Sequence
        """
        return f"{_ESC}[{lines}1B"

    @staticmethod
    def right(columns: int = 1, /) -> str:
        """
        Moves cursor to the right by the number of columns provided.

        ### Args:
            columns (int, optional): Number of columns to move. Defaults to 1.

        ### Returns:
            str: Escape Code Sequence
        """
        return f"{_ESC}[{columns}1C"

    @staticmethod
    def left(columns: int = 1, /) -> str:
        """
        Moves cursor to the left by the number of columns provided.

        ### Args:
            columns (int, optional): Number of columns to move. Defaults to 1.

        ### Returns:
            str: Escape Code Sequence
        """
        return f"{_ESC}[{columns}1D"

    @staticmethod
    def save_pos(sequence: Literal["DEC", "SCO"] = "DEC") -> str:
        """
        Saves the current cursor position for use with restore_pos at a later time.

        #### Note:
        The escape sequences for "save cursor position" and "restore cursor position" were never standardised as part of
        the ANSI (or subsequent) specs, resulting in two different sequences known in some circles as "DEC" and "SCO":\n
            DEC: ESC7 (save) and ESC8 (restore)
            SCO: ESC[s (save) and ESC[u (restore)

        Different terminals (and OSes) support different combinations of these sequences (one, the other, neither or both);
        for example the iTerm2 terminal on macOS supports both, while the built-in macOS Terminal.app only supports the DEC sequences.

        #### Sources:
            https://github.com/fusesource/jansi/issues/226
            https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797#:~:text=saved%20position%20(SCO)-,Note,-%3A%20Some%20sequences

        ### Args:
            sequence (Literal["DEC", "SCO"], optional): which sequence to use. Defaults to "DEC".

        ### Returns:
            str: Escape Code Sequence
        """
        return f"{_ESC}7" if sequence == "DEC" else f"{_ESC}[s"

    @staticmethod
    def restore_pos(sequence: Literal["DEC", "SCO"] = "DEC") -> str:
        """
        Restores the current cursor position, which was previously saved with save_pos.

        #### Note:
        The escape sequences for "save cursor position" and "restore cursor position" were never standardised as part of
        the ANSI (or subsequent) specs, resulting in two different sequences known in some circles as "DEC" and "SCO":\n
            DEC: ESC7 (save) and ESC8 (restore)
            SCO: ESC[s (save) and ESC[u (restore)

        Different terminals (and OSes) support different combinations of these sequences (one, the other, neither or both);
        for example the iTerm2 terminal on macOS supports both, while the built-in macOS Terminal.app only supports the DEC sequences.

        #### Sources:
            https://github.com/fusesource/jansi/issues/226
            https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797#:~:text=saved%20position%20(SCO)-,Note,-%3A%20Some%20sequences

        ### Args:
            sequence (Literal["DEC", "SCO"], optional): which sequence to use. Defaults to "DEC".

        ### Returns:
            str: Escape Code Sequence
        """
        return f"{_ESC}8" if sequence == "DEC" else f"{_ESC}[u"


@final
class Erase(metaclass=_ImmutableMeta):
    """Erase codes."""

    CURSOR_TO_END: Final = f"{_ESC}[0J"
    CURSOR_TO_ENDL: Final = f"{_ESC}[0K"
    START_TO_CURSOR: Final = f"{_ESC}[1K"
    START_TO_END: Final = f"{_ESC}[1J"
    SCREEN: Final = f"{_ESC}[2J"
    LINE: Final = f"{_ESC}[2K"

    @staticmethod
    def lines(count: int = 1, /) -> list[str]:
        """
        Returns a list of escape codes to erase the specified number of lines.

        ### Args:
            count (int, optional): Number of lines to erase. Defaults to 1.

        ### Returns:
            list[str]: List of escape codes.
        """
        return [Cursor.UP + Erase.LINE for _ in range(count)]
