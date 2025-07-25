import numpy as np
from sentence_transformers import SentenceTransformer

from app.crud.product import get_books_with_no_embedding
from app.models.db import async_session
from app.models.product import Book, BookAIDetails

MODEL_NAME = "all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_NAME)


def build_book_text(book: Book) -> str:
    # Combine title, description, category, etc.
    return " | ".join(str(s) for s in [
        book.name,
        book.description or "",
        book.category or "",
    ])


def embed_book(book: Book) -> np.ndarray:
    text = build_book_text(book)
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding


async def generate_and_store_embeddings() -> None:

    async with async_session() as session:
        # Single query to get all books with their BookAIDetails (if they exist)
        books = await get_books_with_no_embedding(session)

        new_details = []

        for book in books:
            vec = embed_book(book)
            embedding_list = vec.tolist()

            if hasattr(book, 'ai_details') and book.ai_details:
                # Update existing BookAIDetails - SQLAlchemy automatically tracks changes
                book.ai_details.embedding = embedding_list
            else:
                # Prepare new BookAIDetails for bulk insert
                new_details.append(BookAIDetails(book_id=book.id, embedding=embedding_list))

        # Bulk add new records
        if new_details:
            session.add_all(new_details)

        # Commit all changes (both updates and inserts)
        await session.commit()


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        print("Generating and storing embeddings for books...")
        await generate_and_store_embeddings()
        print("Embeddings generated and stored successfully.")

    asyncio.run(main())
