"""
Analysis of MIDI files and filtering MIDI files according to note count
tl;dr check if max 4 notes concurrently
"""

from math import floor
from typing import List, Dict
import numpy as np

from common import *

import click

from colorama import init, Fore, Style

init()

RANGE_SOPRAN = (60, 81)
RANGE_ALT = (52, 74)
RANGE_TENOR = (46, 69)
RANGE_BASS = (36, 66)

RANGE_VOICES = [
    ("sopran", RANGE_SOPRAN),
    ("alt", RANGE_ALT),
    ("tenor", RANGE_TENOR),
    ("bass", RANGE_BASS)
]


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
    note: pretty_midi.Note
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


def get_notes_from_midi(mid: pretty_midi.PrettyMIDI, steps: float) -> Dict[float, List[List[pretty_midi.Note]]]:
    result: Dict[float, List[List[pretty_midi.Note]]] = {}
    instr_count = len(mid.instruments)

    for instr_index, instr in enumerate(mid.instruments):
        extracted_notes = get_notes_from_instrument(instr, steps)
        for time, notes in extracted_notes.items():
            if time not in result:
                result[time] = [[] for _ in range(instr_count)]
            result[time][instr_index].extend(notes)
    return result


def get_pitch_ranges_from_instrument(notes: Dict[float, List[List[pretty_midi.Note]]], instr_index: int) -> Tuple[
    int, int]:
    pitch_min = 1000000
    pitch_max = 0
    note: pretty_midi.Note
    for time, instr in notes.items():
        for note in instr[instr_index]:
            pitch_min = min(pitch_min, note.pitch)
            pitch_max = max(pitch_max, note.pitch)
    return pitch_min, pitch_max


def get_concurrent_note_count(notes: Dict[float, List[List[pretty_midi.Note]]]) -> int:
    result_count = 0

    for time, instruments in notes.items():
        count = sum([len(instrument) for instrument in instruments])
        result_count = max(result_count, count)
    return result_count


def get_voice_likelihood(pitches: Tuple[int, int], voice: Tuple[int, int]) -> float:
    count = 0
    for pitch in range(pitches[0], pitches[1] + 1):
        if voice[0] <= pitch <= voice[1]:
            count += 1
    return count / (voice[1] - voice[0])


def get_voice_likelihood_of_instrument(notes: Dict[float, List[List[pretty_midi.Note]]], instr_index: int) -> \
        Dict[Tuple[str, Tuple[int, int]], float]:
    total_note_count = 0
    voice_notes_counts = {
        RANGE_VOICES[0]: 0,
        RANGE_VOICES[1]: 0,
        RANGE_VOICES[2]: 0,
        RANGE_VOICES[3]: 0
    }
    for time, instruments in notes.items():
        instr_notes = instruments[instr_index]
        total_note_count += len(instr_notes)

        for note in instr_notes:
            for voice_tuple in RANGE_VOICES:
                if is_in_range(note.pitch, voice_tuple[1][0], voice_tuple[1][1]):
                    voice_notes_counts[voice_tuple] += 1

    for voice_tuple in RANGE_VOICES:
        voice_notes_counts[voice_tuple] = (
                voice_notes_counts[voice_tuple] / total_note_count) if total_note_count > 0 else 0
    return voice_notes_counts


def get_voices(pitches: Tuple[int, int]) -> List[Tuple[str, float]]:
    result = []
    for voice in RANGE_VOICES:
        result.append((voice[0], get_voice_likelihood(pitches, voice[1])))
    return result


def extract_instrument(notes: Dict[float, List[List[pretty_midi.Note]]], instr_index: int,
                       result: Dict[float, List[List[pretty_midi.Note]]] = None) \
        -> Dict[float, List[List[pretty_midi.Note]]]:
    if result is None:
        result = {}
    for time, instruments in notes.items():
        if time not in result:
            result[time] = [notes[time][instr_index]]
        else:
            result[time].append(notes[time][instr_index])
    return result


def analyse_file(file: Tuple[str, pretty_midi.PrettyMIDI], note_count: int, time_steps: float) -> bool:
    notes = get_notes_from_midi(file[1], time_steps)
    concurrent_count = get_concurrent_note_count(notes)
    print_colored("{} has a maximum of {} concurrent notes.".format(file[0], concurrent_count), Fore.RED,
                  concurrent_count > note_count)

    instr: pretty_midi.Instrument
    filtered_voice_count = 0
    filtered_instr = None
    for instr_index in range(len(file[1].instruments)):
        instr = file[1].instruments[instr_index]
        pitches = get_pitch_ranges_from_instrument(notes, instr_index)
        likelihood = get_voice_likelihood_of_instrument(notes, instr_index)

        voices = [(voice_tuple[0], val) for voice_tuple, val in likelihood.items()]
        print_colored("{}:{}({}) with {},{} has voice likelihood: {}".format(
            file[0], instr.name,
            instr.program,
            pitches[0], pitches[1],
            ", ".join([
                f"{voice[0]}: {voice[1]:.2f}"
                for voice in
                voices])
        ), Fore.BLUE)
        filtered_voices = [voice[0] for voice in voices if voice[1] > 0.9]
        if len(filtered_voices) > 0:
            print_colored("{}:{}({}) with {},{} has the following possible voices: {}".format(
                file[0], instr.name,
                instr.program,
                pitches[0], pitches[1],
                ", ".join(filtered_voices)
            ), Fore.GREEN)
            filtered_voice_count += 1
            filtered_instr = extract_instrument(notes, instr_index, filtered_instr)
        else:
            print_colored("{}:{}({}) with {},{} has none of the requested voices.".format(
                file[0], instr.name,
                instr.program,
                pitches[0], pitches[
                    1]
            ), Fore.LIGHTRED_EX)

    print_colored("{} has a maximum of {} recognized voices.".format(file[0], filtered_voice_count),
                  Fore.RED, filtered_voice_count > note_count)
    if filtered_instr is not None:
        concurrent_count = get_concurrent_note_count(filtered_instr)
        print_colored(
            "{} has a maximum of {} concurrent notes in the filtered instruments.".format(file[0], concurrent_count),
            Fore.RED, concurrent_count > note_count
        )

    return concurrent_count == note_count


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
        "Analysing files from {} to {} with {} notes in {} steps...".format(input_dir, output_dir, note_count,
                                                                            time_steps))
    midis = load_midis_with_files(input_dir)
    for file, midi in midis:
        click.echo("\n\nAnalysing {}...".format(file))
        if analyse_file((file, midi), note_count, time_steps):
            name = get_file_name(file)
            output = "{}_{}.mid".format(name, "analysed")
            output = os.path.join(output_dir, output)
            click.echo("Saving {}...".format(output))
            midi.write(output)

    click.echo("Done.")


if __name__ == '__main__':
    main()
