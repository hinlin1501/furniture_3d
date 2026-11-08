from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.dependencies import DbSession

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Liveness probe")
def health() -> dict:
    return {"status": "ok"}


@router.get("/health/ready", summary="Readiness probe (checks database)")
def ready(db: DbSession):
    try:
        db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        return JSONResponse(status_code=503, content={"status": "unavailable", "database": "down"})
    return {"status": "ok", "database": "up"}
