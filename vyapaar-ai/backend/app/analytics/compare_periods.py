"""backend/app/analytics/compare_periods.py
Tool: compare_periods(db, metric, a_from, a_to, b_from, b_to, group_by)
Compares metric performance between two periods (Period A vs Period B).
Calculates value_a, value_b, delta, delta_pct, and group breakdown if requested.
"""
from typing import Any, Dict, Optional
from app.analytics._data import get_enriched_sales
from app.analytics.periods import resolve_period, get_as_of


def compare_periods(
    db: Optional[Any] = None,
    metric: str = "revenue",
    a_from: str = "diwali_week",
    a_to: Optional[str] = None,
    b_from: str = "prior_week",
    b_to: Optional[str] = None,
    group_by: Optional[str] = None,
) -> Dict[str, Any]:
    """Compares metric performance between two periods."""
    as_of = get_as_of(db)
    a_start, a_end = resolve_period(a_from, a_to, db=db, as_of=as_of)
    b_start, b_end = resolve_period(b_from, b_to, db=db, as_of=as_of)

    df = get_enriched_sales(db)

    mask_a = (df["date"] >= a_start) & (df["date"] <= a_end)
    mask_b = (df["date"] >= b_start) & (df["date"] <= b_end)

    df_a = df[mask_a].copy()
    df_b = df[mask_b].copy()

    def calc_metric(sub_df: Any, met: str) -> float:
        if len(sub_df) == 0:
            return 0.0
        m = met.lower()
        if m in ("revenue", "rev"):
            return round(float(sub_df["rev"].sum()), 2)
        if m == "taxable":
            return round(float(sub_df["taxable"].sum()), 2)
        if m in ("profit", "gross_profit"):
            return round(float(sub_df["profit"].sum()), 2)
        if m in ("units", "qty"):
            return int(sub_df["qty"].sum())
        if m == "invoices":
            return int(sub_df["invoice_id"].nunique())
        return round(float(sub_df["rev"].sum()), 2)

    val_a = calc_metric(df_a, metric)
    val_b = calc_metric(df_b, metric)
    delta = round(val_a - val_b, 2)
    delta_pct = round(100.0 * (val_a - val_b) / val_b, 1) if val_b > 0 else 0.0

    breakdown = []
    if group_by:
        all_keys = set()
        if group_by in df_a.columns:
            all_keys.update(df_a[group_by].dropna().unique())
        if group_by in df_b.columns:
            all_keys.update(df_b[group_by].dropna().unique())

        for k in all_keys:
            sub_a = df_a[df_a[group_by] == k]
            sub_b = df_b[df_b[group_by] == k]
            g_a = calc_metric(sub_a, metric)
            g_b = calc_metric(sub_b, metric)
            g_delta = round(g_a - g_b, 2)
            g_delta_pct = round(100.0 * (g_a - g_b) / g_b, 1) if g_b > 0 else 0.0
            breakdown.append({
                group_by: k,
                "value_a": g_a,
                "value_b": g_b,
                "delta": g_delta,
                "delta_pct": g_delta_pct,
            })
        breakdown.sort(key=lambda x: x["delta"], reverse=True)

    data = {
        "metric": metric,
        "period_a": {
            "from": a_start.strftime("%Y-%m-%d"),
            "to": a_end.strftime("%Y-%m-%d"),
            "value": val_a,
        },
        "period_b": {
            "from": b_start.strftime("%Y-%m-%d"),
            "to": b_end.strftime("%Y-%m-%d"),
            "value": val_b,
        },
        "delta": delta,
        "delta_pct": delta_pct,
    }
    if breakdown:
        data["breakdown"] = breakdown

    return {
        "data": data,
        "meta": {
            "method": f"Compared {metric} between [{a_start.strftime('%Y-%m-%d')}..{a_end.strftime('%Y-%m-%d')}] and [{b_start.strftime('%Y-%m-%d')}..{b_end.strftime('%Y-%m-%d')}]",
            "row_count": len(df_a) + len(df_b),
            "as_of": as_of.strftime("%Y-%m-%d"),
        },
    }
