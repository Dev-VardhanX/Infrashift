"""backend/app/analytics/khata_overdue.py
Tool: khata_overdue(db, min_days)
Identifies customers with positive khata balance whose last payment is older than min_days (default 45).
Flags whether the customer has breached their credit_limit.
"""
from typing import Any, Dict, Optional
import pandas as pd
from app.analytics._data import get_data
from app.analytics.periods import get_as_of


def khata_overdue(
    db: Optional[Any] = None,
    min_days: int = 45,
) -> Dict[str, Any]:
    """Returns customers with overdue khata balances and credit limit breaches."""
    data = get_data(db)
    customers = data["customers"]
    sales = data["sales"]

    if customers.empty:
        return {
            "data": {
                "customers": [],
                "total_overdue": 0.0,
                "customer_count": 0,
                "over_limit_count": 0,
            },
            "meta": {
                "method": f"Identified overdue khata accounts (> {min_days} days)",
                "row_count": 0,
                "as_of": get_as_of(db).strftime("%Y-%m-%d") if not sales.empty else "1970-01-01",
            },
        }

    as_of = get_as_of(db)

    c_df = customers.copy()
    c_df["last_pay_dt"] = pd.to_datetime(c_df["last_payment_date"])
    c_df["days_since_payment"] = (as_of - c_df["last_pay_dt"]).dt.days

    overdue_mask = (c_df["khata_balance"] > 0) & (c_df["days_since_payment"] > min_days)
    overdue_df = c_df[overdue_mask].sort_values("khata_balance", ascending=False)

    results = []
    total_overdue = 0.0
    over_limit_count = 0

    for _, row in overdue_df.iterrows():
        bal = round(float(row["khata_balance"]), 2)
        credit_limit = float(row.get("credit_limit", 0))
        is_over_limit = bool(credit_limit > 0 and bal > credit_limit)
        if is_over_limit:
            over_limit_count += 1
        total_overdue += bal

        results.append({
            "customer_id": str(row["customer_id"]),
            "name": str(row["name"]),
            "phone": str(row.get("phone", "")),
            "balance": bal,
            "days_since_payment": int(row["days_since_payment"]),
            "last_payment_date": str(row.get("last_payment_date", "")),
            "credit_limit": credit_limit,
            "over_limit": is_over_limit,
        })

    total_outstanding = round(float(c_df["khata_balance"].sum()), 2) if not c_df.empty else 0.0

    return {
        "data": {
            "customers": results,
            "total_overdue": round(total_overdue, 2),
            "total_outstanding": total_outstanding,
            "customer_count": len(results),
            "over_limit_count": over_limit_count,
        },
        "meta": {
            "method": f"Filtered khata balances > 0 where days since last payment > {min_days}",
            "row_count": len(results),
            "as_of": as_of.strftime("%Y-%m-%d"),
        },
    }
