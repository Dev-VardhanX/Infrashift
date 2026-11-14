"""M1: central configuration. Reads .env at repo root; no secrets in code.

Doc 01 section 4 & Doc 02 section 7:
- AS_OF is computed dynamically as max(sales.date), never the system clock.
- Key business constants: DIWALI_DATE, SEASONAL_CATEGORIES, GST_SLABS,
  DEAD_STOCK and OVERDUE thresholds.
"""
import os
from pathlib import Path
import sqlite3
from typing import Any

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent

load_dotenv(REPO_ROOT / ".env")

# Domain constants per PRD 01 section 4 & System Design 02
DIWALI_DATE: str = "2026-11-08"
SEASONAL_CATEGORIES: list[str] = ["Puja & Decor"]
GST_SLABS: set[int] = {0, 5, 12, 18}

# Thresholds from docs/01 section 4
DEAD_STOCK_DAYS: int = 30
DEAD_STOCK_SELL_THROUGH_THRESHOLD: float = 0.05  # <= 5% of stock sold in last 30 days
OVERDUE_DAYS: int = 45  # balance > 0 and days since last payment > 45
MARGIN_LEAK_DROP_PP: float = 5.0  # margin fell >= 5 percentage points
EXPENSE_ANOMALY_MULTIPLIER: float = 1.5  # monthly total > 1.5 x median of other months
EXPENSE_ANOMALY_MIN_INR: float = 1000.0  # and > Rs 1,000 absolute


def compute_as_of(conn: sqlite3.Connection) -> str | None:
    """Compute AS_OF date dynamically as max(sales.date)."""
    try:
        row = conn.execute("SELECT MAX(date) AS d FROM sales").fetchone()
        return row[0] if row and row[0] else None
    except Exception:
        return None


class Settings:
    """Immutable-by-convention settings container."""

    def __init__(self) -> None:
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
        self.gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.copilot_mode: str = os.getenv("COPILOT_MODE", "llm").strip().lower()
        self.llm_timeout_s: float = float(os.getenv("LLM_TIMEOUT_S", "6"))
        self.auto_load_sample: bool = os.getenv("AUTO_LOAD_SAMPLE", "true").strip().lower() in ("1", "true", "yes")
        db_path = os.getenv("VYAPAAR_DB_PATH", str(BACKEND_DIR / "vyapaar.db"))
        self.db_path: Path = Path(db_path)
        self.sample_data_dir: Path = REPO_ROOT / "data" / "sample"

        # Domain constants references
        self.diwali_date: str = DIWALI_DATE
        self.seasonal_categories: list[str] = SEASONAL_CATEGORIES
        self.gst_slabs: set[int] = GST_SLABS
        self.dead_stock_days: int = DEAD_STOCK_DAYS
        self.dead_stock_sell_through_threshold: float = DEAD_STOCK_SELL_THROUGH_THRESHOLD
        self.overdue_days: int = int(os.getenv("OVERDUE_DAYS", str(OVERDUE_DAYS)))
        self.margin_leak_drop_pp: float = MARGIN_LEAK_DROP_PP
        self.expense_anomaly_multiplier: float = EXPENSE_ANOMALY_MULTIPLIER
        self.expense_anomaly_min_inr: float = EXPENSE_ANOMALY_MIN_INR

        # Festival marker for the dashboard trend chart (doc 02 section 3.1)
        self.festival_marker: dict[str, str] = {"date": DIWALI_DATE, "label": "Diwali"}


settings = Settings()
