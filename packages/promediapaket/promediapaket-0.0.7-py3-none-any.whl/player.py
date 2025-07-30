#!/usr/bin/env python3
from os import PathLike

from promediapaket import ProMediaPaket
from subprocess import run
from sys import argv


def play_pmp(pmp_path: PathLike | str):
    pmp = ProMediaPaket.fast_open(pmp_path)
    video_filepath = pmp.tmp_path / pmp.metadata.video_filepath
    audio_filepaths = [pmp.tmp_path / "audios" / audio_file for audio_file in pmp.metadata.audio_filepaths]
    subtitle_filepaths = [pmp.tmp_path / "subtitles" / subtitle_file for subtitle_file in pmp.metadata.subtitle_filepaths]

    mpv_cmd = [
        "mpv", "-vo=gpu-next", video_filepath
    ]
    [mpv_cmd.append(f"--audio-file={audio_file}") for audio_file in audio_filepaths]
    [mpv_cmd.append(f"--sub-file={subtitle_file}") for subtitle_file in subtitle_filepaths]

    run(mpv_cmd)


if __name__ == '__main__':
    if len(argv) != 2:
        print('Usage: player.py <file>')
        exit(1)

    play_pmp(argv[1])
