from typing import Optional

from pydantic import BaseModel, ConfigDict


class BookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: float
    rating: int
    description: Optional[str] = None
    category: Optional[str] = None
    upc: Optional[str] = None
    availability: Optional[str] = None
    stock_count: Optional[int] = None
