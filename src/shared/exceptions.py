from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class DomainError(Exception):
    def __init__(self, message: str = "Domain error occurred") -> None:
        self.message = message
        super().__init__(self.message)


class DataSourceNotFoundError(DomainError):
    def __init__(self, data_source_id: str) -> None:
        super().__init__(f"Data source not found: {data_source_id}")


class ExtractionError(DomainError):
    def __init__(self, message: str = "Failed to extract metadata") -> None:
        super().__init__(message)


class EnrichmentError(DomainError):
    def __init__(self, message: str = "Failed to enrich metadata") -> None:
        super().__init__(message)


class CatalogNotFoundError(DomainError):
    def __init__(self, data_source_id: str, table_name: str) -> None:
        super().__init__(
            f"Catalog entry not found for table '{table_name}' in data source '{data_source_id}'"
        )


async def domain_error_handler(
    request: Request, exc: DomainError
) -> JSONResponse:
    status_code = 404 if isinstance(exc, (DataSourceNotFoundError, CatalogNotFoundError)) else 422
    return JSONResponse(
        status_code=status_code,
        content={"error": exc.message},
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
