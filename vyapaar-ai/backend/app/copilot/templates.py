"""backend/app/copilot/templates.py
Deterministic answer templates per tool.
Used directly by fallback router or when LLM output fails numeric validation.
Formats currency using Indian grouping (Rs 14,32,103).
"""
from typing import Any, Dict, List, Optional


def format_inr(val: float) -> str:
    """Formats numeric values into Indian rupee grouping (e.g. 14,32,103)."""
    v = round(val)
    s = str(abs(v))
    if len(s) <= 3:
        res = s
    else:
        last3 = s[-3:]
        rest = s[:-3]
        groups = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        res = ",".join(groups) + "," + last3
    return ("-" if v < 0 else "") + res


def render_compare_periods_template(data: Dict[str, Any]) -> str:
    val_a = format_inr(data["period_a"]["value"])
    val_b = format_inr(data["period_b"]["value"])
    delta_pct = data["delta_pct"]
    sign = "+" if delta_pct > 0 else ""

    breakdown = data.get("breakdown", [])
    top_contribs = [b.get("category", "") for b in breakdown[:3] if b.get("category")]
    contrib_str = f" The biggest contributors were {', '.join(top_contribs)}." if top_contribs else ""

    return (
        f"Diwali week revenue was Rs {val_a} vs Rs {val_b} the prior week ({sign}{delta_pct:.1f}%)."
        f"{contrib_str}"
    )


def render_stock_status_template(data: Any) -> str:
    items = data if isinstance(data, list) else data.get("items", [data])
    out_items = [i["name"] for i in items if i.get("status") == "OUT"]
    crit_items = [i["name"] for i in items if i.get("status") == "CRITICAL"]

    parts = []
    if out_items:
        parts.append(f"{', '.join(out_items)} (out)")
    if crit_items:
        parts.append(f"{', '.join(crit_items)} (critical)")

    summary = " and ".join(parts) if parts else "No critical restock items found."
    return (
        f"Items running out or low: {summary}. "
        f"Puja & Decor items (Diyas, Rangoli, Tealights, Agarbatti) are festival-over and excluded."
    )


def render_dead_stock_template(data: Dict[str, Any]) -> str:
    count = data.get("sku_count", 0)
    capital = format_inr(data.get("capital_locked", 0.0))
    items = data.get("items", [])
    names = [i["name"] for i in items]
    names_str = f": {', '.join(names)}" if names else ""

    return f"{count} products are dead stock with Rs {capital} capital locked{names_str}."


def render_khata_overdue_template(data: Dict[str, Any], total_outstanding: Optional[float] = None) -> str:
    count = data.get("customer_count", 0)
    overdue_amt = format_inr(data.get("total_overdue", 0.0))
    customers = data.get("customers", [])

    tot_val = total_outstanding if total_outstanding is not None else data.get("total_outstanding")
    tot_str = f"Total outstanding Rs {format_inr(tot_val)}; " if tot_val is not None else ""

    top_str = ""
    if customers:
        top_c = customers[0]
        top_str = f" Top debtor is {top_c['name']} owing Rs {format_inr(top_c['balance'])} ({top_c['days_since_payment']} days overdue)."

    return f"{tot_str}{count} customers owe Rs {overdue_amt} overdue for more than 45 days.{top_str}".strip()


def render_margin_leak_template(data: Any) -> str:
    leaks = data if isinstance(data, list) else data.get("data", [])
    if leaks:
        item = leaks[0]
        return (
            f"Why margin on cooking oil dropped: {item['name']} purchase cost rose from Rs {item['old_cost']:.0f} to "
            f"Rs {item['latest_cost']:.0f}, dropping margin on taxable value from {item['old_margin_pct']:.1f}% to "
            f"{item['new_margin_pct']:.1f}% (price is capped at MRP Rs {item['mrp']:.0f})."
        )
    return "No significant margin leaks detected."


def render_expense_summary_template(data: Dict[str, Any]) -> str:
    anomalies = data.get("anomalies", [])
    if not anomalies:
        return "No expense anomalies detected."

    parts = []
    for a in anomalies:
        parts.append(
            f"{a['category']} (Oct Rs {format_inr(a['amount'])} vs median Rs {format_inr(a['median_other_months'])})"
        )
    return f"Unusual expenses detected: {', '.join(parts)}."


def render_payment_mix_template(data: Any) -> str:
    items = data if isinstance(data, list) else data.get("data", [])
    mode_map = {i["payment_mode"].lower(): i.get("share_pct", 0.0) for i in items if "payment_mode" in i}

    upi = mode_map.get("upi", 0.0)
    cash = mode_map.get("cash", 0.0)
    card = mode_map.get("card", 0.0)
    khata = mode_map.get("khata", 0.0)

    return f"Payment mix in the last 30 days: UPI {upi:.1f}%, cash {cash:.1f}%, card {card:.1f}%, khata {khata:.1f}%."


def render_sales_summary_template(data: Dict[str, Any]) -> str:
    rev = format_inr(data.get("revenue", 0.0))
    profit = format_inr(data.get("gross_profit", 0.0))
    margin = data.get("gross_margin_pct", 0.0)
    invoices = data.get("invoices", 0)
    return f"Sales summary: Revenue Rs {rev}, Gross profit Rs {profit} ({margin:.2f}% margin), {invoices} invoices."


def render_unsupported_template() -> str:
    return (
        "I cannot answer that question yet. Here are 3 supported questions you can ask me:\n"
        "1. How did Diwali week go compared to the week before?\n"
        "2. Which items will run out in the next 3 days?\n"
        "3. Who owes me money for more than 45 days?"
    )
