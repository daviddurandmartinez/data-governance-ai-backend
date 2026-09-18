from functools import lru_cache

from sqlalchemy.orm import Session

from src.modules.data_catalog.application.use_cases import (
    ListTablesUseCase,
    SyncAllDataSourcesUseCase,
    SyncCatalogUseCase,
)
from src.modules.data_catalog.domain.entities import DataSource
from src.modules.data_catalog.infrastructure.catalog_repository import CatalogRepository
from src.modules.data_catalog.infrastructure.datasource_repository import DataSourceRepository
from src.modules.data_catalog.infrastructure.groq_enricher import GroqEnricher
from src.modules.data_catalog.infrastructure.sql_server_extractor import SqlServerExtractor
from src.settings import settings


@lru_cache(maxsize=1)
def get_ds_repository() -> DataSourceRepository:
    return DataSourceRepository(settings)


@lru_cache(maxsize=1)
def get_enricher() -> GroqEnricher:
    return GroqEnricher(settings.GROQ_API_KEY)


def get_extractor_factory(data_source: DataSource) -> SqlServerExtractor:
    ds_repo = get_ds_repository()
    engine = ds_repo.get_engine(data_source)
    return SqlServerExtractor(data_source, engine)


def get_catalog_repository(session: Session) -> CatalogRepository:
    return CatalogRepository(session)


def get_sync_use_case(session: Session) -> SyncCatalogUseCase:
    return SyncCatalogUseCase(
        extractor_factory=get_extractor_factory,
        enricher=get_enricher(),
        catalog_repository=get_catalog_repository(session),
        ds_repository=get_ds_repository(),
    )


def get_list_tables_use_case() -> ListTablesUseCase:
    return ListTablesUseCase(
        extractor_factory=get_extractor_factory,
        ds_repository=get_ds_repository(),
    )


def get_sync_all_use_case(session: Session) -> SyncAllDataSourcesUseCase:
    return SyncAllDataSourcesUseCase(
        sync_use_case=get_sync_use_case(session),
        ds_repository=get_ds_repository(),
    )
