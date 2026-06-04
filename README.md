# Parking Revenue Reconciliation Tool (PRRT)

## What problem does this solve?

Municipal parking systems, parking operators, and payment vendors produce transaction records from many sources (on‑street pay stations, mobile apps, kiosks, third‑party consolidators). These feeds often use different field names and contain small discrepancies (rounding, duplicate records, mismatched timestamps). Reconciling posted revenue across sources and producing auditable ledger entries and reports is time consuming and error prone when done manually.

PRRT automates the reconciliation pipeline: ingest transaction feeds, clean and normalize records, group transactions into logical ledger entries, validate totals, and export human‑readable Excel reports together with an audit trail.

## How we approach the problem

- Ingest: load CSV or structured feeds and normalize column names and types so downstream logic can rely on predictable fields.
- Clean: parse amounts, normalize dates/timezones, and remove or flag malformed rows.
- Group: group transactions by user-specified criteria (date, location, revenue source) to create logical buckets for ledger entries.
- Aggregate: sum and count transactions within each group to produce ledger entries suitable for reporting and posting to financial systems.
- Validate: compare aggregated ledger totals back to source transactions and flag mismatches for investigation.
- Report & Audit: export summary and detail Excel reports and write an append-only JSON-lines audit log to record actions and metadata.

This repository is organized to keep each step testable, small, and replaceable so you can extend or replace logic (for example, add support for new input formats or modify grouping rules) without breaking the rest of the pipeline.

## What I fixed / recent work

- Fixed import-time errors in `report.py` so the module can be imported during test discovery. A safe `pandas` import guard was added and accidental top-level Excel-writing code was removed.
- Implemented and cleaned up `post.py` (transaction grouping and ledger generation) so the module functions are well-typed, validated, and tested.
- Added guarded pytest test suites for several modules, including `tests/test_post.py`, `tests/test_audit.py`, and `tests/test_report.py`.
- Upgraded `openpyxl` and verified exports still work (note: openpyxl currently emits a DeprecationWarning from `utcnow()` — this is external to the repo).
- Initialized a Git repository and pushed the current workspace to GitHub: https://github.com/Neil1355/parking_revenue_reconciliation_tool

If you'd like, I can open a PR with these changes or split the work into smaller commits for review.

## Repository layout

- `ingest.py` — load and normalize input feeds
- `post.py` — group transactions and create ledger entries (aggregation, validation)
- `report.py` — build summary and detail payloads and export to Excel (openpyxl)
- `audit.py` — append-only JSON-lines audit log and reporting helpers
- `main.py` — lightweight CLI orchestrator to run the pipeline
- `tests/` — pytest suites covering modules
- `requirements.txt` — runtime dependencies

## Quick start — development

1. Create a Python 3.11+ virtual environment (this repo was validated with Python 3.13):

```bash
python -m venv .venv
source .venv/bin/activate    # on Windows: .venv\Scripts\Activate.ps1 (PowerShell)
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the test suite:

```bash
python -m pytest -q
```

4. Run the pipeline (example):

```bash
python main.py --input-file data/transactions.csv --output-file reports/out.xlsx --group-by transaction_date,location
```

Notes:
- Many tests are written to avoid heavy I/O; the `report.export_to_excel` path will only run if `openpyxl` is available.
- If you run into DeprecationWarnings about `datetime.utcnow()`, they currently originate from the `openpyxl` package and from a couple of places in this codebase; we can update timestamps to use timezone-aware datetimes to silence those warnings.

## Contributing

- Use the included tests as guidance for expected behavior.
- If you add a new feature, include unit tests under `tests/` and run `pytest` locally.
- If you modify public function signatures, update docstrings and tests accordingly.

