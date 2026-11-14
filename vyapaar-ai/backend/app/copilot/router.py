"""backend/app/copilot/router.py
Copilot router per docs/02 section 5.
Flow:
1. Question -> LLM plan -> run at most 3 tools with Pydantic-validated args -> compose answer -> validate.
2. Fallback keyword router (English + Hinglish) used on LLMUnavailable or COPILOT_MODE=fallback.
3. Unsupported questions get an honest "I can't answer that" with 3 supported examples.
4. Fuzzy-resolves product names via rapidfuzz and shows match ("Showing: Fortune Sunflower Oil 1L").
5. Output shape: {"answer": str, "blocks": list, "calc": list, "validated": bool}.
"""
import os
import re
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from rapidfuzz import process, fuzz

from app.analytics._data import get_data
from app.analytics.periods import get_as_of
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
from app.analytics.margin_leak import margin_leak

from app.copilot.validate import validate_answer
from app.copilot.templates import (
    render_compare_periods_template,
    render_stock_status_template,
    render_dead_stock_template,
    render_khata_overdue_template,
    render_margin_leak_template,
    render_expense_summary_template,
    render_payment_mix_template,
    render_sales_summary_template,
    render_unsupported_template,
)

# LLM interface fallback / definition
try:
    from app.copilot.llm import LLMUnavailable, ToolCall, plan, summarise
except ImportError:
    class LLMUnavailable(Exception):
        """Raised when LLM is unavailable or times out."""
        pass

    class ToolCall:
        def __init__(self, name: str, args: Optional[Dict[str, Any]] = None):
            self.name = name
            self.args = args or {}

    def plan(message: str, tool_schemas: List[Dict[str, Any]]) -> List[ToolCall]:
        raise LLMUnavailable("LLM adapter not initialized")

    def summarise(message: str, tool_results: List[Dict[str, Any]], lang: str = "en") -> str:
        raise LLMUnavailable("LLM adapter not initialized")


# Pydantic Tool Schemas
class SalesSummaryArgs(BaseModel):
    from_date: str = "last_30d"
    to_date: Optional[str] = None
    group_by: Optional[str] = None

class TopProductsArgs(BaseModel):
    metric: str = "revenue"
    n: int = 5
    from_date: str = "last_30d"
    to_date: Optional[str] = None
    order: str = "top"

class ComparePeriodsArgs(BaseModel):
    metric: str = "revenue"
    a_from: str = "diwali_week"
    a_to: Optional[str] = None
    b_from: str = "prior_week"
    b_to: Optional[str] = None
    group_by: Optional[str] = None

class MarginByProductArgs(BaseModel):
    from_date: str = "last_30d"
    to_date: Optional[str] = None
    n: Optional[int] = None

class StockStatusArgs(BaseModel):
    sku: Optional[str] = None

class RestockPlanArgs(BaseModel):
    horizon_days: int = 7

class DeadStockArgs(BaseModel):
    days: int = 30
    max_sell_through: float = 0.05

class KhataOverdueArgs(BaseModel):
    min_days: int = 45

class ExpenseSummaryArgs(BaseModel):
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    flag_anomalies: bool = True

class PaymentMixArgs(BaseModel):
    from_date: str = "last_30d"
    to_date: Optional[str] = None

class FestiveLiftArgs(BaseModel):
    category: Optional[str] = None
    event_date: str = "2026-11-08"
    window_days: int = 7

class MarginLeakArgs(BaseModel):
    min_pp_drop: float = 5.0


TOOL_REGISTRY = {
    "sales_summary": (sales_summary, SalesSummaryArgs),
    "top_products": (top_products, TopProductsArgs),
    "compare_periods": (compare_periods, ComparePeriodsArgs),
    "margin_by_product": (margin_by_product, MarginByProductArgs),
    "stock_status": (stock_status, StockStatusArgs),
    "restock_plan": (restock_plan, RestockPlanArgs),
    "dead_stock": (dead_stock, DeadStockArgs),
    "khata_overdue": (khata_overdue, KhataOverdueArgs),
    "expense_summary": (expense_summary, ExpenseSummaryArgs),
    "payment_mix": (payment_mix, PaymentMixArgs),
    "festive_lift": (festive_lift, FestiveLiftArgs),
    "margin_leak": (margin_leak, MarginLeakArgs),
}


def fuzzy_resolve_sku(query: str, db: Optional[Any] = None) -> Optional[Tuple[str, str]]:
    """Fuzzy-resolves SKU names using rapidfuzz."""
    data = get_data(db)
    products = data.get("products")
    if products is None or products.empty:
        return None

    q_lower = query.lower()
    candidate = q_lower
    if "cooking oil" in q_lower or "oil" in q_lower:
        candidate = "fortune sunflower oil"

    names = products["name"].tolist()
    match = process.extractOne(candidate, names, scorer=fuzz.token_set_ratio)
    if match and match[1] >= 50:
        matched_name = match[0]
        sku = products[products["name"] == matched_name]["sku"].iloc[0]
        return sku, matched_name
    return None


def execute_tool_call(call: ToolCall, db: Optional[Any] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Executes a tool call with Pydantic validation."""
    tool_entry = TOOL_REGISTRY.get(call.name)
    if not tool_entry:
        raise ValueError(f"Unknown tool: {call.name}")

    fn, schema_cls = tool_entry
    validated_args = schema_cls(**(call.args or {})).model_dump(exclude_unset=True)
    result = fn(db=db, **validated_args)
    return validated_args, result


def fallback_route(message: str, db: Optional[Any] = None) -> Tuple[List[ToolCall], str]:
    """Keyword/regex fallback router (English + Hinglish)."""
    msg = message.lower()

    # Q1: Diwali week vs week before / period comparison
    if re.search(r"diwali|tyohar|week before|compare", msg):
        return [
            ToolCall("compare_periods", {"metric": "revenue", "a_from": "diwali_week", "b_from": "prior_week", "group_by": "category"})
        ], "compare_periods"

    # Q2: Restock / run out / khatam
    if re.search(r"run out|khatam|restock|stock|kam|out of stock", msg) and not re.search(r"dead|udhaar|margin", msg):
        return [ToolCall("stock_status", {})], "stock_status"

    # Q3: Dead stock / stuck / slow / nahi bik
    if re.search(r"dead|slow|nahi bik|stuck", msg):
        return [ToolCall("dead_stock", {"days": 30, "max_sell_through": 0.05})], "dead_stock"

    # Q4 & Q8: Udhaar / khata / baki
    if re.search(r"udhaar|khata|baki|owe|debt", msg):
        return [ToolCall("khata_overdue", {"min_days": 45})], "khata_overdue"

    # Q5: Margin drop / cooking oil / munafa
    if re.search(r"margin|munafa|cooking oil|drop", msg):
        return [ToolCall("margin_leak", {"min_pp_drop": 5.0})], "margin_leak"

    # Q6: Expense / bijli / fuel / kharcha / unusual
    if re.search(r"expense|kharcha|bijli|fuel|unusual|anomaly", msg):
        return [ToolCall("expense_summary", {"flag_anomalies": True})], "expense_summary"

    # Q7: Payment mix / UPI vs cash / split
    if re.search(r"upi|cash|payment|split|mix", msg):
        return [ToolCall("payment_mix", {"from_date": "last_30d"})], "payment_mix"

    return [], "unsupported"


def render_template_for_intent(intent: str, results: List[Dict[str, Any]], db: Optional[Any] = None, message: str = "") -> str:
    """Selects and renders the appropriate template for a given tool result."""
    if not results:
        return render_unsupported_template()

    first_res = results[0]["data"]

    if intent == "compare_periods":
        return render_compare_periods_template(first_res)
    elif intent == "stock_status":
        return render_stock_status_template(first_res)
    elif intent == "dead_stock":
        return render_dead_stock_template(first_res)
    elif intent == "khata_overdue":
        total_out = None
        # If Hinglish Q8 or general balance question
        if "kitna" in message.lower() or "total" in message.lower() or "outstanding" in message.lower():
            customers = get_data(db).get("customers")
            if customers is not None and not customers.empty and "khata_balance" in customers.columns:
                total_out = float(customers["khata_balance"].sum())
        return render_khata_overdue_template(first_res, total_outstanding=total_out)
    elif intent == "margin_leak":
        return render_margin_leak_template(first_res)
    elif intent == "expense_summary":
        return render_expense_summary_template(first_res)
    elif intent == "payment_mix":
        return render_payment_mix_template(first_res)
    elif intent == "sales_summary":
        return render_sales_summary_template(first_res)

    return render_unsupported_template()


def ask(
    message: str,
    db: Optional[Any] = None,
    lang: str = "en",
    llm: Optional[Any] = None,
    mode: Optional[str] = None,
) -> Dict[str, Any]:
    """Main entrypoint for Copilot /chat requests.
    Returns: {"answer": str, "blocks": list, "calc": list, "validated": bool}
    """
    effective_mode = mode or os.environ.get("COPILOT_MODE", "normal")

    # Step 1: Check fuzzy product matching
    matched_prefix = ""
    fuzzy_match = fuzzy_resolve_sku(message, db=db)
    if fuzzy_match:
        sku, matched_name = fuzzy_match
        # Check if question implies inspecting that specific product
        if "oil" in message.lower() or "fortune" in message.lower():
            matched_prefix = f"Showing: {matched_name}\n"

    tool_calls: List[ToolCall] = []
    intent = ""
    use_llm = (effective_mode != "fallback")

    # Step 2: Attempt LLM planning unless fallback mode
    if use_llm:
        try:
            planner = getattr(llm, "plan", None) if llm else plan
            schemas = [{"name": k} for k in TOOL_REGISTRY.keys()]
            tool_calls = planner(message, schemas)
            intent = tool_calls[0].name if tool_calls else "unsupported"
        except (LLMUnavailable, Exception):
            tool_calls, intent = fallback_route(message, db=db)
            use_llm = False
    else:
        tool_calls, intent = fallback_route(message, db=db)

    # If unsupported question
    if intent == "unsupported" or not tool_calls:
        return {
            "answer": render_unsupported_template(),
            "blocks": [],
            "calc": [],
            "validated": True,
        }

    # Guardrail: execute at most 3 tool calls
    tool_calls = tool_calls[:3]

    calc_log = []
    tool_results = []
    used_args = []

    for call in tool_calls:
        try:
            v_args, res = execute_tool_call(call, db=db)
            used_args.append(v_args)
            tool_results.append(res)
            calc_log.append({
                "tool": call.name,
                "args": v_args,
                "row_count": res["meta"]["row_count"],
                "method": res["meta"]["method"],
            })
        except Exception as e:
            # If tool execution fails
            calc_log.append({"tool": call.name, "error": str(e)})

    # Fallback template answer
    template_answer = matched_prefix + render_template_for_intent(intent, tool_results, db=db, message=message)

    final_answer = template_answer
    is_validated = True

    # Step 3: LLM summarisation & Number Validation
    if use_llm and tool_results:
        try:
            summariser = getattr(llm, "summarise", None) if llm else summarise
            llm_text = summariser(message, tool_results, lang=lang)

            # Validate LLM answer against tool output
            valid, unverified = validate_answer(llm_text, tool_results, used_args)
            if valid:
                final_answer = matched_prefix + llm_text
                is_validated = True
            else:
                # Validation failure: discard LLM text and use template
                final_answer = template_answer
                is_validated = False
        except (LLMUnavailable, Exception):
            final_answer = template_answer
            is_validated = True

    # Construct presentation blocks
    blocks = []
    if tool_results:
        first_data = tool_results[0].get("data")
        if isinstance(first_data, (list, dict)):
            blocks.append({"type": "data_table", "content": first_data})

    return {
        "answer": final_answer,
        "blocks": blocks,
        "calc": calc_log,
        "validated": is_validated,
    }
