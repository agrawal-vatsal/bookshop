from typing import Any

import numpy as np
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Book


async def average_price_by_rating_decile(
        session: AsyncSession
) -> list[dict[str, list[float] | float | None]]:
    # Compute deciles by price and average rating for each decile
    # Step 1: Fetch all prices and ratings
    result = await session.execute(
        select(Book.price, Book.rating).where(Book.price is not None, Book.rating is not None)
    )
    rows = result.all()
    if not rows:
        return []

    prices = np.array([row.price for row in rows], dtype=float)
    ratings = np.array([row.rating for row in rows], dtype=int)

    # Compute deciles (0–10%, 10–20%, ...)
    if len(prices) < 10:
        return []

    decile_edges = np.percentile(prices, [10 * i for i in range(11)])  # 0, 10, 20, ... 100
    decile_stats = []
    for i in range(10):
        mask = (prices >= decile_edges[i]) & (prices < decile_edges[i + 1]) \
            if i < 9 \
            else (prices >= decile_edges[i]) & (prices <= decile_edges[i + 1])
        avg_rating = float(np.mean(ratings[mask])) if np.any(mask) else None
        decile_stats.append({
            "price_range": [float(decile_edges[i]), float(decile_edges[i + 1])],
            "average_rating": avg_rating,
        })
    return decile_stats


async def most_common_categories(session: AsyncSession, k: int = 5) -> list[dict[str, Any]]:
    result = await session.execute(
        select(Book.category, func.count())
        .group_by(Book.category)
        .order_by(desc(func.count()))
        .limit(k)
    )
    return [{"category": row[0], "count": row[1]} for row in result.all()]


async def average_price_by_category(session: AsyncSession) -> list[dict[str, Any]]:
    result = await session.execute(
        select(
            Book.category,
            func.avg(Book.price).label("average_price")
        ).where(Book.price is not None)
        .group_by(Book.category)
    )
    return [{"category": row[0], "average_price": float(row[1])} for row in result.all()]


async def avg_rating_for_popular_categories(session: AsyncSession,
                                            min_count: int = 3) -> list[dict[str, Any]]:
    """
    Returns a list of categories with more than 'min_count' books, along with their average rating.
    """
    result = await session.execute(
        select(
            Book.category,
            func.count().label('book_count'),
            func.avg(Book.rating).label('avg_rating')
        )
        .group_by(Book.category)
        .having(func.count() >= min_count)
        .order_by(func.avg(Book.rating).desc())
    )
    return [
        {
            "category": row.category,
            "book_count": row.book_count,
            "average_rating": float(row.avg_rating) if row.avg_rating is not None else None
        }
        for row in result.all()
    ]


async def get_highest_rated_books_per_category(session: AsyncSession) -> list[dict[str, Any]]:
    """
    Returns the highest rated book for each category.
    """
    subquery = (
        select(
            Book.category,
            func.max(Book.rating).label('max_rating')
        )
        .group_by(Book.category)
        .subquery()
    )

    result = await session.execute(
        select(Book)
        .join(subquery, and_(
            Book.category == subquery.c.category,
            Book.rating == subquery.c.max_rating
        ))
    )

    books = result.scalars().all()

    return [
        {
            "id": book.id,
            "name": book.name,
            "category": book.category,
            "rating": book.rating
        }
        for book in books
    ]
