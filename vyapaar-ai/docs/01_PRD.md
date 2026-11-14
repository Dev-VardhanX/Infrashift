# 01. Product Requirements (PRD)

## 1. Persona

**Rajesh Sharma, 46, owns a kirana store in Delhi.** About 38 SKUs on the shelf here (real shops carry 1,500+; we model a representative slice). Staff of two. Sells about Rs 13 to 14 lakh a month. 60% of billing is UPI, 30% cash, ~6% card, and he gives credit on khata to regulars. Keeps records in a billing app export, a khata notebook, and WhatsApp orders. Not technical. Phone-first. Hindi-comfortable.

**His real questions:**
- "Diwali ke baad kaunsa maal khatam ho raha hai?" (What is running out?)
- "Kitna paisa market mein phasa hai?" (How much money is stuck with customers?)
- "Mera munafa kyun kam hua?" (Why did my profit drop?)
- "Kaunsa saman dead pada hai?" (What is dead stock?)

## 2. Scope

### MVP (must demo, mapped 1:1 to the judging brief)

| Brief requirement | Our feature | Acceptance test |
|---|---|---|
| 1. Import dataset + key metrics in one dashboard | CSV upload (or "Load sample store"), validation report, dashboard with KPIs | After upload, dashboard shows revenue, gross profit, gross margin %, stock value, khata outstanding, UPI/cash split, top products, trend chart. Values match `06_GOLDEN_NUMBERS.md` |
| 2. Natural-language question grounded in data | Chat box: LLM selects analytics tools; answer shows numbers + "How I calculated this" panel | "Which items will run out in the next 3 days?" returns the same SKUs as the restock alerts page; every number in the answer exists in the tool output |
| 3. Identify pattern/exception with evidence | Insights feed: margin leak, expense anomaly, dead stock, festive lift, overdue khata | Each insight card has: title, severity, rupee impact, evidence table, and the rule that fired. Planted insights (see 06) are all detected |
| 4. One useful action | **Restock alerts + one-tap supplier PO draft** and **khata WhatsApp reminders** | Click "Draft PO" gives grouped-by-supplier order text with quantities. Click "Remind" gives a pre-filled `wa.me` link with the customer's amount and days overdue |
| Commercial intent | Business case slide + spoken close | See doc 05 |

### Stretch (only after MVP is demo-stable at checkpoint C3)

In priority order: (S1) Hindi/Hinglish questions and answers; (S2) weekly digest report (PDF or WhatsApp-ready text); (S3) scenario planner ("what if I raise oil price by Rs 5?"); (S4) voice input via browser Web Speech API; (S5) GST summary page (output tax by slab, taxable value).

### Explicit non-goals

No real UPI/GST API integrations, no auth/multi-tenant, no OCR/invoice extraction, no mobile app. Mention them as roadmap only.

## 3. User stories and acceptance criteria

**US-1 Import.** As an owner I upload my CSVs (or load the sample) and see problems clearly.
- Accepts the 7 files in `data/sample/`; only `sales.csv` and `products.csv` are mandatory.
- Validation report lists: row counts per file, rows rejected with reason (bad date, unknown SKU, negative qty), and columns auto-mapped.
- Re-upload replaces data for that file; never crashes on a malformed file (returns a readable error).

**US-2 Dashboard.** As an owner I see how the shop is doing on one screen.
- KPI tiles: Revenue, Gross profit, Gross margin %, Invoices, Avg bill value, Stock value (at cost), Khata outstanding, each with change vs previous period.
- Date-range selector (7d / 30d / custom) defaulting to last 30 days; "as of" date shown (data's last date, not today).
- Charts: daily revenue line (with Diwali marker), revenue by category, payment-mode split, top 10 products by revenue and by profit.

**US-3 Ask.** As an owner I ask a question in plain language and trust the answer.
- Supports at least these intents: top/bottom products, period comparison, margin by product, stock/cover, restock list, dead stock, khata overdue, expense summary/anomaly, payment mix.
- Answer = short text + small table or chart + collapsible "How I calculated this" (tool name, arguments, row count, as-of).
- If the question is unsupported, say so and suggest 3 supported questions. **Never guess.**

**US-4 Insights.** As an owner I am told what needs attention without asking.
- Feed sorted by rupee impact. Each card: severity (High/Med/Low), one-line headline, evidence table, recommended action, "why" (the rule + threshold).

**US-5 Act.**
- Restock page: table of OUT / CRITICAL / LOW items with days of cover, suggested qty, supplier; select rows, "Draft PO" gives text per supplier plus Copy and WhatsApp share.
- Khata page: overdue customers with amount, days since last payment, over-limit flag; "Send reminder" opens WhatsApp with a polite pre-filled message.
- Seasonal items post-festival (diyas, rangoli) must be shown as "festival over, do not reorder", not as restock alerts.

## 4. Metric definitions (single source of truth, M2 implements, everyone uses)

| Metric | Definition |
|---|---|
| Revenue | sum(qty x unit_price) over sales in period. Prices are MRP-inclusive of GST |
| Taxable value | revenue / (1 + gst_rate/100), per line |
| GST collected | revenue - taxable value |
| COGS | sum(qty x cost) where cost = weighted average `unit_cost` of purchases in the 60 days before the sale date for that SKU; fallback `products.cost_price` |
| Gross profit | taxable value - COGS (GST is not income; do not count it as margin) |
| Gross margin % | gross profit / taxable value |
| Average bill value | revenue / distinct invoices |
| Stock value | current_stock x products.cost_price |
| Daily demand (forecast) | see 02 section 6 |
| Days of cover | current_stock / forecast daily demand |
| Khata outstanding | customers.khata_balance (also reconcilable: khata sales - khata_payments) |
| Overdue khata | balance > 0 and days since last payment > 45 (configurable) |
| Dead stock | stock > 0 and units sold in last 30 days <= 5% of the stock on hand (configurable) and not a festival-seasonal item |
| Margin leak | SKU whose margin at latest purchase cost fell >= 5 percentage points vs margin at the average purchase cost from 60+ days ago (price is capped at MRP, so the action is renegotiate or substitute) |
| Expense anomaly | monthly category total > 1.5 x median of other months (and > Rs 1,000 absolute) |

> **Important:** the margin definition uses *taxable value*, not MRP. A judge who knows GST will check this. It also makes our numbers lower and more honest than a naive "price - cost".

## 5. Definition of done (whole product)

1. Fresh clone, `README` steps, app runs in under 5 minutes on a clean laptop.
2. "Load sample store" produces the dashboard and all 5 planted insights with zero manual steps.
3. All golden numbers in 06 pass `pytest backend/tests/test_golden.py`.
4. Copilot answers the 8 scripted demo questions (doc 05) correctly, online and offline (fallback router).
5. 5-minute demo rehearsed twice end-to-end by M4.
