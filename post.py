"""
Post Module - Transaction Grouping and Ledger Generation

Processes cleaned transactions, groups them by specified criteria,
and generates ledger-formatted entries for reconciliation.
"""

from typing import Dict, List, Any, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def group_transactions(
    transactions: List[Dict[str, Any]],
    group_keys: List[str]
) -> Dict[Tuple, List[Dict[str, Any]]]:
    """
    Group transactions by specified key fields.

    Args:
        transactions: List of cleaned transaction records
        group_keys: List of field names to group by (e.g., ['date', 'location'])

    Returns:
        Dictionary where keys are tuples of grouped values and values are
        lists of transactions in that group

    Logic Steps:
        1. Create empty grouping dictionary
        2. Iterate through each transaction
        3. Extract values for group_keys to form tuple key
        4. Append transaction to corresponding group
        5. Return grouped dictionary
    """
    if transactions is None:
        raise ValueError('transactions must be a list')
    if not isinstance(group_keys, list):
        raise TypeError('group_keys must be a list of field names')

    groups: Dict[Tuple, List[Dict[str, Any]]] = {}
    for tx in transactions:
        # build key tuple in order of group_keys
        key = tuple(tx.get(k) for k in group_keys)
        groups.setdefault(key, []).append(tx)

    logger.info('Grouped %d transactions into %d groups', len(transactions), len(groups))
    return groups


def aggregate_to_ledger(
    grouped_transactions: Dict[Tuple, List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """
    Convert grouped transactions into ledger entries.

    Args:
        grouped_transactions: Dictionary of grouped transactions from group_transactions()

    Returns:
        List of ledger entries with aggregated amounts and transaction counts

    Logic Steps:
        1. Iterate through each group
        2. Calculate total revenue for the group
        3. Count transactions in group
        4. Create ledger entry with group identifiers and aggregates
        5. Return list of ledger entries
    """
    if grouped_transactions is None:
        return []

    ledger_entries: List[Dict[str, Any]] = []
    for group_key, txs in grouped_transactions.items():
        entry = generate_ledger_entry(group_key, txs)
        ledger_entries.append(entry)

    logger.info('Aggregated %d groups into %d ledger entries', len(grouped_transactions), len(ledger_entries))
    return ledger_entries


def generate_ledger_entry(
    group_key: Tuple,
    transactions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Create a single ledger entry from a group of transactions.

    Args:
        group_key: Tuple of values from group_transactions()
        transactions: List of transaction records in this group

    Returns:
        Dictionary representing a single ledger entry with:
        - Group identifiers (date, location, etc.)
        - Total amount
        - Transaction count
        - Generated timestamp

    Logic Steps:
        1. Extract group identifiers from group_key
        2. Sum all transaction amounts
        3. Count number of transactions
        4. Add processing timestamp
        5. Return ledger entry dictionary
    """
    # Extract totals and counts
    total = 0.0
    for tx in transactions or []:
        total += _extract_amount(tx)

    count = len(transactions or [])

    entry: Dict[str, Any] = {
        'group_key': group_key,
        'total_amount': total,
        'total_revenue': total,
        'transaction_count': count,
        'count': count,
        'generated_at': datetime.utcnow().isoformat(),
    }

    return entry


def validate_ledger_totals(
    original_transactions: List[Dict[str, Any]],
    ledger_entries: List[Dict[str, Any]]
) -> bool:
    """
    Verify that total amounts match between source transactions and ledger.

    Args:
        original_transactions: Raw transaction records
        ledger_entries: Aggregated ledger entries

    Returns:
        True if totals match within tolerance, False otherwise

    Logic Steps:
        1. Calculate sum of all original transaction amounts
        2. Calculate sum of all ledger entry amounts
        3. Compare with small tolerance for floating-point errors
        4. Return comparison result
    """
    if original_transactions is None:
        original_transactions = []
    if ledger_entries is None:
        ledger_entries = []

    total_original = sum(_extract_amount(t) for t in original_transactions)

    def _entry_amount(e: Dict[str, Any]) -> float:
        for k in ('total_amount', 'total_revenue', 'total'):
            if k in e and e[k] is not None:
                try:
                    return float(e[k])
                except Exception:
                    continue
        return 0.0

    total_ledger = sum(_entry_amount(e) for e in ledger_entries)

    tol = 1e-6
    ok = abs(total_original - total_ledger) <= tol
    if not ok:
        logger.warning('Ledger totals mismatch: original=%s ledger=%s', total_original, total_ledger)
    return ok


def _extract_amount(transaction: Dict[str, Any]) -> float:
    """
    Internal helper to safely extract monetary amount from transaction.

    Args:
        transaction: Transaction record

    Returns:
        Amount as float, 0.0 if amount not found
    """
    if not transaction or not isinstance(transaction, dict):
        return 0.0

    # Common possible keys
    for key in ('revenue_amount', 'amount', 'value', 'total_revenue'):
        if key in transaction and transaction[key] is not None:
            val = transaction[key]
            try:
                # handle strings like '$1,234.56'
                if isinstance(val, str):
                    # strip common currency chars and commas
                    cleaned = val.replace('$', '').replace(',', '').strip()
                    return float(cleaned)
                return float(val)
            except Exception:
                return 0.0

    return 0.0
    
