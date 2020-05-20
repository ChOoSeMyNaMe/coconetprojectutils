"""
Process small MIDI files into a Numpy-Trainingssetfile
Files have to be in seperate folders for train, test and valid -> cli-options
"""


from math import floor
from typing import List, Dict
import numpy as np

from common import *

import click


def get_multiple_number_greater_than(factor: float, target: float):
    tmp = target / factor
    tmp = floor(tmp)
    tmp = tmp * factor
    if tmp < target:
        return tmp + 1
    return tmp


def get_notes_from_instrument(instr: pretty_midi.Instrument, steps: float) -> Dict[float, List[pretty_midi.Note]]:
    result: Dict[float, List[pretty_midi.Note]] = {}
    for note in instr.notes:
        note_time = timespan_from_note(note)
        time = get_multiple_number_greater_than(steps, note_time.start)
        while note_time.contains(time):
            if time not in result:
                result[time] = [note]
            else:
                result[time].append(note)
            time += steps
    return result


def get_notes_from_midi(mid: pretty_midi.PrettyMIDI, steps: float) -> Dict[float, List[pretty_midi.Note]]:
    result: Dict[float, List[pretty_midi.Note]] = {}
    for instr in mid.instruments:
        extracted_notes = get_notes_from_instrument(instr, steps)
        for time, notes in extracted_notes.items():
            if time not in result:
                result[time] = notes
            else:
                result[time].extend(notes)
    return result


def normalize_notelists(notes: List[int], desired_note_count: int) -> List[int]:
    while len(notes) > desired_note_count:
        notes.pop(len(notes) - 1)
    while len(notes) < desired_note_count:
        notes.append(None)
    return notes


def get_note_values_from_midi(mid: pretty_midi.PrettyMIDI, steps: float, desired_note_count: int) -> List[List[int]]:
    notes = get_notes_from_midi(mid, steps)
    result: List[List[int]] = []
    time = 0
    while len(notes) > 0:
        if time in notes:
            pretty_notes = notes[time]
            result.append(normalize_notelists([note.pitch for note in pretty_notes], desired_note_count))
            del notes[time]
        else:
            result.append(normalize_notelists([], desired_note_count))
        time += steps
    return result


def get_all_note_values(midis: List[pretty_midi.PrettyMIDI],
                        steps: float,
                        desired_note_count: int) -> List[List[List[int]]]:
    return [get_note_values_from_midi(mid, steps, desired_note_count) for mid in midis]


def transform_notes(notes: List[List[List[int]]]) -> any:
    data = [np.array(piece, dtype=np.float_) for piece in notes]
    return np.array(data, dtype=np.object)


def build_training_dict(notes_train: List[List[List[int]]],
                        notes_test: List[List[List[int]]],
                        notes_validate: List[List[List[int]]]) -> Dict[str, List[List[List[int]]]]:
    return {
        "train": notes_train,
        "test": notes_test,
        "valid": notes_validate
    }


def transform_training_dict(notes: Dict[str, List[List[List[int]]]]) -> Dict[str, any]:
    return {
        "train": transform_notes(notes["train"]),
        "test": transform_notes(notes["test"]),
        "valid": transform_notes(notes["valid"])
    }


def save_notes_with_pickle(notes: Dict[str, List[List[List[int]]]], file: str):
    with open(file, "wb") as f:
        try:
            import cPickle as pickle
            pickle.dump(notes, f)
        except:
            import pickle
            pickle.dump(notes, f)


def save_notes_with_numpy(notes: Dict[str, any], file: str):
    with open(file, "wb") as f:
        np.savez_compressed(f, **notes)


def load_notes_with_pickle(file: str) -> Dict[str, List[List[List[int]]]]:
    result = None
    with open(file, "rb") as f:
        try:
            import cPickle as pickle
            result = pickle.load(f)
        except:
            import pickle
            result = pickle.load(f)
    return result


def load_notes_with_numpy(file: str) -> Dict[str, any]:
    result = None
    with open(file, "rb") as f:
        with np.load(f, allow_pickle=False) as npz:
            result = {
                "train": npz["train"],
                "test": npz["test"],
                "valid": npz["valid"]
            }
    return result


def build_trainingsdata(train_dir: str,
                        test_dir: str,
                        valid_dir: str,
                        steps: float,
                        desired_note_count: int
                        ) -> Dict[str, List[List[List[int]]]]:
    # load midis
    click.echo("Loading training files from {}...".format(train_dir))
    train_midis = load_midis(train_dir)
    click.echo("Loading testing files from {}...".format(test_dir))
    test_midis = load_midis(test_dir)
    click.echo("Loading validation files from {}...".format(valid_dir))
    valid_midis = load_midis(valid_dir)

    # extract notes
    click.echo("Processing training files...")
    train_notes = get_all_note_values(train_midis, steps, desired_note_count)
    click.echo("Processing testing files...")
    test_notes = get_all_note_values(test_midis, steps, desired_note_count)
    click.echo("Processing validation files...")
    valid_notes = get_all_note_values(valid_midis, steps, desired_note_count)

    click.echo("Combining processed data...")
    return build_training_dict(train_notes, test_notes, valid_notes)


def save_trainingsdata(notes: Dict[str, List[List[List[int]]]], filename: str):
    click.echo("Saving with pickle...")
    save_notes_with_pickle(notes, filename + ".pkl")
    click.echo("Saving with numpy...")
    save_notes_with_numpy(transform_training_dict(notes), filename + ".npz")


@click.command()
@click.option("train_dir", "--train", type=click.Path(exists=True, file_okay=False), required=True)
@click.option("test_dir", "--test", type=click.Path(exists=True, file_okay=False), required=True)
@click.option("valid_dir", "--valid", type=click.Path(exists=True, file_okay=False), required=True)
@click.option("out", "-o", type=str, required=True)
@click.option("--steps", default=0.125, type=float, show_default=True)
@click.option("--desired_note_count", "--notes", default=4, type=int, show_default=True)
def main(train_dir: str,
         test_dir: str,
         valid_dir: str,
         out: str,
         steps: float,
         desired_note_count: int):
    click.echo("Processing files with steps={} and note_count={}...".format(steps, desired_note_count))
    notes = build_trainingsdata(
        train_dir,
        test_dir,
        valid_dir,
        steps,
        desired_note_count
    )
    click.echo("Saving data...")
    save_trainingsdata(notes, out)
    click.echo("Done.")


if __name__ == '__main__':
    main()
