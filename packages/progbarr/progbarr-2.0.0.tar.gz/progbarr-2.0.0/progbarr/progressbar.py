"""Defines the `ProgressBar` class."""

from typing import Optional, Self
from printly import style as apply_color
from printly.types import Color


class ProgressBar:
    """Represents a progress bar."""

    def __init__(
        self: Self,
        message: str,
        tasks: int,
        length: int,
        chars: str,
        color: Optional[str],
        bgcolor: Optional[Color],
    ) -> None:
        self.message: str = message
        self.tasks: int = tasks
        self.length: int = length
        self.chars: str = chars
        self.color: Optional[Color] = color
        self.bgcolor: Optional[Color] = bgcolor
        self._pointer: int
        self._pace: float
        self._border_left: str
        self._fill_char: str
        self._head_char: str
        self._empty_char: str
        self._border_right: str

    def __enter__(self: Self) -> "ProgressBar":
        self._pointer = 0
        self._pace = self.length / self.tasks
        self._border_left = self.chars[0:1].strip()
        self._fill_char = self.chars[1:2] or " "
        self._head_char = self.chars[2:3] or " "
        self._empty_char = self.chars[3:4] or " "
        self._border_right = self.chars[4:5].strip()
        self.advance()
        return self

    def advance(self: Self) -> None:
        """Advances the progress bar."""
        pos = int(self._pointer * self._pace)
        pb = self._fill_char * (pos - 1)
        pb += self._head_char * (pos > 0)
        pb = apply_color(pb, fg=self.color, bg=self.bgcolor)
        pb += self._empty_char * (self.length - pos)
        pb = self._border_left + pb + self._border_right
        percent = int(self._pointer / self.tasks * 100)
        print(f"\r{self.message} {pb} {percent}%", end="")
        self._pointer += 1

    def __exit__(self: Self, exc_type, exc_value, exc_tb) -> None:
        print()
