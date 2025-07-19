import os
from unittest.mock import AsyncMock, mock_open, patch

import aiohttp
import pytest

from app.ingestion.constants import RAW_HTML_DIR
from app.ingestion.crawler import BooksToScrapeCrawler


class TestBooksToScrapeCrawler:
    """Test suite for BooksToScrapeCrawler class"""

    def test_init(self):
        """Test initialization of BooksToScrapeCrawler"""
        # Test default values
        crawler = BooksToScrapeCrawler()
        assert crawler.start_page == 1
        assert crawler.end_page == 50
        assert crawler.concurrency == 10

        # Test custom values
        crawler = BooksToScrapeCrawler(start_page=5, end_page=20, concurrency=5)
        assert crawler.start_page == 5
        assert crawler.end_page == 20
        assert crawler.concurrency == 5

    @pytest.mark.asyncio
    async def test_fetch_url_exception(self):
        """Test URL fetching with exception"""
        # Mock session that raises an exception
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.side_effect = aiohttp.ClientError("Test error")

        # Call the method
        html = await BooksToScrapeCrawler.fetch_url(mock_session, "http://test.com")

        # Assertions
        assert html == ""
        mock_session.get.assert_called_once_with("http://test.com", timeout=10)

    @pytest.mark.asyncio
    async def test_save_html(self):
        """Test saving HTML content to file"""
        # Mock data
        content = "<html>Test content</html>"
        filename = "test.html"
        expected_path = os.path.join(RAW_HTML_DIR, filename)

        # Use patch to mock open
        with patch("builtins.open", mock_open()) as mock_file:
            await BooksToScrapeCrawler.save_html(content, filename)

            # Assertions
            mock_file.assert_called_once_with(expected_path, "w", encoding="utf-8")
            mock_file().write.assert_called_once_with(content)

    @pytest.mark.asyncio
    async def test_fetch_and_save_catalogue_page_success(self):
        """Test fetching and saving catalogue page successfully"""
        # Mock session and fetch_url/save_html methods
        mock_session = AsyncMock()
        html_content = "<html>Catalogue content</html>"

        with patch.object(BooksToScrapeCrawler, 'fetch_url', return_value=html_content) as mock_fetch, \
             patch.object(BooksToScrapeCrawler, 'save_html') as mock_save:

            # Call the method
            result = await BooksToScrapeCrawler.fetch_and_save_catalogue_page(mock_session, 2)

            # Assertions
            assert result == html_content
            mock_fetch.assert_called_once()
            mock_save.assert_called_once_with(html_content, "catalogue_page_2.html")

    @pytest.mark.asyncio
    async def test_fetch_and_save_catalogue_page_failure(self):
        """Test fetching catalogue page with failure"""
        # Mock session and fetch_url method that returns empty string
        mock_session = AsyncMock()

        with patch.object(BooksToScrapeCrawler, 'fetch_url', return_value="") as mock_fetch, \
             patch.object(BooksToScrapeCrawler, 'save_html') as mock_save:

            # Call the method
            result = await BooksToScrapeCrawler.fetch_and_save_catalogue_page(mock_session, 2)

            # Assertions
            assert result is None
            mock_fetch.assert_called_once()
            mock_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_and_save_books(self):
        """Test fetching and saving multiple books"""
        # Mock data
        mock_session = AsyncMock()
        book_urls = [
            "http://books.com/catalogue/book-1_123/index.html",
            "http://books.com/catalogue/book-2_456/index.html"
        ]
        html_content = "<html>Book content</html>"

        # Set up mocks
        with patch.object(BooksToScrapeCrawler, 'fetch_url', return_value=html_content) as mock_fetch, \
             patch.object(BooksToScrapeCrawler, 'save_html') as mock_save:

            # Call the method
            await BooksToScrapeCrawler.fetch_and_save_books(mock_session, book_urls, 5)

            # Assertions
            assert mock_fetch.call_count == 2
            assert mock_save.call_count == 2
            # Check that the right filenames were generated
            mock_save.assert_any_call(html_content, "book_book-1_123.html")
            mock_save.assert_any_call(html_content, "book_book-2_456.html")

    @pytest.mark.asyncio
    async def test_fetch_and_save_books_empty_html(self):
        """Test fetching and saving books when fetch returns empty string"""
        # Mock data
        mock_session = AsyncMock()
        book_urls = ["http://books.com/catalogue/book-1_123/index.html"]

        # Set up mocks
        with patch.object(BooksToScrapeCrawler, 'fetch_url', return_value="") as mock_fetch, \
             patch.object(BooksToScrapeCrawler, 'save_html') as mock_save:

            # Call the method
            await BooksToScrapeCrawler.fetch_and_save_books(mock_session, book_urls, 5)

            # Assertions
            mock_fetch.assert_called_once()
            mock_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_crawl_all_books_success(self):
        """Test successful crawling of all books"""
        # Mock data
        html_content = "<html>Catalogue content</html>"
        book_urls = [
            "http://books.com/catalogue/book-1_123/index.html",
            "http://books.com/catalogue/book-2_456/index.html"
        ]

        # Create crawler with minimal range to test
        crawler = BooksToScrapeCrawler(start_page=1, end_page=2)

        # Mock the required methods and classes
        with patch('aiohttp.ClientSession') as mock_session_class, \
             patch.object(BooksToScrapeCrawler, 'fetch_and_save_catalogue_page', return_value=html_content) as mock_fetch_cat, \
             patch.object(BooksToScrapeCrawler, 'fetch_and_save_books') as mock_fetch_books, \
             patch('app.ingestion.extractor.BooksDataExtractor.extract_book_urls_from_catalogue',
                   new_callable=AsyncMock, return_value=book_urls) as mock_extract:

            # Set up session context manager
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session

            # Call the method
            await crawler.crawl_all_books()

            # Assertions
            assert mock_fetch_cat.call_count == 2  # Two pages
            assert mock_extract.call_count == 2    # Called for each page
            mock_fetch_books.assert_called_once_with(mock_session, book_urls * 2, 10)  # Combined book URLs

    @pytest.mark.asyncio
    async def test_crawl_all_books_no_urls(self):
        """Test crawling when no book URLs are found"""
        # Mock data
        html_content = "<html>Catalogue content</html>"
        empty_book_urls = []

        # Create crawler with minimal range
        crawler = BooksToScrapeCrawler(start_page=1, end_page=1)

        # Mock the required methods and classes
        with patch('aiohttp.ClientSession') as mock_session_class, \
             patch.object(BooksToScrapeCrawler, 'fetch_and_save_catalogue_page', return_value=html_content) as mock_fetch_cat, \
             patch.object(BooksToScrapeCrawler, 'fetch_and_save_books') as mock_fetch_books, \
             patch('app.ingestion.extractor.BooksDataExtractor.extract_book_urls_from_catalogue',
                   new_callable=AsyncMock, return_value=empty_book_urls) as mock_extract:

            # Set up session context manager
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session

            # Call the method
            await crawler.crawl_all_books()

            # Assertions
            mock_fetch_cat.assert_called_once()
            mock_extract.assert_called_once()
            mock_fetch_books.assert_not_called()  # Should not be called when no URLs

    @pytest.mark.asyncio
    async def test_crawl_all_books_failed_fetch(self):
        """Test crawling when fetching a catalogue page fails"""
        # Mock data
        crawler = BooksToScrapeCrawler(start_page=1, end_page=2)

        # Mock the required methods and classes
        with patch('aiohttp.ClientSession') as mock_session_class, \
             patch.object(BooksToScrapeCrawler, 'fetch_and_save_catalogue_page', side_effect=[None, "<html>Page 2</html>"]) as mock_fetch_cat, \
             patch.object(BooksToScrapeCrawler, 'fetch_and_save_books') as mock_fetch_books, \
             patch('app.ingestion.extractor.BooksDataExtractor.extract_book_urls_from_catalogue',
                   new_callable=AsyncMock, return_value=["http://books.com/catalogue/book-1_123/index.html"]) as mock_extract:

            # Set up session context manager
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session

            # Call the method
            await crawler.crawl_all_books()

            # Assertions
            assert mock_fetch_cat.call_count == 2  # Called for both pages
            assert mock_extract.call_count == 1    # Only called for the successful page
            mock_fetch_books.assert_called_once()  # Still called with the URLs from page 2
