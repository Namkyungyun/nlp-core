# TEST.LOCAL.md

로컬 기능 테스트 내역서. 각 섹션의 명령을 그대로 복사해서 실행하면 됩니다.

> **전제 조건**: `.venv` 활성화 및 `pip install -e ".[dev]"` 완료 상태.
>
> ```bash
> source .venv/bin/activate
> ```
>
> 모든 명령은 `python - << 'EOF' ... EOF` 히어독 형식입니다.  
> 셸의 변수 확장·히스토리 확장(`!`)이 코드에 영향을 주지 않아 안전하게 복사·실행할 수 있습니다.

---

## 목차


| #    | 영역               | 테스트 항목              |
| ---- | ---------------- | ------------------- |
| T-01 | 환경               | 공개 API 31개 심볼 로드    |
| T-02 | KoreanNormalizer | NFC 정규화             |
| T-03 | KoreanNormalizer | 반복 문자 축약            |
| T-04 | KoreanNormalizer | 공백 정규화 (유니코드 공백 포함) |
| T-05 | KoreanNormalizer | 커스텀 치환              |
| T-06 | KoreanNormalizer | 에러 처리 (None, int)   |
| T-07 | MeCabTokenizer   | 기본 토크나이징            |
| T-08 | MeCabTokenizer   | 형태소 분석 (POS + 오프셋)  |
| T-09 | MeCabTokenizer   | POS 필터              |
| T-10 | MeCabTokenizer   | 불용어 제거              |
| T-11 | MeCabTokenizer   | 에러 처리 (None, int)   |
| T-12 | QueryAnalyzer    | LEXICAL 타깃          |
| T-13 | QueryAnalyzer    | SEMANTIC 타깃         |
| T-14 | QueryAnalyzer    | GRAPH 타깃            |
| T-15 | QueryAnalyzer    | HYBRID 타깃           |
| T-16 | QueryAnalyzer    | 빈 문자열 / 공백만 입력      |
| T-17 | QueryAnalyzer    | 문자열 타깃 (대소문자 무관)    |
| T-18 | QueryAnalyzer    | 에러 처리               |
| T-19 | JamoUtils        | decompose / compose |
| T-20 | JamoUtils        | extract_choseong    |
| T-21 | JamoUtils        | classify_char       |
| T-22 | Stopwords        | 불용어 집합              |
| T-23 | PII              | 패턴 매칭               |
| T-24 | MeCab 점검         | check_mecab_dict    |


---

## T-01 — 공개 API 29개 심볼 로드

```bash
python - << 'EOF'
import bpmg_korean_nlp
print('심볼 수:', len(bpmg_korean_nlp.__all__))
print(bpmg_korean_nlp.__all__)
EOF
```

**기대 결과**

```
심볼 수: 29
['DEFAULT_STOPWORDS', 'PII_PATTERNS', 'CharType', 'DictCheckResult', 'GraphQueryResult',
 'HybridQueryResult', 'InvalidInputError', 'JamoComponents', 'KoreanNlpError', 'KoreanNormalizer',
 'LexicalQueryResult', 'MeCabNotAvailableError', 'MeCabTokenizer', 'MorphToken',
 'PIIPattern', 'QueryAnalyzer', 'QueryResult', 'QueryTarget', 'SemanticQueryResult',
 'SpacingModelLoadError', 'SpacingRestorer', 'analyze_query', 'check_mecab_dict', 'classify_char',
 'compose', 'decompose', 'extract_choseong',
 'merge_stopwords']
```

---

## T-02 — KoreanNormalizer: NFC 정규화

```bash
python - << 'EOF'
import unicodedata
from bpmg_korean_nlp import KoreanNormalizer

norm = KoreanNormalizer.default()

nfd = unicodedata.normalize('NFD', '안녕')
print('입력 (NFD):', repr(nfd), '길이:', len(nfd))
result = norm.normalize(nfd)
print('출력 (NFC):', repr(result), '길이:', len(result))
print('일반 문자열 동일 결과:', norm.normalize('안녕하세요'))
EOF
```

**기대 결과**

```
입력 (NFD): '안녕' 길이: 4
출력 (NFC): '안녕' 길이: 2
일반 문자열 동일 결과: 안녕하세요
```

> NFD는 한 글자를 초성·중성(·종성)으로 분리 저장합니다. NFC 정규화 후 다시 결합됩니다.

---

## T-03 — KoreanNormalizer: 반복 문자 축약

```bash
python - << 'EOF'
from bpmg_korean_nlp import KoreanNormalizer

norm = KoreanNormalizer.default()

cases = [
    'ㅋㅋㅋㅋ',
    'ㅠㅠㅠㅠㅠ',
    '아아아아 좋다',
    '안녕하세요ㅋㅋㅋㅋ   세종!!!',
]
for text in cases:
    print(repr(text), '->', repr(norm.normalize(text)))
EOF
```

**기대 결과**

```
'ㅋㅋㅋㅋ' -> 'ㅋㅋ'
'ㅠㅠㅠㅠㅠ' -> 'ㅠㅠ'
'아아아아 좋다' -> '아아 좋다'
'안녕하세요ㅋㅋㅋㅋ   세종!!!' -> '안녕하세요ㅋㅋ 세종!!!'
```

> `soynlp.repeat_normalize(num_repeats=2)` 적용: 3회 이상 반복 문자는 2회로 축약됩니다.

---

## T-04 — KoreanNormalizer: 공백 정규화

```bash
python - << 'EOF'
from bpmg_korean_nlp import KoreanNormalizer

norm = KoreanNormalizer.default()

cases = [
    '안녕  하세요',
    '  앞뒤 공백  ',
    '\xa0비공백\xa0',
    '　전각　공백',
    ' EM SPACE',
]
for text in cases:
    print(repr(text), '->', repr(norm.normalize(text)))
EOF
```

**기대 결과**

```
'안녕  하세요' -> '안녕 하세요'
'  앞뒤 공백  ' -> '앞뒤 공백'
'\xa0비공백\xa0' -> '비공백'
'　전각　공백' -> '전각 공백'
' EM SPACE' -> 'EM SPACE'
```

> `\xa0` = NO-BREAK SPACE, 　 `= 전각 공백,`   = EM SPACE.  
> 모든 유니코드 공백 문자를 ASCII 공백으로 변환 후, 연속 공백을 단일 공백으로 축약합니다.

---

## T-05 — KoreanNormalizer: 커스텀 치환

```bash
python - << 'EOF'
from bpmg_korean_nlp import KoreanNormalizer

norm = KoreanNormalizer(custom_substitutions=[('ㅋㅋ', '웃음'), ('ㅠㅠ', '슬픔')])
print(norm.normalize('ㅋㅋㅋㅋ 이렇게해보니까재밌다 ㅠㅠㅠ'))

norm2 = KoreanNormalizer(custom_substitutions=[('AB', 'X'), ('XC', 'Y')])
print(norm2.normalize('ABC'))
EOF
```

**기대 결과**

```
웃음 재밌다 슬픔ㅠ
Y
```

> `ㅠㅠㅠ`는 repeat_normalize → `ㅠㅠ` → 커스텀 치환 → `슬픔` 순으로 처리됩니다.  
> 마지막 `ㅠ`는 단독이므로 repeat_normalize 대상이 아니어서 치환되지 않습니다.

---

## T-06 — KoreanNormalizer: 에러 처리

```bash
python - << 'EOF'
from bpmg_korean_nlp import KoreanNormalizer, InvalidInputError

norm = KoreanNormalizer.default()

for bad in [None, 42, b'bytes', ['list']]:
    try:
        norm.normalize(bad)
    except InvalidInputError as e:
        print(f'{type(bad).__name__} -> InvalidInputError: {e}')
EOF
```

**기대 결과**

```
NoneType -> InvalidInputError: KoreanNormalizer.normalize expects str, got NoneType
int -> InvalidInputError: KoreanNormalizer.normalize expects str, got int
bytes -> InvalidInputError: KoreanNormalizer.normalize expects str, got bytes
list -> InvalidInputError: KoreanNormalizer.normalize expects str, got list
```

---

## T-07 — MeCabTokenizer: 기본 토크나이징

```bash
python - << 'EOF'
from bpmg_korean_nlp import MeCabTokenizer

tok = MeCabTokenizer()

cases = [
    '세종대학교에서 한국어 NLP를 연구한다',
    '아버지가방에들어가신다',
    '나는 학교에 갔다',
    'BTS는 한국 아이돌 그룹이다',
    '2024년 3월 15일',
    '',
]
for text in cases:
    print(repr(text), '->', tok.tokenize(text))
EOF
```

**기대 결과**

```
'세종대학교에서 한국어 NLP를 연구한다' -> ['세종', '대학교', '에서', '한국어', 'NLP', '를', '연구', '한다']
'아버지가방에들어가신다' -> ['아버지', '가', '방', '에', '들어가', '신다']
'나는 학교에 갔다' -> ['나', '는', '학교', '에', '갔', '다']
'BTS는 한국 아이돌 그룹이다' -> ['BTS', '는', '한국', '아이돌', '그룹', '이', '다']
'2024년 3월 15일' -> ['2024', '년', '3', '월', '15', '일']
'' -> []
```

---

## T-08 — MeCabTokenizer: 형태소 분석 (POS + 오프셋)

```bash
python - << 'EOF'
from bpmg_korean_nlp import MeCabTokenizer

tok = MeCabTokenizer()
morphs = tok.analyze('세종대학교에서 한국어 NLP를 연구한다')

print(f"{'surface':10} {'lemma':10} {'pos':12} offset")
print('-' * 46)
for m in morphs:
    print(f'{repr(m.surface):10} {repr(m.lemma):10} {repr(m.pos):12} [{m.start}:{m.end}]')
EOF
```

**기대 결과**

```
surface    lemma      pos          offset
----------------------------------------------
'세종'       '세종'       'NNP'        [0:2]
'대학교'      '대학교'      'NNG'        [2:5]
'에서'       '에서'       'JKB'        [5:7]
'한국어'      '한국어'      'NNG'        [8:11]
'NLP'      'NLP'      'SL'         [12:15]
'를'        '를'        'JKO'        [15:16]
'연구'       '연구'       'NNG'        [17:19]
'한다'       '한다'       'XSV+EC'     [19:21]
```

> 주요 POS 태그 — NNP: 고유명사, NNG: 일반명사, JKB: 부사격조사, JKO: 목적격조사, SL: 외국어, XSV: 동사파생접사, EC: 연결어미

---

## T-09 — MeCabTokenizer: POS 필터

```bash
python - << 'EOF'
from bpmg_korean_nlp import MeCabTokenizer

tok = MeCabTokenizer()
text = '세종대학교에서 한국어 NLP를 연구한다'

nouns = tok.tokenize(text, pos_filter=frozenset({'NNG', 'NNP'}))
print('명사만 (NNG+NNP):', nouns)

verbs = tok.tokenize(text, pos_filter=frozenset({'VV'}))
print('동사만 (VV):', verbs)

particles = tok.tokenize(text, pos_filter=frozenset({'JKS', 'JKO', 'JKB', 'JX'}))
print('조사만:', particles)
EOF
```

**기대 결과**

```
명사만 (NNG+NNP): ['세종', '대학교', '한국어', '연구']
동사만 (VV): []
조사만: ['에서', '를']
```

---

## T-10 — MeCabTokenizer: 불용어 제거

```bash
python - << 'EOF'
from bpmg_korean_nlp import MeCabTokenizer, DEFAULT_STOPWORDS

tok = MeCabTokenizer()
text = '나는 학교에 갔다'

without = tok.tokenize(text, remove_stopwords=False)
print('불용어 유지:', without)

with_stop = tok.tokenize(text, remove_stopwords=True)
print('불용어 제거:', with_stop)

text2 = '세종대학교에서 한국어를 연구한다'
custom = tok.tokenize(text2, remove_stopwords=True, stopwords=frozenset({'에서', '를', '한다'}))
print('커스텀 불용어:', custom)

print()
for word in ['은', '는', '세종', '대학교']:
    print(f'  {repr(word)} in DEFAULT_STOPWORDS: {word in DEFAULT_STOPWORDS}')
EOF
```

**기대 결과**

```
불용어 유지: ['나', '는', '학교', '에', '갔', '다']
불용어 제거: ['학교', '갔', '다']
커스텀 불용어: ['세종', '대학교', '한국어', '연구']

  '은' in DEFAULT_STOPWORDS: True
  '는' in DEFAULT_STOPWORDS: True
  '세종' in DEFAULT_STOPWORDS: False
  '대학교' in DEFAULT_STOPWORDS: False
```

---

## T-11 — MeCabTokenizer: 에러 처리

```bash
python - << 'EOF'
from bpmg_korean_nlp import MeCabTokenizer, InvalidInputError

tok = MeCabTokenizer()

for bad in [None, 123, ['list']]:
    try:
        tok.tokenize(bad)
    except InvalidInputError as e:
        print(f'tokenize({type(bad).__name__}) -> InvalidInputError: {e}')

for bad in [None, 123]:
    try:
        tok.analyze(bad)
    except InvalidInputError as e:
        print(f'analyze({type(bad).__name__}) -> InvalidInputError: {e}')
EOF
```

**기대 결과**

```
tokenize(NoneType) -> InvalidInputError: text must be a str, got NoneType
tokenize(int) -> InvalidInputError: text must be a str, got int
tokenize(list) -> InvalidInputError: text must be a str, got list
analyze(NoneType) -> InvalidInputError: text must be a str, got NoneType
analyze(int) -> InvalidInputError: text must be a str, got int
```

---

## T-12 — QueryAnalyzer: LEXICAL 타깃

> QueryAnalyzer는 내부적으로 SpacingRestorer를 사용합니다.  
> PyKoSpacing 미설치 환경에서는 아래와 같이 noop 스텁을 주입합니다.

```bash
python - << 'EOF'
from bpmg_korean_nlp import QueryAnalyzer, QueryTarget

class _NoopSpacing:
    def restore(self, text):
        return text

qa = QueryAnalyzer(spacing_restorer=_NoopSpacing())

cases = [
    '세종대학교 도서관 위치',
    '조사랑 어미 차이가 뭐예요',
    '자연어 처리란 무엇인가',
]
for text in cases:
    result = qa.analyze(text, QueryTarget.LEXICAL)
    print(f'입력: {repr(text)}')
    print(f'  keywords: {result.keywords}')
    print(f'  query: {repr(result.query)}')
    print()
EOF
```

**기대 결과**

```
입력: '세종대학교 도서관 위치'
  keywords: ('세종', '대학교', '도서관', '위치')
  query: '세종 대학교 도서관 위치'

입력: '조사랑 어미 차이가 뭐예요'
  keywords: ('조사', '어미', '차이', '뭐', '예요')
  query: '조사 어미 차이 뭐 예요'

입력: '자연어 처리란 무엇인가'
  keywords: ('자연어', '처리', '란', '인가')
  query: '자연어 처리 란 인가'
```

---

## T-13 — QueryAnalyzer: SEMANTIC 타깃

```bash
python - << 'EOF'
from bpmg_korean_nlp import QueryAnalyzer, QueryTarget

class _NoopSpacing:
    def restore(self, text):
        return text

qa = QueryAnalyzer(spacing_restorer=_NoopSpacing())

cases = ['세종대학교 도서관 위치', '한국어 NLP란 무엇인가']
for text in cases:
    result = qa.analyze(text, QueryTarget.SEMANTIC)
    print(f'입력: {repr(text)} -> query: {repr(result.query)}')
EOF
```

**기대 결과**

```
입력: '세종대학교 도서관 위치' -> query: '세종대학교 도서관 위치'
입력: '한국어 NLP란 무엇인가' -> query: '한국어 NLP란 무엇인가'
```

> SEMANTIC은 정규화만 수행하고 토크나이징하지 않습니다. 임베딩 모델이 소비할 원문 문장 그대로를 반환합니다.

---

## T-14 — QueryAnalyzer: GRAPH 타깃

```bash
python - << 'EOF'
from bpmg_korean_nlp import QueryAnalyzer, QueryTarget

class _NoopSpacing:
    def restore(self, text):
        return text

qa = QueryAnalyzer(spacing_restorer=_NoopSpacing())

cases = [
    '세종대학교 도서관 위치',
    'BTS와 블랙핑크 콜라보 가능성',
]
for text in cases:
    result = qa.analyze(text, QueryTarget.GRAPH)
    print(f'입력: {repr(text)}')
    print(f'  seed_nodes: {result.seed_nodes}')
EOF
```

**기대 결과**

```
입력: '세종대학교 도서관 위치'
  seed_nodes: ('세종', '대학교', '도서관', '위치')
입력: 'BTS와 블랙핑크 콜라보 가능성'
  seed_nodes: ('블랙', '핑크', '콜라보', '가능')
```

> GRAPH는 NNG(일반명사)·NNP(고유명사) 태그만 추출합니다. 조사·동사·어미는 제외됩니다.

---

## T-15 — QueryAnalyzer: HYBRID 타깃

```bash
python - << 'EOF'
from bpmg_korean_nlp import QueryAnalyzer, QueryTarget

class _NoopSpacing:
    def restore(self, text):
        return text

qa = QueryAnalyzer(spacing_restorer=_NoopSpacing())
result = qa.analyze('세종대학교 도서관 위치', QueryTarget.HYBRID)

print('type:', type(result).__name__)
print()
print('[LEXICAL]')
print('  keywords:', result.lexical.keywords)
print('  query:', repr(result.lexical.query))
print()
print('[SEMANTIC]')
print('  query:', repr(result.semantic.query))
print()
print('[GRAPH]')
print('  seed_nodes:', result.graph.seed_nodes)
EOF
```

**기대 결과**

```
type: HybridQueryResult

[LEXICAL]
  keywords: ('세종', '대학교', '도서관', '위치')
  query: '세종 대학교 도서관 위치'

[SEMANTIC]
  query: '세종대학교 도서관 위치'

[GRAPH]
  seed_nodes: ('세종', '대학교', '도서관', '위치')
```

> HYBRID는 세 파이프라인을 `ThreadPoolExecutor`로 병렬 실행하여 하나의 `HybridQueryResult`로 묶어 반환합니다.

---

## T-16 — QueryAnalyzer: 빈 문자열 / 공백만 입력

```bash
python - << 'EOF'
from bpmg_korean_nlp import QueryAnalyzer, QueryTarget

class _NoopSpacing:
    def restore(self, text):
        return text

qa = QueryAnalyzer(spacing_restorer=_NoopSpacing())

for text in ['', '   ', '\t\n']:
    for target in [QueryTarget.LEXICAL, QueryTarget.SEMANTIC, QueryTarget.GRAPH]:
        result = qa.analyze(text, target)
        print(f'{repr(text):8} [{target}] -> {result}')
EOF
```

**기대 결과**

```
''       [lexical]  -> LexicalQueryResult(keywords=(), query='')
''       [semantic] -> SemanticQueryResult(query='')
''       [graph]    -> GraphQueryResult(seed_nodes=())
'   '    [lexical]  -> LexicalQueryResult(keywords=(), query='')
'   '    [semantic] -> SemanticQueryResult(query='')
'   '    [graph]    -> GraphQueryResult(seed_nodes=())
'\t\n'   [lexical]  -> LexicalQueryResult(keywords=(), query='')
'\t\n'   [semantic] -> SemanticQueryResult(query='')
'\t\n'   [graph]    -> GraphQueryResult(seed_nodes=())
```

---

## T-17 — QueryAnalyzer: 문자열 타깃 (대소문자 무관)

```bash
python - << 'EOF'
from bpmg_korean_nlp import QueryAnalyzer

class _NoopSpacing:
    def restore(self, text):
        return text

qa = QueryAnalyzer(spacing_restorer=_NoopSpacing())
text = '세종대학교에서일하는중입니다.'

for target_str in ['lexical', 'LEXICAL', 'Lexical', 'lEXICaL']:
    result = qa.analyze(text, target_str)
    print(f'target={repr(target_str):12} -> {type(result).__name__}')
EOF
```

**기대 결과**

```
target='lexical'    -> LexicalQueryResult
target='LEXICAL'    -> LexicalQueryResult
target='Lexical'    -> LexicalQueryResult
target='lEXICaL'    -> LexicalQueryResult
```

---

## T-18 — QueryAnalyzer: 에러 처리

```bash
python - << 'EOF'
from bpmg_korean_nlp import QueryAnalyzer, QueryTarget, InvalidInputError, SpacingModelLoadError

class _NoopSpacing:
    def restore(self, text):
        return text

qa = QueryAnalyzer(spacing_restorer=_NoopSpacing())

try:
    qa.analyze(None, QueryTarget.LEXICAL)
except InvalidInputError as e:
    print(f'None 입력 -> InvalidInputError: {e}')

try:
    qa.analyze('테스트', 'invalid_target')
except InvalidInputError as e:
    print(f'잘못된 타깃 -> InvalidInputError: {e}')

try:
    qa_default = QueryAnalyzer()
except SpacingModelLoadError as e:
    print(f'spacing_restorer 미주입 -> SpacingModelLoadError: {type(e).__name__}')
EOF
```

**기대 결과** (PyKoSpacing 미설치 환경)

```
None 입력 -> InvalidInputError: text must be a str, got NoneType
잘못된 타깃 -> InvalidInputError: ...
spacing_restorer 미주입 -> SpacingModelLoadError: SpacingModelLoadError
```

---

## T-19 — JamoUtils: decompose / compose

```bash
python - << 'EOF'
from bpmg_korean_nlp import decompose, compose

for ch in ['강', '힣', '뷁', '한']:
    r = decompose(ch)
    print(f'decompose({repr(ch)}) -> cho={repr(r.choseong)}, jung={repr(r.jungseong)}, jong={repr(r.jongseong)}')

print()

for cho, jung, jong in [('ㄱ','ㅏ','ㅇ'), ('ㅎ','ㅏ','ㄴ'), ('ㅂ','ㅜ','ㄱ'), ('ㅅ','ㅏ','')]:
    print(f'compose({repr(cho)}, {repr(jung)}, {repr(jong)}) -> {repr(compose(cho, jung, jong))}')

print()

for ch in ['강', '한', '국', '어']:
    r = decompose(ch)
    back = compose(r.choseong, r.jungseong, r.jongseong)
    print(f'{repr(ch)} -> decompose -> compose -> {repr(back)}  (일치: {ch == back})')
EOF
```

**기대 결과**

```
decompose('강') -> cho='ㄱ', jung='ㅏ', jong='ㅇ'
decompose('힣') -> cho='ㅎ', jung='ㅣ', jong='ㅎ'
decompose('뷁') -> cho='ㅂ', jung='ㅞ', jong='ㄺ'
decompose('한') -> cho='ㅎ', jung='ㅏ', jong='ㄴ'

compose('ㄱ', 'ㅏ', 'ㅇ') -> '강'
compose('ㅎ', 'ㅏ', 'ㄴ') -> '한'
compose('ㅂ', 'ㅜ', 'ㄱ') -> '북'
compose('ㅅ', 'ㅏ', '') -> '사'

'강' -> decompose -> compose -> '강'  (일치: True)
'한' -> decompose -> compose -> '한'  (일치: True)
'국' -> decompose -> compose -> '국'  (일치: True)
'어' -> decompose -> compose -> '어'  (일치: True)
```

---

## T-20 — JamoUtils: extract_choseong

```bash
python - << 'EOF'
from bpmg_korean_nlp import extract_choseong

cases = ['안녕하세요', '세종대학교', '한국 NLP', '2024년', '']
for text in cases:
    print(f'extract_choseong({repr(text)}) -> {repr(extract_choseong(text))}')
EOF
```

**기대 결과**

```
extract_choseong('안녕하세요') -> 'ㅇㄴㅎㅅㅇ'
extract_choseong('세종대학교') -> 'ㅅㅈㄷㅎㄱ'
extract_choseong('한국 NLP') -> 'ㅎㄱ NLP'
extract_choseong('2024년') -> '2024ㄴ'
extract_choseong('') -> ''
```

> 한글 음절은 초성만 추출. 영문·숫자·공백·기호는 그대로 유지됩니다.

---

## T-21 — JamoUtils: classify_char

```bash
python - << 'EOF'
from bpmg_korean_nlp import classify_char, CharType

cases = [
    ('가', CharType.HANGUL_SYLLABLE),
    ('힣', CharType.HANGUL_SYLLABLE),
    ('ㄱ', CharType.HANGUL_JAMO),
    ('ㅎ', CharType.HANGUL_JAMO),
    ('國', CharType.HANJA),
    ('A', CharType.LATIN),
    ('z', CharType.LATIN),
    ('0', CharType.NUMBER),
    ('9', CharType.NUMBER),
    (' ', CharType.WHITESPACE),
    ('\t', CharType.WHITESPACE),
    ('\n', CharType.WHITESPACE),
    ('!', CharType.SYMBOL),
    ('.', CharType.SYMBOL),
]
for ch, expected in cases:
    result = classify_char(ch)
    status = 'OK' if result == expected else f'FAIL (got {result})'
    print(f'classify_char({repr(ch):4}) -> {str(result):20} [{status}]')
EOF
```

**기대 결과**

```
classify_char('가') -> hangul_syllable      [OK]
classify_char('힣') -> hangul_syllable      [OK]
classify_char('ㄱ') -> hangul_jamo          [OK]
classify_char('ㅎ') -> hangul_jamo          [OK]
classify_char('國') -> hanja               [OK]
classify_char('A' ) -> latin               [OK]
classify_char('z' ) -> latin               [OK]
classify_char('0' ) -> number              [OK]
classify_char('9' ) -> number              [OK]
classify_char(' ' ) -> whitespace          [OK]
classify_char('\t') -> whitespace          [OK]
classify_char('\n') -> whitespace          [OK]
classify_char('!' ) -> symbol              [OK]
classify_char('.' ) -> symbol              [OK]
```

---

## T-22 — Stopwords: 불용어 집합

```bash
python - << 'EOF'
from bpmg_korean_nlp import DEFAULT_STOPWORDS, merge_stopwords

print('type:', type(DEFAULT_STOPWORDS).__name__)
print('크기:', len(DEFAULT_STOPWORDS))

try:
    DEFAULT_STOPWORDS.add('테스트')
except AttributeError as e:
    print('불변 확인: add 불가 ->', type(e).__name__)

print()
for word in ['은', '는', '이', '가', '을', '를', '에서', '세종', '대학교']:
    print(f'  {repr(word):8} in DEFAULT_STOPWORDS: {word in DEFAULT_STOPWORDS}')

print()
merged = merge_stopwords({'커스텀', '단어'})
print('merge 후 크기:', len(merged))
print('커스텀 포함:', '커스텀' in merged)
print('원본 유지:', len(DEFAULT_STOPWORDS))
EOF
```

**기대 결과**

```
type: frozenset
크기: 155
불변 확인: add 불가 -> AttributeError

  '은'       in DEFAULT_STOPWORDS: True
  '는'       in DEFAULT_STOPWORDS: True
  '이'       in DEFAULT_STOPWORDS: True
  '가'       in DEFAULT_STOPWORDS: True
  '을'       in DEFAULT_STOPWORDS: True
  '를'       in DEFAULT_STOPWORDS: True
  '에서'      in DEFAULT_STOPWORDS: True
  '세종'      in DEFAULT_STOPWORDS: False
  '대학교'     in DEFAULT_STOPWORDS: False

merge 후 크기: 157
커스텀 포함: True
원본 유지: 155
```

---

## T-23 — PII: QueryAnalyzer 2차 차단

```bash
python - << 'EOF'
from bpmg_korean_nlp import QueryAnalyzer, QueryTarget, PII_PATTERNS, PIIDetectedError

class _NoopSpacing:
    def restore(self, text):
        return text

analyzer = QueryAnalyzer(spacing_restorer=_NoopSpacing())

print('PII 패턴 목록:')
for p in PII_PATTERNS:
    print(f'  {p.name:20} {p.description}')

print()
cases = [
    ('정상 쿼리',           '세종대학교 도서관 위치',          False),
    ('주민등록번호',         '주민번호 900101-1234567',        True),
    ('휴대전화',             '연락처 010-1234-5678',           True),
    ('사업자번호',           '사업자 123-45-67890',            True),
    ('외국인번호',           '외국인 900101-5234567',          True),
    ('복수 패턴',            '900101-1234567 / 010-9999-8888', True),
    ('빈 문자열',            '',                               False),
]
for desc, text, should_block in cases:
    try:
        analyzer.analyze(text, QueryTarget.LEXICAL)
        blocked = False
        matched = []
    except PIIDetectedError as e:
        blocked = True
        matched = e.matched
    status = 'PASS' if blocked == should_block else 'FAIL'
    suffix = f' matched={matched}' if matched else ''
    print(f'  {status}: {desc}{suffix}')
EOF
```

**기대 결과**

```
PII 패턴 목록:
  resident_id          주민등록번호
  mobile_phone         휴대전화 번호
  business_id          사업자등록번호
  foreign_id           외국인등록번호

  PASS: 정상 쿼리
  PASS: 주민등록번호 matched=['resident_id']
  PASS: 휴대전화 matched=['mobile_phone']
  PASS: 사업자번호 matched=['business_id']
  PASS: 외국인번호 matched=['foreign_id']
  PASS: 복수 패턴 matched=['resident_id', 'mobile_phone']
  PASS: 빈 문자열
```

---

## T-24 — MeCab 점검: check_mecab_dict

```bash
python - << 'EOF'
from bpmg_korean_nlp import check_mecab_dict

result = check_mecab_dict()
print('available:', result.available)
print('dict_path:', result.dict_path)
print('version  :', result.version)
print('type     :', type(result).__name__)

bad = check_mecab_dict('/nonexistent/path')
print()
print('잘못된 경로:')
print('  available:', bad.available)
print('  dict_path:', bad.dict_path)
EOF
```

**기대 결과**

```
available: True
dict_path: /opt/homebrew/lib/mecab/dic/mecab-ko-dic
version  : None
type     : DictCheckResult

잘못된 경로:
  available: False
  dict_path: /nonexistent/path
```

---

## 전체 자동화 테스트 실행

```bash
# 전체 (PyKoSpacing 없는 환경에서 51개 스킵 예상)
pytest tests/ -v

# 커버리지 포함
pytest tests/ --cov=src --cov-report=term-missing

# 특정 모듈만
pytest tests/test_normalizer.py -v
pytest tests/test_tokenizer.py -v
pytest tests/test_query_analyzer.py -v
pytest tests/test_jamo_utils.py -v
```

**예상 결과** (PyKoSpacing 미설치 환경)

```
271 passed, 51 skipped in ~1s
```

스킵된 51개는 `PyKoSpacing not installed` 사유이며 정상입니다.