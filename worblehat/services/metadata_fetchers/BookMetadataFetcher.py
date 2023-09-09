#base fetcher.
from abc import ABC, abstractmethod
from typing import Optional
from worblehat.services.metadata_fetchers.BookMetadata import BookMetadata

class BookMetadataFetcher(ABC):
    __metadata: BookMetadata
    
    def __init__(self, isbn: Optional[str] = None):
        if isbn:
            self.fetch_metadata(isbn)
        else:
            self.__metadata = None
    
    #fetches metadata from the isbn and sets the attributes of the class
    @abstractmethod
    def fetch_metadata(self, isbn: str) -> BookMetadata:
        return self.__metadata
    
    def get_metadata(self) -> BookMetadata:
        return self.__metadata
