from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.modules.data_catalog.infrastructure.dependencies import (
    get_ds_repository,
    get_list_tables_use_case,
    get_sync_all_use_case,
    get_sync_use_case,
)
from src.modules.data_catalog.presentation.schemas import (
    BatchSyncOutput,
    DataSourceResponse,
    SyncAllOutput,
    TableListResponse,
)
from src.shared.database.session import get_session

router = APIRouter(prefix="/api/v1", tags=["catalog"])


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.get("/datasources", response_model=list[DataSourceResponse])
def list_data_sources(ds_repo=Depends(get_ds_repository)):
    sources = ds_repo.get_all()
    return [
        DataSourceResponse(
            id=ds.id,
            name=ds.name,
            db_type=ds.db_type,
            host=ds.host,
            port=ds.port,
            database_name=ds.database_name,
        )
        for ds in sources
    ]


@router.get("/datasources/{data_source_id}/tables", response_model=TableListResponse)
def list_tables(data_source_id: str, use_case=Depends(get_list_tables_use_case)):
    tables = use_case.execute(data_source_id)
    return TableListResponse(data_source_id=data_source_id, tables=tables)


@router.post("/datasources/{data_source_id}/sync", response_model=BatchSyncOutput)
def sync(data_source_id: str, session: Session = Depends(get_session)):
    use_case = get_sync_use_case(session)
    result = use_case.execute(data_source_id)
    return BatchSyncOutput(**result)


@router.post("/datasources/sync-all", response_model=SyncAllOutput)
def sync_all(session: Session = Depends(get_session)):
    use_case = get_sync_all_use_case(session)
    result = use_case.execute()
    return SyncAllOutput(**result)
