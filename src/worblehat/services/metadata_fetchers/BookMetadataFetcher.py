# base fetcher.
from abc import ABC, abstractmethod
from .BookMetadata import BookMetadata


class BookMetadataFetcher(ABC):
    """
    A base class for metadata fetchers.
    """

    @classmethod
    @abstractmethod
    def metadata_source_id(cls) -> str:
        """Returns a unique identifier for the metadata source, to identify where the metadata came from."""
        pass

    @classmethod
    @abstractmethod
    def fetch_metadata(cls, isbn: str) -> BookMetadata | None:
        """Tries to fetch metadata for the given ISBN."""
        pass
