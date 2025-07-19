from sqlalchemy import Column, Float, Integer, String

from app.models.db import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    price = Column(Float)
    rating = Column(Integer)
    description = Column(String)
    category = Column(String)
    upc = Column(String, unique=True)
    availability = Column(String)
    stock_count = Column(Integer)
