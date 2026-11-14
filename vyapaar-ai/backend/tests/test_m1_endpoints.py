"""M1 tests: error shape, not_ready error contracts, caching, and shapes per doc 02 section 3."""
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import MagicMock

import pytest

# Isolate the test DB before importing the app.
os.environ["VYAPAAR_DB_PATH"] = str(Path(tempfile.mkdtemp()) / "test_m1_endpoints.db")

from fastapi.testclient import TestClient

from app.config import DIWALI_DATE
from app.db import store
from app.main import app

client = TestClient(app)


def test_endpoints_return_not_ready_when_modules_missing():
    """Verify endpoints return {"error": {"code": "not_ready", "message": "..."}} and specify needed function."""
    # 1. Dashboard
    res = client.get("/api/dashboard?from=2026-10-15&to=2026-11-13")
    assert res.status_code == 503, res.text
    err = res.json()["error"]
    assert err["code"] == "not_ready"
    assert "get_dashboard" in err["message"]
    assert "app.analytics.dashboard" in err["message"]

    # 2. Khata overdue
    res = client.get("/api/khata/overdue?days=45")
    assert res.status_code == 503, res.text
    err = res.json()["error"]
    assert err["code"] == "not_ready"
    assert "get_overdue" in err["message"]
    assert "app.analytics.khata" in err["message"]

    # 3. Inventory alerts
    res = client.get("/api/inventory/alerts")
    assert res.status_code == 503, res.text
    err = res.json()["error"]
    assert err["code"] == "not_ready"
    assert "get_alerts" in err["message"]
    assert "app.analytics.inventory" in err["message"]

    # 4. Insights
    res = client.get("/api/insights")
    assert res.status_code == 503, res.text
    err = res.json()["error"]
    assert err["code"] == "not_ready"
    assert "run_insights" in err["message"]
    assert "app.insights.engine" in err["message"]

    # 5. Actions draft
    res = client.post("/api/actions/draft", json={"type": "purchase_order", "ids": ["SUG01"]})
    assert res.status_code == 503, res.text
    err = res.json()["error"]
    assert err["code"] == "not_ready"
    assert "make_drafts" in err["message"]
    assert "app.actions.drafts" in err["message"]

    # 6. Chat endpoint
    res = client.post("/api/chat", json={"message": "Kaunsa maal khatam ho raha hai?"})
    assert res.status_code == 503, res.text
    err = res.json()["error"]
    assert err["code"] == "not_ready"
    assert "answer" in err["message"]
    assert "app.copilot.router" in err["message"]


def test_actions_draft_rejects_unknown_type():
    res = client.post("/api/actions/draft", json={"type": "email_blast", "ids": []})
    assert res.status_code == 400, res.text
    assert res.json()["error"]["code"] == "bad_type"


def test_chat_rejects_empty_message():
    res = client.post("/api/chat", json={"message": "   "})
    assert res.status_code == 400, res.text
    assert res.json()["error"]["code"] == "empty_message"


def test_dashboard_with_mock_module_and_caching(monkeypatch):
    """Test dashboard endpoint shape 3.1, default period, Diwali marker, and in-memory caching."""
    mock_analytics_dashboard = MagicMock()
    mock_dashboard_func = MagicMock()
    mock_analytics_dashboard.get_dashboard = mock_dashboard_func

    mock_dashboard_func.return_value = {
        "kpis": {
            "revenue": {"value": 1432103, "prev": 1228253, "delta_pct": 16.6},
            "gross_profit": {"value": 105673, "prev": 85094, "delta_pct": 24.2},
            "gross_margin_pct": {"value": 7.75, "prev": 7.29, "delta_pp": 0.46},
            "invoices": {"value": 3863, "prev": 3579},
            "avg_bill": {"value": 370.7, "prev": 343.2},
            "stock_value": {"value": 265385},
            "khata_outstanding": {"value": 35248},
        },
        "series": {
            "daily_revenue": [{"date": "2026-10-15", "revenue": 45000}],
            "by_category": [{"category": "Staples", "revenue": 500000, "profit": 35000}],
            "payment_mix": [{"mode": "upi", "revenue": 879000, "share_pct": 61.4}],
            "top_products": [{"sku": "ATT01", "name": "Atta", "revenue": 133980, "profit": 6682, "units": 450}],
        },
    }

    monkeypatch.setitem(sys.modules, "app.analytics.dashboard", mock_analytics_dashboard)

    # First call without from/to: should default to last_30d and calculate
    res1 = client.get("/api/dashboard")
    assert res1.status_code == 200, res1.text
    data1 = res1.json()

    assert "kpis" in data1
    assert "series" in data1
    assert "markers" in data1
    assert data1["markers"] == [{"date": DIWALI_DATE, "label": "Diwali"}]
    assert data1["period"]["from"] == "2026-10-15"
    assert data1["period"]["to"] == "2026-11-13"
    assert mock_dashboard_func.call_count == 1

    # Second call with same period: MUST hit the in-memory cache
    res2 = client.get("/api/dashboard")
    assert res2.status_code == 200
    assert mock_dashboard_func.call_count == 1  # Not called again!

    # Bump data version: MUST invalidate cache and call mock again
    store.bump_data_version()
    res3 = client.get("/api/dashboard")
    assert res3.status_code == 200
    assert mock_dashboard_func.call_count == 2  # Called again after cache invalidation!


def test_inventory_alerts_shape(monkeypatch):
    """Test GET /api/inventory/alerts returns shape 3.3."""
    mock_inv = MagicMock()
    mock_inv.get_alerts.return_value = {
        "items": [{
            "sku": "GHE01",
            "name": "Amul Ghee 1L",
            "supplier": "Jain Distributors",
            "stock": 7,
            "daily_demand": 6.5,
            "days_of_cover": 1.1,
            "lead_time_days": 2,
            "status": "CRITICAL",
            "suggested_qty": 30,
            "seasonal_note": None,
            "evidence": "Sold 91 units in last 14 days",
        }]
    }
    monkeypatch.setitem(sys.modules, "app.analytics.inventory", mock_inv)

    res = client.get("/api/inventory/alerts")
    assert res.status_code == 200, res.text
    body = res.json()
    assert "items" in body
    assert "as_of" in body
    assert len(body["items"]) == 1
    assert body["items"][0]["sku"] == "GHE01"
    assert body["items"][0]["status"] == "CRITICAL"


def test_insights_shape(monkeypatch):
    """Test GET /api/insights returns shape 3.2."""
    mock_eng = MagicMock()
    mock_eng.run_insights.return_value = {
        "insights": [{
            "id": "margin_leak:OIL01",
            "type": "margin_leak",
            "severity": "high",
            "title": "Fortune Sunflower Oil now earns only 1.3% margin (was 10.4%)",
            "impact_inr": 3120,
            "evidence": {
                "columns": ["Metric", "Before 15 Sep", "Now"],
                "rows": [["Cost per unit", "128.00", "141.00"], ["Margin on taxable value", "10.4%", "1.3%"]],
            },
            "why": "Latest purchase cost rose 10% on 15 Sep",
            "action": {"label": "Review price", "kind": "none", "payload": {}},
            "as_of": "2026-11-13",
        }]
    }
    monkeypatch.setitem(sys.modules, "app.insights.engine", mock_eng)

    res = client.get("/api/insights")
    assert res.status_code == 200, res.text
    body = res.json()
    assert "insights" in body
    assert len(body["insights"]) == 1
    assert body["insights"][0]["id"] == "margin_leak:OIL01"


def test_khata_overdue_shape(monkeypatch):
    """Test GET /api/khata/overdue returns customer list."""
    mock_khata = MagicMock()
    mock_khata.get_overdue.return_value = {
        "customers": [{
            "id": "C003",
            "name": "Anil Gupta",
            "phone": "9812345678",
            "balance": 9685,
            "days_since_payment": 108,
            "over_limit": True,
        }]
    }
    monkeypatch.setitem(sys.modules, "app.analytics.khata", mock_khata)

    res = client.get("/api/khata/overdue?days=45")
    assert res.status_code == 200, res.text
    body = res.json()
    assert "customers" in body
    assert len(body["customers"]) == 1
    assert body["customers"][0]["name"] == "Anil Gupta"


def test_actions_draft_shape(monkeypatch):
    """Test POST /api/actions/draft returns drafts list."""
    mock_drafts = MagicMock()
    mock_drafts.make_drafts.return_value = {
        "drafts": [{
            "to": "Gupta Traders",
            "text": "Namaste Gupta Traders ji, order for Sharma General Store:\n- Sugar 1kg x 120",
            "wa_link": "https://wa.me/919999999999?text=Namaste",
        }]
    }
    monkeypatch.setitem(sys.modules, "app.actions.drafts", mock_drafts)

    res = client.post("/api/actions/draft", json={"type": "purchase_order", "ids": ["SUG01"]})
    assert res.status_code == 200, res.text
    body = res.json()
    assert "drafts" in body
    assert len(body["drafts"]) == 1
    assert body["drafts"][0]["to"] == "Gupta Traders"


def test_chat_llm_mode_success(monkeypatch):
    """Test POST /api/chat in LLM mode returns expected contract and indicates llm mode."""
    from app.config import settings
    monkeypatch.setattr(settings, "copilot_mode", "llm")
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")

    mock_router = MagicMock()
    mock_router.answer.return_value = {
        "answer": "Sugar 1kg is out of stock and Amul Ghee is critical.",
        "blocks": [{"type": "table", "data": [{"sku": "SUG01", "stock": 0}]}],
        "calc": [{"tool": "stock_status", "args": {}, "row_count": 2, "method": "cover"}],
        "validated": True,
    }
    monkeypatch.setitem(sys.modules, "app.copilot.router", mock_router)

    res = client.post("/api/chat", json={"message": "Kaunsa maal khatam ho raha hai?"})
    assert res.status_code == 200, res.text
    body = res.json()

    assert "answer" in body
    assert "blocks" in body
    assert "calc" in body
    assert "validated" in body
    assert body["mode"] == "llm"
    assert body["rule_based"] is False
    assert "Sugar 1kg is out" in body["answer"]


def test_chat_fallback_mode_direct(monkeypatch):
    """Test POST /api/chat when COPILOT_MODE=fallback routes directly to rule-based without LLM."""
    from app.config import settings
    monkeypatch.setattr(settings, "copilot_mode", "fallback")

    mock_router = MagicMock()
    mock_router.answer_fallback.return_value = {
        "answer": "Rule-based answer: Sugar 1kg is out of stock.",
        "blocks": [],
        "calc": [{"tool": "stock_status", "args": {}, "row_count": 1, "method": "fallback_keywords"}],
        "validated": True,
    }
    monkeypatch.setitem(sys.modules, "app.copilot.router", mock_router)

    res = client.post("/api/chat", json={"message": "khatam maal"})
    assert res.status_code == 200, res.text
    body = res.json()

    assert body["mode"] == "rule_based"
    assert body["rule_based"] is True
    assert "Rule-based answer" in body["answer"]


def test_chat_automatic_fallback_on_llm_unavailable(monkeypatch):
    """Test automatic fallback to rule-based router when LLMUnavailable is raised."""
    from app.config import settings
    from app.copilot.llm import LLMUnavailable
    monkeypatch.setattr(settings, "copilot_mode", "llm")
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")

    mock_router = MagicMock()
    # LLM answer raises LLMUnavailable (e.g. timeout or network dead on stage)
    mock_router.answer.side_effect = LLMUnavailable("Simulated Gemini timeout > 6s")
    mock_router.answer_fallback.return_value = {
        "answer": "Fallback response: Udhaar balance is Rs 35,248.",
        "blocks": [],
        "calc": [{"tool": "khata_overdue", "args": {}, "row_count": 7, "method": "rule_based"}],
        "validated": True,
    }
    monkeypatch.setitem(sys.modules, "app.copilot.router", mock_router)

    res = client.post("/api/chat", json={"message": "Kitna udhaar baaki hai?"})
    assert res.status_code == 200, res.text
    body = res.json()

    # Automatically fell back and set mode to rule_based
    assert body["mode"] == "rule_based"
    assert body["rule_based"] is True
    assert "Fallback response" in body["answer"]

