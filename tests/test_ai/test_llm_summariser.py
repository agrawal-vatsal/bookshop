import pytest
from unittest.mock import patch, MagicMock

from app.models.product import Book, BookAIDetails

@pytest.mark.asyncio
class TestAddSummary:
    async def test_adds_summary_to_books_without_ai_details(self, async_session):
        # Book has no BookAIDetails
        book = Book(name="No Details", description="Alpha Desc")
        async_session.add(book)
        await async_session.commit()
        await async_session.refresh(book)

        fake_response = MagicMock()
        fake_response.choices = [MagicMock()]
        fake_response.choices[0].message.content = "A short synthetic summary!"

        with patch("app.ai.llm_summariser.client.chat.completions.create", return_value=fake_response):
            from app.ai.llm_summariser import fetch_summary_and_update_books
            updated_count = await fetch_summary_and_update_books(async_session)

        found = await async_session.execute(
            async_session.sync_session.query(BookAIDetails).filter(BookAIDetails.book_id == book.id)
        )
        details = found.scalars().first()
        assert details and details.summary == "A short synthetic summary!"
        assert updated_count == 1

    async def test_updates_empty_summary(self, async_session):
        book = Book(name="Has Empty", description="Beta Desc")
        async_session.add(book)
        await async_session.commit()
        await async_session.refresh(book)

        details = BookAIDetails(book_id=book.id, summary="")
        async_session.add(details)
        await async_session.commit()

        fake_response = MagicMock()
        fake_response.choices = [MagicMock()]
        fake_response.choices[0].message.content = "Filled in summary."

        with patch("app.ai.llm_summariser.client.chat.completions.create", return_value=fake_response):
            from app.ai.llm_summariser import fetch_summary_and_update_books
            updated_count = await fetch_summary_and_update_books(async_session)

        query = await async_session.execute(
            async_session.sync_session.query(BookAIDetails).filter(BookAIDetails.book_id == book.id)
        )
        result = query.scalars().first()
        assert result.summary == "Filled in summary."
        assert updated_count == 1

    async def test_skips_existing_summary(self, async_session):
        book = Book(name="Existing", description="Gamma Desc")
        async_session.add(book)
        await async_session.commit()
        await async_session.refresh(book)

        details = BookAIDetails(book_id=book.id, summary="Already present.")
        async_session.add(details)
        await async_session.commit()

        with patch("app.ai.llm_summariser.client.chat.completions.create") as mocked_llm:
            from app.ai.llm_summariser import fetch_summary_and_update_books
            updated_count = await fetch_summary_and_update_books(async_session)
            mocked_llm.assert_not_called()

        updated = await async_session.get(BookAIDetails, book.id)
        assert updated.summary == "Already present."
        assert updated_count == 0