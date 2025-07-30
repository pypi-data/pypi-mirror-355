from pathlib import Path
from shutil import copy
from tempfile import TemporaryDirectory
from flask import abort, jsonify, send_file

from promediapaket import ProMediaPaket

from lib.ffmpeg import convert_audio, get_video_quality, get_audio_quality, get_subtitle_quality
from lib.ffmpeg.ffmpeg import remove_side_data
from lib.ffmpeg.utils import ffprobe, get_duration
from lib.pakete.bestandspaket import Bestandspaket
from lib.pakete.sammelpaket import Sammelpaket
from lib.utils.db import ProDB

from lib.web import app, web_dirs, WebTmpDir


def read_bestandspaket(provider: str, provider_id: str) -> Bestandspaket:
    sammelpaket = Sammelpaket.from_id(provider, provider_id)
    if not ProDB().already_downloaded(sammelpaket):
        abort(404)

    bestandspaket = ProDB().read_bestandspaket(sammelpaket)
    return bestandspaket


def clear_web_dirs() -> None:
    [web_dirs.remove(web_dir) for web_dir in web_dirs if web_dir.expired]


@app.route("/api/bestandspaket/<string:provider>/<string:provider_id>", methods=["GET"])
def get_bestandspaket(provider: str, provider_id: str):
    return jsonify(read_bestandspaket(provider, provider_id).dict)


@app.route("/api/bestandspaket/all", methods=["GET"])
def get_all_bestandspakete():
    bestandspakete = ProDB().read_all_bestandspakete()
    return [bestandspaket.dict for bestandspaket in bestandspakete]


@app.route("/api/bestandspaket/all_small", methods=["GET"])
def get_all_bestands_json():
    """
    Uses only one DB access and has an O(1) time complexity. Use if full Bestandspaket is not required.
    :return: Dict with {provider:provider, id: provider_id, pmp_path: Path to pmp file}
    """
    bestands_json = ProDB().read_all_bestands_json()
    return bestands_json


@app.route("/api/pmp/metadata/<string:provider>/<string:provider_id>", methods=["GET"])
def get_pmp_metadata(provider: str, provider_id: str):
    metadata = ProMediaPaket.metadata(read_bestandspaket(provider, provider_id).pmp_path)
    return jsonify(metadata.dict)


@app.route("/api/pmp/video/<string:provider>/<string:provider_id>/<string:audio_language>/<string:subtitle_language>", methods=["GET"])
def get_pmp_video(provider: str, provider_id: str, audio_language: str, subtitle_language: str):
    """
    Returns a Video Object with url, audio_language, and subtitle_language.
    :param provider: The Provider Name.
    :param provider_id: The ID used by the Provider.
    :param audio_language: The Audio Language to use.
    :param subtitle_language: The Subtitle Language to use can be prefixed with 'forced@' if available.
    :return: JSON str
    """
    clear_web_dirs()

    pmp = ProMediaPaket.fast_open(read_bestandspaket(provider, provider_id).pmp_path)
    video_file = pmp.tmp_path / pmp.metadata.video_filepath
    video_ffprobe = ffprobe(video_file)
    video_info = get_video_quality(video_file, ffprobe_out=video_ffprobe)

    tmp_dir = TemporaryDirectory()
    tmp_path = Path(tmp_dir.name)

    if video_info.codec != "av01":
        video_file = Path(copy(video_file, tmp_path))
        remove_side_data(video_file)

    if not any([audio_language == audio.split('.')[0] for audio in pmp.metadata.audio_filepaths]):
        abort(404, "Audio Language not found.")

    audio_file = pmp.tmp_path / 'audios' / [audio for audio in pmp.metadata.audio_filepaths if audio_language == audio.split('.')[0]][0]
    audio_info = get_audio_quality(audio_file)

    if audio_info.codec != "opus":
        # Fast Encoding to Opus, because of ec-3
        audio_file = Path(copy(audio_file, tmp_path))
        audio_file = convert_audio(audio_file, compression_level=0)

    subtitle_file = None
    subtitle_info = None
    if subtitle_language.lower() != 'none':
        if not any([subtitle_language == subtitle.split('.')[0] for subtitle in pmp.metadata.subtitle_filepaths]):
            abort(404, "Subtitle Language not found.")

        subtitle_file = pmp.tmp_path / 'subtitles' / [subtitle for subtitle in pmp.metadata.subtitle_filepaths if subtitle_language == subtitle.split('.')[0]][0]
        subtitle_info = get_subtitle_quality(subtitle_file).__dict__

    data = {
        'video': str(video_file.absolute()),
        'video_info': video_info.__dict__,
        'audio': str(audio_file.absolute()),
        'audio_info': audio_info.__dict__,
        'subtitle': str(subtitle_file.absolute()) if subtitle_file else None,
        'subtitle_info': subtitle_info
    }

    # Prevent Garbage Collector
    web_dirs.append(WebTmpDir(pmp.tmp_dir, expiration_time=get_duration(video_ffprobe['format'])*2, extra_data=pmp))
    web_dirs.append(WebTmpDir(tmp_dir, expiration_time=get_duration(video_ffprobe['format'])*2))

    return data


@app.route("/tmp/<path:tmp_path>", methods=["GET"])
def get_tmp(tmp_path: str):
    full_path = Path('/tmp', tmp_path).resolve()

    if str(full_path.parents[-2]) != '/tmp':
        abort(451)

    if str(full_path.parents[-3]) not in [web_dir.tempdir.name for web_dir in web_dirs]:
        abort(404)

    return send_file(full_path)
