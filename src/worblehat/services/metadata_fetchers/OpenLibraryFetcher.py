"""
A BookMetadataFetcher for the Open Library API.
"""

import requests

from worblehat.services.metadata_fetchers.BookMetadataFetcher import BookMetadataFetcher
from worblehat.services.metadata_fetchers.BookMetadata import BookMetadata

LANGUAGE_MAP = {
    "Norwegian": "no",
}


class OpenLibraryFetcher(BookMetadataFetcher):
    @classmethod
    def metadata_source_id(_cls) -> str:
      return "open_library"

    @classmethod
    def fetch_metadata(cls, isbn: str) -> BookMetadata | None:
        try:
            jsonInput = requests.get(f"https://openlibrary.org/isbn/{isbn}.json").json()

            author_keys = jsonInput.get("authors") or []
            author_names = set()
            for author_key in author_keys:
                key = author_key.get('key')
                author_name = requests.get(f"https://openlibrary.org/{key}.json").json().get("name")
                author_names.add(author_name)

            title = jsonInput.get("title")
            publishDate = jsonInput.get("publish_date")

            numberOfPages = jsonInput.get("number_of_pages")
            if numberOfPages:
                numberOfPages = int(numberOfPages)

            language_key = jsonInput.get("languages")[0].get("key")
            language = requests.get(f"https://openlibrary.org/{language_key}.json").json().get("identifiers").get("iso_639_1")[0]
            subjects = set(jsonInput.get("subjects") or [])

        except Exception:
            return None

        return BookMetadata(
            isbn = isbn,
            title = title,
            source = cls.metadata_source_id(),
            authors = author_names,
            language = language,
            publish_date = publishDate,
            num_pages = numberOfPages,
            subjects = subjects,
        )


if __name__ == '__main__':
    book_data = OpenLibraryFetcher.fetch_metadata('9788205530751')
    book_data.validate()
    print(book_data)