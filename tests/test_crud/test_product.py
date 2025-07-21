import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.crud.product import get_books, get_book_by_id, book_to_dict
from app.models.product import Book, BookAIDetails
from app.schemas.product import BookDetailOut
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import BookFactory, BookAIDetailsFactory


@pytest_asyncio.fixture
async def books_in_db(async_session: AsyncSession):
    # Insert 20 books spanning all deciles, categories, and ratings
    objs = []
    # 10 in Fiction, rating 1-5; Price: 10 to 100
    for i in range(10):
        objs.append(
            BookFactory.build(
                price=10 + i * 10,
                rating=((i % 5) + 1),
                category="Fiction"
            )
        )
    # 5 in Science, high rating, price 50-70
    for i in range(5):
        objs.append(
            BookFactory.build(
                price=50 + i * 5,
                rating=5,
                category="Science"
            )
        )
    # 5 in History, mixed rating, price 60-80
    for i in range(5):
        objs.append(
            BookFactory.build(
                price=60 + i * 5,
                rating=2 + (i % 3),
                category="History"
            )
        )
    async_session.add_all(objs)
    await async_session.commit()
    yield objs

@pytest.mark.asyncio
class TestProductCrud:
    async def test_get_books_simple(self, async_session: AsyncSession, books_in_db):
        books = await get_books(async_session)
        assert isinstance(books, list)
        assert all(isinstance(b, Book) for b in books)
        assert len(books) <= 20

    async def test_get_books_with_filters(self, async_session: AsyncSession, books_in_db):
        cat = books_in_db[0].category
        filtered = await get_books(async_session, category=cat[:2])
        # All filtered books' category should contain the substring (case insensitive)
        assert all(cat[:2].lower() in b.category.lower() for b in filtered)
        filtered_by_price = await get_books(async_session, min_price=10, max_price=100)
        for b in filtered_by_price:
            assert 10 <= b.price <= 100
        filtered_by_rating = await get_books(async_session, min_rating=3)
        for b in filtered_by_rating:
            assert b.rating >= 3

    async def test_get_books_with_search_query(self, async_session: AsyncSession, books_in_db):
        book = books_in_db[0]
        books_by_name = await get_books(async_session, q=book.name[:3])
        assert (
            any(book.name.lower() in b.name.lower() for b in books_by_name)
            or any(book.name.lower() in b.description.lower() for b in books_by_name)
        )

    async def test_get_books_pagination(self, async_session: AsyncSession, books_in_db):
        total = len(books_in_db)
        part1 = await get_books(async_session, skip=0, limit=1)
        part2 = await get_books(async_session, skip=1, limit=1)
        assert part1 != part2 or total < 2

    async def test_book_to_dict_returns_correct_keys(self, async_session: AsyncSession):
        book = BookFactory.build(
            name="Test Book",
            price=10.5,
            rating=4,
            description="Something",
            category="Tests",
            upc="UPC1",
            availability="In stock",
            stock_count=5,
        )
        ai_details = BookAIDetailsFactory.build(book=book)
        async_session.add_all([book, ai_details])
        await async_session.commit()

        query = select(Book).options(
            selectinload(Book.ai_details)  # Eager load AI details if needed
        ).where(Book.id == book.id)

        result = await async_session.execute(query)
        book = result.scalar_one_or_none()
        d = book_to_dict(book)
        for key in [
            "id", "name", "price", "rating",
            "description", "category", "upc",
            "availability", "stock_count", "summary"
        ]:
            assert key in d
        assert d["summary"] is not None

    async def test_get_book_by_id_found(self, async_session: AsyncSession, books_in_db):
        book = books_in_db[0]
        detail = await get_book_by_id(async_session, book.id)
        assert isinstance(detail, BookDetailOut)
        assert detail.id == book.id

    async def test_get_book_by_id_not_found(self, async_session: AsyncSession):
        detail = await get_book_by_id(async_session, -99999)
        assert detail is None