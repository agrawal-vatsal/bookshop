import logging
from typing import List

from bs4 import BeautifulSoup

from app.ingestion.constants import CATALOGUE_URL

logger = logging.getLogger(__name__)


async def extract_book_urls_from_catalogue(html: str) -> List[str]:
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
