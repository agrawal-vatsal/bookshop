from typing import Optional, Sequence, cast

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Book


async def get_products(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[int] = None,
    category: Optional[str] = None,
    q: Optional[str] = None,
) -> Sequence[Book]:
    query = select(Book)
    filters = []

    if min_price is not None:
        filters.append(Book.price >= min_price)
    if max_price is not None:
        filters.append(Book.price <= max_price)
    if min_rating is not None:
        filters.append(Book.rating >= min_rating)
    if category is not None:
        # Using ilike for case-insensitive, partial match
        filters.append(Book.category.ilike(f"%{category}%"))
    if q:
        filters.append(
            or_(
                Book.name.ilike(f"%{q}%"),
                Book.description.ilike(f"%{q}%"),
            )
        )

    if filters:
        query = query.where(and_(*filters))
    query = query.offset(skip).limit(limit)

    result = await session.execute(query)
    return cast(Sequence[Book], result.scalars().all())


async def get_product_by_id(session: AsyncSession, product_id: int) -> Optional[Book]:
    result = await session.execute(
        select(Book).where(Book.id == product_id)
    )
    return cast(Optional[Book], result.scalar_one_or_none())
