"""M1: Derived sales_enriched view / dataframe builder.

Doc 02 section 2 & PRD 01 section 4:
- Line revenue = qty * unit_price (MRP-inclusive)
- Taxable value = line_revenue / (1 + gst_rate/100)
- GST collected = line_revenue - taxable
- Unit cost at sale = quantity-weighted average unit_cost of that SKU's
  purchases in the 60 days before the sale date, falling back to products.cost_price
- Line COGS = qty * unit_cost_at_sale
- Line profit = taxable - line_cogs
- Time dimensions: week, month, is_festive_window (vectorised in pandas under 2s).
"""
import sqlite3
import pandas as pd
from app.config import DIWALI_DATE


def build_sales_enriched(conn: sqlite3.Connection) -> pd.DataFrame:
    """Build the sales_enriched dataframe using fully vectorized pandas operations."""
    sales_count = conn.execute("SELECT COUNT(*) AS c FROM sales").fetchone()[0]
    products_count = conn.execute("SELECT COUNT(*) AS c FROM products").fetchone()[0]
    if sales_count == 0 or products_count == 0:
        return pd.DataFrame()

    sales_df = pd.read_sql_query("SELECT * FROM sales", conn)
    products_df = pd.read_sql_query(
        "SELECT sku, name, category, mrp, cost_price, gst_rate, supplier, lead_time_days, reorder_level FROM products",
        conn,
    )
    purchases_df = pd.read_sql_query("SELECT * FROM purchases", conn)

    sales_df["date_dt"] = pd.to_datetime(sales_df["date"])

    if not purchases_df.empty:
        purchases_df["date_dt"] = pd.to_datetime(purchases_df["date"])
        purchases_df["val"] = purchases_df["qty"] * purchases_df["unit_cost"]

        min_date = sales_df["date_dt"].min() - pd.Timedelta(days=60)
        max_date = sales_df["date_dt"].max()
        all_dates = pd.date_range(min_date, max_date, freq="D")

        sku_cost_dfs = []
        for sku in products_df["sku"]:
            pu_sku = purchases_df[purchases_df["sku"] == sku]
            if pu_sku.empty:
                continue
            daily_pu = pu_sku.groupby("date_dt")[["qty", "val"]].sum().reindex(all_dates, fill_value=0.0)
            # 60-day rolling sum: includes sale date d and goes back 59 days (60 calendar days window)
            roll = daily_pu.rolling(60, min_periods=1).sum()
            roll_cost = roll["val"] / roll["qty"]
            sku_cost_dfs.append(pd.DataFrame({
                "sku": sku,
                "date_dt": all_dates,
                "unit_cost_at_sale": roll_cost,
            }))

        if sku_cost_dfs:
            costs_df = pd.concat(sku_cost_dfs, ignore_index=True)
            costs_df = costs_df.dropna(subset=["unit_cost_at_sale"])
            enriched = sales_df.merge(costs_df, on=["sku", "date_dt"], how="left")
        else:
            enriched = sales_df.copy()
            enriched["unit_cost_at_sale"] = None
    else:
        enriched = sales_df.copy()
        enriched["unit_cost_at_sale"] = None

    enriched = enriched.merge(products_df, on="sku", how="left")
    enriched["unit_cost_at_sale"] = enriched["unit_cost_at_sale"].fillna(enriched["cost_price"])

    # Vectorized financial metrics
    enriched["line_revenue"] = enriched["qty"] * enriched["unit_price"]
    enriched["taxable"] = enriched["line_revenue"] / (1.0 + enriched["gst_rate"] / 100.0)
    enriched["gst"] = enriched["line_revenue"] - enriched["taxable"]
    enriched["line_cogs"] = enriched["qty"] * enriched["unit_cost_at_sale"]
    enriched["line_profit"] = enriched["taxable"] - enriched["line_cogs"]

    # Vectorized date dimensions
    enriched["week"] = enriched["date_dt"].dt.isocalendar().week.astype(int)
    enriched["month"] = enriched["date_dt"].dt.strftime("%Y-%m")

    # Festive window: 1 Nov to 8 Nov (Diwali week)
    diwali_dt = pd.Timestamp(DIWALI_DATE)
    festive_start = (diwali_dt - pd.Timedelta(days=7)).strftime("%Y-%m-%d")
    festive_end = diwali_dt.strftime("%Y-%m-%d")
    enriched["is_festive_window"] = (enriched["date"] >= festive_start) & (enriched["date"] <= festive_end)

    enriched = enriched.drop(columns=["date_dt"])
    return enriched


def build_and_save_sales_enriched(conn: sqlite3.Connection) -> int:
    """Build sales_enriched and persist into SQLite with indexes."""
    df = build_sales_enriched(conn)
    if df.empty:
        conn.execute("DROP TABLE IF EXISTS sales_enriched")
        conn.commit()
        return 0

    conn.execute("DROP TABLE IF EXISTS sales_enriched")
    df.to_sql("sales_enriched", conn, if_exists="replace", index=False)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sales_enriched_date ON sales_enriched(date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sales_enriched_sku ON sales_enriched(sku)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sales_enriched_category ON sales_enriched(category)")
    conn.commit()
    return len(df)
