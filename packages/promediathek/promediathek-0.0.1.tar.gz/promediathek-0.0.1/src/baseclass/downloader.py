from os import PathLike
from pathlib import Path
from tempfile import TemporaryDirectory

from promediapaket import ProMediaPaket

from lib.baseclass.audio import BaseAudio
from lib.baseclass.subtitle import BaseSubtitle
from lib.baseclass.video import BaseVideo
from lib.ffmpeg import get_video_quality, get_audio_quality, get_subtitle_quality, convert_image, remove_drm
from lib.ffmpeg.ffmpeg import concat_containers
from lib.drm.pssh import PSSHs
from lib.pakete.sammelpaket import Sammelpaket, EpisodeSammelpaket, MovieSammelpaket, MovieExtrasSammelpaket
from lib.pakete.bestandspaket import Bestandspaket, AudioQuality, SubtitleQuality, VideoQuality
from lib.pakete.progresspaket import Progresspaket
from lib.utils.logger import log
from lib.utils.networking import safe_get_large
from lib.utils.threader import MultiThreader
from lib.utils.db import ProDB
from lib.drm import BasicDrm, Widevine


def skip(data: list, skip_index: int):
    skipped_data = data[skip_index:]
    if not skipped_data:
        log("WARN", f"Skipped Data is empty, returning all data instead: {data}")
        return data
    return skipped_data


class BaseDownloadProtocol:
    """
    BaseClass for Download Protocols like Dash or HLS.
    Dash/HLS inherits this; the individual Provider
    should then inherit Dash/HLS and add the Thumbnail methods
    and any other necessary change.
    """

    # If the Download consists of multiple Files, then discard the first {skip_index}. Useful to Logo Intros.
    skip_index = 0

    def __init__(self, sammelpaket: Sammelpaket):
        self.tmp_dir = TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)
        self.sammelpaket = sammelpaket
        self.drm_system: callable(BasicDrm) = Widevine
        self._drm_keys = None

        self._manifest_url = None
        self.request_cookies = {}
        self.request_headers = {}

        self._videos: list[BaseVideo] = []
        self._audios: list[BaseAudio] = []
        self._subtitles: list[BaseSubtitle] = []

        self.pmp = ProMediaPaket()
        self.pmp.set_titel(self.sammelpaket.titel)
        self.pmp.set_description(self.sammelpaket.description)
        self.pmp.set_provider(self.sammelpaket.provider, self.sammelpaket.id)
        if isinstance(self.sammelpaket, MovieExtrasSammelpaket):
            self.pmp.metadata.extras_main_id = self.sammelpaket.main_movie_id

        self.progresspaket = Progresspaket("None")

        if isinstance(self.sammelpaket, EpisodeSammelpaket):
            self.pmp.set_series_id(self.sammelpaket.series_id)
            self.pmp.set_series_title(self.sammelpaket.series_title)
            self.pmp.set_series_description(self.sammelpaket.series_description)

            self.pmp.set_season_id(self.sammelpaket.season_id)
            self.pmp.set_season_number(self.sammelpaket.season_number)

            self.pmp.set_episode_number(self.sammelpaket.episode_number)

    @property
    def video(self) -> BaseVideo:
        return max(self._videos)

    @property
    def audios(self) -> list[BaseAudio]:
        audios = []
        languages = {audio.language for audio in self._audios}
        for language in languages:
            language_audios = [audio for audio in self._audios if audio.language == language]
            audios.append(max(language_audios))

        return audios

    @property
    def subtitles(self) -> list[BaseSubtitle]:
        reduced_subtitle = []
        languages = {subtitle.language for subtitle in self._subtitles if not subtitle.forced}
        for language in languages:
            language_subtitles = [subtitle for subtitle in self._subtitles if subtitle.language == language and not subtitle.forced]
            if len(language_subtitles) == 1:
                reduced_subtitle.append(language_subtitles[0])
                continue

            language_subtitles = [s for s in language_subtitles if not s.is_deaf]
            if len(language_subtitles) == 1:
                reduced_subtitle.append(language_subtitles[0])
                continue

            log('WARN', f"Multiple Subtitle for the same language: {[subtitle for subtitle in language_subtitles]}")
            reduced_subtitle.append(language_subtitles[0])

        # Forced Subtitles
        languages = {subtitle.language for subtitle in self._subtitles if subtitle.forced}
        for language in languages:
            language_subtitles = [subtitle for subtitle in self._subtitles if subtitle.language == language and subtitle.forced]
            if len(language_subtitles) == 1:
                reduced_subtitle.append(language_subtitles[0])
                continue

            language_subtitles = [s for s in language_subtitles if not s.is_deaf]
            if len(language_subtitles) == 1:
                reduced_subtitle.append(language_subtitles[0])
                continue

            log('WARN', f"Multiple Subtitle for the same language: {[subtitle for subtitle in language_subtitles]}")
            reduced_subtitle.append(language_subtitles[0])

        return reduced_subtitle

    def init(self) -> None:
        """
        Put optional Init operations here.
        """
        pass

    def get_manifest_url(self) -> str:
        """
        Returns the base url of the DASH/HLS manifest.
        :return: Url of the DASH/HLS manifest.
        """
        raise NotImplementedError

    @property
    def manifest_url(self) -> str:
        if self._manifest_url is None:
            self._manifest_url = self.get_manifest_url()

        return self._manifest_url

    def _download_thumbnail(self, thumbnail_url: str, filename: str) -> Path | None:
        """
        Thumbnail download method
        Downloads and converts the thumbnail to .png
        :param thumbnail_url:
        :param filename: Filename without Extension
        :return: Path of downloaded thumbnail
        """
        if thumbnail_url is None:
            return None

        thumbnail_file = safe_get_large(thumbnail_url, self.tmp_path / filename)
        converted_thumbnail_file = convert_image(thumbnail_file)
        return converted_thumbnail_file

    def _download_video(self) -> Path:
        videos = self.video.download()
        videos = remove_drm(videos, self.drm_keys)
        video = concat_containers(skip(videos, self.skip_index), 'video')
        return video

    def _download_audio(self, specific_audio: AudioQuality = None) -> list[Path]:
        audio_threads = []
        with MultiThreader() as threader:
            for audio in self.audios:
                if specific_audio and audio.get_quality() != specific_audio:
                    continue

                audio_thread = threader.add_thread(audio.download)
                audio_threads.append(audio_thread)

        audio_files: list[list[Path]] = [thread.result() for thread in audio_threads]
        audio_files = [remove_drm(audio, self.drm_keys) for audio in audio_files]
        audio_files: list[Path] = [concat_containers(skip(audio, self.skip_index), audio[0].stem.rsplit('_', 1)[0]) for audio in audio_files]
        return audio_files

    def _download_subtitle(self) -> list[Path]:
        subtitle_threads = []
        with MultiThreader() as threader:
            for subtitle in self.subtitles:
                thread = threader.add_thread(subtitle.download)
                subtitle_threads.append(thread)

        subtitles = [subtitle.result() for subtitle in subtitle_threads]
        subtitles = [concat_containers(skip(subtitle, self.skip_index), subtitle[0].stem.rsplit('_', 1)[0]) for subtitle in subtitles]
        return subtitles

    def download_video(self) -> Path:
        video_path = self._download_video()
        self.pmp.add_video(video_path)
        return video_path

    def download_audio(self, specific_audio: AudioQuality = None) -> list[Path]:
        audios_path = self._download_audio(specific_audio=specific_audio)
        [self.pmp.add_audio(audio_path) for audio_path in audios_path]
        return audios_path

    def download_subtitle(self) -> list[Path]:
        subtitles_path = self._download_subtitle()
        [self.pmp.add_subtitle(subtitle_path) for subtitle_path in subtitles_path]
        return subtitles_path

    def download_thumbnail_vertical(self) -> Path:
        if isinstance(self.sammelpaket, MovieSammelpaket):
            thumbnail_file = self._download_thumbnail(self.sammelpaket.movie_thumbnail_vertical, "movie_thumbnail_vertical")

        elif isinstance(self.sammelpaket, EpisodeSammelpaket):
            thumbnail_file = self._download_thumbnail(self.sammelpaket.episode_thumbnail_vertical, "episode_thumbnail_vertical")

        else:
            raise NotImplemented

        if thumbnail_file:
            self.pmp.set_thumbnail_vertical(thumbnail_file)

        return thumbnail_file

    def download_thumbnail_horizontal(self) -> Path:
        if isinstance(self.sammelpaket, MovieSammelpaket):
            thumbnail_file = self._download_thumbnail(self.sammelpaket.movie_thumbnail_horizontal, "movie_thumbnail_horizontal")

        elif isinstance(self.sammelpaket, EpisodeSammelpaket):
            thumbnail_file = self._download_thumbnail(self.sammelpaket.episode_thumbnail_horizontal, "episode_thumbnail_horizontal")

        else:
            raise NotImplemented

        if thumbnail_file:
            self.pmp.set_thumbnail_horizontal(thumbnail_file)

        return thumbnail_file

    def download_thumbnail_series_vertical(self) -> Path | None:
        thumbnail_file = None
        if isinstance(self.sammelpaket, EpisodeSammelpaket):
            thumbnail_file = self._download_thumbnail(self.sammelpaket.series_thumbnail_vertical, "series_thumbnail_vertical")

        if thumbnail_file:
            self.pmp.set_series_thumbnail_vertical(thumbnail_file)

        return thumbnail_file

    def download_thumbnail_series_horizontal(self) -> Path | None:
        thumbnail_file = None
        if isinstance(self.sammelpaket, EpisodeSammelpaket):
            thumbnail_file = self._download_thumbnail(self.sammelpaket.series_thumbnail_horizontal, "series_thumbnail_horizontal")

        if thumbnail_file:
            self.pmp.set_series_thumbnail_horizontal(thumbnail_file)

        return thumbnail_file

    def get_video_qualities(self) -> VideoQuality:
        return self.video.get_quality()

    def get_audio_qualities(self) -> list[AudioQuality]:
        return [audio.get_quality() for audio in self.audios]

    def get_subtitle_qualities(self) -> list[SubtitleQuality]:
        return [subtitle.get_quality() for subtitle in self.subtitles]

    def get_psshs(self) -> PSSHs:
        psshs = self.video.get_psshs()
        [psshs.extend(audio.get_psshs()) for audio in self.audios]
        return psshs

    def _get_drm_keys(self, challenge: bytes | str) -> bytes:
        raise NotImplementedError

    def _get_drm_cert(self) -> str | bytes:
        pass

    def get_drm_keys(self) -> list[str]:
        drm_keys = []
        for pssh in self.get_psshs().get_vendor_psshs(self.drm_system.vendor_id):
            cdm: BasicDrm = self.drm_system()
            if cert := self._get_drm_cert():
                cdm.set_server_cert(cert)

            cdm.set_pssh(pssh)
            challenge = cdm.get_challenge()

            response_content = self._get_drm_keys(challenge)
            drm_keys += cdm.parse_license(response_content)

        return drm_keys

    @property
    def drm_keys(self) -> list[str]:
        if self._drm_keys is None:
            self._drm_keys = self.get_drm_keys()
        return self._drm_keys


class BaseDownloadHandler:

    def __init__(self, downloader: BaseDownloadProtocol):
        self.downloader = downloader
        self.downloader.init()

        self.sammelpaket = self.downloader.sammelpaket
        self.progresspaket = Progresspaket(self.sammelpaket.titel, status="Initializing")
        self.downloader.progresspaket = self.progresspaket
        self.db = ProDB()

    def download_video(self) -> Path:
        self.progresspaket.status = "Herunterladen"
        video_file = self.downloader.download_video()
        return video_file

    def download_audio(self, specific_audio: AudioQuality = None) -> list[Path]:
        self.progresspaket.status = "Herunterladen"
        audio_files = self.downloader.download_audio(specific_audio=specific_audio)
        return audio_files

    def make_bestandspaket(self, pmp_target: PathLike | str) -> Bestandspaket:
        self.progresspaket.status = "Überprüfe Qualität"
        video_quality = get_video_quality(
            self.downloader.pmp.tmp_path / self.downloader.pmp.metadata.video_filepath
        )

        audio_qualities = [
            get_audio_quality(self.downloader.pmp.tmp_path / "audios" / audio_file)
            for audio_file in self.downloader.pmp.metadata.audio_filepaths
        ]

        subtitle_qualities = [
            get_subtitle_quality(self.downloader.pmp.tmp_path / "subtitles" / subtitle_file)
            for subtitle_file in self.downloader.pmp.metadata.subtitle_filepaths
        ]

        self.progresspaket.status = "Packe PMP"
        bestandspaket = Bestandspaket(
            provider=self.sammelpaket.provider,
            id=self.sammelpaket.id,
            video=video_quality,
            audios=audio_qualities,
            subtitles=subtitle_qualities,
            pmp_path=self.downloader.pmp.pack(pmp_target)
        )

        self.progresspaket.status = "Aktualisiere Datenbank"
        self.db.write_bestandspaket(bestandspaket)

        return bestandspaket

    def _download(self, pmp_pack_target: PathLike | str):

        try:
            with MultiThreader() as threader:
                threader.add_thread(self.download_video)
                threader.add_thread(self.download_audio)
                threader.add_thread(self.downloader.download_subtitle)
                threader.add_thread(self.downloader.download_thumbnail_vertical)
                threader.add_thread(self.downloader.download_thumbnail_horizontal)

                # Episode
                threader.add_thread(self.downloader.download_thumbnail_series_vertical)
                threader.add_thread(self.downloader.download_thumbnail_series_horizontal)

        except Exception as exception:
            self.progresspaket.status = "Fehler beim Herunterladen"
            self.downloader.tmp_dir.cleanup()
            raise exception

        bestandspaket = self.make_bestandspaket(pmp_pack_target)
        self.progresspaket.status = "Räume auf"
        self.downloader.tmp_dir.cleanup()

        return bestandspaket

    def download(self) -> Bestandspaket | None:

        if self.db.already_downloaded(self.sammelpaket):
            bestandspaket = self.db.read_bestandspaket(self.sammelpaket)
            log("VERBOSE", f"Already downloaded checking for Updates, {bestandspaket.pmp_path}")

            self.progresspaket.status = "Suche Änderungen"
            downloader_video_quality = self.downloader.get_video_qualities()
            new_video = downloader_video_quality > bestandspaket.video

            bestands_audio_languages = {audio.language: audio for audio in bestandspaket.audios}
            downloader_audio_qualities = self.downloader.get_audio_qualities()
            new_audios = [audio for audio in downloader_audio_qualities if audio.language not in bestands_audio_languages or audio > bestands_audio_languages[audio.language]]

            bestands_subtitle_languages = [f'{subtitle.language}{bool(subtitle.forced)}' for subtitle in bestandspaket.subtitles]
            downloader_subtitle_qualities = self.downloader.get_subtitle_qualities()
            new_subtitles = [subtitle for subtitle in downloader_subtitle_qualities if f'{subtitle.language}{bool(subtitle.forced)}' not in bestands_subtitle_languages]

            if new_video or new_audios or new_subtitles:
                log("VERBOSE", f"Found Updates: {new_video}, {new_audios}, {new_subtitles} on {bestandspaket.pmp_path}")
                self.progresspaket.status = "Entpacke PMP"
                self.downloader.pmp = ProMediaPaket.open(bestandspaket.pmp_path)

                if new_video:
                    self.progresspaket.status = "Neues Video"
                    self.download_video()

                if new_audios:
                    self.progresspaket.status = "Neue Audios"
                    [self.download_audio(audio) for audio in new_audios]

                if new_subtitles:
                    self.progresspaket.status = "Neue Untertitel"
                    self.downloader.download_subtitle()

                bestandspaket = self.make_bestandspaket(Path(bestandspaket.pmp_path).parent)
                self.downloader.tmp_dir.cleanup()

            else:
                self.progresspaket.status = "Schon vorhanden"

            self.progresspaket.done = True
            return bestandspaket

        if self.sammelpaket.type == "movie":
            bestandspaket = self._download(f"Filme/{self.sammelpaket.provider}")

        elif self.sammelpaket.type == "episode":
            pmp_path = Path("Serien")
            pmp_path /= self.sammelpaket.provider
            # noinspection PyUnresolvedReferences
            pmp_path /= f"{self.sammelpaket.series_id}@{self.sammelpaket.series_title.replace('/', '⧸')}"  # Series Folder
            # noinspection PyUnresolvedReferences
            pmp_path /= f"{self.sammelpaket.season_id}@{self.sammelpaket.season_number.replace('/', '⧸')}"  # Season Folder
            bestandspaket = self._download(pmp_path)

        elif self.sammelpaket.type == "audiobook":
            raise NotImplementedError

        elif self.sammelpaket.type == "music":
            raise NotImplementedError

        else:
            raise ValueError(f"Unknown Type: {self.sammelpaket.type}")

        self.progresspaket.status = "Fertig"
        self.progresspaket.done = True
        return bestandspaket
