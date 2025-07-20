from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Book, BookAIDetails


async def get_similar_books(
    session: AsyncSession, book_id: int, k: int = 5
) -> list[Book]:
    """
    Returns the top k most similar book IDs (excluding the target itself)
    ranked by cosine distance using pgvector integration.
    """

    # 1. Get the target book's embedding
    result = await session.execute(
        select(BookAIDetails.embedding).where(BookAIDetails.book_id == book_id)
    )
    target_embedding = result.scalar_one_or_none()

    if target_embedding is None:
        return []

    # 2. Query for k most similar books (excluding self)
    query = (
        select(Book)
        .join(BookAIDetails, Book.id == BookAIDetails.book_id)
        .where(BookAIDetails.book_id != book_id)
        .order_by(BookAIDetails.embedding.op('<=>')(target_embedding))
        .limit(k)
    )
    result = await session.execute(query)
    return cast(list["Book"], result.scalars().all())
