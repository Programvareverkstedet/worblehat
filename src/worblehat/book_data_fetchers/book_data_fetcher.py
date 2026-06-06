"""
this module contains the fetch_book_data_from_multiple_sources() function which combines all fetchers and returns ranked results (if any)

"""

from concurrent.futures import ThreadPoolExecutor

from worblehat.book_data_fetchers.BookData import BookData
from worblehat.book_data_fetchers.BookDataFetcher import BookDataFetcher
from worblehat.book_data_fetchers.fetchers.GoogleBooksFetcher import GoogleBooksFetcher
from worblehat.book_data_fetchers.fetchers.OpenLibraryFetcher import OpenLibraryFetcher
from worblehat.book_data_fetchers.fetchers.OutlandScraperFetcher import (
    OutlandScraperFetcher,
)

# The order of these fetchers determines the priority of the sources.
# The first fetcher in the list has the highest priority.
FETCHERS: list[BookDataFetcher] = [
    OpenLibraryFetcher,
    GoogleBooksFetcher,
    OutlandScraperFetcher,
]


FETCHER_SOURCE_IDS: list[str] = [fetcher.fetcher_id() for fetcher in FETCHERS]


def sort_data_by_priority(data: list[BookData]) -> list[BookData]:
    """
    Sorts the given data by the priority of the sources.

    The order of the data is the same as the order of the sources in the FETCHERS list.
    """

    # Note that this function is O(n^2) but the number of fetchers is small so it's fine.
    return sorted(data, key=lambda m: FETCHER_SOURCE_IDS.index(m.source))


def fetch_book_data_from_multiple_sources(isbn: str, strict: bool=False) -> list[BookData]:
    """
    Returns a list of data fetched from multiple fetchers.

    Fetchers that are not able to retrieve any data for the given ISBN will be ignored.

    There is no guarantee that there will be any book data.

    The results are always ordered in the same way as the fetchers are listed in the FETCHERS list.
    """
    isbn = isbn.replace("-", "").replace("_", "").strip().lower()
    if len(isbn) != 10 and len(isbn) != 13 and not isbn.isnumeric():
        raise ValueError("Invalid ISBN")

    results: list[BookData] = []

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetcher.try_fetch_data, isbn) for fetcher in FETCHERS]

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
            print(f"Invalid data: {e}")
            results.remove(result)

    return sort_data_by_priority(results)
