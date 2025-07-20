from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics import (
    average_price_by_category,
    average_price_by_rating_decile,
    avg_rating_for_popular_categories,
    get_highest_rated_books_per_category,
    most_common_categories,
)
from app.models.db import get_session

router = APIRouter()

# Define available trends metadata
AVAILABLE_TRENDS = {
    "price_by_rating_decile": {
        "name": "Price by Rating Decile",
        "description": "Average price grouped by rating deciles",
        "endpoint": "/trends/price_by_rating_decile"
    },
    "top_categories": {
        "name": "Top Categories",
        "description": "Most common product categories",
        "endpoint": "/trends/top_categories"
    },
    "average_rating_by_category": {
        "name": "Average Rating by Category",
        "description": "Average ratings for popular categories",
        "endpoint": "/trends/average_rating_by_category"
    },
    "average_price_by_category": {
        "name": "Average Price by Category",
        "description": "Average price grouped by category",
        "endpoint": "/trends/average_price_by_category"
    },
    "highest_rated_books_per_category": {
        "name": "Highest Rated Books in each category",
        "description": "Books with the highest ratings for each category",
        "endpoint": "/trends/highest_rated_books_per_category"
    },
}


@router.get("/trends")
async def get_available_trends() -> dict[str, Any]:
    """Get list of available trends with their metadata"""
    return {
        "trends": AVAILABLE_TRENDS
    }


@router.get("/trends/{trend_key}")
async def get_trend_data(trend_key: str,
                         session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    """Get data for a specific trend"""
    if trend_key not in AVAILABLE_TRENDS:
        raise HTTPException(status_code=404, detail=f"Trend '{trend_key}' not found")

    if trend_key == "price_by_rating_decile":
        data = await average_price_by_rating_decile(session)
    elif trend_key == "top_categories":
        data = await most_common_categories(session, k=3)
    elif trend_key == "average_rating_by_category":
        data = await avg_rating_for_popular_categories(session, min_count=3)
    elif trend_key == "average_price_by_category":
        data = await average_price_by_category(session)
    elif trend_key == "highest_rated_books_per_category":
        data = await get_highest_rated_books_per_category(session)
        print(data)

    return {
        "trend_key": trend_key,
        "trend_info": AVAILABLE_TRENDS[trend_key],
        "data": data
    }
