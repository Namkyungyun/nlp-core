# bpmg-korean-nlp

한국어 NLP 전처리 Python SDK — 정규화·형태소 분석·쿼리 변환.

`retrieval-engine`을 비롯한 다운스트림 시스템의 한국어 처리 어댑터로 사용되는
공통 모듈입니다. 본 SDK는 BM25/벡터 검색/그래프 순회/랭킹을 수행하지 않으며,
오직 **normalize / tokenize / analyze / query transform**만 담당합니다.

---

## 설치

```bash
pip install bpmg-korean-nlp
```

`KoreanNormalizer`의 `hanja_to_hangul=True` 옵션을 사용하려면 `hanja` 확장도 함께
설치합니다 (기본값은 OFF이므로 일반 사용자에겐 불필요):

```bash
pip install "bpmg-korean-nlp[hanja]"
```

개발용 설치:

```bash
uv pip install -e ".[dev]"
```

### 시스템 의존성 — MeCab

본 SDK는 `python-mecab-ko`를 통해 MeCab 형태소 분석기에 의존합니다. 플랫폼별
시스템 패키지를 먼저 설치하세요.

**macOS (Homebrew)**

```bash
brew install mecab mecab-ko mecab-ko-dic
```

**Ubuntu 22.04 / Debian**

```bash
sudo apt-get update
sudo apt-get install -y mecab libmecab-dev mecab-ipadic-utf8
# mecab-ko-dic은 별도 빌드 또는 wheel 번들 사전 사용
```

**Docker (Ubuntu 22.04 base)**

```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
        mecab libmecab-dev mecab-ipadic-utf8 build-essential \
    && rm -rf /var/lib/apt/lists/*
RUN pip install bpmg-korean-nlp
```

사전 가용성은 SDK가 부팅 시 `check_mecab_dict()`로 확인할 수 있습니다.

---

## 빠른 시작

```python
from bpmg_korean_nlp import (
    KoreanNormalizer,
    MeCabTokenizer,
    QueryAnalyzer,
    QueryTarget,
)

# 1) 정규화 — NFC, 공백, 반복 문자 축약
normalizer = KoreanNormalizer()
text = normalizer.normalize("안녕하세요ㅋㅋㅋㅋㅋㅋ   세종!!!")

# 2) 형태소 분석 (싱글톤)
tokenizer = MeCabTokenizer()
tokens = tokenizer.tokenize("세종대학교에서 한국어 NLP를 연구한다")
morphs = tokenizer.analyze("세종대학교에서 한국어 NLP를 연구한다")

# 3) 쿼리 변환 — 4-target 파이프라인
analyzer = QueryAnalyzer()
lex = analyzer.analyze("세종대학교 도서관 위치", QueryTarget.LEXICAL)
sem = analyzer.analyze("세종대학교 도서관 위치", QueryTarget.SEMANTIC)
graph = analyzer.analyze("세종대학교 도서관 위치", QueryTarget.GRAPH)
hybrid = analyzer.analyze("세종대학교 도서관 위치", QueryTarget.HYBRID)
```

API 상세 설명은 [`GUIDE.md`](GUIDE.md)를, 기능 명세는 [`SPEC.md`](SPEC.md)를 참조하세요.

---

## 의존 패키지

### 런타임 의존성

| 패키지 | 사용 이유 | 사용처 |
|---|---|---|
| `python-mecab-ko` | MeCab 한국어 형태소 분석기의 Python 바인딩. `mecab-ko-dic` 사전을 통해 세종 품사 태그 기반 형태소 분석을 제공 | `MeCabTokenizer`, `check_mecab_dict` |
| `soynlp` | `repeat_normalize` 함수로 "ㅋㅋㅋㅋㅋ" → "ㅋㅋ" 형태의 반복 문자를 축약. 전처리 파이프라인의 고정 단계로 사용 | `KoreanNormalizer` |
| `regex` | 표준 `re` 모듈과 달리 유니코드 속성 기반 `\s` 매칭을 지원. 전각 공백·특수 공백 문자 등 다양한 유니코드 공백을 단일 패턴으로 처리 | `KoreanNormalizer` |

### 선택적 의존성

| 패키지 | 사용 이유 | 사용처 | 설치 방법 |
|---|---|---|---|
| `hanja` | 한자 문자열을 한글 음가로 변환 (`大學校` → `대학교`). 손실 변환이므로 기본값 OFF | `KoreanNormalizer` | `pip install "bpmg-korean-nlp[hanja]"` |

---

## 개발 환경

```bash
# 의존성 설치
pip install -e ".[dev]"

# 포맷·린트·타입체크·임포트 검사·테스트
ruff format src tests
ruff check src tests --fix
mypy --strict src/ tests/
python scripts/check_imports.py src/
pytest tests/ -v
```

개별 명령:

| 명령 | 설명 |
|---|---|
| `ruff format src tests` | 코드 포맷 |
| `ruff check src tests --fix` | 린트 |
| `mypy --strict src/ tests/` | 타입 검사 |
| `python scripts/check_imports.py src/` | 금지 임포트 정적 검사 |
| `pytest tests/ -v` | 테스트 |
| `pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=90` | 커버리지 검사 |
| `python -m build` | wheel + sdist 빌드 |

---

## 패키지 정책

- Python `>= 3.12`
- src layout (`src/bpmg_korean_nlp/`)
- PEP 561 typed (`py.typed` 포함)
- 모든 public API: type hint·docstring·`mypy --strict` 통과
- 데이터 모델은 `@dataclass(frozen=True, slots=True)`
- 싱글톤: `MeCabTokenizer` (사전 로딩 비용)

### 금지 사항

- import 금지: `retrieval-core`, `guardrail-core`, `chatbot-contracts`
- 구현 금지: BM25/벡터/그래프 순회/랭킹/PII 런타임 마스킹/KoNLPy 기반 토크나이저

상기 정책은 CI에서 `scripts/check_imports.py`로 차단합니다.

---

## 라이선스

[MIT License](LICENSE) © 2026 sejong bpmg-korean-nlp team
