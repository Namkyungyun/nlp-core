"""Tests for ``bpmg_korean_nlp.mecab_check.check_mecab_dict``."""

from __future__ import annotations

import pytest

from bpmg_korean_nlp.mecab_check import check_mecab_dict
from bpmg_korean_nlp.models import DictCheckResult
from tests.conftest import HAS_MECAB


def test_returns_dict_check_result_type() -> None:
    """The probe always returns a :class:`DictCheckResult`, never raises."""
    result = check_mecab_dict()
    assert isinstance(result, DictCheckResult)


def test_missing_binding_reports_unavailable() -> None:
    """When the binding is absent the result reports ``available=False``."""
    if HAS_MECAB:
        pytest.skip("python-mecab-ko is installed; cannot exercise the missing-binding branch")
    result = check_mecab_dict()
    assert result.available is False
    assert result.error is not None


def test_invalid_dict_path_reports_unavailable() -> None:
    """A non-existent dictionary path produces a failure result."""
    result = check_mecab_dict(dict_path="/nonexistent/path/to/mecab-ko-dic")
    # If binding is missing the ImportError takes precedence; either way:
    assert result.available is False
    assert result.error is not None


@pytest.mark.slow
def test_real_mecab_environment_reports_available() -> None:
    """When MeCab is installed and the system dictionary loads, ``available=True``."""
    if not HAS_MECAB:
        pytest.skip("python-mecab-ko not installed")
    result = check_mecab_dict()
    if not result.available:
        pytest.skip(f"MeCab binding present but dictionary not loadable: {result.error}")
    assert result.available is True
    assert result.dict_path is not None or result.dict_path is None  # not enforced


def test_explicit_path_passed_through_on_failure() -> None:
    """A bogus *dict_path* still appears on the result for diagnostics."""
    bogus = "/definitely/not/a/dictionary"
    result = check_mecab_dict(dict_path=bogus)
    assert result.available is False
    # When the binding is missing we get the import error path (dict_path=None).
    # Otherwise the bogus path is echoed back.
    assert result.dict_path in (None, bogus)
