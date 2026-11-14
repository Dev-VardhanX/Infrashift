"""backend/app/analytics/payment_mix.py
Tool: payment_mix(db, from_date, to_date)
Computes payment breakdown (revenue, invoice count, and percentage share) by payment mode.
"""
from typing import Any, Dict, Optional
from app.analytics.sales_summary import sales_summary


def payment_mix(
    db: Optional[Any] = None,
    from_date: str = "last_30d",
    to_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Returns revenue share and invoice counts across payment modes (UPI, Cash, Card, Khata)."""
    summary = sales_summary(db=db, from_date=from_date, to_date=to_date, group_by="payment_mode")

    return {
        "data": summary["data"],
        "meta": {
            "method": "Calculated revenue share percentage across payment modes",
            "row_count": summary["meta"]["row_count"],
            "as_of": summary["meta"]["as_of"],
        },
    }
