class BasicDrm:
    device: str = None
    vendor_id: str = None

    def __init__(self):
        self.pssh = None
        self.server_cert = None

        if self.device is None:
            print(f"No device specified for {type(self).__name__}")
            print("Please set the device variable in the DRM class")
            exit(1)

    def set_server_cert(self, server_cert: str | bytes) -> None:
        if isinstance(server_cert, str):
            # Convert URL Safe Base64 to Normal Base64
            server_cert = server_cert.replace('-', '+').replace('_', '/')

        self.server_cert = server_cert

    def set_pssh(self, pssh: (str, bytes)) -> None:
        self.pssh = pssh

    def get_challenge(self, base64: bool = False):
        raise NotImplementedError

    def parse_license(self, license_content: bytes) -> list[str]:
        raise NotImplementedError
