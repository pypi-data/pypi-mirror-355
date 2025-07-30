from pathlib import Path
from argparse import ArgumentParser
from time import sleep

from promediapaket import ProMediaPaket, EpisodeMetadata

from lib.pakete.bestandspaket import Bestandspaket
from lib.ffmpeg import convert_video, convert_audio, get_video_quality, get_subtitle_quality, get_audio_quality, convert_image
from lib.pakete.progresspaket import ConvertProgresspaket
from lib.utils.threader import MultiThreader
from lib.utils.db import ProDB
from lib.utils.cli import ProCLI, CLIThreader
from lib.utils.logger import enable_console_log, log

enable_console_log()

convert_progress = {
    'waiting_download': 'Warte aufs Netzwerk',
    'downloading': 'Lade vom Speicher',
    'waiting_convert': 'Warte vorm Konvertieren.',
    'converting': 'Konvertiere',
    'saving': 'Speichere zum Speicher',
    'error': 'Fehler beim Konvertieren'
}

progresspakete: list[ConvertProgresspaket] = []
cli = ProCLI()


def convert_bestandspaket(bestandspaket: Bestandspaket) -> Bestandspaket:
    progresspaket = ConvertProgresspaket(bestandspaket.id)
    progresspakete.append(progresspaket)
    cli.add_progresspaket(progresspaket)

    print("Converting:", bestandspaket.pmp_path)
    try:
        if args.network_limit:
            while args.network_limit <= len([pp for pp in progresspakete if pp.status == convert_progress['downloading']]):
                progresspaket.status = convert_progress['waiting_download']
                sleep(0.1)

        progresspaket.status = convert_progress['downloading']
        pmp = ProMediaPaket.open(bestandspaket.pmp_path)

        while args.convert_limit <= len([pp for pp in progresspakete if pp.status == convert_progress['converting']]):
            progresspaket.status = convert_progress['waiting_convert']
            sleep(0.1)

        progresspaket.status = convert_progress['converting']
        with MultiThreader() as threader:
            if not bestandspaket.video.is_converted:
                threader.add_thread(convert_video, pmp.tmp_path / pmp.metadata.video_filepath, progresspaket=progresspaket)

            for audio in pmp.metadata.audio_filepaths:
                threader.add_thread(convert_audio, pmp.tmp_path / "audios" / audio)

            # Convert Images
            if pmp.metadata.thumbnail_vertical:
                pmp.metadata.thumbnail_vertical = str(convert_image(pmp.tmp_path / pmp.metadata.thumbnail_vertical))

            if pmp.metadata.thumbnail_horizontal:
                pmp.metadata.thumbnail_horizontal = str(convert_image(pmp.tmp_path / pmp.metadata.thumbnail_horizontal))

            if isinstance(pmp.metadata, EpisodeMetadata) and pmp.metadata.series_thumbnail_horizontal:
                pmp.metadata.series_thumbnail_horizontal = str(convert_image(pmp.tmp_path / pmp.metadata.series_thumbnail_horizontal))

            if isinstance(pmp.metadata, EpisodeMetadata) and pmp.metadata.series_thumbnail_vertical:
                pmp.metadata.series_thumbnail_vertical = str(convert_image(pmp.tmp_path / pmp.metadata.series_thumbnail_vertical))

        video_quality = get_video_quality(pmp.tmp_path / pmp.metadata.video_filepath)
        audios_quality = [get_audio_quality(pmp.tmp_path / "audios" / audio) for audio in pmp.metadata.audio_filepaths]
        subtitles_quality = [get_subtitle_quality(pmp.tmp_path / "subtitles" / subtitle) for subtitle in pmp.metadata.subtitle_filepaths]

        progresspaket.status = convert_progress['saving']
        new_bestandspaket = Bestandspaket(
            provider=bestandspaket.provider,
            id=bestandspaket.id,
            video=video_quality,
            audios=audios_quality,
            subtitles=subtitles_quality,
            pmp_path=pmp.pack(Path(bestandspaket.pmp_path).parent),
        )

        ProDB().write_bestandspaket(new_bestandspaket)

    except Exception as exc:
        log("ERROR", f"Error while converting: {bestandspaket.pmp_path} {exc}")
        progresspaket.status = convert_progress['error']
        progresspaket.done = True
        raise exc

    print("Finished converting:", new_bestandspaket.pmp_path)
    progresspaket.done = True

    return new_bestandspaket


def main():
    db = ProDB()
    bestandspakete = db.read_all_bestandspakete()

    with CLIThreader(cli=cli):
        with MultiThreader(max_threads=args.threads, ignore_exceptions=True) as threader:
            for bestandspaket in bestandspakete:
                if args.provider and bestandspaket.provider != args.provider:
                    continue

                dir_names = {'movie': 'Filme', 'episode': 'Serien'}
                if args.only_type and Path(bestandspaket.pmp_path).parts[0] != dir_names[args.only_type]:
                    continue

                # Clean-up/Memory leak Prevention
                [progresspakete.remove(pp) for pp in progresspakete if pp.done]

                if not bestandspaket.is_converted:
                    threader.add_thread(convert_bestandspaket, bestandspaket)


if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument('--threads', type=int, default=3, help='Limit the overall number of threads. NOT RECOMMENDED.')
    arg_parser.add_argument('--provider', type=str, help="The provider to be converted.")
    arg_parser.add_argument('--only-type', type=str, help="The type to be converted. ['movie', 'episode']")
    arg_parser.add_argument('--network-limit', type=int, default=0, help="Limit the number of Videos to concurrent transfer from/to Storage.")
    arg_parser.add_argument('--convert-limit', type=int, default=1, help="Limit the number of Videos to concurrent be converted.")
    args = arg_parser.parse_args()
    main()
