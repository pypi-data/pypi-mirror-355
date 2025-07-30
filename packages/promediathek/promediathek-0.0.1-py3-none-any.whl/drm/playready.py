from base64 import b64encode
from pathlib import Path

from Crypto.Random import get_random_bytes
from pyplayready import ECCKey
from pyplayready.cdm import Cdm
from pyplayready.device import Device
from pyplayready.system.bcert import Certificate
from pyplayready.system.pssh import PSSH

from lib.drm.basic_drm import BasicDrm


class PlayReady(BasicDrm):
    device = None
    vendor_id = "9a04f07998404286ab92e65be0885f95"

    def __init__(self):
        super().__init__()
        device_file = Path(__file__).parent / self.device
        device = Device.load(device_file)
        device.group_certificate.remove(0)

        encryption_key = ECCKey.generate()
        signing_key = ECCKey.generate()

        device.encryption_key = encryption_key
        device.signing_key = signing_key

        new_certificate = Certificate.new_leaf_cert(
            cert_id=get_random_bytes(16),
            security_level=device.group_certificate.get_security_level(),
            client_id=get_random_bytes(16),
            signing_key=signing_key,
            encryption_key=encryption_key,
            group_key=device.group_key,
            parent=device.group_certificate
        )
        device.group_certificate.prepend(new_certificate)

        self.cdm = Cdm.from_device(device)
        self.session_id = self.cdm.open()

    def get_challenge(self, base64: bool = False):
        challenge = self.cdm.get_license_challenge(self.session_id, PSSH(self.pssh).wrm_headers[0])
        if base64:
            challenge = b64encode(challenge.encode('utf-8')).decode('utf-8')
        return challenge

    def parse_license(self, license_content: bytes) -> list[str]:
        self.cdm.parse_license(self.session_id, license_content.decode('utf-8'))
        keys = [key.key.hex() for key in self.cdm.get_keys(self.session_id)]
        self.cdm.close(self.session_id)
        return keys


class PlayReadySL3000(PlayReady):
    device = "mtc_atv_sl3000_deviceTypeId-A2HYAJ0FEWP6N3.prd"
