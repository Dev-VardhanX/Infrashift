# Vyapaar AI: AI Operations Copilot for Small Indian Businesses

> Working name. Rename freely. Everything below is the single source of truth for the 4-person team.

**One-liner:** Upload your sales, stock and khata records. Ask in Hindi or English. Get a dashboard, grounded answers and a to-do list: *what to reorder, what is stuck, who owes you, where margin is leaking.*

**Chosen setting:** Kirana / general store in Delhi (Sharma General Store), festive season (Diwali 8 Nov 2026).
Why: most relatable to judges, richest data (UPI + cash + khata credit, GST slabs, festive spikes), and every MVP requirement maps to a real owner pain.

## Read in this order

| # | Doc | Who must read |
|---|-----|---------------|
| 01 | [PRD](docs/01_PRD.md): scope, user stories, acceptance criteria | Everyone (15 min) |
| 02 | [System design](docs/02_SYSTEM_DESIGN.md): architecture, data model, API contract, analytics tools | Everyone, esp. M1/M2/M3 |
| 03 | [Team plan](docs/03_TEAM_PLAN.md): roles, ownership, timeline, git rules, checkpoints | Everyone |
| 04 | [Antigravity guide](docs/04_ANTIGRAVITY_GUIDE.md): how we use the IDE agents + copy-paste prompts per member | Everyone |
| 05 | [Demo and business case](docs/05_DEMO_AND_BUSINESS_CASE.md): 5-min script, pitch, pricing, GTM | M4 owns, all review |
| 06 | [Golden numbers](docs/06_GOLDEN_NUMBERS.md): the numbers the app MUST reproduce | M2 (tests), M4 (demo) |
| - | [AGENTS.md](AGENTS.md): rules the Antigravity agents read automatically | Copy to repo root |
| - | [data/generate_data.py](data/generate_data.py) + [data/sample/](data/sample/): realistic dataset with planted insights | Everyone |

## Repo layout (create this on day 0)

```
vyapaar-ai/
  AGENTS.md                # agent rules (from this pack)
  docs/                    # these docs
  data/
    generate_data.py
    sample/*.csv           # 7 CSVs, ~44k sales lines, 15 May - 13 Nov 2026
  backend/                 # FastAPI + pandas + SQLite   (M1, M2)
    app/{main.py,db.py,ingest/,analytics/,insights/,copilot/,actions/}
    tests/
  frontend/                # React + Vite + Tailwind + Recharts   (M3)
    src/{pages,components,api}
  .env.example
```

## Tech stack (decided, do not relitigate)

| Layer | Choice | Why |
|---|---|---|
| Backend | Python 3.11, FastAPI, pandas, SQLite | fastest to build, trivial to run on any laptop |
| Frontend | React + Vite + Tailwind + Recharts | quick charts, easy to demo on a phone-sized screen |
| LLM | Gemini API (function calling), with a rule-based fallback router | free tier, works inside Antigravity; fallback means the demo never dies on Wi-Fi |
| Hosting | Local for demo; optional Render/Railway for a live link | no infra risk |

## The one design rule that wins the hackathon

> **The LLM never computes or invents a number.** It picks a *tool* (a tested pandas function), the tool returns numbers, and a validator checks that every number in the final answer exists in the tool output.

The problem statement says *"A chatbot alone, without validated calculations or functional business logic, is insufficient."* This rule is our answer. See 02_SYSTEM_DESIGN section 5.

## Assumptions to confirm in the first 10 minutes

1. Hackathon length is about 24 to 30 hours. The plan in 03 is in hour-blocks (H0 = kickoff); stretch or squeeze as needed.
2. Everyone has Antigravity installed and a Gemini API key from Google AI Studio.
3. Diwali 2026 date (8 Nov) and GST slab rates in `data/sample/products.csv` are config values; do a 2-minute sanity check against the current GST schedule before the demo.
