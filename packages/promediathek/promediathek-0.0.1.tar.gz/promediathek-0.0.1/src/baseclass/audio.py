from pathlib import Path

from lib.drm.pssh import PSSHs
from lib.pakete.bestandspaket import AudioQuality


class BaseAudio:
    codec_prio = [
        'apac',  # Apple TV Immersive Audio
        'ac-4', 'ec-3', 'ac-3',
        'dtsc', 'dtsh', 'dtse', 'dtsx', 'dtsy',
        'mp4a',
        'mhm2', 'mhm1',
    ]

    def __init__(self):
        self.language = None
        self.codec = None
        self.channels = None
        self.bitrate = None
        self.is_atmos = None

        self.is_audio_description = False

    def __str__(self) -> str:
        return f"{self.language} - {self.codec} - {self.channels}ch - {self.bitrate/8000}KB"

    def __gt__(self, other) -> bool:
        if self.is_audio_description and not other.is_audio_description:
            return False

        if self.is_atmos and not other.is_atmos:
            return True

        if self.codec_prio.index(self.codec) < self.codec_prio.index(other.codec):
            return True

        elif self.codec != other.codec:
            return False

        if self.bitrate > other.bitrate:
            return True

        return False

    def get_quality(self) -> AudioQuality:
        audio_quality = AudioQuality(
            language=self.language,
            codec=self.codec,
            channels=self.channels,
            bandwidth=self.bitrate,
            is_atmos=self.is_atmos,
        )
        if not audio_quality.valid:
            raise RuntimeError(f"Audio Quality not valid: {audio_quality}")

        return audio_quality

    def get_psshs(self) -> PSSHs:
        raise NotImplementedError

    def download(self) -> list[Path]:
        raise NotImplementedError
