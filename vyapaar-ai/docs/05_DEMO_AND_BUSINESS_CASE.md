# 05. Demo script, pitch and business case

Owner: M4. Everyone reviews. Rehearse twice with a timer.

## 1. The story in one breath
"Rajesh runs a kirana in Delhi. Diwali just ended. He is sitting on Rs 45,000 of dead stock, Rs 31,000 of overdue khata, a cooking oil he now sells at 1.3% margin, and he is out of sugar. He knew none of this. We show him in 30 seconds, and let him act on it in one tap."

## 2. Five-minute demo (target: 4:30, leaving buffer)

| Time | Screen | Say | Proves (brief requirement) |
|---|---|---|---|
| 0:00 | Slide: problem | "Millions of shops run on billing exports, a khata notebook and WhatsApp. They have data but no analyst." (15 s) | context |
| 0:15 | Upload page: click **Load sample store** (or drag the 7 CSVs) | "These are real-shaped Indian records: UPI, cash, khata credit, GST slabs, Diwali." Show the validation report (rows ok / rejected, with reasons) | 1 Import |
| 0:50 | Dashboard | Walk: revenue Rs 14.3 lakh last 30 days, +16.6%; **gross margin 7.8% on taxable value, GST excluded**; UPI 61%; stock Rs 2.65 lakh; khata Rs 35k. Point at the Diwali marker and spike | 1 Dashboard |
| 1:30 | Insights feed | Open the **margin leak** card: "Fortune oil cost went up Rs 13 on 15 September, the price is capped at MRP, margin fell from 10.4% to 1.3%." Show evidence table and "why this fired" | 3 Pattern + evidence |
| 2:10 | Chat: Q2 "Which items will run out in the next 3 days?" | Show answer, table, the green **Verified against your data** badge, open **How I calculated this** (tool, formula, row count) | 2 Grounded NL answer |
| 2:50 | Chat: Q8 "Kitna udhaar baaki hai?" | Answers in Hinglish; numbers identical to the Khata page | NL, regional language |
| 3:10 | Restock page | Sugar OUT, Ghee CRITICAL; note diyas/rangoli marked **festival over, do not reorder**. Select items, **Draft PO**, show per-supplier WhatsApp text | 4 Action |
| 3:50 | Khata page | Seven overdue; two over credit limit. Click **Send reminder**, WhatsApp opens with a polite Hindi message | 4 Action |
| 4:15 | Slide: business case (below) | 30-second close: who pays, how much, how we reach 100 shops, the renewal feature | Commercial intent |

**Rules for the demo:** use the sample store (we know the answers); keep one browser tab; Wi-Fi off drill done beforehand (fallback mode must give identical numbers); never type a question not on the list unless a judge asks, and if so, say "let's try it" and accept an "I can't answer that, here's what I can" response gracefully (that is a feature).

## 3. Anticipated judge questions

| Question | Answer |
|---|---|
| "Isn't this just ChatGPT on a CSV?" | No. The model never calculates. It picks one of 12 tested analytics tools; every number in the answer is checked against the tool output before it is shown, otherwise we fall back to a deterministic template. Show the calc panel. |
| "How do you handle messy data?" | Ingest validates dates, SKUs and payment modes, fuzzy-maps columns, and returns a report of every rejected row with its reason. Never fails silently. |
| "Why is margin only 7.8%?" | We compute margin on taxable value (price excluding GST) against actual purchase cost. Naive MRP-minus-cost overstates it. Kirana net margins are thin; that is why small leaks matter. |
| "Why not raise the oil price?" | Packaged goods have a printed MRP. We recommend renegotiating cost or promoting a substitute instead. |
| "How would the forecast improve?" | Today: transparent recent-demand average with festival adjustment. Next: seasonal models per SKU once a shop has 12+ months, plus supplier lead-time learning. |
| "Does it work with my billing software?" | CSV/Excel export is universal; next steps are Vyapar/Tally/Busy export templates and GST portal data. |
| "Privacy?" | Only aggregates and the customer first name + amount for a reminder reach the LLM; the rest never leaves the machine. Sample data is synthetic. |

## 4. Commercial close (what to say, 30 seconds)

> "Our first customer is the **kirana and general store doing Rs 8 to 25 lakh a month**, then pharmacies and cafes. We charge **Rs 499 a month**, about half a percent of the gross profit of a shop like this one, where a single Diwali review surfaced Rs 45,000 of dead stock and Rs 31,000 of overdue khata. We reach the first hundred shops through the people who already visit them every week: **FMCG distributors and their salesmen, and local GST accountants**, with WhatsApp onboarding. The feature owners will renew for is the **Monday morning WhatsApp digest: what to reorder today, with a one-tap order to your supplier, and who to remind about udhaar.**"

## 5. Business case detail (backup slide / Q&A)

**Who pays (ICP):** Owner-operated kirana / general stores with Rs 8 to 25 lakh monthly sales, already billing digitally (UPI + some billing app) but with no analyst, 2 to 4 staff. Second wave: pharmacies (expiry + margin tracking), cafes (slow-moving stock), wholesale traders (receivables).

**Pricing (hypothesis to validate in pilot):**

| Plan | Price | For |
|---|---|---|
| Starter | Rs 499 / month (first 30 days free) | 1 shop, dashboard, Q&A, restock + khata alerts, WhatsApp digest |
| Plus | Rs 999 / month | Pharmacy / cafe / wholesale: expiry or receivables module, multi-user, weekly PDF for accountant |
| Distributor bundle | Rs 299 / shop / month, billed to distributor | Distributor sponsors 50+ shops |

*Value logic:* a shop like the sample has about Rs 1.06 lakh monthly gross profit. Recovering even Rs 5,000 of stuck khata or avoiding one stock-out day on ghee or sugar covers 10 months of subscription. The pilot's job is to measure this, not assume it.

**First 100 shops (90-day plan):**

| Channel | Mechanism | Target shops |
|---|---|---|
| FMCG distributors / wholesalers (Sadar Bazaar, Khari Baoli, local C&F agents) | Pitch the distributor: shops' restock alerts become **pre-formed orders** (more orders, fewer calls). Salesman demos on his visit; distributor sponsors first 3 months | 5 distributors x 20 = 50 |
| GST accountants / CAs | Accountant already collects monthly sales data; we give them a free dashboard for each client and a weekly PDF; they recommend to 10 clients | 3 CAs x 10 = 30 |
| WhatsApp referral | Owner forwards the weekly digest to a neighbour shop; one-tap "try with your own data" link; kirana associations and market WhatsApp groups | 20 |

**Why they renew:** the Monday WhatsApp digest becomes the owner's ordering routine (restock list + supplier PO + udhaar reminders). Cancelling means going back to guessing.

**Risks and honesty:** data entry quality, ownership of billing data, distributor conflict of interest (they may push their own SKUs). Mitigation: shop owns its data; recommendations show evidence, not distributor-driven.

## 6. Pre-demo checklist (M4 runs it at H24 and again 1 hour before)

- [ ] Fresh clone, follow README, app up in under 5 minutes
- [ ] Load sample store, all golden numbers match (`pytest` + `scripts/check_golden.py`)
- [ ] 8 demo questions pass online AND with Wi-Fi off
- [ ] All 6 planted insights visible; no restock alert for diyas/rangoli/tealights/agarbatti
- [ ] WhatsApp links open on the demo laptop and on a phone
- [ ] Browser zoom, dark mode off, notifications off, one tab
- [ ] Backup: screen-recorded full demo video, and screenshots in slides
- [ ] Laptop charged, charger and hotspot ready, `main` tagged `v1-demo`
- [ ] Everyone knows their 30-second slot and who answers which judge question
