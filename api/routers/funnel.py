from datetime import date
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, Query

from database import get_db

router = APIRouter()


@router.get("/funnel")
async def get_funnel(
    start_date: date = Query(...),
    end_date: date = Query(...),
    category: str = Query(default="all"),
    db: asyncpg.Connection = Depends(get_db),
) -> dict[str, Any]:
    """Return view→cart→purchase funnel rates and top cart-abandonment categories."""
    categories_rows = await db.fetch(
        "SELECT DISTINCT category FROM funnel_stats ORDER BY category"
    )
    categories = [r["category"] for r in categories_rows]

    if category == "all":
        row = await db.fetchrow(
            """
            SELECT
                COALESCE(SUM(views), 0) AS views,
                COALESCE(SUM(carts), 0) AS carts,
                COALESCE(SUM(purchases), 0) AS purchases
            FROM funnel_stats
            WHERE date >= $1 AND date <= $2
            """,
            start_date,
            end_date,
        )
    else:
        row = await db.fetchrow(
            """
            SELECT
                COALESCE(SUM(views), 0) AS views,
                COALESCE(SUM(carts), 0) AS carts,
                COALESCE(SUM(purchases), 0) AS purchases
            FROM funnel_stats
            WHERE date >= $1 AND date <= $2 AND category = $3
            """,
            start_date,
            end_date,
            category,
        )

    views = int(row["views"]) if row else 0
    carts = int(row["carts"]) if row else 0
    purchases = int(row["purchases"]) if row else 0

    v2c = carts / views if views > 0 else 0
    c2p = purchases / carts if carts > 0 else 0
    overall = purchases / views if views > 0 else 0

    abandonment_rows = await db.fetch(
        """
        SELECT category,
               SUM(abandoned_carts) AS abandoned_carts,
               AVG(abandonment_rate) AS abandonment_rate
        FROM cart_abandonment
        WHERE date >= $1 AND date <= $2
        GROUP BY category
        ORDER BY AVG(abandonment_rate) DESC
        LIMIT 10
        """,
        start_date,
        end_date,
    )

    return {
        "stages": [
            {"stage": "Views", "count": views, "rate": 1.0},
            {"stage": "Cart Adds", "count": carts, "rate": round(v2c, 4)},
            {"stage": "Purchases", "count": purchases, "rate": round(overall, 4)},
        ],
        "categories": categories,
        "view_to_cart_rate": round(v2c, 4),
        "cart_to_purchase_rate": round(c2p, 4),
        "overall_conversion": round(overall, 4),
        "top_abandonment": [
            {
                "category": r["category"],
                "abandonment_rate": float(r["abandonment_rate"]),
                "abandoned_carts": int(r["abandoned_carts"]),
            }
            for r in abandonment_rows
        ],
    }
