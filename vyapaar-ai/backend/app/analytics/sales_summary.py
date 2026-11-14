"""backend/app/analytics/sales_summary.py
Tool: sales_summary(db, from_date, to_date, group_by)
Computes revenue, taxable value, GST, gross profit, margin %, units, and invoices.
Gross margin uses taxable value (price / (1 + gst_rate/100)), not MRP.
COGS uses 60-day weighted-average purchase cost with fallback to products.cost_price.
"""
from typing import Any, Dict, Optional
import pandas as pd
from app.analytics._data import get_enriched_sales
from app.analytics.periods import resolve_period, get_as_of


def sales_summary(
    db: Optional[Any] = None,
    from_date: str = "last_30d",
    to_date: Optional[str] = None,
    group_by: Optional[str] = None,
) -> Dict[str, Any]:
    """Summarizes sales performance over the requested period.
    Returns:
    {
        "data": dict or list of dicts,
        "meta": {"method": str, "row_count": int, "as_of": str}
    }
    """
    as_of = get_as_of(db)
    start_date, end_date = resolve_period(from_date, to_date, db=db, as_of=as_of)
    df = get_enriched_sales(db)

    # Filter by period
    mask = (df["date"] >= start_date) & (df["date"] <= end_date)
    period_df = df[mask].copy()

    total_rows = len(period_df)
    total_rev = period_df["rev"].sum() if total_rows > 0 else 0.0

    if group_by is None:
        if total_rows == 0:
            data = {
                "revenue": 0.0,
                "taxable": 0.0,
                "gst": 0.0,
                "gross_profit": 0.0,
                "gross_margin_pct": 0.0,
                "invoices": 0,
                "avg_bill": 0.0,
                "units": 0,
            }
        else:
            rev = round(float(period_df["rev"].sum()), 2)
            taxable = round(float(period_df["taxable"].sum()), 2)
            gst = round(float(period_df["gst"].sum()), 2)
            profit = round(float(period_df["profit"].sum()), 2)
            margin_pct = round(100.0 * profit / taxable, 2) if taxable > 0 else 0.0
            invoices = int(period_df["invoice_id"].nunique())
            avg_bill = round(rev / invoices, 1) if invoices > 0 else 0.0
            units = int(period_df["qty"].sum())

            data = {
                "revenue": rev,
                "taxable": taxable,
                "gst": gst,
                "gross_profit": profit,
                "gross_margin_pct": margin_pct,
                "invoices": invoices,
                "avg_bill": avg_bill,
                "units": units,
            }
    else:
        # Handle group_by (e.g. payment_mode, category, day, week, month, sku)
        if group_by == "day":
            period_df["_grp"] = period_df["date"].dt.strftime("%Y-%m-%d")
        elif group_by == "week":
            period_df["_grp"] = period_df["date"].dt.to_period("W").astype(str)
        elif group_by == "month":
            period_df["_grp"] = period_df["date"].dt.strftime("%Y-%m")
        else:
            if group_by not in period_df.columns:
                raise ValueError(f"Unknown group_by field: {group_by}")
            period_df["_grp"] = period_df[group_by]

        results = []
        for grp_val, grp in period_df.groupby("_grp"):
            rev = round(float(grp["rev"].sum()), 2)
            taxable = round(float(grp["taxable"].sum()), 2)
            gst = round(float(grp["gst"].sum()), 2)
            profit = round(float(grp["profit"].sum()), 2)
            margin_pct = round(100.0 * profit / taxable, 2) if taxable > 0 else 0.0
            invoices = int(grp["invoice_id"].nunique())
            units = int(grp["qty"].sum())

            row = {
                group_by: grp_val,
                "revenue": rev,
                "taxable": taxable,
                "gst": gst,
                "gross_profit": profit,
                "gross_margin_pct": margin_pct,
                "invoices": invoices,
                "units": units,
            }
            if total_rev > 0:
                row["share_pct"] = round(100.0 * rev / total_rev, 1)
            results.append(row)
        data = sorted(results, key=lambda x: x["revenue"], reverse=True)

    return {
        "data": data,
        "meta": {
            "method": "Aggregated sales, GST, and profit from taxable values and 60-day purchase COGS fallback",
            "row_count": total_rows,
            "as_of": as_of.strftime("%Y-%m-%d"),
        },
    }
