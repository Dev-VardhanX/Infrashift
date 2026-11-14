"""backend/app/analytics/restock_plan.py
Tool: restock_plan(db, horizon_days)
Generates suggested restock quantities per SKU grouped by supplier.
Alerts only on OUT, CRITICAL, and LOW items.
Excludes OK and FESTIVAL_OVER items.
"""
from collections import defaultdict
from typing import Any, Dict, Optional
from app.analytics.stock_status import stock_status
from app.analytics.periods import get_as_of


def restock_plan(
    db: Optional[Any] = None,
    horizon_days: int = 7,
) -> Dict[str, Any]:
    """Generates suggested restock quantities per SKU grouped by supplier."""
    status_res = stock_status(db=db)
    all_items = status_res["data"]
    as_of = status_res["meta"]["as_of"]

    if not isinstance(all_items, list):
        all_items = [all_items] if all_items else []

    # Filter only OUT, CRITICAL, LOW
    restock_items = [
        item for item in all_items
        if item["status"] in ("OUT", "CRITICAL", "LOW")
    ]

    by_supplier = defaultdict(list)
    for item in restock_items:
        supplier = item.get("supplier") or "Unknown"
        by_supplier[supplier].append({
            "sku": item["sku"],
            "name": item["name"],
            "stock": item["stock"],
            "daily_demand": item["daily_demand"],
            "days_of_cover": item["days_of_cover"],
            "lead_time_days": item["lead_time_days"],
            "status": item["status"],
            "suggested_qty": item["suggested_qty"],
        })

    return {
        "data": {
            "items": restock_items,
            "by_supplier": dict(by_supplier),
            "total_items": len(restock_items),
        },
        "meta": {
            "method": f"Generated restock plan for horizon {horizon_days}d grouped by supplier (excluding FESTIVAL_OVER)",
            "row_count": len(restock_items),
            "as_of": as_of,
        },
    }
