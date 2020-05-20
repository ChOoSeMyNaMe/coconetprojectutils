"""Testing note reduction but it's not really good working"""

from math import floor
from typing import List, Dict
import numpy as np

from common import *

import click

def f_sopran(values: List[int]) -> int:
    return max(values)

def f_alt(values: List[int]) -> int:
    upper = max(values)
    lower = min(values)
    value = upper - lower
    value = value * 0.66
    value = int(value + lower)
    return value

def f_tenor(values: List[int]) -> int:
    upper = max(values)
    lower = min(values)
    value = upper - lower
    value = value * 0.33
    value = int(value + lower)
    return value

def f_bass(values: List[int]) -> int:
    return min(values)

RANGE_SOPRAN = [60, 81]
RANGE_ALT = [52, 74]
RANGE_TENOR = [46, 69]
RANGE_BASS = [36, 66]

RANGE_VOICES = [RANGE_SOPRAN, RANGE_ALT, RANGE_TENOR, RANGE_BASS]
FUNCTION_VOICES = [f_sopran, f_alt, f_tenor, f_bass]

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


def voice_contains(voice: List[int], note: int) -> bool:
    return voice[0] <= note <= voice[1]


def list_diff(a: List[any], b: List[any]) -> List[any]:
    result = []
    for item in a:
        if item not in b:
            result.append(item)
    return result


def get_voices_from_notelist(notes: List[int]) -> List[List[int]]:
    result = []
    for voice_index in range(len(RANGE_VOICES)):
        filtered_voice = []
        for note in notes:
            if note is not None and voice_contains(RANGE_VOICES[voice_index], note):
                filtered_voice.append(note)
        filtered_voice.sort()
        result.append(filtered_voice)
    # filtered_result = []
    # for i in range(len(RANGE_VOICES)):
    #     filtered_result.append(list_diff(result[i], result[(i + 1) % len(RANGE_VOICES)]))
    # return filtered_result
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


def avg(array: List[int]) -> int:
    return int(floor(sum(array) / len(array)))


def normalize_notelists(notes: List[int], desired_note_count: int) -> List[int]:
    if len(notes) == desired_note_count:
        return notes

    voices = get_voices_from_notelist(notes)
    note_count_per_voice = int(floor(len(RANGE_VOICES) / desired_note_count))

    result = []
    voice_index = 0
    for voice in voices:
        if note_count_per_voice > len(voice):
            result.extend(voice)
            missing = note_count_per_voice - len(voice)
            for _ in range(missing):
                result.append(None)
        else:
            splits = split_array(voice, note_count_per_voice)
            assert len(splits) == note_count_per_voice
            for split in splits:
                # value = avg(split)
                value = FUNCTION_VOICES[voice_index](split)
                result.append(value)
        voice_index += 1

    return result


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


def consume_further_notes(notes: List[List[int]], offset: int, pitch: int) -> int:
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


def create_midi(notes: List[List[int]], steps: float) -> pretty_midi.PrettyMIDI:
    result = pretty_midi.PrettyMIDI(initial_tempo=80)
    offset = 0
    # instr = [pretty_midi.Instrument(i) for i in range(len(RANGE_VOICES))]
    instr = pretty_midi.Instrument(0)
    for moment_index in range(len(notes)):
        for pitch_index in range(len(notes[moment_index])):
            pitch = notes[moment_index][pitch_index]
            if pitch is not None:
                total_pitch_length = consume_further_notes(notes, moment_index + 1, pitch) + 1
                total_pitch_length *= steps
                note = pretty_midi.Note(80, pitch, offset, offset + total_pitch_length)
                # instr[pitch_index].notes.append(note)
                instr.notes.append(note)
        offset += steps
    # result.instruments.extend(instr)
    result.instruments.append(instr)
    return result


@click.command()
@click.option("input_dir", "--input", "-i", type=click.Path(exists=True, file_okay=False), required=True)
@click.option("output_dir", "--output", "-o", type=click.Path(exists=True, file_okay=False), required=True)
@click.option("--note_count", "-count", default=4, type=int, show_default=True)
@click.option("--time_steps", "-time", default=0.125, type=float, show_default=True)
def main(input_dir: str,
         output_dir: str,
         note_count: int = 4,
         time_steps: float = 0.125):
    click.echo(
        "Processing files from {} to {} with {} notes in {} steps...".format(input_dir, output_dir, note_count,
                                                                             time_steps))

    midis = load_midis_with_files(input_dir)
    for file, midi in midis:
        click.echo("Processing {}...".format(file))
        notes = get_note_values_from_midi(midi, time_steps, note_count)
        new_midi = create_midi(notes, time_steps)

        name = get_file_name(file)
        output = "{}_{}.mid".format(name, "reduced")
        output = os.path.join(output_dir, output)
        click.echo("Saving {}...".format(output))
        new_midi.write(output)

    click.echo("Done.")


if __name__ == '__main__':
    main()
