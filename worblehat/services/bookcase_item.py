import isbnlib

from worblehat.services.metadata_fetchers.book_metadata_fetcher import fetcher_dict

from sqlalchemy import select
from sqlalchemy.orm import Session

from worblehat.models import (
    Author,
    BookcaseItem,
    Language,
)

def is_valid_pvv_isbn(isbn: str) -> bool:
  try:
      int(isbn)
  except ValueError:
      return False
  return len(isbn) == 8


def is_valid_isbn(isbn: str) -> bool:
    return any([
        isbnlib.is_isbn10(isbn),
        isbnlib.is_isbn13(isbn),
    ])


def create_bookcase_item_from_isbn(isbn: str, sql_session: Session) -> BookcaseItem | None:
    # metadata = isbnlib.meta(isbn, 'openl')
    
    
    metadata = fetcher_dict(isbn)
    
    if len(metadata.keys()) == 0:
        return None

    bookcase_item = BookcaseItem(
        name = metadata.get('Title'),
        isbn = int(isbn.replace('-', '')),
    )

    if len(authors := metadata.get('Authors')) > 0:
        for author in authors:
            bookcase_item.authors.add(Author(author))

    if (language := metadata.get('Language')):
        bookcase_item.language = sql_session.scalars(
            select(Language)
            .where(Language.iso639_1_code == language)
        ).one()

    return bookcase_item


# if __name__ == '__main__':
#     item = create_bookcase_item_from_isbn('9780593678510', None)
#     print(item)