from dataclasses import dataclass, field
from datetime import datetime

@dataclass(frozen=True, slots=True)
class DataSource:
    id: str
    name: str
    db_type: str
    host: str
    port: int
    database_name: str
    default_schema: str = "dbo"
    user: str = ""
    password: str = ""

@dataclass(frozen=True, slots=True)
class ColumnDetail:
    column_name: str
    data_type: str
    business_description: str
    contains_sensitive_data: bool
    suggested_tags: tuple[str, ...] = field(default_factory=tuple)

@dataclass(frozen=True, slots=True)
class CatalogEntry:
    data_source_id: str
    table_name: str
    summary: str
    domain: str
    host: str = ""
    columns: tuple[ColumnDetail, ...] = field(default_factory=tuple)
    synced_at: datetime | None = None