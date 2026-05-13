"""Tests for ``bpmg_korean_nlp.spacing.SpacingRestorer``.

Heavy tests that exercise the actual PyKoSpacing model are guarded by the
``real_spacing`` fixture, which skips when the model is unavailable. The
DI-based pipeline tests in :mod:`test_query_analyzer` already cover the
plumbing without the model.
"""

from __future__ import annotations

import pytest

from bpmg_korean_nlp.exceptions import InvalidInputError, SpacingModelLoadError
from bpmg_korean_nlp.spacing import SpacingRestorer
from tests.conftest import HAS_PYKOSPACING


def test_singleton_returns_same_instance() -> None:
    """Repeated ``get_instance()`` calls return the cached object."""
    if not HAS_PYKOSPACING:
        pytest.skip("PyKoSpacing not installed")
    a = SpacingRestorer.get_instance()
    b = SpacingRestorer.get_instance()
    assert a is b


def test_missing_dep_raises_spacing_model_load_error() -> None:
    """Constructing without PyKoSpacing installed surfaces a typed error."""
    if HAS_PYKOSPACING:
        pytest.skip("PyKoSpacing is installed; cannot exercise missing-dep branch")
    with pytest.raises(SpacingModelLoadError):
        SpacingRestorer()


@pytest.mark.slow
def test_restore_empty_returns_empty() -> None:
    """The empty string flows through without invoking the model."""
    if not HAS_PYKOSPACING:
        pytest.skip("PyKoSpacing not installed")
    restorer = SpacingRestorer.get_instance()
    assert restorer.restore("") == ""


def test_restore_rejects_none() -> None:
    """``None`` input is rejected without loading the model."""
    if not HAS_PYKOSPACING:
        pytest.skip("PyKoSpacing not installed")
    restorer = SpacingRestorer.get_instance()
    with pytest.raises(InvalidInputError):
        restorer.restore(None)  # type: ignore[arg-type]


def test_restore_rejects_non_str() -> None:
    if not HAS_PYKOSPACING:
        pytest.skip("PyKoSpacing not installed")
    restorer = SpacingRestorer.get_instance()
    with pytest.raises(InvalidInputError):
        restorer.restore(123)  # type: ignore[arg-type]


@pytest.mark.slow
def test_restore_returns_string(real_spacing: SpacingRestorer) -> None:
    """A representative messy input returns a non-empty string."""
    out = real_spacing.restore("조사랑어미차이가뭐예요")
    assert isinstance(out, str)
    assert len(out) > 0


@pytest.mark.slow
def test_restore_preserves_well_spaced(real_spacing: SpacingRestorer) -> None:
    """Already-spaced text is not destructively reformatted."""
    out = real_spacing.restore("한국어 띄어쓰기 처리 모듈")
    assert "한국어" in out
    assert "띄어쓰기" in out
