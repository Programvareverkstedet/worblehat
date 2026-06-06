"""
A BookMetadataFetcher for the Open Library API.
"""

import requests

from worblehat.book_data_fetchers.BookData import BookData
from worblehat.book_data_fetchers.BookDataFetcher import BookDataFetcher

LANGUAGE_MAP = {
    "Norwegian": "no",
}


class OpenLibraryFetcher(BookDataFetcher):
    @classmethod
    def fetcher_id(_cls) -> str:
        return "open_library"

    @classmethod
    def try_fetch_data(cls, isbn: str) -> BookData | None:
        try:
            jsonInput = requests.get(f"https://openlibrary.org/isbn/{isbn}.json").json()

            author_keys = jsonInput.get("authors") or []
            author_names = set()
            for author_key in author_keys:
                key = author_key.get("key")
                author_name = requests.get(f"https://openlibrary.org/{key}.json").json().get("name")
                author_names.add(author_name)

            title = jsonInput.get("title")
            publishDate = jsonInput.get("publish_date")

            numberOfPages = jsonInput.get("number_of_pages")
            if numberOfPages:
                numberOfPages = int(numberOfPages)

            language_key = jsonInput.get("languages")[0].get("key")
            language = (
                requests.get(f"https://openlibrary.org/{language_key}.json")
                .json()
                .get("identifiers")
                .get("iso_639_1")[0]
            )
            subjects = set(jsonInput.get("subjects") or [])

        except Exception:
            return None

        return BookData(
            isbn=isbn,
            title=title,
            source=cls.fetcher_id(),
            authors=author_names,
            language=language,
            publish_date=publishDate,
            num_pages=numberOfPages,
            subjects=subjects,
        )
