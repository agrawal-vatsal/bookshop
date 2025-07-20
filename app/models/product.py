from typing import cast

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Float, ForeignKey, Integer, String, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, selectinload

from app.models.db import Base


class BookAIDetails(Base):
    __tablename__ = "book_ai_details"

    id = Column(Integer, primary_key=True)
    book_id = Column(
        Integer, ForeignKey("books.id"), nullable=False, unique=True
    )
    summary = Column(String)
    embedding = Column(Vector(384))

    book = relationship("Book", back_populates="ai_details", uselist=False)


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

    ai_details = relationship("BookAIDetails", back_populates="book", uselist=False)

    @classmethod
    async def get_books_with_no_embedding(cls, session: AsyncSession) -> list["Book"]:
        query = select(Book).outerjoin(BookAIDetails).options(
            selectinload(Book.ai_details)
        ).where(
            or_(
                BookAIDetails.book_id.is_(None),  # No BookAIDetails exists
                BookAIDetails.embedding.is_(None)  # BookAIDetails exists but embedding is null
            )
        )
        return cast(list["Book"], (await session.execute(query)).scalars().unique().all())
