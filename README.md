# bpmg-korean-nlp

한국어 NLP 전처리 Python SDK — 정규화·형태소 분석·쿼리 변환.

`retrieval-engine`을 비롯한 다운스트림 시스템의 한국어 처리 어댑터로 사용되는
공통 모듈입니다. BM25/벡터 검색/그래프 순회/랭킹은 담당하지 않으며,
오직 **normalize / tokenize / analyze / query transform**만 수행합니다.

---

## 설치

본 SDK는 PyPI에 등록되어 있지 않습니다. Git URL로 설치합니다.

```bash
pip install "bpmg-korean-nlp @ git+https://github.com/Namkyungyun/nlp-core.git"
```

> **GitLab 전환 예정**: 추후 private GitLab으로 이전 시 URL과 토큰 인증 방식이 변경됩니다.

### MeCab 설치 — 플랫폼별

SDK pip install 명령은 모든 플랫폼에서 동일합니다.
플랫폼별로 다른 점은 **MeCab C 라이브러리와 한국어 사전을 어떻게 공급하느냐**입니다.

| 플랫폼 | MeCab 공급 방식 | 추가 설치 | 가이드 |
|---|---|---|---|
| **macOS** | 시스템 직접 설치 필요 | `brew install mecab mecab-ko mecab-ko-dic` | [INSTALL.MACOS.md](docs/INSTALL.MACOS.md) |
| **Ubuntu 22.04** | `python-mecab-ko` manylinux wheel 내부 번들 | 불필요 | [INSTALL.UBUNTU.md](docs/INSTALL.UBUNTU.md) |
| **Docker** (`python:3.12-slim`) | `python-mecab-ko` manylinux wheel 내부 번들 | 불필요 | [INSTALL.DOCKER.md](docs/INSTALL.DOCKER.md) |

### 선택적 설치

한자→한글 변환 기능(`hanja_to_hangul=True`)이 필요한 경우:

```bash
pip install "bpmg-korean-nlp[hanja] @ git+https://github.com/Namkyungyun/nlp-core.git"
```

### 개발용 설치

이 저장소를 직접 클론한 경우:

```bash
uv pip install -e ".[dev]"
```

사전 가용성 확인:

```python
from bpmg_korean_nlp import check_mecab_dict
result = check_mecab_dict()
print(result.available, result.dict_path)
```

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
lex    = analyzer.analyze("세종대학교 도서관 위치", QueryTarget.LEXICAL)
sem    = analyzer.analyze("세종대학교 도서관 위치", QueryTarget.SEMANTIC)
graph  = analyzer.analyze("세종대학교 도서관 위치", QueryTarget.GRAPH)
hybrid = analyzer.analyze("세종대학교 도서관 위치", QueryTarget.HYBRID)
```

---

## 문서

| 문서 | 설명 |
|---|---|
| [GUIDE.md](GUIDE.md) | 핵심 기능 빠른 시작 (5분 튜토리얼) |
| [docs/GUIDE.TEST.md](docs/GUIDE.TEST.md) | 전체 API 상세 레퍼런스 |
| [SPEC.md](SPEC.md) | 기능 명세·정책 |
| [docs/LOCAL.README.md](docs/LOCAL.README.md) | 로컬 개발 환경 구축 |
| [docs/INSTALL.MACOS.md](docs/INSTALL.MACOS.md) | macOS 설치 가이드 |
| [docs/INSTALL.UBUNTU.md](docs/INSTALL.UBUNTU.md) | Ubuntu 22.04 설치 가이드 |
| [docs/INSTALL.DOCKER.md](docs/INSTALL.DOCKER.md) | Docker 설치 가이드 |

---

## 요구사항

| 항목 | 내용 |
|---|---|
| **Python** | 3.12 이상 |
| **OS** | macOS, Ubuntu 22.04 / Debian, Docker (`python:3.12-slim`) |
| **패키지 매니저** | `pip` / `uv` |
| **빌드 백엔드** | [Hatchling](https://hatch.pypa.io/) (PEP 517) |
| **타입 선언** | PEP 561 (`py.typed` 포함) |

---

## 의존 패키지

### 런타임 의존성

| 패키지 | 역할 | 사용처 |
|---|---|---|
| `python-mecab-ko` | MeCab 한국어 형태소 분석기 Python 바인딩 | `MeCabTokenizer`, `check_mecab_dict` |
| `soynlp` | `repeat_normalize`로 "ㅋㅋㅋㅋ" → "ㅋㅋ" 반복 문자 축약 | `KoreanNormalizer` |
| `regex` | 유니코드 속성 기반 공백 처리 — 전각·특수 공백 패턴 지원 | `KoreanNormalizer` |

### 선택적 의존성

| 패키지 | 역할 | 설치 방법 |
|---|---|---|
| `hanja` | 한자 → 한글 음가 변환 (`大學校` → `대학교`). 기본값 OFF | `pip install "bpmg-korean-nlp[hanja]"` |

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

# 커버리지 포함 테스트 (목표 90%+)
pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=90

# wheel + sdist 빌드
python -m build
```

| 도구 | 버전 | 용도 |
|---|---|---|
| [`ruff`](https://docs.astral.sh/ruff/) | `>= 0.4` | 린트 + 포맷 (E/F/I/N/W/UP/B/SIM/RUF) |
| [`mypy`](https://mypy-lang.org/) | `>= 1.10` | `--strict` 정적 타입 검사 |
| [`pytest`](https://pytest.org/) | `>= 8.0` | 단위·통합·성능·골든셋 테스트 |

---

## 라이선스

[MIT License](LICENSE) © 2026 sejong bpmg-korean-nlp team
