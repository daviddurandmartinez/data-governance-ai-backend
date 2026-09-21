import logging

from sqlalchemy import Engine

from src.modules.data_catalog.domain.entities import DataSource
from src.modules.data_catalog.infrastructure.db_discovery import DbDiscovery
from src.shared.database.sqlserver_engine import get_sqlserver_engine
from src.shared.exceptions import ExtractionError

logger = logging.getLogger(__name__)


class DataSourceRepository:
    def __init__(self) -> None:
        self._connection: dict | None = None
        self._discovered: list[DataSource] | None = None

    def set_connection(self, host: str, port: int, user: str, password: str) -> list[DataSource]:
        self._connection = {"host": host, "port": port, "user": user, "password": password}
        self._discovered = None
        return self.get_all()

    def get_connection(self) -> dict:
        if self._connection is None:
            raise ExtractionError("No hay conexion activa. Llama a POST /connection primero.")
        return self._connection

    def _get_discovered_sources(self) -> list[DataSource]:
        if self._discovered is None:
            conn = self.get_connection()
            engine = get_sqlserver_engine(
                host=conn["host"],
                port=conn["port"],
                user=conn["user"],
                password=conn["password"],
                database="master",
            )
            discovery = DbDiscovery(
                engine=engine,
                host=conn["host"],
                port=conn["port"],
                user=conn["user"],
                password=conn["password"],
            )
            self._discovered = discovery.discover_databases()
        return self._discovered

    def get_all(self) -> list[DataSource]:
        return self._get_discovered_sources()

    def get_by_id(self, data_source_id: str) -> DataSource | None:
        for ds in self._get_discovered_sources():
            if ds.id == data_source_id:
                return ds
        return None

    def get_engine(self, data_source: DataSource) -> Engine:
        return get_sqlserver_engine(
            host=data_source.host,
            port=data_source.port,
            user=data_source.user,
            password=data_source.password,
            database=data_source.database_name,
        )
