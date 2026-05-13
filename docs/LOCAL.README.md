# 로컬 개발환경 구축 가이드

이 문서는 `korean-nlp-core` 레포를 **처음 클론한 개발자**가 macOS 환경에서 로컬 개발을 시작하기 위한 단계별 가이드입니다.

> Ubuntu / Docker 환경은 별도 가이드를 참고하세요.
> - [docs/INSTALL.MACOS.md](./INSTALL.MACOS.md) — macOS 설치 가이드 (SDK 소비자용)
> - [docs/INSTALL.UBUNTU.md](./INSTALL.UBUNTU.md) — Ubuntu 22.04 설치 가이드
> - [docs/INSTALL.DOCKER.md](./INSTALL.DOCKER.md) — Docker 설치 가이드

---

## 전제조건

| 항목 | 요구사항 | 확인 명령 |
|---|---|---|
| OS | macOS (Apple Silicon / Intel 공통) | `uname -a` |
| Homebrew | 설치 필요 | `brew --version` |
| Python | 3.12 (pyenv 권장) | `python3 --version` |
| Git | 설치 필요 | `git --version` |

### Homebrew가 없다면

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

설치 후 셸 재시작 또는 PATH 반영:

```bash
# Apple Silicon
eval "$(/opt/homebrew/bin/brew shellenv)"
# Intel Mac
eval "$(/usr/local/bin/brew shellenv)"
```

---

## Step 1 — 레포 클론

```bash
git clone <레포_URL> korean-nlp-core
cd korean-nlp-core
```

`pwd` 결과가 `.../korean-nlp-core`인지 확인하세요. 이후 모든 명령은 이 디렉토리에서 실행합니다.

---

## Step 2 — Python 3.12 확인

```bash
python3 --version
# Python 3.12.x  → 정상
# Python 3.11.x 이하 → pyenv로 설치 필요
```

### pyenv로 Python 3.12 설치 (필요 시)

pyenv는 여러 Python 버전을 프로젝트별로 격리해 관리합니다. 이미 시스템에 Python 3.12가 있으면 이 단계는 건너뛰세요.

```bash
# pyenv 설치
brew install pyenv

# 셸 초기화 (zsh 기준 — 한 번만 실행)
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
source ~/.zshrc

# Python 3.12 설치 + 프로젝트에 고정
pyenv install 3.12
pyenv local 3.12

# 다시 확인
python3 --version
# → Python 3.12.x
```

---

## Step 3 — MeCab 시스템 패키지 설치 (macOS)

본 SDK는 한국어 특화 MeCab(`mecab-ko`) + 한국어 사전(`mecab-ko-dic`)을 필수로 사용합니다.

```bash
brew install mecab-ko mecab-ko-dic
```

### 이미 일반 `mecab`이 설치된 경우

일반 `mecab`은 일본어용 사전과 묶여 있어 한국어 분석에 사용할 수 없습니다. 충돌이 발생하면 제거 후 다시 설치하세요.

```bash
brew uninstall mecab
brew install mecab-ko mecab-ko-dic
```

설치 확인:

```bash
mecab --version
# → mecab of 0.996/ko-x.x.x (또는 유사 메시지)

ls /opt/homebrew/lib/mecab/dic/mecab-ko-dic 2>/dev/null \
  || ls /usr/local/lib/mecab/dic/mecab-ko-dic
# → dicrc, sys.dic 등이 보이면 정상
```

> Apple Silicon(M1/M2/...)은 `/opt/homebrew/...`, Intel Mac은 `/usr/local/...` 경로를 사용합니다.

---

## Step 4 — 가상환경 생성 및 활성화

프로젝트 디렉토리에서 Python 3.12 가상환경을 만들고 활성화합니다.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

활성화 확인:

```bash
which python
# → .../korean-nlp-core/.venv/bin/python

python --version
# → Python 3.12.x
```

> 이후 새 터미널을 열 때마다 `source .venv/bin/activate`를 다시 실행해야 합니다.

---

## Step 5 — 패키지 설치 (개발 의존성 포함)

개발용 의존성(pytest, mypy, ruff 등)까지 설치합니다.

```bash
pip install -e ".[dev]"
```

`uv`를 사용하는 경우:

```bash
uv pip install -e ".[dev]"
```

설치되는 주요 항목:
- `bpmg_korean_nlp` (editable install)
- `python-mecab-ko` (MeCab Python 바인딩)
- `soynlp` (반복 문자 정규화)
- 개발 도구: `pytest`, `pytest-cov`, `mypy`, `ruff`, `build`

---

## Step 6 — 설치 확인

공개 API 심볼이 정상적으로 로드되는지 확인합니다.

```bash
python -c "import bpmg_korean_nlp; print(len(bpmg_korean_nlp.__all__), '개 심볼 로드됨')"
```

**기대 출력**

```
27 개 심볼 로드됨
```

심볼 전체 목록을 보고 싶다면:

```bash
python -c "import bpmg_korean_nlp; print(bpmg_korean_nlp.__all__)"
```

---

## Step 7 — MeCab 사전 확인

SDK가 한국어 사전 경로를 올바르게 인식하는지 점검합니다.

```bash
python -c "from bpmg_korean_nlp import check_mecab_dict; r=check_mecab_dict(); print('사전 사용 가능:', r.available, '경로:', r.dict_path)"
```

**기대 출력**

```
사전 사용 가능: True 경로: /opt/homebrew/lib/mecab/dic/mecab-ko-dic
```

> `사용 가능: False`가 출력된다면 Step 3을 다시 확인하세요. 특히 일반 `mecab`이 잔존해 있거나, Intel/Apple Silicon 경로 혼선이 가장 흔한 원인입니다.

---

## Step 8 — 첫 테스트 실행

```bash
pytest tests/ -q
```

**기대 출력**

```
261 passed, 2 skipped
```

> 스킵 2건은 MeCab이 설치된 환경에서 `MeCab 미설치 시 동작`을 검증하는 테스트(`test_missing_binding_raises`, `test_missing_binding_reports_unavailable`)가 정상 스킵됩니다. `@pytest.mark.slow` 테스트가 포함되면 통과 건수가 더 많아집니다. 더 자세한 테스트 절차는 [LOCAL.TEST.md](./LOCAL.TEST.md)를 참고하세요.

---

## 개발 명령어 요약

| 명령 | 용도 |
|---|---|
| `source .venv/bin/activate` | 가상환경 활성화 (새 터미널마다) |
| `pip install -e ".[dev]"` | 개발 의존성 포함 재설치 |
| `pytest tests/ -v` | 전체 테스트 실행 |
| `pytest tests/ --cov=src --cov-report=term-missing` | 커버리지 포함 테스트 |
| `pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=90` | 커버리지 90% 미만 시 실패 |
| `pytest tests/test_normalizer.py -v` | 단일 모듈 테스트 |
| `ruff format src tests` | 코드 포맷팅 |
| `ruff check src tests --fix` | 린트 + 자동 수정 |
| `mypy --strict src/ tests/` | 타입 검사 |
| `python scripts/check_imports.py src/` | 금지 import 검사 |
| `python -m build` | wheel + sdist 빌드 |
| `rm -rf dist/ build/ .coverage htmlcov/ .mypy_cache/ .ruff_cache/ .pytest_cache/` | 빌드/캐시 정리 |

---

## 빠른 동작 확인 (선택)

설치 후 간단한 사용 예시를 즉시 돌려볼 수 있습니다.

```python
from bpmg_korean_nlp import KoreanNormalizer, MeCabTokenizer, QueryAnalyzer, QueryTarget

# 정규화
norm = KoreanNormalizer.default()
print(norm.normalize("안녕하세요ㅋㅋㅋㅋ   세종!!!"))
# → "안녕하세요ㅋㅋ 세종!!!"

# 형태소 분석
tok = MeCabTokenizer()
print(tok.tokenize("세종대학교에서 한국어 NLP를 연구한다"))
# → ['세종', '대학교', '에서', '한국어', 'NLP', '를', '연구', '한다']

# 쿼리 변환
qa = QueryAnalyzer()
print(qa.analyze("조사랑 어미 차이가 뭐예요", QueryTarget.LEXICAL))
# → LexicalQueryResult(keywords=('조사', '어미', '차이', '뭐', '예요'), query='조사 어미 차이 뭐 예요')
```

---

## 환경별 추가 가이드

| 환경 | 가이드 |
|---|---|
| macOS (SDK 소비자용) | [docs/INSTALL.MACOS.md](./INSTALL.MACOS.md) |
| Ubuntu (apt 기반) | [docs/INSTALL.UBUNTU.md](./INSTALL.UBUNTU.md) |
| Docker (컨테이너 빌드) | [docs/INSTALL.DOCKER.md](./INSTALL.DOCKER.md) |
| 로컬 테스트 실행 | [docs/LOCAL.TEST.md](./LOCAL.TEST.md) |
