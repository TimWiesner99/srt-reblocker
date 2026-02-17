"""SRT block class to represent one 'block' in an srt file."""

from dataclasses import dataclass
from timecode import timecode

@dataclass
class Srt_block:
    index: int
    begin: timecode
    end: timecode
    text: str

