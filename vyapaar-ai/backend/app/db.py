"""M1: SQLite storage layer and Store class.

Doc 02 section 2:
- Tables: products, sales, inventory, purchases, expenses, customers, khata_payments
- Store class with .table(name) -> DataFrame, .sales_enriched (cached),
  .as_of, and .data_version (increments on every load/upload).
"""
import contextlib
from pathlib import Path
import sqlite3
from typing import Iterator

import pandas as pd

from app.config import settings

# Column order per table = the CSV headers (doc 02 section 2).
SCHEMA: dict[str, str] = {
    "products": (
        "sku TEXT PRIMARY KEY, name TEXT, category TEXT, mrp REAL, cost_price REAL, "
        "gst_rate REAL, supplier TEXT, lead_time_days INTEGER, reorder_level INTEGER"
    ),
    "sales": (
        "invoice_id TEXT, date TEXT, time TEXT, sku TEXT, qty REAL, unit_price REAL, "
        "payment_mode TEXT, customer_id TEXT"
    ),
    "inventory": "sku TEXT PRIMARY KEY, current_stock REAL, last_restocked TEXT",
    "purchases": (
        "purchase_id TEXT, date TEXT, sku TEXT, qty REAL, unit_cost REAL, supplier TEXT"
    ),
    "expenses": "date TEXT, category TEXT, amount REAL, payment_mode TEXT, note TEXT",
    "customers": (
        "customer_id TEXT PRIMARY KEY, name TEXT, phone TEXT, khata_balance REAL, "
        "last_payment_date TEXT, credit_limit REAL"
    ),
    "khata_payments": "date TEXT, customer_id TEXT, amount REAL, mode TEXT",
}


def get_conn(db_path: Path | None = None) -> sqlite3.Connection:
    """Open a connection with the schema created (idempotent)."""
    path = db_path or settings.db_path
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    for table, ddl in SCHEMA.items():
        conn.execute(f"CREATE TABLE IF NOT EXISTS {table} ({ddl})")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)"
    )
    conn.commit()


def replace_table(conn: sqlite3.Connection, table: str, df: pd.DataFrame) -> None:
    """Replace all rows of `table` with `df` (columns must be canonical)."""
    cols = []
    for part in SCHEMA[table].split(","):
        part = part.strip()
        if part.endswith("PRIMARY KEY"):
            part = part[: -len("PRIMARY KEY")].strip()
        cols.append(part.split()[0])
    df = df[[c for c in cols if c in df.columns]]
    conn.execute(f"DELETE FROM {table}")
    df.to_sql(table, conn, if_exists="append", index=False)
    conn.commit()


def clear_all(conn: sqlite3.Connection) -> None:
    for table in SCHEMA:
        conn.execute(f"DELETE FROM {table}")
    conn.execute("DROP TABLE IF EXISTS sales_enriched")
    conn.commit()


def get_table(conn: sqlite3.Connection, table: str) -> pd.DataFrame:
    """Read an entire table into a pandas DataFrame."""
    return pd.read_sql_query(f"SELECT * FROM {table}", conn)


def get_sales_enriched(conn: sqlite3.Connection) -> pd.DataFrame:
    """Return sales_enriched DataFrame (from SQLite table, or built on-the-fly)."""
    has_table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='sales_enriched'"
    ).fetchone()
    if has_table:
        return pd.read_sql_query("SELECT * FROM sales_enriched", conn)
    from app.ingest.enriched import build_sales_enriched
    return build_sales_enriched(conn)


def as_of(conn: sqlite3.Connection) -> str | None:
    """'Today' is max(sales.date), never the system clock (doc 02 principle 5)."""
    row = conn.execute("SELECT MAX(date) AS d FROM sales").fetchone()
    return row["d"] if row and row["d"] else None


def is_empty(conn: sqlite3.Connection) -> bool:
    """Return True if sales table is empty or has zero rows."""
    try:
        row = conn.execute("SELECT COUNT(*) AS c FROM sales").fetchone()
        return bool(not row or row["c"] == 0)
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        return True


def row_counts(conn: sqlite3.Connection) -> dict[str, int]:
    return {
        table: conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
        for table in SCHEMA
    }


def data_version(conn: sqlite3.Connection) -> str:
    """Bumped on every ingest; cache key component (doc 02 section 7)."""
    row = conn.execute("SELECT value FROM meta WHERE key = 'data_version'").fetchone()
    return row["value"] if row else "0"


def bump_data_version(conn: sqlite3.Connection) -> str:
    current = data_version(conn)
    new = str(int(current) + 1)
    conn.execute(
        "INSERT INTO meta (key, value) VALUES ('data_version', ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (new,),
    )
    conn.commit()
    return new


class Store:
    """High-level Store interface for querying data and managing cache."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or settings.db_path
        self._cached_sales_enriched: pd.DataFrame | None = None
        self._cached_version: str | None = None
        self._init_db()

    def _init_db(self) -> None:
        with self.connection() as conn:
            init_schema(conn)

    @contextlib.contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def table(self, name: str) -> pd.DataFrame:
        """Return the specified SQLite table as a pandas DataFrame."""
        with self.connection() as conn:
            return get_table(conn, name)

    @property
    def as_of(self) -> str | None:
        """As-of date computed dynamically as max(sales.date)."""
        with self.connection() as conn:
            return as_of(conn)

    @property
    def is_empty(self) -> bool:
        """Check if the store database has no sales data."""
        with self.connection() as conn:
            return is_empty(conn)

    @property
    def data_version(self) -> str:
        """Data version string, bumped on every load/upload."""
        with self.connection() as conn:
            return data_version(conn)

    @property
    def sales_enriched(self) -> pd.DataFrame:
        """Cached sales_enriched DataFrame, invalidated when data_version changes."""
        cur_version = self.data_version
        if self._cached_sales_enriched is not None and self._cached_version == cur_version:
            return self._cached_sales_enriched
        with self.connection() as conn:
            df = get_sales_enriched(conn)
        self._cached_sales_enriched = df
        self._cached_version = cur_version
        return df

    def invalidate_cache(self) -> None:
        self._cached_sales_enriched = None
        self._cached_version = None

    def bump_data_version(self) -> str:
        with self.connection() as conn:
            v = bump_data_version(conn)
        self.invalidate_cache()
        return v

    def clear(self) -> None:
        with self.connection() as conn:
            clear_all(conn)
        self.invalidate_cache()


store = Store()
