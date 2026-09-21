from collections.abc import Callable

from src.modules.data_catalog.domain.entities import DataSource
from src.modules.data_catalog.domain.ports import (
    ICatalogRepository,
    IDataSourceRepository,
    IEnricher,
    IExtractor,
)
from src.shared.exceptions import DataSourceNotFoundError


class SyncCatalogUseCase:
    def __init__(
        self,
        extractor_factory: Callable[[DataSource], IExtractor],
        enricher: IEnricher,
        catalog_repository: ICatalogRepository,
        ds_repository: IDataSourceRepository,
    ) -> None:
        self._extractor_factory = extractor_factory
        self._enricher = enricher
        self._catalog_repository = catalog_repository
        self._ds_repository = ds_repository

    def execute(self, data_source_id: str) -> dict:
        return self.execute_batch(data_source_id)

    def execute_single(self, data_source_id: str, table_name: str) -> dict:
        ds = self._ds_repository.get_by_id(data_source_id)
        if ds is None:
            raise DataSourceNotFoundError(data_source_id)

        extractor = self._extractor_factory(ds)
        raw_metadata = extractor.extract(table_name)
        catalog_entry = self._enricher.enrich(raw_metadata, data_source_id, ds.host)
        self._catalog_repository.upsert(catalog_entry)

        return {
            "data_source_id": catalog_entry.data_source_id,
            "table_name": catalog_entry.table_name,
            "summary": catalog_entry.summary,
            "domain": catalog_entry.domain,
            "host": catalog_entry.host,
            "columns_count": len(catalog_entry.columns),
            "synced_at": catalog_entry.synced_at.isoformat() if catalog_entry.synced_at else None,
            "error": None,
        }

    def execute_batch(
        self, data_source_id: str, table_names: list[str] | None = None
    ) -> dict:
        ds = self._ds_repository.get_by_id(data_source_id)
        if ds is None:
            raise DataSourceNotFoundError(data_source_id)

        extractor = self._extractor_factory(ds)

        try:
            if table_names is None:
                table_names = extractor.list_tables()
        except Exception as e:
            return {
                "data_source_id": data_source_id,
                "results": [],
                "total_synced": 0,
                "total_errors": 1,
                "error": f"Error listing tables: {e}",
            }

        results: list[dict] = []
        errors = 0
        for table in table_names:
            try:
                raw_metadata = extractor.extract(table)
                catalog_entry = self._enricher.enrich(raw_metadata, data_source_id, ds.host)
            except Exception as e:
                errors += 1
                results.append({
                    "data_source_id": data_source_id,
                    "table_name": table,
                    "summary": "",
                    "domain": "",
                    "columns_count": 0,
                    "synced_at": None,
                    "error": str(e),
                })
                continue

            try:
                self._catalog_repository.upsert(catalog_entry)
                persisted = True
            except Exception:
                persisted = False

            results.append({
                "data_source_id": catalog_entry.data_source_id,
                "table_name": catalog_entry.table_name,
                "summary": catalog_entry.summary,
                "domain": catalog_entry.domain,
                "host": catalog_entry.host,
                "columns_count": len(catalog_entry.columns),
                "synced_at": catalog_entry.synced_at.isoformat() if catalog_entry.synced_at else None,
                "error": None if persisted else "Extracted but not persisted to catalog",
            })

        return {
            "data_source_id": data_source_id,
            "results": results,
            "total_synced": len(results) - errors,
            "total_errors": errors,
            "error": None,
        }


class ListTablesUseCase:
    def __init__(
        self,
        extractor_factory: Callable[[DataSource], IExtractor],
        ds_repository: IDataSourceRepository,
    ) -> None:
        self._extractor_factory = extractor_factory
        self._ds_repository = ds_repository

    def execute(self, data_source_id: str) -> list[str]:
        ds = self._ds_repository.get_by_id(data_source_id)
        if ds is None:
            raise DataSourceNotFoundError(data_source_id)
        extractor = self._extractor_factory(ds)
        return extractor.list_tables()


class SyncAllDataSourcesUseCase:
    def __init__(
        self,
        sync_use_case: SyncCatalogUseCase,
        ds_repository: IDataSourceRepository,
    ) -> None:
        self._sync_use_case = sync_use_case
        self._ds_repository = ds_repository

    def execute(self) -> dict:
        data_sources = self._ds_repository.get_all()
        results: list[dict] = []
        total_synced = 0
        total_errors = 0

        for ds in data_sources:
            result = self._sync_use_case.execute(ds.id)
            results.append(result)
            total_synced += result.get("total_synced", 0)
            total_errors += result.get("total_errors", 0)

        return {
            "results": results,
            "total_data_sources": len(data_sources),
            "total_synced": total_synced,
            "total_errors": total_errors,
        }
