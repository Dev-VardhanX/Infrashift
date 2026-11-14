"""backend/tests/test_tools_hand.py
Unit tests verifying analytics tools and date resolver against hand-computed expected results.
Includes tests for edge cases and empty periods.
"""
import pytest
from app.analytics.periods import resolve_period, get_as_of
from app.analytics.sales_summary import sales_summary
from app.analytics.top_products import top_products
from app.analytics.compare_periods import compare_periods
from app.analytics.margin_by_product import margin_by_product
from app.analytics.dead_stock import dead_stock
from app.analytics.khata_overdue import khata_overdue
from app.analytics.expense_summary import expense_summary
from app.analytics.stock_status import stock_status
from app.analytics.restock_plan import restock_plan
from app.analytics.payment_mix import payment_mix
from app.analytics.festive_lift import festive_lift


def test_periods_resolution(hand_fixture_data):
    as_of = get_as_of(hand_fixture_data)
    assert as_of.strftime("%Y-%m-%d") == "2026-11-13"

    start, end = resolve_period("last_7d", db=hand_fixture_data)
    assert start.strftime("%Y-%m-%d") == "2026-11-07"
    assert end.strftime("%Y-%m-%d") == "2026-11-13"

    start, end = resolve_period("last_30d", db=hand_fixture_data)
    assert start.strftime("%Y-%m-%d") == "2026-10-15"
    assert end.strftime("%Y-%m-%d") == "2026-11-13"

    start, end = resolve_period("prev_30d", db=hand_fixture_data)
    assert start.strftime("%Y-%m-%d") == "2026-09-15"
    assert end.strftime("%Y-%m-%d") == "2026-10-14"

    start, end = resolve_period("this_month", db=hand_fixture_data)
    assert start.strftime("%Y-%m-%d") == "2026-11-01"
    assert end.strftime("%Y-%m-%d") == "2026-11-13"

    start, end = resolve_period("last_month", db=hand_fixture_data)
    assert start.strftime("%Y-%m-%d") == "2026-10-01"
    assert end.strftime("%Y-%m-%d") == "2026-10-31"

    start, end = resolve_period("diwali_week", db=hand_fixture_data)
    assert start.strftime("%Y-%m-%d") == "2026-11-01"
    assert end.strftime("%Y-%m-%d") == "2026-11-07"


def test_sales_summary_hand_computed(hand_fixture_data):
    # Hand calculation for last_30d:
    # Invoices: 6 (INV01..INV06)
    # Revenue: 200 + 210 + 236 + 300 + 420 + 118 = 1484.0
    # Taxable: 200 + 200 + 200 + 300 + 400 + 100 = 1400.0
    # GST: 0 + 10 + 36 + 0 + 20 + 18 = 84.0
    # COGS: 160 + 160 + 140 + 240 + 320 + 70 = 1090.0
    # Profit: 1400 - 1090 = 310.0
    # Margin %: 310 / 1400 * 100 = 22.14%
    # Avg bill: 1484 / 6 = 247.3
    res = sales_summary(db=hand_fixture_data, from_date="last_30d")
    data = res["data"]
    assert data["revenue"] == 1484.0
    assert data["taxable"] == 1400.0
    assert data["gst"] == 84.0
    assert data["gross_profit"] == 310.0
    assert data["gross_margin_pct"] == pytest.approx(22.14, abs=0.01)
    assert data["invoices"] == 6
    assert data["avg_bill"] == 247.3
    assert res["meta"]["as_of"] == "2026-11-13"
    assert res["meta"]["row_count"] == 6


def test_sales_summary_payment_mode_hand_computed(hand_fixture_data):
    res = sales_summary(db=hand_fixture_data, from_date="last_30d", group_by="payment_mode")
    items = {item["payment_mode"]: item for item in res["data"]}
    # UPI: INV01 (200) + INV03 (236) = 436.0 -> 436/1484 = 29.4%
    # Cash: INV02 (210) + INV06 (118) = 328.0 -> 328/1484 = 22.1%
    # Card: INV04 (300) = 300.0 -> 300/1484 = 20.2%
    # Khata: INV05 (420) = 420.0 -> 420/1484 = 28.3%
    assert items["upi"]["revenue"] == 436.0
    assert items["upi"]["share_pct"] == 29.4
    assert items["cash"]["revenue"] == 328.0
    assert items["cash"]["share_pct"] == 22.1
    assert items["card"]["revenue"] == 300.0
    assert items["card"]["share_pct"] == 20.2
    assert items["khata"]["revenue"] == 420.0
    assert items["khata"]["share_pct"] == 28.3


def test_top_products_hand_computed(hand_fixture_data):
    # Top products last 30d by revenue:
    # 1. SKU02 (Mustard Oil): 210 + 420 = 630.0
    # 2. SKU01 (Wheat Flour): 200 + 300 = 500.0
    # 3. SKU03 (Chocolate Box): 236 + 118 = 354.0
    res_rev = top_products(db=hand_fixture_data, metric="revenue", n=3, from_date="last_30d")
    data_rev = res_rev["data"]
    assert [d["sku"] for d in data_rev] == ["SKU02", "SKU01", "SKU03"]
    assert data_rev[0]["revenue"] == 630.0
    assert data_rev[1]["revenue"] == 500.0
    assert data_rev[2]["revenue"] == 354.0

    # Top products last 30d by profit:
    # 1. SKU02: 40 + 80 = 120.0
    # 2. SKU01: 40 + 60 = 100.0
    # 3. SKU03: 60 + 30 = 90.0
    res_prof = top_products(db=hand_fixture_data, metric="profit", n=3, from_date="last_30d")
    data_prof = res_prof["data"]
    assert [d["sku"] for d in data_prof] == ["SKU02", "SKU01", "SKU03"]
    assert data_prof[0]["profit"] == 120.0
    assert data_prof[1]["profit"] == 100.0
    assert data_prof[2]["profit"] == 90.0


def test_compare_periods_hand_computed(hand_fixture_data):
    # Diwali week (INV03: 236, INV04: 300, INV05: 420) -> 956.0
    # Prior week (INV06: 118) -> 118.0
    # Delta: 956 - 118 = 838.0
    # Delta %: (838 / 118) * 100 = 710.2%
    res = compare_periods(
        db=hand_fixture_data,
        metric="revenue",
        a_from="diwali_week",
        b_from="prior_week",
    )
    data = res["data"]
    assert data["period_a"]["value"] == 956.0
    assert data["period_b"]["value"] == 118.0
    assert data["delta"] == 838.0
    assert data["delta_pct"] == 710.2


def test_margin_by_product_hand_computed(hand_fixture_data):
    # SKU03: taxable = 200, profit = 60, cogs = 140 -> margin = 30.0%
    # SKU01: taxable = 500, profit = 100, cogs = 400 -> margin = 20.0%
    # SKU02: taxable = 600, profit = 120, cogs = 480 -> margin = 20.0%
    res = margin_by_product(db=hand_fixture_data, from_date="last_30d")
    data = {d["sku"]: d for d in res["data"]}
    assert data["SKU03"]["margin_pct"] == pytest.approx(30.0, abs=0.01)
    assert data["SKU01"]["margin_pct"] == pytest.approx(20.0, abs=0.01)
    assert data["SKU02"]["margin_pct"] == pytest.approx(20.0, abs=0.01)
    assert res["meta"]["as_of"] == "2026-11-13"


def test_dead_stock_hand_computed(hand_fixture_data):
    # SKU04 (Old Cold Drink): stock 100, sold 0 in last 30d -> dead stock!
    # Cost = 30.0 -> capital locked = 100 * 30.0 = 3000.0.
    # PUJ01 (Earthen Diyas): stock 25, sold 0, but category is Puja & Decor -> excluded!
    res = dead_stock(db=hand_fixture_data, days=30, max_sell_through=0.05)
    data = res["data"]
    assert data["sku_count"] == 1
    assert data["capital_locked"] == 3000.0
    assert data["items"][0]["sku"] == "SKU04"
    assert data["items"][0]["capital_locked"] == 3000.0


def test_khata_overdue_hand_computed(hand_fixture_data):
    # C01: last payment 2026-10-01 (43 days ago) -> not > 45d.
    # C02: last payment 2026-08-01 (104 days ago) -> > 45d!
    # C02 balance: 6000.0, credit limit 5000.0 -> over_limit = True!
    res = khata_overdue(db=hand_fixture_data, min_days=45)
    data = res["data"]
    assert data["customer_count"] == 1
    assert data["total_overdue"] == 6000.0
    assert data["over_limit_count"] == 1
    assert data["customers"][0]["customer_id"] == "C02"
    assert data["customers"][0]["over_limit"] is True


def test_expense_summary_hand_computed(hand_fixture_data):
    # Electricity has 1000 in Aug, 1000 in Sep, 3000 in Oct, 1000 in Nov.
    # For Oct: other months median is 1000. 3000 > 1.5 * 1000 = 1500 and > 1000 -> Anomaly!
    res = expense_summary(db=hand_fixture_data, flag_anomalies=True)
    anomalies = res["data"]["anomalies"]
    assert len(anomalies) == 1
    a = anomalies[0]
    assert a["category"] == "Electricity"
    assert a["month"] == "2026-10"
    assert a["amount"] == 3000.0
    assert a["median_other_months"] == 1000.0
    assert a["ratio"] == 3.0
    assert "Compressor fault" in a["note"]


def test_stock_status_and_restock_plan_hand_computed(hand_fixture_data):
    # SKU01: stock 50, cover 172.4d > 4d -> OK
    # SKU02: stock 1, daily 0.17, cover 5.88d > 5d -> OK
    # SKU03: stock 0, daily 0.13 <= 0.5, cover 0.0d < lead 2d -> CRITICAL
    # PUJ01: stock 25, category Puja & Decor, as_of (2026-11-13) > Diwali (2026-11-08) -> FESTIVAL_OVER!
    status_res = stock_status(db=hand_fixture_data)
    items = {item["sku"]: item for item in status_res["data"]}

    assert items["SKU01"]["status"] == "OK"
    assert items["SKU02"]["status"] == "OK"
    assert items["SKU03"]["status"] == "CRITICAL"
    assert items["PUJ01"]["status"] == "FESTIVAL_OVER"
    assert items["PUJ01"]["seasonal_note"] == "Festival over, do not reorder"

    # Single SKU query
    single_res = stock_status(db=hand_fixture_data, sku="PUJ01")
    assert single_res["data"]["status"] == "FESTIVAL_OVER"

    # Restock plan: includes SKU03 (CRITICAL)
    # Excludes SKU01, SKU02, SKU04 (OK) and PUJ01 (FESTIVAL_OVER)
    plan_res = restock_plan(db=hand_fixture_data)
    plan_skus = {item["sku"] for item in plan_res["data"]["items"]}
    assert plan_skus == {"SKU03"}
    assert "PUJ01" not in plan_skus
    assert "SKU01" not in plan_skus
    assert "Sweet Co" in plan_res["data"]["by_supplier"]


def test_payment_mix_hand_computed(hand_fixture_data):
    res = payment_mix(db=hand_fixture_data, from_date="last_30d")
    items = {item["payment_mode"]: item for item in res["data"]}
    assert items["upi"]["share_pct"] == 29.4
    assert items["cash"]["share_pct"] == 22.1
    assert items["card"]["share_pct"] == 20.2
    assert items["khata"]["share_pct"] == 28.3


def test_festive_lift_hand_computed(hand_fixture_data):
    res = festive_lift(db=hand_fixture_data, event_date="2026-11-08", window_days=7)
    cats = {c["category"]: c for c in res["data"]["categories"]}
    # In hand fixture:
    # Festive week (1-7 Nov): INV03 (Sweets, 236), INV04 (Staples, 300), INV05 (Oil, 420)
    # Baseline week (18-24 Oct): no sales in that week (INV06 was 28 Oct)
    assert "Sweets & Chocolates" in cats
    assert cats["Sweets & Chocolates"]["festive_revenue"] == 236.0


def test_empty_period_hand_computed(hand_fixture_data):
    """Verify that all tools handle empty periods gracefully without crashing."""
    empty_from = "2025-01-01"
    empty_to = "2025-01-10"

    # sales_summary
    s_res = sales_summary(db=hand_fixture_data, from_date=empty_from, to_date=empty_to)
    assert s_res["data"]["revenue"] == 0.0
    assert s_res["data"]["invoices"] == 0
    assert s_res["meta"]["row_count"] == 0

    # sales_summary with group_by
    s_grp = sales_summary(db=hand_fixture_data, from_date=empty_from, to_date=empty_to, group_by="payment_mode")
    assert s_grp["data"] == []

    # top_products
    top_res = top_products(db=hand_fixture_data, from_date=empty_from, to_date=empty_to)
    assert top_res["data"] == []
    assert top_res["meta"]["row_count"] == 0

    # compare_periods
    comp_res = compare_periods(db=hand_fixture_data, a_from=empty_from, a_to=empty_to, b_from=empty_from, b_to=empty_to)
    assert comp_res["data"]["period_a"]["value"] == 0.0
    assert comp_res["data"]["period_b"]["value"] == 0.0
    assert comp_res["data"]["delta"] == 0.0

    # margin_by_product
    m_res = margin_by_product(db=hand_fixture_data, from_date=empty_from, to_date=empty_to)
    assert m_res["data"] == []
    assert m_res["meta"]["row_count"] == 0

    # expense_summary for empty range
    e_res = expense_summary(db=hand_fixture_data, from_date=empty_from, to_date=empty_to, flag_anomalies=False)
    assert e_res["data"]["total_expense"] == 0.0
    assert e_res["data"]["categories"] == []

    # payment_mix for empty range
    pm_res = payment_mix(db=hand_fixture_data, from_date=empty_from, to_date=empty_to)
    assert pm_res["data"] == []
