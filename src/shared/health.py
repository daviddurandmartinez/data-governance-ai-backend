from fastapi import APIRouter
from sqlalchemy import text

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def health_live():
    return {"status": "ok"}


@router.get("/ready")
def health_ready():
    try:
        from src.shared.database.session import get_session_local

        SessionLocal = get_session_local()
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=503,
            content={"status": "error", "detail": f"Database not available: {type(e).__name__}"},
        )
