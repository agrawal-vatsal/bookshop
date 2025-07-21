import factory
from app.models.product import Book, BookAIDetails


class BookFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Book
        sqlalchemy_session_persistence = "flush"

    id = factory.Sequence(lambda n: n + 1)
    name = factory.Faker("sentence", nb_words=3)
    price = factory.Faker("pyfloat", left_digits=2, right_digits=2, positive=True, min_value=5, max_value=40)
    rating = factory.Faker("pyint", min_value=1, max_value=5)
    category = factory.Iterator(["Fiction", "Non-fiction", "Science", "History", "Children"])
    upc = factory.Faker("ean13")
    description = factory.Faker("text")
    availability = factory.Faker("word")
    stock_count = factory.Faker("pyint", min_value=0, max_value=50)


class BookAIDetailsFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = BookAIDetails
        sqlalchemy_session_persistence = "flush"

    id = factory.Sequence(lambda n: n + 1)
    book_id = factory.SubFactory(BookFactory)
    summary = factory.Faker("text", max_nb_chars=200)
