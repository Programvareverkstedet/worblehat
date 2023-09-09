"""
this module contains the fetch_book_metadata() function which fetches book metadata from multiple sources in threads and returns the higest ranked non-None result.

"""

import threading
from typing import List

from worblehat.services.metadata_fetchers.BookMetadata import BookMetadata
from worblehat.services.metadata_fetchers.GooglebooksFetcher import GoogleBooksFetcher
from worblehat.services.metadata_fetchers.OpenlibraryFetcher import OpenLibraryFetcher
from worblehat.services.metadata_fetchers.StorygraphFetcher import StorygraphFetcher
from worblehat.services.metadata_fetchers.OutlandScraperFetcher import OutlandScraperFetcher
#... import more fetchers here ...

def fetcher(isbn:str) -> (BookMetadata, List[BookMetadata]):
    """_summary_
        This function fetches book metadata from multiple sources in threads and returns the higest ranked non-None result.

    Args:
        isbn (str): isbn of the book to fetch metadata for

    Returns:
        tuple: (BookMetadata, List[BookMetadata]) where the first element is the metadata object and the second element is a list of metadata objects from all the fetchers
    """
    #clean up isbn
    isbn = isbn.replace('-', '').replace('_', '').strip().lower()
    #make sure isbn is valid
    if len(isbn) != 10 and len(isbn) != 13 and not isbn.isnumeric():
        raise ValueError('Invalid ISBN')
    
    # list of fetchers to fetch book metadata from
    open_library = OpenLibraryFetcher(isbn=isbn)
    google = GoogleBooksFetcher(isbn=isbn)
    storygraph = StorygraphFetcher(isbn=isbn)
    outland = OutlandScraperFetcher(isbn=isbn)
    
    #... create more fetchers objects here ...
    
    # Create a list of the objects in priority order
    fetchers = [
        open_library,
        google,
        storygraph,
        outland
        #... add more fetchers here ...
        ]
    
    metadata = None
    
    
    timeout = 15 # timeout in seconds for each fetcher
    
    # make thereads for each fetcher object and run the fetch_metadata() method for the fetcher in the thread with the given isbn as parameter collect the results in a list with a reference to the fetcher object
    results: List[BookMetadata] = [] # list of results in the same order as the fetchers list
    threads = [] # list of threads in the same order as the fetchers list
    
    def fetch_metadata(fetcher, isbn):
        index: int = fetchers.index(fetcher)
        try:
            data: BookMetadata = fetcher.fetch_metadata(isbn)
            results.insert(index, data)
        except Exception as e:
            results.insert(index, None)

    for fetcher in fetchers:
        thread = threading.Thread(target=fetch_metadata, args=(fetcher, isbn))
        threads.append(thread)
        thread.start()
        
    for thread in threads:
        thread.join(timeout)
    
    # iterate over the results list and return the first non-None result
    for result in results:
        if result is not None:
            #add non none result values to metadata where metadata has a none value
            if (metadata == None):
                metadata = result
            elif (metadata.isbn == None):
                metadata.isbn = result.isbn
            elif (metadata.title == None):
                metadata.title = result.title
            elif (metadata.authors == None or len(metadata.authors) == 0 or len(metadata.authors) < len(result.authors)):
                metadata.authors = result.authors
            elif (metadata.language == None):
                metadata.language = result.language
            elif (metadata.publish_date == None):
                metadata.publish_date = result.publish_date
            elif (metadata.num_pages == None):
                metadata.num_pages = result.num_pages
            elif (metadata.subjects == None or len(metadata.subjects) == 0 or len(metadata.subjects) < len(result.subjects)):
                metadata.subjects = result.subjects
            elif (metadata.isbn == None):
                metadata.isbn = result.isbn
                
    return metadata, results

def fetcher_dict(isbn:str) -> dict:
    """_summary_
        This function fetches book metadata from multiple sources in threads and returns the higest ranked non-None result.

    Args:
        isbn (str): isbn of the book to fetch metadata for

    Returns:
        dict: a dictionary of the metadata object
    """
    metadata = fetcher(isbn)[0]
    if metadata is None:
        return None
    elif len(metadata.to_dict().keys()) == 0:
        return None
    metadata = metadata.to_dict() # convert to dict to make it easier to work with
    return metadata

if __name__ == '__main__':
    isbn = '0132624788'
    metadata = fetcher(isbn)[0]
    print(metadata)