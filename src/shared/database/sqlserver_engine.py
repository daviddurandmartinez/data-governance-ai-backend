from __future__ import annotations

import logging
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import URL

logger = logging.getLogger(__name__)


def _make_engine_key(host: str, port: int, database: str, user: str) -> tuple[str, int, str, str]:
    return (host, port, database, user)


@lru_cache(maxsize=10)
def get_sqlserver_engine(
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
) -> Engine:
    key = _make_engine_key(host, port, database, user)
    logger.info("Creating SQL Server engine for %s:%s/%s", host, port, database)

    uri = URL.create(
        "mssql+pyodbc",
        username=user,
        password=password,
        host=host,
        port=port,
        database=database,
        query={
            "driver": "ODBC Driver 18 for SQL Server",
            "MARS_Connection": "yes",
            "Encrypt": "no",
            "TrustServerCertificate": "yes",
            "Trusted_Connection": "no",
        },
    )

    engine = create_engine(
        uri,
        echo=False,
        pool_size=2,
        max_overflow=3,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_timeout=60,
        connect_args={"timeout": 60},
    )

    logger.info("Engine created for %s:%s/%s (pool_size=2, timeout=60)", host, port, database)
    return engine


def clear_engine_cache() -> None:
    get_sqlserver_engine.cache_clear()
