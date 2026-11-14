"""backend/app/analytics/festive_lift.py
Tool: festive_lift(db, category, event_date, window_days)
Computes festive surge by comparing revenue and units in the festival window (e.g. 1-7 Nov)
against the non-festive baseline window (e.g. 18-24 Oct).
"""
from typing import Any, Dict, Optional, Union
import pandas as pd
from app.analytics._data import get_enriched_sales
from app.analytics.periods import get_as_of, DIWALI_DATE


def festive_lift(
    db: Optional[Any] = None,
    category: Optional[str] = None,
    event_date: Union[str, pd.Timestamp] = "2026-11-08",
    window_days: int = 7,
) -> Dict[str, Any]:
    """Measures festive lift multiplier and revenue changes during festive vs baseline windows."""
    ev_dt = pd.Timestamp(event_date if event_date is not None else DIWALI_DATE).normalize()
    as_of = get_as_of(db)
    df = get_enriched_sales(db)

    # Festive window: [event_date - window_days, event_date - 1d]
    fest_start = ev_dt - pd.Timedelta(days=window_days)
    fest_end = ev_dt - pd.Timedelta(days=1)

    # Baseline window: equal length, pre-surge baseline (ending 15 days before event_date)
    # [event_date - 3*window_days, event_date - 2*window_days - 1d] => 18-24 Oct for Diwali 8 Nov
    base_start = ev_dt - pd.Timedelta(days=3 * window_days)
    base_end = ev_dt - pd.Timedelta(days=2 * window_days + 1)

    fest_df = df[(df["date"] >= fest_start) & (df["date"] <= fest_end)]
    base_df = df[(df["date"] >= base_start) & (df["date"] <= base_end)]

    total_rows = len(fest_df) + len(base_df)

    categories_list = []
    all_cats = set(fest_df["category"].dropna().unique()).union(set(base_df["category"].dropna().unique()))

    for cat in all_cats:
        f_sub = fest_df[fest_df["category"] == cat]
        b_sub = base_df[base_df["category"] == cat]

        f_rev = round(float(f_sub["rev"].sum()), 2)
        b_rev = round(float(b_sub["rev"].sum()), 2)
        f_units = int(f_sub["qty"].sum())
        b_units = int(b_sub["qty"].sum())

        lift_x = round(f_rev / b_rev, 1) if b_rev > 0 else 0.0
        delta = round(f_rev - b_rev, 2)

        categories_list.append({
            "category": cat,
            "festive_revenue": f_rev,
            "baseline_revenue": b_rev,
            "festive_units": f_units,
            "baseline_units": b_units,
            "lift_x": lift_x,
            "delta": delta,
        })

    categories_list.sort(key=lambda x: x["lift_x"], reverse=True)

    if category:
        selected = next((c for c in categories_list if c["category"].lower() == category.lower()), None)
        data = {
            "category": category,
            "selected": selected,
            "categories": categories_list,
            "festive_window": {"from": fest_start.strftime("%Y-%m-%d"), "to": fest_end.strftime("%Y-%m-%d")},
            "baseline_window": {"from": base_start.strftime("%Y-%m-%d"), "to": base_end.strftime("%Y-%m-%d")},
        }
    else:
        data = {
            "categories": categories_list,
            "festive_window": {"from": fest_start.strftime("%Y-%m-%d"), "to": fest_end.strftime("%Y-%m-%d")},
            "baseline_window": {"from": base_start.strftime("%Y-%m-%d"), "to": base_end.strftime("%Y-%m-%d")},
        }

    return {
        "data": data,
        "meta": {
            "method": f"Compared festive window [{fest_start.strftime('%Y-%m-%d')}..{fest_end.strftime('%Y-%m-%d')}] vs baseline [{base_start.strftime('%Y-%m-%d')}..{base_end.strftime('%Y-%m-%d')}]",
            "row_count": total_rows,
            "as_of": as_of.strftime("%Y-%m-%d"),
        },
    }
