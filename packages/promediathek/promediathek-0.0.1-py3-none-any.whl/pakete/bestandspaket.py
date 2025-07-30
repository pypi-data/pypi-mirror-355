from dataclasses import dataclass, asdict
from json import dumps
from os import PathLike


@dataclass(frozen=True, eq=True)
class VideoQuality:
    bitrate: int
    codec: str
    width: int
    height: int

    def __gt__(self, other) -> bool:
        return self.width * self.height > other.width * other.height

    @property
    def is_converted(self) -> bool:
        return self.codec.lower() == 'av01'

    @property
    def valid(self) -> bool:
        if not isinstance(self.bitrate, int) or self.bitrate == 0:
            return False

        if not isinstance(self.codec, str) or not self.codec:
            return False

        if not isinstance(self.width, int) or self.width == 0:
            return False

        if not isinstance(self.height, int) or self.height == 0:
            return False

        return True


@dataclass(frozen=True, eq=True)
class AudioQuality:
    language: str
    codec: str
    channels: int
    bandwidth: int
    is_atmos: bool

    def __gt__(self, other) -> bool:
        if self.is_atmos and not other.is_atmos:
            return True
        return self.channels > other.channels

    @property
    def is_converted(self) -> bool:
        return self.codec.lower() == 'opus'

    @property
    def valid(self) -> bool:
        if not isinstance(self.language, str) or not self.language:
            return False

        if not isinstance(self.codec, str) or not self.codec:
            return False

        if not isinstance(self.channels, int) or self.channels == 0:
            return False

        if not isinstance(self.bandwidth, int) or self.bandwidth == 0:
            return False

        if not isinstance(self.is_atmos, bool):
            return False

        return True

    @classmethod
    def load(cls, data: dict):
        audio_quality_instance = cls(
            language=data['language'],
            codec=data['codec'],
            channels=data['channels'],
            bandwidth=data['bandwidth'],
            is_atmos=data.get('is_atmos', False)
        )
        return audio_quality_instance


@dataclass(frozen=True, eq=True)
class SubtitleQuality:
    language: str
    codec: str
    forced: bool

    @property
    def is_converted(self) -> bool:
        return self.codec.lower() == 'ass' or True  # TODO convert subtitles

    @property
    def valid(self) -> bool:
        if not isinstance(self.language, str) or not self.language:
            return False

        if not isinstance(self.codec, str) or not self.codec:
            return False

        if not isinstance(self.forced, bool):
            return False

        return True

    @classmethod
    def load(cls, data: dict):
        subtitle_quality_instance = cls(
            language=data['language'],
            codec=data['codec'],
            forced=data['forced']
        )
        return subtitle_quality_instance


@dataclass(frozen=True, eq=True)
class Bestandspaket:
    provider: str  # provider name
    id: str  # id from provider

    video: VideoQuality | None  # video information
    audios: list[AudioQuality]  # audio information
    subtitles: list[SubtitleQuality]  # subtitle information
    pmp_path: PathLike | str | None   # Path to ProMediaPaket file

    @property
    def is_converted(self) -> bool:
        if not self.video.is_converted:
            return False

        if any([not audio.is_converted for audio in self.audios]):
            return False

        if any([not subtitle.is_converted for subtitle in self.subtitles]):
            return False

        return True

    @property
    def dict(self) -> dict:
        return asdict(self)

    @property
    def json(self) -> str:
        return dumps(self.dict)
