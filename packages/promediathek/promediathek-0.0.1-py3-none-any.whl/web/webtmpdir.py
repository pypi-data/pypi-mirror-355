from tempfile import TemporaryDirectory
from time import time


class WebTmpDir:

    def __init__(self, tempdir: TemporaryDirectory, expiration_time: int | float = 60*60*12, extra_data=None):
        self.tempdir = tempdir
        self.expiration_time = expiration_time
        self.extra_data = extra_data
        self.created_time = time()

    @property
    def expired(self) -> bool:
        return time() > self.created_time + self.expiration_time
