"""backend/app/analytics/dead_stock.py
Tool: dead_stock(db, days, max_sell_through)
Finds items where current_stock > 0 and units sold in last 30 days <= 5% of current stock,
excluding seasonal Puja & Decor items.
"""
from typing import Any, Dict, Optional
import pandas as pd
from app.analytics._data import get_data
from app.analytics.periods import get_as_of


def dead_stock(
    db: Optional[Any] = None,
    days: int = 30,
    max_sell_through: float = 0.05,
) -> Dict[str, Any]:
    """Identifies dead stock and capital locked."""
    data = get_data(db)
    inventory = data["inventory"]
    products = data["products"]
    sales = data["sales"]

    if inventory.empty or products.empty:
        return {
            "data": {"items": [], "capital_locked": 0.0, "sku_count": 0},
            "meta": {
                "method": f"Identified dead stock over last {days}d (<= {int(max_sell_through*100)}% sell-through)",
                "row_count": 0,
                "as_of": "1970-01-01",
            },
        }

    as_of = get_as_of(db)
    window_start = as_of - pd.Timedelta(days=days - 1)

    # Units sold in window
    if not sales.empty:
        w_sales = sales[(sales["date"] >= window_start) & (sales["date"] <= as_of)]
        units_sold = w_sales.groupby("sku")["qty"].sum().to_dict()
    else:
        units_sold = {}

    cols = ["sku", "name", "category", "cost_price"]
    available_cols = [c for c in cols if c in products.columns]
    inv = inventory.merge(products[available_cols], on="sku", how="left")

    items = []
    total_capital_locked = 0.0

    for _, row in inv.iterrows():
        sku = row["sku"]
        stock = float(row.get("current_stock", 0))
        cat = row.get("category", "")
        cost = float(row.get("cost_price", 0))

        if stock <= 0:
            continue
        if cat == "Puja & Decor":
            continue

        sold = int(units_sold.get(sku, 0))
        threshold = max_sell_through * stock

        if sold <= threshold:
            val = round(stock * cost, 2)
            total_capital_locked += val
            items.append({
                "sku": sku,
                "name": row.get("name", sku),
                "category": cat,
                "current_stock": int(stock),
                "units_sold": sold,
                "cost_price": cost,
                "capital_locked": val,
            })

    items.sort(key=lambda x: x["capital_locked"], reverse=True)

    return {
        "data": {
            "items": items,
            "capital_locked": round(total_capital_locked, 2),
            "sku_count": len(items),
        },
        "meta": {
            "method": f"Identified dead stock with <= {max_sell_through*100:.1f}% sell-through in last {days}d excluding seasonal items",
            "row_count": len(items),
            "as_of": as_of.strftime("%Y-%m-%d"),
        },
    }
