"""SRT block class to represent one 'block' in an srt file."""

from dataclasses import dataclass
from src.timecode import DecimalTimecode

@dataclass
class SrtBlock:
    index: int
    begin: DecimalTimecode
    end: DecimalTimecode
    text: str
