"""backend/app/analytics/_data.py
Data loading abstraction and sales enrichment.
Access all data through get_data(db) and get_enriched_sales(db).
Tests inject fixture dictionaries of DataFrames via db argument.
"""
from pathlib import Path
from typing import Any, Dict, Optional
import os
import pandas as pd

_CACHE: Dict[str, Any] = {}


def _find_sample_dir() -> Path:
    """Locate data/sample directory across diverse working directories."""
    file_path = Path(__file__).resolve()
    candidates = [
        Path(os.environ.get("SAMPLE_DATA_DIR", "")),
        file_path.parents[3] / "data" / "sample",  # repo_root/data/sample
        file_path.parents[2] / "data" / "sample",  # backend/data/sample
        Path.cwd() / "data" / "sample",
        Path.cwd().parent / "data" / "sample",
        Path.cwd() / "Infrashift" / "vyapaar-ai" / "data" / "sample",
    ]
    for c in candidates:
        if c.is_dir() and (c / "sales.csv").exists():
            return c
    raise FileNotFoundError("Could not find data/sample directory with sales.csv")


def get_data(db: Optional[Any] = None) -> Dict[str, pd.DataFrame]:
    """Return dictionary of DataFrames:
    {'sales', 'products', 'inventory', 'purchases', 'customers', 'expenses', 'khata_payments'}.
    If db is provided (e.g. dict from test fixture or DB wrapper), returns it directly.
    """
    if isinstance(db, dict):
        return db

    if "raw_data" in _CACHE:
        return _CACHE["raw_data"]

    sample_dir = _find_sample_dir()
    data = {
        "sales": pd.read_csv(sample_dir / "sales.csv", parse_dates=["date"]),
        "products": pd.read_csv(sample_dir / "products.csv"),
        "inventory": pd.read_csv(sample_dir / "inventory.csv"),
        "purchases": pd.read_csv(sample_dir / "purchases.csv", parse_dates=["date"]),
        "customers": pd.read_csv(sample_dir / "customers.csv"),
        "expenses": pd.read_csv(sample_dir / "expenses.csv", parse_dates=["date"]),
        "khata_payments": pd.read_csv(sample_dir / "khata_payments.csv", parse_dates=["date"]),
    }
    _CACHE["raw_data"] = data
    return data


def get_enriched_sales(db: Optional[Any] = None) -> pd.DataFrame:
    """Enriches sales data according to PRD section 4 rules:
    - taxable = rev / (1 + gst_rate / 100)
    - gst = rev - taxable
    - COGS = weighted-average purchase unit_cost over the 60 days before the sale date,
      fallback products.cost_price
    - profit = taxable - cogs
    - gross_margin_pct = profit / taxable * 100
    """
    data = get_data(db)
    sales = data["sales"].copy()
    products = data["products"]
    purchases = data["purchases"].copy()

    # If db is None, we can cache the enriched result for speed
    if db is None and "enriched_sales" in _CACHE:
        return _CACHE["enriched_sales"]

    # Merge product metadata
    cols_to_merge = ["sku", "name", "category", "gst_rate", "cost_price"]
    available_cols = [c for c in cols_to_merge if c in products.columns]
    sales = sales.merge(products[available_cols], on="sku", how="left")

    sales["rev"] = sales["qty"] * sales["unit_price"]
    sales["taxable"] = sales["rev"] / (1 + sales["gst_rate"] / 100)
    sales["gst"] = sales["rev"] - sales["taxable"]

    # Compute purchase weighted-average cost within 60 days prior to sale date
    if not purchases.empty:
        purchases["val"] = purchases["qty"] * purchases["unit_cost"]
        # Group purchases by sku for fast lookup
        pu_by_sku = {}
        for sku, grp in purchases.groupby("sku"):
            pu_by_sku[sku] = grp[["date", "val", "qty"]].copy()

        def compute_cost(sku, d):
            pu = pu_by_sku.get(sku)
            if pu is None or pu.empty:
                return None
            w = pu[(pu["date"] <= d) & (pu["date"] > d - pd.Timedelta(days=60))]
            q_sum = w["qty"].sum()
            return w["val"].sum() / q_sum if q_sum > 0 else None

        keys = sales[["sku", "date"]].drop_duplicates()
        keys["c"] = [compute_cost(s, d) for s, d in zip(keys["sku"], keys["date"])]
        sales = sales.merge(keys, on=["sku", "date"], how="left")
        sales["unit_cost"] = sales["c"].fillna(sales["cost_price"])
        sales = sales.drop(columns=["c"])
    else:
        sales["unit_cost"] = sales["cost_price"]

    sales["cogs"] = sales["qty"] * sales["unit_cost"]
    sales["profit"] = sales["taxable"] - sales["cogs"]

    if db is None:
        _CACHE["enriched_sales"] = sales

    return sales
