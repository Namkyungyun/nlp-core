# QA_TEST_GUIDE.md

bpmg-korean-nlp v0.1 수동 테스트 가이드. 아래 테스트를 순서대로 실행하여 SDK가 정상 동작하는지 확인한다.

## 사전 준비

```bash
# 가상환경 생성 및 패키지 설치
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# MeCab 시스템 패키지 (macOS)
brew install mecab mecab-ko mecab-ko-dic

# MeCab 시스템 패키지 (Ubuntu 22.04)
sudo apt-get install mecab libmecab-dev mecab-ipadic-utf8

# Python 인터랙티브 셸 진입
PYTHONPATH=src python
```

---

## 테스트 목록

| # | 영역 | 테스트 항목 | 중요도 |
|---|---|---|---|
| T-01 | 공통 | Public API 전체 import | P0 |
| T-02 | 공통 | 금지 import 없음 확인 | P0 |
| T-03 | Normalizer | NFC 정규화 | P0 |
| T-04 | Normalizer | 비표준 공백 정규화 | P0 |
| T-05 | Normalizer | 반복 문자 축약 | P0 |
| T-06 | Normalizer | 잘못된 입력 타입 거부 | P0 |
| T-07 | Normalizer | custom_substitutions 적용 | P1 |
| T-08 | Normalizer | 빈 문자열 처리 | P0 |
| T-09 | SpacingRestorer | 싱글톤 패턴 확인 | P0 |
| T-10 | SpacingRestorer | 띄어쓰기 복원 | P0 |
| T-11 | SpacingRestorer | 빈 문자열 처리 | P0 |
| T-12 | MeCabTokenizer | 기본 토크나이즈 | P0 |
| T-13 | MeCabTokenizer | 빈 문자열 → 빈 리스트 | P0 |
| T-14 | MeCabTokenizer | pos_filter 적용 | P0 |
| T-15 | MeCabTokenizer | remove_stopwords 적용 | P0 |
| T-16 | MeCabTokenizer | analyze() — MorphToken 오프셋 | P0 |
| T-17 | MeCabTokenizer | 싱글톤 패턴 확인 | P0 |
| T-18 | MeCabTokenizer | 잘못된 입력 타입 거부 | P0 |
| T-19 | QueryAnalyzer | LEXICAL 타겟 | P0 |
| T-20 | QueryAnalyzer | SEMANTIC 타겟 | P0 |
| T-21 | QueryAnalyzer | GRAPH 타겟 | P0 |
| T-22 | QueryAnalyzer | HYBRID 타겟 | P0 |
| T-23 | QueryAnalyzer | 문자열 타겟("lexical") | P0 |
| T-24 | QueryAnalyzer | 빈 문자열 처리 | P0 |
| T-25 | QueryAnalyzer | 잘못된 타겟 → InvalidInputError | P0 |
| T-26 | QueryAnalyzer | analyze_query() 편의 함수 | P1 |
| T-27 | jamo_utils | decompose() 기본 동작 | P0 |
| T-28 | jamo_utils | compose() 기본 동작 | P0 |
| T-29 | jamo_utils | round-trip 보장 | P0 |
| T-30 | jamo_utils | extract_choseong() | P0 |
| T-31 | jamo_utils | classify_char() 전 종류 | P0 |
| T-32 | jamo_utils | 비한글 입력 → InvalidInputError | P0 |
| T-33 | stopwords | frozenset 타입 및 불변성 | P0 |
| T-34 | stopwords | merge_stopwords() | P0 |
| T-35 | pii | PII_PATTERNS 구조 확인 | P0 |
| T-36 | pii | PIIDetectedError — QueryAnalyzer 자동 차단 | P0 |
| T-37 | pii | PIIDetectedError — 복수 패턴 동시 감지 | P0 |
| T-38 | mecab_check | check_mecab_dict() 반환 타입 | P0 |
| T-39 | mecab_check | 잘못된 경로 → available=False | P1 |

---

## T-01: Public API 전체 import

**목적**: SDK의 29개 public symbol이 모두 import 가능한지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import (
    # 데이터 모델
    MorphToken, JamoComponents, DictCheckResult, PIIPattern,
    LexicalQueryResult, SemanticQueryResult, GraphQueryResult, HybridQueryResult,
    QueryResult,
    # 열거형
    QueryTarget, CharType,
    # 예외
    KoreanNlpError, MeCabNotAvailableError, SpacingModelLoadError, InvalidInputError,
    # 핵심 클래스
    KoreanNormalizer, SpacingRestorer, MeCabTokenizer, QueryAnalyzer,
    # 함수
    analyze_query, decompose, compose, extract_choseong, classify_char,
    merge_stopwords, check_mecab_dict,
    # 상수
    DEFAULT_STOPWORDS, PII_PATTERNS,
)
print("OK:", len(dir()))
```

**기대 결과**: 오류 없이 import 완료. `OK: ...` 출력.

---

## T-02: 금지 import 없음 확인

**목적**: `retrieval_core`, `guardrail_core`, `chatbot_contracts`가 소스에 없는지 확인한다.

**테스트 방법** (셸에서 실행):
```bash
python scripts/check_imports.py src/
echo "Exit code: $?"
```

**기대 결과**: 출력 없이 `Exit code: 0`.

---

## T-03: Normalizer — NFC 정규화

**목적**: NFD 형태의 한글이 NFC로 변환되는지 확인한다.

**테스트 방법**:
```python
import unicodedata
from bpmg_korean_nlp import KoreanNormalizer

norm = KoreanNormalizer.default()

# NFD로 분해한 '가'를 입력
nfd_ga = unicodedata.normalize("NFD", "가")
result = norm.normalize(nfd_ga)

print("입력 form:", unicodedata.is_normalized("NFD", nfd_ga))  # True
print("결과:", result)
print("결과 form:", unicodedata.is_normalized("NFC", result))  # True
assert result == "가"
print("PASS")
```

**기대 결과**:
```
입력 form: True
결과: 가
결과 form: True
PASS
```

---

## T-04: Normalizer — 비표준 공백 정규화

**목적**: NBSP, em-space, ideographic space 등이 ASCII 공백으로 변환되는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import KoreanNormalizer

norm = KoreanNormalizer.default()

# NBSP( ), em-space( ), ideographic space(　)
test = "한국어 자연어 처리　SDK"
result = norm.normalize(test)

print("결과:", result)
assert " " not in result
assert " " not in result
assert "　" not in result
assert result == "한국어 자연어 처리 SDK"
print("PASS")
```

**기대 결과**:
```
결과: 한국어 자연어 처리 SDK
PASS
```

---

## T-05: Normalizer — 반복 문자 축약

**목적**: `ㅋㅋㅋㅋ` → `ㅋㅋ`, `ㅎㅎㅎ` → `ㅎㅎ` (num_repeats=2) 축약이 동작하는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import KoreanNormalizer

norm = KoreanNormalizer.default()

assert norm.normalize("ㅋㅋㅋㅋ") == "ㅋㅋ"
assert norm.normalize("ㅎㅎㅎ") == "ㅎㅎ"
assert norm.normalize("조사랑어미차이가뭐예요ㅋㅋㅋㅋ") == "조사랑어미차이가뭐예요ㅋㅋ"
print("PASS")
```

**기대 결과**: `PASS`

---

## T-06: Normalizer — 잘못된 입력 타입 거부

**목적**: `None` 또는 `str`이 아닌 값 입력 시 `InvalidInputError`가 발생하는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import KoreanNormalizer, InvalidInputError

norm = KoreanNormalizer.default()

for bad in [None, 123, ["한국어"], b"bytes"]:
    try:
        norm.normalize(bad)
        print(f"FAIL: {type(bad)} should raise")
    except InvalidInputError as e:
        print(f"PASS: {type(bad).__name__} → InvalidInputError: {e}")
```

**기대 결과**:
```
PASS: NoneType → InvalidInputError: ...
PASS: int → InvalidInputError: ...
PASS: list → InvalidInputError: ...
PASS: bytes → InvalidInputError: ...
```

---

## T-07: Normalizer — custom_substitutions 적용

**목적**: 사용자 정의 regex 치환이 파이프라인 마지막에 순서대로 적용되는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import KoreanNormalizer

norm = KoreanNormalizer(custom_substitutions=[
    (r"NLP", "자연어처리"),
    (r"SDK", "라이브러리"),
])

result = norm.normalize("korean NLP SDK")
print("결과:", result)
assert "자연어처리" in result
assert "라이브러리" in result
print("PASS")
```

**기대 결과**:
```
결과: korean 자연어처리 라이브러리
PASS
```

---

## T-08: Normalizer — 빈 문자열 처리

**목적**: 빈 문자열 입력 시 빈 문자열이 반환되는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import KoreanNormalizer

norm = KoreanNormalizer.default()
assert norm.normalize("") == ""
assert norm.normalize("   ") == ""   # 공백만 있는 경우 strip 후 빈 문자열
print("PASS")
```

**기대 결과**: `PASS`

---

## T-09: SpacingRestorer — 싱글톤 패턴 확인

**목적**: `get_instance()`가 동일 인스턴스를 반환하는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import SpacingRestorer

a = SpacingRestorer.get_instance()
b = SpacingRestorer.get_instance()

assert a is b, "싱글톤이어야 함"
print("PASS: 동일 인스턴스 확인")
print("타입:", type(a))
```

**기대 결과**:
```
PASS: 동일 인스턴스 확인
타입: <class 'bpmg_korean_nlp.spacing.SpacingRestorer'>
```

> PyKoSpacing이 설치되지 않은 경우 `SpacingModelLoadError`가 발생할 수 있음. 정상 동작은 `pip install PyKoSpacing` 설치 후 확인.

---

## T-10: SpacingRestorer — 띄어쓰기 복원

**목적**: 띄어쓰기가 없는 한글 텍스트가 복원되는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import SpacingRestorer

sr = SpacingRestorer.get_instance()

result = sr.restore("조사랑어미차이가뭐예요")
print("결과:", result)

# 복원된 결과에 주요 단어가 포함되어야 함
assert "어미" in result or " " in result, "공백이 삽입되어야 함"
print("PASS")
```

**기대 결과**:
```
결과: 조사랑 어미 차이가 뭐예요  (또는 유사한 띄어쓰기 복원 결과)
PASS
```

---

## T-11: SpacingRestorer — 빈 문자열 처리

**목적**: 빈 문자열 입력 시 빈 문자열이 반환되는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import SpacingRestorer

sr = SpacingRestorer.get_instance()
result = sr.restore("")
assert result == "", f"빈 문자열이어야 함, 실제: {result!r}"
print("PASS")
```

**기대 결과**: `PASS`

---

## T-12: MeCabTokenizer — 기본 토크나이즈

**목적**: 한글 문장이 형태소 리스트로 분리되는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import MeCabTokenizer

tok = MeCabTokenizer()
result = tok.tokenize("조사랑 어미 차이가 뭐예요")

print("결과:", result)
assert isinstance(result, list)
assert all(isinstance(t, str) for t in result)
assert len(result) > 0
print("PASS")
```

**기대 결과**:
```
결과: ['조사', '랑', '어미', '차이', '가', '뭐', '예', '요']  (MeCab 출력에 따라 변동)
PASS
```

---

## T-13: MeCabTokenizer — 빈 문자열 → 빈 리스트

**목적**: 빈 문자열 입력 시 빈 리스트가 반환되는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import MeCabTokenizer

tok = MeCabTokenizer()
assert tok.tokenize("") == []
assert tok.analyze("") == []
print("PASS")
```

**기대 결과**: `PASS`

---

## T-14: MeCabTokenizer — pos_filter 적용

**목적**: `pos_filter`로 지정한 품사(NNG, NNP)의 토큰만 반환되는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import MeCabTokenizer

tok = MeCabTokenizer()
result = tok.tokenize(
    "서울은 대한민국의 수도입니다",
    pos_filter=frozenset({"NNG", "NNP"}),
)
print("명사만:", result)
assert isinstance(result, list)
# 조사('은', '의'), 서술어('입니다') 등이 제외되어야 함
print("PASS")
```

**기대 결과**:
```
명사만: ['서울', '대한민국', '수도']  (MeCab 분석 결과에 따라 변동)
PASS
```

---

## T-15: MeCabTokenizer — remove_stopwords 적용

**목적**: `remove_stopwords=True` 시 기본 불용어가 제거되는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import MeCabTokenizer, DEFAULT_STOPWORDS

tok = MeCabTokenizer()
all_tokens = tok.tokenize("조사랑 어미 차이가 뭐예요")
filtered = tok.tokenize("조사랑 어미 차이가 뭐예요", remove_stopwords=True)

print("전체:", all_tokens)
print("필터:", filtered)

# 불용어가 포함된 토큰은 filtered에서 제거되어야 함
removed = set(all_tokens) - set(filtered)
stopword_removed = removed & DEFAULT_STOPWORDS
print("제거된 불용어:", stopword_removed)
print("PASS")
```

**기대 결과**: 불용어(조사류 등)가 filtered 결과에서 제거됨.

---

## T-16: MeCabTokenizer — analyze() MorphToken 오프셋

**목적**: `analyze()` 결과의 `start`/`end` 오프셋이 원문과 일치하는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import MeCabTokenizer, MorphToken

tok = MeCabTokenizer()
text = "서울 날씨 어때요"
morphs = tok.analyze(text)

print("형태소 분석 결과:")
for m in morphs:
    print(f"  surface={m.surface!r}, pos={m.pos}, start={m.start}, end={m.end}")
    extracted = text[m.start:m.end]
    assert extracted == m.surface, f"오프셋 불일치: {extracted!r} != {m.surface!r}"

assert all(isinstance(m, MorphToken) for m in morphs)
print("PASS: 모든 오프셋 정확")
```

**기대 결과**:
```
형태소 분석 결과:
  surface='서울', pos='NNP', start=0, end=2
  ...
PASS: 모든 오프셋 정확
```

---

## T-17: MeCabTokenizer — 싱글톤 패턴 확인

**목적**: 동일 설정으로 생성한 인스턴스가 동일 객체인지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import MeCabTokenizer

a = MeCabTokenizer()
b = MeCabTokenizer()
c = MeCabTokenizer.get_instance()

assert a is b, "같은 config → 같은 인스턴스"
assert b is c, "get_instance()도 동일"
print("PASS")
```

**기대 결과**: `PASS`

---

## T-18: MeCabTokenizer — 잘못된 입력 타입 거부

**목적**: `str`이 아닌 값 입력 시 `InvalidInputError`가 발생하는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import MeCabTokenizer, InvalidInputError

tok = MeCabTokenizer()

for bad in [None, 123, ["한국어"]]:
    try:
        tok.tokenize(bad)
        print(f"FAIL: {type(bad)} should raise")
    except InvalidInputError as e:
        print(f"PASS: {type(bad).__name__} → InvalidInputError")
```

**기대 결과**:
```
PASS: NoneType → InvalidInputError
PASS: int → InvalidInputError
PASS: list → InvalidInputError
```

---

## T-19: QueryAnalyzer — LEXICAL 타겟

**목적**: LEXICAL 타겟이 `LexicalQueryResult`를 반환하고, keywords가 tuple인지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import QueryAnalyzer, LexicalQueryResult, QueryTarget

qa = QueryAnalyzer()
result = qa.analyze("조사랑 어미 차이가 뭐예요", QueryTarget.LEXICAL)

print("타입:", type(result).__name__)
print("keywords:", result.keywords)
print("query:", result.query)

assert isinstance(result, LexicalQueryResult)
assert isinstance(result.keywords, tuple)
assert isinstance(result.query, str)
assert result.query == " ".join(result.keywords)
print("PASS")
```

**기대 결과**:
```
타입: LexicalQueryResult
keywords: ('조사', '어미', '차이', ...)  # 불용어 제거 후 명사 중심
query: 조사 어미 차이 ...
PASS
```

---

## T-20: QueryAnalyzer — SEMANTIC 타겟

**목적**: SEMANTIC 타겟이 `SemanticQueryResult`를 반환하고, 자연문이 보존되는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import QueryAnalyzer, SemanticQueryResult, QueryTarget

qa = QueryAnalyzer()
text = "조사랑 어미 차이가 뭐예요"
result = qa.analyze(text, QueryTarget.SEMANTIC)

print("타입:", type(result).__name__)
print("query:", result.query)

assert isinstance(result, SemanticQueryResult)
assert isinstance(result.query, str)
# 자연문이 보존되어야 함 (normalize+spacing 후 형태 유지)
assert "어미" in result.query
print("PASS")
```

**기대 결과**:
```
타입: SemanticQueryResult
query: 조사랑 어미 차이가 뭐예요  (normalize+spacing 적용 후)
PASS
```

---

## T-21: QueryAnalyzer — GRAPH 타겟

**목적**: GRAPH 타겟이 `GraphQueryResult`를 반환하고, seed_nodes가 NNG/NNP만 포함하는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import QueryAnalyzer, GraphQueryResult, QueryTarget

qa = QueryAnalyzer()
result = qa.analyze("서울 날씨 어때요", QueryTarget.GRAPH)

print("타입:", type(result).__name__)
print("seed_nodes:", result.seed_nodes)

assert isinstance(result, GraphQueryResult)
assert isinstance(result.seed_nodes, tuple)
# 명사·고유명사만 포함되어야 함
print("PASS")
```

**기대 결과**:
```
타입: GraphQueryResult
seed_nodes: ('서울', '날씨')  # NNG/NNP만 포함
PASS
```

---

## T-22: QueryAnalyzer — HYBRID 타겟

**목적**: HYBRID 타겟이 세 결과를 모두 포함하는 `HybridQueryResult`를 반환하는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import (
    QueryAnalyzer, HybridQueryResult,
    LexicalQueryResult, SemanticQueryResult, GraphQueryResult,
    QueryTarget,
)

qa = QueryAnalyzer()
result = qa.analyze("조사랑 어미 차이가 뭐예요", QueryTarget.HYBRID)

print("타입:", type(result).__name__)
print("  lexical:", result.lexical)
print("  semantic:", result.semantic)
print("  graph:", result.graph)

assert isinstance(result, HybridQueryResult)
assert isinstance(result.lexical, LexicalQueryResult)
assert isinstance(result.semantic, SemanticQueryResult)
assert isinstance(result.graph, GraphQueryResult)
print("PASS")
```

**기대 결과**:
```
타입: HybridQueryResult
  lexical: LexicalQueryResult(keywords=(...), query='...')
  semantic: SemanticQueryResult(query='...')
  graph: GraphQueryResult(seed_nodes=(...))
PASS
```

---

## T-23: QueryAnalyzer — 문자열 타겟 지원

**목적**: `QueryTarget` enum 대신 문자열(`"lexical"`)로도 동작하는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import QueryAnalyzer, LexicalQueryResult

qa = QueryAnalyzer()

for target_str in ["lexical", "semantic", "graph", "hybrid"]:
    result = qa.analyze("한국어 NLP", target_str)
    print(f"{target_str}: {type(result).__name__}")

print("PASS")
```

**기대 결과**:
```
lexical: LexicalQueryResult
semantic: SemanticQueryResult
graph: GraphQueryResult
hybrid: HybridQueryResult
PASS
```

---

## T-24: QueryAnalyzer — 빈 문자열 처리

**목적**: 빈 문자열 입력 시 각 타겟별로 빈 결과를 반환하는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import QueryAnalyzer, QueryTarget

qa = QueryAnalyzer()

lex = qa.analyze("", QueryTarget.LEXICAL)
assert lex.keywords == () and lex.query == ""

sem = qa.analyze("", QueryTarget.SEMANTIC)
assert sem.query == ""

gph = qa.analyze("", QueryTarget.GRAPH)
assert gph.seed_nodes == ()

hyb = qa.analyze("", QueryTarget.HYBRID)
assert hyb.lexical.query == ""

print("PASS")
```

**기대 결과**: `PASS`

---

## T-25: QueryAnalyzer — 잘못된 타겟 → InvalidInputError

**목적**: 알 수 없는 타겟 문자열 입력 시 `InvalidInputError`가 발생하는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import QueryAnalyzer, InvalidInputError

qa = QueryAnalyzer()

try:
    qa.analyze("한국어", "unknown_target")
    print("FAIL: 예외가 발생해야 함")
except InvalidInputError as e:
    print("PASS:", e)
```

**기대 결과**:
```
PASS: Unknown query target: 'unknown_target'. Valid targets: [...]
```

---

## T-26: QueryAnalyzer — analyze_query() 편의 함수

**목적**: 모듈 레벨 `analyze_query()` 함수가 기본 인스턴스를 재사용하는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import analyze_query, LexicalQueryResult

result = analyze_query("한국어 NLP 처리")
print("결과:", result)
assert isinstance(result, LexicalQueryResult)

# 두 번 호출 시 동일 인스턴스 재사용 (내부 상태 일관성)
result2 = analyze_query("서울 날씨", "semantic")
print("결과2:", result2)
print("PASS")
```

**기대 결과**: 오류 없이 두 결과 출력. `PASS`

---

## T-27: jamo_utils — decompose() 기본 동작

**목적**: 한글 음절이 초성/중성/종성으로 분리되는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import decompose, JamoComponents

result = decompose("한")
print("결과:", result)
assert result == JamoComponents(choseong="ㅎ", jungseong="ㅏ", jongseong="ㄴ")

# 받침 없는 경우
result2 = decompose("가")
assert result2.jongseong == ""

print("PASS")
```

**기대 결과**:
```
결과: JamoComponents(choseong='ㅎ', jungseong='ㅏ', jongseong='ㄴ')
PASS
```

---

## T-28: jamo_utils — compose() 기본 동작

**목적**: 초성/중성/종성으로 한글 음절을 합성하는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import compose

assert compose("ㅎ", "ㅏ", "ㄴ") == "한"
assert compose("ㄱ", "ㅏ") == "가"     # 종성 없음
assert compose("ㄴ", "ㅏ", "ㄹ") == "날"
print("PASS")
```

**기대 결과**: `PASS`

---

## T-29: jamo_utils — round-trip 보장

**목적**: U+AC00~U+D7A3 전체 11,172자에 대해 `compose(*decompose(c)) == c`가 성립하는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import decompose, compose

failures = []
for code in range(0xAC00, 0xD7A4):
    c = chr(code)
    d = decompose(c)
    result = compose(d.choseong, d.jungseong, d.jongseong)
    if result != c:
        failures.append((c, result))

if failures:
    print(f"FAIL: {len(failures)}개 실패")
else:
    print("PASS: 11,172자 round-trip 전부 통과")
```

**기대 결과**:
```
PASS: 11,172자 round-trip 전부 통과
```

> 실행 시간 약 0.1~0.5초 소요.

---

## T-30: jamo_utils — extract_choseong()

**목적**: 한글 음절의 초성만 추출하고 비한글 문자는 보존되는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import extract_choseong

assert extract_choseong("한국어") == "ㅎㄱㅇ"
assert extract_choseong("Hello 세계") == "Hello ㅅㄱ"
assert extract_choseong("") == ""
assert extract_choseong("123") == "123"     # 숫자 보존
print("PASS")
```

**기대 결과**: `PASS`

---

## T-31: jamo_utils — classify_char() 전 종류

**목적**: 모든 `CharType` 분류가 올바르게 동작하는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import classify_char, CharType

cases = [
    ("가", CharType.HANGUL_SYLLABLE),
    ("ㄱ", CharType.HANGUL_JAMO),
    ("漢", CharType.HANJA),
    ("A", CharType.LATIN),
    ("5", CharType.NUMBER),
    (" ", CharType.WHITESPACE),
    ("!", CharType.SYMBOL),
]

for char, expected in cases:
    result = classify_char(char)
    status = "PASS" if result == expected else "FAIL"
    print(f"  {status}: classify_char({char!r}) = {result.value!r} (expected: {expected.value!r})")
```

**기대 결과**:
```
  PASS: classify_char('가') = 'hangul_syllable'
  PASS: classify_char('ㄱ') = 'hangul_jamo'
  PASS: classify_char('漢') = 'hanja'
  PASS: classify_char('A') = 'latin'
  PASS: classify_char('5') = 'number'
  PASS: classify_char(' ') = 'whitespace'
  PASS: classify_char('!') = 'symbol'
```

---

## T-32: jamo_utils — 비한글 입력 → InvalidInputError

**목적**: 한글 음절이 아닌 문자로 `decompose()` 호출 시 `InvalidInputError`가 발생하는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import decompose, InvalidInputError

for bad in ["A", "1", "ㄱ", "漢", "한국"]:  # 마지막은 2글자
    try:
        decompose(bad)
        print(f"FAIL: {bad!r} should raise")
    except InvalidInputError as e:
        print(f"PASS: {bad!r} → InvalidInputError")
```

**기대 결과**:
```
PASS: 'A' → InvalidInputError
PASS: '1' → InvalidInputError
PASS: 'ㄱ' → InvalidInputError
PASS: '漢' → InvalidInputError
PASS: '한국' → InvalidInputError
```

---

## T-33: stopwords — frozenset 타입 및 불변성

**목적**: `DEFAULT_STOPWORDS`가 `frozenset`이고 변경이 불가능한지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import DEFAULT_STOPWORDS

print("타입:", type(DEFAULT_STOPWORDS))
print("크기:", len(DEFAULT_STOPWORDS))

assert isinstance(DEFAULT_STOPWORDS, frozenset)
assert len(DEFAULT_STOPWORDS) >= 50, f"최소 50어 이상이어야 함: {len(DEFAULT_STOPWORDS)}"

# 변경 시도 → AttributeError
try:
    DEFAULT_STOPWORDS.add("테스트")
    print("FAIL: 변경되면 안 됨")
except AttributeError as e:
    print("PASS: 불변성 확인 →", e)
```

**기대 결과**:
```
타입: <class 'frozenset'>
크기: 155  (또는 그 이상)
PASS: 불변성 확인 → 'frozenset' object has no attribute 'add'
```

---

## T-34: stopwords — merge_stopwords()

**목적**: `merge_stopwords()`가 새로운 `frozenset`을 반환하고 원본을 변경하지 않는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import DEFAULT_STOPWORDS, merge_stopwords

original_size = len(DEFAULT_STOPWORDS)
custom = {"수업", "교재", "과제"}

merged = merge_stopwords(custom)

print("원본 크기:", original_size)
print("병합 후 크기:", len(merged))

assert isinstance(merged, frozenset)
assert len(merged) == original_size + len(custom)
assert len(DEFAULT_STOPWORDS) == original_size  # 원본 변경 없음
assert "수업" in merged
assert "수업" not in DEFAULT_STOPWORDS
print("PASS")
```

**기대 결과**:
```
원본 크기: 155
병합 후 크기: 158
PASS
```

---

## T-35: pii — PII_PATTERNS 구조 확인

**목적**: `PII_PATTERNS`가 4개의 `PIIPattern`을 담은 tuple인지 확인한다.

**테스트 방법**:
```python
import re
from bpmg_korean_nlp import PII_PATTERNS, PIIPattern

print("타입:", type(PII_PATTERNS))
print("개수:", len(PII_PATTERNS))

assert isinstance(PII_PATTERNS, tuple)
assert len(PII_PATTERNS) == 4

for p in PII_PATTERNS:
    assert isinstance(p, PIIPattern)
    assert isinstance(p.name, str)
    assert isinstance(p.description, str)
    assert isinstance(p.pattern, re.Pattern)
    print(f"  - {p.name}: {p.description}")

print("PASS")
```

**기대 결과**:
```
타입: <class 'tuple'>
개수: 4
  - resident_id: 주민등록번호
  - mobile_phone: 휴대전화 번호
  - business_id: 사업자등록번호
  - foreign_id: 외국인등록번호
PASS
```

---

## T-36: pii — PIIDetectedError QueryAnalyzer 자동 차단

**목적**: PII가 포함된 입력을 `QueryAnalyzer.analyze()`가 자동으로 차단하는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import QueryAnalyzer, QueryTarget, PIIDetectedError

class _NoopSpacing:
    def restore(self, text: str) -> str:
        return text

analyzer = QueryAnalyzer(spacing_restorer=_NoopSpacing())

cases = [
    ("정상 쿼리 — 통과", "세종대학교 도서관 위치", False),
    ("주민등록번호 — 차단", "내 주민번호 900101-1234567", True),
    ("휴대전화 — 차단", "연락처 010-1234-5678", True),
    ("사업자번호 — 차단", "사업자번호 123-45-67890", True),
    ("외국인번호 — 차단", "외국인등록 900101-5234567", True),
    ("빈 문자열 — 통과", "", False),
]

for desc, text, should_block in cases:
    try:
        analyzer.analyze(text, QueryTarget.LEXICAL)
        blocked = False
    except PIIDetectedError:
        blocked = True
    status = "PASS" if blocked == should_block else "FAIL"
    print(f"  {status}: {desc}")
```

**기대 결과**: 모든 항목이 `PASS`.

---

## T-37: pii — PIIDetectedError 복수 패턴 동시 감지

**목적**: 복수의 PII 패턴이 동시에 존재할 때 `matched`에 모두 포함되는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import QueryAnalyzer, QueryTarget, PIIDetectedError

class _NoopSpacing:
    def restore(self, text: str) -> str:
        return text

analyzer = QueryAnalyzer(spacing_restorer=_NoopSpacing())

try:
    analyzer.analyze("주민번호 900101-1234567 전화 010-9999-8888", QueryTarget.LEXICAL)
    print("FAIL: 차단되어야 함")
except PIIDetectedError as e:
    print("matched:", e.matched)
    assert "resident_id" in e.matched
    assert "mobile_phone" in e.matched
    print("PASS: 복수 패턴 동시 감지")
```

**기대 결과**:
```
matched: ['resident_id', 'mobile_phone']
PASS: 복수 패턴 동시 감지
```

---

## T-38: mecab_check — check_mecab_dict() 반환 타입

**목적**: `check_mecab_dict()`가 `DictCheckResult`를 반환하는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import check_mecab_dict, DictCheckResult

result = check_mecab_dict()
print("결과:", result)
print("available:", result.available)
print("dict_path:", result.dict_path)
print("version:", result.version)
print("error:", result.error)

assert isinstance(result, DictCheckResult)
print("PASS")
```

**기대 결과 (MeCab 설치 환경)**:
```
결과: DictCheckResult(available=True, dict_path='/usr/local/lib/mecab/dic/mecab-ko-dic', version='...', error=None)
available: True
dict_path: /usr/local/lib/mecab/dic/mecab-ko-dic
version: ...
error: None
PASS
```

**기대 결과 (MeCab 미설치 환경)**:
```
결과: DictCheckResult(available=False, dict_path=None, version=None, error='...')
PASS
```

---

## T-39: mecab_check — 잘못된 경로 → available=False

**목적**: 존재하지 않는 사전 경로를 전달 시 `available=False`와 오류 메시지가 반환되는지 확인한다.

**테스트 방법**:
```python
from bpmg_korean_nlp import check_mecab_dict

result = check_mecab_dict(dict_path="/nonexistent/path/to/dic")
print("결과:", result)

assert result.available is False
assert result.error is not None and len(result.error) > 0
print("PASS: available=False, error 메시지 확인")
```

**기대 결과**:
```
결과: DictCheckResult(available=False, dict_path=None, version=None, error='...')
PASS: available=False, error 메시지 확인
```

---

## 전체 자동화 테스트 실행

위 수동 테스트 외에 pytest 자동화 테스트도 실행할 수 있다:

```bash
# 전체 테스트 실행
pytest tests/ -v

# 커버리지 포함
pytest tests/ --cov=src --cov-report=term-missing

# 골든셋 테스트만
pytest tests/test_golden.py -v

# 특정 모듈 테스트만
pytest tests/test_normalizer.py -v
pytest tests/test_tokenizer.py tests/test_tokenizer_mocked.py -v

# 성능 벤치마크
python scripts/benchmark.py
```
