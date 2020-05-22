"""
Separate randomly MIDI-files into train, valid and test folders
Separation happens evenly distributed
"""

import os
import random
import shutil

import click

from common import *


def get_sets(folder: str) -> List[List[str]]:
    files = get_files(folder, "mid")
    count = len(files)
    part_length = int(count / 3)
    if count % 3 != 0:
        part_length += 1

    result = []
    random.shuffle(files)
    i = 0
    tmp = []
    for file in files:
        if i == part_length:
            result.append(tmp)
            tmp = []
            i = 0
        tmp.append(file)
        i += 1
    result.append(tmp)
    assert len(result) == 3
    return result


def copy_file(origin: str, dest_folder: str):
    shutil.copy(origin, dest_folder)


def copy_sets(sets: List[List[str]], folder: str):
    subfolders = ["train", "test", "valid"]
    subfolders = [os.path.join(folder, subfolder) for subfolder in subfolders]
    for i, subfolder in enumerate(subfolders):
        click.echo("Copying {} files to {}".format(len(sets[i]), subfolder))
        if not os.path.exists(subfolder):
            os.mkdir(subfolder)
        for file in sets[i]:
            copy_file(file, subfolder)


@click.command()
@click.option("input_dir", "--input", "-i", type=click.Path(exists=True, file_okay=False), required=True)
@click.option("output_dir", "--output", "-o", type=click.Path(exists=True, file_okay=False), required=True)
def main(input_dir: str,
         output_dir: str):
    click.echo(
        "Processing files from {} to {}...".format(input_dir, output_dir))
    copy_sets(get_sets(input_dir), output_dir)
    click.echo("Done.")


if __name__ == '__main__':
    main()
