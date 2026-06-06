"""
A BookMetadataFetcher for the Google Books API.
"""

import requests

from worblehat.book_data_fetchers.BookData import BookData
from worblehat.book_data_fetchers.BookDataFetcher import BookDataFetcher


class GoogleBooksFetcher(BookDataFetcher):
    @classmethod
    def fetcher_id(_cls) -> str:
        return "google_books"

    @classmethod
    def try_fetch_data(cls, isbn: str) -> BookData | None:
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

        return BookData(
            isbn=isbn,
            title=title,
            source=cls.fetcher_id(),
            authors=authors,
            language=languages,
            publish_date=publishDate,
            num_pages=numberOfPages,
            subjects=subjects,
        )
