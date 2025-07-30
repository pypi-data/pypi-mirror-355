from pathlib import Path

from lib.drm.pssh import PSSHs
from lib.pakete.bestandspaket import VideoQuality
from lib.utils.logger import log


class BaseVideo:
    # Up is better
    codec_prio = [
        'dvh1', 'dvhe',
        'hvc1',
        'avc1'
    ]

    def __init__(self):
        self.bitrate = None
        self.codec = None
        self.width = None
        self.height = None

    def __str__(self) -> str:
        return f"{self.codec} - {self.bitrate/8000}KB - {self.width}x{self.height}"

    def __gt__(self, other) -> bool:
        if self.width * self.height != other.width * other.height:
            return self.width * self.height > other.width * other.height

        if self.codec != other.codec:
            return self.codec_prio.index(self.codec) < self.codec_prio.index(other.codec)

        if self.bitrate > other.bitrate:
            return True

        return False

    def get_quality(self) -> VideoQuality:
        video_quality = VideoQuality(
            bitrate=self.bitrate,
            codec=self.codec,
            width=self.width,
            height=self.height
        )
        if not video_quality.valid:
            log("ERROR", f"Video quality not valid: {video_quality}")
            raise RuntimeError(f"Video quality not valid: {video_quality}")

        return video_quality

    def get_psshs(self) -> PSSHs:
        raise NotImplementedError

    def download(self) -> list[Path]:
        raise NotImplementedError
