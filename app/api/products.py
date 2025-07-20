from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.product import get_product_by_id, get_products
from app.models.db import get_session
from app.schemas.product import BookOut

router = APIRouter()


@router.get("/", response_model=List[BookOut])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    min_rating: Optional[int] = Query(None, ge=1, le=5),
    category: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
) -> List[BookOut]:
    products = await get_products(
        session=session,
        skip=skip,
        limit=limit,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        category=category,
        q=q,
    )
    return [BookOut.model_validate(product) for product in products]


@router.get("/{product_id}", response_model=BookOut)
async def product_detail(
    product_id: int,
    session: AsyncSession = Depends(get_session),
) -> BookOut:
    product = await get_product_by_id(session, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
