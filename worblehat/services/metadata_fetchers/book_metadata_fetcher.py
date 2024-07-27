"""
this module contains the fetch_book_metadata() function which fetches book metadata from multiple sources in threads and returns the higest ranked non-None result.

"""

from concurrent.futures import ThreadPoolExecutor

from worblehat.services.metadata_fetchers.BookMetadata import BookMetadata
from worblehat.services.metadata_fetchers.BookMetadataFetcher import BookMetadataFetcher

from worblehat.services.metadata_fetchers.GoogleBooksFetcher import GoogleBooksFetcher
from worblehat.services.metadata_fetchers.OpenLibraryFetcher import OpenLibraryFetcher
from worblehat.services.metadata_fetchers.OutlandScraperFetcher import OutlandScraperFetcher


# The order of these fetchers determines the priority of the sources.
# The first fetcher in the list has the highest priority.
FETCHERS: list[BookMetadataFetcher] = [
    OpenLibraryFetcher,
    GoogleBooksFetcher,
    OutlandScraperFetcher,
]


FETCHER_SOURCE_IDS: list[str] = [fetcher.metadata_source_id() for fetcher in FETCHERS]


def sort_metadata_by_priority(metadata: list[BookMetadata]) -> list[BookMetadata]:
    """
    Sorts the given metadata by the priority of the sources.

    The order of the metadata is the same as the order of the sources in the FETCHERS list.
    """

    # Note that this function is O(n^2) but the number of fetchers is small so it's fine.
    return sorted(metadata, key=lambda m: FETCHER_SOURCE_IDS.index(m.source))


def fetch_metadata_from_multiple_sources(isbn: str, strict=False) -> list[BookMetadata]:
    """
    Returns a list of metadata fetched from multiple sources.

    Sources that does not have metadata for the given ISBN will be ignored.

    There is no guarantee that there will be any metadata.

    The results are always ordered in the same way as the fetchers are listed in the FETCHERS list.
    """
    isbn = isbn.replace('-', '').replace('_', '').strip().lower()
    if len(isbn) != 10 and len(isbn) != 13 and not isbn.isnumeric():
        raise ValueError('Invalid ISBN')

    results: list[BookMetadata] = []

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetcher.fetch_metadata, isbn) for fetcher in FETCHERS]

    for future in futures:
        result = future.result()
        if result is not None:
            results.append(result)

    for result in results:
        try:
            result.validate()
        except ValueError as e:
            if strict:
                raise e
            else:
                print(f'Invalid metadata: {e}')
                results.remove(result)

    return sort_metadata_by_priority(results)


if __name__ == '__main__':
    from pprint import pprint
    isbn = '0132624788'
    metadata = fetch_metadata_from_multiple_sources(isbn)
    pprint(metadata)