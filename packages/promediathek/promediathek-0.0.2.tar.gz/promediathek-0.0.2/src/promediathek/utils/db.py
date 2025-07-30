from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from sqlite3 import connect, OperationalError
from time import sleep

from promediapaket import ProMediaPaket

from lib.pakete.sammelpaket import Sammelpaket
from lib.pakete.bestandspaket import Bestandspaket, VideoQuality, AudioQuality, SubtitleQuality
from lib.ffmpeg import get_video_quality, get_audio_quality, get_subtitle_quality
from lib.utils.logger import log, enable_console_log

from lib.utils.pythonlib import classproperty


sql_types = {
    int: 'INTEGER',
    str: 'TEXT',
    bool: 'INTEGER'
}


class BestandspaketNotFound(Exception):
    pass


# noinspection PyPropertyDefinition
@dataclass
class DBSchema:

    # noinspection PyMethodParameters
    @classproperty
    def field_names(cls) -> list[str]:
        # noinspection PyTypeChecker
        field_names = list(cls.fields)
        return field_names

    # noinspection PyMethodParameters
    @classproperty
    def fields(cls) -> dict[str: type]:
        if cls == DBSchema:
            return {}

        # noinspection PyUnresolvedReferences
        base_fields = cls.__base__.fields
        fields = {field_name: field_type for field_name, field_type in cls.__dict__.items() if not field_name.startswith('_')}
        base_fields.update(fields)
        return base_fields

    @property
    def sql_safe_dict(self) -> dict[str: int | str]:
        safe_fields = {field_name: field_value.replace('"', '""') if isinstance(field_value, str) else field_value for field_name, field_value in self.__dict__.items()}
        safe_fields = {field_name: str(field_value).replace('"', '""') if isinstance(field_value, Path) else field_value for field_name, field_value in safe_fields.items()}
        return safe_fields


@dataclass
class DBTable:
    name: str
    schema: dataclass
    unique: str = None
    primary_key: str = None
    foreign_key: str = None
    foreign_table: str = None

    @property
    def create_cmd(self) -> str:
        sql_cmd = f'CREATE TABLE IF NOT EXISTS {self.name}('
        sql_cmd += ', '.join([f"{field_name} {sql_types[field_type]}" for field_name, field_type in self.schema.fields.items()])

        if self.primary_key:
            sql_cmd += f', PRIMARY KEY ({self.primary_key})'

        if self.foreign_key:
            sql_cmd += f", FOREIGN KEY ({self.foreign_key}) REFERENCES {self.foreign_table}"

        if self.unique:
            sql_cmd += f", UNIQUE ({self.unique}) ON CONFLICT REPLACE"

        sql_cmd += ')'
        return sql_cmd

    @property
    def insert_cmd(self) -> str:
        fields = {field_name: field_type for field_name, field_type in self.schema.fields.items() if field_name != self.primary_key}
        fields_template = {field_name: '"{' + field_name + '}"' if field_type is str else '{' + field_name + '}' for field_name, field_type in fields.items()}

        sql_cmd = f'INSERT INTO {self.name}('
        sql_cmd += ', '.join(fields_template)
        sql_cmd += ') VALUES ('
        sql_cmd += ', '.join(fields_template.values())
        sql_cmd += ')'
        if self.unique:
            sql_cmd += f' ON CONFLICT ({self.unique}) DO UPDATE SET '
            sql_cmd += ', '.join([f"{field_name}={field_template}" for field_name, field_template in fields_template.items()])

        if self.primary_key:
            sql_cmd += f' RETURNING {self.primary_key}'

        return sql_cmd


@dataclass
class Subtitle(DBSchema):
    key: int = int
    language: str = str
    codec: str = str
    forced: bool = bool


@dataclass
class Audio(DBSchema):
    key: int = int
    language: str = str
    codec: str = str
    channels: int = int
    bandwidth: int = int
    is_atmos: bool = bool


@dataclass
class Video(DBSchema):
    key: int = int
    bitrate: int = int
    codec: str = str
    width: int = int
    height: int = int


@dataclass
class Bestand(DBSchema):
    key = int            # primary key for DB
    provider: str = str  # provider name
    id: str = str        # id from provider
    pmp_path: str = str  # Path to ProMediaPaket file


db_schema = [
    DBTable(
        name="bestand",
        schema=Bestand,
        unique="provider, id",
        primary_key="key"
    ),
    DBTable(
        name="video",
        schema=Video,
        unique="key",
        foreign_table="bestand",
        foreign_key="key"
    ),
    DBTable(
        name="audio",
        schema=Audio,
        unique="key, language",
        foreign_table="bestand",
        foreign_key="key"
    ),
    DBTable(
        name="subtitle",
        schema=Subtitle,
        unique="key, language, forced",
        foreign_table="bestand",
        foreign_key="key"
    )
]


class ProDB:

    def __init__(self, db_path: PathLike | str = "promediathek.db"):
        self._db = None
        self._auto_commit_and_close = True  # Disable ONLY for high-throughput Operations

        self.db_path = db_path
        self.db_schema = {table.name: table for table in db_schema}

        self.db.execute('PRAGMA foreign_keys = ON')
        self.create_db()
        self.db_close()

    @property
    def db(self):
        if self._db:
            return self._db
        self._db = connect(self.db_path)
        return self._db

    def db_close(self):
        if self._db and self._auto_commit_and_close:
            self._db.close()
            self._db = None

    def db_commit(self):
        if self._auto_commit_and_close:
            self._db.commit()

    def create_db(self):
        for table in self.db_schema.values():
            sql_cmd = table.create_cmd
            self.execute(sql_cmd)

        self.db_commit()

    def execute(self, cmd, return_json=False):
        try:
            res = self.db.execute(cmd)
            if return_json:
                json_data = []
                for data in res.fetchall():
                    json_data.append({field_name[0]: data[field_num] for field_num, field_name in enumerate(res.description)})

                return json_data

            else:
                return res

        except OperationalError as exc:
            if 'locked' not in str(exc):
                raise exc

            log("WARN", "Database Locked.")
            sleep(1)
            return self.execute(cmd)

    def _fill_bestand(self, bestand_json: dict) -> Bestandspaket:
        video_key = bestand_json['key']
        video_json = self.execute(f"SELECT * FROM video WHERE key is \"{video_key}\"", return_json=True)[0]
        video_quality = VideoQuality(
            bitrate=video_json['bitrate'],
            codec=video_json['codec'],
            width=video_json['width'],
            height=video_json['height'],
        )

        audio_json = self.execute(f"SELECT * FROM audio WHERE key is \"{video_key}\"", return_json=True)
        audio_quality = [AudioQuality(
            language=audio['language'],
            codec=audio['codec'],
            channels=audio['channels'],
            bandwidth=audio['bandwidth'],
            is_atmos=bool(audio['is_atmos'])
        ) for audio in audio_json]

        subtitle_json = self.execute(f"SELECT * FROM subtitle WHERE key is \"{video_key}\"", return_json=True)
        subtitle_quality = [SubtitleQuality(
            language=subtitle['language'],
            codec=subtitle['codec'],
            forced=bool(subtitle['forced'])
        ) for subtitle in subtitle_json]

        bestandspaket = Bestandspaket(
            provider=bestand_json['provider'],
            id=bestand_json['id'],

            video=video_quality,
            audios=audio_quality,
            subtitles=subtitle_quality,
            pmp_path=bestand_json['pmp_path']
        )
        return bestandspaket

    def read_bestandspaket(self, sammelpaket: Sammelpaket) -> Bestandspaket:
        bestand_json = self.execute(f"SELECT * FROM bestand WHERE provider is \"{sammelpaket.provider}\" AND id is \"{sammelpaket.id}\"", return_json=True)
        if not bestand_json:
            self.db_close()
            raise BestandspaketNotFound("No bestand paket in DB.")

        bestandspaket = self._fill_bestand(bestand_json[0])
        self.db_close()
        return bestandspaket

    def read_all_bestandspakete(self) -> list[Bestandspaket]:
        all_bestand_json_plus_video = self.execute("SELECT *, video.key AS 'video_key', video.codec AS 'video_codec', audio.codec AS 'audio_codec', audio.language AS 'audio_language' FROM bestand JOIN video ON video.key == bestand.key LEFT JOIN audio ON audio.key == bestand.key LEFT JOIN subtitle ON video.key == subtitle.key", return_json=True)
        self.db_close()

        bestandspakete = []
        bestands_json = {}
        for bestand in all_bestand_json_plus_video:
            if bestand['video_key'] is None:
                log("WARN", f"DB Key is None, probably Audio missing: {bestand['id']}.")
                continue

            if bestand['video_key'] not in bestands_json:
                bestands_json[bestand['video_key']] = []

            bestands_json[bestand['video_key']].append(bestand)

        for bestand_json in bestands_json.values():
            video_quality = VideoQuality(
                bitrate=bestand_json[0]['bitrate'],
                codec=bestand_json[0]['video_codec'],
                width=bestand_json[0]['width'],
                height=bestand_json[0]['height'],
            )

            subtitle_quality = list({SubtitleQuality(
                language=subtitle['language'],
                codec=subtitle['codec'],
                forced=subtitle['forced']
            ) for subtitle in bestand_json if subtitle['forced'] is not None})

            if not subtitle_quality:
                audio_quality = [AudioQuality(
                    language=audio['audio_language'],
                    codec=audio['audio_codec'],
                    channels=audio['channels'],
                    bandwidth=audio['bandwidth'],
                    is_atmos=bool(audio['is_atmos'])
                ) for audio in bestand_json]

            else:
                audio_quality = list({AudioQuality(
                    language=audio['audio_language'],
                    codec=audio['audio_codec'],
                    channels=audio['channels'],
                    bandwidth=audio['bandwidth'],
                    is_atmos=bool(audio['is_atmos'])
                ) for audio in bestand_json})

            bestandspaket = Bestandspaket(
                provider=bestand_json[0]['provider'],
                id=bestand_json[0]['id'],

                video=video_quality,
                audios=audio_quality,
                subtitles=subtitle_quality,
                pmp_path=bestand_json[0]['pmp_path']
            )
            bestandspakete.append(bestandspaket)

        return bestandspakete

    def read_all_bestands_json(self) -> list[dict]:
        all_bestand_json = self.execute("SELECT * FROM bestand", return_json=True)
        self.db_close()
        return all_bestand_json

    def write_bestandspaket(self, bestandspaket: Bestandspaket) -> None:
        bestand = Bestand(
            provider=bestandspaket.provider,
            id=bestandspaket.id,
            pmp_path=bestandspaket.pmp_path
        )
        insert_cmd = self.db_schema["bestand"].insert_cmd
        insert_cmd = insert_cmd.format(**bestand.sql_safe_dict)
        key = self.execute(insert_cmd).fetchone()[0]

        if bestandspaket.video:
            video = Video(
                key=key,
                bitrate=bestandspaket.video.bitrate,
                codec=bestandspaket.video.codec,
                width=bestandspaket.video.width,
                height=bestandspaket.video.height
            )
            insert_cmd = self.db_schema["video"].insert_cmd
            insert_cmd = insert_cmd.format(**video.sql_safe_dict)
            self.execute(insert_cmd)

        for audio in bestandspaket.audios:
            audio = Audio(
                key=key,
                language=audio.language,
                codec=audio.codec,
                channels=audio.channels,
                bandwidth=audio.bandwidth,
                is_atmos=audio.is_atmos
            )
            insert_cmd = self.db_schema["audio"].insert_cmd
            insert_cmd = insert_cmd.format(**audio.sql_safe_dict)
            self.execute(insert_cmd)

        for subtitle in bestandspaket.subtitles:
            subtitle = Subtitle(
                key=key,
                language=subtitle.language,
                codec=subtitle.codec,
                forced=subtitle.forced
            )
            insert_cmd = self.db_schema["subtitle"].insert_cmd
            insert_cmd = insert_cmd.format(**subtitle.sql_safe_dict)
            self.execute(insert_cmd)

        self.db_commit()
        self.db_close()

    def remove_bestandspaket(self, bestandspaket: Bestandspaket) -> None:
        """
        Removes the Bestandspaket from the database, including all Video/Audio/Subtitle Information.
        :param bestandspaket:
        :return:
        """
        bestand_json = self.execute(f"SELECT * FROM bestand WHERE provider is \"{bestandspaket.provider}\" AND id is \"{bestandspaket.id}\"", return_json=True)[0]
        self.execute(f"DELETE FROM subtitle WHERE key is {bestand_json['key']}")
        self.execute(f"DELETE FROM audio WHERE key is {bestand_json['key']}")
        self.execute(f"DELETE FROM video WHERE key is {bestand_json['key']}")
        self.execute(f"DELETE FROM bestand WHERE key is {bestand_json['key']}")

        self.db_commit()
        self.db_close()

    def _already_downloaded(self, provider: str, provider_id: str) -> bool:
        res = self.execute(f"SELECT 1 FROM bestand where provider is \"{provider}\" and id is \"{provider_id}\"")
        downloaded = bool(res.fetchone())
        self.db_close()
        return downloaded

    def already_downloaded(self, sammelpaket: Sammelpaket) -> bool:
        return self._already_downloaded(sammelpaket.provider, sammelpaket.id)

    def sort_sammelpakete(self, sammelpakete: list[Sammelpaket]) -> list[Sammelpaket]:
        """
        Sorts the list of Sammelpaket in respect to which ones are already downloaded (they will be last).
        :param sammelpakete:
        :return:
        """
        return sorted(sammelpakete, key=lambda x: self.already_downloaded(x))

    def index_files(self, scan_folder: PathLike | str):
        for file in Path(scan_folder).rglob('*'):
            if file.suffix != '.pmp':
                continue

            provider = Path(file).stem.split('@')[0]
            provider_id = Path(file).stem.split('@')[1]
            if self._already_downloaded(provider, provider_id):
                continue

            bestandspaket = index_file(file)
            self.write_bestandspaket(bestandspaket)


def index_file(file: PathLike | str) -> Bestandspaket:

    print("INFO", f"Indexing {file}")
    pmp = ProMediaPaket.open(file)
    video_quality = get_video_quality(pmp.tmp_path / pmp.metadata.video_filepath)

    audio_quality = [
        get_audio_quality(pmp.tmp_path / "audios" / audio_file)
        for audio_file in pmp.metadata.audio_filepaths
    ]

    subtitle_quality = [
        get_subtitle_quality(pmp.tmp_path / "subtitles" / subtitle_file)
        for subtitle_file in pmp.metadata.subtitle_filepaths
    ]

    bestandspaket = Bestandspaket(
        provider=pmp.metadata.provider,
        id=pmp.metadata.provider_id,
        pmp_path=file,

        video=video_quality,
        audios=audio_quality,
        subtitles=subtitle_quality,
    )
    return bestandspaket


def repair_db() -> None:
    """
    Tries to find invalid Data, like Videos without Audio.
    :return:
    """
    db = ProDB()
    bestands_json = db.read_all_bestands_json()
    for bestand in bestands_json:
        video_key = bestand['key']
        audio_json = db.execute(f"SELECT * FROM audio WHERE key is \"{video_key}\"", return_json=True)
        if len(audio_json) == 0:
            log("WARN", f"Found Video without Audio removing: {bestand['provider']} {bestand['id']} {bestand['pmp_path']}")
            bestandspakete = db.read_bestandspaket(Sammelpaket.from_id(bestand['provider'], bestand['id']))
            db.remove_bestandspaket(bestandspakete)
            Path(bestand['pmp_path']).unlink(missing_ok=True)

        if bestand['pmp_path'] == 'None':
            log("WARN", f"Found PMP with Path None: {bestand['provider']} {bestand['id']}")
            bestandspakete = db.read_bestandspaket(Sammelpaket.from_id(bestand['provider'], bestand['id']))
            db.remove_bestandspaket(bestandspakete)

        if not Path(bestand['pmp_path']).exists():
            log("WARN", f"PMP file doesn't exist: {bestand['provider']} {bestand['id']} {bestand['pmp_path']}")
            bestandspakete = db.read_bestandspaket(Sammelpaket.from_id(bestand['provider'], bestand['id']))
            db.remove_bestandspaket(bestandspakete)

    print("Repair half complete")
    for file in Path().rglob('*'):
        if file.suffix != '.pmp':
            continue

        pmp = ProMediaPaket.metadata(file)
        try:
            db.read_bestandspaket(Sammelpaket.from_id(pmp.provider, pmp.provider_id))
        except BestandspaketNotFound:
            log("WARN", f"PMP File not in DB, deleting it: {file}")
            file.unlink()

    db.db_close()


if __name__ == '__main__':
    enable_console_log()
    repair_db()
