from dataclasses import dataclass
from pathlib import Path
from re import fullmatch

from lib.baseclass import BaseDownloadProtocol
from lib.baseclass.audio import BaseAudio
from lib.baseclass.subtitle import BaseSubtitle
from lib.baseclass.video import BaseVideo
from lib.drm.pssh import PSSHs, PSSH
from lib.pakete.sammelpaket import Sammelpaket
from lib.pakete.progresspaket import Progresspaket
from lib.utils.logger import log
from lib.utils.networking import safe_get


@dataclass
class HLSLine:
    name: str
    value: None | str | int | dict
    url: str = None


def parse_hls_line(line: str) -> HLSLine | None:
    if line.startswith("##") or not line.startswith('#'):
        return None

    name = line[1:].split(':')[0].strip()
    if ':' not in line:
        return HLSLine(name, None)

    value = line[1:].split(':', 1)[1].strip()
    if value.isnumeric():
        value = int(value)

    if fullmatch(r'#[^:]+:[^=]+', line):
        return HLSLine(name, value)

    params = {}
    parmas_line = line.split(':', 1)[-1]

    value = ''
    key = ''
    in_key = True
    in_quotes = False

    for char in parmas_line:
        if char == '"':
            in_quotes = not in_quotes
            continue

        if char == '=' and not in_quotes:
            in_key = not in_key
            continue

        if char == ',' and not in_quotes:
            in_key = not in_key
            params[key] = value
            key = ''
            value = ''
            continue

        if in_key:
            key += char
        else:
            value += char

    params[key] = value
    return HLSLine(name, params)


def parse_hls_lines(url: str, text: str) -> list[HLSLine]:
    hls_lines = []
    for line_num, line in enumerate(text.splitlines()):
        if hls_line := parse_hls_line(line):
            if isinstance(hls_line.value, dict):
                hls_line.url = hls_line.value.get('URI')

            if hls_line.name in ['EXT-X-STREAM-INF', 'EXTINF']:
                i = 1
                while text.splitlines()[line_num + i].startswith('#'):
                    i += 1

                hls_line.url = text.splitlines()[line_num + i]

            if hls_line.name in ['EXT-X-STREAM-INF', 'EXTINF', 'EXT-X-MEDIA', 'EXT-X-MAP']:
                if hls_line.url and not hls_line.url.startswith('http'):
                    hls_line.url = url[::-1].split('/', 1)[-1][::-1] + '/' + hls_line.url

            hls_lines.append(hls_line)
    return hls_lines


def get_psshs_from_manifest(manifest: str) -> PSSHs:
    psshs = PSSHs(set())
    hls_lines = parse_hls_lines('', manifest)
    for hls_line in hls_lines:
        if hls_line.name == 'EXT-X-SESSION-KEY' or hls_line.name == 'EXT-X-KEY':
            pssh = PSSH(hls_line.value['KEYFORMAT'], hls_line.url.split(',')[-1])
            psshs.append(pssh)
    return psshs


def parse_time_stamp_ms(timestamp: bytes) -> int:
    time_segments = timestamp.split(b':')
    time_ms = int(float(time_segments[-1]) * 1000)
    time_ms += int(time_segments[-2]) * 60 * 1000
    time_ms += int(time_segments[-3]) * 60 * 60 * 1000
    return time_ms


def dumps_time_stamp_ms(timestamp: int) -> bytes:
    hours = timestamp // (60*60*1000)
    minutes = (timestamp - hours*60*60*1000) // (60*1000)
    seconds = (timestamp - hours*60*60*1000 - minutes*60*1000) // 1000
    miliseconds = timestamp - hours*60*60*1000 - minutes*60*1000 - seconds*1000

    timestamp = b''
    timestamp += str(hours).rjust(2, '0').encode()
    timestamp += b':'
    timestamp += str(minutes).rjust(2, '0').encode()
    timestamp += b':'
    timestamp += str(seconds).rjust(2, '0').encode()
    timestamp += b'.'
    timestamp += str(miliseconds).rjust(3, '0').encode()
    return timestamp


def download_manifest(url: str, download_filename: Path, progresspaket: Progresspaket = None) -> list[Path]:
    progresspaket = progresspaket or Progresspaket('None')

    manifest = safe_get(url)
    hls_lines = parse_hls_lines(url, manifest.text)

    progress_index = len(progresspaket.progress_list)
    progresspaket.progress_list.append(0)

    downloaded_files: list[Path] = []
    current_file = None

    for hls_line in hls_lines:
        if hls_line.name == 'EXT-X-MAP':
            new_file = download_filename.with_stem(f'{download_filename.stem}_{len(downloaded_files)}')
            current_file = open(new_file, 'wb')
            downloaded_files.append(new_file)

            init_data = safe_get(hls_line.url)
            current_file.write(init_data.content)

        if hls_line.name == 'EXTINF':
            if current_file is None:
                new_file = download_filename.with_stem(f'{download_filename.stem}_{len(downloaded_files)}')
                current_file = open(new_file, 'wb')
                downloaded_files.append(new_file)

            fragment_data = safe_get(hls_line.url)
            if fragment_data.status_code != 200:
                raise RuntimeError(f"Download failed {fragment_data}")

            current_file.write(fragment_data.content)
            progresspaket.progress_list[progress_index] += 1 / manifest.text.count('#EXTINF')

        if hls_line.name == 'EXT-X-DISCONTINUITY':
            current_file.close()
            current_file = None

    return downloaded_files


class Video(BaseVideo):
    def __init__(self, hls_line: HLSLine, download_path: Path, progresspaket: Progresspaket = None):
        super().__init__()
        self.hls_line = hls_line
        self.download_path = download_path
        self.progresspaket = progresspaket or Progresspaket("None")

        self.url = hls_line.url

        self.width = 0
        self.height = 0
        self.bitrate = 0

        if not hls_line.value:
            return

        self.width = int(hls_line.value['RESOLUTION'].split('x')[0])
        self.height = int(hls_line.value['RESOLUTION'].split('x')[1])
        self.bitrate = int(hls_line.value['BANDWIDTH'])

        codecs = [c.split('.')[0] for c in hls_line.value['CODECS'].split(',')]
        self.codec = [c for c in codecs if c in self.codec_prio][0]
        self.audio_codec = [c for c in codecs if c in BaseAudio.codec_prio][0]

        self.audio_group = hls_line.value.get('AUDIO')

    def get_psshs(self) -> PSSHs:
        manifest = safe_get(self.url)
        return get_psshs_from_manifest(manifest.text)

    def download(self) -> list[Path]:
        return download_manifest(self.url, self.download_path / 'video.mp4', self.progresspaket)


class Audio(BaseAudio):

    def __init__(self, hls_line: HLSLine, download_path: Path, videos: list[Video], progresspaket: Progresspaket = None):
        super().__init__()

        self.hls_line = hls_line
        self.download_path = download_path
        self.videos = [video for video in videos if video.audio_group == hls_line.value.get('GROUP-ID', None)]
        self.progresspaket = progresspaket or Progresspaket("None")
        self.rendition_id = hls_line.value.get('STABLE-RENDITION-ID', None)

        self.url = hls_line.url
        self.language = hls_line.value.get('LANGUAGE')
        self.channels = int(hls_line.value.get('CHANNELS', '0').split('/')[0])
        self.is_atmos = '/JOC' in hls_line.value.get('CHANNELS', '')
        self.is_audio_description = 'CHARACTERISTICS' in hls_line.value and hls_line.value['CHARACTERISTICS'] == 'public.accessibility.describes-video'

        if not self.videos:
            log("WARN", f"Audio Group is not in any Video Variant: {hls_line.value.get('GROUP-ID', None)}")
            self.codec = "mp4a"
            self.bitrate = -1

        else:
            self.codec = self.videos[0].audio_codec
            self.bitrate = max(self.videos).bitrate

    def get_psshs(self) -> PSSHs:
        manifest = safe_get(self.url)
        return get_psshs_from_manifest(manifest.text)

    def download(self) -> list[Path]:
        download_filename = self.download_path / f'{self.language}.mp4'
        return download_manifest(self.url, download_filename, self.progresspaket)


class SubtitleBlock:
    def __init__(self, block: str | bytes):
        block = block.strip() if isinstance(block, bytes) else block.encode().strip()
        lines = block.splitlines()
        self.identifier = ''

        self.is_style = lines[0] == b'STYLE' or lines[0] == b'REGION'
        if self.is_style:
            self.text_lines = lines
            self.start_time = 0
            self.end_time = 0
            return

        timing_line = [line for line in lines if b'-->' in line][0]
        if lines.index(timing_line) != 0:
            self.identifier = lines[:lines.index(timing_line)][-1]

        self.start_time = parse_time_stamp_ms(timing_line.split(b'-->')[0].strip())
        self.end_time = parse_time_stamp_ms(timing_line.split(b'-->')[1].strip().split(b' ')[0])

        self.styling = b''.join(timing_line.split(b'-->')[1].strip().split(b' ', 1)[1:])
        self.text_lines = lines[lines.index(timing_line)+1:]

    def add_time(self, time_ms: int):
        self.start_time += time_ms
        self.end_time += time_ms

    def text(self):
        text = b'\n'.join(self.text_lines)
        if self.is_style:
            return text

        subtitle = b''
        if self.identifier:
            subtitle += self.identifier
            subtitle += b'\n'

        subtitle += dumps_time_stamp_ms(self.start_time)
        subtitle += b' --> '
        subtitle += dumps_time_stamp_ms(self.end_time)
        if self.styling:
            subtitle += b' '
            subtitle += self.styling

        subtitle += b'\n'
        subtitle += text
        return subtitle


def combine_subtitle_blocks(subtitle_blocks: list[SubtitleBlock]):
    new_subtitle_blocks: list[SubtitleBlock] = []
    skip_next = False
    for subtitle_block_index, subtitle_block in enumerate(subtitle_blocks):
        if skip_next:
            skip_next = False
            continue

        if subtitle_block_index == len(subtitle_blocks) - 1:
            new_subtitle_blocks.append(subtitle_block)
            break

        next_block = subtitle_blocks[subtitle_block_index+1]
        if subtitle_block.end_time == next_block.start_time and subtitle_block.text_lines == next_block.text_lines:
            subtitle_block.end_time = next_block.end_time
            skip_next = True
        new_subtitle_blocks.append(subtitle_block)

    # Filter out duplicate Blocks left from the previous step.
    for new_subtitle_block in new_subtitle_blocks:
        duplicates = [block for block in new_subtitle_blocks if block.text() == new_subtitle_block.text() and block != new_subtitle_block]
        for duplicate in duplicates:
            duplicate.identifier = None

    new_subtitle_blocks = [block for block in new_subtitle_blocks if block.identifier is not None]
    return new_subtitle_blocks


class Subtitle(BaseSubtitle):

    def __init__(self, hls_line: HLSLine, download_path: Path):
        super().__init__()
        self.hls_line = hls_line
        self.download_path = download_path

        self.codec = 'vtt'
        self.language = hls_line.value['LANGUAGE']
        self.rendition_id = hls_line.value.get('STABLE-RENDITION-ID', None)
        self.url = hls_line.url

        self.is_deaf = 'CHARACTERISTICS' in hls_line.value and hls_line.value['CHARACTERISTICS'] in ['public.accessibility.transcribes-spoken-dialog,public.accessibility.describes-music-and-sound', 'public.accessibility.describes-music-and-sound,public.accessibility.transcribes-spoken-dialog']
        self.forced = 'FORCED' in hls_line.value and hls_line.value['FORCED'] == 'YES'

        self.hls_lines = parse_hls_lines(self.url, safe_get(self.url).text)

    def download(self) -> list[Path]:
        filepath = (self.download_path / self.language).with_suffix('.vtt')
        if self.forced:
            filepath = (self.download_path / f"forced@{self.language}").with_suffix('.vtt')

        subtitle_files = download_manifest(self.url, filepath)
        return subtitle_files


class HLS(BaseDownloadProtocol):

    def __init__(self, sammelpaket: Sammelpaket):
        super().__init__(sammelpaket=sammelpaket)
        self.manifest_text = None
        self.hls_lines = None

    def init(self) -> None:
        self.manifest_text = safe_get(self.manifest_url, cookies=self.request_cookies, headers=self.request_headers).text
        self.hls_lines = parse_hls_lines(self.manifest_url, self.manifest_text)

        # Videos
        self._videos = [Video(hls_line, download_path=self.tmp_path, progresspaket=self.progresspaket) for hls_line in self.hls_lines if hls_line.name == 'EXT-X-STREAM-INF']
        if not self._videos:
            # video/audio are in the same file. And the current Manifest is this.
            video_hls_line = HLSLine(name='EXT-X-STREAM-INF', value=None, url=self.manifest_url)
            self._videos = [Video(video_hls_line, download_path=self.tmp_path, progresspaket=self.progresspaket)]

        # Audios
        for hls_line in self.hls_lines:
            if hls_line.name == 'EXT-X-MEDIA' and hls_line.value['TYPE'] == 'AUDIO':
                audio = Audio(hls_line, self.tmp_path, self._videos, progresspaket=self.progresspaket)
                if audio.rendition_id and audio.rendition_id in [a.rendition_id for a in self._audios]:
                    continue
                self._audios.append(audio)

        # Audio and Video is combined.
        if not self._audios:
            self._audios.append(Audio(self.video.hls_line, self.tmp_path, self._videos, progresspaket=self.progresspaket))

        # Subtitles
        for hls_line in self.hls_lines:
            if hls_line.name == 'EXT-X-MEDIA' and hls_line.value['TYPE'] == 'SUBTITLES':
                subtitle = Subtitle(hls_line, download_path=self.tmp_path)
                if subtitle.rendition_id and subtitle.rendition_id in [s.rendition_id for s in self._subtitles]:
                    continue
                self._subtitles.append(subtitle)

        # Closed Captions
        for hls_line in self.hls_lines:
            if hls_line.name == 'EXT-X-MEDIA' and hls_line.value['TYPE'] == 'CLOSED-CAPTIONS':
                log("WARN", f"HLS Manifest has Closed Captions: {self.manifest_url}")
                if hls_line.value['LANGUAGE'] not in [s.language for s in self._subtitles]:
                    raise RuntimeError(f"HLS Manifest has extra Closed Captions: {self.manifest_url}")

