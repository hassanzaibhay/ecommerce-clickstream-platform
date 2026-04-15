from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import lifespan
from routers import funnel, live, overview, products

app = FastAPI(
    title="Clickstream Analytics API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dev config — restrict to specific origins in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(overview.router, prefix="/api")
app.include_router(funnel.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(live.router, prefix="/api")


@app.get("/api/health")
async def health() -> dict[str, str]:
    """Liveness probe — returns service status and UTC timestamp."""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/data-range")
async def data_range() -> dict[str, str]:
    """Return the min/max dates of the dataset so the UI can anchor date pickers."""
    return {"min_date": "2019-10-01", "max_date": "2019-11-30"}
