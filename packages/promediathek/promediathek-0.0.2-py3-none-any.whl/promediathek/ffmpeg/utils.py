from tempfile import TemporaryDirectory
from time import strptime, mktime
from subprocess import run
from pathlib import Path
from os import PathLike
from shutil import move
from json import loads
from time import sleep

from lib.pakete.bestandspaket import VideoQuality, AudioQuality, SubtitleQuality
from lib.utils.logger import log
from lib.utils.threader import MultiThreader


def ffprobe(file: PathLike | str) -> dict:
    if not Path(file).is_file():
        raise RuntimeError(f'"{file}" is not a file')
    ffprobe_out = loads(run(['ffprobe', file, '-print_format', 'json', '-show_streams', '-show_format'], capture_output=True).stdout)
    return ffprobe_out


def ffprobe_hdr(file: PathLike | str) -> dict:
    if not Path(file).is_file():
        raise RuntimeError(f'"{file}" is not a file')
    ffprobe_out = loads(run(['ffprobe', file, '-print_format', 'json', '-show_streams', '-show_format', '-show_entries', 'side_data', '-read_intervals', '%+#1'], capture_output=True).stdout)
    return ffprobe_out


def get_video_quality(video_file: PathLike | str, ffprobe_out: dict = None) -> VideoQuality:
    if not ffprobe_out:
        ffprobe_out = ffprobe(video_file)

    try:
        for stream in ffprobe_out['streams']:
            if stream['codec_type'] != 'video':
                continue

            codec = stream['codec_tag_string']
            codec = codec.replace('[27][0][0][0]', 'avc1')
            if '[' in codec:
                raise RuntimeError(f'"{codec}" is unknown codec type.')

            bitrate = stream['bit_rate'] if 'bit_rate' in stream else ffprobe_out['format']['bit_rate']
            return VideoQuality(
                bitrate=int(bitrate),
                codec=codec,
                width=stream['width'],
                height=stream['height'],
            )

        raise RuntimeError(f"ffprobe failed to get Video Quality on: {video_file}")

    except KeyError:
        sleep(1)
        return get_video_quality(video_file)


def get_audio_quality(audio_file: PathLike | str) -> AudioQuality:
    ffprobe_out = ffprobe(audio_file)
    try:
        for stream in ffprobe_out['streams']:
            if stream['codec_type'] != 'audio':
                continue

            audio_quality = AudioQuality(
                language=Path(audio_file).stem,
                codec=stream['codec_name'],
                channels=stream['channels'],
                bandwidth=int(stream['bit_rate']),
                is_atmos='Dolby Atmos' in stream.get('profile', '')
            )

            return audio_quality

        raise RuntimeError(f"ffprobe failed to get Audio Quality on: {audio_file}")

    except KeyError:
        sleep(1)
        return get_audio_quality(audio_file)


def get_subtitle_quality(subtitle_file: PathLike | str) -> SubtitleQuality:
    return SubtitleQuality(
        language=Path(subtitle_file).stem.split('@')[-1],
        codec=Path(subtitle_file).suffix[1:],
        forced='forced' in Path(subtitle_file).stem.split('@')
    )


def get_audio_channel_count(audio_file: Path) -> int:
    ffprobe_out = ffprobe(audio_file)
    for stream in ffprobe_out['streams']:
        if stream['codec_type'] != 'audio':
            continue

        return stream['channels']

    raise RuntimeError(f"No Audio Streams found: {audio_file}")


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


def drm_cmd(drm_key) -> list[str]:
    if len(drm_key) == 32:
        return ['-decryption_key', drm_key]

    elif len(drm_key) == 8:
        return ['-activation_bytes', drm_key]

    return []


def test_keys(filepath: PathLike | str, drm_keys: list[str]) -> list[str]:
    for drm_key in drm_keys:
        cmd = ['ffmpeg', '-loglevel', 'error'] + drm_cmd(drm_key) + ['-i', filepath, '-t', '60', '-f', 'null', '/dev/null']
        ffmpeg_output = run(cmd, capture_output=True)
        if not ffmpeg_output.stderr:
            return [drm_key]
    return []


def mp4decrypt(filepath: PathLike | str, drm_keys: list[str]) -> Path:
    tmp_dir = TemporaryDirectory()
    tmp_path = Path(tmp_dir.name)

    test_file = tmp_path / 'test.mp4'
    for drm_key in drm_keys:
        mp4decrypt_out = run(['mp4decrypt', '--key', f"1:{drm_key}", filepath, test_file], capture_output=True)
        if mp4decrypt_out.returncode or check_for_errors(test_file):
            continue

        Path(filepath).unlink()
        return move(test_file, filepath)

    tmp_dir.cleanup()
    log("ERROR", f"Found no DRM key for: {filepath}")
    raise RuntimeError(f"Found no DRM key for: {filepath}")


def remove_drm(file: PathLike | str | list[PathLike | str], drm_keys: list[str]) -> Path | list[Path]:
    """
    Removes DRM from a file.
    :param file: Path to the file to remove DRM from OR list of paths.
    :param drm_keys: List of DRM keys to try.
    :return:
    """
    if isinstance(file, list):
        drm_threads = []
        with MultiThreader() as threader:
            for f in file:
                thread = threader.add_thread(remove_drm, file=f, drm_keys=drm_keys)
                drm_threads.append(thread)

        return [thread.result() for thread in drm_threads]

    # If ffmpeg can't find the key, test them all with mp4decrypt.
    drm_key = test_keys(file, drm_keys) or drm_keys
    return mp4decrypt(file, drm_key)
