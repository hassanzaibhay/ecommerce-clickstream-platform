import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

import database

router = APIRouter()


def _serialize(obj: Any) -> Any:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


async def _event_generator(pool: asyncpg.Pool) -> Any:
    """Poll live_sessions every 2 s and yield SSE frames.

    The pool is captured at request time (inside the route handler, after the
    lifespan has run) and passed in explicitly.  This avoids the module-level
    'from database import _pool' trap where the name is bound to None at import
    time, as well as any race where the generator might first tick before the
    lifespan completes.
    """
    while True:
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT session_id, user_id, last_event_time, event_count, "
                    "has_cart, has_purchase, last_category "
                    "FROM live_sessions ORDER BY updated_at DESC LIMIT 20"
                )
                sessions = [
                    {
                        "session_id": r["session_id"],
                        "user_id": r["user_id"],
                        "last_event_time": r["last_event_time"].isoformat() if r["last_event_time"] else None,
                        "event_count": r["event_count"],
                        "has_cart": r["has_cart"],
                        "has_purchase": r["has_purchase"],
                        "last_category": r["last_category"] or "",
                    }
                    for r in rows
                ]
                yield f"data: {json.dumps(sessions, default=_serialize)}\n\n"
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"SSE error: {e}")
            yield "data: []\n\n"
        await asyncio.sleep(2)


@router.get("/live/sessions")
async def live_sessions() -> StreamingResponse:
    """SSE stream of the 20 most-recently updated live sessions, refreshed every 2 s."""
    # Capture pool here — lifespan has definitely run by the time any request
    # arrives, so database._pool is the live asyncpg.Pool object, not None.
    pool = database._pool
    if pool is None:
        # Should never happen in normal operation; guard for tests/startup races.
        async def _empty() -> AsyncGenerator[str, None]:
            yield "data: []\n\n"
        return StreamingResponse(_empty(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    return StreamingResponse(
        _event_generator(pool),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/live/events")
async def live_events(
    limit: int = Query(default=50, ge=1, le=200),
    db: asyncpg.Connection = Depends(database.get_db),
) -> list[dict[str, Any]]:
    """REST snapshot of recent live sessions — REST alternative to the SSE endpoint."""
    rows = await db.fetch(
        "SELECT session_id, user_id, last_event_time, event_count, "
        "has_cart, has_purchase, last_category "
        "FROM live_sessions ORDER BY updated_at DESC LIMIT $1",
        limit,
    )
    return [
        {
            "session_id": r["session_id"],
            "user_id": r["user_id"],
            "last_event_time": r["last_event_time"].isoformat() if r["last_event_time"] else None,
            "event_count": r["event_count"],
            "has_cart": r["has_cart"],
            "has_purchase": r["has_purchase"],
            "last_category": r["last_category"] or "",
        }
        for r in rows
    ]
