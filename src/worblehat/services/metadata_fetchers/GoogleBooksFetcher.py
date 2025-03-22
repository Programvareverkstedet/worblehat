"""
A BookMetadataFetcher for the Google Books API.
"""

import requests

from worblehat.services.metadata_fetchers.BookMetadataFetcher import BookMetadataFetcher
from worblehat.services.metadata_fetchers.BookMetadata import BookMetadata


class GoogleBooksFetcher(BookMetadataFetcher):
    @classmethod
    def metadata_source_id(_cls) -> str:
        return "google_books"

    @classmethod
    def fetch_metadata(cls, isbn: str) -> BookMetadata | None:
        try:
            jsonInput = requests.get(
                "https://www.googleapis.com/books/v1/volumes",
                params={"q": f"isbn:{isbn}"},
            ).json()
            data = jsonInput.get("items")[0].get("volumeInfo")

            authors = set(data.get("authors") or [])
            title = data.get("title")
            publishDate = data.get("publish_date")
            numberOfPages = data.get("number_of_pages")
            if numberOfPages:
                numberOfPages = int(numberOfPages)
            subjects = set(data.get("categories") or [])
            languages = data.get("languages")
        except Exception:
            return None

        return BookMetadata(
            isbn=isbn,
            title=title,
            source=cls.metadata_source_id(),
            authors=authors,
            language=languages,
            publish_date=publishDate,
            num_pages=numberOfPages,
            subjects=subjects,
        )


if __name__ == "__main__":
    book_data = GoogleBooksFetcher.fetch_metadata("0132624788")
    book_data.validate()
    print(book_data)
