import os
from numbers import Number
from typing import List, Dict, Generator, Tuple, Iterable

import click
import pretty_midi
from colorama import Style


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
    files = get_files(dir, "mid")
    for file in files:
        try:
            mid = pretty_midi.PrettyMIDI(file)
            yield (file, mid)
        except IOError:
            continue


def load_midis(dir: str) -> Iterable[pretty_midi.PrettyMIDI]:
    return (pretty_midi.PrettyMIDI(file) for file in get_files(dir, "mid"))


def get_file_name(path: str) -> str:
    fullname = os.path.basename(path)
    ext_point = fullname.rfind(".")
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


def is_in_range(value: Number, min: Number, max: Number) -> bool:
    return min <= value <= max


def get_and_create_folder_path(folder: str, name: str) -> str:
    path = os.path.join(folder, name)
    if not os.path.exists(path):
        os.mkdir(path)
    return path


def print_colored(text, color, colored=True):
    if colored:
        click.echo(color + text + Style.RESET_ALL)
    else:
        click.echo(text)
