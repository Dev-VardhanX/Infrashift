"""M1 golden tests: /api/load-sample, Store class, sales_enriched vectorisation, and golden numbers."""
from pathlib import Path
import time

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.config import (
    DEAD_STOCK_DAYS,
    DEAD_STOCK_SELL_THROUGH_THRESHOLD,
    DIWALI_DATE,
    GST_SLABS,
    OVERDUE_DAYS,
    SEASONAL_CATEGORIES,
    settings,
)
from app.db import Store, store as default_store
from app.ingest.enriched import build_sales_enriched
from app.main import app

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def load_sample_data():
    """Ensure sample store data is loaded before running tests."""
    res = client.post("/api/load-sample")
    assert res.status_code == 200, res.text


def test_config_constants():
    """Verify constants defined in app/config.py per PRD / System Design."""
    assert DIWALI_DATE == "2026-11-08"
    assert SEASONAL_CATEGORIES == ["Puja & Decor"]
    assert GST_SLABS == {0, 5, 12, 18}
    assert DEAD_STOCK_DAYS == 30
    assert DEAD_STOCK_SELL_THROUGH_THRESHOLD == 0.05
    assert OVERDUE_DAYS == 45


def test_load_sample_endpoint_and_store():
    """Verify POST /api/load-sample response shape and Store class behavior."""
    response = client.post("/api/load-sample")
    assert response.status_code == 200, response.text
    body = response.json()

    assert "loaded" in body
    assert "as_of" in body
    assert body["as_of"] == "2026-11-13"

    loaded = body["loaded"]
    assert "sales" in loaded
    assert "products" in loaded
    assert loaded["products"] == 38
    assert abs(loaded["sales"] - 44303) / 44303 <= 0.005


def test_store_class_and_caching():
    """Verify Store has .table(name), .sales_enriched (cached), .as_of, and .data_version."""
    store = Store(settings.db_path)
    assert store.as_of == "2026-11-13"
    assert int(store.data_version) >= 1

    # .table(name) returns a DataFrame
    products_df = store.table("products")
    assert isinstance(products_df, pd.DataFrame)
    assert len(products_df) == 38

    # .sales_enriched is cached
    se1 = store.sales_enriched
    se2 = store.sales_enriched
    assert se1 is se2

    # Invalidation on bump_data_version
    store.bump_data_version()
    se3 = store.sales_enriched
    assert se3 is not se1


def test_vectorised_sales_enriched_performance():
    """Verify build_sales_enriched is vectorised and completes in under 2 seconds."""
    store = Store(settings.db_path)
    with store.connection() as conn:
        t0 = time.perf_counter()
        df = build_sales_enriched(conn)
        elapsed = time.perf_counter() - t0

    assert not df.empty
    assert elapsed < 2.0, f"Vectorised build took {elapsed:.3f}s, expected < 2.0s"


def test_golden_numbers_tolerance_half_percent():
    """Verify golden numbers from docs/06_GOLDEN_NUMBERS.md within +-0.5% tolerance."""
    store = Store(settings.db_path)

    # 1. Sales rows == 44303 (+-0.5%)
    sales_df = store.table("sales")
    sales_rows = len(sales_df)
    assert abs(sales_rows - 44303) / 44303 <= 0.005, f"Sales rows {sales_rows} outside +-0.5%"

    # 2. AS_OF == 2026-11-13
    assert store.as_of == "2026-11-13"

    # 3. Whole-dataset revenue == 8,153,368 (+-0.5%)
    se = store.sales_enriched
    whole_revenue = se["line_revenue"].sum()
    golden_whole_rev = 8153368
    assert abs(whole_revenue - golden_whole_rev) / golden_whole_rev <= 0.005, (
        f"Whole revenue {whole_revenue} outside +-0.5% of {golden_whole_rev}"
    )

    # 4. Last-30d (15 Oct to 13 Nov) revenue == 1,432,103 and sum(line_profit) == 105,673 (+-0.5%)
    l30 = se[(se["date"] >= "2026-10-15") & (se["date"] <= "2026-11-13")]
    l30_revenue = l30["line_revenue"].sum()
    l30_profit = l30["line_profit"].sum()
    golden_l30_rev = 1432103
    golden_l30_profit = 105673

    assert abs(l30_revenue - golden_l30_rev) / golden_l30_rev <= 0.005, (
        f"Last-30d revenue {l30_revenue} outside +-0.5% of {golden_l30_rev}"
    )
    assert abs(l30_profit - golden_l30_profit) / golden_l30_profit <= 0.005, (
        f"Last-30d profit {l30_profit} outside +-0.5% of {golden_l30_profit}"
    )

    # 5. Stock value at cost == 265,385 (+-0.5%)
    inv = store.table("inventory").merge(store.table("products"), on="sku")
    stock_value = (inv["current_stock"] * inv["cost_price"]).sum()
    golden_stock_val = 265385
    assert abs(stock_value - golden_stock_val) / golden_stock_val <= 0.005, (
        f"Stock value {stock_value} outside +-0.5% of {golden_stock_val}"
    )

    # 6. Khata outstanding == 35,248 (+-0.5%)
    customers = store.table("customers")
    khata_outstanding = customers["khata_balance"].sum()
    golden_khata = 35248
    assert abs(khata_outstanding - golden_khata) / golden_khata <= 0.005, (
        f"Khata outstanding {khata_outstanding} outside +-0.5% of {golden_khata}"
    )
