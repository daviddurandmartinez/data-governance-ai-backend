import logging

from src.modules.data_catalog.domain.entities import DataSource
from src.modules.data_catalog.infrastructure.db_discovery import DbDiscovery
from src.settings import Settings
from src.shared.database.sqlserver_engine import get_sqlserver_engine

logger = logging.getLogger(__name__)


class DataSourceRepository:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._discovered: list[DataSource] | None = None

    def _get_discovered_sources(self) -> list[DataSource]:
        if self._discovered is None and self._settings.is_db_discovery_enabled:
            logger.info("Discovering databases from %s:%s", self._settings.SQL_SERVER_HOST, self._settings.SQL_SERVER_PORT)
            engine = get_sqlserver_engine(
                host=self._settings.SQL_SERVER_HOST,
                port=self._settings.SQL_SERVER_PORT,
                user=self._settings.SQL_SERVER_USER,
                password=self._settings.SQL_SERVER_PASSWORD,
                database="master",
            )
            discovery = DbDiscovery(
                engine=engine,
                host=self._settings.SQL_SERVER_HOST,
                port=self._settings.SQL_SERVER_PORT,
                user=self._settings.SQL_SERVER_USER,
                password=self._settings.SQL_SERVER_PASSWORD,
                exclude_databases=[self._settings.CATALOG_DB_NAME],
            )
            self._discovered = discovery.discover_databases()
        return self._discovered or []

    def get_all(self) -> list[DataSource]:
        return self._get_discovered_sources()

    def get_by_id(self, data_source_id: str) -> DataSource | None:
        for ds in self._get_discovered_sources():
            if ds.id == data_source_id:
                return ds
        return None

    def get_engine(self, data_source: DataSource):
        return get_sqlserver_engine(
            host=data_source.host,
            port=data_source.port,
            user=data_source.user,
            password=data_source.password,
            database=data_source.database_name,
        )
