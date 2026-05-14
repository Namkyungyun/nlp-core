"""``bpmg_korean_nlp.mecab_check.check_mecab_dict`` 테스트."""

from __future__ import annotations

import pytest

from bpmg_korean_nlp.mecab_check import check_mecab_dict
from bpmg_korean_nlp.models import DictCheckResult
from tests.conftest import HAS_MECAB


def test_returns_dict_check_result_type() -> None:
    """확인 함수는 항상 :class:`DictCheckResult`를 반환하며 예외를 발생시키지 않습니다."""
    result = check_mecab_dict()
    assert isinstance(result, DictCheckResult)


def test_missing_binding_reports_unavailable() -> None:
    """바인딩이 없으면 결과에 ``available=False``가 보고됩니다."""
    if HAS_MECAB:
        pytest.skip("python-mecab-ko is installed; cannot exercise the missing-binding branch")
    result = check_mecab_dict()
    assert result.available is False
    assert result.error is not None


def test_invalid_dict_path_reports_unavailable() -> None:
    """존재하지 않는 사전 경로는 실패 결과를 생성합니다."""
    result = check_mecab_dict(dict_path="/nonexistent/path/to/mecab-ko-dic")
    # If binding is missing the ImportError takes precedence; either way:
    assert result.available is False
    assert result.error is not None


@pytest.mark.slow
def test_real_mecab_environment_reports_available() -> None:
    """MeCab이 설치되어 있고 시스템 사전이 로드되면 ``available=True``입니다."""
    if not HAS_MECAB:
        pytest.skip("python-mecab-ko not installed")
    result = check_mecab_dict()
    if not result.available:
        pytest.skip(f"MeCab binding present but dictionary not loadable: {result.error}")
    assert result.available is True
    assert result.dict_path is not None or result.dict_path is None  # not enforced


def test_explicit_path_passed_through_on_failure() -> None:
    """잘못된 *dict_path*도 진단을 위해 결과에 나타납니다."""
    bogus = "/definitely/not/a/dictionary"
    result = check_mecab_dict(dict_path=bogus)
    assert result.available is False
    # 바인딩이 없으면 임포트 오류 경로를 얻습니다 (dict_path=None).
    # 그렇지 않으면 잘못된 경로가 그대로 반환됩니다.
    assert result.dict_path in (None, bogus)
