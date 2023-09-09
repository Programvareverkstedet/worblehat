from typing import Dict, Optional

# import isbnlib
#used these instead of isbnlib as i have already written the code for them
import json
import requests

from worblehat.services.metadata_fetchers.BookMetadataFetcher import BookMetadataFetcher
from worblehat.services.metadata_fetchers.BookMetadata import BookMetadata
from tsg.client import SyncTSGClient


class StorygraphFetcher(BookMetadataFetcher):

    def fetch_metadata(self, isbn: str) -> BookMetadata:
        
        client = SyncTSGClient()
        books = client.get_browse(text=isbn)
        
        if len(books) == 0:
            return None
        
        book = books[0]
        
        if book is None:
            return None
        
        if book.series is not None:
            series = book.series.name[0]
        else:
            series = None
            
        # parse the metadata into a BookMetadata object
        self.__metadata = BookMetadata(
            isbn = isbn,
            title = book.title,
            authors = book.author_names,
            language = None,
            publish_date = None,
            num_pages = None,
            subjects = series,
        )
        
        return self.__metadata
    

        
if __name__ == '__main__':
    fetcher = StorygraphFetcher()
    book_data = fetcher.fetch_metadata('9780593678510')
    print(book_data)