from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, Query

from database import get_db

router = APIRouter()


@router.get("/products")
async def get_products(
    limit: int = Query(default=20, ge=1, le=100),
    db: asyncpg.Connection = Depends(get_db),
) -> dict[str, Any]:
    """Return top products ranked by revenue."""
    rows = await db.fetch(
        """
        SELECT product_id, category, brand, price, views, carts, purchases, revenue
        FROM top_products
        ORDER BY revenue DESC
        LIMIT $1
        """,
        limit,
    )
    return {
        "products": [
            {
                "product_id": int(r["product_id"]),
                "category": r["category"] or "",
                "brand": r["brand"] or "",
                "price": float(r["price"]),
                "views": int(r["views"]),
                "carts": int(r["carts"]),
                "purchases": int(r["purchases"]),
                "revenue": float(r["revenue"]),
            }
            for r in rows
        ]
    }


@router.get("/brands")
async def get_brands(
    limit: int = Query(default=20, ge=1, le=100),
    db: asyncpg.Connection = Depends(get_db),
) -> dict[str, Any]:
    """Return top brands ranked by revenue."""
    rows = await db.fetch(
        """
        SELECT brand, views, carts, purchases, revenue
        FROM top_brands
        ORDER BY revenue DESC
        LIMIT $1
        """,
        limit,
    )
    return {
        "brands": [
            {
                "brand": r["brand"] or "",
                "views": int(r["views"]),
                "carts": int(r["carts"]),
                "purchases": int(r["purchases"]),
                "revenue": float(r["revenue"]),
            }
            for r in rows
        ]
    }


@router.get("/categories")
async def get_categories(
    db: asyncpg.Connection = Depends(get_db),
) -> dict[str, Any]:
    """Return all categories ranked by revenue."""
    rows = await db.fetch(
        """
        SELECT category, views, carts, purchases, revenue
        FROM top_categories
        ORDER BY revenue DESC
        """
    )
    return {
        "categories": [
            {
                "category": r["category"] or "",
                "views": int(r["views"]),
                "carts": int(r["carts"]),
                "purchases": int(r["purchases"]),
                "revenue": float(r["revenue"]),
            }
            for r in rows
        ]
    }
