import re
import logging

from sqlalchemy import Engine, inspect, text
from sqlalchemy.engine import Connection

from src.modules.data_catalog.domain.entities import DataSource
from src.shared.exceptions import ExtractionError

logger = logging.getLogger(__name__)

_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9_\.]+$")
_SYSTEM_SCHEMAS = frozenset({"sys", "information_schema", "guest"})


def _validate_identifier(name: str) -> str:
    if not _SAFE_IDENTIFIER.match(name):
        raise ExtractionError(f"Invalid identifier: {name!r}")
    return name


class SqlServerExtractor:
    def __init__(self, data_source: DataSource, engine: Engine) -> None:
        self._data_source = data_source
        self._engine = engine

    def extract(self, table_name: str) -> dict:
        try:
            return self._extract_sync(table_name)
        except ExtractionError:
            raise
        except Exception as e:
            raise ExtractionError(f"Error extracting metadata from {table_name}: {e}") from e

    def list_tables(self) -> list[str]:
        try:
            return self._list_tables_sync()
        except Exception as e:
            raise ExtractionError(f"Error listing tables: {e}") from e

    def _list_tables_sync(self) -> list[str]:
        with self._engine.connect() as conn:
            inspector = inspect(conn)
            all_schemas = inspector.get_schema_names()
            user_schemas = [s for s in all_schemas if s.lower() not in _SYSTEM_SCHEMAS]
            tables: list[str] = []
            for schema in user_schemas:
                for t in inspector.get_table_names(schema=schema):
                    tables.append(f"{schema}.{t}")
            return sorted(tables)

    def _extract_sync(self, table_name: str) -> dict:
        with self._engine.connect() as conn:
            inspector = inspect(conn)

            schema, table = self._parse_table_name(table_name)

            columns = inspector.get_columns(table, schema=schema)
            pk_constraint = inspector.get_pk_constraint(table, schema=schema)
            fk_constraints = inspector.get_foreign_keys(table, schema=schema)

            pk_columns = pk_constraint.get("constrained_columns", []) if pk_constraint else []

            sample_data = self._get_sample_data(conn, table, schema)

            return {
                "data_source_id": self._data_source.id,
                "table_name": table_name,
                "schema": schema,
                "columns": [
                    {
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col.get("nullable", True),
                        "is_primary_key": col["name"] in pk_columns,
                        "default": str(col.get("default", "")),
                    }
                    for col in columns
                ],
                "primary_key": pk_columns,
                "foreign_keys": [
                    {
                        "constrained_columns": fk["constrained_columns"],
                        "referred_table": fk["referred_table"],
                        "referred_columns": fk["referred_columns"],
                    }
                    for fk in fk_constraints
                ],
                "sample_data": sample_data,
                "row_count": self._get_row_count(conn, table, schema),
            }

    def _parse_table_name(self, table_name: str) -> tuple[str, str]:
        if "." in table_name:
            parts = table_name.split(".", 1)
            return parts[0], parts[1]
        return self._data_source.default_schema, table_name

    def _get_sample_data(self, conn: Connection, table_name: str, schema: str, limit: int = 5) -> list[dict]:
        try:
            safe_schema = _validate_identifier(schema)
            safe_table = _validate_identifier(table_name)
            query = text(f"SELECT TOP :limit * FROM [{safe_schema}].[{safe_table}]")
            result = conn.execute(query, {"limit": limit})
            return [dict(row._mapping) for row in result]
        except Exception:
            return []

    def _get_row_count(self, conn: Connection, table_name: str, schema: str) -> int:
        try:
            safe_schema = _validate_identifier(schema)
            safe_table = _validate_identifier(table_name)
            query = text(f"SELECT COUNT(*) as cnt FROM [{safe_schema}].[{safe_table}]")
            result = conn.execute(query)
            return result.scalar() or 0
        except Exception:
            return 0
