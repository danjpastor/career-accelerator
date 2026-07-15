"""Applied Lab 33: Ingest paginated REST API and JSON data."""

from pathlib import Path
import json

try:
    import pandas as pd
except ImportError:
    pd = None

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "practice" / "applied" / "datasets" / "api_json"

def load_page(filename: str) -> dict:
    """Read one local API-response fixture."""
    path = DATA / filename
    return json.loads(path.read_text(encoding="utf-8"))

def main() -> None:
    print("Dataset folder:", DATA)
    page_name = "page_1.json"
    seen_pages = set()
    records = []
    while page_name:
        if page_name in seen_pages:
            raise RuntimeError(f"Pagination loop detected: {page_name}")
        seen_pages.add(page_name)
        payload = load_page(page_name)
        if payload.get("status") != 200:
            raise RuntimeError(f"API fixture failed: {payload}")
        records.extend(payload.get("data", []))
        page_name = payload.get("next_page")

    print(f"Loaded {len(records)} raw records from {len(seen_pages)} pages.")
    # TODO: flatten nested fields, detect duplicate IDs and schema drift,
    # add extraction metadata, validate, and export a clean CSV.

if __name__ == "__main__":
    main()
