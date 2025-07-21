import pytest
import numpy as np
from unittest.mock import patch, AsyncMock

from app.ai import embeddings
from tests.factories import BookFactory
from app.models.product import BookAIDetails


@pytest.mark.asyncio
class TestGenerateAndStoreEmbeddings:
    @pytest.fixture
    def fake_embedding(self):
        return np.ones(384)

    @pytest.fixture
    def dummy_session(self):
        class DummySession:
            def __init__(self):
                self.added = []
                self.committed = False

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

            def add_all(self, values):
                self.added.extend(values)

            async def commit(self):
                self.committed = True

        return DummySession()

    async def test_updates_existing_embedding(self, fake_embedding, dummy_session):
        # Use BookFactory to create a Book with existing ai_details
        book = BookFactory.build()
        ai_details = BookAIDetails(book_id=book.id, embedding=None)
        book.ai_details = ai_details
        books_list = [book]

        with (
            patch(
                "app.ai.embeddings.get_books_with_no_embedding",
                new=AsyncMock(return_value=books_list)
                ),
            patch("app.ai.embeddings.embed_book", return_value=fake_embedding),
            patch("app.ai.embeddings.async_session", return_value=dummy_session),
        ):
            await embeddings.generate_and_store_embeddings()
        assert np.allclose(book.ai_details.embedding, fake_embedding.tolist())

    async def test_creates_new_embedding(self, fake_embedding, dummy_session):
        # Use BookFactory to create a Book without ai_details
        book = BookFactory.build()
        book.ai_details = None
        books_list = [book]

        with (
            patch(
                "app.ai.embeddings.get_books_with_no_embedding",
                new=AsyncMock(return_value=books_list)
                ),
            patch("app.ai.embeddings.embed_book", return_value=fake_embedding),
            patch("app.ai.embeddings.BookAIDetails") as mock_aidetails,
            patch("app.ai.embeddings.async_session", return_value=dummy_session),
        ):
            await embeddings.generate_and_store_embeddings()
            assert dummy_session.added  # BookAIDetails should be added
            args, kwargs = mock_aidetails.call_args
            assert kwargs.get("book_id") == book.id
            assert np.allclose(kwargs.get("embedding"), fake_embedding.tolist())

    async def test_commit_called(self, fake_embedding, dummy_session):
        book = BookFactory.build()
        book.ai_details = None
        with (
            patch(
                "app.ai.embeddings.get_books_with_no_embedding", new=AsyncMock(return_value=[book])
                ),
            patch("app.ai.embeddings.embed_book", return_value=fake_embedding),
            patch("app.ai.embeddings.BookAIDetails"),
            patch("app.ai.embeddings.async_session", return_value=dummy_session),
        ):
            await embeddings.generate_and_store_embeddings()
        assert dummy_session.committed is True

    async def test_existing_embedding_is_unchanged(self, async_session):
        # The book already has an embedding
        original_embedding = [42.0] * 384
        book = BookFactory.build()
        ai_details = BookAIDetails(book_id=book.id, embedding=original_embedding.copy())
        book.ai_details = ai_details
        books_list = [book]

        # embed_book returns a different ("fake") embedding, but it should NOT overwrite the original
        new_embedding = [1.0] * 384

        with (
            patch("app.ai.embeddings.embed_book", return_value=new_embedding),
            patch("app.ai.embeddings.async_session", return_value=async_session)
        ):
            await embeddings.generate_and_store_embeddings()

        # The embedding should remain what it was originally
        assert book.ai_details.embedding == original_embedding