# bpmg-korean-nlp 빠른 시작

`bpmg-korean-nlp`는 한국어 검색·NLP 파이프라인의 **전처리 계층**을 담당하는
Python SDK입니다. 텍스트 정규화, MeCab 형태소 분석, 쿼리 변환(LEXICAL/SEMANTIC/GRAPH/HYBRID)
세 가지 핵심 기능을 5분 안에 둘러보세요.

## 설치

```bash
pip install bpmg-korean-nlp
```

`MeCabTokenizer`는 시스템 MeCab 사전이 필요합니다.

- **macOS**: `brew install mecab mecab-ko mecab-ko-dic`
- **Ubuntu 22.04**: [INSTALL.UBUNTU.md](INSTALL.UBUNTU.md) 참고
- **Docker**: [INSTALL.DOCKER.md](INSTALL.DOCKER.md) 참고

---

## 핵심 기능 3가지

### 1. 텍스트 정규화 (`KoreanNormalizer`)

NFC, 유니코드 공백 통일, 반복 문자 축약(`ㅋㅋㅋㅋㅋ` → `ㅋㅋ`)을 한 번에 처리합니다.
색인 전처리에는 `strip_noise=True`로 구두점·이모지·자모 감탄사까지 제거하세요.

```python
from bpmg_korean_nlp import KoreanNormalizer

norm = KoreanNormalizer()
norm.normalize("안녕하세요ㅋㅋㅋㅋㅋㅋ   세종!!!")
# → '안녕하세요ㅋㅋ 세종!!!'

norm_strip = KoreanNormalizer(strip_noise=True)
norm_strip.normalize("세종대 도서관!!! ㅋㅋ 위치 알려줘 :)")
# → '세종대 도서관 위치 알려줘'
```

### 2. 형태소 분석 (`MeCabTokenizer`)

사전 로딩 비용이 크므로 SDK 내부에서 싱글톤으로 관리됩니다. BM25용
표층형 토큰은 `tokenize()`, 품사·오프셋이 필요한 분석은 `analyze()`를 쓰세요.

```python
from bpmg_korean_nlp import MeCabTokenizer

tok = MeCabTokenizer()

tok.tokenize("세종대학교에서 한국어 NLP를 연구한다")
# → ['세종', '대학교', '에서', '한국어', 'NLP', '를', '연구', '한다']

tok.analyze("한국어 NLP")
# → [MorphToken(surface='한국어', lemma='한국어', pos='NNG', start=0, end=3),
#    MorphToken(surface='NLP',  lemma='NLP',  pos='SL',  start=4, end=7)]
```

### 3. 쿼리 변환 (`QueryAnalyzer`)

원시 쿼리를 4가지 검색 타깃 표현으로 한 번에 변환합니다. 점수 계산이나
검색 실행은 하지 않는, 순수 변환 레이어입니다.

```python
from bpmg_korean_nlp import QueryAnalyzer, QueryTarget, analyze_query

analyzer = QueryAnalyzer()
text = "세종대학교 도서관 위치"

analyzer.analyze(text, QueryTarget.LEXICAL)   # BM25 키워드 묶음
analyzer.analyze(text, QueryTarget.SEMANTIC)  # 벡터 임베딩용 자연문
analyzer.analyze(text, QueryTarget.GRAPH)     # 그래프 시드 노드(명사만)
analyzer.analyze(text, QueryTarget.HYBRID)    # 위 세 결과를 병렬로 합산

# 모듈 레벨 단축 함수 — 기본 싱글톤 재사용
analyze_query(text, QueryTarget.LEXICAL)
```

---

## 자주 쓰는 패턴

### retrieval-engine 어댑터 패턴

이 SDK의 주 소비자는 `retrieval-engine`입니다. 색인·검색 양쪽 흐름에서
`preprocess`에는 `strip_noise=True`를 쓰는 것이 핵심입니다 — 자모 감탄사가
BM25 토큰으로 새어 들어가는 것을 막기 위함입니다.

```python
from bpmg_korean_nlp import (
    KoreanNormalizer,
    MeCabTokenizer,
    QueryAnalyzer,
    QueryTarget,
    QueryResult,
)


class KoreanNlpAdapter:
    """retrieval-engine ↔ bpmg-korean-nlp 어댑터."""

    def __init__(self) -> None:
        self._preprocessor = KoreanNormalizer(strip_noise=True)
        self._tokenizer = MeCabTokenizer()
        self._query = QueryAnalyzer()

    def preprocess(self, text: str) -> str:
        """문서 색인 전 정규화 + 노이즈 제거."""
        return self._preprocessor.normalize(text)

    def tokenize_for_bm25(self, text: str) -> list[str]:
        """BM25 색인용 표층형 토큰 리스트."""
        return self._tokenizer.tokenize(self.preprocess(text))

    def analyze_query(
        self,
        text: str,
        target: QueryTarget = QueryTarget.HYBRID,
    ) -> QueryResult:
        """검색어를 LEXICAL/SEMANTIC/GRAPH/HYBRID 형태로 변환."""
        return self._query.analyze(text, target)
```

이 어댑터는 의도적으로 30줄 안쪽으로 유지됩니다 — 더 길어진다면 SDK에
누락된 추상화가 있다는 신호입니다.

---

## 더 알아보기

- 전체 API 레퍼런스 (모든 인자·예외·필드 설명): [GUIDE.TEST.md](GUIDE.TEST.md)
- 로컬 개발 환경 셋업: [LOCAL.README.md](LOCAL.README.md)
- 기능 명세·정책: [SPEC.md](SPEC.md)
