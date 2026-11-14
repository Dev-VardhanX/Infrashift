#!/usr/bin/env python3
"""Independent calculation of the golden numbers (no backend code). Usage: python scripts/check_golden.py [data/sample]
Implements PRD section 4 definitions. Compare backend output against this."""
import sys, math, datetime as dt
import pandas as pd
D = sys.argv[1] if len(sys.argv) > 1 else "data/sample"
S = pd.read_csv(f"{D}/sales.csv", parse_dates=["date"]); P = pd.read_csv(f"{D}/products.csv")
I = pd.read_csv(f"{D}/inventory.csv"); PU = pd.read_csv(f"{D}/purchases.csv", parse_dates=["date"])
C = pd.read_csv(f"{D}/customers.csv"); E = pd.read_csv(f"{D}/expenses.csv", parse_dates=["date"])
AS_OF = S.date.max(); DIWALI = pd.Timestamp("2026-11-08")
S = S.merge(P[["sku", "name", "category", "gst_rate", "cost_price"]], on="sku")
S["rev"] = S.qty * S.unit_price; S["taxable"] = S.rev / (1 + S.gst_rate / 100)
# cost at sale = weighted avg purchase cost in the 60 days before the sale date (fallback: products.cost_price)
PU["val"] = PU.qty * PU.unit_cost
def cost_at(sku, d):
    w = PU[(PU.sku == sku) & (PU.date <= d) & (PU.date > d - pd.Timedelta(days=60))]
    return w.val.sum() / w.qty.sum() if w.qty.sum() else None
keys = S[["sku", "date"]].drop_duplicates()
keys["c"] = [cost_at(s, d) for s, d in zip(keys.sku, keys.date)]
S = S.merge(keys, on=["sku", "date"]); S["c"] = S.c.fillna(S.cost_price)
S["cogs"] = S.qty * S.c; S["profit"] = S.taxable - S.cogs
def win(a, b): return S[(S.date >= a) & (S.date <= b)]
def kp(a, b):
    w = win(a, b); return dict(revenue=round(w.rev.sum()), taxable=round(w.taxable.sum()), gst=round(w.rev.sum() - w.taxable.sum()),
        gross_profit=round(w.profit.sum()), margin_pct=round(100 * w.profit.sum() / w.taxable.sum(), 2),
        invoices=w.invoice_id.nunique(), avg_bill=round(w.rev.sum() / w.invoice_id.nunique(), 1))
l30 = (AS_OF - pd.Timedelta(days=29), AS_OF); p30 = (AS_OF - pd.Timedelta(days=59), AS_OF - pd.Timedelta(days=30))
print("AS_OF", AS_OF.date()); print("LAST30", l30[0].date(), l30[1].date(), kp(*l30)); print("PREV30", p30[0].date(), p30[1].date(), kp(*p30))
print("\nPayment mix last30 %:", (win(*l30).groupby("payment_mode").rev.sum() / win(*l30).rev.sum() * 100).round(1).to_dict())
w = win(*l30)
print("\nTop5 revenue last30:", w.groupby("name").rev.sum().nlargest(5).round().to_dict())
print("Top5 profit  last30:", w.groupby("name").profit.sum().nlargest(5).round().to_dict())
dw = (DIWALI - pd.Timedelta(days=7), DIWALI - pd.Timedelta(days=1)); pw = (dw[0] - pd.Timedelta(days=7), dw[0] - pd.Timedelta(days=1))
print("\nDiwali week", dw[0].date(), dw[1].date(), round(win(*dw).rev.sum()), "vs prior week", round(win(*pw).rev.sum()))
for cat in ["Dry Fruits", "Puja & Decor", "Sweets & Chocolates"]:
    a = win(*dw); b = win(*pw)
    print(f"  {cat}: {round(a[a.category==cat].rev.sum())} vs {round(b[b.category==cat].rev.sum())}")
I = I.merge(P[["sku", "name", "cost_price", "lead_time_days", "category"]], on="sku")
I["val"] = I.current_stock * I.cost_price
print("\nStock value at cost:", round(I.val.sum()))
u30 = w.groupby("sku").qty.sum()
I["u30"] = I.sku.map(u30).fillna(0)
dead = I[(I.current_stock > 0) & (I.u30 <= 0.05 * I.current_stock) & (I.category != "Puja & Decor")]
print("Dead stock:", dead[["sku", "name", "current_stock", "u30"]].values.tolist(), "capital locked", round(dead.val.sum()))
u14 = win(AS_OF - pd.Timedelta(days=13), AS_OF).groupby("sku").qty.sum() / 14
I["d14"] = I.sku.map(u14).fillna(0); I["cover"] = I.current_stock / I.d14.replace(0, float("nan"))
print("Lowest cover (14d-avg demand, simple):\n", I.nsmallest(8, "cover")[["sku", "name", "current_stock", "d14", "cover", "lead_time_days"]].round(1).to_string(index=False))
# margin leak OIL01
for lab, a, b in [("OIL01 before", "2026-08-01", "2026-09-14"), ("OIL01 after", "2026-09-20", "2026-11-13")]:
    x = win(a, b); x = x[x.sku == "OIL01"]; print(lab, "margin %", round(100 * x.profit.sum() / x.taxable.sum(), 2), "avg cost", round(x.cogs.sum() / x.qty.sum(), 2))
# expenses
E["m"] = E.date.dt.strftime("%Y-%m"); print("\nExpenses by month/category (Electricity, Delivery Fuel):")
print(E[E.category.isin(["Electricity", "Delivery Fuel"])].pivot_table(index="m", columns="category", values="amount", aggfunc="sum").to_string())
print("Expenses total by month:", E.groupby("m").amount.sum().to_dict())
# khata
C["days"] = (AS_OF - pd.to_datetime(C.last_payment_date)).dt.days
print("\nKhata outstanding:", int(C.khata_balance.sum()))
od = C[(C.khata_balance > 0) & (C.days > 45)].sort_values("khata_balance", ascending=False)
print("Overdue >45d:", od[["customer_id", "name", "khata_balance", "days", "credit_limit"]].values.tolist(), "TOTAL", int(od.khata_balance.sum()))
print("Over credit limit:", C[(C.credit_limit > 0) & (C.khata_balance > C.credit_limit)][["customer_id", "khata_balance"]].values.tolist())
