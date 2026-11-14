"""M1 tests: sales_enriched derived builder and mathematical consistency."""
import os
import tempfile
from pathlib import Path
import pandas as pd
import pytest

os.environ["VYAPAAR_DB_PATH"] = str(Path(tempfile.mkdtemp()) / "test_m1_enriched.db")

from app import db as db_module
from app.ingest import loaders
from app.ingest.enriched import build_sales_enriched, build_and_save_sales_enriched


@pytest.fixture(scope="module")
def loaded_db():
    conn = db_module.get_conn()
    loaders.load_sample(conn)
    yield conn
    conn.close()


def test_sales_enriched_structure_and_counts(loaded_db):
    df = db_module.get_sales_enriched(loaded_db)
    assert not df.empty
    # Must have the exact same number of rows as sales (44,305)
    sales_count = loaded_db.execute("SELECT COUNT(*) AS c FROM sales").fetchone()["c"]
    assert len(df) == sales_count

    expected_cols = {
        "invoice_id", "date", "time", "sku", "qty", "unit_price", "payment_mode",
        "customer_id", "name", "category", "mrp", "cost_price", "gst_rate",
        "supplier", "lead_time_days", "reorder_level", "line_revenue", "taxable",
        "gst", "unit_cost_at_sale", "line_cogs", "line_profit", "week", "month",
        "is_festive_window"
    }
    for col in expected_cols:
        assert col in df.columns, f"Missing column {col} in sales_enriched"


def test_sales_enriched_math_invariants(loaded_db):
    df = db_module.get_sales_enriched(loaded_db)
    # 1. line_revenue = qty * unit_price
    rev_diff = (df["qty"] * df["unit_price"] - df["line_revenue"]).abs().max()
    assert rev_diff < 0.001

    # 2. taxable + gst = line_revenue
    tax_diff = ((df["taxable"] + df["gst"]) - df["line_revenue"]).abs().max()
    assert tax_diff < 0.001

    # 3. line_profit = taxable - line_cogs
    profit_diff = ((df["taxable"] - df["line_cogs"]) - df["line_profit"]).abs().max()
    assert profit_diff < 0.001

    # 4. line_cogs = qty * unit_cost_at_sale
    cogs_diff = (df["qty"] * df["unit_cost_at_sale"] - df["line_cogs"]).abs().max()
    assert cogs_diff < 0.001


def test_sales_enriched_golden_reconciliation(loaded_db):
    df = db_module.get_sales_enriched(loaded_db)
    as_of = pd.to_datetime(df["date"].max())
    # Last 30 days = [AS_OF - 29 days, AS_OF]
    start_date = (as_of - pd.Timedelta(days=29)).strftime("%Y-%m-%d")
    end_date = as_of.strftime("%Y-%m-%d")

    l30 = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
    revenue = round(l30["line_revenue"].sum())
    taxable = round(l30["taxable"].sum())
    gst = round(l30["gst"].sum())
    profit = round(l30["line_profit"].sum())

    # Golden numbers from 06_GOLDEN_NUMBERS.md:
    # Revenue: Rs 14,32,103
    # Taxable: Rs 13,62,759
    # GST: Rs 69,344
    # Gross Profit: Rs 1,05,673
    assert abs(revenue - 1432103) / 1432103 < 0.005, f"Revenue {revenue} mismatch"
    assert abs(taxable - 1362759) / 1362759 < 0.005, f"Taxable {taxable} mismatch"
    assert abs(gst - 69344) / 69344 < 0.005, f"GST {gst} mismatch"
    assert abs(profit - 105673) / 105673 < 0.005, f"Profit {profit} mismatch"

