from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.product import get_book_by_id, get_books
from app.models.db import get_session
from app.schemas.product import BookDetailOut, BookListOut

router = APIRouter()


@router.get("/", response_model=dict[str, Any])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    min_rating: Optional[int] = Query(None, ge=1, le=5),
    category: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    books = await get_books(
        session=session,
        skip=skip,
        limit=limit,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        category=category,
        q=q,
    )
    return {"books": [BookListOut.model_validate(book) for book in books], "total": len(books)}


@router.get("/{book_id}", response_model=BookDetailOut)
async def book_detail(
    book_id: int,
    session: AsyncSession = Depends(get_session),
) -> BookDetailOut:
    book = await get_book_by_id(session, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book
