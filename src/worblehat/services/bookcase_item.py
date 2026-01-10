import isbnlib
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    Author,
    BookcaseItem,
    Language,
)
from .metadata_fetchers import fetch_metadata_from_multiple_sources


def is_valid_pvv_isbn(isbn: str) -> bool:
    try:
        int(isbn)
    except ValueError:
        return False
    return len(isbn) == 8


def is_valid_isbn(isbn: str) -> bool:
    return any(
        [
            isbnlib.is_isbn10(isbn),
            isbnlib.is_isbn13(isbn),
        ]
    )


def create_bookcase_item_from_isbn(
    isbn: str,
    sql_session: Session,
) -> BookcaseItem | None:
    """
    This function fetches metadata for the given ISBN and creates a BookcaseItem from it.
    It does so using a database connection to connect it to the correct authors and language
    through the sql ORM.

    If no metadata is found, None is returned.

    Please not that the returned BookcaseItem will likely not be fully populated with the required
    data, such as the book's location in the library, and the owner of the book, etc.
    """
    metadata = fetch_metadata_from_multiple_sources(isbn)
    if len(metadata) == 0:
        return None

    metadata = metadata[0]

    bookcase_item = BookcaseItem(
        name=metadata.title,
        isbn=int(isbn.replace("-", "")),
    )

    if len(authors := metadata.authors) > 0:
        for author in authors:
            bookcase_item.authors.add(Author(author))

    if language := metadata.language:
        bookcase_item.language = sql_session.scalars(
            select(Language).where(Language.iso639_1_code == language)
        ).one()

    return bookcase_item
