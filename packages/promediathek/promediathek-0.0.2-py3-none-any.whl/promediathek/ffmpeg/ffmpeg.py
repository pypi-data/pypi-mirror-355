from os import PathLike
from pathlib import Path
from shutil import move
from subprocess import run, Popen, PIPE
from tempfile import TemporaryDirectory

from lib.ffmpeg import check_for_errors
from lib.ffmpeg.utils import ffprobe, get_duration
from lib.utils.logger import log
from lib.pakete.progresspaket import ConvertProgresspaket


def read_until_newline(readable) -> str:
    line = b""
    while (char := readable.read(1)) not in (b'\n', b'\r', b''):
        line += char
    return line.decode('utf-8')


def parse_ffmpeg_frame_line(line: str) -> dict:
    ffmpeg_data = {}
    line_split = line.split('=')
    last_key = line_split[0]
    for line_data in line_split[1:]:
        ffmpeg_data[last_key] = line_data.rsplit(maxsplit=1)[0].strip()
        last_key = line_data.rsplit(maxsplit=1)[-1].strip()

    return ffmpeg_data


def parse_time(timestamp: str) -> float:
    seconds = 0
    seconds += int(timestamp.split(':')[0]) * 60*60
    seconds += int(timestamp.split(':')[1]) * 60
    seconds += int(timestamp.split(':')[2].split('.')[0])
    seconds += float(timestamp.split('.')[1]) / 100
    return seconds


def convert_video(video_file: PathLike | str, progresspaket: ConvertProgresspaket = None) -> Path:
    """
    Converts the video in place to AV1 if not already.
    :param progresspaket:
    :param video_file:
    :return: The same as video_file or None if an error occurred
    """
    video_file = Path(video_file)

    progresspaket = progresspaket or ConvertProgresspaket('None')
    progress_list_index = len(progresspaket.progress_list)
    progresspaket.progress_list.append(0)

    ffprobe_data = ffprobe(video_file)
    stream_data = ffprobe_data['streams'][0]
    video_duration = get_duration(ffprobe_data=ffprobe_data)

    video_codec = stream_data['codec_name']
    if video_codec == 'av1':
        return video_file

    temp_dir = TemporaryDirectory()
    temp_file = Path(temp_dir.name) / video_file.name
    crf = 26
    ffmpeg_out = Popen([
        'ffmpeg', '-hide_banner',
        '-i', video_file,
        '-map', '0:V',
        '-metadata:s:v:0', 'language=',
        '-c:V', 'libsvtav1',
        '-crf', f"{crf}",
        '-preset', '6',
        '-pix_fmt', 'yuv420p10le',
        '-movflags', 'faststart',
        '-svtav1-params', f'tune=2:fast-decode=1:enable-qm=1:qm-min=0:enable-variance-boost=1:variance-boost-strength=2',
        temp_file
    ], start_new_session=False, stdout=PIPE, stderr=PIPE)

    while ffmpeg_out.poll() is None:
        ffmpeg_line = read_until_newline(ffmpeg_out.stderr)
        if not ffmpeg_line.startswith('frame='):
            continue

        ffmpeg_progress = parse_ffmpeg_frame_line(ffmpeg_line)
        if ffmpeg_progress['speed'] == 'N/A':
            continue

        convert_time = parse_time(ffmpeg_progress['time'])
        progresspaket.progress_list[progress_list_index] = convert_time / video_duration
        progresspaket.convert_speed = float(ffmpeg_progress['speed'].replace('x', ''))

    if ffmpeg_out.returncode:
        log('ERROR', f"FFmpeg Video Conversion failed: {video_file}")
        raise RuntimeError(f"Video conversion failed: {video_file}")

    video_file.unlink()
    move(temp_file, video_file)
    temp_dir.cleanup()
    return video_file


def convert_audio(audio_file: PathLike | str, compression_level: int = 10) -> Path:
    audio_file = Path(audio_file)
    stream_data = ffprobe(audio_file)['streams']

    audio_stream_data = None
    for stream in stream_data:
        if stream['codec_type'] == 'audio':
            audio_stream_data = stream
            break

    if audio_stream_data is None:
        raise RuntimeError(f"No Audio in audio file: {audio_file}")

    audio_codec = audio_stream_data['codec_name']
    audio_channels = audio_stream_data['channels']
    if audio_codec == 'opus':
        return audio_file

    new_bitrate = [0, 64, 128, 128, 128, 256, 256, 256, 320]
    if audio_channels > len(new_bitrate) - 1:
        log('ERROR', f"More than {len(new_bitrate) - 1} channels in audio file: {audio_file}")
        raise ValueError

    new_bitrate = new_bitrate[audio_channels]

    temp_dir = TemporaryDirectory()
    temp_file = Path(temp_dir.name) / audio_file.name
    ffmpeg_out = run([
        'ffmpeg', '-i', audio_file,
        '-map', '0:a',
        '-movflags', 'faststart',
        '-c:a', 'libopus',
        '-compression_level', f"{compression_level}",
        '-ac', f'{audio_channels}',
        '-b:a', f'{new_bitrate}k',
        temp_file
    ], capture_output=True)

    if ffmpeg_out.returncode:
        log('ERROR', ffmpeg_out.stderr.decode('utf-8'))
        raise RuntimeError(f"Audio conversion failed: {audio_file}")

    audio_file.unlink()
    move(temp_file, audio_file)
    temp_dir.cleanup()
    return audio_file


def convert_image(image_path: PathLike | str) -> Path:
    image_file = Path(image_path)
    if image_file.suffix == '.avif':
        return image_file

    tmp_dir = TemporaryDirectory()
    tmp_path = Path(tmp_dir.name)

    image_info = ffprobe(image_file)
    if not image_info:
        log("WARN", f"No image data found, retrying with file extension: {image_path}")
        file_output = run(['file', '--extension', '--brief', image_file], capture_output=True).stdout.decode('utf-8').strip()
        image_file = image_file.rename(image_file.with_suffix('.' + file_output.split('/')[0]))
        image_info = ffprobe(image_file)

    image_width = image_info['streams'][0]['width']
    image_height = image_info['streams'][0]['height']
    if image_width % 2 or image_height % 2:
        log("WARN", f"Thumbnail size is uneven: {image_width}x{image_height}")
        image_width -= image_width % 2
        image_height -= image_height % 2

    out_file = tmp_path / image_file.with_suffix('.avif').name
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", image_file,
        "-map", "0:v",
        "-preset", "5",
        "-crf", "18",
        "-c:v", "libsvtav1",
        '-pix_fmt', 'yuv420p10le',
        '-vf', f"crop={image_width}:{image_height}",
        "-svtav1-params", "avif=1:tune=0:fast-decode=1:enable-qm=1:qm-min=0",
        out_file
    ]

    ffmpeg_output = run(ffmpeg_cmd, capture_output=True)
    if ffmpeg_output.returncode:
        raise RuntimeError(ffmpeg_output.stderr.decode('utf-8'))

    image_file.unlink()
    move(out_file, image_file.with_suffix('.avif'))
    tmp_dir.cleanup()
    return image_file.with_suffix('.avif')


def concat_containers(container_files: list[PathLike | str], filestem: str = None) -> Path:
    if not container_files:
        log("ERROR", "No container files to concat.")
        raise RuntimeError("No container files to concat.")

    tmp_dir = TemporaryDirectory()
    tmp_path = Path(tmp_dir.name)

    for container_file in container_files:
        run(['ffmpeg', '-i', container_file, '-strict', 'unofficial', '-c', 'copy', tmp_path / f"copy-{Path(container_file).name}"], capture_output=True)
        Path(container_file).unlink()

    ffmpeg_concat_file = tmp_path / f"ffmpeg_concat.txt"
    ffmpeg_concat_file.write_text('\n'.join([f"file '{tmp_path / ("copy-" + Path(file).name)}'" for file in container_files]))

    combined_file = (tmp_path / "combined").with_suffix(Path(container_files[0]).suffix)
    if filestem:
        combined_file = combined_file.with_stem(filestem)

    ffmpeg_cmd = run([
        "ffmpeg", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", ffmpeg_concat_file, '-strict', 'unofficial', "-c", "copy", "-y", combined_file
    ], capture_output=True)

    if ffmpeg_cmd.returncode:
        tmp_dir.cleanup()
        log("ERROR", ffmpeg_cmd.stderr.decode('utf-8'))
        raise RuntimeError("ffmpeg concat failed 1.")

    if ffmpeg_cmd.stderr:
        tmp_dir.cleanup()
        log("ERROR", ffmpeg_cmd.stderr.decode('utf-8'))
        raise RuntimeError("ffmpeg concat failed 2.")

    if check_for_errors(combined_file):
        tmp_dir.cleanup()
        log("ERROR", "Container concat failed.")
        raise RuntimeError("ffmpeg concat failed 3.")

    combined_file_target = Path(container_files[0]).with_name(combined_file.name)
    move(combined_file, combined_file_target)
    tmp_dir.cleanup()
    return combined_file_target


def remove_side_data(file_path: PathLike | str) -> Path:
    """
    Used for removing DRM side information because Firefox doesn't like it.
    :param file_path:
    :return:
    """
    tmp_dir = TemporaryDirectory()
    tmp_path = Path(tmp_dir.name)

    out_file = tmp_path / Path(file_path).name
    ffmpeg_output = run([
        'ffmpeg',
        '-i', file_path,
        '-c', 'copy',
        out_file.with_suffix('.mkv')
    ], capture_output=True)
    if ffmpeg_output.returncode:
        raise RuntimeError(ffmpeg_output.stderr.decode('utf-8'))

    ffmpeg_output = run([
        'ffmpeg',
        '-i', out_file.with_suffix('.mkv'),
        '-c', 'copy',
        out_file
    ], capture_output=True)
    if ffmpeg_output.returncode:
        raise RuntimeError(ffmpeg_output.stderr.decode('utf-8'))

    Path(file_path).unlink()
    move(out_file, file_path)
    return Path(file_path)
