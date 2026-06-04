"""
Main Module - CLI Orchestrator

Provides command-line interface and orchestrates the parking revenue
reconciliation workflow across all modules.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

try:
    import yaml
except Exception:
    yaml = None


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Namespace object containing parsed arguments:
        - input_file: Path to input CSV file
        - output_file: Path to output Excel report
        - config_file: Path to config YAML file
        - group_by: Comma-separated list of fields to group by
        - audit_log: Path to audit log file
        - verbose: Boolean flag for verbose output

    Logic Steps:
        1. Create ArgumentParser
        2. Add required arguments (input_file)
        3. Add optional arguments (output_file, config_file, etc.)
        4. Parse sys.argv
        5. Return parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Parking Revenue Reconciliation Tool (PRRT)"
    )

    parser.add_argument(
        "--input-file",
        required=True,
        help="Path to input CSV file",
    )

    parser.add_argument(
        "--output-file",
        required=False,
        default=None,
        help="Path to output Excel report",
    )

    parser.add_argument(
        "--config-file",
        required=False,
        default="config.yaml",
        help="Path to config YAML file",
    )

    parser.add_argument(
        "--group-by",
        required=False,
        default=None,
        help="Comma-separated list of fields to group by",
    )

    parser.add_argument(
        "--audit-log",
        required=False,
        default="audit.log",
        help="Path to audit log file",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    return parser.parse_args()


def main() -> int:
    """
    Orchestrate the complete reconciliation workflow.

    Returns:
        Exit code (0 for success, non-zero for failure)

    Logic Steps:
        1. Parse command-line arguments
        2. Load configuration from config file
        3. Call ingest.load_csv() to load input data
        4. Call ingest.validate_schema() to validate data
        5. Call ingest.map_columns() with config mappings
        6. Call ingest.clean_transactions() to clean data
        7. Call post.group_transactions() to group by specified fields
        8. Call post.aggregate_to_ledger() to create ledger entries
        9. Call report.generate_summary_report() for summary
        10. Call report.generate_transaction_detail_report() for details
        11. Call report.export_to_excel() to write output file
        12. Call audit.log_operation() to record the execution
        13. Print summary and return 0 on success, 1 on failure
    """
    args = parse_arguments()

    # Load config if possible
    config = {}
    try:
        config_path = Path(args.config_file)
        if yaml and config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
    except Exception:
        # fall back to empty config
        config = {}

    # Helper safe audit logger
    def _safe_audit_log(operation: str, input_count: int = 0, output_count: int = 0, details: Optional[dict] = None):
        try:
            import audit as _audit

            _audit.log_operation(operation, input_count, output_count, details=details, log_filepath=args.audit_log)
        except Exception:
            # best-effort only
            if args.verbose:
                print("Warning: failed to write audit log")

    try:
        # Dynamic imports of processing modules
        import ingest
        import post
        import report

        # Step 1: Load transactions
        data = ingest.load_csv(args.input_file)
        input_count = len(data) if data is not None else 0

        # Step 2: Validate schema if available
        if hasattr(ingest, "validate_schema") and config.get("required_fields"):
            valid = ingest.validate_schema(data, config.get("required_fields", []))
            if not valid:
                raise ValueError("Schema validation failed")

        # Step 3: Map columns if mapping present
        if hasattr(ingest, "map_columns") and config.get("column_mapping"):
            data = ingest.map_columns(data, config.get("column_mapping", {}))

        # Step 4: Clean transactions
        if hasattr(ingest, "clean_transactions"):
            data = ingest.clean_transactions(data)

        # Step 5: Group transactions
        group_by = []
        if args.group_by:
            group_by = [g.strip() for g in args.group_by.split(",") if g.strip()]

        grouped = data
        if hasattr(post, "group_transactions"):
            grouped = post.group_transactions(data, group_by)

        # Step 6: Aggregate to ledger
        ledger = grouped
        if hasattr(post, "aggregate_to_ledger"):
            ledger = post.aggregate_to_ledger(grouped)

        output_count = len(ledger) if ledger is not None else 0

        # Step 7: Generate reports
        out_path = args.output_file or config.get("default_output")
        if out_path and hasattr(report, "export_to_excel"):
            report.export_to_excel(out_path, ledger)

        # Step 8: Audit log
        _safe_audit_log("run", input_count=input_count, output_count=output_count)

        if args.verbose:
            print(f"Run complete. {output_count} rows posted. Report: {out_path}")

        return 0

    except Exception as e:
        _safe_audit_log("run", input_count=0, output_count=0, details={"error": str(e)})
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
