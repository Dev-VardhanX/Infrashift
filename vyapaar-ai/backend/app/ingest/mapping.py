"""M1 ingest: column header mapping and table detection.

Doc 02 section 2:
- Exact header match first
- Canonical alias lookup (e.g. Item Code -> sku, Qty -> qty, Bill No -> invoice_id)
- Rapidfuzz fuzzy header mapping for billing app exports
- Table detection by filename keywords and column matching.
"""
from rapidfuzz import fuzz, process

# Canonical headers per table = CSV headers (doc 02 section 2).
CANONICAL: dict[str, list[str]] = {
    "products": [
        "sku", "name", "category", "mrp", "cost_price", "gst_rate",
        "supplier", "lead_time_days", "reorder_level",
    ],
    "sales": [
        "invoice_id", "date", "time", "sku", "qty", "unit_price",
        "payment_mode", "customer_id",
    ],
    "inventory": ["sku", "current_stock", "last_restocked"],
    "purchases": ["purchase_id", "date", "sku", "qty", "unit_cost", "supplier"],
    "expenses": ["date", "category", "amount", "payment_mode", "note"],
    "customers": [
        "customer_id", "name", "phone", "khata_balance",
        "last_payment_date", "credit_limit",
    ],
    "khata_payments": ["date", "customer_id", "amount", "mode"],
}

# Known synonyms from billing-app exports (exact, lowercased match first).
ALIASES: dict[str, str] = {
    "item code": "sku", "item": "sku", "product code": "sku", "code": "sku", "item_code": "sku",
    "product name": "name", "item name": "name", "product": "name", "item_name": "name",
    "quantity": "qty", "units": "qty", "qnt": "qty", "count": "qty",
    "price": "unit_price", "rate": "unit_price", "unit price": "unit_price",
    "selling price": "unit_price", "sales price": "unit_price", "mrp price": "unit_price",
    "payment mode": "payment_mode", "payment method": "payment_mode",
    "pay mode": "payment_mode", "mode of payment": "payment_mode", "pay_mode": "payment_mode",
    "invoice": "invoice_id", "bill no": "invoice_id", "bill number": "invoice_id",
    "invoice no": "invoice_id", "invoice number": "invoice_id", "bill_no": "invoice_id",
    "txn date": "date", "bill date": "date", "invoice date": "date", "sale date": "date",
    "customer": "customer_id", "customer code": "customer_id", "party code": "customer_id",
    "stock": "current_stock", "stock on hand": "current_stock",
    "closing stock": "current_stock", "qty in stock": "current_stock", "current stock": "current_stock",
    "value": "amount", "total": "amount", "expense amount": "amount",
    "tax rate": "gst_rate", "gst %": "gst_rate", "gst": "gst_rate", "gst rate": "gst_rate",
    "cost": "cost_price", "purchase cost": "cost_price", "unit cost": "unit_cost",
    "lead time": "lead_time_days", "reorder point": "reorder_level",
    "balance": "khata_balance", "udhaar": "khata_balance", "udhaar balance": "khata_balance",
    "customer name": "name", "party name": "name",
}

_FUZZ_CUTOFF = 80


def map_headers(columns: list[str], table: str) -> dict[str, str]:
    """Map uploaded column headers to canonical table column names.

    Matching precedence:
    1. Exact canonical header match (case-insensitive)
    2. Exact alias match from ALIASES
    3. Rapidfuzz token_sort_ratio match above cutoff.
    """
    canonical = CANONICAL[table]
    mapping: dict[str, str] = {}
    used: set[str] = set()

    for col in columns:
        clean_col = str(col).strip()
        low = clean_col.lower()

        # 1. Exact match in canonical
        if low in canonical and low not in used:
            mapping[clean_col] = low
            used.add(low)
            continue

        # 2. Known alias match
        target = ALIASES.get(low)
        if target and target in canonical and target not in used:
            mapping[clean_col] = target
            used.add(target)
            continue

        # 3. Fuzzy matching via Rapidfuzz
        candidates = [c for c in canonical if c not in used]
        if candidates:
            match = process.extractOne(
                low,
                candidates,
                scorer=fuzz.token_sort_ratio,
                score_cutoff=_FUZZ_CUTOFF,
            )
            if match:
                matched_target = match[0]
                mapping[clean_col] = matched_target
                used.add(matched_target)

    return mapping


def detect_table(filename: str, columns: list[str]) -> str | None:
    """Detect which table an uploaded file belongs to based on filename and columns."""
    stem = filename.rsplit(".", 1)[0].strip().lower()

    # 1. Exact or substring match in filename
    for table in CANONICAL:
        if table == stem or table in stem:
            return table

    # 2. Fuzzy match filename stem
    match = process.extractOne(
        stem,
        list(CANONICAL),
        scorer=fuzz.token_sort_ratio,
        score_cutoff=70,
    )
    if match:
        return match[0]

    # 3. Best column header match score
    best_table = None
    best_score = 0.0
    for table, canonical in CANONICAL.items():
        mapping = map_headers(columns, table)
        score = len(mapping) / len(canonical)
        if score > best_score:
            best_table = table
            best_score = score

    return best_table if best_score >= 0.4 else None
