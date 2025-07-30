"""
Unit-tests for evaluator_api.update_ground_truth

They avoid heavy dependencies (deltalake, sempy_labs, Spark, HTTP) by
registering minimal stub modules in ``sys.modules`` **before** the code
under test is imported.
"""

from __future__ import annotations

import sys
import types
import pandas as pd
import pytest
import string


# 1.  Stub external libraries so evaluator_api imports cleanly
def _register_stub(name: str) -> types.ModuleType:
    mod = types.ModuleType(name)
    sys.modules[name] = mod
    return mod


# create parent & sub-modules (deltalake, deltalake.writer, sempy_labs)
for missing in ("deltalake", "deltalake.writer", "sempy_labs"):
    parts = missing.split(".")
    for i in range(1, len(parts) + 1):
        _register_stub(".".join(parts[:i]))

# give the required attribute so `from deltalake.writer import write_deltalake` works
sys.modules["deltalake.writer"].write_deltalake = lambda *_, **__: None

# 2.  Import module under test
from fabric.dataagent.evaluation import evaluator_api
from fabric.dataagent.evaluation.evaluator_api import _extract_placeholders


# 3.  Helpers
def _dummy_sql(df: pd.DataFrame):
    """Mimic labs.ConnectX context manager with a .query() method returning *df*."""

    class _Ctx:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def query(self, _):
            return df

    return _Ctx()


# Patch the evaluator_api module to use our dummy SQL connection
def _patch(monkeypatch, df: pd.DataFrame):
    # force a lakehouse source and dummy connection
    monkeypatch.setattr(
        evaluator_api,
        "_get_source",
        lambda *_: types.SimpleNamespace(connect=lambda: _dummy_sql(df)),
    )


# 4.  Tests
def test_single_scalar_named_placeholder(monkeypatch):
    """Single column, named placeholder is rendered correctly."""
    _patch(monkeypatch, pd.DataFrame({"total": [42]}))

    out = evaluator_api.add_ground_truth(
        question="Total sales?",
        answer_template="Total sales: {total}",
        datasource_id_or_name="Any",
        query="dummy",
        data_agent=None,
    )
    assert out["expected_answer"].iloc[0] == "Total sales: 42"


def test_single_row_multi_column(monkeypatch):
    """Several columns with matching named placeholders."""
    _patch(monkeypatch, pd.DataFrame({"country": ["US"], "sales": [123]}))

    out = evaluator_api.add_ground_truth(
        "By country",
        "{country} sold {sales}",
        "Any",
        "dummy",
        data_agent=None,
    )
    assert out["expected_answer"].iloc[0] == "US sold 123"


def test_error_positional_placeholder(monkeypatch):
    """Positional '{}' is now forbidden."""
    _patch(monkeypatch, pd.DataFrame({"x": [1]}))

    with pytest.raises(ValueError, match="Positional"):
        evaluator_api.add_ground_truth(
            "Bad",
            "Answer is {}",
            "Any",
            "dummy",
            data_agent=None,
        )


def test_error_multiple_rows(monkeypatch):
    """Multiple query rows should raise."""
    _patch(monkeypatch, pd.DataFrame({"id": [1, 2]}))

    with pytest.raises(ValueError, match="multiple rows"):
        evaluator_api.add_ground_truth(
            "Bad",
            "{id}",
            "Any",
            "dummy",
            data_agent=None,
        )

# 5.  _extract_placeholders() edge-cases coverage
@pytest.mark.parametrize(
    "template, expected",
    [
        ("Value is {amount:.2f}", {"amount"}),          # format-spec
        ("Balance {{USD}} {balance}", {"balance"}),     # escaped braces
        ("Repeated {a}-{a}-{b}", {"a", "b"}),           # duplicates collapse
        ("No placeholders here", set()),                # no placeholders
    ],
)
def test_extract_placeholders_edge_cases(template, expected):
    assert evaluator_api._extract_placeholders(template) == expected
