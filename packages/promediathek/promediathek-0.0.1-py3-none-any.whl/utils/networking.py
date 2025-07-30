from dataclasses import dataclass
from http.client import HTTPConnection, HTTPSConnection, HTTPResponse, IncompleteRead
from urllib.parse import urlparse, quote_plus
from json import JSONDecodeError, loads, dumps
from time import sleep
from pathlib import Path

from lib.pakete.progresspaket import Progresspaket
from lib.utils.logger import log

# Timeout for Network requests in Seconds.
timeout = 20


@dataclass
class SafeHTTPResponse:
    status_code: int
    headers: dict
    content: bytes
    url: str
    text: str | None
    json: dict | None

    def __init__(self, url: str, http_response: HTTPResponse):
        self.status_code = http_response.status
        self.content = http_response.read()

        try:
            self.text = self.content.decode("utf-8")
        except UnicodeDecodeError:
            self.text = None

        # noinspection PyTypeChecker
        self.headers = http_response.headers
        self.cookies = {v.split('=')[0]: v.split('=', 1)[1].split(';')[0] for k, v in self.headers.items() if k == 'Set-Cookie'}
        self.url = url

        try:
            self.json = loads(self.text)
        except (JSONDecodeError, TypeError):
            self.json = None


def prepare_form_data(data: dict) -> str | None:
    """
    Turns a dict with x-www-form-urlencoded data into a String.
    :param data:
    :return:
    """
    if not data:
        return None

    prepared_string = ""
    for key, value in data.items():
        if isinstance(value, bool):
            prepared_string += f"&{key}={str(value).lower()}"

        if isinstance(value, str):
            prepared_string += f"&{key}={quote_plus(value)}"

        if isinstance(value, list):
            for item in value:
                prepared_string += f"&{key}={quote_plus(item)}"

    return prepared_string[1:]


def safe_request(methode: str, url: str, params: dict = None, headers: dict = None, cookies: dict = None, data: str = None, json: dict = None, allow_redirects: bool = True, stream: bool = False, return_json: bool = True) -> SafeHTTPResponse | HTTPResponse | dict:
    if headers is None:
        headers = {}

    if isinstance(data, dict):
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        data = prepare_form_data(data)

    if json:
        headers["Content-Type"] = "application/json"
        data = dumps(json)

    if cookies:
        headers["Cookie"] = "; ".join([f"{k}={v}" for k, v in cookies.items()])

    parsed_url = urlparse(url)
    if parsed_url.scheme == "https":
        conn = HTTPSConnection(host=parsed_url.hostname, port=parsed_url.port, timeout=timeout)

    elif parsed_url.scheme == "http":
        conn = HTTPConnection(host=parsed_url.hostname, port=parsed_url.port, timeout=timeout)

    elif parsed_url.scheme == "file":
        # noinspection PyTypeChecker
        conn: HTTPConnection = SafeHTTPResponse.__new__(SafeHTTPResponse)
        conn.request = lambda *args, **kwargs: None
        # noinspection PyTypeChecker
        resp: HTTPResponse = open(parsed_url.path, "rb")
        resp.status = 200
        # noinspection PyTypeChecker
        resp.headers = {}
        conn.getresponse = lambda: resp

    else:
        raise ValueError("Invalid scheme")

    pretty_path = parsed_url.path
    if parsed_url.query or params:
        pretty_path += '?' + parsed_url.query

        if params:
            pretty_path += '&'.join([
                f"{k}={str(v).lower()}" if isinstance(v, bool) else f"{k}={quote_plus(str(v))}"
                for k, v in params.items()
            ])

    # Make sure the headers are only strings and lowercase. Catches None.
    headers = {k.lower(): str(v) for k, v in headers.items()}

    # set defaults
    if 'user-agent' not in headers:
        headers['user-agent'] = 'promediathek/2'

    try:
        conn.request(
            methode.upper(),
            pretty_path,
            headers=headers,
            body=data
        )
        response = conn.getresponse()

        if allow_redirects and response.status in [301, 302, 303, 307, 308]:
            if urlparse(response.headers['Location']).netloc:
                location_url = response.headers['Location']
            else:
                location_url = parsed_url.scheme + '://' + parsed_url.netloc + response.headers['Location']

            return safe_request(methode=methode, url=location_url, headers=headers, data=data, stream=stream)

        if response.status in [500, 502, 503, 504, 111]:
            if b'{"message": "Internal server error"}' == response.read():
                # Thumbnail Size to big:
                # noinspection SpellCheckingInspection
                if 'edits=eyJyZXNpemUiOnsid2lkdGgiOjM4NDAsImhlaWdodCI6MjE2MH0sInF1YWxpdHkiOjEwMH0=' in url:
                    # noinspection SpellCheckingInspection
                    url = url.split('?')[0] + '?edits=eyJyZXNpemUiOnsid2lkdGgiOjE5MjAsImhlaWdodCI6MTA4MH0sInF1YWxpdHkiOjEwMH0='

                else:
                    log('ERROR', f"ArdPlus Thumbnail download failed: {url}")

            log("INFO", f"Got status code {response.status} on {url}")
            sleep(2)
            return safe_request(methode=methode, url=url, headers=headers, data=data, allow_redirects=allow_redirects, stream=stream)

        if stream:
            return response

        try:
            safe_response = SafeHTTPResponse(url, response)
        except IncompleteRead:
            return safe_request(methode=methode, url=url, headers=headers, data=data, allow_redirects=allow_redirects, stream=stream)

        if safe_response.json and return_json:
            return safe_response.json

        return safe_response

    except TimeoutError:
        log("WARN", f"Timeout while connecting to {url}")
        return safe_request(methode=methode, url=url, headers=headers, data=data, allow_redirects=allow_redirects, stream=stream)

    except BaseException as e:
        log("ERROR", f"{e} with: {url}")
        sleep(1)
        return safe_request(methode=methode, url=url, headers=headers, data=data, allow_redirects=allow_redirects, stream=stream)


def safe_get(url: str, **kwargs) -> SafeHTTPResponse | HTTPResponse | dict:
    return safe_request("GET", url=url, **kwargs)


def safe_post(url: str, **kwargs) -> SafeHTTPResponse | HTTPResponse | dict:
    return safe_request("POST", url=url, **kwargs)


def safe_get_large(url: str, outfile: Path, progresspaket: Progresspaket = None, **kwargs) -> Path:
    progress_index = None
    if progresspaket:
        progress_index = len(progresspaket.progress_list)
        progresspaket.progress_list.append(0)

    with safe_request(methode="GET", url=url, stream=True, **kwargs) as stream:
        if stream.status != 200:
            raise RuntimeError(f"Request failed with status {stream.status}")

        total_size = 16238
        if 'content-length' in stream.headers:
            total_size = int(stream.headers['content-length']) + 1
        chunk_num = 0
        chunk_size = max(total_size//2000, 16238)
        with outfile.open('wb') as file:
            while chunk := stream.read(chunk_size):
                file.write(chunk)
                chunk_num += 1

                if progresspaket:
                    progresspaket.progress_list[progress_index] = chunk_num / (total_size / chunk_size)

    return outfile
