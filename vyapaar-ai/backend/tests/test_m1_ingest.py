"""M1 tests: ingest validation, payment-mode normalisation, column mapping, and upload with sample files + messy CSV."""
import io
import os
from pathlib import Path
import tempfile

import pytest
from fastapi.testclient import TestClient

# Isolate the test DB before importing the app.
os.environ["VYAPAAR_DB_PATH"] = str(Path(tempfile.mkdtemp()) / "test_m1_ingest.db")

from app.config import settings
from app.db import store
from app.ingest.loaders import normalise_payment_mode, parse_date_lenient, _num
from app.ingest.mapping import map_headers
from app.main import app

client = TestClient(app)


def test_fuzzy_header_mapping() -> None:
    mapping = map_headers(["Item Code", "Qty", "Bill No", "Rate"], "sales")
    assert mapping["Item Code"] == "sku"
    assert mapping["Qty"] == "qty"
    assert mapping["Bill No"] == "invoice_id"
    assert mapping["Rate"] == "unit_price"


def test_lenient_date_parsing() -> None:
    assert parse_date_lenient("2026-11-13") == "2026-11-13"
    assert parse_date_lenient("13/11/2026") == "2026-11-13"
    assert parse_date_lenient("13-11-26") == "2026-11-13"
    assert parse_date_lenient("13/11/26") == "2026-11-13"
    assert parse_date_lenient("2026-11-01 10:30:00") == "2026-11-01"
    assert parse_date_lenient("01.11.2026") == "2026-11-01"
    assert parse_date_lenient("not a date") is None
    assert parse_date_lenient("") is None


def test_payment_mode_synonyms() -> None:
    assert normalise_payment_mode("GPay") == "upi"
    assert normalise_payment_mode("PhonePe") == "upi"
    assert normalise_payment_mode("Paytm") == "upi"
    assert normalise_payment_mode("Cash") == "cash"
    assert normalise_payment_mode("Udhaar") == "khata"
    assert normalise_payment_mode("Credit") == "khata"
    assert normalise_payment_mode("POS") == "card"
    assert normalise_payment_mode("pigeon post") is None


def test_numeric_parser_with_currency_and_commas() -> None:
    assert _num(100) == 100.0
    assert _num("150.50") == 150.50
    assert _num("₹1,250") == 1250.0
    assert _num("Rs 2,500.00") == 2500.0
    assert _num("invalid") is None


def test_upload_never_crashes_on_malformed_file() -> None:
    response = client.post(
        "/api/upload",
        files=[("files", ("junk.csv", b"\x00\x01not,a,csv\x00", "application/octet-stream"))],
    )
    assert response.status_code == 200, response.text
    report = response.json()["files"][0]
    assert report["rows_ok"] == 0
    assert report["reasons"] == {"unknown_table": 1}


def test_upload_all_sample_files() -> None:
    """Test POST /api/upload with all sample CSVs."""
    sample_dir = settings.sample_data_dir
    files_payload = []
    for csv_path in sorted(sample_dir.glob("*.csv")):
        files_payload.append(
            ("files", (csv_path.name, csv_path.read_bytes(), "text/csv"))
        )

    res = client.post("/api/upload", files=files_payload)
    assert res.status_code == 200, res.text
    body = res.json()

    assert "files" in body
    assert "as_of" in body
    assert body["as_of"] == "2026-11-13"
    assert len(body["files"]) == 7

    reports = {r["name"]: r for r in body["files"]}
    assert reports["products.csv"]["rows_ok"] == 38
    assert reports["sales.csv"]["rows_ok"] == 44305


def test_upload_deliberately_messy_csv_and_reupload_replacement() -> None:
    """Test POST /api/upload with messy data and re-upload replacement behavior.

    Ingest rules verified:
    - Lenient dates (YYYY-MM-DD, DD/MM/YYYY, DD-MM-YY)
    - Payment mode synonyms (GPay, PhonePe, Paytm, Udhaar, Credit, POS)
    - Rejections for unknown SKU, qty <= 0, price < 0 with counts per reason
    - Never drop silently: rows_ok + rows_rejected == total_rows
    - Re-upload replaces table and bumps data_version.
    """
    initial_version = store.data_version

    # First, ensure products table has valid SKUs for foreign key checking
    products_csv = (
        "Item Code,Product Name,Category,MRP,Cost Price,GST %,Supplier,Lead Time,Reorder Level\n"
        "ATT01,Aashirvaad Atta 5kg,Staples,₹250,₹220,0,Gupta Traders,3,15\n"
        "GHE01,Amul Ghee 1L,Oil & Ghee,₹600,₹540,12,Jain Distributors,2,10\n"
    )

    # Deliberately messy sales CSV with mixed headers, currency symbols, bad dates, bad modes, negative numbers
    messy_sales_csv = (
        "Bill No,Bill Date,Time,Item Code,Units,Selling Price,Payment Method,Customer ID,Notes\n"
        # Row 1: Valid row with YYYY-MM-DD and GPay -> upi
        "INV001,2026-11-01,10:00,ATT01,2,₹250,GPay,C001,Walk-in\n"
        # Row 2: Valid row with DD/MM/YYYY and PhonePe -> upi, numeric with comma
        "INV002,02/11/2026,11:30,GHE01,1,600.00,PhonePe,,Regular\n"
        # Row 3: Valid row with DD-MM-YY and Udhaar -> khata
        "INV003,03-11-26,12:15,ATT01,1,250,Udhaar,C002,On credit\n"
        # Row 4: Valid row with POS, numeric with quotes and comma
        'INV004,2026-11-04,14:00,GHE01,2,"Rs 1,200",POS,,\n'
        # Row 5: Bad date
        "INV005,32/13/2026,15:00,ATT01,1,250,Cash,,\n"
        # Row 6: Bad payment mode (pigeon_post)
        "INV006,2026-11-05,15:30,ATT01,1,250,pigeon_post,,\n"
        # Row 7: Bad qty (0)
        "INV007,2026-11-05,16:00,ATT01,0,250,Cash,,\n"
        # Row 8: Bad qty (negative)
        "INV008,2026-11-05,16:15,ATT01,-3,250,Cash,,\n"
        # Row 9: Bad price (negative)
        "INV009,2026-11-06,17:00,GHE01,1,-50,Cash,,\n"
        # Row 10: Unknown SKU
        "INV010,2026-11-06,17:30,NON_EXISTENT_SKU,1,100,Cash,,\n"
    )

    res = client.post(
        "/api/upload",
        files=[
            ("files", ("products.csv", products_csv.encode("utf-8"), "text/csv")),
            ("files", ("messy_sales.csv", messy_sales_csv.encode("utf-8"), "text/csv")),
        ],
    )
    assert res.status_code == 200, res.text
    body = res.json()

    assert "files" in body
    reports = {r["name"]: r for r in body["files"]}

    sales_report = reports["messy_sales.csv"]
    # 4 valid rows (rows 1-4), 6 rejected rows (rows 5-10)
    assert sales_report["rows_ok"] == 4
    assert sales_report["rows_rejected"] == 6

    # Verify counts per rejection reason (never dropped silently)
    reasons = sales_report["reasons"]
    assert reasons["bad_date"] == 1
    assert reasons["bad_payment_mode"] == 1
    assert reasons["bad_qty"] == 2  # 0 and -3
    assert reasons["bad_price"] == 1  # -50
    assert reasons["unknown_sku"] == 1  # NON_EXISTENT_SKU
    assert sales_report["rows_ok"] + sales_report["rows_rejected"] == 10

    # Data version bumped
    new_version = store.data_version
    assert int(new_version) > int(initial_version)

    # Re-upload replaces table: upload 1 single new sale row
    clean_replacement_sales = (
        "invoice_id,date,time,sku,qty,unit_price,payment_mode,customer_id\n"
        "REP001,2026-11-10,09:00,ATT01,5,250,cash,\n"
    )
    res_replace = client.post(
        "/api/upload",
        files=[("files", ("sales.csv", clean_replacement_sales.encode("utf-8"), "text/csv"))],
    )
    assert res_replace.status_code == 200
    rep_body = res_replace.json()
    assert rep_body["files"][0]["rows_ok"] == 1

    # Verify table replaced in database
    sales_df = store.table("sales")
    assert len(sales_df) == 1
    assert sales_df.iloc[0]["invoice_id"] == "REP001"
    assert int(store.data_version) > int(new_version)
