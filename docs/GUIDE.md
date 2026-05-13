# bpmg-korean-nlp SDK API 가이드

한국어 NLP 전처리 SDK의 공개 API 레퍼런스입니다.
모든 public 심볼은 `bpmg_korean_nlp` 패키지에서 직접 임포트합니다.

```python
from bpmg_korean_nlp import KoreanNormalizer, MeCabTokenizer, ...
```

서브모듈(`bpmg_korean_nlp.normalizer` 등)에서 직접 임포트하면 내부 구조 변경 시
호환성이 깨질 수 있으므로 사용하지 마세요.

---

## 목차

1. [설치](#1-설치)
2. [KoreanNormalizer — 텍스트 정규화](#2-koreannormalizer--텍스트-정규화)
3. [SpacingRestorer — 띄어쓰기 복원](#3-spacingrestorer--띄어쓰기-복원)
4. [MeCabTokenizer — 형태소 분석](#4-mecabtokenizer--형태소-분석)
5. [QueryAnalyzer — 쿼리 변환](#5-queryanalyzer--쿼리-변환)
6. [Jamo 유틸리티](#6-jamo-유틸리티)
7. [불용어](#7-불용어)
8. [PII 패턴](#8-pii-패턴)
9. [MeCab 상태 확인](#9-mecab-상태-확인)
10. [데이터 모델](#10-데이터-모델)
11. [열거형](#11-열거형)
12. [예외 처리](#12-예외-처리)
13. [테스트 환경 패턴](#13-테스트-환경-패턴)

---

## 1. 설치

```bash
# 기본 설치
pip install bpmg-korean-nlp

# 한자→한글 변환 옵션 포함
pip install "bpmg-korean-nlp[hanja]"

# 개발 환경
uv pip install -e ".[dev]"
```

### 시스템 의존성

`MeCabTokenizer`는 MeCab과 mecab-ko-dic을 필요로 합니다.

**macOS**

```bash
brew install mecab mecab-ko mecab-ko-dic
```

**Ubuntu 22.04**

```bash
sudo apt-get install -y mecab libmecab-dev mecab-ipadic-utf8
```

`SpacingRestorer`는 PyKoSpacing을 별도 설치해야 합니다. 미설치 환경에서
`SpacingRestorer.get_instance()`를 호출하면 `SpacingModelLoadError`가 발생합니다.
나머지 기능은 PyKoSpacing 없이도 정상 동작합니다.

---

## 2. KoreanNormalizer — 텍스트 정규화

```python
from bpmg_korean_nlp import KoreanNormalizer
```

### 파이프라인 (고정 순서)

```
NFC → 유니코드 공백 통일 → 연속 공백 축소 → 반복 문자 축약(soynlp, num_repeats=2)
    → (선택) 한자→한글 → (선택) 커스텀 치환
```

### 생성자

```python
KoreanNormalizer(
    hanja_to_hangul: bool = False,
    custom_substitutions: list[tuple[str, str]] | None = None,
)
```


| 파라미터                   | 타입                             | 기본값     | 설명                                               |
| ---------------------- | ------------------------------ | ------- | ------------------------------------------------ |
| `hanja_to_hangul`      | `bool`                         | `False` | 한자를 한글로 음가 변환 (손실 가능, `hanja` 패키지 필요)            |
| `custom_substitutions` | `list[tuple[str, str]] | None` | `None`  | `(pattern, replacement)` 쌍의 리스트 — `re.sub` 순서 적용 |


### 메서드

#### `normalize(text: str) → str`

- 빈 문자열 입력 → 빈 문자열 반환
- `None` 또는 비문자열 → `InvalidInputError`

```python
normalizer = KoreanNormalizer()
normalizer.normalize("안녕하세요ㅋㅋㅋㅋㅋㅋ   세종!!!")
# → '안녕하세요ㅋㅋ 세종!!!'
```

#### `KoreanNormalizer.default() → KoreanNormalizer` (클래스 메서드)

기본 옵션으로 구성된 인스턴스를 반환합니다.

```python
norm = KoreanNormalizer.default()
```

### 예시

```python
norm = KoreanNormalizer()

# 전각 공백 → 일반 공백
print(norm.normalize("세　종　대　학교"))
# 세 종 대 학교

# 반복 문자 축약 (num_repeats=2)
print(norm.normalize("ㅋㅋㅋㅋㅋ"))
# ㅋㅋ

# 빈 문자열
print(repr(norm.normalize("")))
# ''

# 한자→한글 변환 (hanja 패키지 필요)
norm_hj = KoreanNormalizer(hanja_to_hangul=True)
print(norm_hj.normalize("大學校"))
# 대학교

# 커스텀 치환 규칙
norm_custom = KoreanNormalizer(
    custom_substitutions=[
        (r"\bSNU\b", "서울대"),
        (r"\bSJU\b", "세종대"),
    ]
)
print(norm_custom.normalize("SJU 도서관"))
# 세종대 도서관

# None 입력 → InvalidInputError
from bpmg_korean_nlp import InvalidInputError
try:
    norm.normalize(None)
except InvalidInputError as e:
    print(e)
# KoreanNormalizer.normalize expects str, got NoneType
```

---

## 3. git  — 띄어쓰기 복원

```python
from bpmg_korean_nlp import SpacingRestorer
```

PyKoSpacing 딥러닝 모델 기반의 띄어쓰기 복원기입니다.
모델 로딩 비용이 크므로 프로세스 내 싱글톤으로 관리됩니다.

> **주의**: PyKoSpacing을 별도 설치해야 합니다. 미설치 시 `SpacingModelLoadError`가 발생합니다.

### 싱글톤 획득

```python
# 권장 방식
restorer = SpacingRestorer.get_instance()

# 직접 생성 (동일 객체 반환)
restorer = SpacingRestorer()
```

### 메서드

#### `restore(text: str) → str`

내부적으로 `kss`로 문장 분리 후 각 문장에 PyKoSpacing 적용, 결과를 공백으로 합칩니다.


| 입력            | 출력                  |
| ------------- | ------------------- |
| 빈 문자열         | 빈 문자열               |
| `None` / 비문자열 | `InvalidInputError` |


### 예시

```python
restorer = SpacingRestorer.get_instance()

print(restorer.restore("아버지가방에들어가신다"))
# 아버지가 방에 들어가신다

print(restorer.restore("세종대학교도서관이어디있나요"))
# 세종대학교 도서관이 어디 있나요

# 두 번 호출해도 모델은 한 번만 로딩
restorer2 = SpacingRestorer.get_instance()
print(restorer is restorer2)
# True
```

---

## 4. MeCabTokenizer — 형태소 분석

```python
from bpmg_korean_nlp import MeCabTokenizer
```

`python-mecab-ko` 기반의 형태소 분석기입니다.
사전 로딩 비용이 크므로 `(dict_path, user_dict_path)` 쌍 기준으로 싱글톤 캐싱됩니다.

### 싱글톤 획득

```python
# 세 가지 방식 모두 동일 인스턴스 반환
tokenizer = MeCabTokenizer()
tokenizer = MeCabTokenizer.get_instance()
tokenizer = MeCabTokenizer(dict_path=None, user_dict_path=None)
```

### 생성자 / `get_instance`

```python
MeCabTokenizer(
    dict_path: str | None = None,
    user_dict_path: str | None = None,
)
```


| 파라미터             | 타입           | 기본값    | 설명                                   |
| ---------------- | ------------ | ------ | ------------------------------------ |
| `dict_path`      | `str | None` | `None` | mecab-ko-dic 경로. `None`이면 시스템 기본값 사용 |
| `user_dict_path` | `str | None` | `None` | 사용자 사전 경로                            |


### 메서드

#### `tokenize(text, pos_filter, remove_stopwords, stopwords) → list[str]`

BM25 검색에 적합한 표층형 토큰 리스트를 반환합니다.

```python
def tokenize(
    self,
    text: str,
    pos_filter: frozenset[str] | None = None,
    remove_stopwords: bool = False,
    stopwords: frozenset[str] | None = None,
) -> list[str]: ...
```


| 파라미터               | 설명                                          |
| ------------------ | ------------------------------------------- |
| `text`             | 분석할 문자열. 빈 문자열이면 `[]` 반환                    |
| `pos_filter`       | 세종 품사 태그 허용 집합. `None`이면 전체 품사 포함           |
| `remove_stopwords` | `True`이면 불용어 제거                             |
| `stopwords`        | 커스텀 불용어 집합. `None`이면 `DEFAULT_STOPWORDS` 사용 |


```python
tok = MeCabTokenizer()

# 기본 토크나이징
print(tok.tokenize("세종대학교에서 한국어 NLP를 연구한다"))
# ['세종', '대학교', '에서', '한국어', 'NLP', '를', '연구', '한다']

# 명사만 추출 (NNG: 일반명사, NNP: 고유명사)
print(tok.tokenize("세종대학교 도서관", pos_filter=frozenset({"NNG", "NNP"})))
# ['세종', '대학교', '도서관']

# 불용어 제거 ('의'가 DEFAULT_STOPWORDS에 포함)
print(tok.tokenize("세종대학교의 도서관", remove_stopwords=True))
# ['세종', '대학교', '도서관']

# 빈 문자열
print(tok.tokenize(""))
# []
```

#### `analyze(text) → list[MorphToken]`

형태소별 표층형·레마·품사·오프셋 정보를 담은 리스트를 반환합니다.

```python
tok = MeCabTokenizer()

for m in tok.analyze("세종대학교에서 한국어 NLP를 연구한다"):
    print(m)
# MorphToken(surface='세종', lemma='세종', pos='NNP', start=0, end=2)
# MorphToken(surface='대학교', lemma='대학교', pos='NNG', start=2, end=5)
# MorphToken(surface='에서', lemma='에서', pos='JKB', start=5, end=7)
# MorphToken(surface='한국어', lemma='한국어', pos='NNG', start=8, end=11)
# MorphToken(surface='NLP', lemma='NLP', pos='SL', start=12, end=15)
# MorphToken(surface='를', lemma='를', pos='JKO', start=15, end=16)
# MorphToken(surface='연구', lemma='연구', pos='NNG', start=17, end=19)
# MorphToken(surface='한다', lemma='한다', pos='XSV+EC', start=19, end=21)

# 짧은 입력
for m in tok.analyze("한국어 NLP"):
    print(m)
# MorphToken(surface='한국어', lemma='한국어', pos='NNG', start=0, end=3)
# MorphToken(surface='NLP', lemma='NLP', pos='SL', start=4, end=7)
```

`MorphToken` 필드:


| 필드        | 타입    | 설명               |
| --------- | ----- | ---------------- |
| `surface` | `str` | 원문 표층형           |
| `lemma`   | `str` | 기본형 (현재 표층형과 동일) |
| `pos`     | `str` | 세종 품사 태그         |
| `start`   | `int` | 원문 시작 오프셋 (포함)   |
| `end`     | `int` | 원문 종료 오프셋 (미포함)  |


#### `reset_instances()` (클래스 메서드, 테스트 전용)

싱글톤 캐시를 초기화합니다. 프로덕션 코드에서는 사용하지 마세요.

```python
MeCabTokenizer.reset_instances()
```

### 주요 세종 품사 태그


| 태그                 | 설명          |
| ------------------ | ----------- |
| `NNG`              | 일반 명사       |
| `NNP`              | 고유 명사       |
| `NNB`              | 의존 명사       |
| `VV`               | 동사          |
| `VA`               | 형용사         |
| `XSN`              | 명사 파생 접미사   |
| `JKS`, `JKO`, `JX` | 조사류         |
| `SL`               | 외국어 (Latin) |
| `SN`               | 숫자          |


---

## 5. QueryAnalyzer — 쿼리 변환

```python
from bpmg_korean_nlp import QueryAnalyzer, QueryTarget, analyze_query
```

원시 쿼리를 4가지 검색 타깃 표현으로 변환합니다.
점수 계산·검색 실행은 하지 않으며, 순수 변환 레이어입니다.

### 타깃별 동작


| `QueryTarget` | 출력 타입                 | 설명                              |
| ------------- | --------------------- | ------------------------------- |
| `LEXICAL`     | `LexicalQueryResult`  | 토크나이징 + 불용어 제거 → BM25 키워드       |
| `SEMANTIC`    | `SemanticQueryResult` | 정규화·띄어쓰기 복원된 자연어 문장 그대로 유지      |
| `GRAPH`       | `GraphQueryResult`    | 명사(`NNG`, `NNP`) 추출 → 그래프 시드 노드 |
| `HYBRID`      | `HybridQueryResult`   | 위 세 결과를 병렬로 합산                  |


### 생성자

```python
QueryAnalyzer(
    normalizer: KoreanNormalizer | None = None,
    tokenizer: MeCabTokenizer | None = None,
    spacing_restorer: SpacingRestorer | None = None,
    stopwords: frozenset[str] | None = None,
)
```

모든 파라미터가 `None`이면 SDK 기본 싱글톤을 자동 사용합니다.

### 메서드

#### `analyze(text: str, target: QueryTarget | str) → QueryResult`

`target`은 `QueryTarget` 열거형 또는 소문자 문자열(`"lexical"`, `"semantic"`, `"graph"`, `"hybrid"`)을 받습니다.

```python
# PyKoSpacing이 없는 환경에서는 스텁 주입 (아래 §14 참고)
# PyKoSpacing이 설치된 환경에서는 QueryAnalyzer() 그대로 사용
analyzer = QueryAnalyzer()

lex = analyzer.analyze("세종대학교 도서관 위치", QueryTarget.LEXICAL)
print(lex)
# LexicalQueryResult(keywords=('세종', '대학교', '도서관', '위치'), query='세종 대학교 도서관 위치')

sem = analyzer.analyze("세종대학교 도서관 위치", QueryTarget.SEMANTIC)
print(sem)
# SemanticQueryResult(query='세종대학교 도서관 위치')

graph = analyzer.analyze("세종대학교 도서관 위치", QueryTarget.GRAPH)
print(graph)
# GraphQueryResult(seed_nodes=('세종', '대학교', '도서관', '위치'))

hybrid = analyzer.analyze("세종대학교 도서관 위치", QueryTarget.HYBRID)
print(hybrid.lexical)
# LexicalQueryResult(keywords=('세종', '대학교', '도서관', '위치'), query='세종 대학교 도서관 위치')
print(hybrid.semantic)
# SemanticQueryResult(query='세종대학교 도서관 위치')
print(hybrid.graph)
# GraphQueryResult(seed_nodes=('세종', '대학교', '도서관', '위치'))
```

### 모듈 수준 편의 함수

#### `analyze_query(text, target="lexical") → QueryResult`

내부적으로 기본 `QueryAnalyzer` 싱글톤을 재사용합니다.
단순 호출 시 권장 방식입니다.

```python
from bpmg_korean_nlp import analyze_query, QueryTarget

result = analyze_query("세종대학교 도서관 위치", QueryTarget.LEXICAL)
print(result)
# LexicalQueryResult(keywords=('세종', '대학교', '도서관', '위치'), query='세종 대학교 도서관 위치')

result = analyze_query("세종대학교 도서관 위치", "semantic")  # 문자열도 가능
print(result)
# SemanticQueryResult(query='세종대학교 도서관 위치')
```

### HYBRID 병렬 처리

`HYBRID` 타깃은 `ThreadPoolExecutor(max_workers=3)`로 세 파이프라인을 병렬 실행합니다.
호출 비용: LEXICAL + SEMANTIC + GRAPH 중 가장 오래 걸리는 시간 ≈ HYBRID 총 소요 시간.

### 의존성 주입 (DI)

커스텀 컴포넌트 또는 테스트용 스텁을 주입할 수 있습니다.

```python
# 커스텀 불용어
from bpmg_korean_nlp import merge_stopwords

domain_stopwords = merge_stopwords(frozenset({"수업", "교재", "학점"}))
analyzer = QueryAnalyzer(stopwords=domain_stopwords)

# PyKoSpacing 없는 환경 — 스텁 주입
class _NoopSpacing:
    def restore(self, text: str) -> str:
        return text

analyzer = QueryAnalyzer(spacing_restorer=_NoopSpacing())
result = analyzer.analyze("테스트 쿼리", QueryTarget.LEXICAL)
print(result)
# LexicalQueryResult(keywords=('테스트', '쿼리'), query='테스트 쿼리')
```

---

## 6. Jamo 유틸리티

```python
from bpmg_korean_nlp import decompose, compose, extract_choseong, classify_char, CharType
```

유니코드 표준 기반 한글 자모 연산 함수들입니다. 모두 순수 함수입니다.

### `decompose(char: str) → JamoComponents`

한글 완성형 음절 하나를 초성·중성·종성으로 분해합니다.

- 입력: 완성형 한글 1글자 (U+AC00–U+D7A3)
- 입력이 아니거나 길이가 1이 아니면 `InvalidInputError`

```python
from bpmg_korean_nlp import decompose

print(decompose("닭"))
# JamoComponents(choseong='ㄷ', jungseong='ㅏ', jongseong='ㄺ')
# → 종성이 'ㄺ'(ㄹ+ㄱ 복합 자음)임에 주의

print(decompose("가"))
# JamoComponents(choseong='ㄱ', jungseong='ㅏ', jongseong='')

print(decompose("한"))
# JamoComponents(choseong='ㅎ', jungseong='ㅏ', jongseong='ㄴ')

print(decompose("세"))
# JamoComponents(choseong='ㅅ', jungseong='ㅔ', jongseong='')
```

### `compose(choseong, jungseong, jongseong="") → str`

초성·중성·종성을 합성해 한글 음절 하나를 만듭니다. `decompose`와 완전한 라운드트립을 보장합니다.

- 잘못된 자모 → `InvalidInputError`
- `compose(*decompose(c)) == c` 보장 (U+AC00–U+D7A3 전체)

```python
from bpmg_korean_nlp import compose

print(compose("ㄷ", "ㅏ", "ㄺ"))   # 닭  (종성 복합자음 ㄺ)
print(compose("ㄷ", "ㅏ", "ㄱ"))   # 닥  (종성 단순자음 ㄱ)
print(compose("ㄱ", "ㅏ"))          # 가  (종성 생략)
print(compose("ㄱ", "ㅏ", ""))      # 가  (빈 문자열도 종성 없음)
print(compose("ㅅ", "ㅔ"))          # 세
```

라운드트립 예시:

```python
from bpmg_korean_nlp import decompose, compose

for ch in ["닭", "세", "종", "한"]:
    comp = decompose(ch)
    back = compose(comp.choseong, comp.jungseong, comp.jongseong)
    print(f"{ch} → {comp} → {back!r}")
# 닭 → JamoComponents(choseong='ㄷ', jungseong='ㅏ', jongseong='ㄺ') → '닭'
# 세 → JamoComponents(choseong='ㅅ', jungseong='ㅔ', jongseong='') → '세'
# 종 → JamoComponents(choseong='ㅈ', jungseong='ㅗ', jongseong='ㅇ') → '종'
# 한 → JamoComponents(choseong='ㅎ', jungseong='ㅏ', jongseong='ㄴ') → '한'
```

### `extract_choseong(text: str) → str`

문자열의 초성 투영을 반환합니다. 한글 음절만 초성으로 치환하고 나머지 문자는 그대로 유지합니다.
초성 검색, 퍼지 매칭 등에 활용합니다.

```python
from bpmg_korean_nlp import extract_choseong

print(extract_choseong("안녕하세요"))
# ㅇㄴㅎㅅㅇ

print(extract_choseong("한국어 NLP"))
# ㅎㄱㅇ NLP

print(extract_choseong("123 테스트"))
# 123 ㅌㅅㅌ
```

### `classify_char(char: str) → CharType`

단일 유니코드 문자를 스크립트/카테고리별로 분류합니다.

- 입력: 정확히 한 글자. 아니면 `InvalidInputError`

```python
from bpmg_korean_nlp import classify_char

print(classify_char("가"))   # hangul_syllable
print(classify_char("ㄱ"))   # hangul_jamo
print(classify_char("語"))   # hanja
print(classify_char("A"))    # latin
print(classify_char("1"))    # number
print(classify_char("!"))    # symbol
print(classify_char(" "))    # whitespace
```

`CharType`은 `StrEnum`이므로 `classify_char("가") == "hangul_syllable"`이 `True`입니다.

---

## 7. 불용어

```python
from bpmg_korean_nlp import DEFAULT_STOPWORDS, merge_stopwords
```

### `DEFAULT_STOPWORDS: frozenset[str]`

도메인 비특화 한국어 불용어 집합입니다. 조사·보조동사·지시어·부사 등 155개 포함.
`frozenset`이므로 직접 변경할 수 없습니다.

```python
print("의" in DEFAULT_STOPWORDS)     # True
print("도서관" in DEFAULT_STOPWORDS)  # False
print(len(DEFAULT_STOPWORDS))         # 155
```

### `merge_stopwords(*additional, base=None) → frozenset[str]`

`DEFAULT_STOPWORDS`(또는 `base`)에 도메인 불용어를 추가한 새 `frozenset`을 반환합니다.
원본은 변경되지 않습니다.

```python
from bpmg_korean_nlp import DEFAULT_STOPWORDS, merge_stopwords

# 도메인 불용어 4개 추가
edu_stopwords = merge_stopwords(
    frozenset({"수업", "교재", "학점", "학기"}),
)
print(len(edu_stopwords))             # 159  (155 + 4)
print("수업" in edu_stopwords)        # True
print(len(DEFAULT_STOPWORDS))         # 155  (원본 불변)

# 여러 세트를 한 번에 병합
combined = merge_stopwords(
    frozenset({"수업", "교재"}),
    frozenset({"과제", "시험"}),
    base=DEFAULT_STOPWORDS,
)
print(len(combined))                  # 159  (155 + 4)
```

---

## 8. PII 패턴

```python
from bpmg_korean_nlp import PII_PATTERNS, PIIPattern, PIIDetectedError
```

`guardrail-core`가 1차 필터라면 이 SDK는 **2차 차단 레이어**입니다.
`QueryAnalyzer.analyze()` 진입 시 입력 텍스트를 자동으로 검사하고,
PII 패턴이 감지되면 `PIIDetectedError`를 raise합니다.

### 자동 차단 동작

```python
from bpmg_korean_nlp import QueryAnalyzer, QueryTarget, PIIDetectedError

analyzer = QueryAnalyzer()

try:
    analyzer.analyze("내 주민번호는 900101-1234567 이야", QueryTarget.LEXICAL)
except PIIDetectedError as e:
    print(e)
    # PII detected in input: resident_id
    print(e.matched)
    # ['resident_id']

# 복수 패턴 동시 감지 — 전부 수집해서 한 번에 보고
try:
    analyzer.analyze("주민번호 900101-1234567, 전화 010-1234-5678", QueryTarget.LEXICAL)
except PIIDetectedError as e:
    print(e.matched)
    # ['resident_id', 'mobile_phone']

# PII 없는 정상 쿼리 — 그대로 통과
result = analyzer.analyze("세종대학교 도서관 위치", QueryTarget.LEXICAL)
print(result)
# LexicalQueryResult(keywords=('세종', '대학교', '도서관', '위치'), query='세종 대학교 도서관 위치')
```

### `PII_PATTERNS: tuple[PIIPattern, ...]`

내장 PII 패턴 목록입니다. 소비자가 직접 정규식을 활용해야 하는 경우에 참조합니다.


| `name`         | `description` | 패턴 예시            |
| -------------- | ------------- | ---------------- |
| `resident_id`  | 주민등록번호        | `900101-1234567` |
| `mobile_phone` | 휴대전화 번호       | `010-1234-5678`  |
| `business_id`  | 사업자등록번호       | `123-45-67890`   |
| `foreign_id`   | 외국인등록번호       | `900101-5234567` |


```python
for p in PII_PATTERNS:
    print(p.name, p.description, p.pattern.pattern)
# resident_id 주민등록번호 \d{6}-[1-4]\d{6}
# mobile_phone 휴대전화 번호 01[016789]-\d{3,4}-\d{4}
# business_id 사업자등록번호 \d{3}-\d{2}-\d{5}
# foreign_id 외국인등록번호 \d{6}-[5-8]\d{6}
```

### `PIIPattern` 필드


| 필드            | 타입                |
| ------------- | ----------------- |
| `name`        | `str`             |
| `description` | `str`             |
| `pattern`     | `re.Pattern[str]` |


---

## 9. MeCab 상태 확인

```python
from bpmg_korean_nlp import check_mecab_dict, DictCheckResult
```

### `check_mecab_dict() → DictCheckResult`

MeCab 사전 로드 가능 여부를 확인합니다. CI 헬스체크·부팅 진단에 활용합니다.

```python
result = check_mecab_dict()
print(result)
# DictCheckResult(available=True, dict_path='/opt/homebrew/lib/mecab/dic/mecab-ko-dic', version=None, error=None)

print(result.available)   # True
print(result.dict_path)   # /opt/homebrew/lib/mecab/dic/mecab-ko-dic
print(result.version)     # None  (mecab-ko-dic은 버전 정보를 별도 노출하지 않음)
print(result.error)       # None
```

`DictCheckResult` 필드:


| 필드          | 타입           | 설명                             |
| ----------- | ------------ | ------------------------------ |
| `available` | `bool`       | MeCab 초기화 성공 여부                |
| `dict_path` | `str | None` | 활성 사전 경로                       |
| `version`   | `str | None` | 사전 버전                          |
| `error`     | `str | None` | 오류 메시지 (`available=False`인 경우) |


```python
# CI 스크립트 예시
result = check_mecab_dict()
if not result.available:
    raise SystemExit(f"MeCab 사전 로드 실패: {result.error}")
print(f"MeCab OK — dict: {result.dict_path}")
# MeCab OK — dict: /opt/homebrew/lib/mecab/dic/mecab-ko-dic
```

---

## 10. 데이터 모델

모든 모델은 `@dataclass(frozen=True, slots=True)`로 선언되어 있어 불변·해시 가능합니다.

```python
from bpmg_korean_nlp import (
    MorphToken, JamoComponents, DictCheckResult,
    PIIPattern, LexicalQueryResult, SemanticQueryResult,
    GraphQueryResult, HybridQueryResult,
)
```

### `MorphToken`

```python
MorphToken(surface: str, lemma: str, pos: str, start: int, end: int)
```

### `JamoComponents`

```python
JamoComponents(choseong: str, jungseong: str, jongseong: str)
# jongseong은 받침 없으면 ""
```

### `DictCheckResult`

```python
DictCheckResult(available: bool, dict_path: str | None,
                version: str | None, error: str | None)
```

### `PIIPattern`

```python
PIIPattern(name: str, description: str, pattern: re.Pattern[str])
```

### `LexicalQueryResult`

```python
LexicalQueryResult(keywords: tuple[str, ...], query: str)
# query = " ".join(keywords)
```

### `SemanticQueryResult`

```python
SemanticQueryResult(query: str)
```

### `GraphQueryResult`

```python
GraphQueryResult(seed_nodes: tuple[str, ...])
```

### `HybridQueryResult`

```python
HybridQueryResult(
    lexical: LexicalQueryResult,
    semantic: SemanticQueryResult,
    graph: GraphQueryResult,
)
```

```python
# 필드 접근 예시
result = analyzer.analyze("세종대학교 도서관", QueryTarget.HYBRID)

print(result.lexical.keywords)
# ('세종', '대학교', '도서관')

print(result.semantic.query)
# 세종대학교 도서관

print(result.graph.seed_nodes)
# ('세종', '대학교', '도서관')
```

### `QueryResult` (타입 별칭)

```python
type QueryResult = LexicalQueryResult | SemanticQueryResult | GraphQueryResult | HybridQueryResult
```

---

## 11. 열거형

```python
from bpmg_korean_nlp import QueryTarget, CharType
```

두 열거형 모두 `StrEnum`을 상속합니다 — 문자열 비교와 열거형 비교 모두 가능합니다.

### `QueryTarget`


| 멤버                     | 값            |
| ---------------------- | ------------ |
| `QueryTarget.LEXICAL`  | `"lexical"`  |
| `QueryTarget.SEMANTIC` | `"semantic"` |
| `QueryTarget.GRAPH`    | `"graph"`    |
| `QueryTarget.HYBRID`   | `"hybrid"`   |


```python
print(QueryTarget.LEXICAL == "lexical")   # True
print(str(QueryTarget.SEMANTIC))          # semantic
```

### `CharType`


| 멤버                         | 값                   |
| -------------------------- | ------------------- |
| `CharType.HANGUL_SYLLABLE` | `"hangul_syllable"` |
| `CharType.HANGUL_JAMO`     | `"hangul_jamo"`     |
| `CharType.HANJA`           | `"hanja"`           |
| `CharType.LATIN`           | `"latin"`           |
| `CharType.NUMBER`          | `"number"`          |
| `CharType.SYMBOL`          | `"symbol"`          |
| `CharType.WHITESPACE`      | `"whitespace"`      |
| `CharType.OTHER`           | `"other"`           |


---

## 12. 예외 처리

```python
from bpmg_korean_nlp import (
    KoreanNlpError,
    InvalidInputError,
    MeCabNotAvailableError,
    PIIDetectedError,
    SpacingModelLoadError,
)
```

### 예외 계층

```
KoreanNlpError (기반 클래스)
├── InvalidInputError        — None 또는 str이 아닌 입력
├── MeCabNotAvailableError   — MeCab 초기화·분석 실패
├── SpacingModelLoadError    — PyKoSpacing 모델 로드 실패
└── PIIDetectedError         — PII 패턴 감지 (2차 필터)
```

### 언제 발생하는가


| 예외                       | 발생 시점                                                             |
| ------------------------ | ----------------------------------------------------------------- |
| `InvalidInputError`      | `None` 또는 비문자열 입력 시. **빈 문자열은 정상** — 빈 결과 반환                      |
| `MeCabNotAvailableError` | `python-mecab-ko` 미설치, 사전 경로 오류, 분석 실패                            |
| `SpacingModelLoadError`  | `pykospacing` 미설치 또는 모델 초기화 실패                                    |
| `PIIDetectedError`       | `QueryAnalyzer.analyze()` 입력에 PII 패턴 감지. `e.matched`에 패턴 이름 목록 포함 |


### 예시

```python
from bpmg_korean_nlp import KoreanNormalizer, KoreanNlpError, InvalidInputError

norm = KoreanNormalizer()

# 빈 문자열은 정상 — 빈 문자열 반환
print(repr(norm.normalize("")))
# ''

# None은 오류
try:
    norm.normalize(None)
except InvalidInputError as e:
    print(e)
# KoreanNormalizer.normalize expects str, got NoneType

# SDK 전체 예외를 한 번에 처리
try:
    result = norm.normalize(some_input)
except KoreanNlpError as e:
    print(f"SDK 오류: {e}")
```

```python
from bpmg_korean_nlp import MeCabTokenizer, MeCabNotAvailableError

try:
    tok = MeCabTokenizer()
    tokens = tok.tokenize("테스트")
    print(tokens)
    # ['테스트']
except MeCabNotAvailableError as e:
    print(f"MeCab 사용 불가: {e}")
```

```python
from bpmg_korean_nlp import SpacingRestorer, SpacingModelLoadError

try:
    restorer = SpacingRestorer.get_instance()
except SpacingModelLoadError as e:
    print(f"PyKoSpacing 로드 실패: {e}")
    # PyKoSpacing 없이 계속 진행하는 폴백 처리
```

```python
from bpmg_korean_nlp import QueryAnalyzer, QueryTarget, PIIDetectedError

analyzer = QueryAnalyzer()

try:
    analyzer.analyze("주민번호 900101-1234567", QueryTarget.SEMANTIC)
except PIIDetectedError as e:
    print(e)
    # PII detected in input: resident_id
    print(e.matched)
    # ['resident_id']
```

---

## 13. 테스트 환경 패턴

### PyKoSpacing 없는 환경에서 QueryAnalyzer 사용

PyKoSpacing이 설치되지 않은 CI 환경이나 경량 개발 환경에서 `QueryAnalyzer`를 테스트할 때
스텁을 주입합니다.

```python
from bpmg_korean_nlp import QueryAnalyzer, QueryTarget

class _NoopSpacing:
    """PyKoSpacing 스텁 — 입력을 그대로 반환."""
    def restore(self, text: str) -> str:
        return text

analyzer = QueryAnalyzer(spacing_restorer=_NoopSpacing())
result = analyzer.analyze("세종대학교 도서관", QueryTarget.LEXICAL)
print(result)
# LexicalQueryResult(keywords=('세종', '대학교', '도서관'), query='세종 대학교 도서관')

print(result.keywords)
# ('세종', '대학교', '도서관')
```

### MeCabTokenizer 싱글톤 캐시 초기화 (테스트 격리)

```python
import pytest
from bpmg_korean_nlp import MeCabTokenizer

@pytest.fixture(autouse=True)
def reset_tokenizer():
    MeCabTokenizer.reset_instances()
    yield
    MeCabTokenizer.reset_instances()
```

### MeCab 상태 확인 후 테스트 건너뛰기

```python
import pytest
from bpmg_korean_nlp import check_mecab_dict

mecab_available = check_mecab_dict().available

@pytest.mark.skipif(not mecab_available, reason="MeCab 사전 없음")
def test_tokenize():
    from bpmg_korean_nlp import MeCabTokenizer
    tok = MeCabTokenizer()
    result = tok.tokenize("테스트")
    print(result)
    # ['테스트']
    assert result != []
```

---

## Public API 목록 (`__all__`)


| 심볼                       | 종류                       | 모듈               |
| ------------------------ | ------------------------ | ---------------- |
| `KoreanNormalizer`       | 클래스                      | `normalizer`     |
| `SpacingRestorer`        | 클래스                      | `spacing`        |
| `MeCabTokenizer`         | 클래스                      | `tokenizer`      |
| `QueryAnalyzer`          | 클래스                      | `query_analyzer` |
| `QueryTarget`            | StrEnum                  | `enums`          |
| `CharType`               | StrEnum                  | `enums`          |
| `analyze_query`          | 함수                       | `query_analyzer` |
| `decompose`              | 함수                       | `jamo_utils`     |
| `compose`                | 함수                       | `jamo_utils`     |
| `extract_choseong`       | 함수                       | `jamo_utils`     |
| `classify_char`          | 함수                       | `jamo_utils`     |
| `check_mecab_dict`       | 함수                       | `mecab_check`    |
| `DEFAULT_STOPWORDS`      | `frozenset[str]`         | `stopwords`      |
| `merge_stopwords`        | 함수                       | `stopwords`      |
| `PII_PATTERNS`           | `tuple[PIIPattern, ...]` | `pii`            |
| `MorphToken`             | 데이터클래스                   | `models`         |
| `JamoComponents`         | 데이터클래스                   | `models`         |
| `DictCheckResult`        | 데이터클래스                   | `models`         |
| `PIIPattern`             | 데이터클래스                   | `models`         |
| `LexicalQueryResult`     | 데이터클래스                   | `models`         |
| `SemanticQueryResult`    | 데이터클래스                   | `models`         |
| `GraphQueryResult`       | 데이터클래스                   | `models`         |
| `HybridQueryResult`      | 데이터클래스                   | `models`         |
| `QueryResult`            | 타입 별칭                    | `models`         |
| `KoreanNlpError`         | 예외                       | `exceptions`     |
| `InvalidInputError`      | 예외                       | `exceptions`     |
| `MeCabNotAvailableError` | 예외                       | `exceptions`     |
| `PIIDetectedError`       | 예외                       | `exceptions`     |
| `SpacingModelLoadError`  | 예외                       | `exceptions`     |


