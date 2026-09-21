import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.data_catalog.domain.entities import CatalogEntry, ColumnDetail
from src.modules.data_catalog.infrastructure.orm_models import CatalogEntryORM


class CatalogRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert(self, entry: CatalogEntry) -> None:
        stmt = select(CatalogEntryORM).where(
            CatalogEntryORM.data_source_id == entry.data_source_id,
            CatalogEntryORM.table_name == entry.table_name,
        )
        result = self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        columns_json = json.dumps(
            [
                {
                    "column_name": col.column_name,
                    "data_type": col.data_type,
                    "business_description": col.business_description,
                    "contains_sensitive_data": col.contains_sensitive_data,
                    "suggested_tags": list(col.suggested_tags),
                }
                for col in entry.columns
            ],
            ensure_ascii=False,
        )

        synced_at = entry.synced_at or datetime.now()

        if existing:
            existing.summary = entry.summary
            existing.domain = entry.domain
            existing.host = entry.host
            existing.columns_json = columns_json
            existing.synced_at = synced_at
        else:
            orm_entry = CatalogEntryORM(
                data_source_id=entry.data_source_id,
                table_name=entry.table_name,
                summary=entry.summary,
                domain=entry.domain,
                host=entry.host,
                columns_json=columns_json,
                synced_at=synced_at,
            )
            self._session.add(orm_entry)

        self._session.commit()

    def get_all(self, data_source_id: str | None = None) -> list[CatalogEntry]:
        stmt = select(CatalogEntryORM)
        if data_source_id:
            stmt = stmt.where(CatalogEntryORM.data_source_id == data_source_id)
        result = self._session.execute(stmt)
        orm_entries = result.scalars().all()
        return [self._to_entity(entry) for entry in orm_entries]

    def get_by_table(self, data_source_id: str, table_name: str) -> CatalogEntry | None:
        stmt = select(CatalogEntryORM).where(
            CatalogEntryORM.data_source_id == data_source_id,
            CatalogEntryORM.table_name == table_name,
        )
        result = self._session.execute(stmt)
        orm_entry = result.scalar_one_or_none()
        if orm_entry is None:
            return None
        return self._to_entity(orm_entry)

    def get_data_sources(self) -> list[str]:
        stmt = select(CatalogEntryORM.data_source_id).distinct()
        result = self._session.execute(stmt)
        return [row[0] for row in result.all()]

    def _to_entity(self, orm: CatalogEntryORM) -> CatalogEntry:
        columns_data = json.loads(orm.columns_json)
        return CatalogEntry(
            data_source_id=orm.data_source_id,
            table_name=orm.table_name,
            summary=orm.summary,
            domain=orm.domain,
            host=orm.host,
            columns=tuple(ColumnDetail(**col) for col in columns_data),
            synced_at=orm.synced_at,
        )
