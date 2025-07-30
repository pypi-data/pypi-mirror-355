from base64 import urlsafe_b64encode
from hashlib import sha256
from random import choices
from string import ascii_letters, digits
from uuid import uuid4


class OAuth2:
    valid_chars = ascii_letters + digits + '-._~'

    def __init__(self, scope: str = None, redirect_uri: str = None, client_id: str = None):
        self.scope = scope
        self.redirect_uri = redirect_uri
        self.client_id = client_id or str(uuid4())

        self.code_verifier = ''.join(choices(self.valid_chars, k=64))
        self.code_challenge = urlsafe_b64encode(sha256(self.code_verifier.encode()).digest()).decode().replace('=', '')

    def get_params(self) -> dict:
        params = {
            'response_type': 'code',
            'code_challenge_method': 'S256',
            'code_challenge': self.code_challenge,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'scope': self.scope,
        }
        return params

    def get_data(self, code: str) -> dict:
        data = {
            'code': code,
            'grant_type': 'authorization_code',
            'code_verifier': self.code_verifier,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id
        }
        return data
