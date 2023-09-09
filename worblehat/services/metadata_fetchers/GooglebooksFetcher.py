"""
This module provides a class for fetching book metadata from Google Books API.

The class `GoogleBooksFetcher` implements the `BookMetadataFetcher` interface and provides a method `fetch_metadata`
that takes an ISBN as input and returns a `BookMetadata` object containing the metadata for the book with the given ISBN.

Example:
    To fetch metadata for a book with ISBN '0132624788', create an instance of `GoogleBooksFetcher` and call its
    `fetch_metadata` method:

    >>> fetcher = GoogleBooksFetcher()
    >>> book_data = fetcher.fetch_metadata('0132624788')
    >>> print(book_data)
    BookMetadata(isbn='0132624788', title='Elements of the theory of computation', authors=['Harry R. Lewis'], language='English', publish_date=1998, num_pages=361, subjects=['Machine theory.', 'Formal languages.', 'Computational complexity.', 'Logic, Symbolic and mathematical.'])
"""

from typing import Dict, Optional
import json
import requests

from worblehat.services.metadata_fetchers.BookMetadataFetcher import BookMetadataFetcher
from worblehat.services.metadata_fetchers.BookMetadata import BookMetadata

class GoogleBooksFetcher(BookMetadataFetcher):
    """
    A class for fetching book metadata from Google Books API.

    This class implements the `BookMetadataFetcher` interface and provides a method `fetch_metadata`
    that takes an ISBN as input and returns a `BookMetadata` object containing the metadata for the book with the given ISBN.
    """

    def fetch_metadata(self, isbn: str) -> BookMetadata:
        """
        Fetches book metadata for the given ISBN from Google Books API.

        Args:
            isbn (str): The ISBN of the book to fetch metadata for.

        Returns:
            BookMetadata: A `BookMetadata` object containing the metadata for the book with the given ISBN.
            Returns `None` if no metadata is found for the given ISBN.
        """
        metadata = self.__googlebooks__(isbn)
        if not metadata or len(metadata.keys()) == 0 or (not metadata.get('Title') and not metadata.get('Authors') and not metadata.get('Language')):
            return None
        
        # parse the metadata into a BookMetadata object
        self.__metadata__ = BookMetadata(
            isbn = isbn,
            title = metadata.get('Title'),
            authors = metadata.get('Authors'),
            language = metadata.get('Language'),
            publish_date = metadata.get('PublishDate'),
            num_pages = metadata.get('NumberOfPages'),
            subjects = metadata.get('Subjects'),
        )
        return self.__metadata__
    
    def __googlebooks__(self, isbn):    
        """
        Internal method do not use.
        Fetches book metadata for the given ISBN from Google Books API.
        """
        try:
            jsonInput = json.loads(requests.get("https://openlibrary.org/isbn/"+str(isbn)+".json").text)
            #format data to standard format.
            authors = jsonInput.get("authors")
            for i in range(len(authors)):
                authors[i] = json.loads(requests.get("https://openlibrary.org"+str(authors[i].get("key"))+".json").text).get("name")
            authors = list(set(authors))

            title = jsonInput.get("title")
            publishDate = jsonInput.get("publish_date")
            numberOfPages = jsonInput.get("number_of_pages")
            genre = jsonInput.get("subjects")
            language = jsonInput.get("languages")[0]
            language = json.loads(requests.get("https://openlibrary.org"+language.get("key")+".json").text).get("name")
            subjects = jsonInput.get("subjects")

            #create a dictionary to represent a book and its data
            bookData = {
                        "Authors": authors,
                        "Title": title,
                        "PublishDate": int(publishDate),
                        "NumberOfPages": numberOfPages,
                        "Genre": genre,
                        "Language": language,
                        "Subjects": subjects
                        } 
            return bookData
        except:
            return False


if __name__ == '__main__':
    fetcher = GoogleBooksFetcher()
    book_data = fetcher.fetch_metadata('0132624788')
    print(book_data)