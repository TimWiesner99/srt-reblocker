"""Timecode classes for handling video and subtitle timecodes.

Provides an ABC base class with shared arithmetic/comparison operators,
and two concrete subclasses:
- FrameTimecode:   HH:MM:SS:FF (frame-based, e.g. broadcast)
- DecimalTimecode: HH:MM:SS,mmm (millisecond-based, e.g. SRT subtitles)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import re


class TimecodeBase(ABC):
    """Abstract base class for timecodes.

    Provides shared arithmetic and comparison operators.
    Subclasses must implement unit conversion and string parsing/formatting.
    """

    @abstractmethod
    def to_units(self) -> int:
        """Convert timecode to its smallest unit (frames or milliseconds)."""

    @classmethod
    @abstractmethod
    def from_units(cls, total: int) -> TimecodeBase:
        """Create a timecode from a total unit count."""

    @classmethod
    @abstractmethod
    def from_string(cls, tc_string: str, **kwargs: object) -> TimecodeBase:
        """Parse a timecode from a string."""

    @abstractmethod
    def to_string(self) -> str:
        """Format the timecode as a string."""

    def __str__(self) -> str:
        return self.to_string()

    def __add__(self, other: TimecodeBase) -> TimecodeBase:
        if not isinstance(other, self.__class__):
            return NotImplemented
        total = self.to_units() + other.to_units()
        return self.__class__.from_units(total)

    def __sub__(self, other: TimecodeBase) -> TimecodeBase:
        if not isinstance(other, self.__class__):
            return NotImplemented
        total = self.to_units() - other.to_units()
        if total < 0:
            raise ValueError("Cannot have negative timecode result")
        return self.__class__.from_units(total)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.to_units() == other.to_units()

    def __lt__(self, other: TimecodeBase) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.to_units() < other.to_units()

    def __le__(self, other: TimecodeBase) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.to_units() <= other.to_units()

    def __gt__(self, other: TimecodeBase) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.to_units() > other.to_units()

    def __ge__(self, other: TimecodeBase) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.to_units() >= other.to_units()

    def __hash__(self) -> int:
        return hash(self.to_units())


@dataclass
class FrameTimecode(TimecodeBase):
    """Represents a video timecode with hours, minutes, seconds, and frames.

    The timecode format is HH:MM:SS:FF where FF is the frame number (0-based).
    Frame rate is configurable, with 25 fps as the default (PAL standard).
    """

    hours: int
    minutes: int
    seconds: int
    frames: int
    fps: int = 25

    TIMECODE_PATTERN = re.compile(r'^(\d{2}):(\d{2}):(\d{2}):(\d{2})$')

    def __post_init__(self) -> None:
        if self.hours < 0:
            raise ValueError(f"Hours cannot be negative: {self.hours}")
        if not 0 <= self.minutes < 60:
            raise ValueError(f"Minutes must be 0-59: {self.minutes}")
        if not 0 <= self.seconds < 60:
            raise ValueError(f"Seconds must be 0-59: {self.seconds}")
        if not 0 <= self.frames < self.fps:
            raise ValueError(f"Frames must be 0-{self.fps - 1}: {self.frames}")

    def to_units(self) -> int:
        return self.to_frames()

    @classmethod
    def from_units(cls, total: int, fps: int = 25) -> FrameTimecode:
        return cls.from_frames(total, fps)

    def to_frames(self) -> int:
        """Convert timecode to total frame count."""
        return (
            self.frames
            + self.seconds * self.fps
            + self.minutes * 60 * self.fps
            + self.hours * 3600 * self.fps
        )

    @classmethod
    def from_frames(cls, total_frames: int, fps: int = 25) -> FrameTimecode:
        """Create a FrameTimecode from total frame count."""
        if total_frames < 0:
            raise ValueError(f"Total frames cannot be negative: {total_frames}")

        frames = total_frames % fps
        total_seconds = total_frames // fps
        seconds = total_seconds % 60
        total_minutes = total_seconds // 60
        minutes = total_minutes % 60
        hours = total_minutes // 60

        return cls(hours=hours, minutes=minutes, seconds=seconds, frames=frames, fps=fps)

    @classmethod
    def from_string(cls, tc_string: str, fps: int = 25) -> FrameTimecode:
        """Parse a timecode string in HH:MM:SS:FF format."""
        if not tc_string or not isinstance(tc_string, str):
            raise ValueError(f"Invalid timecode string: {tc_string}")

        tc_string = tc_string.strip()
        match = cls.TIMECODE_PATTERN.match(tc_string)

        if not match:
            raise ValueError(f"Invalid timecode format: '{tc_string}'. Expected HH:MM:SS:FF")

        hours, minutes, seconds, frames = map(int, match.groups())

        if frames >= fps:
            frames = 0

        return cls(hours=hours, minutes=minutes, seconds=seconds, frames=frames, fps=fps)

    def to_string(self) -> str:
        """Convert timecode to string format HH:MM:SS:FF."""
        return f"{self.hours:02d}:{self.minutes:02d}:{self.seconds:02d}:{self.frames:02d}"

    def __add__(self, other: TimecodeBase) -> FrameTimecode:
        if not isinstance(other, FrameTimecode):
            return NotImplemented
        if self.fps != other.fps:
            raise ValueError(f"Cannot add timecodes with different frame rates: {self.fps} vs {other.fps}")
        total_frames = self.to_frames() + other.to_frames()
        return FrameTimecode.from_frames(total_frames, self.fps)

    def __sub__(self, other: TimecodeBase) -> FrameTimecode:
        if not isinstance(other, FrameTimecode):
            return NotImplemented
        if self.fps != other.fps:
            raise ValueError(f"Cannot subtract timecodes with different frame rates: {self.fps} vs {other.fps}")
        total_frames = self.to_frames() - other.to_frames()
        if total_frames < 0:
            raise ValueError("Cannot have negative timecode result")
        return FrameTimecode.from_frames(total_frames, self.fps)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FrameTimecode):
            return NotImplemented
        return self.to_frames() == other.to_frames() and self.fps == other.fps

    def __hash__(self) -> int:
        return hash((self.to_frames(), self.fps))

    def round_to_seconds(self) -> FrameTimecode:
        """Round timecode to the nearest second."""
        if self.frames >= self.fps / 2:
            total_frames = self.to_frames() + (self.fps - self.frames)
            return FrameTimecode.from_frames(total_frames, self.fps)
        else:
            return FrameTimecode(
                hours=self.hours,
                minutes=self.minutes,
                seconds=self.seconds,
                frames=0,
                fps=self.fps
            )

    def to_string_rounded(self) -> str:
        """Convert timecode to string format HH:MM:SS (without frames), rounded to nearest second."""
        rounded = self.round_to_seconds()
        return f"{rounded.hours:02d}:{rounded.minutes:02d}:{rounded.seconds:02d}"

    def __repr__(self) -> str:
        return f"FrameTimecode({self.to_string()}, fps={self.fps})"


@dataclass
class DecimalTimecode(TimecodeBase):
    """Represents an SRT subtitle timecode with hours, minutes, seconds, and milliseconds.

    The timecode format is HH:MM:SS,mmm as used in SRT subtitle files.
    """

    hours: int = 0
    minutes: int = 0
    seconds: int = 0
    milliseconds: int = 0

    TIMECODE_PATTERN = re.compile(r'^(\d{2}):(\d{2}):(\d{2}),(\d{3})$')

    def __post_init__(self) -> None:
        if self.hours < 0:
            raise ValueError(f"Hours cannot be negative: {self.hours}")
        if not 0 <= self.minutes < 60:
            raise ValueError(f"Minutes must be 0-59: {self.minutes}")
        if not 0 <= self.seconds < 60:
            raise ValueError(f"Seconds must be 0-59: {self.seconds}")
        if not 0 <= self.milliseconds < 1000:
            raise ValueError(f"Milliseconds must be 0-999: {self.milliseconds}")

    def to_units(self) -> int:
        """Convert timecode to total milliseconds."""
        return (
            self.milliseconds
            + self.seconds * 1000
            + self.minutes * 60_000
            + self.hours * 3_600_000
        )

    @classmethod
    def from_units(cls, total_ms: int) -> DecimalTimecode:
        """Create an SrtTimecode from total milliseconds."""
        if total_ms < 0:
            raise ValueError(f"Total milliseconds cannot be negative: {total_ms}")

        milliseconds = total_ms % 1000
        total_seconds = total_ms // 1000
        seconds = total_seconds % 60
        total_minutes = total_seconds // 60
        minutes = total_minutes % 60
        hours = total_minutes // 60

        return cls(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)

    @classmethod
    def from_string(cls, tc_string: str) -> DecimalTimecode:
        """Parse a timecode string in HH:MM:SS,mmm format."""
        if not tc_string or not isinstance(tc_string, str):
            raise ValueError(f"Invalid timecode string: {tc_string}")

        tc_string = tc_string.strip()
        match = cls.TIMECODE_PATTERN.match(tc_string)

        if not match:
            raise ValueError(f"Invalid timecode format: '{tc_string}'. Expected HH:MM:SS,mmm")

        hours, minutes, seconds, milliseconds = map(int, match.groups())
        return cls(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)

    def to_string(self) -> str:
        """Convert timecode to string format HH:MM:SS,mmm."""
        return f"{self.hours:02d}:{self.minutes:02d}:{self.seconds:02d},{self.milliseconds:03d}"

    def round_to_seconds(self) -> DecimalTimecode:
        """Round timecode to the nearest second."""
        if self.milliseconds >= 500:
            total_ms = self.to_units() + (1000 - self.milliseconds)
            return DecimalTimecode.from_units(total_ms)
        else:
            return DecimalTimecode(
                hours=self.hours,
                minutes=self.minutes,
                seconds=self.seconds,
                milliseconds=0
            )

    def to_string_rounded(self) -> str:
        """Convert timecode to string format HH:MM:SS (without milliseconds), rounded to nearest second."""
        rounded = self.round_to_seconds()
        return f"{rounded.hours:02d}:{rounded.minutes:02d}:{rounded.seconds:02d}"

    def __repr__(self) -> str:
        return f"SrtTimecode({self.to_string()})"

__all__ = ["TimecodeBase", "FrameTimecode", "DecimalTimecode", "Timecode"]
