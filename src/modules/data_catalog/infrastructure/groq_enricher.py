import json
from datetime import UTC, datetime
from groq import Groq
from pydantic import BaseModel, Field
from src.modules.data_catalog.domain.entities import CatalogEntry, ColumnDetail
from src.shared.exceptions import EnrichmentError

class TableCatalogOutput(BaseModel):
    table_name: str
    summary: str = Field(description="Resumen funcional de lo que representa esta tabla")
    domain: str = Field(description="Área funcional estimada (ej. 'Finanzas', 'RRHH', 'Operaciones')")
    columns: list[dict]

class GroqEnricher:
    def __init__(self, api_key: str) -> None:
        self._client = Groq(api_key=api_key)
        self._model = "openai/gpt-oss-20b"
        self._system_prompt = (
            "Eres un arquitecto de datos experto en gobierno de datos. "
            "Analizas la estructura técnica de tablas de bases de datos y generas catálogos.\n\n"
            "Debes responder SIEMPRE con un JSON válido con exactamente esta estructura:\n"
            "{\n"
            '  "table_name": "nombre_real_de_la_tabla",\n'
            '  "summary": "resumen funcional de qué sirve esta tabla",\n'
            '  "domain": "área de negocio (ej. Finanzas, RRHH, Operaciones, Ventas, Marketing)",\n'
            '  "columns": [\n'
            "    {\n"
            '      "column_name": "nombre_columna",\n'
            '      "data_type": "tipo_dato",\n'
            '      "business_description": "qué representa esta columna",\n'
            '      "contains_sensitive_data": false,\n'
            '      "suggested_tags": ["tag1", "tag2"]\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            "NO incluyas campos adicionales como data_source_id, solo los 4 campos indicados."
        )

    def enrich(self, raw_metadata: dict, data_source_id: str) -> CatalogEntry:
        try:
            user_prompt = (
                f"Analiza la siguiente estructura de tabla y genera su catálogo.\n"
                f"La tabla pertenece a la fuente de datos '{data_source_id}'.\n"
                f"Estructura técnica:\n{json.dumps(raw_metadata, ensure_ascii=False, indent=2)}"
            )
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": self._system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=2048,
                response_format={"type": "json_object"},
            )
            output = json.loads(response.choices[0].message.content)
            parsed = TableCatalogOutput(**output)

            columns = tuple(
                ColumnDetail(
                    column_name=col.get("column_name", ""),
                    data_type=col.get("data_type", ""),
                    business_description=col.get("business_description", ""),
                    contains_sensitive_data=col.get("contains_sensitive_data", False),
                    suggested_tags=tuple(col.get("suggested_tags", [])),
                )
                for col in parsed.columns
            )

            return CatalogEntry(
                data_source_id=data_source_id,
                table_name=parsed.table_name,
                summary=parsed.summary,
                domain=parsed.domain,
                columns=columns,
                synced_at=datetime.now(UTC),
            )
        except EnrichmentError:
            raise
        except Exception as e:
            raise EnrichmentError(f"Groq enrichment failed: {e}") from e
