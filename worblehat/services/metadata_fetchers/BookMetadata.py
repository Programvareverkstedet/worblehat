from dataclasses import dataclass
from typing import Set

@dataclass
class BookMetadata:
    """
    A class representing the metadata for a book.

    Attributes:
        isbn (str): The ISBN of the book.
        title (str): The title of the book.
        authors (Set[str]): A set of authors of the book.
        language (str): The language of the book.
        publish_date (int): The publish date of the book.
        num_pages (int): The number of pages in the book.
        subjects (Set[str]): A set of subjects related to the book.
    """
    isbn: str
    title: str
    authors: Set[str]
    language: str
    publish_date: int
    num_pages: int
    subjects: Set[str]

    def to_dict(self) -> dict:
        
        dict = {
            'Isbn': self.isbn,
            'Title': self.title,
            'Authors': None,
            'Language': self.language,
            'Publish_date': self.publish_date,
            'Num_pages': self.num_pages,
            'Subjects': None
        }
        if self.authors is not None:
            dict['Authors'] = self.authors
        if self.subjects is not None:
            dict['Subjects'] = self.subjects
        
        return dict