"""backend/tests/test_edge_cases.py
Edge case test suite:
1. Empty period (zero sales in requested window)
2. Unknown SKU (non-existent SKU id or unmatchable name)
3. SKU with zero sales across entire history
4. Malformed date token (invalid token or unparseable string)
"""
import pytest
import pandas as pd
from app.analytics.periods import resolve_period, get_as_of
from app.analytics.sales_summary import sales_summary
from app.analytics.top_products import top_products
from app.analytics.compare_periods import compare_periods
from app.analytics.margin_by_product import margin_by_product
from app.analytics.stock_status import stock_status
from app.analytics.forecast import daily_demand
from app.analytics.dead_stock import dead_stock
from app.analytics.payment_mix import payment_mix
from app.copilot.router import ask, fuzzy_resolve_sku


def test_empty_period_edge_cases():
    """All tools must handle empty periods (no sales in range) cleanly without crashing."""
    empty_start = "2020-01-01"
    empty_end = "2020-01-15"

    # 1. sales_summary (aggregate)
    ss = sales_summary(db=None, from_date=empty_start, to_date=empty_end)
    assert ss["data"]["revenue"] == 0.0
    assert ss["data"]["gross_profit"] == 0.0
    assert ss["data"]["invoices"] == 0
    assert ss["meta"]["row_count"] == 0

    # 2. sales_summary (grouped)
    ss_grp = sales_summary(db=None, from_date=empty_start, to_date=empty_end, group_by="payment_mode")
    assert ss_grp["data"] == []
    assert ss_grp["meta"]["row_count"] == 0

    # 3. top_products
    tp = top_products(db=None, from_date=empty_start, to_date=empty_end)
    assert tp["data"] == []
    assert tp["meta"]["row_count"] == 0

    # 4. compare_periods
    cp = compare_periods(db=None, a_from=empty_start, a_to=empty_end, b_from=empty_start, b_to=empty_end)
    assert cp["data"]["period_a"]["value"] == 0.0
    assert cp["data"]["period_b"]["value"] == 0.0
    assert cp["data"]["delta"] == 0.0
    assert cp["data"]["delta_pct"] == 0.0

    # 5. margin_by_product
    mp = margin_by_product(db=None, from_date=empty_start, to_date=empty_end)
    assert mp["data"] == []
    assert mp["meta"]["row_count"] == 0

    # 6. payment_mix
    pm = payment_mix(db=None, from_date=empty_start, to_date=empty_end)
    assert pm["data"] == []


def test_unknown_sku_edge_cases():
    """Tools must handle unknown/non-existent SKUs without raising unhandled exceptions."""
    unknown_sku = "NONEXISTENT_SKU_999"

    # 1. daily_demand should return 0.0
    demand = daily_demand(unknown_sku, db=None)
    assert demand == 0.0

    # 2. stock_status for unknown SKU should return an empty dict (not crash or return a list)
    status_res = stock_status(db=None, sku=unknown_sku)
    assert status_res["data"] == {} or status_res["data"] is None
    assert status_res["meta"]["row_count"] == 0

    # 3. fuzzy_resolve_sku should return None for unmatchable query
    match = fuzzy_resolve_sku("Completely Unknown Flying Carpet", db=None)
    assert match is None

    # 4. Copilot ask with completely unknown question
    res = ask("What is the price of Martian space rock?", db=None, mode="fallback")
    assert "cannot answer" in res["answer"].lower()
    assert res["validated"] is True


def test_sku_with_zero_sales(hand_fixture_data):
    """Product with zero sales in entire history must be handled gracefully."""
    # In hand_fixture_data, SKU04 (Old Cold Drink) has 0 sales in the sales table
    zero_sales_sku = "SKU04"

    # 1. daily_demand is 0.0
    demand = daily_demand(zero_sales_sku, db=hand_fixture_data)
    assert demand == 0.0

    # 2. stock_status: stock is 100, daily is 0 -> cover is 999.0, status is OK
    res = stock_status(db=hand_fixture_data, sku=zero_sales_sku)
    assert res["data"]["stock"] == 100
    assert res["data"]["daily_demand"] == 0.0
    assert res["data"]["days_of_cover"] == 999.0
    assert res["data"]["status"] == "OK"

    # 3. dead_stock: 0 sales <= 5% of 100 stock -> must be detected as dead stock
    ds = dead_stock(db=hand_fixture_data)
    skus = [i["sku"] for i in ds["data"]["items"]]
    assert zero_sales_sku in skus


def test_malformed_date_token_edge_cases():
    """Malformed date tokens must raise a clean ValueError instead of pandas internal parser error."""
    malformed_tokens = ["invalid_token", "not_a_date", "last_99d", "2026-99-99"]

    for token in malformed_tokens:
        with pytest.raises(ValueError, match="Invalid date or period token"):
            resolve_period(token, db=None)
