"""M1: Gemini function-calling adapter using the official Google Gen AI Python SDK (google-genai).

Docs & PRD:
- Interface: plan(message, tool_schemas) -> list[ToolCall] and summarise(message, tool_results, lang) -> str
- Model name is read from env GEMINI_MODEL (never hard-coded)
- COPILOT_MODE in {auto, llm, fallback}: fallback mode NEVER calls the network
- 6-second timeout, one retry, raise LLMUnavailable on failure
- Never log API key or customer phone numbers
- FakeLLM for tests with scripted responses (including fabricated number response)
- No business logic here (transport adapter only).
"""
from dataclasses import dataclass, field
import json
import re
import time
from typing import Any, Callable

from app.config import settings

# Sensitive pattern matching for sanitisation: 10-digit phone numbers and API keys
PHONE_PATTERN = re.compile(
    r"(?:\+?91[-\s]?)?[6-9]\d{4}[-\s]?\d{5}\b|\b(?:\+?91[-\s]?)?[6-9]\d{9}\b"
)


@dataclass
class ToolCall:
    name: str
    args: dict[str, Any] = field(default_factory=dict)


class LLMUnavailable(Exception):
    """Raised when the LLM is unconfigured, unreachable, timed out, or in fallback mode."""


# Backward compatibility alias
LLMError = LLMUnavailable

SYSTEM_PROMPT_PLAN = (
    "You are a business analyst for an Indian kirana. You may only answer by "
    "calling tools. Never state a number that did not come from a tool. If no tool fits, say so."
)

SYSTEM_PROMPT_SUMMARISE = (
    "You are a helpful business operations assistant for an Indian kirana store. "
    "Provide a concise, clear 2-3 sentence summary based STRICTLY on the tool results provided. "
    "Do not invent or extrapolate numbers."
)


def _sanitize(text: str) -> str:
    """Mask any API keys or customer phone numbers to prevent leakage in logs/errors."""
    if not text:
        return ""
    key = settings.gemini_api_key
    if key and key in text:
        text = text.replace(key, "[REDACTED_API_KEY]")
    # Mask Indian phone numbers
    return PHONE_PATTERN.sub("[REDACTED_PHONE]", text)


def get_copilot_mode() -> str:
    """Return normalised COPILOT_MODE in {'auto', 'llm', 'fallback'}."""
    mode = (settings.copilot_mode or "auto").strip().lower()
    if mode in ("auto", "llm", "fallback"):
        return mode
    return "auto"


def is_configured() -> bool:
    """Return True if Gemini is configured and enabled to make network calls."""
    mode = get_copilot_mode()
    if mode == "fallback":
        return False
    if mode in ("llm", "auto"):
        return bool(settings.gemini_api_key)
    return False


def _get_genai_client() -> Any:
    """Initialize the official Google Gen AI Client (never called in fallback mode)."""
    mode = get_copilot_mode()
    if mode == "fallback":
        raise LLMUnavailable("COPILOT_MODE is 'fallback': network calls are disabled")
    if not settings.gemini_api_key:
        raise LLMUnavailable(f"GEMINI_API_KEY is not set (COPILOT_MODE={mode})")

    try:
        from google import genai
        return genai.Client(api_key=settings.gemini_api_key)
    except ImportError as exc:
        raise LLMUnavailable(f"google-genai SDK not installed: {_sanitize(str(exc))}") from exc
    except Exception as exc:
        raise LLMUnavailable(f"Failed to initialize GenAI client: {_sanitize(str(exc))}") from exc


def _format_tools(tool_schemas: list[Any] | None) -> list[Any] | None:
    """Format tool schemas into types.Tool accepted by google-genai."""
    if not tool_schemas:
        return None
    try:
        from google.genai import types
    except ImportError:
        return tool_schemas

    tools: list[Any] = []
    func_decls: list[Any] = []
    for item in tool_schemas:
        if isinstance(item, types.Tool):
            tools.append(item)
        elif isinstance(item, types.FunctionDeclaration):
            func_decls.append(item)
        elif isinstance(item, dict):
            if "function_declarations" in item:
                tools.append(types.Tool(**item))
            else:
                func_decls.append(types.FunctionDeclaration(**item))
        elif callable(item):
            tools.append(item)

    if func_decls:
        tools.append(types.Tool(function_declarations=func_decls))
    return tools or None


def call_gemini(
    message: str,
    *,
    system_prompt: str | None = None,
    tool_schemas: list[Any] | None = None,
    timeout_s: float | None = None,
) -> dict[str, Any]:
    """Execute Gemini request via official SDK with timeout and 1 retry; returns text & tool_calls."""
    # Enforce fallback guard without hitting network
    if get_copilot_mode() == "fallback":
        raise LLMUnavailable("COPILOT_MODE is 'fallback': network calls are disabled")

    client = _get_genai_client()
    from google.genai import types

    timeout_s = timeout_s or settings.llm_timeout_s
    timeout_ms = int(timeout_s * 1000)

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=_format_tools(tool_schemas),
        temperature=0.0,
        http_options=types.HttpOptions(timeout=timeout_ms),
    )

    last_err: Exception | None = None
    for attempt in range(2):  # 1 retry = 2 attempts total
        try:
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=message,
                config=config,
            )
            text = response.text
            tool_calls: list[dict[str, Any]] = []
            if response.function_calls:
                for fc in response.function_calls:
                    args = dict(fc.args or {})
                    tool_calls.append({"name": fc.name, "args": args})

            if not text and not tool_calls:
                raise LLMUnavailable("Gemini returned an empty response")
            return {"text": text, "tool_calls": tool_calls}
        except Exception as exc:
            last_err = exc
            if attempt == 0:
                time.sleep(0.5)

    clean_err = _sanitize(str(last_err))
    raise LLMUnavailable(f"Gemini call failed after 1 retry: {clean_err}") from last_err


def plan(
    message: str,
    tool_schemas: list[Any] | None = None,
    *,
    timeout_s: float | None = None,
) -> list[ToolCall]:
    """Ask Gemini to select tool(s) for the user query using function calling."""
    if get_copilot_mode() == "fallback":
        raise LLMUnavailable("COPILOT_MODE is 'fallback': network calls are disabled")

    res = call_gemini(
        message,
        system_prompt=SYSTEM_PROMPT_PLAN,
        tool_schemas=tool_schemas,
        timeout_s=timeout_s,
    )
    return [
        ToolCall(name=tc["name"], args=tc.get("args", {}))
        for tc in res.get("tool_calls", [])
    ]


def summarise(
    message: str,
    tool_results: list[dict[str, Any]],
    lang: str | None = None,
    *,
    timeout_s: float | None = None,
) -> str:
    """Summarise tool results in 2-3 sentences in the requested language."""
    if get_copilot_mode() == "fallback":
        raise LLMUnavailable("COPILOT_MODE is 'fallback': network calls are disabled")

    lang_instruction = f" Respond in {lang}." if lang else ""
    # Sanitize tool results before constructing prompt so phone numbers do not reach the LLM
    clean_results = _sanitize(json.dumps(tool_results, indent=2, default=str))
    prompt = (
        f"User question: {_sanitize(message)}\n\n"
        f"Tool execution results:\n{clean_results}\n\n"
        f"Please summarise the findings.{lang_instruction}"
    )

    res = call_gemini(
        prompt,
        system_prompt=SYSTEM_PROMPT_SUMMARISE,
        timeout_s=timeout_s,
    )
    return res.get("text") or ""


def call_gemini_json(message: str, *, timeout_s: float | None = None) -> str:
    """Plain completion helper."""
    result = call_gemini(message, timeout_s=timeout_s)
    return result.get("text") or ""


def make_tool_executor(executor: Callable[[str, dict[str, Any]], dict[str, Any]]) -> Callable:
    """Wrap an M2 tool executor safely."""
    def _run(tool_name: str, args_json: str | dict) -> dict[str, Any]:
        args = json.loads(args_json) if isinstance(args_json, str) else dict(args_json)
        return executor(tool_name, args)
    return _run


class FakeLLM:
    """Mock LLM adapter for deterministic unit testing with zero network calls."""

    def __init__(
        self,
        plan_responses: list[list[ToolCall]] | None = None,
        summarise_responses: list[str] | None = None,
        should_fail: bool = False,
    ) -> None:
        self.plan_responses: list[list[ToolCall]] = list(plan_responses or [])
        self.summarise_responses: list[str] = list(summarise_responses or [])
        self.should_fail = should_fail
        self.plan_calls: list[dict[str, Any]] = []
        self.summarise_calls: list[dict[str, Any]] = []

    def plan(
        self,
        message: str,
        tool_schemas: list[Any] | None = None,
        *,
        timeout_s: float | None = None,
    ) -> list[ToolCall]:
        self.plan_calls.append({"message": message, "tool_schemas": tool_schemas})
        if self.should_fail:
            raise LLMUnavailable("FakeLLM simulated failure")
        if self.plan_responses:
            return self.plan_responses.pop(0)
        return []

    def summarise(
        self,
        message: str,
        tool_results: list[dict[str, Any]],
        lang: str | None = None,
        *,
        timeout_s: float | None = None,
    ) -> str:
        self.summarise_calls.append({"message": message, "tool_results": tool_results, "lang": lang})
        if self.should_fail:
            raise LLMUnavailable("FakeLLM simulated failure")
        if self.summarise_responses:
            return self.summarise_responses.pop(0)
        return "Fake summary based on tool results."

    @classmethod
    def with_fabricated_number(cls, fake_number: float = 999999.0) -> "FakeLLM":
        """Scripted mock response containing a fabricated number not in tool output."""
        return cls(
            summarise_responses=[f"Your total profit was Rs {fake_number:,.0f}."]
        )
