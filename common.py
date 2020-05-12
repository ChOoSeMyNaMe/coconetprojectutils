import os
from typing import List, Dict
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


def load_midis_with_files(dir: str) -> Dict[str, pretty_midi.PrettyMIDI]:
    result = {}
    for file in get_files(dir, "mid"):
        result[file] = pretty_midi.PrettyMIDI(file)
    return result


def load_midis(dir: str) -> List[pretty_midi.PrettyMIDI]:
    return [pretty_midi.PrettyMIDI(file) for file in get_files(dir, "mid")]


def get_file_name(path: str) -> str:
    fullname = os.path.basename(path)
    ext_point = fullname.rindex(".")
    if ext_point != -1:
        return fullname[:ext_point]
    return fullname