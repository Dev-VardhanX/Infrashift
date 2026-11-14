"""backend/app/analytics/stock_status.py
Tool: stock_status(db, sku)
Evaluates inventory status (OUT, CRITICAL, LOW, OK, FESTIVAL_OVER) using daily_demand forecast.
"""
import math
from typing import Any, Dict, Optional, Union
import pandas as pd
from app.analytics._data import get_data
from app.analytics.periods import get_as_of, DIWALI_DATE
from app.analytics.forecast import daily_demand, SEASONAL_CATEGORIES


def stock_status(
    db: Optional[Any] = None,
    sku: Optional[str] = None,
) -> Dict[str, Any]:
    """Returns current stock status, daily demand, days of cover, and suggested restock."""
    data = get_data(db)
    inventory = data["inventory"]
    products = data["products"]
    sales = data["sales"]

    if inventory.empty or products.empty:
        return {
            "data": {} if sku else [],
            "meta": {
                "method": "Evaluated stock status and days of cover",
                "row_count": 0,
                "as_of": get_as_of(db).strftime("%Y-%m-%d") if not sales.empty else "1970-01-01",
            },
        }

    as_of = get_as_of(db)

    # Merge inventory with product catalog
    cols = ["sku", "name", "category", "supplier", "lead_time_days", "reorder_level", "cost_price"]
    available_cols = [c for c in cols if c in products.columns]
    merged = inventory.merge(products[available_cols], on="sku", how="left")

    if sku:
        merged = merged[merged["sku"] == sku]

    safety_days = 2
    horizon_days = 7
    items = []

    for _, row in merged.iterrows():
        s_id = row["sku"]
        name = row.get("name", s_id)
        cat = row.get("category", "")
        supplier = row.get("supplier", "")
        lead_time = int(row.get("lead_time_days", 2))
        stock = float(row.get("current_stock", 0))

        # Calculate forecast daily demand
        daily = daily_demand(s_id, db=db)
        cover = round(stock / daily, 2) if daily > 0 else (0.0 if stock == 0 else 999.0)

        # Recent 14-day units sold for evidence
        d14_start = as_of - pd.Timedelta(days=13)
        sold_14d = int(sales[(sales["sku"] == s_id) & (sales["date"] >= d14_start) & (sales["date"] <= as_of)]["qty"].sum()) if not sales.empty else 0

        # Status rules per doc 02 section 6.2
        seasonal_note = None
        if cat in SEASONAL_CATEGORIES and as_of > DIWALI_DATE:
            status = "FESTIVAL_OVER"
            seasonal_note = "Festival over, do not reorder"
            suggested = 0
        elif stock == 0 and daily > 0.5:
            status = "OUT"
            suggested = max(0, math.ceil(daily * (lead_time + safety_days + horizon_days)))
        elif cover < lead_time:
            status = "CRITICAL"
            suggested = max(0, math.ceil(daily * (lead_time + safety_days + horizon_days)) - int(stock))
        elif cover < (lead_time + safety_days):
            status = "LOW"
            suggested = max(0, math.ceil(daily * (lead_time + safety_days + horizon_days)) - int(stock))
        else:
            status = "OK"
            suggested = 0

        items.append({
            "sku": s_id,
            "name": name,
            "category": cat,
            "supplier": supplier,
            "stock": int(stock),
            "daily_demand": daily,
            "days_of_cover": cover,
            "lead_time_days": lead_time,
            "status": status,
            "suggested_qty": suggested,
            "seasonal_note": seasonal_note,
            "evidence": f"Sold {sold_14d} units in last 14 days",
        })

    result_data: Union[Dict[str, Any], list] = items[0] if (sku and items) else ({} if sku else items)

    return {
        "data": result_data,
        "meta": {
            "method": "Evaluated stock status, daily demand forecast, and days of cover",
            "row_count": len(items),
            "as_of": as_of.strftime("%Y-%m-%d"),
        },
    }
