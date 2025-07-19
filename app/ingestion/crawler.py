import asyncio
import logging
import os
from typing import Optional

import aiohttp

from app.ingestion.constants import CATALOGUE_URL, RAW_HTML_DIR

logger = logging.getLogger(__name__)

os.makedirs(RAW_HTML_DIR, exist_ok=True)


async def fetch_url(session: aiohttp.ClientSession, url: str) -> str:
    try:
        async with session.get(url, timeout=10) as response:
            response.raise_for_status()
            html_data: str = await response.text()
            logger.info(f"Successfully fetched {url}")
            return html_data

    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return ""


async def save_html(content: str, filename: str) -> None:
    path = os.path.join(RAW_HTML_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"Saved HTML content to {path}")


async def fetch_and_save_catalogue_page(session: aiohttp.ClientSession, page: int) -> Optional[str]:
    cat_url = f"{CATALOGUE_URL}/page-{page}.html"
    html = await fetch_url(session, cat_url)
    if not html:
        return None

    await save_html(html, f"catalogue_page_{page}.html")

    return html


async def fetch_and_save_books(
        session: aiohttp.ClientSession,
        book_urls: list[str],
        concurrency: int
) -> None:

    semaphore = asyncio.Semaphore(concurrency)

    async def fetch_and_save_book(book_url: str) -> None:
        async with semaphore:
            html = await fetch_url(session, book_url)
            if not html:
                return

            # slug is clean from the url, e.g., /catalogue/a-light-in-the-attic_1000/index.html
            slug = book_url.split('/')[-2]
            filename = f"book_{slug}.html"

            await save_html(html, filename)
            logger.info(f"Saved HTML content for {book_url} to {filename}")

    await asyncio.gather(*(fetch_and_save_book(url) for url in book_urls))


async def crawl_all_books(start_page: int = 1, end_page: int = 50, concurrency: int = 10) -> None:
    async with aiohttp.ClientSession() as session:
        # 1. Get all book detail URLs from all catalogue pages
        book_detail_urls = []
        for page in range(start_page, end_page + 1):
            html = await fetch_and_save_catalogue_page(session, page)

            if not html:
                continue

            from app.ingestion.extractor import extract_book_urls_from_catalogue
            book_urls = await extract_book_urls_from_catalogue(html)

            book_detail_urls.extend(book_urls)

        logger.info(f"Discovered {len(book_detail_urls)} book detail pages.")

        # 2. Fetch and save each book's detail page HTML
        if book_detail_urls:
            await fetch_and_save_books(session, book_detail_urls, concurrency)
        else:
            logger.warning("No book detail URLs found to fetch.")

# To run the full crawl from command line


if __name__ == "__main__":
    asyncio.run(crawl_all_books())
