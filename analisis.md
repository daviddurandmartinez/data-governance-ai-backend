# Análisis del Proyecto: Data Governance AI Backend

## 1. Propósito Principal

### ¿Qué problema resuelve?

Este proyecto es un **Catálogo Automatizado de Gobiernos de Datos**. Resuelve un problema muy común en empresas: nadie sabe qué hay dentro de las bases de datos.

Imagina que una empresa tiene 10, 20 o más bases de datos en un servidor SQL Server. Los datos están ahí, pero nadie sabe:
- Qué tablas existen
- Qué significa cada tabla (¿es de finanzas? ¿de RH? ¿de ventas?)
- Qué columnas tienen datos sensibles (nombres, correos, contraseñas)
- Cuántos registros tiene cada tabla

### ¿Qué hace en la práctica?

1. **Descubre automáticamente** todas las bases de datos del servidor SQL Server
2. **Extrae la estructura técnica** de cada tabla (columnas, tipos de datos, llaves primarias, llaves foráneas)
3. **Envía esa información a una IA** (Groq API con el modelo GPT-OSS-20B) que genera:
   - Un resumen funcional de qué sirve la tabla
   - A qué área de negocio pertenece (Finanzas, RRHH, Ventas, etc.)
   - Descripción de cada columna en lenguaje de negocio
   - Detección de datos sensibles
   - Tags sugeridos
4. **Guarda todo en un catálogo interno** que la empresa puede consultar

En resumen: **transforma información técnica cruda de bases de datos en un catálogo de negocio comprensible, usando inteligencia artificial**.

---

## 2. Mapa de la Estructura

El proyecto sigue **Arquitectura Limpia (Clean Architecture)** con el patrón **Puertos y Adaptadores (Hexagonal)**. Cada capa tiene una responsabilidad clara:

```
src/
├── main.py                    ← Punto de entrada: crea la app FastAPI
├── settings.py                ← Configuración centralizada (variables de entorno)
│
├── shared/                    ← UTILIDADES COMPARTIDAS (no son de un módulo específico)
│   ├── exceptions.py          ← Jerarquía de errores del dominio
│   ├── health.py              ← Endpoints de salud (/health/live, /health/ready)
│   ├── constants.py           ← Constantes (ruta del proyecto)
│   └── database/
│       ├── session.py         ← Conexión a la BD del catálogo + creación de tablas
│       └── sqlserver_engine.py← Factory de motores de BD (con cache LRU)
│
└── modules/
    └── data_catalog/          ← MÓDULO PRINCIPAL
        ├── domain/            ← REGLAS DE NEGOCIO (puro, sin dependencias)
        │   ├── entities.py    ← Modelos: DataSource, CatalogEntry, ColumnDetail
        │   └── ports.py       ← Contratos: IExtractor, IEnricher, ICatalogRepository
        │
        ├── application/       ← LÓGICA DE NEGOCIO (orquestación)
        │   └── use_cases.py   ← SyncCatalogUseCase, ListTablesUseCase, SyncAllDataSourcesUseCase
        │
        ├── presentation/      ← ENTRADAS HTTP (API REST)
        │   ├── router.py      ← Endpoints: /datasources, /sync, /sync-all
        │   └── schemas.py     ← Modelos Pydantic para request/response
        │
        └── infrastructure/    ← IMPLEMENTACIONES CONCRETAS
            ├── sql_server_extractor.py  ← Extrae metadatos de SQL Server
            ├── groq_enricher.py         ← Llama a la API de Groq (IA)
            ├── catalog_repository.py    ← Guarda en la BD del catálogo
            ├── datasource_repository.py ← Descubre bases de datos automáticamente
            ├── db_discovery.py          ← Consulta sys.databases
            ├── orm_models.py            ← Modelo ORM de la tabla catalog_entries
            └── dependencies.py          ← Inyección de dependencias (ensambla todo)
```

### ¿Qué hace cada capa en lenguaje sencillo?

| Capa | ¿Qué es? | Ejemplo |
|------|----------|---------|
| **Domain** | Las reglas del negocio. No sabe de bases de datos ni de APIs. Solo define QUÉ es un DataSource, QUÉ es un CatalogEntry. | `DataSource(host="172.16.120.15", database_name="ventas")` |
| **Application** | El "director de orquesta". Dice QUÉ pasos seguir: extraer → enriquecer → guardar. No sabe CÓMO se hacen. | `SyncCatalogUseCase.execute("db_gestion_datos")` |
| **Presentation** | Las puertas de entrada. Recibe peticiones HTTP y las traduce a llamadas al application layer. | `POST /api/v1/datasources/db_gestion_datos/sync` |
| **Infrastructure** | Las herramientas concretas. Sabe CÓMO conectar a SQL Server, CÓMO llamar a Groq, CÓMO guardar en la BD. | `SqlServerExtractor`, `GroqEnricher` |

---

## 3. Flujo de Ejecución (End-to-End)

Vamos a seguir una petición de principio a fin: **`POST /api/v1/datasources/db_gestion_datos/sync`**

```
┌─────────────────────────────────────────────────────────────────────┐
│  PASO 1: LLEGADA HTTP                                              │
│  POST /api/v1/datasources/db_gestion_datos/sync                    │
│                                                                     │
│  FastAPI recibe la petición y resuelve las dependencias:            │
│  - session = Depends(get_session) → crea conexión a catálogo DB     │
│  - data_source_id = "db_gestion_datos" (del path URL)              │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PASO 2: ROUTER → USE CASE                                         │
│  router.py llama a get_sync_use_case(session)                      │
│                                                                     │
│  dependencies.py "ensambla" el SyncCatalogUseCase con:             │
│  - extractor_factory (crea SqlServerExtractor cuando se necesite)  │
│  - enricher (GroqEnricher, singleton con la API key)               │
│  - catalog_repository (CatalogRepository con la sesión de BD)      │
│  - ds_repository (DataSourceRepository, singleton)                 │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PASO 3: DESCUBRIMIENTO DE LA BASE DE DATOS                        │
│  DataSourceRepository.get_by_id("db_gestion_datos")                │
│                                                                     │
│  Primera vez:                                                       │
│  → Conecta a master en 172.16.120.15                                │
│  → Ejecuta: SELECT name FROM sys.databases WHERE name NOT IN       │
│    ('master','tempdb','model','msdb','data_governance_catalog')     │
│  → Crea una entidad DataSource por cada BD encontrada              │
│  → Guarda en caché (no vuelve a preguntar)                         │
│                                                                     │
│  Encuentra: DataSource(id="db_gestion_datos", host="172.16.120.15")│
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PASO 4: LISTAR TABLAS                                             │
│  SqlServerExtractor.list_tables()                                  │
│                                                                     │
│  → Conecta a db_gestion_datos en 172.16.120.15                     │
│  → Usa SQLAlchemy Inspector:                                       │
│    inspector.get_table_names(schema="dbo")                         │
│  → Retorna: ["dbo.retiro_temporal", "dbo.empleados", ...]         │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PASO 5: EXTRAER METADATOS (por cada tabla)                        │
│  SqlServerExtractor.extract("dbo.retiro_temporal")                 │
│                                                                     │
│  → Conecta a db_gestion_datos                                      │
│  → Inspector extrae:                                               │
│    • Columnas (nombre, tipo, nullable)                             │
│    • Llave primaria                                                │
│    • Llaves foráneas                                               │
│  → Consultas directas:                                             │
│    • SELECT TOP 5 * FROM [dbo].[retiro_temporal]  (muestra)       │
│    • SELECT COUNT(*) FROM [dbo].[retiro_temporal] (conteo)        │
│  → Retorna diccionario con metadatos crudos                       │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PASO 6: ENRIQUECIMIENTO CON IA                                    │
│  GroqEnricher.enrich(raw_metadata, "db_gestion_datos")            │
│                                                                     │
│  → Envía a Groq API (openai/gpt-oss-20b):                         │
│    Sistema: "Eres un arquitecto de datos experto..."               │
│    Usuario: "Analiza esta estructura y genera su catálogo..."      │
│    Datos: JSON con columnas, tipos, PKs, muestra, conteo          │
│  → IA retorna JSON con:                                           │
│    • summary: "Tabla de retiros temporales de empleados..."       │
│    • domain: "RRHH"                                                │
│    • columns: descripción de cada columna, si es sensible, tags   │
│  → Se mapea a CatalogEntry (entidad del dominio)                  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PASO 7: PERSISTIR EN EL CATÁLOGO                                  │
│  CatalogRepository.upsert(catalog_entry)                           │
│                                                                     │
│  → Conecta a data_governance_catalog (catálogo interno)            │
│  → Busca: SELECT * FROM catalog_entries WHERE                      │
│    data_source_id='db_gestion_datos' AND table_name='dbo.retiro..' │
│  → Si existe: ACTUALIZA (summary, domain, columns_json, synced_at)│
│  → Si no existe: INSERTA nueva fila                                │
│  → COMMIT                                                          │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PASO 8: RESPUESTA HTTP                                            │
│  Router retorna BatchSyncOutput como JSON                          │
│                                                                     │
│  {                                                                 │
│    "data_source_id": "db_gestion_datos",                           │
│    "results": [                                                    │
│      {                                                             │
│        "table_name": "dbo.retiro_temporal",                        │
│        "summary": "Tabla de retiros temporales...",                │
│        "domain": "RRHH",                                           │
│        "columns_count": 8,                                         │
│        "synced_at": "2026-09-15T22:32:42",                        │
│        "error": null                                               │
│      }                                                             │
│    ],                                                              │
│    "total_synced": 15,                                             │
│    "total_errors": 0                                               │
│  }                                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

### Diagrama simplificado del pipeline

```
  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
  │ DESCUBRE │───▶│  EXTRAE  │───▶│ENRIQUECE │───▶│ GUARDA   │
  │   BDs    │    │METADATOS │    │  CON IA  │    │CATÁLOGO  │
  └──────────┘    └──────────┘    └──────────┘    └──────────┘
   sys.databases   SQLAlchemy     Groq API        SQLAlchemy
   (master)        Inspector      (GPT-OSS-20B)   ORM (upsert)
```

---

## 4. Guion para la Presentación (5 Puntos Clave)

### Punto 1: ¿Qué es?
> "Este es un backend de gobierno de datos que automatiza la creación de catálogos de bases de datos. Conecta a nuestro servidor SQL Server, descubre todas las bases de datos existentes, extrae la estructura técnica de cada tabla y utiliza inteligencia artificial para generar descripciones de negocio, clasificar por dominio funcional y detectar datos sensibles."

### Punto 2: Arquitectura
> "Está construido con FastAPI siguiendo Arquitectura Limpia en 4 capas: Dominio (entidades puras como DataSource y CatalogEntry), Aplicación (casos de uso como SyncCatalogUseCase), Presentación (endpoints REST) e Infraestructura (implementaciones concretas contra SQL Server y Groq API). Esto permite cambiar cualquier componente sin afectar al resto."

### Punto 3: Pipeline de sincronización
> "El proceso de sincronización tiene 4 pasos automáticos: (1) Descubrimiento de bases de datos via sys.databases, (2) Extracción de metadatos técnicos (columnas, tipos, PKs, FKs, muestras, conteos), (3) Enriquecimiento con IA que genera resumen funcional, dominio de negocio, descripción de columnas y detección de datos sensibles, y (4) Persistencia en un catálogo interno con upsert para mantener datos actualizados."

### Punto 4: Endpoints disponibles
> "La API expone 5 endpoints REST: GET /datasources para listar bases de datos descubiertas, GET /datasources/{id}/tables para listar tablas de una base específica, POST /datasources/{id}/sync para sincronizar todas las tablas de una base, POST /datasources/sync-all para sincronizar todo el servidor, y endpoints de salud para monitoreo."

### Punto 5: Valor de negocio
> "Este proyecto elimina el problema de 'no sé qué hay en mis bases de datos'. En lugar de que un analista revise manualmente cada tabla, el sistema lo hace automáticamente y genera un catálogo comprensible para el negocio. Detecta datos sensibles para cumplimiento de regulaciones, clasifica por dominio para facilitar la búsqueda, y se actualiza con cada sincronización. El catálogo resultante es la base para gobierno de datos, auditorías y toma de decisiones basada en datos."

---

## 5. Endpoints de la API

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/v1/health` | Verificar estado del servicio |
| `GET` | `/api/v1/datasources` | Listar todas las bases de datos descubiertas |
| `GET` | `/api/v1/datasources/{id}/tables` | Listar tablas de una base de datos específica |
| `POST` | `/api/v1/datasources/{id}/sync` | Sincronizar metadatos de TODAS las tablas de un data source |
| `POST` | `/api/v1/datasources/sync-all` | Sincronizar metadatos de TODOS los data sources |

---

## 6. Modelo de Dominio

### Entidades (puras, sin dependencias de framework)

| Entidad | Campos | Descripción |
|---------|--------|-------------|
| **DataSource** | id, name, db_type, host, port, database_name, default_schema, user, password | Representa una base de datos descubierta |
| **ColumnDetail** | column_name, data_type, business_description, contains_sensitive_data, suggested_tags | Detalle de una columna enriquecido por IA |
| **CatalogEntry** | data_source_id, table_name, summary, domain, columns, synced_at | Entrada completa del catálogo para una tabla |

### Interfaces (Puertos)

| Interfaz | Métodos | Implementación |
|----------|---------|----------------|
| **IExtractor** | extract(), list_tables() | SqlServerExtractor |
| **IEnricher** | enrich() | GroqEnricher |
| **ICatalogRepository** | upsert(), get_all(), get_by_table(), get_data_sources() | CatalogRepository |
| **IDataSourceRepository** | get_all(), get_by_id() | DataSourceRepository |

---

## 7. Dependencias Externas

| Servicio | Propósito | Conexión |
|----------|-----------|----------|
| **SQL Server** (datos fuente) | Extraer metadatos de tablas | 172.16.120.15:1433, ODBC Driver 18 |
| **SQL Server** (catálogo) | Almacenar catálogo enriquecido | 172.16.120.15:1433, DB: data_governance_catalog |
| **Groq API** (IA) | Enriquecer metadatos con descripciones de negocio | api.groq.com, modelo: openai/gpt-oss-20b |
