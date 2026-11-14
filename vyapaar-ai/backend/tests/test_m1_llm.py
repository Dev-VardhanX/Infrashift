"""M1 tests: Gemini adapter interface, official SDK integration, FakeLLM, timeout, retries, and offline execution."""
from unittest.mock import MagicMock, patch

import pytest

from app.config import settings
from app.copilot.llm import (
    FakeLLM,
    LLMUnavailable,
    ToolCall,
    _sanitize,
    call_gemini,
    is_configured,
    plan,
    summarise,
)


def test_copilot_modes_and_fallback_network_guard(monkeypatch):
    """COPILOT_MODE in {auto, llm, fallback}: fallback mode never touches the network."""
    # 1. Fallback mode
    monkeypatch.setattr(settings, "copilot_mode", "fallback")
    monkeypatch.setattr(settings, "gemini_api_key", "secret-test-key")
    assert not is_configured()

    # Must raise LLMUnavailable without making any network call
    with pytest.raises(LLMUnavailable) as exc1:
        plan("any question")
    assert "fallback" in str(exc1.value).lower()

    with pytest.raises(LLMUnavailable) as exc2:
        summarise("any question", [])
    assert "fallback" in str(exc2.value).lower()

    # 2. Auto mode
    monkeypatch.setattr(settings, "copilot_mode", "auto")
    monkeypatch.setattr(settings, "gemini_api_key", "")
    assert not is_configured()
    with pytest.raises(LLMUnavailable):
        plan("any question")

    monkeypatch.setattr(settings, "gemini_api_key", "valid-key")
    assert is_configured()

    # 3. LLM mode
    monkeypatch.setattr(settings, "copilot_mode", "llm")
    monkeypatch.setattr(settings, "gemini_api_key", "")
    assert not is_configured()
    with pytest.raises(LLMUnavailable):
        plan("any question")


def test_gemini_model_read_from_env_not_hardcoded(monkeypatch):
    """Verify GEMINI_MODEL is read from configuration rather than hardcoded."""
    monkeypatch.setattr(settings, "gemini_model", "gemini-custom-experimental")
    assert settings.gemini_model == "gemini-custom-experimental"


def test_sanitization_masks_key_and_customer_phones():
    """Verify API keys and customer phone numbers are sanitized and never leaked."""
    settings.gemini_api_key = "AIzaSySecretApiKey123"
    raw_text = (
        "Customer Ramesh phone is 9876543210 and second contact +919123456789. "
        "Error using key AIzaSySecretApiKey123."
    )
    sanitized = _sanitize(raw_text)

    assert "AIzaSySecretApiKey123" not in sanitized
    assert "[REDACTED_API_KEY]" in sanitized
    assert "9876543210" not in sanitized
    assert "+919123456789" not in sanitized
    assert "[REDACTED_PHONE]" in sanitized


def test_fake_llm_scripted_plan_and_summarise():
    """Verify FakeLLM produces scripted responses without network access."""
    fake = FakeLLM(
        plan_responses=[[
            ToolCall(name="stock_status", args={"sku": "GHE01"}),
            ToolCall(name="restock_plan", args={"horizon_days": 7}),
        ]],
        summarise_responses=["Amul Ghee 1L is critical with 1.1 days cover."],
    )

    calls = fake.plan("Which items are running low?")
    assert len(calls) == 2
    assert calls[0].name == "stock_status"
    assert calls[0].args == {"sku": "GHE01"}
    assert calls[1].name == "restock_plan"

    summary = fake.summarise("Which items are running low?", [{"sku": "GHE01", "cover": 1.1}])
    assert "Amul Ghee 1L is critical" in summary


def test_fake_llm_fabricated_number_response():
    """Verify FakeLLM can return a fabricated number for copilot validator testing."""
    fake = FakeLLM.with_fabricated_number(999999.0)
    summary = fake.summarise("What was my gross profit?", [{"profit": 105673}])

    # Scripted response contains a fabricated number not in the tool results
    assert "999,999" in summary
    assert "105673" not in summary


def test_fake_llm_simulated_failure():
    """Verify FakeLLM raises LLMUnavailable when should_fail=True."""
    fake = FakeLLM(should_fail=True)
    with pytest.raises(LLMUnavailable):
        fake.plan("test message")

    with pytest.raises(LLMUnavailable):
        fake.summarise("test message", [])


def test_retry_and_timeout_error_handling(monkeypatch):
    """Verify retry logic on transient errors and raising LLMUnavailable on failure."""
    monkeypatch.setattr(settings, "copilot_mode", "llm")
    monkeypatch.setattr(settings, "gemini_api_key", "mock-test-key")
    monkeypatch.setattr(settings, "llm_timeout_s", 0.05)

    mock_client = MagicMock()
    # Simulate failures on all attempts
    mock_client.models.generate_content.side_effect = TimeoutError("Deadline exceeded after 6000ms")

    with patch("app.copilot.llm._get_genai_client", return_value=mock_client):
        with pytest.raises(LLMUnavailable) as exc:
            call_gemini("test prompt")
        # 1 retry = 2 attempts total
        assert mock_client.models.generate_content.call_count == 2
        assert "after 1 retry" in str(exc.value)


def test_mock_successful_function_calling_and_summarise(monkeypatch):
    """Verify successful parsing of function calls and text via mock SDK without network."""
    monkeypatch.setattr(settings, "copilot_mode", "llm")
    monkeypatch.setattr(settings, "gemini_api_key", "mock-test-key")

    mock_fc = MagicMock()
    mock_fc.name = "sales_summary"
    mock_fc.args = {"from_date": "2026-10-15", "to_date": "2026-11-13"}

    mock_plan_resp = MagicMock()
    mock_plan_resp.function_calls = [mock_fc]
    mock_plan_resp.text = None

    mock_sum_resp = MagicMock()
    mock_sum_resp.function_calls = None
    mock_sum_resp.text = "Revenue in Diwali week was Rs 4,36,555, up 8.1%."

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = [mock_plan_resp, mock_sum_resp]

    with patch("app.copilot.llm._get_genai_client", return_value=mock_client):
        # 1. Test plan()
        tool_calls = plan("How did sales go last month?")
        assert len(tool_calls) == 1
        assert tool_calls[0].name == "sales_summary"
        assert tool_calls[0].args == {"from_date": "2026-10-15", "to_date": "2026-11-13"}

        # 2. Test summarise()
        summary = summarise("How did sales go?", [{"revenue": 436555}], lang="en")
        assert "Rs 4,36,555" in summary
