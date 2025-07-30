from time import strptime, mktime
from subprocess import run
from pathlib import Path
from os import PathLike
from json import loads

from utils import log


def ffprobe(file: PathLike | str) -> dict:
    if not Path(file).is_file():
        raise RuntimeError(f'"{file}" is not a file')
    ffprobe_out = loads(run(['ffprobe', file, '-print_format', 'json', '-show_streams', '-show_format'], capture_output=True).stdout)
    return ffprobe_out


def get_duration(ffprobe_data: dict) -> float:
    if 'format' in ffprobe_data:
        ffprobe_data = ffprobe_data['format']

    duration = 0
    if 'duration' in ffprobe_data:
        duration = ffprobe_data['duration']
    elif 'tags' in ffprobe_data and 'DURATION' in ffprobe_data['tags']:
        duration = ffprobe_data['tags']['DURATION']

    try:
        duration = float(duration)

    except ValueError:
        duration_seconds = duration.split('.')[0]
        duration_milliseconds = float('0.' + duration.split('.')[1])
        duration = mktime(strptime(duration_seconds, '%H:%M:%S')) + 2208992400 + duration_milliseconds

    return duration


def check_for_errors(video_file, ignore_duration: bool = False) -> int:
    ffprobe_out = ffprobe(video_file)
    if ffprobe_out['format']['format_name'] == 'webvtt':
        print("VERBOSE", "Subtitles can't be checked for errors.")
        return 0

    ffmpeg_out = run([
        'ffmpeg', '-y', '-loglevel', 'error',
        '-i', video_file, '-c', 'copy',
        '-f', 'null', '/dev/null'
    ], capture_output=True)

    video_duration = get_duration(ffprobe_out)
    stream_durations = [get_duration(stream) for stream in ffprobe_out['streams']]

    if ffmpeg_out.returncode:
        log("ERROR", f'FFmpeg Check Error failed. {video_file}')
        return 1

    elif ffmpeg_out.stderr:
        log("ERROR", f'FFmpeg Check Error failed. {video_file}')
        return 2

    if not ignore_duration:
        for stream in [stream for stream in stream_durations if video_duration - stream > 1]:
            log("ERROR", f'Duration missmatch {video_duration=} > {stream=}')
            return 3

    ffmpeg_out = run([
        'ffmpeg', '-y', '-loglevel', 'error',
        '-i', video_file, '-t', '180',
        '-f', 'null', '/dev/null'
    ], capture_output=True)

    if ffmpeg_out.returncode:
        log("ERROR", f'FFmpeg Check Error failed. {video_file}')
        return 4

    elif ffmpeg_out.stderr:
        log("ERROR", f'FFmpeg Check Error failed. {video_file}')
        return 5

    ffmpeg_out = run([
        'ffmpeg', '-y', '-loglevel', 'error',
        '-sseof', '-180', '-i', video_file,
        '-f', 'null', '/dev/null'
    ], capture_output=True)
    if ffmpeg_out.returncode:
        log("ERROR", f'FFmpeg Check Error failed. {video_file}')
        return 6

    elif ffmpeg_out.stderr:
        log("ERROR", f'FFmpeg Check Error failed. {video_file}')
        return 7

    return 0
