"""
Audit Module - Audit Logging and Tracking

Manages audit log creation, writing, and tracking of all operations for
compliance and reconciliation verification.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import json
import os
import uuid


def create_audit_log_entry(
    operation: str,
    details: Dict[str, Any],
    status: str = "success"
) -> Dict[str, Any]:
    """
    Create a new audit log entry.

    Args:
        operation: Name of the operation being logged (e.g., "ingest_csv", "generate_report")
        details: Dictionary of operation-specific details
        status: Status of operation ("success" or "failure")

    Returns:
        Dictionary containing:
        - timestamp: ISO format datetime
        - operation: Operation name
        - details: Operation details
        - status: Operation status
        - entry_id: Unique identifier for this log entry

    Logic Steps:
        1. Get current timestamp
        2. Generate unique entry ID
        3. Assemble audit entry dictionary
        4. Return complete audit entry
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    entry_id = _generate_entry_id()

    audit_entry = {
        "timestamp": timestamp,
        "operation": operation,
        "details": details or {},
        "status": status,
        "entry_id": entry_id,
    }

    return audit_entry


def write_audit_log(
    entry: Dict[str, Any],
    log_filepath: str,
    append: bool = True
) -> bool:
    """
    Write a single audit log entry to the audit log file.

    Args:
        entry: Audit log entry from create_audit_log_entry()
        log_filepath: Path to audit log file
        append: If True, append to existing log; if False, create new log

    Returns:
        True if write successful, False otherwise

    Logic Steps:
        1. Check if log file exists
        2. Open file in append or write mode as specified
        3. Serialize entry to JSON
        4. Write entry to file with newline separator
        5. Close file and return success status
    """
    try:
        mode = "a" if append else "w"
        # Ensure directory exists
        dirpath = os.path.dirname(log_filepath)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)

        with open(log_filepath, mode, encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str))
            f.write("\n")

        return True
    except Exception:
        return False


def log_operation(
    operation: str,
    input_count: int,
    output_count: int,
    details: Optional[Dict[str, Any]] = None,
    log_filepath: str = "audit.log"
) -> bool:
    """
    Convenience function to log a complete operation with input/output counts.

    Args:
        operation: Operation name
        input_count: Number of records processed
        output_count: Number of records output
        details: Optional additional details
        log_filepath: Path to audit log file

    Returns:
        True if logging successful, False otherwise

    Logic Steps:
        1. Create details dictionary with input/output counts
        2. Merge with additional details if provided
        3. Create audit log entry
        4. Write entry to log file
        5. Return success status
    """
    merged_details = {"input_count": input_count, "output_count": output_count}
    if details:
        merged_details.update(details)

    entry = create_audit_log_entry(operation=operation, details=merged_details)
    return write_audit_log(entry, log_filepath, append=True)


def read_audit_log(
    log_filepath: str
) -> list[Dict[str, Any]]:
    """
    Read all entries from an audit log file.

    Args:
        log_filepath: Path to audit log file

    Returns:
        List of audit log entry dictionaries

    Logic Steps:
        1. Check if log file exists
        2. Open and read file
        3. Parse each line as JSON
        4. Collect entries into list
        5. Return entries list
    """
    entries: list[Dict[str, Any]] = []
    if not os.path.exists(log_filepath):
        return entries

    try:
        with open(log_filepath, mode="r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    entries.append(obj)
                except json.JSONDecodeError:
                    # Skip malformed lines
                    continue
    except Exception:
        return []

    return entries


def generate_audit_report(
    log_filepath: str
) -> Dict[str, Any]:
    """
    Generate summary report from audit log.

    Args:
        log_filepath: Path to audit log file

    Returns:
        Dictionary containing:
        - total_operations: Count of all operations logged
        - success_count: Count of successful operations
        - failure_count: Count of failed operations
        - operations_by_type: Dictionary of operation counts by type
        - total_records_processed: Sum of input_count across all operations

    Logic Steps:
        1. Read audit log entries
        2. Count total operations
        3. Count successes vs failures
        4. Group and count by operation type
        5. Sum input records across operations
        6. Return summary report
    """
    entries = read_audit_log(log_filepath)

    total_operations = len(entries)
    success_count = 0
    failure_count = 0
    operations_by_type: Dict[str, int] = {}
    total_records_processed = 0

    for e in entries:
        status = e.get("status", "success")
        if status == "success":
            success_count += 1
        else:
            failure_count += 1

        op = e.get("operation")
        if op:
            operations_by_type[op] = operations_by_type.get(op, 0) + 1

        details = e.get("details", {}) or {}
        try:
            total_records_processed += int(details.get("input_count", 0))
        except Exception:
            # ignore non-int values
            pass

    return {
        "total_operations": total_operations,
        "success_count": success_count,
        "failure_count": failure_count,
        "operations_by_type": operations_by_type,
        "total_records_processed": total_records_processed,
    }


def _generate_entry_id() -> str:
    """
    Internal helper to generate unique audit entry ID.

    Returns:
        Unique string identifier for audit entry
    """
    return f"audit-{uuid.uuid4().hex}"
