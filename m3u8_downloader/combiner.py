from os import system, remove
from .utils import vprint


def combine_segments(
    filelist_path: str,
    output_file: str,
    ffmpeg_path: str = "ffmpeg",
    remove_filelist: bool = True,
):
    vprint("Combining segments...")

    system(f"{ffmpeg_path} -f concat -safe 0 -i {filelist_path} -c copy {output_file}")

    if remove_filelist:
        vprint(f"Removing {filelist_path}...")
        remove(filelist_path)

    vprint("Combining segments finished...")
