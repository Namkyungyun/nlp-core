# README.LOCAL.md

로컬 개발 환경 설정 및 테스트 실행 가이드.

---

## 환경 요구사항

| 항목 | 요구사항 |
|---|---|
| Python | 3.12 이상 |
| MeCab 바이너리 | `mecab-ko` (일반 `mecab`과 충돌 — 교체 필요) |
| MeCab 한국어 사전 | `mecab-ko-dic` |
| Python MeCab 바인딩 | `python-mecab-ko` (pip으로 설치) |

---

## 1단계 — Python 3.12 설치

```bash
pyenv install 3.12
```

---

## 2단계 — MeCab 교체 (mecab → mecab-ko)

기존 `mecab`이 설치되어 있다면 먼저 제거 후 한국어 특화 버전으로 교체한다.

```bash
brew uninstall mecab
brew install mecab-ko mecab-ko-dic
```

---

## 3단계 — 가상환경 생성 및 패키지 설치

```bash
cd ~/Desktop/Workspace/sejong/bpmg-korean-nlp
pyenv local 3.12
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

---

## 4단계 — 동작 확인

```bash
python -c "import bpmg_korean_nlp; print(len(bpmg_korean_nlp.__all__)); print(bpmg_korean_nlp.__all__)"
```

31이 출력되면 정상.

---

## 5단계 — 테스트 실행

```bash
# 전체 테스트
pytest tests/ -v

# 커버리지 포함
pytest tests/ --cov=src --cov-report=term-missing

# 특정 모듈만
pytest tests/test_normalizer.py -v
pytest tests/test_tokenizer.py -v
pytest tests/test_jamo_utils.py -v
```

---

## 빠른 기능 테스트

```python
from bpmg_korean_nlp import KoreanNormalizer, MeCabTokenizer, QueryAnalyzer, QueryTarget

# 정규화
norm = KoreanNormalizer.default()
print(norm.normalize("안녕하세요ㅋㅋㅋㅋ   세종!!!"))
# → "안녕하세요ㅋㅋ 세종!!!"

# 형태소 분석
tok = MeCabTokenizer()
print(tok.tokenize("세종대학교에서 한국어 NLP를 연구한다"))
# → ['세종대학교', '에서', '한국어', 'NLP', '를', '연구', '한다']

# 쿼리 변환
qa = QueryAnalyzer()
print(qa.analyze("조사랑 어미 차이가 뭐예요", QueryTarget.LEXICAL))
# → LexicalQueryResult(keywords=('조사', '어미', '차이'), query='조사 어미 차이')
```

---

## 개발 명령

```bash
ruff format src tests                                                              # 코드 포맷
ruff check src tests --fix                                                         # 린트
mypy --strict src/ tests/                                                          # 타입 검사
python scripts/check_imports.py src/                                               # 금지 import 검사
pytest tests/ -v                                                                   # 테스트 실행
pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=90             # 커버리지 포함 테스트
python -m build                                                                    # wheel + sdist 빌드
rm -rf dist/ build/ .coverage htmlcov/ .mypy_cache/ .ruff_cache/ .pytest_cache/   # 빌드/캐시 정리
```
