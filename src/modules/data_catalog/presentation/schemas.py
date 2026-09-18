from pydantic import BaseModel


class DataSourceResponse(BaseModel):
    id: str
    name: str
    db_type: str
    host: str
    port: int
    database_name: str


class TableListResponse(BaseModel):
    data_source_id: str
    tables: list[str]


class SyncOutput(BaseModel):
    data_source_id: str
    table_name: str
    summary: str
    domain: str
    columns_count: int
    synced_at: str | None = None
    error: str | None = None


class BatchSyncOutput(BaseModel):
    data_source_id: str
    results: list[SyncOutput]
    total_synced: int
    total_errors: int
    error: str | None = None


class SyncAllOutput(BaseModel):
    results: list[BatchSyncOutput]
    total_data_sources: int
    total_synced: int
    total_errors: int
