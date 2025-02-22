"""
A BookMetadataFetcher that webscrapes https://outland.no/
"""

from bs4 import BeautifulSoup

import requests

from worblehat.services.metadata_fetchers.BookMetadataFetcher import BookMetadataFetcher
from worblehat.services.metadata_fetchers.BookMetadata import BookMetadata


LANGUAGE_MAP = {
    "Norsk": "no",
    "Engelsk": "en",
    "Tysk": "de",
    "Fransk": "fr",
    "Spansk": "es",
    "Italiensk": "it",
    "Svensk": "sv",
    "Dansk": "da",
    "Finsk": "fi",
    "Russisk": "ru",
    "Kinesisk": "zh",
    "Japansk": "ja",
    "Koreansk": "ko",
}


class OutlandScraperFetcher(BookMetadataFetcher):
    @classmethod
    def metadata_source_id(_cls) -> str:
      return "outland_scraper"

    @classmethod
    def fetch_metadata(cls, isbn: str) -> BookMetadata | None:
        try:
            # Find the link to the product page
            response = requests.get(f"https://outland.no/{isbn}")
            soup = BeautifulSoup(response.content, "html.parser")
            soup = soup.find_all("a", class_="product-item-link")
            href = soup[0].get("href")

            # Find the metadata on the product page
            response = requests.get(href)
            soup = BeautifulSoup(response.content, "html.parser")
            data = soup.find_all("td", class_="col data")

            # Collect the metadata
            title = soup.find_all("span", class_="base")[0].text

            releaseDate = soup.find_all("span", class_="release-date")[0].text.strip()
            releaseDate = releaseDate[-4:] # only keep year

            bookData = {
                "Title": title,
                "PublishDate": releaseDate,
                "Authors": None,
                "NumberOfPages": None,
                "Genre": None,
                "Language": None,
                "Subjects": None,
            }

            dataKeyMap = {
                "Authors": "Forfattere",
                "NumberOfPages": "Antall Sider",
                "Genre": "Sjanger",
                "Language": "Språk",
                "Subjects": "Serie"
            }

            for value in data:
                for key in dataKeyMap:
                    if str(value).lower().__contains__(dataKeyMap[key].lower()):
                        bookData[key] = value.text
                        break

            if bookData["Language"] is not None:
                bookData["Language"] = LANGUAGE_MAP.get(bookData["Language"])

            if bookData["Authors"] is not None:
                bookData["Authors"] = set(bookData["Authors"].split(", "))

            if bookData["Subjects"] is not None:
                bookData["Subjects"] = set(bookData["Subjects"].split(", "))

            if bookData["NumberOfPages"] is not None:
                bookData["NumberOfPages"] = int(bookData["NumberOfPages"])

        except Exception:
            return None

        return BookMetadata(
            isbn = isbn,
            title = bookData.get('Title'),
            source = cls.metadata_source_id(),
            authors = bookData.get('Authors'),
            language = bookData.get('Language'),
            publish_date = bookData.get('PublishDate'),
            num_pages = bookData.get('NumberOfPages'),
            subjects = bookData.get('Subjects'),
        )


if __name__ == '__main__':
    book_data = OutlandScraperFetcher.fetch_metadata('9781947808225')
    book_data.validate()
    print(book_data)