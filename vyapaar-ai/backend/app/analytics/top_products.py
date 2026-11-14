"""backend/app/analytics/top_products.py
Tool: top_products(db, metric, n, from_date, to_date, order)
Ranks SKUs by revenue, profit, units sold, or margin %.
"""
from typing import Any, Dict, Optional
from app.analytics._data import get_enriched_sales
from app.analytics.periods import resolve_period, get_as_of


def top_products(
    db: Optional[Any] = None,
    metric: str = "revenue",
    n: int = 5,
    from_date: str = "last_30d",
    to_date: Optional[str] = None,
    order: str = "top",
) -> Dict[str, Any]:
    """Returns top or bottom ranked products by metric in {revenue, profit, units, margin}."""
    as_of = get_as_of(db)
    start_date, end_date = resolve_period(from_date, to_date, db=db, as_of=as_of)
    df = get_enriched_sales(db)

    mask = (df["date"] >= start_date) & (df["date"] <= end_date)
    period_df = df[mask].copy()

    total_rows = len(period_df)
    if total_rows == 0:
        return {
            "data": [],
            "meta": {
                "method": f"Ranked products by {metric} ({order} {n})",
                "row_count": 0,
                "as_of": as_of.strftime("%Y-%m-%d"),
            },
        }

    # Group by SKU and product info
    group_cols = ["sku", "name"]
    if "category" in period_df.columns:
        group_cols.append("category")

    grouped = []
    for keys, grp in period_df.groupby(group_cols):
        sku = keys[0]
        name = keys[1]
        cat = keys[2] if len(keys) > 2 else ""

        rev = round(float(grp["rev"].sum()), 2)
        taxable = round(float(grp["taxable"].sum()), 2)
        gst = round(float(grp["gst"].sum()), 2)
        cogs = round(float(grp["cogs"].sum()), 2)
        profit = round(float(grp["profit"].sum()), 2)
        margin_pct = round(100.0 * profit / taxable, 2) if taxable > 0 else 0.0
        units = int(grp["qty"].sum())

        grouped.append({
            "sku": sku,
            "name": name,
            "category": cat,
            "revenue": rev,
            "taxable": taxable,
            "gst": gst,
            "cogs": cogs,
            "profit": profit,
            "margin_pct": margin_pct,
            "units": units,
        })

    metric_key = metric.lower()
    if metric_key in ("margin", "margin_pct", "gross_margin_pct"):
        sort_col = "margin_pct"
    elif metric_key in ("profit", "gross_profit"):
        sort_col = "profit"
    elif metric_key in ("units", "qty"):
        sort_col = "units"
    else:
        sort_col = "revenue"

    ascending = (order.lower() == "bottom")
    grouped.sort(key=lambda x: x[sort_col], reverse=not ascending)

    data = grouped[:n] if n is not None else grouped

    return {
        "data": data,
        "meta": {
            "method": f"Ranked products by {sort_col} ({order} {n}) over {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            "row_count": total_rows,
            "as_of": as_of.strftime("%Y-%m-%d"),
        },
    }
