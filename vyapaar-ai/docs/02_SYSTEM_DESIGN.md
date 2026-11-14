# 02. System Design

## 1. Architecture

```
 CSV files / "Load sample"
        |
        v
 [ Ingest ]  validate, normalise, auto-map columns  -->  [ SQLite store ]  (tables = the 7 CSVs, cleaned)
                                                               |
                         +-------------------------------------+------------------+
                         v                                     v                  v
                 [ Analytics tools ]                  [ Insight engine ]    [ Action generators ]
                 pure pandas functions                rules -> Insight[]    PO draft, WhatsApp text
                 (the ONLY source of numbers)         (uses analytics tools)
                         ^                                     |                  |
                         |                                     v                  v
                 [ Copilot ]  user question -> LLM picks tool(s) -> results -> answer template -> number validator
                         ^
                         |
                 FastAPI  /api/*   <------>   React dashboard + chat + alerts + khata pages
```

**Principles**
1. Analytics tools are deterministic, unit-tested, and return `{data, meta}`. No LLM inside them.
2. The insight engine is rule-based. The LLM may *rephrase* an insight but never creates one.
3. The copilot is a router and explainer, not a calculator.
4. Everything is explainable: each result carries `meta.method` (human-readable), `meta.row_count`, `meta.as_of`.
5. "Today" is `max(sales.date)` (as-of date), so the demo is stable even if the clock changes. Expose it as `AS_OF`.

## 2. Data model (SQLite; column names = CSV headers)

| Table | Columns | Notes |
|---|---|---|
| products | sku PK, name, category, mrp, cost_price, gst_rate, supplier, lead_time_days, reorder_level | gst_rate in {0,5,12,18} (config) |
| sales | invoice_id, date, time, sku FK, qty, unit_price, payment_mode, customer_id | one row per invoice line; payment_mode in {upi,cash,card,khata}; customer_id blank for walk-ins |
| inventory | sku PK, current_stock, last_restocked | snapshot at as-of date |
| purchases | purchase_id, date, sku, qty, unit_cost, supplier | receipts from suppliers; used for true cost and cost-change detection |
| expenses | date, category, amount, payment_mode, note | |
| customers | customer_id PK, name, phone, khata_balance, last_payment_date, credit_limit | phones are synthetic |
| khata_payments | date, customer_id, amount, mode | |

Derived view `sales_enriched`: sales + product fields + `line_revenue`, `taxable`, `gst`, `unit_cost_at_sale`, `line_cogs`, `line_profit`, `week`, `month`, `is_festive_window`.

**Ingest rules (M1):**
- Parse dates leniently (`YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YY`); reject unparsable rows with reason.
- Normalise payment_mode synonyms: `UPI/GPay/PhonePe/Paytm -> upi`, `Cash -> cash`, `Credit/Udhaar/Khata -> khata`, `Card/POS -> card`.
- Reject rows with unknown SKU, qty <= 0, price < 0. Never drop silently: return counts per reason.
- Auto-map columns by fuzzy header match (`Item Code -> sku`, `Qty -> qty`, `Amount`...). Show the mapping for confirmation. Only `sales` + `products` are mandatory.

## 3. API contract (freeze by H2; frontend mocks against it)

All responses JSON. Base `/api`. Errors: `{ "error": { "code": "...", "message": "human readable" } }`.

| Method + path | Purpose | Response (abridged) |
|---|---|---|
| `POST /load-sample` | Load bundled sample data | `{ "loaded": {"sales": 44303, ...}, "as_of": "2026-11-13" }` |
| `POST /upload` (multipart, many files) | Import user CSVs | `{ "files": [{"name","rows_ok","rows_rejected","reasons":{...},"mapping":{...}}], "as_of" }` |
| `GET /dashboard?from=&to=` | KPIs + charts data | see 3.1 |
| `GET /inventory/alerts` | Restock list | `{ "items": [Alert...], "as_of" }` |
| `GET /insights` | Insight feed | `{ "insights": [Insight...] }` |
| `GET /khata/overdue?days=45` | Overdue customers | `{ "customers": [{id,name,phone,balance,days_since_payment,over_limit}] }` |
| `POST /chat` `{message, lang?}` | Copilot | `{ "answer", "blocks":[table/chart], "calc":[{tool,args,row_count,method}], "validated": true }` |
| `POST /actions/draft` `{type, ids[]}` | `type`: `purchase_order` or `khata_reminder` | `{ "drafts":[{"to","text","wa_link"}] }` |
| `GET /report/weekly` (stretch) | Digest text | `{ "markdown": "..." }` |

### 3.1 `/dashboard` shape
```json
{
  "as_of": "2026-11-13",
  "period": {"from": "2026-10-15", "to": "2026-11-13"},
  "kpis": {
    "revenue": {"value": 1432103, "prev": 1228253, "delta_pct": 16.6},
    "gross_profit": {"value": 0, "prev": 0, "delta_pct": 0},
    "gross_margin_pct": {"value": 0, "prev": 0, "delta_pp": 0},
    "invoices": {"value": 0, "prev": 0},
    "avg_bill": {"value": 0, "prev": 0},
    "stock_value": {"value": 265385},
    "khata_outstanding": {"value": 35248}
  },
  "series": {
    "daily_revenue": [{"date": "2026-10-15", "revenue": 0}],
    "by_category": [{"category": "Staples", "revenue": 0, "profit": 0}],
    "payment_mix": [{"mode": "upi", "revenue": 0, "share_pct": 0}],
    "top_products": [{"sku": "ATT01", "name": "", "revenue": 0, "profit": 0, "units": 0}]
  },
  "markers": [{"date": "2026-11-08", "label": "Diwali"}]
}
```
(Revenue and stock/khata values above are real golden values; zeros are to be filled by the implementation.)

### 3.2 Insight object (the contract between backend and UI)
```json
{
  "id": "margin_leak:OIL01",
  "type": "margin_leak | expense_anomaly | dead_stock | restock | khata_overdue | festive_lift",
  "severity": "high | medium | low",
  "title": "Fortune Sunflower Oil now earns only 1.3% margin (was 10.4%)",
  "impact_inr": 0,
  "evidence": { "columns": ["Metric","Before 15 Sep","Now"], "rows": [["Cost per unit","128.00","141.00"],["Margin on taxable value","10.4%","1.3%"]] },
  "why": "Latest purchase cost rose 10% on 15 Sep; price is capped at MRP Rs150 (rule: margin at latest cost dropped >= 5pp vs margin at cost 60+ days ago)",
  "action": { "label": "Review price", "kind": "none | draft_po | whatsapp_reminder", "payload": {} },
  "as_of": "2026-11-13"
}
```

### 3.3 Restock Alert object
```json
{ "sku":"GHE01","name":"Amul Ghee 1L","supplier":"Jain Distributors","stock":7,
  "daily_demand":6.5,"days_of_cover":1.1,"lead_time_days":2,
  "status":"CRITICAL","suggested_qty":0,"seasonal_note":null,"evidence":"Sold 91 units in last 14 days" }
```
`status` in `OUT | CRITICAL | LOW | OK | FESTIVAL_OVER`.

## 4. Analytics tool registry (M2 owns; each has a unit test)

Signature convention: `def tool(db, **args) -> {"data": <list|dict>, "meta": {"method": str, "row_count": int, "as_of": str}}`

| Tool | Args | Returns |
|---|---|---|
| `sales_summary` | `from, to, group_by in {day,week,month,category,sku,payment_mode}` | revenue, taxable, gst, profit, units, invoices per group |
| `top_products` | `metric in {revenue,profit,units,margin}, n, from, to, order in {top,bottom}` | ranked SKUs |
| `compare_periods` | `metric, a_from, a_to, b_from, b_to, group_by?` | values, delta, delta_pct, biggest contributors |
| `margin_by_product` | `from, to, n` | margin % per SKU with cost basis |
| `stock_status` | `sku?` | stock, daily demand, cover, status |
| `restock_plan` | `horizon_days` | suggested qty per SKU grouped by supplier |
| `dead_stock` | `days, max_sell_through` | SKUs, units, capital locked (Rs) |
| `khata_overdue` | `min_days` | customers, balance, days overdue, over-limit |
| `expense_summary` | `from, to, flag_anomalies` | totals per category, anomaly flags with baseline |
| `payment_mix` | `from, to` | share by mode |
| `gst_summary` (stretch) | `from, to` | taxable + GST per slab |
| `festive_lift` | `category, event_date, window_days` | revenue/units before vs during window |

Date handling: tools accept ISO dates or the tokens `last_7d`, `last_30d`, `prev_30d`, `this_month`, `last_month`, `diwali_week` (resolved against `AS_OF`). Put the resolver in one place (`analytics/periods.py`).

## 5. Copilot design (M2 builds; M1 owns the LLM adapter)

**Flow**
1. User message (+ optional `lang`).
2. **LLM call with tool schemas** (Gemini function calling). System prompt: *"You are a business analyst for an Indian kirana. You may only answer by calling tools. Never state a number that did not come from a tool. If no tool fits, say so."*
3. Execute the chosen tool(s) (max 3 calls per question), collect `{data, meta}`.
4. **Compose answer**:
   - Preferred: second LLM call given only the tool results, asked for a 2-3 sentence summary in the user's language.
   - Fallback: deterministic Python template per tool (always available).
5. **Number validator** (`copilot/validate.py`): extract all numbers from the answer (strip commas, Rs, %, lakh/crore conversions); every number must appear in the tool results within rounding (+-0.5%) or be a date/ordinal. If validation fails, discard the LLM text and use the template. Set `validated: true/false` in response and show a small green "Verified against your data" badge.
6. **Fallback router** (no network or LLM error): keyword/regex intent map (English + Hinglish keywords, e.g. `khatam|stock|kam|restock`, `udhaar|khata|baki`, `margin|munafa|profit`, `dead|slow|nahi bik`). Routes to the same tools. Demo must pass the 8 scripted questions in this mode too.

**Guardrails:** max 3 tool calls; tool args validated by Pydantic; unknown SKU names resolved by fuzzy match (`rapidfuzz`) with the match shown ("Showing: Fortune Sunflower Oil 1L"); LLM output never executed as code or SQL (no text-to-SQL, deliberately).

**Hindi/Hinglish (stretch S1):** same flow; the LLM answers in the question's language; numbers stay in Western digits for the validator; the fallback router carries a Hinglish keyword list.

## 6. Insight engine and forecasting (M2)

### 6.1 Demand forecast (explainable, no ML needed)
```
recent = mean daily units over last 14 days (zero-filled)
base   = mean daily units over a 60-day window ending 21 days before AS_OF, excluding the festival window
if category is festival-seasonal AND AS_OF is after the event:   daily = base * 0.5   # post-festival decay, flagged
else:                                                              daily = 0.6*recent + 0.4*mean(last 28 days)
```
Show the formula in "How I calculated this". (We can always swap in a better model later; the interface stays `daily_demand(sku)`.)

### 6.2 Restock status
```
cover = stock / daily
safety = 2 days
OUT        stock == 0 and daily > 0.5
CRITICAL   cover < lead_time
LOW        cover < lead_time + safety
FESTIVAL_OVER  seasonal category and after event  -> never alert, show note
suggested_qty = max(0, ceil(daily * (lead_time + safety + 7)) - stock)
```
Seasonal categories (config): `Puja & Decor`. Dry fruits and sweets are *not* excluded: they still sell, just at a lower rate.

### 6.3 Insight rules (each returns Insight[])
| Rule | Trigger | Impact (Rs) | Evidence |
|---|---|---|---|
| restock | status in OUT/CRITICAL/LOW | daily_demand x unit margin x days at risk (lost profit) | cover days, sold last 14d |
| dead_stock | see PRD metric | stock x cost_price (capital locked) | units sold last 30d vs stock |
| margin_leak | margin at **latest purchase cost** is >= 5pp below margin at the average purchase cost from 60+ days ago | (old margin - new margin) x taxable sales last 30d | purchase cost before/after, price. **Action: price cannot exceed printed MRP, so recommend negotiating cost or promoting a higher-margin substitute (e.g. OIL02), never "raise price"** |
| expense_anomaly | category month > 1.5 x median of other months | month total - median | monthly table + note column |
| khata_overdue | days since payment > 45 | balance | last payment date, over-limit flag |
| festive_lift | category revenue in festive window >= 2x prior equal window | n/a (opportunity) | before/after table; "plan earlier next year" |
| payment_mix (info) | n/a | n/a | UPI vs cash vs khata share |

Sort by `impact_inr` desc, then severity. Cap the feed at ~12 items; always include at least one of each planted type.

### 6.4 Actions (M3 UI, M1/M2 text generation, plain string templates, no LLM needed)
- **Purchase order draft**: grouped by supplier.
  ```
  Namaste Gupta Traders ji, order for Sharma General Store:
  - Sugar 1kg x 120
  - Aashirvaad Atta 5kg x 40
  Please deliver by tomorrow. Dhanyavaad.
  ```
- **Khata reminder** (polite, not threatening), Hindi default with English toggle:
  `Namaste Ramesh ji, Sharma General Store se yaad dilana tha: Rs 9,685 baaki hai (aakhri payment 28 Jul). Jab suvidha ho UPI kar dijiye. Dhanyavaad.`
  Link: `https://wa.me/91<phone>?text=<urlencoded>`.

## 7. Security, privacy, reliability (keep it short)
- No secrets in repo; `.env` with `GEMINI_API_KEY`. `.env.example` committed.
- Sample data is synthetic (phones are fake). Do not paste real customer data into the LLM; only tool outputs (aggregates or customer first name + amount for reminders) go in prompts.
- If the LLM call fails or times out (> 6 s), fall back automatically; the UI shows nothing different except the badge reads "Rule-based answer".
- Cache dashboard queries in memory keyed by `(from,to,data_version)`.

## 8. Test strategy
- `tests/test_golden.py`: asserts the numbers in 06 within +-0.5%.
- `tests/test_tools_*.py`: one test per tool with a tiny hand-made fixture (3 SKUs, 10 invoices) where you can compute the answer by hand.
- `tests/test_copilot.py`: 8 demo questions, both LLM-mocked and fallback modes; validator rejects a fabricated number.
- Frontend: smoke test by loading each page with mocked API; manual checklist before demo.
