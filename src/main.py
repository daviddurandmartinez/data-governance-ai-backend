from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.modules.data_catalog.presentation.router import router as catalog_router
from src.settings import settings
from src.shared.database.session import init_catalog_db
from src.shared.exceptions import (
    DomainError,
    domain_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
)
from src.shared.health import router as health_router


def create_app() -> FastAPI:
    try:
        init_catalog_db()
    except Exception:
        pass

    app = FastAPI(
        title="Data Governance AI Backend",
        description="Agente Inteligente de Gobierno de Datos y Catálogo Automatizado",
        version="0.1.0",
    )

    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(catalog_router)
    return app


app = create_app()


#uvicorn src.main:app --reload --host 0.0.0.0 --port 8000''''''