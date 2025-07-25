import logging
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.db import async_session
from app.models.product import Book, BookAIDetails

logger = logging.getLogger(__name__)

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))


async def get_books_with_no_summary(session: AsyncSession) -> Any:
    query = select(Book).outerjoin(BookAIDetails).options(
        selectinload(Book.ai_details)
    ).where(
        or_(
            BookAIDetails.book_id.is_(None),  # No BookAIDetails exists
            BookAIDetails.summary.is_(None),  # BookAIDetails exists but summary is null
            BookAIDetails.summary == ""  # BookAIDetails exists but summary is empty
        )
    )

    return (await session.execute(query)).scalars().unique().all()


async def fetch_summary_and_update_books(session: AsyncSession) -> int:
    books = await get_books_with_no_summary(session)
    new_ai_details = []

    for i, book in enumerate(books):
        # Generate summary using OpenAI
        prompt = (f"Write a catchy marketing summary (≤ 40 words) for this book:\nTitle: "
                  f"{book.name}\nDescription: {book.description or ''}")
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "You are a creative book marketer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=80,
            temperature=0.8
            )
        summary = response.choices[0].message.content.strip()

        logger.info(f"Generated summary for book '{book.name}': {summary}")

        if hasattr(book, 'ai_details') and book.ai_details:
            # Update existing BookAIDetails with the summary
            book.ai_details.summary = summary
        else:
            # Create new BookAIDetails with the summary
            new_ai_details.append(BookAIDetails(book_id=book.id, summary=summary))

        if i % 10 == 0:
            print(f"Processed {i + 1}/{len(books)} books...")

    # Bulk add new BookAIDetails records
    if new_ai_details:
        session.add_all(new_ai_details)

    # Commit all changes (both updates and inserts)
    await session.commit()

    return len(books)


async def add_summary() -> int:
    """
    Fetches all books that either don't have BookAIDetails or have no summary,
    generates summaries for them using OpenAI, and stores them in BookAIDetails.
    """
    async with async_session() as session:
        updated_count = await fetch_summary_and_update_books(session)
        return updated_count


if __name__ == "__main__":
    import asyncio

    async def run() -> None:
        print("Generating summaries for books...")
        await add_summary()
        print("Summaries generated and stored successfully.")

    asyncio.run(run())
