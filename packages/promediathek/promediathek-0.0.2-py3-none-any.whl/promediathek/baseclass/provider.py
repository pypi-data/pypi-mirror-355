from lib.baseclass import BaseAPI, BaseDownloadProtocol
from lib.pakete.sammelpaket import Sammelpaket, MovieSammelpaket, EpisodeSammelpaket


class BaseProvider:
    api: BaseAPI = None   # Init the provider API e. g. api = ArdAPI()

    def __init__(self):
        self.name = self.api.name

    def check_if_subscribed(self) -> bool:
        """
        Checks if the current login user has subscribed and can download anything.
        :return: True if subscribed, False otherwise
        """
        raise NotImplementedError

    def search(self, search_term: str) -> list[Sammelpaket]:
        all_sammelpakete = self.get_all()
        matching_sammelpakete = [sp for sp in all_sammelpakete if search_term.lower().strip() in sp.titel.lower()]
        return matching_sammelpakete

    def get_all_movies(self) -> list[MovieSammelpaket]:
        return []

    def get_all_episodes(self) -> list[EpisodeSammelpaket]:
        return []

    def get_downloader(self, sammelpaket: Sammelpaket) -> BaseDownloadProtocol:
        raise NotImplementedError

    def get_all(self) -> list[Sammelpaket]:
        return self.get_all_movies() + self.get_all_episodes()
