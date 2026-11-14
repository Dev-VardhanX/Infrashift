"""backend/tests/test_golden.py
Verifies golden numbers from docs/06_GOLDEN_NUMBERS.md against analytics tools.
Rule: Tolerance +-0.5% for amounts; counts and Rs balances exact.
Golden numbers live ONLY in tests, never in app code.
"""
import pytest
from app.analytics.sales_summary import sales_summary
from app.analytics.top_products import top_products
from app.analytics.compare_periods import compare_periods
from app.analytics.dead_stock import dead_stock
from app.analytics.khata_overdue import khata_overdue
from app.analytics.expense_summary import expense_summary
from app.analytics.stock_status import stock_status
from app.analytics.restock_plan import restock_plan
from app.analytics.payment_mix import payment_mix
from app.analytics.festive_lift import festive_lift
from app.analytics._data import get_data


def test_golden_kpis_last_30d():
    """Verify KPIs for last 30 days (15 Oct to 13 Nov 2026)."""
    res = sales_summary(db=None, from_date="last_30d")
    data = res["data"]

    # Golden numbers: docs/06
    # Revenue: Rs 14,32,103
    # Taxable value: Rs 13,62,759
    # GST collected: Rs 69,344
    # Gross profit: Rs 1,05,673
    # Gross margin %: 7.75%
    # Invoices: 3,863 (exact)
    # Average bill: Rs 370.7
    assert data["revenue"] == pytest.approx(1432103, rel=0.005)
    assert data["taxable"] == pytest.approx(1362759, rel=0.005)
    assert data["gst"] == pytest.approx(69344, rel=0.005)
    assert data["gross_profit"] == pytest.approx(105673, rel=0.005)
    assert data["gross_margin_pct"] == pytest.approx(7.75, rel=0.005)
    assert data["invoices"] == 3863
    assert data["avg_bill"] == pytest.approx(370.7, rel=0.005)
    assert res["meta"]["as_of"] == "2026-11-13"


def test_golden_kpis_prev_30d():
    """Verify KPIs for previous 30 days (15 Sep to 14 Oct 2026)."""
    res = sales_summary(db=None, from_date="prev_30d")
    data = res["data"]

    # Golden numbers: docs/06
    # Revenue: Rs 12,28,253
    # Taxable value: Rs 11,67,246
    # GST collected: Rs 61,007
    # Gross profit: Rs 85,094
    # Gross margin %: 7.29%
    # Invoices: 3,579 (exact)
    # Average bill: Rs 343.2
    assert data["revenue"] == pytest.approx(1228253, rel=0.005)
    assert data["taxable"] == pytest.approx(1167246, rel=0.005)
    assert data["gst"] == pytest.approx(61007, rel=0.005)
    assert data["gross_profit"] == pytest.approx(85094, rel=0.005)
    assert data["gross_margin_pct"] == pytest.approx(7.29, rel=0.005)
    assert data["invoices"] == 3579
    assert data["avg_bill"] == pytest.approx(343.2, rel=0.005)


def test_golden_payment_mix_last_30d():
    """Payment mix (last 30d, share of revenue): UPI 61.4%, cash 30.6%, card 5.8%, khata 2.2%."""
    res = payment_mix(db=None, from_date="last_30d")
    items = {item["payment_mode"]: item for item in res["data"]}

    assert items["upi"]["share_pct"] == pytest.approx(61.4, rel=0.005)
    assert items["cash"]["share_pct"] == pytest.approx(30.6, rel=0.005)
    assert items["card"]["share_pct"] == pytest.approx(5.8, rel=0.005)
    assert items["khata"]["share_pct"] == pytest.approx(2.2, rel=0.005)


def test_golden_top_5_by_revenue_last_30d():
    """Top 5 by revenue (last 30d):
    Aashirvaad Atta 5kg Rs 1,33,980; Amul Ghee 1L Rs 1,20,960;
    India Gate Basmati 5kg Rs 1,16,725; Fortune Sunflower Oil 1L Rs 77,250;
    Almonds 250g Rs 65,415.
    """
    res = top_products(db=None, metric="revenue", n=5, from_date="last_30d")
    top_list = res["data"]

    assert len(top_list) == 5
    expected_top = [
        ("Aashirvaad Atta 5kg", 133980),
        ("Amul Ghee 1L", 120960),
        ("India Gate Basmati Rice 5kg", 116725),
        ("Fortune Sunflower Oil 1L", 77250),
        ("Almonds 250g", 65415),
    ]

    for item, (expected_name, expected_rev) in zip(top_list, expected_top):
        assert item["name"] == expected_name
        assert item["revenue"] == pytest.approx(expected_rev, rel=0.005)


def test_golden_top_5_by_profit_last_30d():
    """Top 5 by profit (last 30d):
    India Gate Basmati Rs 8,206; Almonds Rs 7,534;
    Aashirvaad Atta Rs 6,682; Cashew Rs 6,541; Amul Ghee Rs 4,692.
    """
    res = top_products(db=None, metric="profit", n=5, from_date="last_30d")
    top_list = res["data"]

    assert len(top_list) == 5
    expected_top = [
        ("India Gate Basmati Rice 5kg", 8206),
        ("Almonds 250g", 7534),
        ("Aashirvaad Atta 5kg", 6682),
        ("Cashew 250g", 6541),
        ("Amul Ghee 1L", 4692),
    ]

    for item, (expected_name, expected_prof) in zip(top_list, expected_top):
        assert item["name"] == expected_name
        assert item["profit"] == pytest.approx(expected_prof, rel=0.005)


def test_golden_diwali_week_vs_prior_week():
    """Diwali week total revenue: Rs 4,36,555 vs prior week Rs 4,03,802 (+8.1%)."""
    res = compare_periods(
        db=None,
        metric="revenue",
        a_from="diwali_week",
        b_from="prior_week",
    )
    data = res["data"]

    assert data["period_a"]["value"] == pytest.approx(436555, rel=0.005)
    assert data["period_b"]["value"] == pytest.approx(403802, rel=0.005)
    assert data["delta_pct"] == pytest.approx(8.1, rel=0.02)  # 8.11% rounded to 8.1%


def test_golden_stock_value_and_khata_outstanding():
    """Stock value at cost: Rs 2,65,385 (exact).
    Khata outstanding: Rs 35,248 (exact).
    """
    data_dict = get_data(db=None)
    inventory = data_dict["inventory"]
    products = data_dict["products"]
    customers = data_dict["customers"]

    # Stock value = current_stock * products.cost_price
    inv_prod = inventory.merge(products[["sku", "cost_price"]], on="sku")
    stock_value = round((inv_prod["current_stock"] * inv_prod["cost_price"]).sum())
    assert stock_value == 265385

    # Khata outstanding = sum(customers.khata_balance)
    khata_outstanding = int(customers["khata_balance"].sum())
    assert khata_outstanding == 35248


def test_golden_dead_stock():
    """Dead stock: 3 SKUs (JUC01, SYR01, SYR02), capital locked Rs 45,556."""
    res = dead_stock(db=None, days=30, max_sell_through=0.05)
    data = res["data"]

    assert data["sku_count"] == 3
    assert data["capital_locked"] == pytest.approx(45556, rel=0.005)

    skus = {item["sku"] for item in data["items"]}
    assert skus == {"JUC01", "SYR01", "SYR02"}


def test_golden_khata_overdue():
    """Khata overdue >45d: 7 customers, total Rs 31,369, C003 and C010 over limit."""
    res = khata_overdue(db=None, min_days=45)
    data = res["data"]

    assert data["customer_count"] == 7
    assert data["total_overdue"] == 31369.0
    assert data["over_limit_count"] == 2

    cust_map = {c["customer_id"]: c for c in data["customers"]}
    assert "C003" in cust_map and cust_map["C003"]["over_limit"] is True
    assert "C010" in cust_map and cust_map["C010"]["over_limit"] is True
    assert cust_map["C003"]["balance"] == 9685.0
    assert cust_map["C003"]["days_since_payment"] == 108


def test_golden_expense_summary():
    """Expense anomaly: Electricity Oct (Rs 9,718) and Delivery Fuel Oct (Rs 5,100)."""
    res = expense_summary(db=None, flag_anomalies=True)
    anomalies = res["data"]["anomalies"]

    flagged = {(a["month"], a["category"]): a for a in anomalies}
    assert ("2026-10", "Electricity") in flagged
    assert ("2026-10", "Delivery Fuel") in flagged

    elec = flagged[("2026-10", "Electricity")]
    fuel = flagged[("2026-10", "Delivery Fuel")]

    assert elec["amount"] == 9718.0
    assert "Compressor fault - high bill" in elec["note"]
    assert elec["median_other_months"] == 5305.0

    assert fuel["amount"] == 5100.0
    assert fuel["median_other_months"] == 3020.0


def test_golden_stock_status_and_restock_plan():
    """Stock status: Sugar 1kg OUT, Amul Ghee 1L CRITICAL, Puja items FESTIVAL_OVER and never alerted."""
    status_res = stock_status(db=None)
    items_by_sku = {item["sku"]: item for item in status_res["data"]}

    # Sugar 1kg must be OUT
    assert items_by_sku["SUG01"]["status"] == "OUT"
    assert items_by_sku["SUG01"]["stock"] == 0

    # Amul Ghee 1L must be CRITICAL
    assert items_by_sku["GHE01"]["status"] == "CRITICAL"
    assert items_by_sku["GHE01"]["days_of_cover"] < items_by_sku["GHE01"]["lead_time_days"]

    # Puja items must be FESTIVAL_OVER
    for p_sku in ["PUJ01", "PUJ02", "PUJ03", "PUJ04"]:
        assert items_by_sku[p_sku]["status"] == "FESTIVAL_OVER"
        assert items_by_sku[p_sku]["seasonal_note"] == "Festival over, do not reorder"

    # Restock plan must NEVER alert on Puja & Decor items
    plan_res = restock_plan(db=None)
    alerted_skus = {item["sku"] for item in plan_res["data"]["items"]}
    assert "SUG01" in alerted_skus
    assert "GHE01" in alerted_skus
    for p_sku in ["PUJ01", "PUJ02", "PUJ03", "PUJ04"]:
        assert p_sku not in alerted_skus


def test_golden_festive_lift():
    """Festive lift: Diwali week (1-7 Nov) vs baseline (18-24 Oct):
    Dry Fruits (Rs 57,630 vs Rs 14,185, ~4.1x), Puja & Decor (Rs 35,135 vs Rs 8,715, ~4.0x),
    Sweets & Chocolates (Rs 36,815 vs Rs 12,560, ~2.9x).
    """
    res = festive_lift(db=None, event_date="2026-11-08", window_days=7)
    cats = {c["category"]: c for c in res["data"]["categories"]}

    assert cats["Dry Fruits"]["festive_revenue"] == pytest.approx(57630, rel=0.005)
    assert cats["Dry Fruits"]["baseline_revenue"] == pytest.approx(14185, rel=0.005)
    assert cats["Dry Fruits"]["lift_x"] == pytest.approx(4.1, abs=0.1)

    assert cats["Puja & Decor"]["festive_revenue"] == pytest.approx(35135, rel=0.005)
    assert cats["Puja & Decor"]["baseline_revenue"] == pytest.approx(8715, rel=0.005)
    assert cats["Puja & Decor"]["lift_x"] == pytest.approx(4.0, abs=0.1)

    assert cats["Sweets & Chocolates"]["festive_revenue"] == pytest.approx(36815, rel=0.005)
    assert cats["Sweets & Chocolates"]["baseline_revenue"] == pytest.approx(12560, rel=0.005)
    assert cats["Sweets & Chocolates"]["lift_x"] == pytest.approx(2.9, abs=0.1)
