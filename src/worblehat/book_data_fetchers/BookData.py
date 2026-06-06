from dataclasses import dataclass
from typing import Any

# TODO: Add more languages
LANGUAGES: set[str] = {
    "no",
    "en",
    "de",
    "fr",
    "es",
    "it",
    "sv",
    "da",
    "fi",
    "ru",
    "zh",
    "ja",
    "ko",
}


@dataclass
class BookData:
    """
    A class representing metadata for a book that we might want to fetch from external sources
    """

    isbn: str
    title: str
    # ID of the data fetcher used to fetch this instance
    source: str
    authors: set[str]
    language: str | None
    publish_date: str | None
    num_pages: int | None
    subjects: set[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "isbn": self.isbn,
            "title": self.title,
            "source": self.source,
            "authors": set() if self.authors is None else self.authors,
            "language": self.language,
            "publish_date": self.publish_date,
            "num_pages": self.num_pages,
            "subjects": set() if self.subjects is None else self.subjects,
        }

    def validate(self) -> None:
        if not self.isbn:
            raise ValueError("Missing ISBN")
        if not self.title:
            raise ValueError("Missing title")
        if not self.source:
            raise ValueError("Missing source")
        if not self.authors:
            raise ValueError("Missing authors")

        if self.language is not None and self.language not in LANGUAGES:
            raise ValueError(
                f"Invalid language: {self.language}. Consider adding it to the LANGUAGES set if you think this is a mistake.",
            )

        if self.num_pages is not None and self.num_pages < 0:
            raise ValueError(f"Invalid number of pages: {self.num_pages}")
