"""
Dieses Skript nimmt einen Ordner mit Midi-Dateien, filtert diese nach maximal 4 gleichzeitigen Stimmen, teilt die Stuecke in kleinere Teile auf,
verteilt diese gleichmaessig auf train/test/valid-Ordner und erstellt daraus dann Trainingsdateien.
--input sollte vom mit dem Namen des Kuenstlers enden, also zum Beispiel pfad/zum/<kuenstler>
--output sollte irgendein anderer Ordner sein, dabei werden die einzelnen Schritte und das Endergebnis in output/<kuenstler> gespeichert
"""


import os

import click

import common
import check_satb as check
import split_midi as split
import separate_midis as sep
import process_midi as process


def filter_midis(input_dir: str, output_dir: str,
                 note_count: int = 4,
                 time_steps: float = 0.125) -> str:
    suboutput = common.get_and_create_folder_path(output_dir, "filtered")
    click.echo(
        "Filtering files from {} to {} with {} notes in {} steps...".format(input_dir, suboutput, note_count,
                                                                            time_steps))
    midis = common.load_midis_with_files(input_dir)
    for file, midi in midis:
        click.echo("\n\nAnalysing {}...".format(file))
        if check.analyse_file((file, midi), note_count, time_steps):
            name = common.get_file_name(file)
            output = "{}.mid".format(name)
            output = os.path.join(suboutput, output)
            click.echo("Saving {}...".format(output))
            midi.write(output)

    return suboutput


def split_midis(input_dir: str, output_dir: str,
                min_length: float = 15,
                max_length: float = 90) -> str:
    suboutput = common.get_and_create_folder_path(output_dir, "splitted")
    click.echo(
        "Splitting files from {} to {} with min: {}, max: {}...".format(input_dir, suboutput,
                                                                        min_length, max_length))
    split.split_all_midis_from_dir(input_dir, suboutput, min_length, max_length)
    return suboutput


def separate_midis(input_dir: str, output_dir: str) -> str:
    suboutput = common.get_and_create_folder_path(output_dir, "sets")
    click.echo(
        "Separating files from {} into {}...".format(input_dir, suboutput))
    sep.copy_sets(sep.get_sets(input_dir), suboutput)
    return suboutput


def transform_midis(input_dir: str, output_dir: str,
                    steps: float,
                    desired_note_count: int):
    train_dir = os.path.join(input_dir, "train")
    test_dir = os.path.join(input_dir, "test")
    valid_dir = os.path.join(input_dir, "valid")

    click.echo("Transforming files with steps={} and note_count={}...".format(steps, desired_note_count))
    notes = process.build_trainingsdata(
        train_dir,
        test_dir,
        valid_dir,
        steps,
        desired_note_count
    )
    click.echo("Saving data...")
    filename = os.path.basename(output_dir)
    process.save_trainingsdata(notes, os.path.join(output_dir, filename))


@click.command()
@click.option("input_dir", "--input", "-i", type=click.Path(exists=True, file_okay=False), required=True, prompt=True)
@click.option("output_dir", "--output", "-o", type=click.Path(exists=True, file_okay=False), required=True)
@click.option("--note_count", "-count", default=4, type=int, show_default=True)
@click.option("--time_steps", "-time", default=0.125, type=float, show_default=True)
@click.option("--min_length", "-min", default=15, type=float, show_default=True)
@click.option("--max_length", "-max", default=90, type=float, show_default=True)
def main(input_dir: str,
         output_dir: str,
         note_count: int = 4,
         time_steps: float = 0.125,
         min_length: float = 15,
         max_length: float = 90):
    suboutput = common.get_and_create_folder_path(output_dir, os.path.basename(input_dir))
    click.echo(f"Converting {input_dir} with {note_count} notes, {time_steps}s steps and piece lengths "
               f"of {min_length} to {max_length} and outputting into {suboutput}...")
    filtered_folder = filter_midis(input_dir, suboutput, note_count, time_steps)
    splitted_folder = split_midis(filtered_folder, suboutput, min_length, max_length)
    set_folder = separate_midis(splitted_folder, suboutput)
    transform_midis(set_folder, suboutput, time_steps, note_count)
    click.echo("Done.")


if __name__ == '__main__':
    main()
