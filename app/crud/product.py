from typing import Any, Optional, Sequence, cast

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Book
from app.schemas.product import BookDetailOut, BookListOut


async def get_books(
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
    return cast(Sequence[BookListOut], result.scalars().all())


def book_to_dict(book: Book) -> dict[str, Any]:
    """Convert a Book model to dictionary including summary from ai_details"""
    book_dict = {
        "id": book.id,
        "name": book.name,
        "price": book.price,
        "rating": book.rating,
        "description": book.description,
        "category": book.category,
        "upc": book.upc,
        "availability": book.availability,
        "stock_count": book.stock_count,
        "summary": book.ai_details.summary if book.ai_details else None
    }
    return book_dict


async def get_book_by_id(session: AsyncSession, book_id: int) -> Optional[BookDetailOut]:
    query = select(Book).options(
        selectinload(Book.ai_details)  # Eager load AI details if needed
    ).where(Book.id == book_id)
    result = await session.execute(query)
    result_data = result.scalar_one_or_none()

    if result_data is None:
        return None

    # Convert to BookDetailOut schema
    book_dict = book_to_dict(result_data)
    return cast(BookListOut, BookDetailOut.model_validate(book_dict))
