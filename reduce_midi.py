"""Testing note reduction but it's not really good working"""

from math import floor
from typing import List, Dict
import numpy as np

from common import *

import click


class InstrNote:
    def __init__(self, instr: int, pitch: int):
        self.pitch = pitch
        self.instr = instr

    def __add__(self, other):
        self.pitch = self.pitch + other
        return self

    def __hash__(self):
        return hash((self.instr, self.pitch))

    def __eq__(self, other):
        if self is not None and other is not None:
            return self.pitch == other.pitch and self.instr == other.instr
        if self is None and other is None:
            return True
        return False


def sortInstrNotes(notes: List[InstrNote]) -> List[InstrNote]:
    return sorted(notes, key=lambda x: x.pitch)


def is_grundton(values: List[InstrNote]) -> List[InstrNote]:  # Grundton ist doppelt
    for i in range(1, len(values)):
        if values[0] + 4 == values[i]:  # Dur Akkord
            for j in range(i + 1, len(values)):
                if values[i] + 3 == values[j] or values[i] + 4 == values[j]:
                    return [values[0], values[i], values[j], values[0] + 12]
        elif values[0] + 3 == values[i]:  # Moll Akkord
            for j in range(i + 1, len(values)):
                if values[i] + 4 == values[j] or values[i] + 3 == values[j]:
                    return [values[0], values[i], values[j], values[0] + 12]


def is_quinte(values: List[InstrNote]) -> List[InstrNote]:  # Quinte ist doppelt
    for i in range(1, len(values)):
        if values[0] + 5 == values[i]:  # Dur Akkord
            for j in range(i + 1, len(values)):
                if values[i] + 4 == values[j] or values[i] + 3 == values[j]:
                    return [values[0], values[i], values[j], values[0] + 12]
        elif values[0] + 6 == values[i]:  # Moll Akkord
            for j in range(i + 1, len(values)):
                if values[i] + 3 == values[j]:
                    return [values[0], values[i], values[j], values[0] + 12]


def is_terz(values: List[InstrNote]) -> List[InstrNote]:  # Terz ist doppelt
    for i in range(1, len(values)):
        if values[0] + 3 == values[i]:  # Dur Akkord
            for j in range(i + 1, len(values)):
                if values[i] + 5 == values[j] or values[i] + 6 == values[j]:
                    return [values[0], values[i], values[j], values[0] + 12]
        elif values[0] + 4 == values[i]:  # Moll Akkord
            for j in range(i + 1, len(values)):
                if values[i] + 5 == values[j]:
                    return [values[0], values[i], values[j], values[0] + 12]


PITCH_FUNCTIONS = [is_grundton, is_quinte, is_terz]


def transform_pitches(notes: List[InstrNote], double_index: int) -> List[InstrNote]:
    return [(note + 12 if i < double_index else note) for i, note in enumerate(notes)]


def get_base_pitches(notes: List[InstrNote], double_index: int) -> List[InstrNote]:
    values = transform_pitches(notes, double_index)
    values = sortInstrNotes(values)
    for func in PITCH_FUNCTIONS:
        result = func(values)
        if result is not None:
            return result
    return None


def get_double_pitch(notes: List[InstrNote]) -> int:
    notes = sortInstrNotes(notes)
    for i, n in enumerate(notes):
        for note in notes:
            if n + 12 == note:
                return i
    return -1


def get_multiple_number_greater_than(factor: float, target: float):
    tmp = target / factor
    tmp = floor(tmp)
    result = tmp * factor
    if result < target:
        tmp += 1
        result = tmp * factor
    return result


def get_notes_from_instrument(instr: pretty_midi.Instrument, steps: float) -> Dict[float, List[pretty_midi.Note]]:
    result: Dict[float, List[pretty_midi.Note]] = {}
    for note in instr.notes:
        if note.duration < steps:
            continue
        note_time = timespan_from_note(note)
        time = get_multiple_number_greater_than(steps, note_time.start)
        while note_time.contains(time):
            if time not in result:
                result[time] = [note]
            else:
                result[time].append(note)
            time += steps
    return result


def get_notes_from_midi(mid: pretty_midi.PrettyMIDI, steps: float) -> Dict[float, List[InstrNote]]:
    result: Dict[float, List[InstrNote]] = {}
    for instr_index, instr in enumerate(mid.instruments):
        extracted_notes = get_notes_from_instrument(instr, steps)
        for time, notes in extracted_notes.items():
            mapped = [InstrNote(instr_index, note.pitch) for note in notes]
            if time not in result:
                result[time] = mapped
            else:
                result[time].extend(mapped)
    return result


def split_array(array: List[any], count: int) -> List[List[any]]:
    result = []
    part_length = int(floor(len(array) / count))

    for i in range(count):
        offset = i * part_length
        length = min(part_length, len(array) - offset)
        part = [array[index + offset] for index in range(length)]
        result.append(part)
    return result


def normalize_notelists(notes: List[InstrNote], desired_note_count: int) -> List[InstrNote]:
    if len(notes) <= desired_note_count:
        while len(notes) < desired_note_count:
            notes.append(None)
        return notes

    result = get_base_pitches(notes, get_double_pitch(notes))
    return result


def get_note_values_from_midi(mid: pretty_midi.PrettyMIDI, steps: float, desired_note_count: int) -> List[
    List[InstrNote]]:
    notes = get_notes_from_midi(mid, steps)
    result: List[List[InstrNote]] = []
    time = 0
    while len(notes) > 0:
        if time in notes:
            r = normalize_notelists(notes[time], desired_note_count)
            if r is not None:
                result.append(r)
            else:
                result.append([])
            del notes[time]
        else:
            r = normalize_notelists([], desired_note_count)
            if r is not None:
                result.append(r)
            else:
                result.append([])
        time += steps
    return result


def consume_further_notes(notes: List[List[InstrNote]], offset: int, pitch: InstrNote) -> int:
    i = offset
    count = 0
    while i < len(notes):
        if pitch in notes[i]:
            count += 1
            index: int = notes[i].index(pitch)
            notes[i][index] = None
            i += 1
        else:
            break
    return count


def create_midi(notes: List[List[InstrNote]], steps: float) -> pretty_midi.PrettyMIDI:
    result = pretty_midi.PrettyMIDI(initial_tempo=80)
    offset = 0
    instr_values = set()
    for step in notes:
        for note in step:
            if note is not None:
                instr_values.add(note.instr)

    instr_indices = dict()
    for i, x in enumerate(instr_values):
        instr_indices[x] = i

    instr = [pretty_midi.Instrument(i) for i in range(len(instr_values))]
    # instr = pretty_midi.Instrument(0)
    for moment_index in range(len(notes)):
        for note in notes[moment_index]:
            if note is not None:
                total_pitch_length = consume_further_notes(notes, moment_index + 1, note) + 1
                total_pitch_length *= steps
                new_note = pretty_midi.Note(80, note.pitch, offset, offset + total_pitch_length)
                instr[instr_indices[note.instr]].notes.append(new_note)
                # instr.notes.append(note)
        offset += steps
    result.instruments.extend(instr)
    # result.instruments.append(instr)
    return result


@click.command()
@click.option("input_dir", "--input", "-i", type=click.Path(exists=True, file_okay=False), required=True)
@click.option("output_dir", "--output", "-o", type=click.Path(exists=True, file_okay=False), required=True)
@click.option("--note_count", "-count", default=4, type=int, show_default=True)
@click.option("--time_steps", "-time", default=0.125, type=float, show_default=True)
@click.option("--recursive", "-r", default=False, type=bool, show_default=True)
def main(input_dir: str,
         output_dir: str,
         note_count: int = 4,
         time_steps: float = 0.125,
         recursive: bool = False):
    click.echo(
        "Processing files from {} to {} with {} notes in {} steps...".format(input_dir, output_dir, note_count,
                                                                             time_steps))

    midis = load_midis_with_files(input_dir, recursive)
    for file, midi in midis:
        click.echo("Processing {}...".format(file))
        notes = get_note_values_from_midi(midi, time_steps, note_count)
        new_midi = create_midi(notes, time_steps)

        name = get_file_name(file)
        output = "{}_{}.mid".format(name, "reduced")
        if not recursive:
            output = os.path.join(output_dir, output)
        else:
            subdir = os.path.dirname(file)
            subdir = os.path.relpath(subdir, input_dir)
            subdir = get_and_create_folder_path(output_dir, subdir)
            output = os.path.join(subdir, output)
        click.echo("Saving {}...".format(output))
        new_midi.write(output)

    click.echo("Done.")


if __name__ == '__main__':
    main()
