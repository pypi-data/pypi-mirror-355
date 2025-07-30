from dataclasses import dataclass, asdict
from json import dumps, loads
from pathlib import Path
from typing import Self

from lib.utils.logger import log
from lib.utils.networking import safe_get, safe_post, SafeHTTPResponse


@dataclass
class LoginData:
    provider: str
    email: str = "CHANGE ME"
    password: str = "CHANGE ME"
    last_login_data: dict | str | None = None
    last_anon_login_data: dict | str | None = None

    @property
    def json(self):
        return dumps(asdict(self))

    @classmethod
    def load(cls, data: dict) -> Self:
        self = cls.__new__(cls)
        self.__dict__.update(data)
        return self


class BaseAPI:
    name: str = "base"  # change to provider name, can't have a / or a .

    def __init__(self):
        self.login_path = Path("logins", self.name).with_suffix('.json')
        if not self.login_path.is_file():
            log("ERROR", f"No login file found for {self.name}")
            self.login_path.parent.mkdir(parents=True, exist_ok=True)
            self.login_path.write_text(LoginData(self.name).json, encoding="utf-8")

        login_data = loads(self.login_path.read_text(encoding="utf-8"))
        self.login_data = LoginData.load(login_data)

    def anon_login(self) -> None:
        """
        Use if anonymous Login is required.
        :return:
        """
        raise NotImplementedError

    def _anon_login(self) -> None:
        """
        Use if anonymous Login is required.
        :return:
        """
        self.anon_login()
        self.login_path.write_text(self.login_data.json, encoding="utf-8")

    def login(self) -> None:
        """
        Return nothing if successful and raise an Exception if not.
        """
        raise NotImplementedError

    def _login(self) -> None:
        log("INFO", f"Login for {self.name}")
        self.login()
        self.login_path.write_text(self.login_data.json, encoding="utf-8")

    def prepare_anon_auth(self, **kwargs) -> dict:
        """
        Prepares the anon request data e.g. Headers, Params, Cookies, etc. with the required anon auth data.
        :param kwargs: Optional request data.
        :return: The prepared request data as dict.
        """
        return kwargs

    def request_was_anon_authed(self, response: SafeHTTPResponse | dict) -> bool:
        """
        Determines if the request failed because of authentication.
        :param response: The response to check.
        :return: If True, call self._anon_login()
        """
        return True

    def get(self, url: str, **kwargs) -> SafeHTTPResponse | dict:
        """
        Makes an anon GET request.
        :param url: The url, optional with params.
        :param kwargs: The request data.
        :return:
        """
        kwargs = self.prepare_anon_auth(**kwargs)
        response = safe_get(url=url, **kwargs)

        if not self.request_was_anon_authed(response):
            self._anon_login()
            return self.get(url=url, **kwargs)

        return response

    def post(self, url: str, **kwargs) -> SafeHTTPResponse | dict:
        """
        Makes an anon POST request.
        :param url: The url, optional with params.
        :param kwargs: The request data.
        :return:
        """
        kwargs = self.prepare_anon_auth(**kwargs)
        response = safe_post(url=url, **kwargs)

        if not self.request_was_anon_authed(response):
            self._anon_login()
            return self.post(url=url, **kwargs)

        return response

    def prepare_auth(self, **kwargs) -> dict:
        """
        Prepares the request data e.g. Headers, Params, Cookies, etc. with the required auth data.
        :param kwargs: Optional request data.
        :return: The prepared request data as dict.
        """
        raise NotImplementedError

    def request_was_authed(self, response: SafeHTTPResponse | dict) -> bool:
        """
        Determines if the request failed because of authentication.
        Use with auth_get() and auth_post()
        :param response: The response to check.
        :return: If True, call self._login()
        """
        raise NotImplementedError

    def auth_get(self, url: str, **kwargs) -> SafeHTTPResponse | dict:
        """
        Makes an authed GET request.
        :param url: The url, optional with params.
        :param kwargs: The request data.
        :return:
        """
        kwargs = self.prepare_auth(**kwargs)
        response = safe_get(url=url, **kwargs)

        if not self.request_was_authed(response):
            self._login()
            return self.auth_get(url=url, **kwargs)

        return response

    def auth_post(self, url: str, **kwargs) -> SafeHTTPResponse | dict:
        """
        Makes an authed POST request.
        :param url: The url, optional with params.
        :param kwargs: The request data.
        :return:
        """
        kwargs = self.prepare_auth(**kwargs)
        response = safe_post(url=url, **kwargs)

        if not self.request_was_authed(response):
            self._login()
            return self.auth_post(url=url, **kwargs)

        return response
