from datetime import date
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, Query

from database import get_db

router = APIRouter()


@router.get("/overview")
async def get_overview(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: asyncpg.Connection = Depends(get_db),
) -> dict[str, Any]:
    """Aggregate KPIs and daily trend for the given date range."""
    row = await db.fetchrow(
        """
        SELECT
            COALESCE(SUM(total_events), 0) AS total_events,
            COALESCE(SUM(unique_users), 0) AS unique_users,
            COALESCE(SUM(total_views), 0) AS total_views,
            COALESCE(SUM(total_carts), 0) AS total_carts,
            COALESCE(SUM(total_purchases), 0) AS total_purchases,
            COALESCE(SUM(total_revenue), 0) AS total_revenue,
            CASE WHEN SUM(unique_users) > 0
                 THEN SUM(total_purchases)::NUMERIC / SUM(unique_users)
                 ELSE 0 END AS conversion_rate,
            CASE WHEN SUM(total_purchases) > 0
                 THEN SUM(total_revenue) / SUM(total_purchases)
                 ELSE 0 END AS avg_order_value
        FROM daily_metrics
        WHERE date >= $1 AND date <= $2
        """,
        start_date,
        end_date,
    )

    daily_trend = await db.fetch(
        """
        SELECT date, total_views, total_carts, total_purchases, total_revenue
        FROM daily_metrics
        WHERE date >= $1 AND date <= $2
        ORDER BY date
        """,
        start_date,
        end_date,
    )

    if row is None:
        return {
            "total_events": 0,
            "unique_users": 0,
            "total_revenue": 0,
            "conversion_rate": 0,
            "avg_order_value": 0,
            "total_views": 0,
            "total_carts": 0,
            "total_purchases": 0,
            "daily_trend": [],
        }

    return {
        "total_events": int(row["total_events"]),
        "unique_users": int(row["unique_users"]),
        "total_revenue": float(row["total_revenue"]),
        "conversion_rate": float(row["conversion_rate"]),
        "avg_order_value": float(row["avg_order_value"]),
        "total_views": int(row["total_views"]),
        "total_carts": int(row["total_carts"]),
        "total_purchases": int(row["total_purchases"]),
        "daily_trend": [
            {
                "date": str(r["date"]),
                "views": int(r["total_views"]),
                "carts": int(r["total_carts"]),
                "purchases": int(r["total_purchases"]),
                "revenue": float(r["total_revenue"]),
            }
            for r in daily_trend
        ],
    }
