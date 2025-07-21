import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import analytics
from tests.factories import BookFactory

pytestmark = pytest.mark.asyncio

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

class TestAnalytics:

    async def test_average_price_by_rating_decile(self, async_session: AsyncSession, books_in_db):
        result = await analytics.average_price_by_rating_decile(async_session)
        assert isinstance(result, list)
        assert len(result) == 10
        for item in result:
            assert "price_range" in item
            assert isinstance(item["price_range"], list)
            assert len(item["price_range"]) == 2
            assert "average_rating" in item

    async def test_most_common_categories(self, async_session: AsyncSession, books_in_db):
        result = await analytics.most_common_categories(async_session, k=3)
        cats = [r["category"] for r in result]
        assert "Fiction" in cats
        assert "Science" in cats
        assert isinstance(result[0]["count"], int)

    async def test_average_price_by_category(self, async_session: AsyncSession, books_in_db):
        result = await analytics.average_price_by_category(async_session)
        assert isinstance(result, list)
        for row in result:
            assert "category" in row and "average_price" in row

    async def test_avg_rating_for_popular_categories(self, async_session: AsyncSession, books_in_db):
        result = await analytics.avg_rating_for_popular_categories(async_session, min_count=3)
        assert isinstance(result, list)
        assert all(r["book_count"] >= 3 for r in result)
        for r in result:
            assert "category" in r and "book_count" in r and "average_rating" in r

    async def test_get_highest_rated_books_per_category(self, async_session: AsyncSession, books_in_db):
        result = await analytics.get_highest_rated_books_per_category(async_session)
        assert isinstance(result, list)
        # There should be one per category
        cat_names = set(b.category for b in books_in_db)
        res_cats = set(r["category"] for r in result)
        assert cat_names == res_cats
        for entry in result:
            assert "name" in entry and entry["rating"] is not None
