from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

if TYPE_CHECKING:
    pass

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _get_engine() -> Engine:
    global _engine
    if _engine is None:
        from src.settings import settings

        uri = URL.create(
            "mssql+pyodbc",
            username=settings.CATALOG_DB_USER,
            password=settings.CATALOG_DB_PASSWORD,
            host=settings.CATALOG_DB_HOST,
            port=settings.CATALOG_DB_PORT,
            database=settings.CATALOG_DB_NAME,
            query={
                "driver": "ODBC Driver 18 for SQL Server",
                "MARS_Connection": "yes",
                "Encrypt": "no",
                "TrustServerCertificate": "yes",
                "Trusted_Connection": "no",
            },
        )
        _engine = create_engine(
            uri,
            pool_pre_ping=True,
            pool_timeout=60,
            connect_args={"timeout": 60},
        )
    return _engine


def get_session_local() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_get_engine(),
            expire_on_commit=False,
        )
    return _SessionLocal


class Base(DeclarativeBase):
    ...


def get_session():
    SessionLocal = get_session_local()
    with SessionLocal() as session:
        yield session


def init_catalog_db() -> None:
    engine = _get_engine()
    Base.metadata.create_all(engine)
