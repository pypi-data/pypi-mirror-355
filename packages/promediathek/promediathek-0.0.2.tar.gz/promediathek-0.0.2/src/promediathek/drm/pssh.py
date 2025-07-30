from base64 import b64encode
from dataclasses import dataclass
from pathlib import Path


widevine_id = "edef8ba979d64acea3c827dcd51d21ed"
playready_id = "9a04f07998404286ab92e65be0885f95"
fairplay_id = "94ce86fb07ff4f43adb893d2fa968ca2"

drm_vendor_table = {
    'urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed': widevine_id,
    'com.microsoft.playready': playready_id,
    'com.apple.streamingkeydelivery': fairplay_id,
}


@dataclass(frozen=True, eq=True)
class PSSH:
    #  "edef8ba979d64acea3c827dcd51d21ed" is Widevine DRM
    #  "9a04f07998404286ab92e65be0885f95" is PlayReady DRM
    drm_vendor_id: str
    pssh: str  # Base64 Pssh String

    def __post_init__(self):
        if self.drm_vendor_id in drm_vendor_table:
            self.__dict__['drm_vendor_id'] = drm_vendor_table[self.drm_vendor_id]

    def __str__(self) -> str:
        return f"Vendor: {self.drm_vendor_id} - PSSH: {self.pssh}"


@dataclass
class PSSHs:
    pssh_list: set[PSSH]

    def get_vendor_psshs(self, vendor_id: str) -> list[str]:
        psshs = []
        for pssh in self.pssh_list:
            if pssh.drm_vendor_id == vendor_id:
                psshs.append(pssh.pssh)

        return psshs

    @property
    def widevine_psshs(self) -> list[str]:
        return self.get_vendor_psshs(widevine_id)

    @property
    def playready_psshs(self) -> list[str]:
        return self.get_vendor_psshs(playready_id)

    def __add__(self, other):
        return PSSHs(self.pssh_list.union(other.pssh_list))

    def extend(self, psshs):
        self.pssh_list.update(psshs.pssh_list)

    def append(self, pssh: PSSH) -> None:
        self.pssh_list.add(pssh)


class BytesReader:
    def __init__(self, data: bytes):
        self.data = data

    def read(self, length: int, is_int=False, decode=None) -> int | str | bytes:
        if length == 0:
            if b'\x00' not in self.data:
                return self.data.decode(decode)

            length = self.data.index(b'\x00')
            data = self.data[:length]
            self.data = self.data[length+1:]

        else:
            data = self.data[:length]
            self.data = self.data[length:]

        if length == 1:
            data = data[0]

        if decode:
            data = data.decode(decode)
        if is_int:
            data = int.from_bytes(data)

        return data

    def readable(self):
        return bool(self.data)

    def close(self):
        pass


def get_pssh_from_mp4_file(filepath: Path | bytes) -> PSSHs:
    pssh_list = []

    if isinstance(filepath, bytes):
        file = BytesReader(filepath)
    else:
        file = filepath.open(mode='rb')

    while box_length := file.read(4):
        box_length = int.from_bytes(box_length)
        box_type = file.read(4).decode('ascii')
        if box_length == 1:
            box_length = int.from_bytes(file.read(8))
            box_data = file.read(box_length - 16)

        else:
            box_data = file.read(box_length - 8)

        if box_type == 'moov':
            moov_data = BytesReader(box_data)

            while moov_data.data:
                moov_box_length = moov_data.read(4, is_int=True)
                moov_box_type = moov_data.read(4, decode='ascii')
                if moov_box_length == 1:
                    moov_box_length = moov_data.read(8, is_int=True)
                    moov_box_data = moov_data.read(moov_box_length - 16)

                else:
                    moov_box_data = moov_data.read(moov_box_length - 8)

                if moov_box_type == 'pssh':
                    drm_vendor_id = moov_box_data[4:20].hex()
                    pssh = b64encode(moov_box_length.to_bytes(4) + b'pssh' + moov_box_data).decode('utf-8')
                    pssh_list.append(PSSH(drm_vendor_id, pssh))

    file.close()
    return PSSHs(set(pssh_list))
