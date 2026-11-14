"""backend/tests/test_insights.py
Tests verifying that the insight engine detects all 6 planted insights from docs/06
with correct evidence, schema compliance, proper actions, and exclusions.
"""
import pytest
from app.insights.rules import (
    get_insights,
    restock_insights,
    dead_stock_insights,
    margin_leak_insights,
    expense_anomaly_insights,
    khata_overdue_insights,
    festive_lift_insights,
)

PLANTED_TYPES = {
    "restock",
    "dead_stock",
    "margin_leak",
    "expense_anomaly",
    "khata_overdue",
    "festive_lift",
}


def test_insight_schema_and_feed_properties():
    """Insights feed must:
    1. Be capped at ~12 items.
    2. Include at least one of each planted type.
    3. Be sorted by impact_inr desc then severity.
    4. Conform strictly to docs/02 section 3.2 schema.
    """
    insights = get_insights(db=None, cap=12)

    assert len(insights) <= 12
    found_types = {i["type"] for i in insights}
    for pt in PLANTED_TYPES:
        assert pt in found_types, f"Planted insight type {pt} missing from feed"

    # Schema check
    for ins in insights:
        assert isinstance(ins["id"], str) and ins["id"]
        assert ins["type"] in PLANTED_TYPES
        assert ins["severity"] in ("high", "medium", "low")
        assert isinstance(ins["title"], str) and ins["title"]
        assert isinstance(ins["impact_inr"], (int, float))
        assert "evidence" in ins and isinstance(ins["evidence"], dict)
        assert isinstance(ins["evidence"]["columns"], list)
        assert isinstance(ins["evidence"]["rows"], list)
        assert isinstance(ins["why"], str) and ins["why"]
        assert "action" in ins and isinstance(ins["action"], dict)
        assert ins["action"]["kind"] in ("none", "draft_po", "whatsapp_reminder")
        assert isinstance(ins["action"]["payload"], dict)
        assert ins["as_of"] == "2026-11-13"

    # Sort order check (descending impact)
    impacts = [i["impact_inr"] for i in insights]
    assert impacts == sorted(impacts, reverse=True)


def test_planted_insight_1_restock():
    """Planted Insight 1: Restock risk for Sugar (OUT) and Amul Ghee (CRITICAL).
    Puja & Decor items must NEVER produce a restock insight.
    """
    items = restock_insights(db=None)
    sku_map = {i["action"]["payload"]["sku"]: i for i in items}

    # Sugar 1kg must be OUT
    assert "SUG01" in sku_map
    assert sku_map["SUG01"]["severity"] == "high"
    assert "out of stock" in sku_map["SUG01"]["title"].lower()

    # Amul Ghee 1L must be CRITICAL
    assert "GHE01" in sku_map
    assert sku_map["GHE01"]["severity"] == "high"
    assert "critical" in sku_map["GHE01"]["title"].lower()

    # Puja & Decor items (PUJ01..PUJ04) must NEVER produce a restock insight
    for p_sku in ["PUJ01", "PUJ02", "PUJ03", "PUJ04"]:
        assert p_sku not in sku_map, f"Puja item {p_sku} should not produce a restock insight"


def test_planted_insight_2_dead_stock():
    """Planted Insight 2: Dead stock for JUC01, SYR01, SYR02 locking Rs 45,556."""
    items = dead_stock_insights(db=None)
    sku_map = {i["action"]["payload"]["sku"]: i for i in items}

    assert "JUC01" in sku_map  # Real Mango Juice
    assert "SYR01" in sku_map  # Rooh Afza
    assert "SYR02" in sku_map  # Glucon-D

    total_locked = sum(i["impact_inr"] for i in items)
    assert total_locked == pytest.approx(45556, rel=0.005)


def test_planted_insight_3_margin_leak():
    """Planted Insight 3: Margin leak on Fortune Sunflower Oil (OIL01).
    Cost rose 128 -> 141; margin fell 10.4% -> 1.3%.
    Action must NEVER recommend raising price; recommends negotiating cost or substitute OIL02.
    """
    items = margin_leak_insights(db=None)
    oil = next((i for i in items if "OIL01" in i["id"]), None)
    assert oil is not None

    assert oil["type"] == "margin_leak"
    assert oil["severity"] == "high"

    # Evidence check
    evidence_rows = {r[0]: (r[1], r[2]) for r in oil["evidence"]["rows"]}
    assert "Cost per unit" in evidence_rows
    assert evidence_rows["Cost per unit"] == ("128.00", "141.00")
    assert "Margin on taxable value" in evidence_rows
    assert evidence_rows["Margin on taxable value"] == ("10.4%", "1.3%")

    # Action check: NEVER raise price, recommend cost negotiation or OIL02 substitute
    action = oil["action"]
    payload = action["payload"]
    rec = payload.get("recommendation", "").lower()

    assert "raise price" not in rec or "do not raise price" in rec
    assert "oil02" in rec or "saffola" in rec
    assert "gupta" in rec or "negotiate" in rec
    assert payload.get("substitute_sku") == "OIL02"


def test_planted_insight_4_expense_anomaly():
    """Planted Insight 4: Expense anomaly for Electricity (Oct Rs 9,718) and Delivery Fuel (Oct Rs 5,100)."""
    items = expense_anomaly_insights(db=None)
    cat_map = {i["action"]["payload"]["category"]: i for i in items}

    assert "Electricity" in cat_map
    assert "Delivery Fuel" in cat_map

    elec = cat_map["Electricity"]
    assert elec["action"]["payload"]["month"] == "2026-10"
    assert "9,718" in elec["title"] or elec["evidence"]["rows"][0][2] == "Rs 9,718"

    # Check note carried in evidence
    note_row = next((r for r in elec["evidence"]["rows"] if r[0] == "Note"), None)
    assert note_row is not None
    assert "Compressor fault - high bill" in note_row[2]


def test_planted_insight_5_khata_overdue():
    """Planted Insight 5: Khata overdue >45d (7 customers, total Rs 31,369).
    C003 and C010 flagged over credit limit.
    """
    items = khata_overdue_insights(db=None)
    cust_map = {i["action"]["payload"]["customer_id"]: i for i in items}

    assert len(items) == 7
    assert sum(i["impact_inr"] for i in items) == 31369.0

    # Top customer: C003 Anil Gupta
    assert "C003" in cust_map
    c003 = cust_map["C003"]
    assert c003["severity"] == "high"
    assert c003["action"]["kind"] == "whatsapp_reminder"

    # Check over credit limit in evidence for C003 and C010
    for cid in ["C003", "C010"]:
        over_row = next((r for r in cust_map[cid]["evidence"]["rows"] if r[0] == "Over Credit Limit"), None)
        assert over_row is not None and over_row[1] == "Yes"


def test_planted_insight_6_festive_lift():
    """Planted Insight 6: Festive lift for Diwali week vs 18-24 Oct baseline.
    Dry Fruits ~4.1x, Puja & Decor ~4.0x, Sweets ~2.9x.
    """
    items = festive_lift_insights(db=None)
    assert len(items) >= 1
    fl = items[0]

    assert fl["type"] == "festive_lift"
    ev_rows = {r[0]: (r[1], r[2], r[3]) for r in fl["evidence"]["rows"]}

    assert "Dry Fruits" in ev_rows
    assert "Puja & Decor" in ev_rows
    assert "Sweets & Chocolates" in ev_rows

    assert "4.1x" in ev_rows["Dry Fruits"][2]
    assert "4.0x" in ev_rows["Puja & Decor"][2]
    assert "2.9x" in ev_rows["Sweets & Chocolates"][2]
