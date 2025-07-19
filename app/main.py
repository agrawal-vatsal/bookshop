# app/main.py

from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(
        title="Bookshop API",
        version="1.0.0",
        description="Microservice for books with analytics and AI-powered features"
    )

    # Optionally: add root health check
    @app.get("/", tags=["Health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

# For `uvicorn app.main:app`
