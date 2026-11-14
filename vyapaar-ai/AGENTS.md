# AGENTS.md: rules for AI coding agents (Antigravity, Gemini, Claude, etc.)

Project: Vyapaar AI, an AI operations copilot for small Indian businesses (kirana store demo).
Read first: `README.md`, `docs/01_PRD.md`, `docs/02_SYSTEM_DESIGN.md`. They are the source of truth.

## Hard rules
1. **Never compute or invent business numbers in LLM output or UI code.** Numbers come from `backend/app/analytics/` tools only. The copilot selects tools; it never writes SQL or does arithmetic itself.
2. **Do not change the API contract or metric definitions** (docs 01 and 02) without being told. If the contract seems wrong, stop and say so.
3. **Stay inside the owner's folders** given in the task. Do not edit other members' files. If a change elsewhere is needed, describe it instead of making it.
4. Money is INR. Format with the Indian grouping (Rs 14,32,103 or 14.3 lakh). Dates ISO internally, `DD MMM` in UI. "Today" is `AS_OF = max(sales.date)`, never the system clock.
5. Gross margin uses **taxable value** (price / (1 + GST%)), not MRP.
6. No secrets in code. Read `GEMINI_API_KEY` from `.env`. Never log customer phone numbers.
7. Keep changes small and runnable. After every change, run the relevant tests and report the result.

## Stack
Backend: Python 3.11, FastAPI, pandas, SQLite, pydantic, pytest, rapidfuzz. Frontend: React, Vite, Tailwind, Recharts. LLM: Gemini function calling behind `copilot/llm.py` with a rule-based fallback.

## Commands
- Backend: `cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && uvicorn app.main:app --reload`
- Tests: `cd backend && pytest -q`
- Frontend: `cd frontend && npm install && npm run dev`
- Sample data: `python data/generate_data.py data/sample` (deterministic)

## Code style
Type hints everywhere in Python; small pure functions; each analytics tool returns `{"data":..., "meta":{"method","row_count","as_of"}}`. UI: functional components, no global state library, one `api/` module that wraps fetch, loading + empty + error state on every screen. Mobile-first layout (the owner uses a phone).

## Definition of done for any task
Runs on the sample data, has a test or screenshot, matches the contract, and `docs/` is updated if behavior changed.

## When unsure
Ask a short question rather than guessing. Prefer the simplest implementation that satisfies the acceptance criteria in `docs/01_PRD.md`.
