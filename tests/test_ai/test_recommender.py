import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Book, BookAIDetails
from app.ai.recommender import get_similar_books_to_given_book

from tests.factories import BookFactory

import numpy as np

def random_embedding(dim=384):
    # pgvector converts python list to vector
    # match the dimension with your vector extension
    return list(np.random.rand(dim))

@pytest.mark.asyncio
class TestGetSimilarBooksToGivenBook:
    async def test_returns_similar_books_excluding_self(self, async_session: AsyncSession):
        # Create books with embeddings
        books = []
        details = []
        for _ in range(4):
            book = BookFactory.build()
            async_session.add(book)
            books.append(book)
        await async_session.flush()

        # Give each book an embedding:
        for idx, book in enumerate(books):
            embedding = [float(idx)] * 384
            det = BookAIDetails(book_id=book.id, embedding=embedding)
            async_session.add(det)
            details.append(det)
        await async_session.commit()

        # Now query for book[0]'s neighbours
        results = await get_similar_books_to_given_book(async_session, book_id=books[0].id, k=3)
        # Should not include the book itself
        assert all(b.id != books[0].id for b in results)
        # Should return at most k results
        assert len(results) <= 3
        # Should return others in order of vector distance (1,2,3)
        returned_ids = [b.id for b in results]
        expected_ids = [b.id for b in books[1:4]]
        assert set(returned_ids) == set(expected_ids)

    async def test_returns_empty_when_no_embedding(self, async_session: AsyncSession):
        # Create a book with no embedding
        book = BookFactory.build()
        async_session.add(book)
        await async_session.commit()

        # Should return []
        results = await get_similar_books_to_given_book(async_session, book_id=book.id)
        assert results == []

    async def test_returns_fewer_if_not_enough_books(self, async_session: AsyncSession):
        # Only one book with embedding
        # query = delete(Book)
        # await async_session.execute(query)
        book1 = BookFactory.build()
        async_session.add(book1)
        await async_session.flush()
        det1 = BookAIDetails(book_id=book1.id, embedding=[0.0]*384)
        async_session.add(det1)

        book2 = BookFactory.build()
        async_session.add(book2)
        await async_session.flush()
        det2 = BookAIDetails(book_id=book2.id, embedding=[1.0]*384)
        async_session.add(det2)

        await async_session.commit()

        # Only one other present (k much higher)
        results = await get_similar_books_to_given_book(async_session, book_id=book1.id, k=5)
        assert len(results) == 1
        assert results[0].id == book2.id
