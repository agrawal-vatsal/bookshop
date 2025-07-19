import os
from unittest.mock import mock_open, patch

import pytest
from bs4 import BeautifulSoup

from app.ingestion.constants import CATALOGUE_URL
from app.ingestion.extractor import BooksDataExtractor, SingleBookDataExtractor


class TestExtractor:
    """Test suite for extractor module"""

    # Sample HTML fixtures
    @pytest.fixture
    def sample_book_html(self):
        return """
        <html>
            <div class="product_main">
                <h1>Test Book Title</h1>
                <p class="price_color">£29.99</p>
                <p class="star-rating Four"></p>
            </div>
            <div id="product_description">
                <h2>Product Description</h2>
            </div>
            <p>This is a sample book description.</p>
            <ul class="breadcrumb">
                <li><a href="/">Home</a></li>
                <li><a href="/category">Fiction</a></li>
                <li><a href="/category/subcategory">Mystery</a></li>
            </ul>
            <table class="table table-striped">
                <tr>
                    <th>UPC</th>
                    <td>123456789</td>
                </tr>
                <tr>
                    <th>Availability</th>
                    <td>In stock (15 available)</td>
                </tr>
            </table>
        </html>
        """

    @pytest.fixture
    def sample_catalogue_html(self):
        return """
        <html>
            <article class="product_pod">
                <h3><a href="../../../book1.html">Book 1</a></h3>
            </article>
            <article class="product_pod">
                <h3><a href="../../../book2.html">Book 2</a></h3>
            </article>
            <article class="product_pod">
                <h3><a href="../../../book3.html">Book 3</a></h3>
            </article>
        </html>
        """

    # SingleBookDataExtractor tests
    def test_single_book_extractor_init(self, sample_book_html):
        """Test initialization of SingleBookDataExtractor"""
        extractor = SingleBookDataExtractor(sample_book_html)
        assert extractor.html == sample_book_html
        assert isinstance(extractor.soup, BeautifulSoup)

    def test_parse_rating(self, sample_book_html):
        """Test parsing rating from book HTML"""
        extractor = SingleBookDataExtractor(sample_book_html)
        assert extractor.parse_rating() == 4

    def test_parse_rating_missing(self):
        """Test parsing rating when star-rating element is missing"""
        html = "<html><body></body></html>"
        extractor = SingleBookDataExtractor(html)
        assert extractor.parse_rating() is None

    def test_parse_rating_invalid_class(self):
        """Test parsing rating with invalid star-rating class"""
        html = "<html><p class='star-rating Invalid'></p></html>"
        extractor = SingleBookDataExtractor(html)
        assert extractor.parse_rating() is None

    def test_get_name(self, sample_book_html):
        """Test extracting book name"""
        extractor = SingleBookDataExtractor(sample_book_html)
        assert extractor.get_name() == "Test Book Title"

    def test_get_name_missing(self):
        """Test extracting book name when element is missing"""
        html = "<html><body></body></html>"
        extractor = SingleBookDataExtractor(html)
        with pytest.raises(AttributeError):
            extractor.get_name()

    def test_get_price(self, sample_book_html):
        """Test extracting book price"""
        extractor = SingleBookDataExtractor(sample_book_html)
        assert extractor.get_price() == 29.99

    def test_get_price_missing(self):
        """Test extracting book price when element is missing"""
        html = "<html><body></body></html>"
        extractor = SingleBookDataExtractor(html)
        assert extractor.get_price() is None

    def test_get_description(self, sample_book_html):
        """Test extracting book description"""
        extractor = SingleBookDataExtractor(sample_book_html)
        assert extractor.get_description() == "This is a sample book description."

    def test_get_description_missing_header(self):
        """Test extracting description when product_description is missing"""
        html = "<html><body></body></html>"
        extractor = SingleBookDataExtractor(html)
        assert extractor.get_description() is None

    def test_get_description_missing_paragraph(self):
        """Test extracting description when paragraph is missing"""
        html = "<html><div id='product_description'></div></html>"
        extractor = SingleBookDataExtractor(html)
        assert extractor.get_description() is None

    def test_get_category(self, sample_book_html):
        """Test extracting book category"""
        extractor = SingleBookDataExtractor(sample_book_html)
        assert extractor.get_category() == "Mystery"

    def test_get_category_two_links(self):
        """Test extracting category with only two breadcrumb links"""
        html = """
        <html>
            <ul class="breadcrumb">
                <li><a href="/">Home</a></li>
                <li><a href="/category">Fiction</a></li>
            </ul>
        </html>
        """
        extractor = SingleBookDataExtractor(html)
        assert extractor.get_category() == "Fiction"

    def test_get_category_missing(self):
        """Test extracting category when breadcrumb is missing"""
        html = "<html><body></body></html>"
        extractor = SingleBookDataExtractor(html)
        assert extractor.get_category() is None

    def test_get_extra_attributes(self, sample_book_html):
        """Test extracting additional book attributes"""
        extractor = SingleBookDataExtractor(sample_book_html)
        attrs = extractor.get_extra_attributes()
        assert attrs["upc"] == "123456789"
        assert attrs["availability"] == "In stock (15 available)"
        assert attrs["stock_count"] == 15

    def test_get_extra_attributes_missing_table(self):
        """Test extracting attributes when table is missing"""
        html = "<html><body></body></html>"
        extractor = SingleBookDataExtractor(html)
        attrs = extractor.get_extra_attributes()
        assert attrs["upc"] is None
        assert attrs["availability"] is None
        assert attrs["stock_count"] is None

    def test_get_extra_attributes_no_stock_count(self):
        """Test extracting attributes when stock count format is different"""
        html = """
        <html>
            <table class="table table-striped">
                <tr>
                    <th>UPC</th>
                    <td>123456789</td>
                </tr>
                <tr>
                    <th>Availability</th>
                    <td>Out of stock</td>
                </tr>
            </table>
        </html>
        """
        extractor = SingleBookDataExtractor(html)
        attrs = extractor.get_extra_attributes()
        assert attrs["stock_count"] is None

    def test_extract_book_data(self, sample_book_html):
        """Test the main extract_book_data method"""
        with patch('app.ingestion.extractor.logger') as mock_logger:
            extractor = SingleBookDataExtractor(sample_book_html)
            data = extractor.extract_book_data()

            assert data["name"] == "Test Book Title"
            assert data["price"] == 29.99
            assert data["rating"] == 4
            assert data["description"] == "This is a sample book description."
            assert data["category"] == "Mystery"
            assert data["upc"] == "123456789"
            assert data["availability"] == "In stock (15 available)"
            assert data["stock_count"] == 15

            # Check that logging happened
            mock_logger.info.assert_called_once()

    # BooksDataExtractor tests
    @pytest.mark.asyncio
    async def test_extract_book_urls_from_catalogue(self, sample_catalogue_html):
        """Test extracting book URLs from catalogue HTML"""
        with patch('app.ingestion.extractor.logger') as mock_logger:
            urls = await BooksDataExtractor.extract_book_urls_from_catalogue(sample_catalogue_html)
            assert len(urls) == 3
            assert urls[0] == f"{CATALOGUE_URL}/book1.html"
            assert urls[1] == f"{CATALOGUE_URL}/book2.html"
            assert urls[2] == f"{CATALOGUE_URL}/book3.html"
            assert mock_logger.info.call_count == 3

    @pytest.mark.asyncio
    async def test_extract_book_urls_from_catalogue_empty(self):
        """Test extracting book URLs from empty HTML"""
        html = "<html><body></body></html>"
        urls = await BooksDataExtractor.extract_book_urls_from_catalogue(html)
        assert len(urls) == 0

    @pytest.mark.asyncio
    async def test_extract_book_urls_from_catalogue_no_href(self):
        """Test extracting book URLs when href attribute is missing"""
        html = "<html><article class='product_pod'><h3><a>No Href Book</a></h3></article></html>"
        urls = await BooksDataExtractor.extract_book_urls_from_catalogue(html)
        assert len(urls) == 0

    def test_extract_books_from_dir(self):
        """Test extracting books from a directory"""
        # Mock directory content
        mock_files = ['book_1.html', 'book_2.html', 'other_file.txt']

        # Mock file reading and extraction
        mock_data = {"name": "Test Book"}

        with patch('os.listdir', return_value=mock_files), \
             patch('os.path.join', side_effect=lambda dir, file: f"{dir}/{file}"), \
             patch('builtins.open', mock_open(read_data="dummy html")), \
             patch.object(SingleBookDataExtractor, 'extract_book_data', return_value=mock_data), \
             patch('app.ingestion.extractor.logger') as mock_logger:

            books = BooksDataExtractor.extract_books_from_dir('/fake/path')

            assert len(books) == 2  # Only 2 HTML files with 'book_' prefix
            assert books[0] == mock_data
            assert books[1] == mock_data
            mock_logger.info.assert_called_once()

    def test_extract_books_from_dir_no_books(self):
        """Test extracting books when directory has no book files"""
        with patch('os.listdir', return_value=[]), \
             patch('app.ingestion.extractor.logger') as mock_logger:
            books = BooksDataExtractor.extract_books_from_dir('/fake/path')
            assert len(books) == 0
            mock_logger.info.assert_called_once_with("Extracted 0 books from directory /fake/path")

    def test_extract_books_from_dir_extraction_returns_none(self):
        """Test extracting books when extraction returns None"""
        with patch('os.listdir', return_value=['book_1.html']), \
             patch('os.path.join', side_effect=lambda dir, file: f"{dir}/{file}"), \
             patch('builtins.open', mock_open(read_data="dummy html")), \
             patch.object(SingleBookDataExtractor, 'extract_book_data', return_value=None), \
             patch('app.ingestion.extractor.logger') as mock_logger:

            books = BooksDataExtractor.extract_books_from_dir('/fake/path')
            assert len(books) == 0
            mock_logger.info.assert_called_once_with("Extracted 0 books from directory /fake/path")

    def test_extract_books_from_dir_custom_directory(self):
        """Test extracting books from a custom directory"""
        custom_dir = "/custom/path"
        mock_files = ['book_1.html']
        mock_data = {"name": "Test Book"}

        with patch('os.listdir', return_value=mock_files), \
             patch('os.path.join', side_effect=lambda dir, file: f"{dir}/{file}"), \
             patch('builtins.open', mock_open(read_data="dummy html")), \
             patch.object(SingleBookDataExtractor, 'extract_book_data', return_value=mock_data), \
             patch('app.ingestion.extractor.logger') as mock_logger:

            books = BooksDataExtractor.extract_books_from_dir(custom_dir)

            assert len(books) == 1
            assert books[0] == mock_data
            # Verify that the custom directory was used
            os.path.join.assert_called_with(custom_dir, mock_files[0])
