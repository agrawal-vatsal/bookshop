import asyncio
import logging
from typing import Any, Dict, List, Optional

from app.ingestion.extractor import BooksDataExtractor
from app.models.db import async_session
from app.models.product import Book

logger = logging.getLogger(__name__)


async def insert_books(books: List[Dict[str, Optional[Any]]]) -> None:
    async with async_session() as session:
        for book in books:
            # Check if the book already exists by unique UPC or name
            exists = await session.execute(
                Book.__table__.select().where(Book.upc == book.get("upc"))
            )
            if exists.first():
                continue  # Skip if duplicate

            book_obj = Book(
                name=book["name"],
                price=book["price"],
                rating=book["rating"],
                description=book["description"],
                category=book["category"],
                upc=book["upc"],
                availability=book["availability"],
                stock_count=book["stock_count"],
            )
            session.add(book_obj)
        await session.commit()


async def main() -> None:
    books = BooksDataExtractor.extract_books_from_dir(directory="app/data/raw_html")
    logger.info(f"Discovered {len(books)} book detail pages.")
    print(f"Discovered {len(books)} book detail pages.")
    await insert_books(books)
    logger.info("Books inserted successfully.")
    print("Books inserted successfully.")


if __name__ == "__main__":
    asyncio.run(main())
