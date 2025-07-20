# Bookshop: Async E-commerce Analytics & AI Microservice

This project provides async scraping, robust storage, RESTful APIs, and AI-driven analytics for e-commerce products (books example).

---

## Features

- **Async Crawler:** Collects and normalizes product data (name, price, rating, description, category, upc, availability, stock_count), and persists raw HTML for reprocessing.
- **SQLAlchemy ORM & Alembic Migrations:** Persistent relational schema with Postgres pgvector-ready setup, working with Docker for local and CI.
- **REST API:** FastAPI-based, Pydantic-validated endpoints with:
  - Paginated listing with filtering/search
  - Product detail view
  - Recommendations endpoint (with embeddings)
  - Trends analytics
- **AI Module:**
  - Embedding generation using `sentence-transformers`
  - LLM-based summaries for products
  - Both AI features have explicit code for bulk generation and updating
- **Testing:** Project contains pytest support and configuration
- **Deployment:** Containerized via Docker & Compose; Postgres+FastAPI bundled
- **CI:** Ready for simple workflow in .github/workflows

---

## Architecture Summary

- `app/ingestion/`: Crawling & data normalization logic (async, aiohttp/bs4)
- `app/models/`: SQLAlchemy models (`product.py` shows `Book` and `BookAIDetails` with vector+summary)
- `app/ai/`: 
  - `embeddings.py`: Embedding generation and storage
  - `llm_summariser.py`: For LLM-driven summary
  - `recommender.py`: For similarity-based recommendations
- `app/api/`: FastAPI endpoints and routers
- `alembic/`: Migrations
- Docker, Compose, Pytest, Ruff, MyPy, and Coverage configs

---

## Setup & Installation

### Requirements

- Python 3.13+
- Docker & Docker Compose
- PostgreSQL server

### 1. Clone and prepare

```bash
git clone https://github.com/agrawal-vatsal/bookshop.git
cd bookshop
cp .env.example .env  # Edit DB URI as needed, but matches Docker defaults
python3 -m venv .venv
source .venv/bin/activate  # Activate virtual environment
pip install uv
uv sync
```

### 2. Launch with Docker Compose (Recommended)

All app and DB services will spin up:

```bash
docker compose up --build
# FastAPI at http://localhost:8000
# PostgreSQL at localhost:5432 (user: bookshopuser, pass: bookshoppassword, db: bookshopdb)
```

---

## Usage

Before starting the application, please add the OpenAI API keys to the `.env` file. The keys are required for generating summaries.

## Running docker-compose web shell

```
docker-compose exec web bash
```
Run all the following commands inside the web shell.

### 1. Apply Migrations

Migrations are in `alembic/` directory:

To migrate the database schema to the latest version, run:
```bash
alembic upgrade head
```

This will create all needed tables: `books` and `book_ai_details` (with embedding vector columns).

### 2. Crawl Product Data

To collect book data from websites:

```bash
python -m app.ingestion.crawler
```

This will save raw HTML and produce normalized records (books) to seed the database.

All the files will be saved in `app/data/raw_html` directory, including raw HTML files.

### 3. Seed the Database

After crawling and normalizing the data:

```bash
python -m app.ingestion.seed
```

This will insert the normalized product data into the database.

### 4. Generate Embeddings

To generate and store embeddings for all books that don't have them:

```bash
python -m app.ai.embeddings
```

This uses `generate_and_store_embeddings()` function to create vector embeddings for each product using sentence-transformers, and stores them in the `book_ai_details.embedding` column.

### 5. Generate LLM Summaries

To create summaries for all books:

```bash
python -m app.ai.llm_summariser
```

This will query an LLM for each product that lacks a summary and update the database with concise descriptions.

---

## Running the API

The app is bootstrapped via `app/main.py`:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## API Endpoints

### Products

#### `GET /api/v1/products`
Returns a paginated list of books with filtering options.

**Query Parameters:**
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 20, max: 100)
- `min_price`: Filter by minimum price (optional)
- `max_price`: Filter by maximum price (optional)
- `min_rating`: Filter by minimum rating (1-5, optional)
- `category`: Filter by book category (optional)
- `q`: Search query string (optional)

**Response:**
```json
{
  "books": [
    {
      "id": int,
      "name": str,
      "price": float,
      "rating": int,
      "category": str,
      "upc": str,
      "availability": str,
      "stock_count": int,
    }
  ],
  "total": 123
}
```

#### `GET /api/v1/products/{book_id}`
Returns detailed information about a specific book.

**Path Parameters:**
- `book_id`: The ID of the book to retrieve

**Response:**
```json
{
  "id": int,
  "name": str,
  "price": float,
  "rating": int,
  "category": str,
  "upc": str,
  "availability": str,
  "stock_count": int,
  "description": str,
  "ai_summary": str | null,  // AI-generated summary if available
}
```

**Error Responses:**
- `404 Not Found`: Book with the specified ID doesn't exist

### Analytics

#### `GET /api/v1/analytics/trends`
Returns pricing, rating, or category analysis of the book catalog.

**Response:**
Trend analysis data including pricing patterns and rating distributions.

#### `GET /api/v1/analytics/recommendations/{product_id}`
Returns books similar to the specified book using vector embeddings.

**Path Parameters:**
- `product_id`: The ID of the book to find recommendations for

**Query Parameters:**
- `limit`: Maximum number of recommendations to return (optional)

**Response:**
A list of recommended books sorted by similarity score.

**Error Responses:**
- `404 Not Found`: Book with the specified ID doesn't exist

All endpoints are type-safe and validated with Pydantic models.

---

## Testing

```bash
pytest
```

### Test Coverage

The project is configured with coverage.py to track test coverage. To run tests with coverage and generate a report:

```bash
# Run tests with coverage
coverage run -m pytest

# Generate a coverage report
coverage report

# Generate an HTML coverage report
coverage html
```

The HTML report will be available in the `htmlcov` directory and provides a detailed breakdown of coverage by file and line.

Coverage settings are configured in `pyproject.toml` with:
- Branch coverage enabled
- Minimum coverage threshold of 80%
- Missing line reporting

---

## Development & Linting

- Lint: `ruff .`
- Type check: `mypy .`

---

## Environment Variables

**.env.example** is provided; set `OpenAI API keys.

---

## Summary of Testing Steps

For someone testing this application, follow these steps in order:

1. **Start the environment**: `docker compose up --build`
2. **Apply migrations**: `alembic upgrade head`
3. **Crawl data**: `python -m app.ingestion.crawler`
4. **Seed database**: `python -m app.ingestion.seed`
5. **Generate embeddings**: `python -m app.ai.embeddings`
6. **Generate summaries**: `python -m app.ai.llm_summariser`

---

## Troubleshooting

- **Docker issues?**  
  Ensure Docker is running and you have sufficient resources allocated (CPU, memory).
- **LLM API errors?**  
  Set proper keys/URL in `.env`.
- **Database connection issues?**  
  Stop the local Postgres server if running, and ensure Docker is configured correctly. This is needed as both point to the port 5432.

---

_For questions, issues, or support: raise a GitHub issue or contact the maintainer._