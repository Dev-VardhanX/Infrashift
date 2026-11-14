"""backend/app/analytics/expense_summary.py
Tool: expense_summary(db, from_date, to_date, flag_anomalies)
Summarizes expenses by category and detects monthly anomalies
(monthly category total > 1.5x median of other months and > Rs 1,000).
Carries the note column for context.
"""
from typing import Any, Dict, List, Optional
import pandas as pd
from app.analytics._data import get_data
from app.analytics.periods import resolve_period, get_as_of


def expense_summary(
    db: Optional[Any] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    flag_anomalies: bool = True,
) -> Dict[str, Any]:
    """Summarizes expenses and flags monthly category anomalies."""
    data = get_data(db)
    expenses = data["expenses"]
    sales = data["sales"]

    if expenses.empty or "date" not in expenses.columns:
        return {
            "data": {
                "categories": [],
                "anomalies": [],
                "total_expense": 0.0,
            },
            "meta": {
                "method": "Summarized expenses by category and detected anomalies",
                "row_count": 0,
                "as_of": get_as_of(db).strftime("%Y-%m-%d") if not sales.empty else "1970-01-01",
            },
        }

    as_of = get_as_of(db)

    e_df = expenses.copy()
    e_df["date"] = pd.to_datetime(e_df["date"])
    e_df["m"] = e_df["date"].dt.strftime("%Y-%m")

    # Detect anomalies across the historical monthly timeline
    anomalies: List[Dict[str, Any]] = []
    if flag_anomalies:
        # Group by month and category
        monthly_cat = e_df.groupby(["m", "category"])["amount"].sum().reset_index()

        for (m, cat), grp in e_df.groupby(["m", "category"]):
            m_amount = float(grp["amount"].sum())
            other_months = monthly_cat[(monthly_cat["category"] == cat) & (monthly_cat["m"] != m)]["amount"]

            if len(other_months) >= 2:
                median_other = float(other_months.median())
                if median_other > 0 and m_amount > (1.5 * median_other) and m_amount > 1000:
                    notes = grp["note"].dropna().astype(str).tolist()
                    note_str = "; ".join(dict.fromkeys(notes))  # unique preserving order
                    ratio = round(m_amount / median_other, 2)
                    anomalies.append({
                        "month": m,
                        "category": cat,
                        "amount": round(m_amount, 2),
                        "median_other_months": round(median_other, 2),
                        "ratio": ratio,
                        "note": note_str,
                        "anomaly": True,
                    })

    # Filter period for category summary if specified
    if from_date:
        start_date, end_date = resolve_period(from_date, to_date, db=db, as_of=as_of)
        filtered_df = e_df[(e_df["date"] >= start_date) & (e_df["date"] <= end_date)]
    else:
        filtered_df = e_df

    total_expense = round(float(filtered_df["amount"].sum()), 2)
    cat_summary = []
    if total_expense > 0:
        for cat, grp in filtered_df.groupby("category"):
            amt = round(float(grp["amount"].sum()), 2)
            cat_summary.append({
                "category": cat,
                "amount": amt,
                "share_pct": round(100.0 * amt / total_expense, 1),
            })
        cat_summary.sort(key=lambda x: x["amount"], reverse=True)

    return {
        "data": {
            "categories": cat_summary,
            "anomalies": anomalies,
            "total_expense": total_expense,
        },
        "meta": {
            "method": "Aggregated expenses by category and flagged monthly anomalies (>1.5x median of other months & > Rs 1,000)",
            "row_count": len(filtered_df),
            "as_of": as_of.strftime("%Y-%m-%d"),
        },
    }
