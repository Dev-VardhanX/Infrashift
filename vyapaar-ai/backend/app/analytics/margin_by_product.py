"""backend/app/analytics/margin_by_product.py
Tool: margin_by_product(db, from_date, to_date, n)
Calculates gross margin % per SKU using taxable value (price / (1 + gst_rate/100))
and weighted-average purchase cost in the 60 days before sale date (fallback products.cost_price).
"""
from typing import Any, Dict, Optional
from app.analytics._data import get_enriched_sales, get_data
from app.analytics.periods import resolve_period, get_as_of


def margin_by_product(
    db: Optional[Any] = None,
    from_date: str = "last_30d",
    to_date: Optional[str] = None,
    n: Optional[int] = None,
) -> Dict[str, Any]:
    """Returns margin % and cost basis per SKU."""
    as_of = get_as_of(db)
    start_date, end_date = resolve_period(from_date, to_date, db=db, as_of=as_of)
    df = get_enriched_sales(db)
    raw_data = get_data(db)
    products = raw_data["products"]

    mask = (df["date"] >= start_date) & (df["date"] <= end_date)
    period_df = df[mask].copy()

    total_rows = len(period_df)
    results = []

    # Map product info
    prod_meta = {
        row["sku"]: row for _, row in products.iterrows()
    }

    if not period_df.empty:
        for sku, grp in period_df.groupby("sku"):
            p_info = prod_meta.get(sku, {})
            name = p_info.get("name", grp["name"].iloc[0] if "name" in grp.columns else sku)
            cat = p_info.get("category", grp["category"].iloc[0] if "category" in grp.columns else "")
            gst_rate = p_info.get("gst_rate", grp["gst_rate"].iloc[0] if "gst_rate" in grp.columns else 0.0)

            units = int(grp["qty"].sum())
            rev = round(float(grp["rev"].sum()), 2)
            taxable = round(float(grp["taxable"].sum()), 2)
            cogs = round(float(grp["cogs"].sum()), 2)
            profit = round(float(grp["profit"].sum()), 2)
            margin_pct = round(100.0 * profit / taxable, 2) if taxable > 0 else 0.0
            avg_unit_cost = round(cogs / units, 2) if units > 0 else 0.0

            results.append({
                "sku": sku,
                "name": name,
                "category": cat,
                "gst_rate": gst_rate,
                "units": units,
                "revenue": rev,
                "taxable": taxable,
                "cogs": cogs,
                "avg_unit_cost": avg_unit_cost,
                "profit": profit,
                "margin_pct": margin_pct,
                "cost_basis": "60d weighted purchase avg (fallback cost_price)",
            })

    # Sort by margin_pct descending
    results.sort(key=lambda x: x["margin_pct"], reverse=True)
    data = results[:n] if n is not None else results

    return {
        "data": data,
        "meta": {
            "method": "Computed product margin % using taxable value and 60-day purchase cost fallback",
            "row_count": total_rows,
            "as_of": as_of.strftime("%Y-%m-%d"),
        },
    }
