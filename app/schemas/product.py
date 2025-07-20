from typing import Optional

from pydantic import BaseModel


class BookListOut(BaseModel):

    id: int
    name: str
    price: float
    rating: int
    category: Optional[str] = None
    upc: Optional[str] = None
    availability: Optional[str] = None
    stock_count: Optional[int] = None

    class Config:
        from_attributes = True


class BookDetailOut(BaseModel):

    id: int
    name: str
    price: float
    rating: int
    description: Optional[str] = None
    category: Optional[str] = None
    upc: Optional[str] = None
    availability: Optional[str] = None
    stock_count: Optional[int] = None
    summary: Optional[str] = None

    class Config:
        from_attributes = True
