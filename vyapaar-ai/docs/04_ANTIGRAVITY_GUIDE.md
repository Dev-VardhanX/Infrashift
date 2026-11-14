# 04. Building with Antigravity: team workflow and prompts

> Antigravity is an agent-first IDE, so features and menu names change between versions. Treat the specifics below as a starting point and check your installed version (Agent Manager, Editor view, Customizations/Rules, Workflows, Browser).

## 1. Setup (everyone, H0, 15 min)
1. Clone the repo, create your branch `mX/...`, and open the **repo root** as the workspace.
2. Make sure `AGENTS.md` is at the repo root. Also paste its contents into Antigravity's workspace rules (Customizations -> Rules, usually `.agent/rules/`) if your version does not read `AGENTS.md` automatically. Commit that file so all four members share identical rules.
3. Put `GEMINI_API_KEY` in your local `.env` (never commit).
4. Pin context for the agent: tell it to read `README.md`, `docs/01_PRD.md`, `docs/02_SYSTEM_DESIGN.md` before coding. Reference files with `@` mentions where supported.
5. Choose a model per task: the strongest available model for planning and analytics logic; a faster one for UI polish and boilerplate.

## 2. How to work with the agents (rules of thumb)

- **Plan first, then build.** Ask the agent for a short plan and the files it will touch. Approve, then let it implement. Reject plans that touch another member's folders.
- **One task per agent conversation.** Small, testable tasks (30-90 min each). Long vague tasks produce messy diffs.
- **Spec by reference, not by retelling.** "Implement tool `restock_plan` exactly as in docs/02 section 4 and 6.2" beats a paragraph of improvisation.
- **Tests before trust.** For anything numeric, ask the agent to write the test from `docs/06_GOLDEN_NUMBERS.md` first, then the code. Run it yourself.
- **Parallel agents are fine, parallel edits to the same files are not.** Use Agent Manager to run several agents, but give each a disjoint folder, ideally in its own worktree or branch.
- **Review every diff.** Agents will happily invent an API field or hard-code a number. Search the diff for hard-coded values like `1432103`; golden numbers belong only in tests.
- **Use the browser agent for UI checks:** "Open localhost:5173, load the sample store, screenshot the dashboard, and list anything that looks broken on a 390px-wide viewport." Attach the screenshot to the PR.
- **Keep prompts and results.** Paste the final prompt into the PR description; it helps teammates reproduce.
- **Commit often** (before and after each agent task) so a bad run is one `git restore` away.

## 3. Copy-paste prompts (edit the bracketed parts)

### M1: skeleton and ingest
```
Read README.md, docs/01_PRD.md and docs/02_SYSTEM_DESIGN.md and AGENTS.md.
Task: create the backend skeleton under backend/ (FastAPI, SQLite via sqlite3 or SQLModel, pandas).
1) POST /api/load-sample loads the 7 CSVs from data/sample into SQLite tables exactly as in doc 02 section 2.
2) POST /api/upload accepts multiple CSVs, runs the ingest rules in doc 02 section 2 (lenient dates, payment_mode normalisation, row rejection with reasons, fuzzy column mapping) and returns the validation report shape from section 3.
3) Add a `sales_enriched` view/dataframe builder (taxable value, GST, cost at sale from the 60-day weighted average of purchases, line profit).
Only edit files in backend/app/{main.py,db.py,ingest/}. Write pytest tests with a tiny fixture. Do not change the API contract. Show me the plan first.
```

### M1: LLM adapter
```
In backend/app/copilot/llm.py implement a Gemini function-calling adapter. Interface: `plan(message, tool_schemas) -> list[ToolCall]` and `summarise(message, tool_results, lang) -> str`. Read GEMINI_API_KEY from env, 6-second timeout, one retry, and raise `LLMUnavailable` on any failure so the caller can use the fallback router. Add a FakeLLM for tests. Do not put any business logic here.
```

### M2: analytics tools
```
Read docs/01_PRD.md section 4 (metric definitions), docs/02_SYSTEM_DESIGN.md sections 4 and 6, and docs/06_GOLDEN_NUMBERS.md.
Task: implement the analytics tools in backend/app/analytics/ one file per tool, each returning {"data","meta":{"method","row_count","as_of"}}.
First write backend/tests/test_golden.py using the golden numbers, then implement `periods.py` (tokens like last_30d, prev_30d, diwali_week resolved against AS_OF), `sales_summary`, `top_products`, `compare_periods`, `margin_by_product`. Make the tests pass. Margin must use taxable value, not MRP. Do not touch any folder except backend/app/analytics and backend/tests.
```

### M2: insights and copilot
```
Implement backend/app/insights/ per doc 02 section 6.3 (restock, dead_stock, margin_leak, expense_anomaly, khata_overdue, festive_lift), returning Insight objects exactly as in section 3.2. Implement the demand forecast and restock status in section 6.1 and 6.2, including FESTIVAL_OVER for Puja & Decor after Diwali. Verify the planted insights listed in docs/06_GOLDEN_NUMBERS.md are all produced and that no restock alert is raised for Puja & Decor items.
Then implement backend/app/copilot/{router.py,validate.py,templates.py}: tool-calling orchestration with max 3 calls, the number validator (every number in the final text must appear in tool output within 0.5%), template fallback per tool, and a keyword fallback router with English and Hinglish keywords. Write tests including one where the LLM returns a fabricated number and the validator rejects it.
```

### M3: frontend
```
Read docs/01_PRD.md (US-2 to US-5) and docs/02_SYSTEM_DESIGN.md section 3 (API contract). Build the React + Vite + Tailwind + Recharts frontend in frontend/.
Start with src/api/ that reads from mock JSON files shaped exactly like the contract, switchable to the real API by an env flag.
Pages: Upload/Load sample (with validation report), Dashboard (KPI tiles with delta arrows, daily revenue line with a Diwali marker, category bars, payment-mix donut, top products), Insights feed (cards with severity, evidence table, action button), Restock (table, row selection, Draft PO modal with Copy and WhatsApp), Khata (overdue list, Send reminder), Chat (messages, result table/chart, collapsible 'How I calculated this', 'Verified against your data' badge).
Mobile-first, Indian number formatting (lakh/crore), loading/empty/error states on every screen. Only edit files in frontend/. Use the browser to screenshot at 390px and 1280px and fix layout problems.
```

### M4: actions, tests, demo
```
Implement backend/app/actions/ with two pure functions: `purchase_order_text(supplier, items)` and `khata_reminder_text(name, balance, last_payment_date, lang)` plus `wa_link(phone, text)` using wa.me with URL encoding, as in doc 02 section 6.4. Add pytest tests. Keep Hindi (Devanagari and Hinglish) strings in a single strings.py. Do not edit other folders.
```
```
Write scripts/check_golden.py that loads data/sample into pandas independently of the backend (no shared code) and prints the golden numbers from docs/06_GOLDEN_NUMBERS.md so we can compare the backend against an independent calculation.
```

## 4. Troubleshooting
- **Agent edited files outside its scope:** `git restore` those paths; re-prompt with the folder restriction in the first line.
- **Agent invents API fields:** paste the exact JSON shape from doc 02 into the prompt and say "match exactly".
- **Numbers don't match golden values:** first check the margin definition (taxable vs MRP) and the AS_OF date; those two cause most mismatches.
- **Gemini quota or latency issues:** switch to fallback mode (`COPILOT_MODE=fallback` in `.env`) and keep building; M1 owns this switch.
