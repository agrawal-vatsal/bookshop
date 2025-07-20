from api import analytics, products
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(
        title="Bookshop API",
        version="1.0.0",
        description="Microservice for books with analytics and AI-powered features"
    )

    app.include_router(products.router, prefix="/api/v1/products", tags=["Products"])
    app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])

    # Optionally: add root health check
    @app.get("/", tags=["Health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
