import asyncio
import pytest
import pytest_asyncio
from sqlalchemy import text, delete
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

from app.models.product import Book, BookAIDetails

# Your DB URL for testing
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5433/bookshop_test"

# Import your Base (update to match your project)
from app.models.db import Base

# Ensure a new event loop per session for async tests
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

# Create an async engine
@pytest_asyncio.fixture(scope="session")
async def async_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=True,
        poolclass=NullPool,
    )
    yield engine
    await engine.dispose()

# Create tables once per testing session and drop them after
@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database(async_engine):
    async with async_engine.begin() as conn:
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# Sessionmaker, bound to the test engine
@pytest_asyncio.fixture(scope="session")
async def async_session_maker(async_engine, prepare_database):
    return async_sessionmaker(
        async_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

# Function-scoped async session for test isolation
@pytest_asyncio.fixture
async def async_session(async_session_maker):
    async with async_session_maker() as session:
        yield session

@pytest_asyncio.fixture(autouse=True)
async def cleanup_db(async_session):
    await async_session.execute(delete(BookAIDetails))
    await async_session.execute(delete(Book))
    await async_session.commit()
    yield
