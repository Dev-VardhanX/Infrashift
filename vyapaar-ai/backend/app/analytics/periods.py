"""backend/app/analytics/periods.py
Single source of truth for date calculations and period resolution.
Never uses the system clock; resolves strictly against AS_OF = max(sales.date).
"""
from typing import Any, Optional, Tuple, Union
import pandas as pd
from app.analytics._data import get_data

DIWALI_DATE = pd.Timestamp("2026-11-08")


def get_as_of(db: Optional[Any] = None) -> pd.Timestamp:
    """Return AS_OF date as max(sales.date). Never uses system clock."""
    data = get_data(db)
    sales = data["sales"]
    if sales.empty or "date" not in sales.columns:
        raise ValueError("Sales data is empty or missing 'date' column")
    as_of = pd.to_datetime(sales["date"]).max()
    return pd.Timestamp(as_of).normalize()


def resolve_period(
    from_spec: Union[str, pd.Timestamp],
    to_spec: Optional[Union[str, pd.Timestamp]] = None,
    db: Optional[Any] = None,
    as_of: Optional[pd.Timestamp] = None,
) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Resolves period tokens and ISO dates against AS_OF.
    Tokens supported:
    - 'last_7d': [AS_OF - 6d, AS_OF]
    - 'last_30d': [AS_OF - 29d, AS_OF]
    - 'prev_30d': [AS_OF - 59d, AS_OF - 30d]
    - 'this_month': [1st of AS_OF month, AS_OF]
    - 'last_month': [1st of prev month, last day of prev month]
    - 'diwali_week': [2026-11-01, 2026-11-07] (7 days ending day before Diwali)
    - 'prior_week': [2026-10-25, 2026-10-31] (7 days prior to diwali_week)
    Also resolves explicit ISO dates 'YYYY-MM-DD'.
    """
    if as_of is None:
        as_of = get_as_of(db)
    else:
        as_of = pd.Timestamp(as_of).normalize()

    # If from_spec is a recognized full period token and to_spec is None
    token = str(from_spec).strip().lower() if isinstance(from_spec, str) else None

    if token == "last_7d" and to_spec is None:
        return as_of - pd.Timedelta(days=6), as_of

    if token == "last_30d" and to_spec is None:
        return as_of - pd.Timedelta(days=29), as_of

    if token == "prev_30d" and to_spec is None:
        return as_of - pd.Timedelta(days=59), as_of - pd.Timedelta(days=30)

    if token == "this_month" and to_spec is None:
        start = pd.Timestamp(year=as_of.year, month=as_of.month, day=1)
        return start, as_of

    if token == "last_month" and to_spec is None:
        # First day of previous month
        first_of_this_month = pd.Timestamp(year=as_of.year, month=as_of.month, day=1)
        end_of_last_month = first_of_this_month - pd.Timedelta(days=1)
        start_of_last_month = pd.Timestamp(
            year=end_of_last_month.year, month=end_of_last_month.month, day=1
        )
        return start_of_last_month, end_of_last_month

    if token == "diwali_week" and to_spec is None:
        dw_end = DIWALI_DATE - pd.Timedelta(days=1)
        dw_start = DIWALI_DATE - pd.Timedelta(days=7)
        return dw_start, dw_end

    if token == "prior_week" and to_spec is None:
        dw_start = DIWALI_DATE - pd.Timedelta(days=7)
        pw_end = dw_start - pd.Timedelta(days=1)
        pw_start = dw_start - pd.Timedelta(days=7)
        return pw_start, pw_end

    # Explicit resolution of from_spec and to_spec
    def parse_bound(val: Union[str, pd.Timestamp], default_bound: pd.Timestamp) -> pd.Timestamp:
        if val is None:
            return default_bound
        s = str(val).strip().lower()
        if s == "as_of":
            return as_of
        if s == "diwali":
            return DIWALI_DATE
        try:
            return pd.Timestamp(val).normalize()
        except Exception as e:
            raise ValueError(f"Invalid date or period token: '{val}'") from e

    start_date = parse_bound(from_spec, as_of - pd.Timedelta(days=29))
    end_date = parse_bound(to_spec, as_of)

    return start_date, end_date
