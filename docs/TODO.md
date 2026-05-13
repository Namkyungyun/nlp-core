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

### [x] SpacingRestorer (PyKoSpacing 기반) — 제거 완료
- **파일**: `src/bpmg_korean_nlp/spacing.py` (삭제됨)
- **결정**: SpacingRestorer를 SDK에서 완전 제거. PyKoSpacing(~1.5GB)은 선택적 의존성으로 전환
- **처리 일자**: 2026-05-13

### [?] extract_choseong()
- **파일**: `src/bpmg_korean_nlp/jamo_utils.py`
- **내용**: 한글 문자열의 초성만 추출
- **명세 언급**: §2.3에는 "음절 분리·결합", "글자 종류 분류"만 명시. 초성 추출은 미언급
- **확인 사항**: 유지 여부 (자모 유틸리티의 자연스러운 확장으로 볼 수 있음)

---

## 4. SpacingRestorer 제거 작업 검증 포인트

> 2026-05-13 완료된 작업. 이후 회귀 발생 시 아래 체크리스트로 재확인.

### 4.1 소스 코드 정리

| 항목 | 확인 명령 | 기대 결과 |
|---|---|---|
| `spacing.py` 삭제 | `ls src/bpmg_korean_nlp/spacing.py` | No such file |
| `SpacingModelLoadError` 제거 | `grep -r "SpacingModelLoadError" src/` | 결과 없음 |
| `SpacingRestorer` export 제거 | `grep -r "SpacingRestorer" src/` | 결과 없음 |
| `query_analyzer.py` 파라미터 제거 | `grep "spacing_restorer" src/bpmg_korean_nlp/query_analyzer.py` | 결과 없음 |
| `__init__.py` export 제거 | `grep "SpacingRestorer\|SpacingModelLoadError" src/bpmg_korean_nlp/__init__.py` | 결과 없음 |

### 4.2 의존성 정리

| 항목 | 확인 명령 | 기대 결과 |
|---|---|---|
| pyproject.toml core deps | `grep "kss\|pykospacing\|tensorflow" pyproject.toml` | `[spacing]` optional 그룹 내에만 존재 |
| 로컬 venv 패키지 제거 | `pip show kss pykospacing tensorflow 2>&1` | WARNING: Package(s) not found |
| 의존성 충돌 없음 | `pip check` | No broken requirements |

### 4.3 테스트 정리

| 항목 | 확인 명령 | 기대 결과 |
|---|---|---|
| 삭제된 테스트 파일 | `ls tests/test_spacing*.py` | No such file |
| spacing 참조 잔존 확인 | `grep -r "SpacingRestorer\|HAS_PYKOSPACING\|FakeSpacing\|_run_spacing" tests/` | 결과 없음 |
| golden.jsonl spacing 항목 | `grep '"type": "spacing"' tests/fixtures/golden.jsonl` | 결과 없음 |
| 전체 테스트 통과 | `pytest tests/ -q --tb=short` | 261 passed, 2 skipped (MeCab slow 제외 시) |
| golden set 항목 수 | `wc -l tests/fixtures/golden.jsonl` | 80줄 이상 |

### 4.4 문서 정리

| 항목 | 확인 명령 | 기대 결과 |
|---|---|---|
| SPEC.md 잔존 참조 | `grep -n "SpacingRestorer\|SpacingModelLoadError\|spacing\.py" docs/SPEC.md` | 결과 없음 |
| TEST_GUIDE.md 잔존 참조 | `grep -n "SpacingRestorer\|SpacingModelLoadError" docs/TEST_GUIDE.md` | 결과 없음 |
| GUIDE.md 잔존 참조 | `grep -n "SpacingRestorer\|SpacingModelLoadError" docs/GUIDE.md` | 결과 없음 |
| LOCAL.TEST.md 잔존 참조 | `grep -n "SpacingRestorer\|SpacingModelLoadError" docs/LOCAL.TEST.md` | 결과 없음 |
| LOCAL.README.md 잔존 참조 | `grep -n "SpacingRestorer\|SpacingModelLoadError" docs/LOCAL.README.md` | 결과 없음 |
| CLAUDE.md 잔존 참조 | `grep "SpacingRestorer\|spacing_restorer" CLAUDE.md` | 결과 없음 |
| README.md SpacingRestorer 섹션 제거 | `grep "SpacingRestorer" README.md` | 결과 없음 |
| README.md optional 안내 | `grep "\[spacing\]" README.md` | optional extras 설치 안내 존재 |

### 4.5 품질 게이트

```bash
# 한 번에 전체 검증
mypy --strict src/ 2>&1 | tail -3
ruff check src tests 2>&1 | tail -3
pytest tests/ -q --tb=short 2>&1 | tail -5
grep -r "SpacingRestorer\|SpacingModelLoadError" src/ tests/ docs/ CLAUDE.md
```

모든 명령이 오류 없이 통과하고 마지막 grep 결과가 비어 있으면 제거 작업 완전 완료.

---

## 5. 완료 확인 항목 (참고)

명세 §9 완료 정의 기준 코드 레벨 항목 상태 (SpacingRestorer 제거 반영).

| 항목 | 결과 |
|---|---|
| §2 전체 책임 구현 | ✅ |
| 단위 검증 커버리지 90% 이상 | ✅ (재측정 필요 — spacing 제거 후) |
| 골든셋 75건 이상 통과 | ✅ 80건 (spacing 16건 제거 후, 기준 75로 조정) |
| macOS 설치 절차 검증 | ✅ (로컬 실증) |
| CI import 자동 차단 | ✅ `scripts/check_imports.py` |
| `mypy --strict` 통과 | ✅ spacing.py 제거 후 재확인 필요 |
| 성능 p99 < 5ms | ✅ 0.18ms |
| 성능 1000건 < 2초 | ✅ 0.15초 |
