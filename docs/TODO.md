# TODO.md

명세(`02_bpmg-korean-nlp_명세.md`) 대비 구현 검토 결과에서 도출된 미완 항목 및 확인 필요 사항.

---

## 상태 범례

| 기호 | 의미 |
|---|---|
| `[ ]` | 미완료 |
| `[x]` | 완료 |
| `[?]` | 담당자 판단 필요 |

---

## 1. 명세 §9 완료 정의 — 미수행 항목

### [ ] 어댑터 30줄 sanity check
- **근거**: 명세 §9 마지막 항목, §13.6
  > "세종 retrieval-engine 개발 담당자가 어댑터를 한 번 만들어 본 결과 30줄 안팎으로 끝났는지 sanity check"
- **작업**: `retrieval-engine` 측에서 `MeCabTokenizer`를 `retrieval-core`의 토크나이저 인터페이스에 끼워 맞추는 어댑터를 실제로 작성
- **판단 기준**: 어댑터가 30줄을 초과하면 본 SDK에 빠진 추상화가 있다는 신호 → 프로젝트 설계 담당자에게 보고
- **담당**: 세종 retrieval-engine 개발 담당자

---

### [ ] Ubuntu 22.04 설치 절차 실제 검증
- **근거**: 명세 §9
  > "mecab-ko-dic 설치 절차 검증 (macOS / Ubuntu 22.04 / Docker 슬림)"
- **현황**: `README.md`에 Ubuntu 설치 절차가 기술되어 있으나 실환경에서 검증된 적 없음
- **작업**: Ubuntu 22.04 환경에서 아래 절차 실행 후 `pip install bpmg-korean-nlp` + `pytest` 통과 확인
  ```bash
  sudo apt-get update
  sudo apt-get install -y mecab libmecab-dev mecab-ipadic-utf8
  # mecab-ko-dic 별도 설치 또는 wheel 번들 사전 사용
  pip install bpmg-korean-nlp
  python -c "from bpmg_korean_nlp import MeCabTokenizer; print(MeCabTokenizer().tokenize('테스트'))"
  ```
- **완료 기준**: 오류 없이 토크나이징 결과 출력

---

### [ ] Docker slim 설치 절차 실제 검증
- **근거**: 명세 §9
- **현황**: `README.md`에 Dockerfile 예시가 있으나 실제 빌드·실행 미검증
- **작업**: 아래 Dockerfile로 이미지 빌드 후 동작 확인
  ```dockerfile
  FROM python:3.12-slim
  RUN apt-get update && apt-get install -y --no-install-recommends \
          mecab libmecab-dev mecab-ipadic-utf8 build-essential \
      && rm -rf /var/lib/apt/lists/*
  RUN pip install bpmg-korean-nlp
  ```
- **완료 기준**: 컨테이너 내 `MeCabTokenizer().tokenize('테스트')` 정상 출력
- **비고**: mecab-ko-dic을 Docker 이미지 안에 번들하는 방법도 함께 검토 필요

---

## 2. 설계 담당자 판단 필요 항목

### [?] soynlp 런타임 의존성 — 명세 §3과의 해석 여지
- **근거**: 명세 §3
  > "KoNLPy 전체·soynlp 같은 추가 형태소 라이브러리 의존 — mecab-ko-dic 단일 의존으로 단순화"
- **현황**: `normalizer.py`에서 `soynlp.normalizer.repeat_normalize`를 **반복 문자 축약** 용도로 사용 중. `pyproject.toml`의 runtime dependencies에 `soynlp` 포함
- **판단 필요 이유**: 금지 의도가 "soynlp를 형태소 분석기로 사용하지 말 것"인지, "soynlp 자체를 의존하지 말 것"인지에 따라 결론이 달라짐
- **선택지**

  | 선택 | 내용 | 영향 |
  |---|---|---|
  | A. 유지 | soynlp 의존 허용으로 해석, 현행 유지 | 없음 |
  | B. 제거 | soynlp 제거, `repeat_normalize` 로직 직접 구현 | 정규화 로직 재작성 필요, 의존성 1개 감소 |

- **담당**: 프로젝트 설계 담당자 최종 결정

---

## 3. 명세 외 추가 구현 — 범위 확인

명세 §2에 정의되지 않았으나 구현에 포함된 기능들입니다. 명세 위반은 아니지만, 유지 여부를 명시적으로 확인해 두는 것이 좋습니다.

### [?] QueryAnalyzer (LEXICAL / SEMANTIC / GRAPH / HYBRID)
- **파일**: `src/bpmg_korean_nlp/query_analyzer.py`
- **내용**: 쿼리를 4가지 검색 타깃 표현으로 변환하는 파이프라인
- **명세 언급**: 없음 (명세 §2에 미포함)
- **확인 사항**: retrieval-engine 어댑터 설계에서 필요한 기능인지, 본 SDK에 두는 것이 적절한지 설계 담당자 판단

### [?] SpacingRestorer (PyKoSpacing 기반)
- **파일**: `src/bpmg_korean_nlp/spacing.py`
- **내용**: PyKoSpacing 딥러닝 모델을 통한 띄어쓰기 복원
- **명세 언급**: 없음
- **특이사항**: PyKoSpacing이 PyPI 미배포 패키지이므로 런타임 의존 추가에 주의 필요
- **확인 사항**: 본 SDK의 책임 범위에 포함할지 설계 담당자 판단

### [?] extract_choseong()
- **파일**: `src/bpmg_korean_nlp/jamo_utils.py`
- **내용**: 한글 문자열의 초성만 추출
- **명세 언급**: §2.3에는 "음절 분리·결합", "글자 종류 분류"만 명시. 초성 추출은 미언급
- **확인 사항**: 유지 여부 (자모 유틸리티의 자연스러운 확장으로 볼 수 있음)

---

## 4. 완료 확인 항목 (참고)

명세 §9 완료 정의 기준으로 코드 레벨 항목은 모두 충족된 상태입니다.

| 항목 | 결과 |
|---|---|
| §2 전체 책임 구현 | ✅ |
| 단위 검증 커버리지 90% 이상 | ✅ 97.27% |
| 골든셋 100건 이상 통과 | ✅ 110건 |
| macOS 설치 절차 검증 | ✅ (로컬 실증) |
| CI import 자동 차단 | ✅ `scripts/check_imports.py` |
| `mypy --strict` 통과 | ✅ 13 files, no issues |
| 성능 p99 < 5ms | ✅ 0.18ms |
| 성능 1000건 < 2초 | ✅ 0.15초 |
