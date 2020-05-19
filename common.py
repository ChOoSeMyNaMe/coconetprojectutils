import os
from typing import List, Dict, Generator, Tuple, Iterable
import pretty_midi


def get_files(dir: str, extension: str = None) -> List[str]:
    result = []
    files = os.listdir(dir)
    for file in files:
        fullpath = os.path.join(dir, file)
        if os.path.isfile(fullpath):
            if extension is None or file.endswith("." + extension):
                result.append(fullpath)
    return result


def load_midis_with_files(dir: str) -> Iterable[Tuple[str, pretty_midi.PrettyMIDI]]:
    return ((file, pretty_midi.PrettyMIDI(file)) for file in get_files(dir, "mid"))


def load_midis(dir: str) -> Iterable[pretty_midi.PrettyMIDI]:
    return (pretty_midi.PrettyMIDI(file) for file in get_files(dir, "mid"))


def get_file_name(path: str) -> str:
    fullname = os.path.basename(path)
    ext_point = fullname.rindex(".")
    if ext_point != -1:
        return fullname[:ext_point]
    return fullname


class Timespan:
    def __init__(self, start: float, end: float):
        self.start = start
        self.end = end

    def get_contained(self, other: "Timespan") -> "Timespan":
        if self.start <= other.start < self.end:
            if other.end < self.end:
                return other
            else:
                return Timespan(other.start, self.end)
        else:
            if other.end >= self.start and other.start < self.end:
                if other.end > self.end:
                    return Timespan(self.start, self.end)
                else:
                    return Timespan(self.start, other.end)
        return None

    def subtract(self, offset: float):
        self.start = max(0, self.start - offset)
        self.end = max(0, self.end - offset)

    def contains(self, time: float) -> bool:
        return self.start <= time <= self.end

    def overlaps(self, other: "Timespan") -> bool:
        return self.get_contained(other) is not None


def timespan_from_note(note: pretty_midi.Note) -> Timespan:
    return Timespan(note.start, note.end)
