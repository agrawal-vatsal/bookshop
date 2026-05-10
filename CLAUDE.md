# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes` or `query_graph` instead of Grep
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` instead of reading entire files
- **Finding relationships**: `query_graph` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview` + `list_communities`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool                        | Use when                                               |
|-----------------------------|--------------------------------------------------------|
| `detect_changes`            | Reviewing code changes — gives risk-scored analysis    |
| `get_review_context`        | Need source snippets for review — token-efficient      |
| `get_impact_radius`         | Understanding blast radius of a change                 |
| `get_affected_flows`        | Finding which execution paths are impacted             |
| `query_graph`               | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes`     | Finding functions/classes by name or keyword           |
| `get_architecture_overview` | Understanding high-level codebase structure            |
| `refactor_tool`             | Planning renames, finding dead code                    |

### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes` for code review.
3. Use `get_affected_flows` to understand impact.
4. Use `query_graph` pattern="tests_for" to check coverage.

---

## Commands

### Setup
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install uv && uv sync
```

### Run (Docker Compose — recommended)
```bash
docker compose up --build        # API at http://localhost:8000, DB at localhost:5432
docker-compose exec web bash     # shell into running web container
```

### Database migrations
```bash
alembic upgrade head
```

### Data pipeline (run inside the web container or with app DB reachable)
```bash
python -m app.ingestion.crawler   # crawl books.toscrape.com → raw HTML in app/data/raw_html/
python -m app.ingestion.seed      # parse HTML and insert Book rows
python -m app.ai.embeddings       # generate 384-dim sentence-transformer vectors
python -m app.ai.llm_summariser   # OpenAI summaries for books missing one
```

### Tests
Tests run against a **separate test database** on port 5433. Start it first:
```bash
docker compose up test_db         # or docker compose up (starts all services)
```
Then run tests:
```bash
pytest                            # all tests
pytest tests/test_crud/test_product.py::TestProductCrud::test_get_books_simple  # single test
coverage run -m pytest && coverage report   # with coverage (80% minimum enforced)
```

### Lint & type check
```bash
ruff .        # auto-fixes on save (pre-commit hook)
mypy .        # strict mode; excludes tests/ and alembic/
```

---

## Architecture

### Layer overview

```
app/api/          FastAPI routers — thin, delegate to crud/
app/crud/         Async SQLAlchemy queries — no HTTP concerns
app/models/       ORM models + async engine/session factory
app/schemas/      Pydantic response models (BookListOut, BookDetailOut)
app/ingestion/    Web crawler + HTML extractor + DB seeder (standalone scripts)
app/ai/           Embedding, LLM summary, and vector-similarity recommender (standalone scripts)
alembic/          Schema migrations
tests/            pytest-asyncio test suite against test_db
```

### Key design decisions

**Two separate databases**: The main app DB (`localhost:5432`, `bookshopdb`) is used at runtime. Tests always connect to `localhost:5433` (`bookshop_test`), hardcoded in `tests/conftest.py`. Both use the `pgvector/pgvector:pg15` image because the `BookAIDetails.embedding` column is a `Vector(384)`.

**Two ORM models, one-to-one**: `Book` (core product data) and `BookAIDetails` (AI-specific: `summary` string + `embedding` Vector(384)). The relationship is declared with `CASCADE` delete so removing a `Book` automatically removes its `BookAIDetails`. The AI columns live in a separate table so the ingestion pipeline never touches AI infra.

**Fully async**: The SQLAlchemy engine uses `asyncpg` (`postgresql+asyncpg://...`). All API handlers, CRUD functions, and test fixtures are `async`. `get_session()` in `app/models/db.py` is a FastAPI dependency that yields an `AsyncSession`.

**AI pipeline is script-based, not request-based**: `app/ai/embeddings.py` and `app/ai/llm_summariser.py` are run as one-off scripts (`python -m app.ai.*`) to backfill the DB. The embedding model is `all-MiniLM-L6-v2` (sentence-transformers, 384 dimensions). LLM summaries require `OPENAI_API_KEY` in `.env`.

**Test isolation**: `conftest.py` creates all tables once per session via `Base.metadata.create_all` and truncates `Book`/`BookAIDetails` before each test via the `cleanup_db` autouse fixture. `factory_boy` factories (`tests/factories.py`) generate `Book` and `BookAIDetails` instances.

**Ruff excludes `tests/`**: Linting is only enforced on `app/`. MyPy also excludes `tests/` and `alembic/`. Pre-commit runs both ruff and mypy on commit.
