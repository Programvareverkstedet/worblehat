from typing import Dict, Optional

# import isbnlib
#used these instead of isbnlib as i have already written the code for them
import json
import requests

from worblehat.services.metadata_fetchers.base_fetcher import BookMetadataFetcher
from worblehat.models.BookMetadata import BookMetadata

class OutlandScraperFetcher(BookMetadataFetcher):

    def fetch_metadata(self, isbn: str) -> BookMetadata:
        metadata = self.__outland(isbn)
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
    def __outland(self, isbn):
        #get data from openlibrary
        try:
            
            from bs4 import BeautifulSoup
            url = "https://outland.no/"+isbn
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")
            #get all hrefs from elements with class "product-item-link"
            soup = soup.find_all("a", class_="product-item-link")
            #get the first href
            href = soup[0].get("href")
            
            #get data from the first href
            response = requests.get(href)
            soup = BeautifulSoup(response.content, "html.parser")
            #get all elements with class "language"
            data = soup.find_all("td", class_="col data")
            base = soup.find_all("span", class_="base")[0].text
            releaseDate = soup.find_all("span", class_="release-date")[0].text.strip()
            #only keep the year of the release date
            releaseDate = releaseDate[-4:]
            
            #get the element withch contains anything in the intestingData list anywhere in it. 
            intrestingData = {
                        "Authors": "Forfattere",
                        "NumberOfPages": "Antall Sider",
                        "Genre": "Sjanger",
                        "Language": "Språk",
                        "Subjects": "Serie"
                        } 
            bookData = {
                        "Title": base,
                        "PublishDate": releaseDate,
                        "Authors": None,
                        "NumberOfPages": None,
                        "Genre": None,
                        "Language": None,
                        "Subjects": None
                        } 
            
            for value in data:
                for key in intrestingData:
                    if str(value).lower().__contains__(intrestingData[key].lower()):
                        #get the next element in the list and add it to the bookData dict
                        bookData[key] = value.text
                        break
            
            return bookData
        except Exception as e:
            print(str(e))
            return False
        
if __name__ == '__main__':
    fetcher = OutlandScraperFetcher()
    book_data = fetcher.fetch_metadata('9781947808225')
    print(book_data)