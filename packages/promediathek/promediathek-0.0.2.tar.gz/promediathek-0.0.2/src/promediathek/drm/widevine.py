from pywidevine.cdm import Cdm
from pywidevine.device import Device
from pywidevine.pssh import PSSH

from pathlib import Path
from base64 import b64encode

from lib.drm.basic_drm import BasicDrm


class Widevine(BasicDrm):
    device = None
    vendor_id = "edef8ba979d64acea3c827dcd51d21ed"

    def __init__(self):
        super().__init__()
        device_file = Device.load(Path(__file__).parent / self.device)
        self.cdm = Cdm.from_device(device_file)
        self.session = None

    def get_challenge(self, base64=False):
        self.session = self.cdm.open()
        if self.server_cert:
            self.cdm.set_service_certificate(self.session, self.server_cert)

        challenge = self.cdm.get_license_challenge(self.session, PSSH(self.pssh))
        if base64:
            challenge = b64encode(challenge).decode('utf-8')

        return challenge

    def parse_license(self, license_content) -> list[str]:
        self.cdm.parse_license(self.session, license_content)
        keys = self.cdm.get_keys(self.session)
        content_keys = [key.key.hex() for key in keys if key.type == 'CONTENT']
        return content_keys
