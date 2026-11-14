"""Copilot package for Vyapaar AI."""
from app.copilot.router import ask
from app.copilot.validate import validate_answer
from app.copilot.templates import (
    render_compare_periods_template,
    render_stock_status_template,
    render_dead_stock_template,
    render_khata_overdue_template,
    render_margin_leak_template,
    render_expense_summary_template,
    render_payment_mix_template,
    render_unsupported_template,
)

__all__ = [
    "ask",
    "validate_answer",
    "render_compare_periods_template",
    "render_stock_status_template",
    "render_dead_stock_template",
    "render_khata_overdue_template",
    "render_margin_leak_template",
    "render_expense_summary_template",
    "render_payment_mix_template",
    "render_unsupported_template",
]
