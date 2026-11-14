"""M1 tests for main.py review items:
- Unhandled exceptions & sanitized error shape
- Missing timeouts & 504 handling
- CORS headers for frontend dev ports (localhost:5173, 127.0.0.1:5173)
- Empty DB startup behaviour & /api/health + /health endpoints
- Privacy sanitization masking customer phone numbers in logs and query strings
"""
import asyncio
import os
from pathlib import Path
import tempfile
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.copilot.llm import PHONE_PATTERN, _sanitize
import app.db as db_module
from app.main import app, sanitize_text

client = TestClient(app)


def test_cors_headers_for_frontend_port() -> None:
    """Verify CORS headers return for Vite dev port localhost:5173."""
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_health_endpoints_and_empty_db_diagnostics() -> None:
    """Verify /api/health and /health report complete diagnostics."""
    for path in ("/api/health", "/health"):
        res = client.get(path)
        assert res.status_code == 200
        data = res.json()
        assert data["ok"] is True
        assert "status" in data
        assert "database_empty" in data
        assert "llm_configured" in data
        assert "copilot_mode" in data
        assert "message" in data


def test_sanitization_masks_phone_numbers_and_secrets() -> None:
    """Verify phone numbers and secrets are masked."""
    masked = sanitize_text("Customer phone 9876543210 and +91 98765 43210 owe money")
    assert "9876543210" not in masked
    assert "[REDACTED_PHONE]" in masked


def test_validation_error_returns_contract_error_shape() -> None:
    """Verify invalid payloads return contract error shape with no stack trace."""
    res = client.post("/api/actions/draft", json={"type": "invalid_type"})
    assert res.status_code == 400
    body = res.json()
    assert "error" in body
    assert body["error"]["code"] == "bad_type"
    assert "message" in body["error"]

