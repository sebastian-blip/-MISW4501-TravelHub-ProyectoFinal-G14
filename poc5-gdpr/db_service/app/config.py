import os

# Path to DuckDB file (volume in Docker)
DATABASE_PATH = os.getenv("DATABASE_PATH", "/data/poc5_gdpr.duckdb")
