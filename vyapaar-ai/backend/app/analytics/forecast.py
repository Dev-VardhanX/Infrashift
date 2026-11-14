"""backend/app/analytics/forecast.py
Demand forecasting per docs/02 section 6.1.
Interface: daily_demand(sku, db) -> float
Formula:
- recent = mean daily units over last 14 days
- mean_28d = mean daily units over last 28 days
- base = mean daily units over 60-day window ending 21 days before AS_OF, excluding festival window
- if category is festival-seasonal and AS_OF > event_date: daily = base * 0.5 (post-festival decay)
- else: daily = 0.6 * recent + 0.4 * mean_28d
"""
from typing import Any, Optional
import pandas as pd
from app.analytics._data import get_data
from app.analytics.periods import get_as_of, DIWALI_DATE

SEASONAL_CATEGORIES = {"Puja & Decor"}


def daily_demand(sku: str, db: Optional[Any] = None) -> float:
    """Computes daily demand forecast for a given SKU."""
    data = get_data(db)
    sales = data["sales"]
    products = data["products"]

    if sales.empty or "date" not in sales.columns:
        return 0.0

    as_of = get_as_of(db)

    # Find category
    prod_row = products[products["sku"] == sku]
    category = prod_row.iloc[0]["category"] if not prod_row.empty and "category" in prod_row.columns else ""

    sku_sales = sales[sales["sku"] == sku]
    if sku_sales.empty:
        return 0.0

    # 1. Recent: last 14 days [as_of - 13d, as_of]
    d14_start = as_of - pd.Timedelta(days=13)
    s14 = sku_sales[(sku_sales["date"] >= d14_start) & (sku_sales["date"] <= as_of)]
    recent = s14["qty"].sum() / 14.0

    # 2. Last 28 days [as_of - 27d, as_of]
    d28_start = as_of - pd.Timedelta(days=27)
    s28 = sku_sales[(sku_sales["date"] >= d28_start) & (sku_sales["date"] <= as_of)]
    mean_28d = s28["qty"].sum() / 28.0

    # 3. Base: 60-day window ending 21 days before as_of, excluding festival window
    base_end = as_of - pd.Timedelta(days=21)
    base_start = as_of - pd.Timedelta(days=80)
    fw_start = DIWALI_DATE - pd.Timedelta(days=7)
    fw_end = DIWALI_DATE - pd.Timedelta(days=1)

    s_base = sku_sales[(sku_sales["date"] >= base_start) & (sku_sales["date"] <= base_end)]
    # Exclude festival window if within window
    s_base_clean = s_base[~((s_base["date"] >= fw_start) & (s_base["date"] <= fw_end))]
    base = s_base_clean["qty"].sum() / 60.0

    # Post-festival decay for seasonal categories
    if category in SEASONAL_CATEGORIES and as_of > DIWALI_DATE:
        demand = base * 0.5
    else:
        demand = 0.6 * recent + 0.4 * mean_28d

    return round(float(demand), 2)
