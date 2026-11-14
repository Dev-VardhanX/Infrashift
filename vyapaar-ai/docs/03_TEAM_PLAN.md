# 03. Team Plan: 4 members, one product

Hour 0 (H0) = kickoff. Timeline assumes about 30 hours; compress proportionally if shorter. **Feature freeze is H24. Last 6 hours are polish, tests, rehearsal. No new features after the freeze.**

## 1. Roles and ownership (each file/folder has exactly one owner)

| | Role | Owns (folders) | Primary deliverables |
|---|---|---|---|
| **M1** | Backend platform and LLM | `backend/app/{main.py,db.py,ingest/,copilot/llm.py}`, `.env.example`, deployment | Repo + FastAPI skeleton, SQLite, CSV ingest + validation, all API endpoints wired, Gemini adapter with timeout + fallback switch |
| **M2** | Analytics and intelligence | `backend/app/{analytics/,insights/,copilot/(router.py,validate.py,templates.py)}`, `backend/tests/` | Metric tools, forecast, restock logic, insight rules, copilot orchestration, number validator, golden tests |
| **M3** | Frontend | `frontend/` (everything) | Dashboard, chat, restock page, khata page, insights feed, upload flow, responsive/mobile-friendly layout |
| **M4** | Product, data, demo and QA | `docs/`, `data/`, `README.md`, demo script, slides, `backend/app/actions/` (text templates), Hindi strings | Keeps docs true, owns sample data + golden numbers, writes action templates, runs test checklist, builds pitch + business case, stretch features (Hindi, weekly report) |

**Why this split:** M1 and M2 meet only at the tool interface (`{data, meta}`) and the API contract (doc 02). M3 meets the backend only through the API contract, and builds against mock JSON on day one. M4 unblocks everyone with data, copy and tests, and is the integration owner.

**Cross-cover (so nobody is a single point of failure):** M1 backs up M2 on tools; M3 and M4 back each other on UI and copy; M2 backs up M3 on charts if behind at C2.

## 2. Timeline and checkpoints

| Hours | M1 | M2 | M3 | M4 |
|---|---|---|---|---|
| **H0-1** | Create repo, push this pack, branch protection, invite all; FastAPI hello-world | Read 02 section 4 + 6; set up pytest | Vite + Tailwind + Recharts scaffold | Confirm assumptions in README, split tasks in board, share Gemini keys |
| **H1-4** (**C1**) | SQLite schema + `/load-sample` loads the 7 CSVs; `/upload` skeleton | Period resolver + `sales_summary`, `top_products`; golden test for revenue | App shell, routes, **mock-API** JSON files copied from doc 02 shapes; KPI tiles with mocks | Write `GOLDEN` verification script; action text templates (PO, reminder); collect 8 demo questions |
| **C1 (H4)** | Demo: `/load-sample` + `/dashboard` returns real revenue | | Demo: UI shell renders from mocks | Check-in 10 min: contract still frozen? |
| **H4-10** (**C2**) | Ingest validation + column mapping; `/dashboard`, `/khata/overdue`; LLM adapter | `margin_by_product`, `compare_periods`, `stock_status`, `restock_plan`, `dead_stock`, `khata_overdue`, `expense_summary`, `payment_mix` | Dashboard charts on real API; upload page with validation report | Unit tests for tools (fixture CSVs); start slide deck skeleton |
| **C2 (H10)** | All GET endpoints live | All tools pass golden tests | Dashboard on real data | Review with fresh eyes against PRD US-2 |
| **H10-18** (**C3**) | `/chat` endpoint; `/insights`; `/inventory/alerts`; `/actions/draft` | Insight rules (6.3), forecast, copilot router + validator, templates, fallback router | Chat UI with calc panel; Restock page with select + "Draft PO"; Khata page with WhatsApp links; Insights feed | Test all 8 demo questions daily; start stretch S1 (Hindi strings, keywords) |
| **C3 (H18)** | **MVP complete.** Full run-through of PRD "Definition of done" 1-4 | | | M4 leads a 20-min bug-bash; log bugs in the board |
| **H18-24** | Hardening: error handling, timeouts, caching; optional deploy | Fix bugs; edge cases (fuzzy SKU, empty periods); stretch S2 report | Polish UI, empty/loading/error states, mobile check, Diwali marker | Pick **max 2** stretch goals; finalise pitch + business case |
| **H24 FREEZE** | tag `v1-demo` | | | Full dress rehearsal #1 |
| **H24-30** | Run demo in offline mode (fallback) as a drill | Bug fixes only | Bug fixes only; screenshots for slides | Rehearsal #2, backup video recording, final README |

**Checkpoints are binary.** If C2 is missed by more than 90 minutes, the team drops the lowest-priority item from "Stretch" and moves a person to the blocker. Decide at the standup, not silently.

## 3. Rituals
- **Standups** (10 min, at H0, H4, H10, H18, H24): what's done, what's blocked, what contract changes I need. Timebox hard.
- **One task board** (GitHub Projects or a shared doc): columns `Todo / Doing / Review / Done`. Every card has an owner and a PRD story ID.
- **Contract changes** (API shape, tool signature, metric definition) go through a PR that edits docs 01/02 first, tagged `contract`, reviewed by the consumer of the change. No silent drift.

## 4. Git workflow (keeps four Antigravity agents from colliding)

- `main` is always demo-able. Protected. Merge by PR with at least one review (30-minute review SLA; self-merge allowed only for `docs/` typos).
- Branch naming: `m1/<topic>`, `m2/<topic>`, `m3/<topic>`, `m4/<topic>`.
- Small PRs (under ~300 lines) merged at least every 2 hours. Rebase on `main` before opening.
- **Never edit another member's folder** without telling them in chat. If you need a change, open an issue or ask. This matters most when agents are generating code.
- Each person works in a **separate branch, and ideally a separate git worktree or clone**, so agents don't overwrite each other's working files.
- Commit message prefix: `feat:`, `fix:`, `docs:`, `test:`, `chore:`.
- Generated files, `node_modules`, `.env`, SQLite DB file are git-ignored. Sample CSVs are committed.

## 5. Definition of done per task
1. Works against the sample data. 2. Has a test (backend) or a screenshot in the PR (frontend). 3. Matches the contract in doc 02. 4. Docs updated if behavior changed. 5. Reviewed and merged to `main`.

## 6. Risk register

| Risk | Likelihood | Mitigation | Owner |
|---|---|---|---|
| LLM gives a wrong or invented number | Medium | Tools-only answers + number validator + template fallback | M2 |
| Wi-Fi or API quota dies on stage | Medium | Fallback router; demo rehearsed in offline mode; recorded backup video | M1, M4 |
| UI and API drift | High | Frozen contract at H2; mock JSON; `contract` PR label | M3, M1 |
| Merge conflicts from parallel agents | High | Folder ownership; per-person branches/worktrees; small PRs | all |
| Scope creep into stretch goals | High | Stretch only after C3; max 2; freeze at H24 | M4 |
| Messy real-world CSVs break ingest in front of judges | Medium | Validation report never crashes; demo uses our file, but test one messy file | M1 |
| Forecast recommends restocking festival items | Medium | `FESTIVAL_OVER` status + test | M2 |
| Judges doubt "AI" depth | Medium | Show calc panel, validator badge, Hinglish, evidence tables in demo | M4 |

## 7. Communication
One group chat. Rules: post blockers immediately; post "done, merged, PR link" for each merge; keep a pinned message with the run command and the current `main` status. Avoid long debates: if a decision takes more than 5 minutes, M4 decides.
