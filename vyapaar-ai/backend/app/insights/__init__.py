"""Insights package for Vyapaar AI."""
from app.insights.rules import (
    get_insights,
    restock_insights,
    dead_stock_insights,
    margin_leak_insights,
    expense_anomaly_insights,
    khata_overdue_insights,
    festive_lift_insights,
)

__all__ = [
    "get_insights",
    "restock_insights",
    "dead_stock_insights",
    "margin_leak_insights",
    "expense_anomaly_insights",
    "khata_overdue_insights",
    "festive_lift_insights",
]
