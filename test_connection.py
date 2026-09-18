import pyodbc
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

print(f"pyodbc version: {pyodbc.version}")
print(f"SQLAlchemy version: {sqlalchemy.__version__}")
print(f"ODBC drivers: {pyodbc.drivers()}")
print()

# Test 1: pyodbc directo
print("=== Test 1: pyodbc directo ===")
try:
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=172.16.120.15,1433;"
        "UID=sa;PWD=samcorp$123;"
        "Encrypt=no;TrustServerCertificate=yes;timeout=30"
    )
    print("Conexion pyodbc directa: OK")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sys.databases")
    for row in cursor.fetchall():
        print(f"  DB: {row[0]}")
    conn.close()
except Exception as e:
    print(f"Error pyodbc: {type(e).__name__}: {e}")

print()

# Test 2: SQLAlchemy con connect_args
print("=== Test 2: SQLAlchemy con connect_args ===")
try:
    uri = URL.create(
        "mssql+pyodbc",
        username="sa",
        password="samcorp$123",
        host="172.16.120.15",
        port=1433,
        database="master",
        query={
            "driver": "ODBC Driver 18 for SQL Server",
            "MARS_Connection": "yes",
            "Encrypt": "no",
            "TrustServerCertificate": "yes",
            "Trusted_Connection": "no",
        },
    )
    engine = create_engine(uri, echo=False, connect_args={"timeout": 30})
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1 AS test"))
        row = result.fetchone()
        print(f"SQLAlchemy connect_args: OK (result={row[0]})")
    engine.dispose()
except Exception as e:
    print(f"Error SQLAlchemy: {type(e).__name__}: {e}")

print()

# Test 3: SQLAlchemy con timeout en query string
print("=== Test 3: SQLAlchemy con timeout en query string ===")
try:
    uri2 = URL.create(
        "mssql+pyodbc",
        username="sa",
        password="samcorp$123",
        host="172.16.120.15",
        port=1433,
        database="master",
        query={
            "driver": "ODBC Driver 18 for SQL Server",
            "MARS_Connection": "yes",
            "Encrypt": "no",
            "TrustServerCertificate": "yes",
            "Trusted_Connection": "no",
            "timeout": "30",
        },
    )
    engine2 = create_engine(uri2, echo=False)
    with engine2.connect() as conn:
        result = conn.execute(text("SELECT 1 AS test"))
        row = result.fetchone()
        print(f"SQLAlchemy query timeout: OK (result={row[0]})")
    engine2.dispose()
except Exception as e:
    print(f"Error SQLAlchemy query: {type(e).__name__}: {e}")

print()

# Test 4: Conectar a db_gestion_datos
print("=== Test 4: Conectar a db_gestion_datos ===")
try:
    uri3 = URL.create(
        "mssql+pyodbc",
        username="sa",
        password="samcorp$123",
        host="172.16.120.15",
        port=1433,
        database="db_gestion_datos",
        query={
            "driver": "ODBC Driver 18 for SQL Server",
            "MARS_Connection": "yes",
            "Encrypt": "no",
            "TrustServerCertificate": "yes",
            "Trusted_Connection": "no",
        },
    )
    engine3 = create_engine(uri3, echo=False, connect_args={"timeout": 30})
    with engine3.connect() as conn:
        inspector_result = conn.execute(text("SELECT TOP 1 * FROM dbo.retiro_temporal"))
        print(f"db_gestion_datos: OK ({inspector_result.rowcount} rows)")
    engine3.dispose()
except Exception as e:
    print(f"Error db_gestion_datos: {type(e).__name__}: {e}")

print()

# Test 5: Conectar a ludoplay
print("=== Test 5: Conectar a ludoplay ===")
try:
    uri4 = URL.create(
        "mssql+pyodbc",
        username="sa",
        password="samcorp$123",
        host="172.16.120.15",
        port=1433,
        database="ludoplay",
        query={
            "driver": "ODBC Driver 18 for SQL Server",
            "MARS_Connection": "yes",
            "Encrypt": "no",
            "TrustServerCertificate": "yes",
            "Trusted_Connection": "no",
        },
    )
    engine4 = create_engine(uri4, echo=False, connect_args={"timeout": 30})
    with engine4.connect() as conn:
        inspector_result = conn.execute(text("SELECT TOP 1 * FROM dbo.players_player"))
        print(f"ludoplay: OK ({inspector_result.rowcount} rows)")
    engine4.dispose()
except Exception as e:
    print(f"Error ludoplay: {type(e).__name__}: {e}")
