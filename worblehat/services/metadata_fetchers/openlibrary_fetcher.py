from typing import Dict, Optional

# import isbnlib
#used these instead of isbnlib as i have already written the code for them
import json
import requests

from worblehat.services.metadata_fetchers.base_fetcher import BookMetadataFetcher
from worblehat.models.BookMetadata import BookMetadata

class OpenLibraryFetcher(BookMetadataFetcher):

    def fetch_metadata(self, isbn: str) -> BookMetadata:
        metadata = self.__openLibrary(isbn)
        if not metadata or len(metadata.keys()) == 0 or (not metadata.get('Title') and not metadata.get('Authors') and not metadata.get('Language')):
            return None
        
        # parse the metadata into a BookMetadata object
        self.__metadata = BookMetadata(
            isbn = isbn,
            title = metadata.get('Title'),
            authors = metadata.get('Authors'),
            language = metadata.get('Language'),
            publish_date = metadata.get('PublishDate'),
            num_pages = metadata.get('NumberOfPages'),
            subjects = metadata.get('Subjects'),
        )
        return self.__metadata
    

    #create a dictionary to represent a book and its data
    #gather data from openlibrary api and return it directly as json 
    def __openLibrary(self, isbn):
        #get data from openlibrary
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
    fetcher = OpenLibraryFetcher()
    book_data = fetcher.fetch_metadata('0132624788')
    print(book_data)