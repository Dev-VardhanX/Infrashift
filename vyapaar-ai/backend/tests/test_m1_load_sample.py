"""M1 tests: /api/load-sample loads the 7 sample CSVs (doc 03, checkpoint C1)."""
import os
import tempfile
from pathlib import Path

# Isolate the test DB before importing the app.
os.environ["VYAPAAR_DB_PATH"] = str(Path(tempfile.mkdtemp()) / "test_m1_load.db")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def test_load_sample_returns_counts_and_as_of() -> None:
    response = client.post("/api/load-sample")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["as_of"] == "2026-11-13"
    loaded = body["loaded"]
    # 7 tables loaded (doc 01 US-1: accepts the 7 files in data/sample/).
    assert len(loaded) == 7
    # 38 SKUs; sales rows = actual data rows in data/sample/sales.csv.
    # NOTE: docs/06 says "44,303 lines / 22,822 invoices" but the file really
    # holds 44,305 rows / 22,824 invoices — flagged to M4 to fix the doc.
    assert loaded.get("products", loaded.get("products.csv")) == 38
    assert loaded.get("sales", loaded.get("sales.csv")) == 44305


def test_load_sample_is_idempotent() -> None:
    first = client.post("/api/load-sample").json()
    second = client.post("/api/load-sample").json()
    assert first["loaded"] == second["loaded"]
    assert first["as_of"] == second["as_of"]


def test_health_reports_as_of() -> None:
    body = client.get("/api/health").json()
    assert body["ok"] is True
    assert body["as_of"] == "2026-11-13"
