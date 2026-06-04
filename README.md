# Parking Revenue Reconciliation Tool (PRRT)

## Overview

Parking Revenue Reconciliation Tool, abbreviated PRRT, is a software system intended to automate the reconciliation of parking-related transaction records from multiple sources. The system is organized as a modular pipeline that ingests transaction feeds, normalizes and validates records, groups transactions into logical buckets, aggregates those buckets into ledger entries, validates totals, and produces human-readable reports and an auditable metadata log.

This repository contains the core pipeline modules, a command-line orchestrator, and a comprehensive test suite to validate behavior and prevent regressions.

## Problem statement

Agencies and operators that manage parking typically receive transaction records from several independent systems. Each source may present records using different field names, date formats, or numeric conventions. The resulting reconciliation problems include:

- Inconsistent field names and data schemas across providers
- Monetary values with different formatting and rounding conventions
- Missing or inconsistent timestamps and timezones
- Duplicate records or near-duplicates introduced by upstream batching or retries
- Small arithmetic discrepancies due to rounding or truncation

Manually reconciling this data is slow and can allow errors to persist. PRRT reduces manual effort by providing deterministic processing steps, validation checks, and exported artifacts that support both automated workflows and manual review.

## Design and approach

The pipeline is intentionally modular. Each module has a narrow responsibility and clear input and output types. The high-level stages are:

- Ingest: Read transaction data from CSV or structured feeds, apply canonical column mapping, and produce a normalized in-memory representation.
- Clean: Parse numeric and date fields, normalize timezone handling, and apply validation rules to filter or flag malformed records.
- Group: Partition transactions into groups defined by a set of grouping keys provided by the user or configuration. Groups are deterministic and stable.
- Aggregate: For each group compute aggregates such as total revenue and transaction counts and produce a ledger-style record containing group identifiers and aggregated metrics.
- Validate: Compare aggregated ledger totals with the sum of source transactions and identify discrepancies that exceed a configurable tolerance.
- Report and Audit: Build summary and detailed representations for human consumption and optionally write consolidated results to Excel files. The pipeline also writes an append-only audit log in JSON-lines format for traceability.

This separation of concerns simplifies testing, allows individual modules to be extended or replaced, and supports running partial workflows during development.

## Recent stabilization work

To improve the repository's reliability and testability the following actions were taken:

- Resolved import-time execution in the reporting module by removing code that executed at import and by guarding optional dependencies. This prevents test runners from failing during module import.
- Implemented robust grouping and ledger generation functions in the post module, along with unit tests that validate aggregation and counting logic.
- Added deterministic pytest suites for the core modules. Tests minimize heavy I/O by using mocks and temporary file paths when necessary.
- Upgraded the Excel writer dependency to a more recent release to ensure compatibility with the runtime environment. An external dependency emits a deprecation warning related to timestamp handling. This warning does not affect correctness but should be resolved in an upstream release or by migrating timestamp creation to timezone-aware datetimes within this codebase.

These changes were made to enable continuous integration and to make the codebase easier to review and extend.

## Repository layout

The repository is organized to reflect the pipeline stages and to keep responsibilities clear:

- `ingest.py` - ingestion and normalization utilities for input feeds.
- `post.py` - grouping, aggregation, and ledger entry generation logic.
- `report.py` - functions to assemble summary and detail payloads and optional export to Excel.
- `audit.py` - append-only audit logging and audit report helpers.
- `main.py` - a small command-line entry point that orchestrates a single pipeline run.
- `tests/` - pytest test modules that exercise the core logic.
- `requirements.txt` - a concise list of runtime dependencies for development and deployment.

## Development environment and prerequisites

The project is compatible with Python 3.11 and later; development was performed using Python 3.13. Use an isolated virtual environment when working on the project to avoid affecting system packages.

Recommended setup steps:

1. Create and activate a virtual environment:

```bash
python -m venv .venv
# On macOS or Linux:
source .venv/bin/activate
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
```

2. Install project dependencies:

```bash
pip install -r requirements.txt
```

3. Execute the test suite to verify the environment:

```bash
python -m pytest -q
```

Running tests locally before editing ensures that any changes introduced are validated against the current expectations.

## Command line usage

The `main.py` module provides a simple command-line interface to run the reconciliation pipeline for a single input file. The primary options are:

- `--input-file`: Path to the input CSV file containing transactions.
- `--output-file`: Path to the Excel report to write. Optional; if omitted the export step can be skipped.
- `--config-file`: Path to a YAML configuration file containing default settings and column mappings.
- `--group-by`: Comma-separated list of fields to use when grouping transactions.
- `--audit-log`: Path to an append-only audit log.

Example invocation:

```bash
python main.py --input-file data/transactions.csv --output-file reports/out.xlsx --group-by transaction_date,location
```

Operational notes:

- The `--group-by` parameter should reference fields that are present in the normalized transaction records. Use the ingest module mapping to adapt vendor-specific names to canonical names.
- Excel export requires `openpyxl`. If that package is not present the export step will raise a clear error. Unit tests avoid running the full Excel export unless the dependency is available.

## Configuration

The repository includes a `config.yaml` template that can be used to specify default behaviors, such as:

- Default output paths and file names.
- Canonical column mappings for vendor feeds.
- Required fields for validation.
- Numeric tolerance thresholds for total comparisons.

Configuration is loaded by the CLI and applied during the ingestion and validation stages.

## Testing strategy and best practices

The test suite is designed to be deterministic and fast. Tests avoid external network calls and minimize heavy file I/O by using fixtures and temporary directories.

Best practices for adding tests:

1. Add unit tests for each new function and for edge cases.
2. Use `tmp_path` fixtures for temporary files to avoid leaving artifacts in the repository.
3. Mock heavy dependencies, such as Excel writers or external APIs, to keep tests focused on behavior.

## Continuous integration recommendations

Integrate the project with CI to validate changes automatically. A minimal CI workflow should:

1. Set up the Python environment.
2. Install dependencies from `requirements.txt`.
3. Run the test suite and report status.
4. Optionally run linting and static analysis tools.

I can prepare a GitHub Actions workflow file that implements these steps and runs on pull requests.

## Observability and audit considerations

The pipeline writes structured logs and an append-only audit log for each run. The audit log captures metadata such as input and output counts, timestamps, and discrepancies discovered.

Operational recommendations:

- Rotate or archive audit logs to prevent uncontrolled growth.
- Redact or encrypt sensitive fields in audit logs when required by policy.
- Integrate critical alerts with monitoring systems if runs fail or if discrepancies exceed thresholds.

## Known limitations and next work items

Current limitations:

- An external Excel library emits deprecation warnings relating to naive UTC timestamp construction. These warnings do not affect functionality but should be addressed.

Recommended next steps:

1. Convert naive UTC timestamps to timezone-aware timestamps across the codebase to remove deprecation warnings.
2. Add CI workflow to run tests on pull requests.
3. Expand ingest adapters and strengthen schema validation.
4. Add documentation for common vendor mappings and example data files.

## Contribution guidelines

Contributions are accepted via pull requests. When preparing changes please:

1. Create a feature branch for your work.
2. Include unit tests that cover new or changed behavior.
3. Run the test suite locally and ensure all tests pass.
4. Provide a clear description of the change and any operational impact.

## Contact and support

For questions or to request additional capabilities, open an issue on the repository or contact me via neilbarot5@gmail.com.

---


