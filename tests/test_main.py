"""
Tests for `main.py` CLI orchestrator.

These tests avoid invoking heavy processing by inserting lightweight
fake modules into `sys.modules` and assert the CLI parsing and
top-level `main()` return codes.
"""
from pathlib import Path
import sys
import types

import pytest


def test_parse_arguments_minimal(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['prog', '--input-file', 'input.csv'])
    ns = __import__('main').parse_arguments()
    assert ns.input_file == 'input.csv'
    assert ns.output_file is None
    assert ns.config_file == 'config.yaml'
    assert ns.group_by is None
    assert ns.audit_log == 'audit.log'
    assert not ns.verbose


def _install_fake_modules(monkeypatch, *, ingest=None, post=None, report=None, audit=None):
    # lightweight fake processing modules to keep tests fast and deterministic
    if ingest is None:
        ingest = types.SimpleNamespace(
            load_csv=lambda path: [{'id': 1}],
            validate_schema=lambda data, req: True,
            map_columns=lambda d, m: d,
            clean_transactions=lambda d: d,
        )
    if post is None:
        post = types.SimpleNamespace(
            group_transactions=lambda d, g: d,
            aggregate_to_ledger=lambda d: d,
        )
    if report is None:
        report = types.SimpleNamespace(export_to_excel=lambda *a, **k: True)
    if audit is None:
        audit = types.SimpleNamespace(log_operation=lambda *a, **k: None)

    monkeypatch.setitem(sys.modules, 'ingest', ingest)
    monkeypatch.setitem(sys.modules, 'post', post)
    monkeypatch.setitem(sys.modules, 'report', report)
    monkeypatch.setitem(sys.modules, 'audit', audit)


def test_main_success(monkeypatch, tmp_path):
    out_path = tmp_path / 'out.xlsx'
    monkeypatch.setattr(sys, 'argv', ['prog', '--input-file', 'in.csv', '--output-file', str(out_path)])
    _install_fake_modules(monkeypatch)
    # Ensure no config file is read during test
    monkeypatch.setattr(Path, 'exists', lambda self: False)

    rc = __import__('main').main()
    assert rc == 0


def test_main_handles_ingest_error(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['prog', '--input-file', 'in.csv'])

    def _raise(_):
        raise RuntimeError('load failed')

    bad_ingest = types.SimpleNamespace(load_csv=_raise)
    _install_fake_modules(monkeypatch, ingest=bad_ingest)

    rc = __import__('main').main()
    assert rc == 1
