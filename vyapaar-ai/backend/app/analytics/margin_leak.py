"""backend/app/analytics/margin_leak.py
Tool: margin_leak(db, min_pp_drop)
Detects margin leakage where margin at latest purchase cost fell >= min_pp_drop (default 5.0 pp)
compared to average purchase cost from 60+ days ago.
Uses taxable value (price / (1 + gst_rate/100)), NOT MRP.
"""
from typing import Any, Dict, List, Optional
import pandas as pd
from app.analytics._data import get_data
from app.analytics.periods import get_as_of


def margin_leak(
    db: Optional[Any] = None,
    min_pp_drop: float = 5.0,
) -> Dict[str, Any]:
    """Identifies products where latest purchase cost compressed margins by >= min_pp_drop percentage points."""
    data = get_data(db)
    purchases = data["purchases"]
    products = data["products"]
    sales = data["sales"]

    if purchases.empty or products.empty:
        return {
            "data": [],
            "meta": {
                "method": f"Checked margin compression >= {min_pp_drop}pp",
                "row_count": 0,
                "as_of": get_as_of(db).strftime("%Y-%m-%d") if not sales.empty else "1970-01-01",
            },
        }

    as_of = get_as_of(db)
    pu = purchases.copy()
    pu["date"] = pd.to_datetime(pu["date"])
    pu["val"] = pu["qty"] * pu["unit_cost"]

    # Filter sales for last 30d to compute rupee impact
    l30_start = as_of - pd.Timedelta(days=29)
    if not sales.empty:
        s30 = sales[(sales["date"] >= l30_start) & (sales["date"] <= as_of)].copy()
        s30 = s30.merge(products[["sku", "gst_rate"]], on="sku", how="left")
        s30["rev"] = s30["qty"] * s30["unit_price"]
        s30["taxable"] = s30["rev"] / (1 + s30["gst_rate"] / 100)
        taxable_by_sku = s30.groupby("sku")["taxable"].sum().to_dict()
        units_by_sku = s30.groupby("sku")["qty"].sum().to_dict()
    else:
        taxable_by_sku = {}
        units_by_sku = {}

    leaks: List[Dict[str, Any]] = []

    for sku, grp in pu.groupby("sku"):
        grp = grp.sort_values("date")
        latest_row = grp.iloc[-1]
        latest_cost = float(latest_row["unit_cost"])
        latest_date = latest_row["date"]

        # Purchases 60+ days before AS_OF
        old_pu = grp[grp["date"] <= as_of - pd.Timedelta(days=60)]
        if old_pu.empty:
            continue

        old_qty = old_pu["qty"].sum()
        if old_qty <= 0:
            continue
        old_cost = float(old_pu["val"].sum() / old_qty)

        prod_rows = products[products["sku"] == sku]
        if prod_rows.empty:
            continue
        prod = prod_rows.iloc[0]
        mrp = float(prod.get("mrp", 0))
        gst_rate = float(prod.get("gst_rate", 0))

        taxable_price = mrp / (1 + gst_rate / 100)
        if taxable_price <= 0:
            continue

        old_margin_pct = round(((taxable_price - old_cost) / taxable_price) * 100, 2)
        new_margin_pct = round(((taxable_price - latest_cost) / taxable_price) * 100, 2)
        pp_drop = round(old_margin_pct - new_margin_pct, 2)

        if pp_drop >= min_pp_drop:
            taxable_30d = float(taxable_by_sku.get(sku, 0.0))
            units_30d = int(units_by_sku.get(sku, 0))
            impact_inr = round((pp_drop / 100.0) * taxable_30d, 2)

            leaks.append({
                "sku": sku,
                "name": prod.get("name", sku),
                "category": prod.get("category", ""),
                "supplier": prod.get("supplier", latest_row.get("supplier", "")),
                "mrp": mrp,
                "gst_rate": gst_rate,
                "taxable_price": round(taxable_price, 2),
                "old_cost": round(old_cost, 2),
                "latest_cost": round(latest_cost, 2),
                "latest_purchase_date": latest_date.strftime("%Y-%m-%d"),
                "old_margin_pct": old_margin_pct,
                "new_margin_pct": new_margin_pct,
                "pp_drop": pp_drop,
                "units_30d": units_30d,
                "taxable_30d": round(taxable_30d, 2),
                "impact_inr": impact_inr,
            })

    leaks.sort(key=lambda x: x["impact_inr"], reverse=True)

    return {
        "data": leaks,
        "meta": {
            "method": f"Identified margin leaks where latest cost margin dropped >= {min_pp_drop}pp vs 60d+ baseline",
            "row_count": len(leaks),
            "as_of": as_of.strftime("%Y-%m-%d"),
        },
    }
