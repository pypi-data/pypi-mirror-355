from dataclasses import dataclass


@dataclass(frozen=True, eq=True)
class Sammelpaket:
    type: str  # movie episode
    provider: str  # provider name
    id: str  # id from provider

    titel: str
    description: str

    @property
    def valid(self) -> bool:
        str_properties = [self.type, self.provider, self.id, self.titel, self.description]
        if all([isinstance(p, str) for p in str_properties]):
            return True
        return False

    @classmethod
    def from_id(cls, provider: str, provider_id: str) -> "Sammelpaket":
        return cls('None', provider, provider_id, 'None', 'None')


@dataclass(frozen=True, eq=True)
class MovieSammelpaket(Sammelpaket):
    movie_thumbnail_vertical: str | None
    movie_thumbnail_horizontal: str | None

    @property
    def valid(self) -> bool:
        if not (isinstance(self.movie_thumbnail_vertical, str) or self.movie_thumbnail_vertical is None):
            return False
        if not (isinstance(self.movie_thumbnail_horizontal, str) or self.movie_thumbnail_horizontal is None):
            return False

        return super().valid


@dataclass(frozen=True, eq=True)
class MovieExtrasSammelpaket(MovieSammelpaket):
    main_movie_id: str

    @property
    def valid(self) -> bool:
        if not (isinstance(self.main_movie_id, str) and self.main_movie_id):
            return False

        return super().valid


@dataclass(frozen=True, eq=True)
class EpisodeSammelpaket(Sammelpaket):
    series_title: str
    series_description: str

    series_id: str
    season_id: str

    season_number: str
    episode_number: str

    series_thumbnail_vertical: str | None = None
    series_thumbnail_horizontal: str | None = None

    episode_thumbnail_vertical: str | None = None
    episode_thumbnail_horizontal: str | None = None

    @property
    def valid(self) -> bool:
        str_properties = [self.series_title, self.series_description, self.series_id, self.season_id, self.season_number, self.episode_number]
        if not all([isinstance(p, str) for p in str_properties]):
            return False

        if not (isinstance(self.series_thumbnail_vertical, str) or self.series_thumbnail_vertical is None):
            return False
        if not (isinstance(self.series_thumbnail_horizontal, str) or self.series_thumbnail_horizontal is None):
            return False

        if not (isinstance(self.episode_thumbnail_vertical, str) or self.episode_thumbnail_vertical is None):
            return False
        if not (isinstance(self.episode_thumbnail_horizontal, str) or self.episode_thumbnail_horizontal is None):
            return False

        return super().valid


test_sammelpaket = Sammelpaket(
    type="movie",
    provider="test",
    id="test_id",
    titel="test_title",
    description="test_description",
)
