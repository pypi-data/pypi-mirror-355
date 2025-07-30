from pathlib import Path

from lib.pakete.bestandspaket import SubtitleQuality


class BaseSubtitle:

    def __init__(self):
        self.language = None
        self.codec = None
        self.forced = None
        self.is_deaf = False

    def __str__(self) -> str:
        return f"{self.language} - {self.codec}{' - Forced' if self.forced else ''}"

    def __repr__(self) -> str:
        return self.__str__()

    def __gt__(self, other) -> bool:
        if not self.is_deaf and other.is_deaf:
            return True

        return False

    def get_quality(self) -> SubtitleQuality:
        subtitle_quality = SubtitleQuality(
            language=self.language,
            codec=self.codec,
            forced=self.forced
        )
        if not subtitle_quality.valid:
            raise RuntimeError(f"Subtitle quality is not valid: {subtitle_quality}")

        return subtitle_quality

    def download(self) -> list[Path]:
        raise NotImplementedError
