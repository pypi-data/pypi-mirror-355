from dataclasses import dataclass


@dataclass
class Progresspaket:
    text: str
    status: str = None
    progress_list: list[float] = None
    done: bool = False

    def __init__(self, text: str, status: str = None):
        self.text = text
        self.status = status
        if self.progress_list is None:
            self.progress_list = []

    @property
    def progress(self) -> float:
        if not self.progress_list:
            return 0

        # Median because of multiple fast Audio Tracks
        return (max(self.progress_list) + min(self.progress_list)) / 2

    def __str__(self) -> str:
        return f"{self.text} - Status: {self.status} - Progress: {self.progress:.0%}"


@dataclass
class ConvertProgresspaket(Progresspaket):
    convert_speed: float = 0

    def __init__(self, text: str, status: str = None):
        super().__init__(text, status)

    def __str__(self) -> str:
        return f"{self.text} - Status: {self.status} - Progress: {self.progress:.2%} - Speed: {float(self.convert_speed):.2}x"
