"""M1: FastAPI application — endpoints wired per doc 02 section 3.

Endpoints:
- GET /api/dashboard?from=&to= (shape 3.1, in-memory cache, default last_30d)
- GET /api/inventory/alerts (shape 3.3)
- GET /api/insights (shape 3.2)
- GET /api/khata/overdue?days=45
- POST /api/actions/draft (type: purchase_order | khata_reminder)
- POST /api/chat (copilot router)
- POST /api/load-sample & POST /api/upload (data ingestion)
- GET /api/health & GET /health

Thin endpoints: call external modules in analytics/, insights/, actions/, and copilot/.
Never compute business numbers here. Return code "not_ready" if imported module is missing.
All errors follow {"error": {"code": "...", "message": "..."}}. Never return a stack trace.
"""
import asyncio
import contextlib
import logging
from pathlib import Path
import re
import time
from typing import Any, Iterator

from fastapi import FastAPI, File, Query, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import Response

from app import db as db_module
from app.config import DIWALI_DATE, settings
from app.copilot import llm as llm_adapter
from app.db import store
from app.ingest import loaders

logger = logging.getLogger("vyapaar.api")

PHONE_PATTERN = re.compile(
    r"(?:\+?91[-\s]?)?[6-9]\d{4}[-\s]?\d{5}\b|\b(?:\+?91[-\s]?)?[6-9]\d{9}\b"
)


def sanitize_text(text: str) -> str:
    """Mask any API keys or customer phone numbers to prevent leakage in logs/errors."""
    if not text:
        return ""
    key = settings.gemini_api_key
    if key and key in text:
        text = text.replace(key, "[REDACTED_API_KEY]")
    return PHONE_PATTERN.sub("[REDACTED_PHONE]", text)


class SensitiveDataFilter(logging.Filter):
    """Ensure no log record ever emits raw phone numbers or API keys."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = sanitize_text(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: sanitize_text(str(v)) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    sanitize_text(str(v)) if isinstance(v, (str, int)) and len(str(v)) >= 10 else v
                    for v in record.args
                )
        return True


# Attach privacy filter to relevant loggers
logging.getLogger("vyapaar").addFilter(SensitiveDataFilter())
logging.getLogger("uvicorn.access").addFilter(SensitiveDataFilter())


class NotReady(Exception):
    """Raised when an external module owned by another member is not yet implemented."""

    def __init__(self, function_needed: str, module_path: str) -> None:
        self.function_needed = function_needed
        self.module_path = module_path
        self.message = (
            f"Function '{function_needed}' from '{module_path}' is not implemented yet. "
            f"Please implement '{function_needed}' in '{module_path}'."
        )
        super().__init__(self.message)


@contextlib.asynccontextmanager
async def lifespan(app_instance: FastAPI) -> Iterator[None]:
    """Manage application startup and shutdown lifecycle.

    Startup behaviour: if the database is empty, auto-loads the sample dataset
    from data/sample if available; otherwise logs a clear actionable message.
    """
    with open_db() as conn:
        empty = db_module.is_empty(conn)
        if empty and settings.auto_load_sample:
            sample_dir = settings.sample_data_dir
            if sample_dir.exists() and (sample_dir / "sales.csv").exists():
                logger.info(
                    "[STARTUP] Database is empty. Auto-loading sample dataset from %s...",
                    sample_dir,
                )
                try:
                    counts, as_of_val = loaders.load_sample(conn)
                    logger.info(
                        "[STARTUP] Successfully auto-loaded sample dataset: %s rows across %d tables (as_of=%s)",
                        counts.get("sales", 0),
                        len(counts),
                        as_of_val,
                    )
                except Exception as exc:
                    logger.warning(
                        "[STARTUP] Failed to auto-load sample data: %s. Call POST /api/load-sample manually.",
                        sanitize_text(str(exc)),
                    )
            else:
                logger.warning(
                    "[STARTUP] Database is empty and sample data directory not found at %s. "
                    "Please populate data using POST /api/load-sample or POST /api/upload.",
                    sample_dir,
                )
        elif empty:
            logger.info(
                "[STARTUP] Database is empty (AUTO_LOAD_SAMPLE=false). "
                "Awaiting data load via POST /api/load-sample or POST /api/upload."
            )
        else:
            as_of_val = db_module.as_of(conn)
            logger.info(
                "[STARTUP] Database ready (as_of=%s, data_version=%s)",
                as_of_val,
                db_module.data_version(conn),
            )
    yield


app = FastAPI(title="Vyapaar AI", version="0.1.0", lifespan=lifespan)

# CORS configuration supporting Vite frontend dev port (5173), Next (3000), and all localhost dev ports
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next: Any) -> Response:
    """Log incoming requests and responses while strictly masking phone numbers and secrets."""
    start_time = time.perf_counter()

    raw_query = str(request.url.query) if request.url.query else ""
    safe_query = sanitize_text(raw_query)
    safe_path = sanitize_text(request.url.path)
    safe_target = f"{safe_path}?{safe_query}" if safe_query else safe_path

    client_host = request.client.host if request.client else "unknown"
    logger.info("--> %s %s from %s", request.method, safe_target, client_host)

    try:
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "<-- %s %s [%s] in %.1fms",
            request.method,
            safe_target,
            response.status_code,
            duration_ms,
        )
        return response
    except Exception as exc:
        duration_ms = (time.perf_counter() - start_time) * 1000
        safe_exc = sanitize_text(str(exc))
        logger.error(
            "<!- %s %s failed in %.1fms: %s",
            request.method,
            safe_target,
            duration_ms,
            safe_exc,
        )
        raise


# Contract error handlers: Never return a stack trace, sanitize all output
@app.exception_handler(NotReady)
async def not_ready_handler(_request: Request, exc: NotReady) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"error": {"code": "not_ready", "message": sanitize_text(exc.message)}},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"error": {"code": "validation_error", "message": sanitize_text(str(exc))}},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "http_error", "message": sanitize_text(str(exc.detail))}},
    )


@app.exception_handler(Exception)
async def unhandled_handler(_request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal_error", "message": sanitize_text(f"unexpected error: {exc}")}},
    )


@contextlib.contextmanager
def open_db() -> Iterator[Any]:
    conn = db_module.get_conn()
    try:
        yield conn
    finally:
        conn.close()


def resolve_callable(module_path: str, attr_names: list[str] | str) -> Any:
    """Import an external module attribute; raises NotReady with human-readable error if absent."""
    attrs = [attr_names] if isinstance(attr_names, str) else attr_names
    try:
        module = __import__(module_path, fromlist=attrs)
    except ImportError:
        raise NotReady(attrs[0], module_path)

    for attr in attrs:
        fn = getattr(module, attr, None)
        if callable(fn):
            return fn

    raise NotReady(attrs[0], module_path)


# In-memory dashboard cache keyed by (from_date, to_date, store.data_version)
_dashboard_cache: dict[tuple[str, str, str], dict[str, Any]] = {}


def resolve_dashboard_period(
    from_d: str | None,
    to_d: str | None,
    as_of: str | None,
) -> tuple[str, str, str, str]:
    """Resolve default (from, to, prev_from, prev_to) defaulting to last_30d and prev_30d."""
    base_as_of = as_of or "2026-11-13"
    try:
        as_of_dt = pd.to_datetime(base_as_of)
    except Exception:
        as_of_dt = pd.Timestamp("2026-11-13")

    if not from_d or not to_d:
        to_dt = as_of_dt
        from_dt = to_dt - pd.Timedelta(days=29)
        final_to = to_dt.strftime("%Y-%m-%d")
        final_from = from_dt.strftime("%Y-%m-%d")
    else:
        final_from = from_d.strip()
        final_to = to_d.strip()
        try:
            from_dt = pd.to_datetime(final_from)
        except Exception:
            from_dt = as_of_dt - pd.Timedelta(days=29)

    try:
        to_parsed = pd.to_datetime(final_to)
        days_len = (to_parsed - from_dt).days + 1
    except Exception:
        days_len = 30

    prev_to_dt = from_dt - pd.Timedelta(days=1)
    prev_from_dt = prev_to_dt - pd.Timedelta(days=days_len - 1)
    prev_from = prev_from_dt.strftime("%Y-%m-%d")
    prev_to = prev_to_dt.strftime("%Y-%m-%d")

    return final_from, final_to, prev_from, prev_to


# ---------------------------------------------------------------- health ---

@app.get("/api/health")
@app.get("/health")
def health() -> dict:
    """System health check and diagnostic status."""
    with open_db() as conn:
        empty = db_module.is_empty(conn)
        as_of_val = db_module.as_of(conn)
        return {
            "ok": True,
            "status": "ready" if not empty else "empty_database",
            "as_of": as_of_val,
            "data_version": db_module.data_version(conn),
            "database_empty": empty,
            "llm_configured": llm_adapter.is_configured(),
            "copilot_mode": llm_adapter.get_copilot_mode(),
            "message": (
                "Store database is ready"
                if not empty
                else "Database is empty. Please call POST /api/load-sample or POST /api/upload."
            ),
        }


# --------------------------------------------------------------- ingest ---

@app.post("/api/load-sample")
def load_sample() -> dict:
    with open_db() as conn:
        counts, as_of_val = loaders.load_sample(conn)
    _dashboard_cache.clear()
    return {"loaded": counts, "as_of": as_of_val}


@app.post("/api/upload")
async def upload(files: list[UploadFile] = File(...)) -> Any:
    if len(files) > 20:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "too_many_files", "message": "upload at most 20 files at once"}},
        )
    payload: dict[str, bytes] = {}
    for f in files:
        content = await f.read()
        filename = f.filename or "unnamed"
        if not filename.lower().endswith(".csv"):
            payload[filename] = b""
        payload[filename] = content
    with open_db() as conn:
        try:
            reports, as_of_val = loaders.ingest_files(conn, payload)
        except Exception as exc:
            return JSONResponse(
                status_code=400,
                content={"error": {"code": "ingest_failed", "message": sanitize_text(f"could not import files: {exc}")}},
            )
    _dashboard_cache.clear()
    return {"files": reports, "as_of": as_of_val}


# ------------------------------------------------- tool-backed endpoints ---

@app.get("/api/dashboard")
async def dashboard(
    from_d: str | None = Query(None, alias="from"),
    to_d: str | None = Query(None, alias="to"),
) -> Any:
    """GET /api/dashboard shape 3.1: in-memory cache keyed by (from, to, store.data_version)."""
    as_of_val = store.as_of
    from_date, to_date, prev_from, prev_to = resolve_dashboard_period(from_d, to_d, as_of_val)

    cache_key = (from_date, to_date, store.data_version)
    if cache_key in _dashboard_cache:
        return _dashboard_cache[cache_key]

    run_tool = resolve_callable(
        "app.analytics.dashboard", ["get_dashboard", "dashboard", "run_tool"]
    )

    def _execute():
        with open_db() as conn:
            try:
                return run_tool(
                    from_date=from_date,
                    to_date=to_date,
                    prev_from=prev_from,
                    prev_to=prev_to,
                    conn=conn,
                )
            except TypeError:
                try:
                    return run_tool(conn, from_date=from_date, to_date=to_date)
                except TypeError:
                    return run_tool("dashboard", conn, from_d=from_date, to_d=to_date)

    loop = asyncio.get_running_loop()
    try:
        raw = await asyncio.wait_for(loop.run_in_executor(None, _execute), timeout=10.0)
    except (TimeoutError, asyncio.TimeoutError):
        return JSONResponse(
            status_code=504,
            content={"error": {"code": "timeout", "message": "Dashboard calculation timed out after 10s"}},
        )

    result = raw if isinstance(raw, dict) else {"data": raw}
    result.setdefault("as_of", as_of_val)
    result.setdefault("period", {"from": from_date, "to": to_date})
    result.setdefault("markers", [{"date": DIWALI_DATE, "label": "Diwali"}])

    _dashboard_cache[cache_key] = result
    return result


@app.get("/api/inventory/alerts")
async def inventory_alerts() -> Any:
    """GET /api/inventory/alerts shape 3.3."""
    fn = resolve_callable(
        "app.analytics.inventory", ["get_alerts", "inventory_alerts", "restock_plan", "run_tool"]
    )

    def _execute():
        with open_db() as conn:
            try:
                return fn(conn)
            except TypeError:
                return fn("restock_plan", conn)

    loop = asyncio.get_running_loop()
    try:
        raw = await asyncio.wait_for(loop.run_in_executor(None, _execute), timeout=10.0)
    except (TimeoutError, asyncio.TimeoutError):
        return JSONResponse(
            status_code=504,
            content={"error": {"code": "timeout", "message": "Inventory alerts calculation timed out after 10s"}},
        )

    items = raw if isinstance(raw, list) else raw.get("items", raw.get("data", []))
    return {
        "items": items,
        "as_of": store.as_of,
    }


@app.get("/api/insights")
async def insights() -> Any:
    """GET /api/insights shape 3.2."""
    fn = resolve_callable("app.insights.engine", ["run_insights", "get_insights", "insights"])

    def _execute():
        with open_db() as conn:
            return fn(conn)

    loop = asyncio.get_running_loop()
    try:
        raw = await asyncio.wait_for(loop.run_in_executor(None, _execute), timeout=10.0)
    except (TimeoutError, asyncio.TimeoutError):
        return JSONResponse(
            status_code=504,
            content={"error": {"code": "timeout", "message": "Insights generation timed out after 10s"}},
        )

    insights_list = raw if isinstance(raw, list) else raw.get("insights", raw.get("data", []))
    return {
        "insights": insights_list,
    }


@app.get("/api/khata/overdue")
async def khata_overdue(days: int = Query(None)) -> Any:
    """GET /api/khata/overdue?days=45."""
    min_days = days if days is not None else settings.overdue_days
    fn = resolve_callable(
        "app.analytics.khata", ["get_overdue", "khata_overdue", "run_tool"]
    )

    def _execute():
        with open_db() as conn:
            try:
                return fn(min_days=min_days, conn=conn)
            except TypeError:
                try:
                    return fn(conn, min_days=min_days)
                except TypeError:
                    return fn("khata_overdue", conn, min_days=min_days)

    loop = asyncio.get_running_loop()
    try:
        raw = await asyncio.wait_for(loop.run_in_executor(None, _execute), timeout=10.0)
    except (TimeoutError, asyncio.TimeoutError):
        return JSONResponse(
            status_code=504,
            content={"error": {"code": "timeout", "message": "Khata overdue query timed out after 10s"}},
        )

    customers = raw if isinstance(raw, list) else raw.get("customers", raw.get("data", []))
    return {
        "customers": customers,
    }


@app.post("/api/actions/draft")
async def actions_draft(payload: dict) -> Any:
    """POST /api/actions/draft (type: purchase_order | khata_reminder)."""
    draft_type = (payload or {}).get("type")
    ids = (payload or {}).get("ids", [])
    if draft_type not in ("purchase_order", "khata_reminder"):
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "bad_type", "message": "type must be purchase_order or khata_reminder"}},
        )

    fn = resolve_callable("app.actions.drafts", ["make_drafts", "create_drafts", "draft"])

    def _execute():
        with open_db() as conn:
            try:
                return fn(draft_type, ids, conn=conn)
            except TypeError:
                return fn(draft_type, ids)

    loop = asyncio.get_running_loop()
    try:
        raw = await asyncio.wait_for(loop.run_in_executor(None, _execute), timeout=10.0)
    except (TimeoutError, asyncio.TimeoutError):
        return JSONResponse(
            status_code=504,
            content={"error": {"code": "timeout", "message": "Draft action generation timed out after 10s"}},
        )

    drafts = raw if isinstance(raw, list) else raw.get("drafts", raw.get("data", []))
    return {
        "drafts": drafts,
    }


def _invoke_router_fn(fn: Any, message: str, conn: Any, lang: str | None, mode: str) -> dict[str, Any]:
    """Invoke M2 router function handling signature variations."""
    try:
        return fn(message=message, conn=conn, lang=lang, mode=mode)
    except TypeError:
        try:
            return fn(message, conn, lang, mode)
        except TypeError:
            try:
                return fn(message, conn, lang=lang)
            except TypeError:
                return fn(message, conn)


@app.post("/api/chat")
async def chat(payload: dict) -> Any:
    """POST /api/chat {message, lang?} returning {answer, blocks, calc, validated, mode, rule_based}.

    M1 owns: mode selection (COPILOT_MODE), the 6s timeout, and automatic fallback
    to the rule-based router when LLMUnavailable or timeout occurs.
    """
    message = (payload or {}).get("message", "").strip()
    lang = (payload or {}).get("lang")
    if not message:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "empty_message", "message": 'send {"message": "..."}'}},
        )

    mode = llm_adapter.get_copilot_mode()  # "auto", "llm", "fallback"
    loop = asyncio.get_running_loop()
    timeout_s = settings.llm_timeout_s

    with open_db() as conn:
        # Fallback mode: invoke rule-based router directly with 6s timeout
        if mode == "fallback":
            fallback_fn = resolve_callable(
                "app.copilot.router",
                ["answer_fallback", "fallback_answer", "answer", "chat"],
            )
            try:
                raw = await asyncio.wait_for(
                    loop.run_in_executor(None, _invoke_router_fn, fallback_fn, message, conn, lang, "fallback"),
                    timeout=timeout_s,
                )
            except (TimeoutError, asyncio.TimeoutError):
                return JSONResponse(
                    status_code=504,
                    content={"error": {"code": "timeout", "message": f"Copilot processing timed out after {int(timeout_s)} seconds"}},
                )
            res = raw if isinstance(raw, dict) else {"answer": str(raw)}
            res.setdefault("blocks", [])
            res.setdefault("calc", [])
            res.setdefault("validated", True)
            res["mode"] = "rule_based"
            res["rule_based"] = True
            return res

        # Attempt LLM mode with timeout and automatic fallback to rule-based router
        try:
            fn = resolve_callable(
                "app.copilot.router",
                ["answer", "chat", "answer_llm"],
            )
            raw = await asyncio.wait_for(
                loop.run_in_executor(None, _invoke_router_fn, fn, message, conn, lang, "llm"),
                timeout=timeout_s,
            )
            res = raw if isinstance(raw, dict) else {"answer": str(raw)}
            res.setdefault("blocks", [])
            res.setdefault("calc", [])
            res.setdefault("validated", True)
            res.setdefault("mode", "llm")
            res.setdefault("rule_based", False)
            return res

        except (llm_adapter.LLMUnavailable, TimeoutError, asyncio.TimeoutError):
            # Fall back automatically to the rule-based router with timeout
            fallback_fn = resolve_callable(
                "app.copilot.router",
                ["answer_fallback", "fallback_answer", "answer", "chat"],
            )
            try:
                raw = await asyncio.wait_for(
                    loop.run_in_executor(None, _invoke_router_fn, fallback_fn, message, conn, lang, "fallback"),
                    timeout=timeout_s,
                )
            except (TimeoutError, asyncio.TimeoutError):
                return JSONResponse(
                    status_code=504,
                    content={"error": {"code": "timeout", "message": f"Copilot fallback timed out after {int(timeout_s)} seconds"}},
                )
            res = raw if isinstance(raw, dict) else {"answer": str(raw)}
            res.setdefault("blocks", [])
            res.setdefault("calc", [])
            res.setdefault("validated", True)
            res["mode"] = "rule_based"
            res["rule_based"] = True
            return res
