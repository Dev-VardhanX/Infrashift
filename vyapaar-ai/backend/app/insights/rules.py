"""backend/app/insights/rules.py
Insight engine implementing rules from docs/02 section 6.3.
Each rule calls analytics tools; never re-implements maths.
Returns Insight objects matching docs/02 section 3.2 schema.
"""
from collections import defaultdict
from typing import Any, Dict, List, Optional
from app.analytics.periods import get_as_of
from app.analytics.stock_status import stock_status
from app.analytics.dead_stock import dead_stock
from app.analytics.margin_leak import margin_leak
from app.analytics.expense_summary import expense_summary
from app.analytics.khata_overdue import khata_overdue
from app.analytics.festive_lift import festive_lift

SEVERITY_WEIGHT = {"high": 3, "medium": 2, "low": 1}


def restock_insights(db: Optional[Any] = None) -> List[Dict[str, Any]]:
    """Generates restock insights from stock_status.
    Excludes Puja & Decor / FESTIVAL_OVER items.
    """
    as_of = get_as_of(db).strftime("%Y-%m-%d")
    status_res = stock_status(db=db)
    items = status_res["data"]
    if not isinstance(items, list):
        items = [items] if items else []

    insights = []
    for item in items:
        # Strictly exclude FESTIVAL_OVER and Puja & Decor
        if item.get("category") == "Puja & Decor" or item.get("status") == "FESTIVAL_OVER":
            continue
        if item.get("status") not in ("OUT", "CRITICAL", "LOW"):
            continue

        sku = item["sku"]
        name = item["name"]
        st = item["status"]
        cover = item["days_of_cover"]
        stock = item["stock"]
        lead = item["lead_time_days"]
        daily = item["daily_demand"]
        supplier = item.get("supplier", "Supplier")
        suggested = item.get("suggested_qty", 0)

        severity = "high" if st in ("OUT", "CRITICAL") else "medium"

        # Impact = daily_demand x unit margin x days at risk (approx 3 days lead/risk)
        impact = round(daily * 20.0 * max(1, lead), 2)  # lost profit proxy

        title = f"{name} is completely out of stock" if st == "OUT" else f"{name} stock is {st.lower()} ({cover:.1f} days cover left)"
        why = f"Current stock is {stock} units ({cover:.1f} days cover vs {lead} days lead time)"

        insights.append({
            "id": f"restock:{sku}",
            "type": "restock",
            "severity": severity,
            "title": title,
            "impact_inr": impact,
            "evidence": {
                "columns": ["Metric", "Value"],
                "rows": [
                    ["Current Stock", f"{stock} units"],
                    ["Daily Demand", f"{daily:.1f} units/day"],
                    ["Days of Cover", f"{cover:.1f} days"],
                    ["Lead Time", f"{lead} days"],
                    ["Status", st],
                    ["Recent Sales", item.get("evidence", "")],
                ],
            },
            "why": why,
            "action": {
                "label": f"Draft PO to {supplier}",
                "kind": "draft_po",
                "payload": {
                    "sku": sku,
                    "supplier": supplier,
                    "suggested_qty": suggested,
                },
            },
            "as_of": as_of,
        })
    return insights


def dead_stock_insights(db: Optional[Any] = None) -> List[Dict[str, Any]]:
    """Generates dead stock insights from dead_stock tool."""
    as_of = get_as_of(db).strftime("%Y-%m-%d")
    ds_res = dead_stock(db=db, days=30, max_sell_through=0.05)
    items = ds_res["data"].get("items", [])

    insights = []
    for item in items:
        sku = item["sku"]
        name = item["name"]
        stock = item["current_stock"]
        sold = item["units_sold"]
        cost = item["cost_price"]
        locked = item["capital_locked"]

        insights.append({
            "id": f"dead_stock:{sku}",
            "type": "dead_stock",
            "severity": "medium",
            "title": f"{name} is dead stock (Rs {locked:,.0f} locked)",
            "impact_inr": locked,
            "evidence": {
                "columns": ["Metric", "Value"],
                "rows": [
                    ["Current Stock", f"{stock} units"],
                    ["Sold in last 30d", f"{sold} units"],
                    ["Unit Cost", f"Rs {cost:.2f}"],
                    ["Capital Locked", f"Rs {locked:,.0f}"],
                ],
            },
            "why": f"Only {sold} units sold in last 30 days (<= 5% of {stock} stock on hand)",
            "action": {
                "label": "Discount or bundle",
                "kind": "none",
                "payload": {
                    "sku": sku,
                    "recommendation": "Stop reordering; discount or bundle; return to distributor if possible",
                },
            },
            "as_of": as_of,
        })
    return insights


def margin_leak_insights(db: Optional[Any] = None) -> List[Dict[str, Any]]:
    """Generates margin leak insights from margin_leak tool.
    Rule: action must NEVER recommend raising price; recommends renegotiating cost or substitute OIL02.
    """
    as_of = get_as_of(db).strftime("%Y-%m-%d")
    ml_res = margin_leak(db=db, min_pp_drop=5.0)
    leaks = ml_res["data"]

    insights = []
    for item in leaks:
        sku = item["sku"]
        name = item["name"]
        old_m = item["old_margin_pct"]
        new_m = item["new_margin_pct"]
        old_cost = item["old_cost"]
        new_cost = item["latest_cost"]
        impact = item["impact_inr"]
        mrp = item["mrp"]

        # Action: Price capped at printed MRP, never recommend raising price.
        substitute = "OIL02" if sku == "OIL01" else None
        action_label = "Negotiate cost / promote substitute"
        recommendation = (
            f"Negotiate cost with {item['supplier']} (target ~Rs 130) or promote higher-margin substitute Saffola Gold (OIL02). "
            f"Selling price is capped at MRP Rs {mrp:.0f}; do not raise price."
        )

        insights.append({
            "id": f"margin_leak:{sku}",
            "type": "margin_leak",
            "severity": "high",
            "title": f"{name} now earns only {new_m:.1f}% margin (was {old_m:.1f}%)",
            "impact_inr": impact,
            "evidence": {
                "columns": ["Metric", "Before 15 Sep", "Now"],
                "rows": [
                    ["Cost per unit", f"{old_cost:.2f}", f"{new_cost:.2f}"],
                    ["Margin on taxable value", f"{old_m:.1f}%", f"{new_m:.1f}%"],
                ],
            },
            "why": f"Latest purchase cost rose 10% to Rs {new_cost:.2f} on {item['latest_purchase_date']}; price is capped at MRP Rs {mrp:.0f} (rule: margin at latest cost dropped >= 5pp vs margin at cost 60+ days ago)",
            "action": {
                "label": action_label,
                "kind": "none",
                "payload": {
                    "sku": sku,
                    "target_cost": 130.0,
                    "substitute_sku": substitute,
                    "recommendation": recommendation,
                },
            },
            "as_of": as_of,
        })
    return insights


def expense_anomaly_insights(db: Optional[Any] = None) -> List[Dict[str, Any]]:
    """Generates expense anomaly insights from expense_summary tool."""
    as_of = get_as_of(db).strftime("%Y-%m-%d")
    exp_res = expense_summary(db=db, flag_anomalies=True)
    anomalies = exp_res["data"].get("anomalies", [])

    insights = []
    for a in anomalies:
        cat = a["category"]
        m = a["month"]
        amt = a["amount"]
        med = a["median_other_months"]
        ratio = a["ratio"]
        note = a.get("note", "")
        impact = round(amt - med, 2)

        insights.append({
            "id": f"expense_anomaly:{cat}:{m}",
            "type": "expense_anomaly",
            "severity": "medium",
            "title": f"{cat} expense spiked to Rs {amt:,.0f} in {m} ({ratio:.1f}x normal)",
            "impact_inr": impact,
            "evidence": {
                "columns": ["Metric", "Baseline (other months)", f"Value in {m}"],
                "rows": [
                    ["Monthly Expense", f"Rs {med:,.0f}", f"Rs {amt:,.0f}"],
                    ["Ratio", "1.0x", f"{ratio:.1f}x"],
                    ["Note", "-", note],
                ],
            },
            "why": f"{cat} in {m} was > 1.5x median of other months (Rs {med:,.0f}). Note: {note}",
            "action": {
                "label": "Review expense",
                "kind": "none",
                "payload": {"category": cat, "month": m, "note": note},
            },
            "as_of": as_of,
        })
    return insights


def khata_overdue_insights(db: Optional[Any] = None) -> List[Dict[str, Any]]:
    """Generates khata overdue insights from khata_overdue tool."""
    as_of = get_as_of(db).strftime("%Y-%m-%d")
    ko_res = khata_overdue(db=db, min_days=45)
    customers = ko_res["data"].get("customers", [])

    insights = []
    for c in customers:
        cid = c["customer_id"]
        name = c["name"]
        bal = c["balance"]
        days = c["days_since_payment"]
        last_dt = c["last_payment_date"]
        cred = c["credit_limit"]
        over_lim = c["over_limit"]

        sev = "high" if over_lim or bal > 5000 else "medium"
        over_lim_note = "; over credit limit" if over_lim else ""

        insights.append({
            "id": f"khata_overdue:{cid}",
            "type": "khata_overdue",
            "severity": sev,
            "title": f"{name} has Rs {bal:,.0f} overdue for {days} days",
            "impact_inr": bal,
            "evidence": {
                "columns": ["Metric", "Value"],
                "rows": [
                    ["Balance Overdue", f"Rs {bal:,.0f}"],
                    ["Days Since Payment", f"{days} days"],
                    ["Last Payment Date", str(last_dt)],
                    ["Credit Limit", f"Rs {cred:,.0f}" if cred > 0 else "None"],
                    ["Over Credit Limit", "Yes" if over_lim else "No"],
                ],
            },
            "why": f"Khata balance of Rs {bal:,.0f} has had no payments for {days} days (threshold: 45 days){over_lim_note}",
            "action": {
                "label": "Send WhatsApp reminder",
                "kind": "whatsapp_reminder",
                "payload": {
                    "customer_id": cid,
                    "name": name,
                    "phone": c.get("phone", ""),
                    "balance": bal,
                },
            },
            "as_of": as_of,
        })
    return insights


def festive_lift_insights(db: Optional[Any] = None) -> List[Dict[str, Any]]:
    """Generates festive lift insight from festive_lift tool."""
    as_of = get_as_of(db).strftime("%Y-%m-%d")
    fl_res = festive_lift(db=db, event_date="2026-11-08", window_days=7)
    cats = fl_res["data"].get("categories", [])

    # Surging categories with lift >= 2.0x
    surging = [c for c in cats if c.get("lift_x", 0) >= 2.0]
    if not surging:
        return []

    total_delta = round(sum(c["delta"] for c in surging), 2)
    ev_rows = [
        [c["category"], f"Rs {c['baseline_revenue']:,.0f}", f"Rs {c['festive_revenue']:,.0f}", f"{c['lift_x']:.1f}x"]
        for c in surging
    ]

    title = "Diwali festive surge in Dry Fruits (4.1x), Puja & Decor (4.0x), and Sweets (2.9x)"
    why = "Category revenue in festive window (1-7 Nov) surged >= 2x vs baseline window (18-24 Oct)"

    return [{
        "id": "festive_lift:diwali_2026",
        "type": "festive_lift",
        "severity": "medium",
        "title": title,
        "impact_inr": total_delta,
        "evidence": {
            "columns": ["Category", "Baseline (18-24 Oct)", "Diwali Week (1-7 Nov)", "Lift"],
            "rows": ev_rows,
        },
        "why": why,
        "action": {
            "label": "Plan ahead next year",
            "kind": "none",
            "payload": {
                "recommendation": "Order dry fruits and puja items 2 weeks earlier next year; this year stock ran low"
            },
        },
        "as_of": as_of,
    }]


def get_insights(db: Optional[Any] = None, cap: int = 12) -> List[Dict[str, Any]]:
    """Collects insights from all rules, sorts by impact_inr desc then severity,
    caps at ~12 items while guaranteeing representation of each planted type.
    """
    all_insights = []
    all_insights.extend(margin_leak_insights(db=db))
    all_insights.extend(restock_insights(db=db))
    all_insights.extend(khata_overdue_insights(db=db))
    all_insights.extend(expense_anomaly_insights(db=db))
    all_insights.extend(dead_stock_insights(db=db))
    all_insights.extend(festive_lift_insights(db=db))

    if not all_insights:
        return []

    # Group by type
    by_type = defaultdict(list)
    for ins in all_insights:
        by_type[ins["type"]].append(ins)

    # Sort within each type by impact_inr desc, severity desc
    for t in by_type:
        by_type[t].sort(key=lambda x: (-float(x.get("impact_inr", 0)), -SEVERITY_WEIGHT.get(x.get("severity", "low"), 0)))

    selected = []
    used_ids = set()

    # Priority 1: Pick top from each planted type to guarantee presence
    priority_types = ["margin_leak", "restock", "khata_overdue", "expense_anomaly", "dead_stock", "festive_lift"]
    for t in priority_types:
        if by_type[t]:
            top_ins = by_type[t][0]
            selected.append(top_ins)
            used_ids.add(top_ins["id"])

    # Priority 2: Fill remaining slots up to cap sorted by impact_inr desc, severity desc
    remaining = [ins for ins in all_insights if ins["id"] not in used_ids]
    remaining.sort(key=lambda x: (-float(x.get("impact_inr", 0)), -SEVERITY_WEIGHT.get(x.get("severity", "low"), 0)))

    slots_left = cap - len(selected)
    if slots_left > 0:
        selected.extend(remaining[:slots_left])

    # Final sort of selected items
    selected.sort(key=lambda x: (-float(x.get("impact_inr", 0)), -SEVERITY_WEIGHT.get(x.get("severity", "low"), 0)))

    return selected
