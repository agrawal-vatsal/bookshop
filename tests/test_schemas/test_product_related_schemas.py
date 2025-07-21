import pytest
from pydantic import ValidationError

from schemas.product import BookDetailOut


class TestProductOut:

    def test_product_out_valid_full(self):
        product = BookDetailOut(
            id=1,
            name="Widget",
            price=12.5,
            rating=4,
            description="A useful widget",
            category="Tools",
            upc="123456789012",
            availability="In Stock",
            stock_count=10
        )
        assert product.id == 1
        assert product.name == "Widget"
        assert product.price == 12.5
        assert product.rating == 4
        assert product.description == "A useful widget"
        assert product.category == "Tools"
        assert product.upc == "123456789012"
        assert product.availability == "In Stock"
        assert product.stock_count == 10

    def test_valid_required_fields_only(self):
        BookDetailOut(
            id=2,
            name="Gadget",
            price=2.50,
            rating=5
        )

    def test_invalid_price_type(self):
        with pytest.raises(ValidationError):
            BookDetailOut(
                id=3,
                name="Invalid",
                price="wrong_type",
                rating=3
            )

    def test_invalid_optional_stock_count_type(self):
        with pytest.raises(ValidationError):
            BookDetailOut(
                id=4,
                name="Another",
                price=5.50,
                rating=4,
                stock_count="wrong"
            )
