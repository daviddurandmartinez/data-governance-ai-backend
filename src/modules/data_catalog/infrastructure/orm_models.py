from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint, func

from src.shared.database.session import Base


class CatalogEntryORM(Base):
    __tablename__ = "catalog_entries"
    __table_args__ = (
        UniqueConstraint("data_source_id", "table_name", name="uq_ds_table"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    data_source_id = Column(String(100), nullable=False, index=True)
    table_name = Column(String(255), nullable=False, index=True)
    summary = Column(Text, nullable=False)
    domain = Column(String(100), nullable=False)
    columns_json = Column(Text, nullable=False)
    synced_at = Column(DateTime, nullable=False, server_default=func.now())
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
