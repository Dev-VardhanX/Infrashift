"""M1 ingest: lenient parsing, validation, and table loading.

Doc 02 section 2:
- Lenient date parsing (YYYY-MM-DD, DD/MM/YYYY, DD-MM-YY, etc.)
- Payment mode synonyms (GPay/PhonePe/Paytm->upi, Udhaar/Credit->khata, POS->card, Cash->cash)
- Rejection of unknown SKU, qty <= 0, price < 0 with counts per reason (never drop silently)
- Never crash on malformed file
- Only sales + products are mandatory
- Re-upload replaces that table and bumps data_version.
"""
import datetime as dt
import io
import re
from typing import Any

import pandas as pd

from app import db as db_module
from app.config import settings
from app.ingest.mapping import CANONICAL, detect_table, map_headers

DATE_FORMATS = (
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d-%m-%y",
    "%d/%m/%y",
    "%Y/%m/%d",
    "%d.%m.%Y",
    "%d.%m.%y",
    "%y-%m-%d",
)

PAYMENT_SYNONYMS: dict[str, str] = {
    # UPI variants
    "upi": "upi",
    "gpay": "upi",
    "google pay": "upi",
    "googlepay": "upi",
    "phonepe": "upi",
    "phone pe": "upi",
    "paytm": "upi",
    "bhim": "upi",
    "bhim upi": "upi",
    # Cash variants
    "cash": "cash",
    "rokad": "cash",
    "nagad": "cash",
    # Card variants
    "card": "card",
    "pos": "card",
    "credit card": "card",
    "debit card": "card",
    "swipe": "card",
    # Khata variants
    "khata": "khata",
    "udhaar": "khata",
    "udhar": "khata",
    "credit": "khata",
    "baki": "khata",
}

# Required columns after header mapping
REQUIRED: dict[str, set[str]] = {
    "products": {"sku"},
    "sales": {"invoice_id", "date", "sku", "qty", "unit_price", "payment_mode"},
    "inventory": {"sku", "current_stock"},
    "purchases": {"purchase_id", "date", "sku", "qty", "unit_cost"},
    "expenses": {"date", "category", "amount"},
    "customers": {"customer_id", "khata_balance"},
    "khata_payments": {"date", "customer_id", "amount", "mode"},
}

LOAD_ORDER = ["products", "inventory", "purchases", "expenses", "customers",
              "khata_payments", "sales"]


def parse_date_lenient(value: object) -> str | None:
    """Return ISO date string (YYYY-MM-DD) or None if unparsable."""
    if value is None or (isinstance(value, float) and pd.isna(value)) or value == "":
        return None
    if isinstance(value, (dt.datetime, pd.Timestamp)):
        return value.date().isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()

    # Split on space or T to extract date segment: "2026-11-01 10:30:00" -> "2026-11-01"
    text = str(value).strip().split()[0].split("T")[0]
    for fmt in DATE_FORMATS:
        try:
            parsed = dt.datetime.strptime(text, fmt).date()
            if parsed.year < 100:
                parsed = parsed.replace(year=2000 + parsed.year)
            return parsed.isoformat()
        except ValueError:
            continue

    # Fallback attempt via pandas date parser
    try:
        ts = pd.to_datetime(text, dayfirst=True)
        if pd.notna(ts):
            return ts.date().isoformat()
    except Exception:
        pass

    return None


def normalise_payment_mode(value: object) -> str | None:
    """Normalise payment mode string into canonical {upi, cash, card, khata}."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    key = str(value).strip().lower()
    return PAYMENT_SYNONYMS.get(key)


def _num(value: object) -> float | None:
    """Parse numeric values, stripping currency symbols and formatting commas."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = (
        str(value)
        .strip()
        .replace("₹", "")
        .replace("Rs", "")
        .replace("rs", "")
        .replace(",", "")
        .strip()
    )
    try:
        out = float(text)
        return out if pd.notna(out) else None
    except (TypeError, ValueError):
        return None


def read_csv_bytes(content: bytes) -> pd.DataFrame | None:
    """Safely read CSV bytes across encodings and separators; never raises on malformed input."""
    if not content or len(content.strip()) == 0:
        return None

    # Try common encodings and separators
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        for sep in (",", ";", "\t", "|"):
            try:
                df = pd.read_csv(
                    io.BytesIO(content),
                    sep=sep,
                    encoding=encoding,
                    on_bad_lines="skip",
                )
                if df is not None and len(df.columns) > 1 and len(df) > 0:
                    return df
            except Exception:
                continue

    try:
        return pd.read_csv(io.BytesIO(content), on_bad_lines="skip")
    except Exception:
        return None


def ingest_dataframe(
    conn, table: str, df: pd.DataFrame, mapping: dict[str, str] | None = None
) -> dict[str, Any]:
    """Validate + load one dataframe into `table`. Returns validation report."""
    if mapping is None:
        mapping = map_headers(list(df.columns), table)
    df = df.rename(columns=mapping)

    canonical = CANONICAL[table]
    missing_required = REQUIRED[table] - set(df.columns)
    if missing_required:
        return {
            "name": table,
            "rows_ok": 0,
            "rows_rejected": len(df),
            "reasons": {"missing_columns": sorted(missing_required)},
            "mapping": mapping,
        }

    known_skus: set[str] = set()
    if table == "sales":
        rows = conn.execute("SELECT sku FROM products").fetchall()
        known_skus = {r[0] for r in rows}

    reasons: dict[str, int] = {}
    clean: list[dict[str, Any]] = []

    def reject(reason: str) -> None:
        reasons[reason] = reasons.get(reason, 0) + 1

    for row in df.to_dict(orient="records"):
        if table == "sales":
            iso = parse_date_lenient(row.get("date"))
            mode = normalise_payment_mode(row.get("payment_mode"))
            qty = _num(row.get("qty"))
            price = _num(row.get("unit_price"))
            sku = str(row.get("sku") or "").strip()

            if iso is None:
                reject("bad_date")
            elif mode is None:
                reject("bad_payment_mode")
            elif qty is None or qty <= 0:
                reject("bad_qty")
            elif price is None or price < 0:
                reject("bad_price")
            elif not sku or sku not in known_skus:
                reject("unknown_sku")
            else:
                clean.append({
                    "invoice_id": str(row.get("invoice_id") or "").strip(),
                    "date": iso,
                    "time": str(row.get("time") or "").strip(),
                    "sku": sku,
                    "qty": qty,
                    "unit_price": price,
                    "payment_mode": mode,
                    "customer_id": str(row.get("customer_id") or "").strip() or None,
                })
            continue

        # Generic validation for products, inventory, purchases, expenses, customers, khata_payments
        iso = parse_date_lenient(row.get("date")) if "date" in df.columns else None
        if "date" in df.columns and iso is None:
            reject("bad_date")
            continue

        record: dict[str, Any] = {}
        for col in canonical:
            if col not in df.columns:
                continue
            raw = row.get(col)
            if col in (
                "qty", "amount", "mrp", "cost_price", "unit_cost",
                "khata_balance", "credit_limit", "gst_rate", "current_stock",
            ):
                num = _num(raw)
                if num is None:
                    reject(f"bad_{col}")
                    record = {}
                    break
                record[col] = num
            elif col == "payment_mode":
                record[col] = normalise_payment_mode(raw) or str(raw).strip().lower()
            else:
                record[col] = str(raw).strip() if pd.notna(raw) else None

        if record:
            clean.append(record)

    # Re-upload replaces this table
    if clean:
        db_module.replace_table(conn, table, pd.DataFrame(clean))

    report = {
        "name": table,
        "rows_ok": len(clean),
        "rows_rejected": len(df) - len(clean),
        "reasons": reasons,
        "mapping": mapping,
    }
    return report


def ingest_files(conn, files: dict[str, bytes]) -> tuple[list[dict[str, Any]], str | None]:
    """Ingest uploaded files (name -> bytes). Returns (reports, as_of).

    Products are loaded before sales so SKU checks work properly.
    """
    parsed: list[tuple[str, str, pd.DataFrame]] = []
    unreadable: list[dict[str, Any]] = []

    for filename, content in files.items():
        df = read_csv_bytes(content)
        if df is None:
            unreadable.append({
                "name": filename,
                "rows_ok": 0,
                "rows_rejected": 0,
                "reasons": {"unreadable_file": 1},
                "mapping": {},
            })
            continue
        table = detect_table(filename, [str(c) for c in df.columns])
        parsed.append((table or "unknown", filename, df))

    order = LOAD_ORDER + ["unknown"]
    reports: list[dict[str, Any]] = []

    for table in order:
        for tab, filename, df in parsed:
            if tab != table:
                continue
            if tab == "unknown":
                reports.append({
                    "name": filename,
                    "rows_ok": 0,
                    "rows_rejected": len(df),
                    "reasons": {"unknown_table": 1},
                    "mapping": {},
                })
            else:
                report = ingest_dataframe(conn, tab, df)
                report["name"] = filename
                reports.append(report)

    reports.extend(unreadable)

    # Refresh sales_enriched view if sales or products updated
    from app.ingest.enriched import build_and_save_sales_enriched
    build_and_save_sales_enriched(conn)
    db_module.bump_data_version(conn)

    return reports, db_module.as_of(conn)


class TableCounts(dict):
    """Dictionary supporting lookup by table name or filename."""

    def __getitem__(self, key: str) -> int:
        if key not in self:
            alt = key[:-4] if key.endswith(".csv") else f"{key}.csv"
            if alt in self:
                return super().__getitem__(alt)
        return super().__getitem__(key)

    def get(self, key: str, default: object = None) -> object:
        try:
            return self[key]
        except KeyError:
            return default


def load_sample(conn) -> tuple[dict[str, int], str | None]:
    """Load the bundled sample CSVs (doc 03 C1). Returns (counts, as_of)."""
    db_module.clear_all(conn)
    directory = settings.sample_data_dir
    files = {p.name: p.read_bytes() for p in sorted(directory.glob("*.csv"))}
    if len(files) != len(CANONICAL):
        raise FileNotFoundError(
            f"expected {len(CANONICAL)} sample CSVs in {directory}, found {len(files)}"
        )
    reports, as_of = ingest_files(conn, files)
    counts = TableCounts({
        (r["name"].rsplit(".", 1)[0] if "." in r["name"] else r["name"]): r["rows_ok"]
        for r in reports
    })
    return counts, as_of
