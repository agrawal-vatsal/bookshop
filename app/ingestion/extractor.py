import logging
import os
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from app.ingestion.constants import CATALOGUE_URL, RAW_HTML_DIR

logger = logging.getLogger(__name__)


class SingleBookDataExtractor:
    """
    Extracts data from a single book HTML file.
    Parses book details like name, price, rating, description, category, UPC, and availability.
    """

    def __init__(self, html: str):
        self.html = html
        self.soup = BeautifulSoup(html, "html.parser")

    def parse_rating(self) -> Optional[int]:
        # The rating is stored in a class like <p class="star-rating Three">
        ratings_map = {
            "one": 1,
            "two": 2,
            "three": 3,
            "four": 4,
            "five": 5,
        }
        p = self.soup.find("p", class_="star-rating")
        if p:
            for klass in p.get("class", []):
                if klass.lower() in ratings_map:
                    return ratings_map[klass.lower()]
        return None

    def get_name(self) -> Optional[str]:
        # Title / name
        title_tag = self.soup.find("div", class_="product_main").find("h1")
        return title_tag.text.strip() if title_tag else None

    def get_price(self) -> Optional[float]:
        # Price (strip £ and convert to float)
        price_tag = self.soup.find("p", class_="price_color")
        return float(price_tag.text.replace("£", "").strip()) if price_tag else None

    def get_description(self) -> Optional[str]:
        # Description: as given under product_description → following <p>
        desc_header = self.soup.find("div", id="product_description")
        if desc_header:
            desc_p = desc_header.find_next_sibling("p")
            return desc_p.text.strip() if desc_p else None
        return None

    def get_category(self) -> Optional[str]:
        # Category: second breadcrumb (Home > Category > Book)
        breadcrumb = self.soup.find("ul", class_="breadcrumb")
        if breadcrumb:
            links = breadcrumb.find_all("a")
            if len(links) > 2:
                return str(links[2].text.strip())
            elif len(links) == 2:
                return str(links[1].text.strip())
        return None

    def get_extra_attributes(self) -> Dict[str, Optional[Any]]:
        # Additional attributes (UPC, availability, stock count)
        table = self.soup.find("table", class_="table table-striped")
        attrs = {}
        if table:
            for row in table.find_all("tr"):
                th = row.find("th").text.strip()
                td = row.find("td").text.strip()
                attrs[th] = td

        upc = attrs.get("UPC")
        stock = attrs.get("Availability")  # e.g., "In stock (22 available)"
        # Extra: parse stock count if you want
        stock_count = None
        if stock:
            import re
            m = re.search(r"\((\d+) available\)", stock)
            if m:
                stock_count = int(m.group(1))

        return {
            "upc": upc,
            "availability": stock,
            "stock_count": stock_count
        }

    def extract_book_data(self) -> Optional[Dict[str, Optional[Any]]]:

        # Title / name
        name = self.get_name()

        # Price (strip £ and convert to float)
        price = self.get_price()

        # Rating as integer (1–5)
        rating = self.parse_rating()

        # Description: as given under product_description → following <p>
        desc = self.get_description()

        # Category: second breadcrumb (Home > Category > Book)
        cat = self.get_category()

        # Additional attributes (UPC, availability, stock count)
        extra_attrs = self.get_extra_attributes()

        logger.info(f"Extracted book data for {name}: {price=}, {rating=}, {cat=}, {extra_attrs=}")

        return {
            "name": name,
            "price": price,
            "rating": rating,
            "description": desc,
            "category": cat,
            **extra_attrs
        }


class BooksDataExtractor:
    """
    Extracts book data from HTML files saved in the RAW_HTML_DIR.
    Parses book detail URLs from catalogue pages and extracts book details.
    """

    @classmethod
    async def extract_book_urls_from_catalogue(cls, html: str) -> List[str]:
        """
        Parses book detail URLs from a catalogue page HTML.
        """
        soup = BeautifulSoup(html, "html.parser")
        books = soup.select("article.product_pod h3 a")
        book_urls = []
        for book in books:
            relative_url = book.get('href')
            if relative_url:
                # Normalize for things like '../../../'
                relative_url = relative_url.replace('../', '')
                full_url = f"{CATALOGUE_URL}/{relative_url}"
                logger.info(f"Found book detail URL: {full_url} for relative URL: {relative_url}")
                book_urls.append(full_url)
        return book_urls

    @classmethod
    def extract_books_from_dir(
            cls,
            directory: str = RAW_HTML_DIR
    ) -> List[Dict[str, Optional[Any]]]:
        """
        Parses all saved book HTMLs in the directory.
        """
        books = []
        # Only process files that are individual book HTMLs
        for filename in os.listdir(directory):
            if filename.startswith("book_") and filename.endswith(".html"):
                filepath = os.path.join(directory, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    html = f.read()
                data = SingleBookDataExtractor(html).extract_book_data()
                if data:
                    books.append(data)

        logger.info(f"Extracted {len(books)} books from directory {directory}")
        return books
