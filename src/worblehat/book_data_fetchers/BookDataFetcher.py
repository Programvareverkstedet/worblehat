# base fetcher.
from abc import ABC, abstractmethod

from .BookData import BookData


class BookDataFetcher(ABC):
    """
    A base class for adapters that fetch book data from external sources.
    """

    @classmethod
    @abstractmethod
    def fetcher_id(cls) -> str:
        """Returns a unique identifier for this specific fetcher, to identify where the data came from."""
        pass

    @classmethod
    @abstractmethod
    def try_fetch_data(cls, isbn: str) -> BookData | None:
        """Tries to fetch data for the given ISBN."""
        pass
