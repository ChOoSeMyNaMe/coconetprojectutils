import os
from typing import List

import click
import pretty_midi

from common import load_midis_with_files, get_file_name


def create_sub_midi(midi: pretty_midi.PrettyMIDI, start_time: float, end_time: float) -> pretty_midi.PrettyMIDI:
    result = pretty_midi.PrettyMIDI()

    for instr in midi.instruments:
        subInstr = pretty_midi.Instrument(instr.program, instr.is_drum, instr.name)
        for note in instr.notes:
            if note.start >= start_time and note.end < end_time:
                subInstr.notes.append(note)
        result.instruments.append(subInstr)
    return result


def split_midi(midi: pretty_midi.PrettyMIDI,
               optimal_part_count: int = 5,
               min_length: float = 15,
               max_length: float = 90) -> List[pretty_midi.PrettyMIDI]:
    total_length = midi.get_end_time()
    part_length = total_length / optimal_part_count
    part_length = max(min_length, part_length)
    part_length = min(max_length, part_length)

    result = []
    time = 0.0
    while time < total_length:
        part_end = min(total_length, time + part_length)
        part = create_sub_midi(midi, time, part_end)
        result.append(part)
        time += part_length
    return result


def split_all_midis_from_dir(dir: str, output_dir: str,
                             optimal_part_count: int = 5,
                             min_length: float = 15,
                             max_length: float = 90):
    click.echo("Loading files from {}...".format(dir))
    midis = load_midis_with_files(dir)

    click.echo("Processing data...")
    for file, midi in midis.items():
        click.echo("Processing {}...".format(file))
        parts = split_midi(midi, optimal_part_count, min_length, max_length)
        name = get_file_name(file)
        click.echo("Saving {}...".format(file))
        for i in range(len(parts)):
            output = "{}_{}.mid".format(name, i)
            output = os.path.join(output_dir, output)
            midi.write(output)


@click.command()
@click.option("input_dir", "--input", "-i", type=click.Path(exists=True, file_okay=False), required=True)
@click.option("output_dir", "--output", "-o", type=click.Path(exists=True, file_okay=False), required=True)
@click.option("--optimal_part_count", "-count", default=5, type=int, show_default=True)
@click.option("--min_length", "-min", default=15, type=float, show_default=True)
@click.option("--max_length", "-max", default=90, type=float, show_default=True)
def main(input_dir: str,
         output_dir: str,
         optimal_part_count: int = 5,
         min_length: float = 15,
         max_length: float = 90):
    click.echo(
        "Processing files from {} to {} with {}(min: {}, max: {})...".format(input_dir, output_dir, optimal_part_count,
                                                                             min_length, max_length))
    split_all_midis_from_dir(input_dir, output_dir, optimal_part_count, min_length, max_length)
    click.echo("Done.")


if __name__ == '__main__':
    main()
