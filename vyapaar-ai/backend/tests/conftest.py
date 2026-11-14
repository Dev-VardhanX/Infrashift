"""backend/tests/conftest.py
Provides tiny hand-computable test fixtures for unit tests.
3 core SKUs + 1 dead stock SKU + 1 seasonal SKU, 10 invoices, 2 purchases, 2 customers, expenses.
"""
import sys
from pathlib import Path
import pytest
import pandas as pd

# Ensure backend root is on sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))


@pytest.fixture
def hand_fixture_data():
    """Tiny hand-computable dataset:
    - Products: 3 core SKUs (0%, 5%, 18% GST), 1 dead stock SKU (Cold Drink), 1 seasonal SKU (Diya)
    - Purchases: 2 purchases for SKU02 (weighted unit cost 160.0)
    - Customers: C01 (43 days, not overdue), C02 (104 days overdue, over limit)
    - Invoices: 10 invoices (6 in last_30d, 4 in prev_30d)
    - Expenses: Electricity with October anomaly (>1.5x median of other months)
    """
    products = pd.DataFrame([
        {
            "sku": "SKU01",
            "name": "Wheat Flour",
            "category": "Staples",
            "mrp": 100.0,
            "cost_price": 80.0,
            "gst_rate": 0.0,
            "supplier": "Gupta Traders",
            "lead_time_days": 2,
            "reorder_level": 20,
        },
        {
            "sku": "SKU02",
            "name": "Mustard Oil",
            "category": "Oil & Ghee",
            "mrp": 210.0,
            "cost_price": 160.0,
            "gst_rate": 5.0,  # taxable = 200.0, gst = 10.0
            "supplier": "Oil Mills",
            "lead_time_days": 3,
            "reorder_level": 10,
        },
        {
            "sku": "SKU03",
            "name": "Chocolate Box",
            "category": "Sweets & Chocolates",
            "mrp": 118.0,
            "cost_price": 70.0,
            "gst_rate": 18.0,  # taxable = 100.0, gst = 18.0
            "supplier": "Sweet Co",
            "lead_time_days": 2,
            "reorder_level": 5,
        },
        {
            "sku": "SKU04",
            "name": "Old Cold Drink",
            "category": "Beverages",
            "mrp": 50.0,
            "cost_price": 30.0,
            "gst_rate": 0.0,
            "supplier": "Drink Dist",
            "lead_time_days": 2,
            "reorder_level": 10,
        },
        {
            "sku": "PUJ01",
            "name": "Earthen Diyas",
            "category": "Puja & Decor",
            "mrp": 20.0,
            "cost_price": 10.0,
            "gst_rate": 0.0,
            "supplier": "Om Puja",
            "lead_time_days": 2,
            "reorder_level": 10,
        },
    ])

    # 2 purchases for SKU02:
    # 10 @ 150 = 1500, 10 @ 170 = 1700 -> (1500 + 1700) / 20 = 160.0 weighted unit cost
    purchases = pd.DataFrame([
        {
            "purchase_id": "P01",
            "date": pd.Timestamp("2026-10-20"),
            "sku": "SKU02",
            "qty": 10,
            "unit_cost": 150.0,
            "supplier": "Oil Mills",
        },
        {
            "purchase_id": "P02",
            "date": pd.Timestamp("2026-10-25"),
            "sku": "SKU02",
            "qty": 10,
            "unit_cost": 170.0,
            "supplier": "Oil Mills",
        },
    ])

    # Customers: C01 (not overdue, 43d), C02 (overdue 104d, over limit 6000 > 5000)
    customers = pd.DataFrame([
        {
            "customer_id": "C01",
            "name": "Ramesh Kumar",
            "phone": "9876543210",
            "khata_balance": 420.0,
            "last_payment_date": "2026-10-01",  # 43 days before 2026-11-13
            "credit_limit": 5000.0,
        },
        {
            "customer_id": "C02",
            "name": "Suresh Gupta",
            "phone": "9876543211",
            "khata_balance": 6000.0,
            "last_payment_date": "2026-08-01",  # 104 days before 2026-11-13
            "credit_limit": 5000.0,
        },
    ])

    # Inventory
    inventory = pd.DataFrame([
        {"sku": "SKU01", "current_stock": 50, "last_restocked": "2026-11-01"},
        {"sku": "SKU02", "current_stock": 1, "last_restocked": "2026-10-25"},
        {"sku": "SKU03", "current_stock": 0, "last_restocked": "2026-10-15"},
        {"sku": "SKU04", "current_stock": 100, "last_restocked": "2026-09-01"},  # 0 sold, dead stock: 100 * 30 = 3000
        {"sku": "PUJ01", "current_stock": 25, "last_restocked": "2026-10-15"},   # Puja & Decor, FESTIVAL_OVER
    ])

    # 10 core invoices (dates spread between 2026-09-20 and 2026-11-13; AS_OF is 2026-11-13)
    sales = pd.DataFrame([
        # last_30d invoices
        {"invoice_id": "INV01", "date": pd.Timestamp("2026-11-13"), "time": "10:00", "sku": "SKU01", "qty": 2, "unit_price": 100.0, "payment_mode": "upi", "customer_id": ""},
        {"invoice_id": "INV02", "date": pd.Timestamp("2026-11-08"), "time": "11:00", "sku": "SKU02", "qty": 1, "unit_price": 210.0, "payment_mode": "cash", "customer_id": ""},
        {"invoice_id": "INV03", "date": pd.Timestamp("2026-11-06"), "time": "12:00", "sku": "SKU03", "qty": 2, "unit_price": 118.0, "payment_mode": "upi", "customer_id": ""},
        {"invoice_id": "INV04", "date": pd.Timestamp("2026-11-04"), "time": "14:00", "sku": "SKU01", "qty": 3, "unit_price": 100.0, "payment_mode": "card", "customer_id": ""},
        {"invoice_id": "INV05", "date": pd.Timestamp("2026-11-02"), "time": "16:00", "sku": "SKU02", "qty": 2, "unit_price": 210.0, "payment_mode": "khata", "customer_id": "C01"},
        {"invoice_id": "INV06", "date": pd.Timestamp("2026-10-28"), "time": "18:00", "sku": "SKU03", "qty": 1, "unit_price": 118.0, "payment_mode": "cash", "customer_id": ""},
        # prev_30d invoices
        {"invoice_id": "INV07", "date": pd.Timestamp("2026-10-10"), "time": "09:00", "sku": "SKU01", "qty": 1, "unit_price": 100.0, "payment_mode": "upi", "customer_id": ""},
        {"invoice_id": "INV08", "date": pd.Timestamp("2026-10-05"), "time": "10:30", "sku": "SKU02", "qty": 1, "unit_price": 210.0, "payment_mode": "cash", "customer_id": ""},
        {"invoice_id": "INV09", "date": pd.Timestamp("2026-09-25"), "time": "12:00", "sku": "SKU03", "qty": 1, "unit_price": 118.0, "payment_mode": "upi", "customer_id": ""},
        {"invoice_id": "INV10", "date": pd.Timestamp("2026-09-20"), "time": "17:00", "sku": "SKU01", "qty": 2, "unit_price": 100.0, "payment_mode": "card", "customer_id": ""},
    ])

    # Expenses with October Electricity spike (3000 vs median 1000 of other months)
    expenses = pd.DataFrame([
        {"date": pd.Timestamp("2026-08-10"), "category": "Electricity", "amount": 1000.0, "payment_mode": "upi", "note": "Normal bill"},
        {"date": pd.Timestamp("2026-09-10"), "category": "Electricity", "amount": 1000.0, "payment_mode": "upi", "note": "Normal bill"},
        {"date": pd.Timestamp("2026-10-10"), "category": "Electricity", "amount": 3000.0, "payment_mode": "upi", "note": "Compressor fault"},
        {"date": pd.Timestamp("2026-11-10"), "category": "Electricity", "amount": 1000.0, "payment_mode": "upi", "note": "Normal bill"},
    ])

    khata_payments = pd.DataFrame(columns=["date", "customer_id", "amount", "mode"])

    return {
        "products": products,
        "purchases": purchases,
        "sales": sales,
        "customers": customers,
        "inventory": inventory,
        "expenses": expenses,
        "khata_payments": khata_payments,
    }
