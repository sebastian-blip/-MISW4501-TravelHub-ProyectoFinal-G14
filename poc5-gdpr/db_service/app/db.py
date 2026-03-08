"""
DuckDB connection and schema init for PoC-5.
Single file DB; one connection per process with lock for concurrent requests.
"""
import os
import threading
import duckdb
from .config import DATABASE_PATH

_conn: duckdb.DuckDBPyConnection | None = None
_lock = threading.Lock()


def get_connection() -> duckdb.DuckDBPyConnection:
    global _conn
    with _lock:
        if _conn is None:
            os.makedirs(os.path.dirname(DATABASE_PATH) or ".", exist_ok=True)
            _conn = duckdb.connect(DATABASE_PATH)
            _init_schema(_conn)
        return _conn


def _init_schema(conn: duckdb.DuckDBPyConnection) -> None:
    """Create tables and seed data (DuckDB-compatible SQL)."""
    # users
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          UUID PRIMARY KEY,
            email       VARCHAR NOT NULL,
            name        VARCHAR,
            anonymized  BOOLEAN DEFAULT FALSE,
            created_at  TIMESTAMP DEFAULT current_timestamp,
            updated_at  TIMESTAMP DEFAULT current_timestamp
        )
    """)
    # audit_events
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_events (
            id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            event_type   VARCHAR NOT NULL,
            user_id      UUID NOT NULL,
            consumer_id  VARCHAR,
            timestamp    TIMESTAMP DEFAULT current_timestamp,
            payload      JSON
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_events(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_events(event_type)")
    # user_read_model
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_read_model (
            id          UUID PRIMARY KEY,
            email       VARCHAR,
            name        VARCHAR,
            anonymized  BOOLEAN DEFAULT FALSE,
            updated_at  TIMESTAMP DEFAULT current_timestamp
        )
    """)
    # reservations
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id      UUID NOT NULL,
            hotel_id     UUID NOT NULL,
            room_id      UUID NOT NULL,
            check_in     DATE NOT NULL,
            check_out    DATE NOT NULL,
            total_price  DECIMAL(10, 2),
            status       VARCHAR DEFAULT 'confirmed',
            created_at   TIMESTAMP DEFAULT current_timestamp,
            updated_at   TIMESTAMP DEFAULT current_timestamp
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_reservations_user_id ON reservations(user_id)")
    # analytics_user_activity
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analytics_user_activity (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id     UUID NOT NULL,
            event_type  VARCHAR NOT NULL,
            payload     JSON,
            created_at  TIMESTAMP DEFAULT current_timestamp,
            anonymized  BOOLEAN DEFAULT FALSE
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_analytics_user_id ON analytics_user_activity(user_id)")

    # Seed: test user and read model
    test_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
    conn.execute(
        "INSERT INTO users (id, email, name, anonymized) VALUES (?, ?, ?, ?) ON CONFLICT (id) DO NOTHING",
        [test_id, "test@travelhub.com", "Test User", False],
    )
    conn.execute(
        "INSERT INTO user_read_model (id, email, name, anonymized) VALUES (?, ?, ?, ?) ON CONFLICT (id) DO NOTHING",
        [test_id, "test@travelhub.com", "Test User", False],
    )
    # Seed one reservation if empty
    cur = conn.execute("SELECT 1 FROM reservations LIMIT 1")
    if cur.fetchone() is None:
        conn.execute("""
            INSERT INTO reservations (user_id, hotel_id, room_id, check_in, check_out, total_price, status)
            VALUES (?, gen_random_uuid(), gen_random_uuid(), current_date, current_date + 2, 150.00, 'confirmed')
        """, [test_id])
    # Seed one analytics row if empty
    cur = conn.execute("SELECT 1 FROM analytics_user_activity LIMIT 1")
    if cur.fetchone() is None:
        conn.execute(
            "INSERT INTO analytics_user_activity (user_id, event_type, payload, anonymized) VALUES (?, ?, ?, ?)",
            [test_id, "page_view", '{"page": "home"}', False],
        )


def close_db() -> None:
    global _conn
    with _lock:
        if _conn:
            _conn.close()
            _conn = None
