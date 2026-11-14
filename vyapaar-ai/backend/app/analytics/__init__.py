"""Analytics package for Vyapaar AI."""
from app.analytics.periods import resolve_period, get_as_of
from app.analytics.sales_summary import sales_summary
from app.analytics.top_products import top_products
from app.analytics.compare_periods import compare_periods
from app.analytics.margin_by_product import margin_by_product
from app.analytics.stock_status import stock_status
from app.analytics.restock_plan import restock_plan
from app.analytics.dead_stock import dead_stock
from app.analytics.khata_overdue import khata_overdue
from app.analytics.expense_summary import expense_summary
from app.analytics.payment_mix import payment_mix
from app.analytics.festive_lift import festive_lift
from app.analytics.forecast import daily_demand
from app.analytics.margin_leak import margin_leak

__all__ = [
    "resolve_period",
    "get_as_of",
    "sales_summary",
    "top_products",
    "compare_periods",
    "margin_by_product",
    "stock_status",
    "restock_plan",
    "dead_stock",
    "khata_overdue",
    "expense_summary",
    "payment_mix",
    "festive_lift",
    "daily_demand",
    "margin_leak",
]
