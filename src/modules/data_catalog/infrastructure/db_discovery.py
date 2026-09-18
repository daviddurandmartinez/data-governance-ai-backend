import logging

from sqlalchemy import Engine, text

from src.modules.data_catalog.domain.entities import DataSource
from src.shared.exceptions import ExtractionError

logger = logging.getLogger(__name__)


class DbDiscovery:
    def __init__(
        self,
        engine: Engine,
        host: str,
        port: int,
        user: str,
        password: str,
        exclude_databases: list[str] | None = None,
    ) -> None:
        self._engine = engine
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._exclude = set(exclude_databases) if exclude_databases else set()

    def discover_databases(self) -> list[DataSource]:
        system_dbs = {"master", "tempdb", "model", "msdb"}
        excluded = system_dbs | self._exclude
        excluded_str = ", ".join(f"'{db}'" for db in sorted(excluded))

        try:
            with self._engine.connect() as conn:
                result = conn.execute(
                    text(f"SELECT name FROM sys.databases WHERE name NOT IN ({excluded_str})"),
                )
                databases = [row[0] for row in result]
                logger.info("Discovered %d databases", len(databases))
        except Exception as e:
            logger.error("Error discovering databases: %s", e)
            raise ExtractionError(f"Error discovering databases: {e}") from e

        return [
            DataSource(
                id=db,
                name=db,
                db_type="sqlserver",
                host=self._host,
                port=self._port,
                database_name=db,
                user=self._user,
                password=self._password,
            )
            for db in sorted(databases)
        ]
