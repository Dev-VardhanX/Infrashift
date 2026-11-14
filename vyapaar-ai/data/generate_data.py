#!/usr/bin/env python3
"""
Synthetic kirana-store dataset generator (Python stdlib only, deterministic).

Store: "Sharma General Store", Delhi. Period: 15 May 2026 - 13 Nov 2026 (Diwali = 8 Nov 2026).
Usage:  python generate_data.py [outdir]      (default: ./sample)

Outputs: products.csv sales.csv inventory.csv purchases.csv expenses.csv customers.csv khata_payments.csv

PLANTED INSIGHTS (so the demo is reliable - see docs/05_DEMO_AND_BUSINESS_CASE.md):
  1. Restock risk : SUG01 out of stock, GHE01 ~1 day cover, ATT01/DRY01/DRY02/SWT01 low (supplier delays after Diwali demand);
                    PUJ* items look low but are post-festival -> engine must NOT recommend reordering them
  2. Dead stock   : JUC01, SYR01, SYR02 (summer drinks) over-bought on 22 Sep, ~no sales since Sep
  3. Margin leak  : OIL01 (Fortune oil) cost rose Rs128 -> Rs141 on 15 Sep, selling price stuck at Rs150
  4. Expense flag : Electricity Oct = ~Rs9,800 vs ~Rs4,300 normal; delivery fuel Oct spike
  5. Khata overdue: C003, C007 (no payment since 28 Jul), C009, C011, C013 (since 28 Sep), several over credit limit
  6. Festive lift : Dry fruits, sweets, diyas, oil/ghee spike in the ~12 days before Diwali
GST rates are configuration (0/5/18); verify against the current GST schedule before the demo.
"""
import csv
import datetime as dt
import math
import os
import random
import sys
from collections import defaultdict, namedtuple

random.seed(2026)
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample")
os.makedirs(OUT, exist_ok=True)

START, END = dt.date(2026, 5, 15), dt.date(2026, 11, 13)
DIWALI = dt.date(2026, 11, 8)
SCALE = 1.5                       # shop size multiplier
DELAYED = {"OIL01", "SUG01", "GHE01"}   # supplier delays after DELAY_FROM
DELAY_FROM, DELAY_DAYS = dt.date(2026, 11, 7), 4
DEAD = {"JUC01", "SYR01", "SYR02"}      # seasonal items that stop selling in Sep

Prod = namedtuple("Prod", "sku name category mrp cost gst daily supplier lead")
P = [
    # Staples
    Prod("ATT01", "Aashirvaad Atta 5kg", "Staples", 290, 262, 5, 9, "Gupta Traders", 3),
    Prod("RIC01", "India Gate Basmati Rice 5kg", "Staples", 725, 640, 5, 3, "Gupta Traders", 3),
    Prod("DAL01", "Toor Dal 1kg", "Staples", 165, 148, 5, 7, "Gupta Traders", 3),
    Prod("SUG01", "Sugar 1kg", "Staples", 52, 46, 5, 14, "Gupta Traders", 3),
    Prod("SAL01", "Tata Salt 1kg", "Staples", 28, 24, 0, 8, "Gupta Traders", 3),
    # Oil & Ghee
    Prod("OIL01", "Fortune Sunflower Oil 1L", "Oil & Ghee", 150, 128, 5, 9, "Gupta Traders", 2),
    Prod("OIL02", "Saffola Gold Oil 1L", "Oil & Ghee", 195, 172, 5, 4, "Gupta Traders", 2),
    Prod("GHE01", "Amul Ghee 1L", "Oil & Ghee", 640, 585, 5, 3.5, "Jain Distributors", 2),
    # Dairy & Eggs
    Prod("MLK01", "Amul Taza Milk 500ml", "Dairy & Eggs", 29, 27.5, 0, 40, "Delhi Dairy Agency", 1),
    Prod("PNR01", "Amul Paneer 200g", "Dairy & Eggs", 98, 88, 0, 6, "Delhi Dairy Agency", 1),
    Prod("EGG01", "Eggs Tray (30)", "Dairy & Eggs", 210, 190, 0, 2, "Delhi Dairy Agency", 2),
    Prod("BUT01", "Amul Butter 500g", "Dairy & Eggs", 285, 262, 5, 4, "Delhi Dairy Agency", 2),
    # Snacks & Biscuits
    Prod("BIS01", "Parle-G 800g", "Snacks & Biscuits", 85, 77, 5, 8, "Jain Distributors", 2),
    Prod("BIS02", "Good Day Cashew 250g", "Snacks & Biscuits", 50, 44, 5, 7, "Jain Distributors", 2),
    Prod("MAG01", "Maggi Noodles 12-pack", "Snacks & Biscuits", 168, 152, 5, 5, "Jain Distributors", 2),
    Prod("SNK01", "Haldiram Bhujia 400g", "Snacks & Biscuits", 105, 93, 5, 5, "Jain Distributors", 2),
    Prod("SNK02", "Lays Classic 52g", "Snacks & Biscuits", 20, 17.5, 5, 22, "Jain Distributors", 2),
    # Sweets & Chocolates
    Prod("CHO01", "Cadbury Dairy Milk 52g", "Sweets & Chocolates", 50, 43, 5, 12, "Jain Distributors", 2),
    Prod("CHO02", "Cadbury Celebrations 118g", "Sweets & Chocolates", 175, 150, 5, 3, "Jain Distributors", 2),
    Prod("SWT01", "Haldiram Soan Papdi 250g", "Sweets & Chocolates", 120, 102, 5, 2, "Jain Distributors", 2),
    # Dry Fruits
    Prod("DRY01", "Almonds 250g", "Dry Fruits", 245, 205, 5, 3, "Verma Dry Fruit House", 3),
    Prod("DRY02", "Cashew 250g", "Dry Fruits", 295, 250, 5, 2.5, "Verma Dry Fruit House", 3),
    Prod("DRY03", "Raisins 250g", "Dry Fruits", 110, 90, 5, 2, "Verma Dry Fruit House", 3),
    # Personal & Home Care
    Prod("SOP01", "Dettol Soap 3x75g", "Personal & Home Care", 135, 118, 5, 5, "Jain Distributors", 2),
    Prod("SHM01", "Clinic Plus Shampoo 340ml", "Personal & Home Care", 210, 184, 5, 2, "Jain Distributors", 2),
    Prod("TPS01", "Colgate Strong Teeth 200g", "Personal & Home Care", 120, 104, 5, 5, "Jain Distributors", 2),
    Prod("DET01", "Surf Excel Easy Wash 1kg", "Personal & Home Care", 130, 114, 5, 6, "Jain Distributors", 2),
    Prod("HRP01", "Harpic Toilet Cleaner 500ml", "Personal & Home Care", 98, 84, 18, 3, "Jain Distributors", 2),
    # Beverages
    Prod("TEA01", "Tata Tea Gold 500g", "Beverages", 310, 275, 5, 4, "Gupta Traders", 3),
    Prod("COF01", "Nescafe Classic 100g", "Beverages", 340, 300, 18, 2, "Jain Distributors", 3),
    Prod("WAT01", "Bisleri Water 1L", "Beverages", 20, 14, 18, 30, "Jain Distributors", 1),
    Prod("JUC01", "Real Mango Juice 1L", "Beverages", 120, 102, 5, 4, "Jain Distributors", 2),
    Prod("SYR01", "Rooh Afza 750ml", "Beverages", 245, 212, 5, 3, "Jain Distributors", 2),
    Prod("SYR02", "Glucon-D Orange 500g", "Beverages", 160, 140, 18, 3, "Jain Distributors", 2),
    # Puja & Decor
    Prod("PUJ01", "Earthen Diyas (12)", "Puja & Decor", 60, 38, 0, 1.5, "Om Puja Bhandar", 2),
    Prod("PUJ02", "Agarbatti Cycle Pure 100s", "Puja & Decor", 95, 78, 5, 3, "Om Puja Bhandar", 2),
    Prod("PUJ03", "Rangoli Colour 500g", "Puja & Decor", 80, 55, 5, 1, "Om Puja Bhandar", 2),
    Prod("PUJ04", "Tealight Candles 50pc", "Puja & Decor", 140, 100, 5, 1, "Om Puja Bhandar", 2),
]
BY_SKU = {p.sku: p for p in P}


def fest(cat, d):
    k = (DIWALI - d).days
    f = 1.0
    if cat == "Dry Fruits" and 0 <= k <= 12:
        f = 3.5
    elif cat == "Sweets & Chocolates" and 0 <= k <= 10:
        f = 2.5
    elif cat == "Puja & Decor":
        if 0 <= k <= 9:
            f = 6.0
        elif dt.date(2026, 10, 11) <= d <= dt.date(2026, 10, 19):
            f = 2.0
        elif k < 0:
            f = 0.2
    elif cat == "Oil & Ghee" and 0 <= k <= 14:
        f = 1.7
    elif cat == "Staples" and 0 <= k <= 14:
        f = 1.3
    if -5 <= k < 0 and cat != "Puja & Decor":
        f *= 0.7
    return f


def demand(p, d):
    lam = p.daily * SCALE * fest(p.category, d) * (1.2 if d.weekday() >= 5 else 1.0)
    if p.sku in DEAD and d >= dt.date(2026, 9, 1):
        lam *= 0.03
    return lam


def pois(lam):
    if lam <= 0:
        return 0
    if lam > 30:
        return max(0, int(round(random.gauss(lam, math.sqrt(lam)))))
    L, k, pr = math.exp(-lam), 0, 1.0
    while True:
        k += 1
        pr *= random.random()
        if pr <= L:
            return k - 1


def unit_cost(p, d):
    if p.sku == "OIL01":
        base = 141.0 if d >= dt.date(2026, 9, 15) else 128.0
    else:
        base = p.cost
    return round(base * (1 + random.uniform(-0.008, 0.008)) if p.sku != "OIL01" else base, 2)


NAMES = ["Ramesh Kumar", "Sunita Devi", "Anil Gupta", "Pooja Verma", "Mohd. Irfan", "Neha Singh",
         "Vikas Yadav", "Kavita Sharma", "Rajesh Jain", "Meena Kohli", "Sandeep Arora", "Priya Nair",
         "Harish Chand", "Fatima Begum", "Gurpreet Singh", "Anjali Mehta", "Deepak Tyagi", "Rekha Rani",
         "Suresh Babu", "Nisha Khan", "Amit Saxena", "Lata Mishra", "Manoj Tiwari", "Seema Bhatia",
         "Kiran Pal", "Rohit Malhotra", "Shanti Devi", "Ajay Chauhan", "Divya Kapoor", "Bharat Lal"]
CUST = {f"C{i+1:03d}": NAMES[i] for i in range(30)}
KHATA_CUST = [f"C{i:03d}" for i in range(1, 15)]
STOP = {"C003": dt.date(2026, 7, 28), "C007": dt.date(2026, 7, 28),
        "C009": dt.date(2026, 9, 28), "C011": dt.date(2026, 9, 28), "C013": dt.date(2026, 9, 28)}

stock = {p.sku: int(p.daily * SCALE * 14) for p in P}
on_order = defaultdict(list)          # sku -> [(arrive, qty, cost)]
last_rcv = {p.sku: START for p in P}
purchases, sales, kpay = [], [], []
ledger = defaultdict(float)
last_pay = {}
inv_no = 0
HOURS = list(range(8, 22))
HW = [2, 3, 3, 2, 2, 3, 2, 2, 3, 4, 5, 5, 3, 1]

d = START
while d <= END:
    # receive deliveries
    for p in P:
        due = [o for o in on_order[p.sku] if o[0] <= d]
        for arr, qty, cost in due:
            stock[p.sku] += qty
            last_rcv[p.sku] = d
            purchases.append([f"PO-{len(purchases)+1:05d}", d.isoformat(), p.sku, qty, cost, p.supplier])
        on_order[p.sku] = [o for o in on_order[p.sku] if o[0] > d]
    if d == dt.date(2026, 9, 22):          # planted over-buy of summer drinks
        for sku in DEAD:
            stock[sku] += 60
            last_rcv[sku] = d
            purchases.append([f"PO-{len(purchases)+1:05d}", d.isoformat(), sku, 60, unit_cost(BY_SKU[sku], d), BY_SKU[sku].supplier])

    # sell
    sold = {}
    for p in P:
        q = min(pois(demand(p, d)), stock[p.sku])
        stock[p.sku] -= q
        if q:
            sold[p.sku] = q
    n_inv = max(1, int(sum(sold.values()) / 2.6))
    baskets = [defaultdict(int) for _ in range(n_inv)]
    for sku, q in sold.items():
        r = q
        while r > 0:
            c = min(r, random.choice([1, 1, 1, 2, 2, 3]))
            baskets[random.randrange(n_inv)][sku] += c
            r -= c
    for b in baskets:
        if not b:
            continue
        inv_no += 1
        iid = f"INV-2026-{inv_no:06d}"
        t = f"{random.choices(HOURS, HW)[0]:02d}:{random.randint(0, 59):02d}"
        total = sum(BY_SKU[s].mrp * q for s, q in b.items())
        cid, mode = "", None
        if random.random() < 0.10:
            cid = random.choice(list(CUST))
            if cid in KHATA_CUST and random.random() < 0.5:
                mode = "khata"
        if mode is None:
            mode = random.choices(["upi", "cash", "card"], [0.62, 0.32, 0.06])[0]
        if mode == "khata":
            ledger[cid] += total
        for s, q in b.items():
            sales.append([iid, d.isoformat(), t, s, q, BY_SKU[s].mrp, mode, cid])

    # khata payments
    for cid in KHATA_CUST:
        stop = STOP.get(cid, END)
        if d > stop or ledger[cid] <= 0:
            continue
        if d == stop and cid in STOP or (d.day in (12, 28) and random.random() < 0.55):
            amt = min(ledger[cid], max(100, round(ledger[cid] * random.uniform(0.7, 1.0) / 10) * 10))
            ledger[cid] -= amt
            last_pay[cid] = d
            kpay.append([d.isoformat(), cid, amt, random.choice(["upi", "cash"])])

    # reorder
    for p in P:
        pos = stock[p.sku] + sum(o[1] for o in on_order[p.sku])
        if pos <= math.ceil(p.daily * SCALE * (p.lead + 3)):
            lead = p.lead + (DELAY_DAYS if p.sku in DELAYED and d >= DELAY_FROM else 0)
            arrive = d + dt.timedelta(days=lead)
            fm = sum(fest(p.category, arrive + dt.timedelta(days=i)) for i in range(12)) / 12
            qty = max(1, math.ceil(p.daily * SCALE * 12 * fm) - pos)
            on_order[p.sku].append((arrive, qty, unit_cost(p, arrive)))
    d += dt.timedelta(days=1)

# ---------- expenses ----------
expenses = []


def exp(day, cat, amt, mode, note=""):
    if START <= day <= END:
        expenses.append([day.isoformat(), cat, round(amt), mode, note])


for m in range(5, 12):
    exp(dt.date(2026, m, 1), "Rent", 28000, "bank_transfer", "Shop rent")
    exp(dt.date(2026, m, 5), "Staff Salary", 18000, "cash", "2 helpers")
    elec = {5: 3800, 6: 5400, 7: 5600, 8: 5300, 9: 4300, 10: 9800, 11: 4400}[m]
    exp(dt.date(2026, m, 10), "Electricity", elec + random.randint(-150, 150), "upi",
        "Compressor fault - high bill" if m == 10 else "BSES bill")
    fuel = 5100 if m == 10 else 3000 + random.randint(-200, 200)
    exp(dt.date(2026, m, 15), "Delivery Fuel", fuel, "cash", "Home delivery bike")
    exp(dt.date(2026, m, 18), "Phone & Internet", 899, "upi", "Broadband")
x = START
while x <= END:
    if x.weekday() == 0:
        exp(x, "Packaging", 700 + random.randint(-100, 100), "cash", "Carry bags")
    x += dt.timedelta(days=1)
exp(dt.date(2026, 7, 14), "Repairs", 2500, "cash", "Deep freezer repair")
exp(dt.date(2026, 9, 3), "Licence & Fees", 3500, "upi", "FSSAI renewal")
exp(dt.date(2026, 11, 3), "Staff Bonus", 12000, "cash", "Diwali bonus")
expenses.sort()


# ---------- write ----------
def w(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as f:
        cw = csv.writer(f)
        cw.writerow(header)
        cw.writerows(rows)


rl = lambda p: max(5, math.ceil(p.daily * SCALE * (p.lead + 3)))
w("products.csv", "sku name category mrp cost_price gst_rate supplier lead_time_days reorder_level".split(),
  [[p.sku, p.name, p.category, p.mrp, p.cost, p.gst, p.supplier, p.lead, rl(p)] for p in P])
w("sales.csv", "invoice_id date time sku qty unit_price payment_mode customer_id".split(), sales)
w("inventory.csv", "sku current_stock last_restocked".split(),
  [[p.sku, stock[p.sku], last_rcv[p.sku].isoformat()] for p in P])
w("purchases.csv", "purchase_id date sku qty unit_cost supplier".split(), purchases)
w("expenses.csv", "date category amount payment_mode note".split(), expenses)
w("customers.csv", "customer_id name phone khata_balance last_payment_date credit_limit".split(),
  [[c, n, "90000%05d" % (i * 137 % 100000), round(ledger[c]),
    last_pay[c].isoformat() if c in last_pay else "", 5000 if c in KHATA_CUST else 0]
   for i, (c, n) in enumerate(CUST.items())])
w("khata_payments.csv", "date customer_id amount mode".split(), kpay)

# ---------- sanity summary ----------
rev = defaultdict(float)
mix = defaultdict(float)
for r in sales:
    v = r[4] * r[5]
    rev[r[1][:7]] += v
    mix[r[6]] += v
print("rows: sales=%d invoices=%d purchases=%d expenses=%d" % (len(sales), inv_no, len(purchases), len(expenses)))
print("revenue by month:", {k: round(v) for k, v in sorted(rev.items())})
tot = sum(mix.values())
print("payment mix %:", {k: round(100 * v / tot, 1) for k, v in mix.items()})
print("\nDays of cover (last 14d avg demand) - lowest 8:")
recent = defaultdict(int)
for r in sales:
    if r[1] >= (END - dt.timedelta(days=13)).isoformat():
        recent[r[3]] += r[4]
cov = sorted(((stock[s] / max(recent[s] / 14, 0.01), s, stock[s]) for s in BY_SKU), key=lambda t: t[0])
for c, s, st in cov[:8]:
    print("  %-6s %-30s stock=%4d cover=%5.1f d" % (s, BY_SKU[s].name, st, c))
dv = sum(stock[s] * BY_SKU[s].cost for s in DEAD)
print("\nDead-stock value (JUC01,SYR01,SYR02): Rs", round(dv), {s: stock[s] for s in DEAD})
print("Khata overdue:", {c: (round(ledger[c]), last_pay.get(c)) for c in KHATA_CUST if round(ledger[c]) > 0})
tx = 150 / 1.05
print("OIL01 margin on taxable value: at cost 128 = %.1f%%, at cost 141 = %.1f%%" % (100 * (tx - 128) / tx, 100 * (tx - 141) / tx))
print("Electricity:", [(e[0], e[2]) for e in expenses if e[1] == "Electricity"])
