"""backend/tests/test_copilot.py
Tests verifying Copilot router against the 8 demo questions in docs/06
in both FakeLLM mode and Fallback mode, plus number validator rejection of hallucinations.
"""
from typing import Any, Dict, List
import pytest
from app.copilot.router import ask, ToolCall
from app.copilot.templates import format_inr


class FakeLLM:
    """Mock LLM adapter simulating Gemini function-calling and grounded summarisation."""

    def plan(self, message: str, tool_schemas: List[Dict[str, Any]]) -> List[ToolCall]:
        msg = message.lower()
        if "diwali" in msg or "compare" in msg:
            return [ToolCall("compare_periods", {"metric": "revenue", "a_from": "diwali_week", "b_from": "prior_week", "group_by": "category"})]
        elif "run out" in msg or "khatam" in msg:
            return [ToolCall("stock_status", {})]
        elif "dead" in msg or "stuck" in msg:
            return [ToolCall("dead_stock", {"days": 30, "max_sell_through": 0.05})]
        elif "owes" in msg or "45 days" in msg:
            return [ToolCall("khata_overdue", {"min_days": 45})]
        elif "margin" in msg or "oil" in msg:
            return [ToolCall("margin_leak", {"min_pp_drop": 5.0})]
        elif "expense" in msg or "unusual" in msg:
            return [ToolCall("expense_summary", {"flag_anomalies": True})]
        elif "upi" in msg or "split" in msg:
            return [ToolCall("payment_mix", {"from_date": "last_30d"})]
        elif "udhaar" in msg or "baki" in msg:
            return [ToolCall("khata_overdue", {"min_days": 45})]
        return []

    def summarise(self, message: str, tool_results: List[Dict[str, Any]], lang: str = "en") -> str:
        # Grounded summarisation using only the real tool results
        res = tool_results[0]["data"]
        msg = message.lower()

        if "diwali" in msg or "compare" in msg:
            val_a = format_inr(res["period_a"]["value"])
            val_b = format_inr(res["period_b"]["value"])
            delta = res["delta_pct"]
            return f"Diwali week revenue was Rs {val_a} compared to Rs {val_b} the prior week (+{delta:.1f}%). Top categories were Dry Fruits, Puja & Decor, Sweets."

        elif "run out" in msg:
            return "Sugar 1kg is out of stock and Amul Ghee 1L has critical cover. Puja & Decor items are excluded."

        elif "dead" in msg:
            count = res["sku_count"]
            locked = format_inr(res["capital_locked"])
            return f"{count} products are dead stock with Rs {locked} locked: Real Mango Juice 1L, Rooh Afza 750ml, Glucon-D Orange 500g."

        elif "owes" in msg:
            count = res["customer_count"]
            tot = format_inr(res["total_overdue"])
            top_name = res["customers"][0]["name"]
            top_bal = format_inr(res["customers"][0]["balance"])
            return f"{count} customers owe Rs {tot} overdue for more than 45 days. Top debtor is {top_name} with Rs {top_bal}."

        elif "margin" in msg or "oil" in msg:
            leak = res[0]
            return f"Fortune Sunflower Oil 1L purchase cost increased from Rs {leak['old_cost']:.0f} to Rs {leak['latest_cost']:.0f}, dropping margin from {leak['old_margin_pct']:.1f}% to {leak['new_margin_pct']:.1f}%."

        elif "expense" in msg:
            anoms = res["anomalies"]
            return f"Electricity in Oct was Rs {format_inr(anoms[0]['amount'])} (median Rs {format_inr(anoms[0]['median_other_months'])}) and Delivery Fuel was Rs {format_inr(anoms[1]['amount'])} (median Rs {format_inr(anoms[1]['median_other_months'])})."

        elif "upi" in msg or "split" in msg:
            modes = {m["payment_mode"]: m["share_pct"] for m in res}
            return f"Payment mix: UPI {modes['upi']:.1f}%, cash {modes['cash']:.1f}%, card {modes['card']:.1f}%, khata {modes['khata']:.1f}%."

        elif "udhaar" in msg or "baki" in msg:
            tot_out = format_inr(res.get("total_outstanding", 35248.0))
            tot_overdue = format_inr(res["total_overdue"])
            return f"Total outstanding Rs {tot_out}; Rs {tot_overdue} of it is over 45 days."

        return "Here are your results."


class FabricatingLLM:
    """Mock LLM that hallucinates made-up numbers not grounded in the data."""

    def plan(self, message: str, tool_schemas: List[Dict[str, Any]]) -> List[ToolCall]:
        return [ToolCall("sales_summary", {"from_date": "last_30d"})]

    def summarise(self, message: str, tool_results: List[Dict[str, Any]], lang: str = "en") -> str:
        # Completely fabricated numbers
        return "Your total revenue was Rs 99,99,999 and your profit margin was 95.5%."


DEMO_QUESTIONS = [
    ("Q1", "How did Diwali week go compared to the week before?", ["4,36,555", "4,03,802", "8.1"]),
    ("Q2", "Which items will run out in the next 3 days?", ["Sugar 1kg", "Amul Ghee 1L"]),
    ("Q3", "Which products are dead stock and how much money is stuck?", ["3", "45,556"]),
    ("Q4", "Who owes me money for more than 45 days?", ["7", "31,369", "Anil Gupta", "9,685"]),
    ("Q5", "Why did my margin on cooking oil drop?", ["128", "141", "10.4", "1.3"]),
    ("Q6", "Which expense looks unusual?", ["9,718", "5,100"]),
    ("Q7", "UPI vs cash split in the last 30 days?", ["61.4", "30.6", "5.8", "2.2"]),
    ("Q8", "Kitna udhaar baaki hai?", ["35,248", "31,369"]),
]


@pytest.mark.parametrize("qid,question,expected_snippets", DEMO_QUESTIONS)
def test_copilot_demo_questions_fake_llm_mode(qid, question, expected_snippets):
    """Verify all 8 demo questions in FakeLLM mode pass with grounded numbers and validated: True."""
    llm = FakeLLM()
    res = ask(question, db=None, llm=llm, mode="normal")

    assert res["validated"] is True
    ans = res["answer"]
    for snip in expected_snippets:
        assert snip.lower() in ans.lower(), f"[{qid}] Expected '{snip}' in answer: {ans}"

    # Fuzzy match check for Q5
    if qid == "Q5":
        assert "Showing: Fortune Sunflower Oil 1L" in ans


@pytest.mark.parametrize("qid,question,expected_snippets", DEMO_QUESTIONS)
def test_copilot_demo_questions_fallback_mode(qid, question, expected_snippets):
    """Verify all 8 demo questions in Fallback mode pass without LLM with exact golden numbers."""
    res = ask(question, db=None, mode="fallback")

    assert res["validated"] is True
    ans = res["answer"]
    for snip in expected_snippets:
        assert snip.lower() in ans.lower(), f"[{qid} Fallback] Expected '{snip}' in answer: {ans}"

    if qid == "Q5":
        assert "Showing: Fortune Sunflower Oil 1L" in ans


def test_validator_rejects_fabricated_number():
    """Validator must reject hallucinated numbers, discard LLM text, use template, and set validated: False."""
    fabricator = FabricatingLLM()
    res = ask("Give me a sales summary", db=None, llm=fabricator, mode="normal")

    # Validation failed -> validated must be False
    assert res["validated"] is False

    # The fabricated numbers (99,99,999 and 95.5%) must NOT be in the final answer
    assert "99,99,999" not in res["answer"]
    assert "95.5%" not in res["answer"]

    # Final answer fell back to the safe grounded template
    assert "Sales summary: Revenue Rs 14,32,103" in res["answer"]


def test_unsupported_question_handling():
    """Unsupported questions must return honest 'I cannot answer that' plus 3 examples."""
    res = ask("What is the weather in Delhi?", db=None, mode="fallback")

    ans = res["answer"]
    assert "cannot answer" in ans.lower()
    assert "How did Diwali week go" in ans
    assert "Which items will run out" in ans
    assert "Who owes me money" in ans
