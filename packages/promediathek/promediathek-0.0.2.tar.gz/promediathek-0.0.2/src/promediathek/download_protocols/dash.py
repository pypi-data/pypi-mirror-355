from pathlib import Path
from dataclasses import dataclass
from re import search

from mpegdash.parser import MPEGDASHParser
from mpegdash.nodes import MPEGDASH, AdaptationSet, Representation, SegmentTemplate, S

from lib.baseclass.audio import BaseAudio
from lib.baseclass.subtitle import BaseSubtitle
from lib.baseclass.video import BaseVideo
from lib.ffmpeg import get_audio_channel_count
from lib.pakete.sammelpaket import Sammelpaket
from lib.drm.pssh import get_pssh_from_mp4_file, PSSHs
from lib.utils.logger import log
from lib.utils.networking import safe_get, safe_get_large

from lib.baseclass.downloader import BaseDownloadProtocol


@dataclass
class Manifest:
    manifest_url: str
    manifest_xml: str
    manifest: MPEGDASH
    adaptation_sets: list[AdaptationSet]
    download_path: Path
    request_cookies: dict = None
    request_headers: dict = None
    dash_self: dict = None


def get_adaption_set_type(adaption_set: AdaptationSet) -> str:
    if adaption_set.content_type:
        return adaption_set.content_type

    if adaption_set.mime_type:
        return adaption_set.mime_type.split('/')[0]

    if adaption_set.max_width or adaption_set.width or adaption_set.max_height or adaption_set.height or adaption_set.max_frame_rate or adaption_set.frame_rate:
        return 'video'

    if adaption_set.audio_channel_configurations:
        return 'audio'

    raise NotImplementedError


def get_absolute_base_url(manifest: Manifest, representation: Representation = None) -> str:
    base_url = manifest.manifest_url.rsplit('/', 1)[0]
    if manifest.manifest.base_urls:
        if len(manifest.manifest.base_urls) > 1:
            log("ERROR", "Multiple base URLs found!")
            raise NotImplementedError

        base_url_value = manifest.manifest.base_urls[0].base_url_value
        if base_url_value.startswith('http'):
            base_url = base_url_value

    if manifest.manifest.periods[0].base_urls:
        if len(manifest.manifest.periods[0].base_urls) > 1:
            log("ERROR", "Multiple base URLs found!")
            raise NotImplementedError

        base_url_value = manifest.manifest.periods[0].base_urls[0].base_url_value
        if base_url_value.startswith('http'):
            base_url = base_url_value

    if representation and representation.base_urls:
        if len(representation.base_urls) > 1:
            log("ERROR", "Multiple base URLs found!")
            raise NotImplementedError

        base_url_value = representation.base_urls[0].base_url_value
        if base_url_value.startswith('http'):
            base_url = base_url_value

    if not base_url.endswith('/'):
        base_url += '/'

    return base_url


def get_base_url(manifest: Manifest, representation: Representation = None):
    base_url = manifest.manifest_url.rsplit('/', 1)[0]
    if manifest.manifest.base_urls:
        base_url = manifest.manifest.base_urls

    if manifest.manifest.periods[0].base_urls:
        base_url = manifest.manifest.periods[0].base_urls

    if representation and representation.base_urls:
        base_url = representation.base_urls

    if isinstance(base_url, list):
        if len(base_url) > 1:
            log('ERROR', f"Multiple Base Urls: {base_url}")
            raise NotImplementedError

        base_url: str = base_url[0].base_url_value

    if not base_url.startswith('http'):
        base_url = get_absolute_base_url(manifest, representation) + base_url

    return base_url


def combine_templates(base_template, overwrite_template):
    """
    Combines two templates, whereas the values in overwrite_template get priority over base_template.
    :param base_template:
    :param overwrite_template:
    :return:
    """
    if base_template is None:
        return overwrite_template

    if overwrite_template is None:
        return base_template

    for i in overwrite_template.__dict__.keys():
        if overwrite_template.__getattribute__(i):
            base_template.__setattr__(i, overwrite_template.__getattribute__(i))

    return base_template


def get_segment_template(adaption_set: AdaptationSet, representation: Representation):
    if adaption_set.segment_templates and len(adaption_set.segment_templates) > 1:
        log('WARN', f'Multiple Segment Templates: {[s.initialization for s in adaption_set.segment_templates]}')

    if representation.segment_templates and len(representation.segment_templates) > 1:
        log('WARN', f'Multiple Segment Templates: {[s.initialization for s in representation.segment_templates]}')

    adaption_set_segment_template = adaption_set.segment_templates[0] if adaption_set.segment_templates else None
    representation_segment_template = representation.segment_templates[0] if representation.segment_templates else None

    segment_template = combine_templates(adaption_set_segment_template, representation_segment_template)
    return segment_template


def construct_url(base_url: str, representation: Representation, url: str = ''):
    url_template = base_url + url
    url_template = url_template.replace('$$', '$')
    url_template = url_template.replace('$RepresentationID$', representation.id)
    return url_template


def parse_timestamp(timestamp: str) -> float:
    if not timestamp.startswith('PT'):
        log('ERROR', f"Unknown Timestamp: {timestamp}")

    timestamp = timestamp[2:]
    time_in_second = 0
    last_chars = ''
    for char in timestamp:
        if char.isdigit():
            last_chars += char

        elif char == 'H':
            time_in_second += int(last_chars)*60*60
            last_chars = ''

        elif char == 'M':
            time_in_second += int(last_chars)*60
            last_chars = ''

        elif char == '.':
            last_chars += char

        elif char == 'S':
            time_in_second += float(last_chars)
            last_chars = ''

        else:
            log('ERROR', f'Unknown Timestamp Char: {timestamp}')

    return time_in_second


class SegmentTemplateDownloader:
    def __init__(self, manifest: Manifest, segment_template: SegmentTemplate):
        self.manifest = manifest
        self.segment_template = segment_template
        self.ignore_error_on_last_fragment = False
        if self.segment_template is None:
            return

        self.segment_url = segment_template.media

        if segment_template.segment_timelines:
            if len(segment_template.segment_timelines) > 1:
                log('WARN', f"Multiple Segment Timelines: {self.segment_url}")

            self.segment_timeline: list[S] = segment_template.segment_timelines[0].Ss
            self.segments_amount = len(self.segment_timeline) + sum([s_node.r if s_node.r else 0 for s_node in self.segment_timeline])

        # $Number$
        self.start_number = 0
        if search(r"\$Number(%0(\d+)d|)\$", self.segment_url):
            self.start_number = self.segment_template.start_number
            if not segment_template.segment_timelines:
                video_segments_time = segment_template.duration/segment_template.timescale
                video_time = parse_timestamp(self.manifest.manifest.media_presentation_duration)
                self.segments_amount = (video_time/video_segments_time).__ceil__()
                if round(video_time/video_segments_time, 2) < self.segments_amount:
                    self.ignore_error_on_last_fragment = True

            elif self.segment_template.end_number and self.segments_amount != self.segment_template.end_number:
                log('WARN', f"{self.segments_amount=} != {self.segment_template.end_number=}")

        # $Time$
        self.start_time = 0
        self.segment_durations = []
        if '$Time$' in self.segment_url:
            self.start_time = segment_template.segment_timelines[0].Ss[0].t
            for s_node in segment_template.segment_timelines[0].Ss:
                self.segment_durations.append(s_node.d)
                if s_node.r:
                    self.segment_durations += [s_node.d for _ in range(s_node.r)]

    def download_init(self, base_url: str, representation: Representation) -> bytes:
        if self.segment_template is None:
            media_url = construct_url(base_url=base_url, representation=representation)
            headers = {
                'Range': f"bytes={representation.segment_bases[0].initializations[0].range}"
            }
            if self.manifest.request_headers:
                headers.update(self.manifest.request_headers)

            init_data = safe_get(media_url, headers=headers, cookies=self.manifest.request_cookies).content
            return init_data

        initialization_url = construct_url(base_url=base_url, representation=representation, url=self.segment_template.initialization)
        init_data = safe_get(initialization_url, cookies=self.manifest.request_cookies, headers=self.manifest.request_headers).content
        return init_data

    def download(self, base_url: str, representation: Representation, filename: str) -> Path:
        filepath = self.manifest.download_path / filename
        filepath.parent.mkdir(exist_ok=True, parents=True)

        if self.segment_template is None:
            media_url = construct_url(base_url=base_url, representation=representation)
            safe_get_large(url=media_url, outfile=filepath, progresspaket=self.manifest.dash_self.progresspaket)
            return filepath

        media_url_template = construct_url(base_url=base_url, representation=representation, url=self.segment_url)
        number_regex = search(r"\$Number(%0(\d+)d|)\$", media_url_template)
        progresspaket_index = len(self.manifest.dash_self.progresspaket.progress_list)
        self.manifest.dash_self.progresspaket.progress_list.append(0)

        open(filepath, 'wb').write(self.download_init(base_url=base_url, representation=representation))
        with open(filepath, 'ab') as file:
            for segment_number in range(self.segments_amount):
                if '$Number$' in media_url_template:
                    media_url = media_url_template.replace('$Number$', str(self.start_number + segment_number))

                elif number_regex:
                    number_padding = int(number_regex.group(2))
                    media_url = media_url_template.replace(number_regex.group(0), str(self.start_number + segment_number).rjust(number_padding, '0'))

                if '$Time$' in media_url_template:
                    media_url = media_url_template.replace('$Time$', str(self.start_time + sum(self.segment_durations[:segment_number])))

                media_response = safe_get(media_url, cookies=self.manifest.request_cookies, headers=self.manifest.request_headers)
                if media_response.status_code != 200 or not media_response.content:
                    if segment_number == self.segments_amount - 1 and self.ignore_error_on_last_fragment:
                        log("WARN", f"Expected error on last DASH Segment, can be ignored: {self.manifest.manifest_url}")
                        continue

                    log("ERROR", f'DASH Fragment Error: {media_response.status_code} {media_response.content}')
                    raise RuntimeError(f'DASH Fragment Error: {media_response.status_code} {media_response.content}')

                file.write(media_response.content)
                self.manifest.dash_self.progresspaket.progress_list[progresspaket_index] = segment_number/self.segments_amount

        return filepath


class Video(BaseVideo):
    def __init__(self, manifest: Manifest, adaption_set: AdaptationSet, representation: Representation):
        super().__init__()

        self.manifest = manifest
        self.adaption_set = adaption_set
        self.representation = representation

        self.bitrate = self.representation.bandwidth
        self.width = self.representation.width or self.adaption_set.width or 0
        self.height = self.representation.height or self.adaption_set.height or 0

        self.codec = self.representation.codecs or adaption_set.codecs
        self.codec = self.codec.split('.')[0]

        self.base_url = get_base_url(manifest=self.manifest, representation=self.representation)
        segment_template = get_segment_template(adaption_set=self.adaption_set, representation=self.representation)
        self.segment_template = SegmentTemplateDownloader(manifest=self.manifest, segment_template=segment_template)

    def download(self) -> list[Path]:
        filename = 'video.mp4'
        video_file = self.segment_template.download(base_url=self.base_url, representation=self.representation, filename=filename)
        return [video_file]

    def get_psshs(self) -> PSSHs:
        video_init = self.segment_template.download_init(self.base_url, self.representation)
        return get_pssh_from_mp4_file(video_init)


class Audio(BaseAudio):
    def __init__(self, manifest: Manifest, adaption_set: AdaptationSet):
        super().__init__()

        self.manifest = manifest
        self.adaption_set = adaption_set
        self.language: str = adaption_set.lang

        self.is_audio_description = False
        if adaption_set.roles:
            self.is_audio_description = adaption_set.roles[0].value == 'description'

        elif adaption_set.accessibilities:
            self.is_audio_description = adaption_set.accessibilities[0].value == 'description'

        representations: list[Representation] = adaption_set.representations
        best_resolution = max([representation.bandwidth for representation in representations])
        best_representation = [representation for representation in representations if representation.bandwidth == best_resolution]

        if len(best_representation) > 1:
            log('WARN', f'Multiple Best Representations: {manifest.manifest_url}')
            if best_representation[0].base_urls:
                best_representation.sort(key=lambda x: int(''.join(c for c in x.base_urls[0].base_url_value if c.isdigit())), reverse=True)

        self.representation = best_representation[0]

        self.bitrate: int = self.representation.bandwidth
        self.codec: str = self.representation.codecs or adaption_set.codecs
        self.codec = self.codec.split('.')[0]

        self.is_atmos = False
        if adaption_set.supplemental_properties:
            for supplemental_property in adaption_set.supplemental_properties:
                if supplemental_property.scheme_id_uri == 'tag:dolby.com,2018:dash:EC3_ExtensionType:2018' and supplemental_property.value == 'JOC':
                    self.is_atmos = True

        if self.representation.supplemental_properties:
            for supplemental_property in self.representation.supplemental_properties:
                if supplemental_property.scheme_id_uri == 'tag:dolby.com,2018:dash:EC3_ExtensionType:2018' and supplemental_property.value == 'JOC':
                    self.is_atmos = True

        self.base_url = get_base_url(manifest=self.manifest, representation=self.representation)
        segment_template = get_segment_template(adaption_set=self.adaption_set, representation=self.representation)
        self.segment_template = SegmentTemplateDownloader(manifest=self.manifest, segment_template=segment_template)

        self.channels = self.get_channels_count()

    def get_channels_count(self) -> int:
        if self.representation.audio_channel_configurations and self.representation.audio_channel_configurations[0].value == "2":
            return 2

        elif self.adaption_set.audio_channel_configurations and self.adaption_set.audio_channel_configurations[0].value == "2":
            return 2

        init_data = self.segment_template.download_init(base_url=self.base_url, representation=self.representation)
        init_file = self.manifest.download_path / (str(self.language) + '-init.mp4')
        init_file.write_bytes(init_data)
        audio_channels = get_audio_channel_count(init_file)
        return audio_channels

    def download(self) -> list[Path]:
        filename = self.language + '.mp4' if self.language else f"{self.adaption_set.id}.mp4"
        audio_file = self.segment_template.download(base_url=self.base_url, representation=self.representation, filename=filename)
        return [audio_file]

    def get_psshs(self) -> PSSHs:
        audio_init = self.segment_template.download_init(self.base_url, self.representation)
        return get_pssh_from_mp4_file(audio_init)


class Subtitle(BaseSubtitle):
    def __init__(self, manifest: Manifest, adaption_set: AdaptationSet):
        super().__init__()

        self.manifest = manifest
        self.adaption_set = adaption_set
        self.language: str = adaption_set.lang

        self.role: str = adaption_set.roles[0].value if adaption_set.roles else None
        self.forced = self.role == 'forced-subtitle'

        if len(adaption_set.representations) > 1:
            log('WARN', f'Multiple Subtitle Representations: {[r.id for r in adaption_set.representations]}')
            raise RuntimeError('Multiple Subtitle Representations')

        self.representation = adaption_set.representations[0]

        self.codec: str = self.representation.codecs or adaption_set.codecs
        self.mime_type: str = self.representation.mime_type or adaption_set.mime_type

        self.base_url = get_base_url(manifest=self.manifest, representation=self.representation)
        self.segment_template = get_segment_template(adaption_set=self.adaption_set, representation=self.representation)
        if self.segment_template:
            self.segment_template = SegmentTemplateDownloader(manifest=self.manifest, segment_template=self.segment_template)

        if self.codec is None and self.mime_type:
            self.codec = self.mime_type.split('/')[-1]

    def download(self) -> list[Path]:
        filename = self.language + '.mp4'
        if self.forced:
            filename = 'forced@' + filename

        if self.segment_template:
            subtitle_file = self.segment_template.download(base_url=self.base_url, representation=self.representation, filename=filename)

        else:
            subtitle_file = Path(self.manifest.download_path, filename).with_suffix('.' + self.mime_type.split('/')[-1])
            subtitle_text = safe_get(self.base_url, cookies=self.manifest.request_cookies, headers=self.manifest.request_headers).content
            subtitle_file.write_bytes(subtitle_text)

        return [subtitle_file]


class Dash(BaseDownloadProtocol):

    def __init__(self, sammelpaket: Sammelpaket):
        super().__init__(sammelpaket)
        self.manifest = None

    def init(self):
        manifest_response = safe_get(self.manifest_url, cookies=self.request_cookies, headers=self.request_headers)
        manifest_url = manifest_response.url
        manifest_xml = manifest_response.text

        if not manifest_xml:
            log('ERROR', f'No Manifest: {manifest_url}')
            raise RuntimeError(f'No Manifest: {manifest_url}')

        manifest = MPEGDASHParser.parse(manifest_xml)
        adaptation_sets = manifest.periods[0].adaptation_sets

        if len(manifest.periods) > 1:
            log('WARN', f"Multiple Periods! {manifest_url}")
            raise NotImplementedError

        # noinspection PyTypeChecker
        self.manifest = Manifest(
            manifest_url=manifest_url,
            manifest_xml=manifest_xml,
            manifest=manifest,
            adaptation_sets=adaptation_sets,
            download_path=self.tmp_path,
            request_cookies=self.request_cookies,
            request_headers=self.request_headers,
            dash_self=self
        )

        self._videos = [Video(self.manifest, adaption_set, representation) for adaption_set in self.manifest.adaptation_sets if get_adaption_set_type(adaption_set) == 'video' for representation in adaption_set.representations]
        self._audios = [Audio(self.manifest, adaption_set) for adaption_set in self.manifest.adaptation_sets if get_adaption_set_type(adaption_set) == 'audio']
        self._subtitles = [Subtitle(self.manifest, adaption_set) for adaption_set in self.manifest.adaptation_sets if get_adaption_set_type(adaption_set) == 'text']
