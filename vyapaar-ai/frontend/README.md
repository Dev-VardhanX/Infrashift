# Frontend (M3)

React + Vite + Tailwind + Recharts. Talks to the backend only through `src/api/index.js`.

```
npm install
npm run dev        # http://localhost:5173
npm test           # formatting unit tests (node --test)
npm run build
```

## Mock vs real API
`.env` (copy from `.env.example`):
- `VITE_USE_MOCK=true` reads `src/api/mock/*.json` (shaped like docs/02 section 3). No backend needed.
- `VITE_USE_MOCK=false` calls `/api/*`; Vite proxies it to `http://localhost:8000`.

## Pages
Dashboard, Ask (chat), Insights, Restock, Khata, Data (load sample / upload). Hash routes: `#/dashboard`, `#/chat`, ...

## Contract notes for M1/M2 (not in doc 02 yet, raise as a `contract` PR if you agree)
- `/chat` `blocks[]`: `{type:"table",columns,rows}` and `{type:"chart",kind:"bar",x,y,data}`. `validated:false` renders the "Rule-based answer" badge. Optional `suggestions: string[]` is shown as tappable chips for unsupported questions.
- `/actions/draft` also receives an optional `lang` (`hi` | `en`) for khata reminders.
- `/dashboard` may optionally include `series.top_products_by_profit`; otherwise the UI re-sorts `top_products` by profit.
- `/khata/overdue` customers may include `last_payment_date` (ISO) for display.
- Rows in `evidence.rows` and table blocks are already formatted strings (the UI never computes or reformats business numbers).
