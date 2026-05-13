# Ubuntu 22.04 설치 가이드

`bpmg-korean-nlp`을 Ubuntu 22.04에서 설치하고 동작을 확인하는 가이드입니다.

> **핵심 요약** — Ubuntu에서는 `pip install bpmg-korean-nlp` 한 줄이면 됩니다.
>
> **이유 (두 가지)**
> 1. `python-mecab-ko`는 Linux용으로 **`manylinux` 규격 wheel**을 제공합니다.
>    이 wheel 안에는 `auditwheel repair`로 **MeCab C 런타임 라이브러리(`libmecab.so`)
>    가 번들**되어 있습니다. 시스템에 `mecab`을 apt로 별도 설치하지 않아도 됩니다.
> 2. `python-mecab-ko-dic` 패키지가 **한국어 사전 데이터**를 포함하여 함께 설치됩니다.
>
> 따라서 `mecab-ipadic-utf8`(일본어 사전) 등 시스템 MeCab 패키지는 **필요하지 않습니다.**

---

## 1. 전제조건

| 항목 | 요구사항 |
|---|---|
| **OS** | Ubuntu 22.04 LTS 이상 (24.04 / Debian 12 동일) |
| **Python** | 3.12 이상 |
| **권한** | `sudo` 사용 가능한 일반 계정 |
| **네트워크** | PyPI 접근 가능 |

설치된 Python 버전을 먼저 확인합니다.

```bash
python3 --version
```

3.12 미만이거나 설치되어 있지 않다면 다음 절을 참고해 Python 3.12를 설치합니다.

---

## 2. Python 3.12 설치

Ubuntu 22.04의 기본 Python은 3.10입니다. 다음 두 방법 중 하나로 3.12를 설치합니다.

### 2-A. deadsnakes PPA 사용 (권장 — 시스템 전역)

```bash
sudo apt-get update
sudo apt-get install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv python3.12-dev
```

설치 확인:

```bash
python3.12 --version
```

### 2-B. pyenv 사용 (사용자 단위 — 여러 버전 병행)

```bash
# pyenv 빌드 의존성
sudo apt-get update
sudo apt-get install -y make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev curl libncursesw5-dev \
    xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

# pyenv 설치
curl -fsSL https://pyenv.run | bash

# 셸 설정 (~/.bashrc 또는 ~/.zshrc)
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# Python 3.12 설치
pyenv install 3.12.7
pyenv global 3.12.7
```

---

## 3. 가상환경 생성

프로젝트 디렉터리를 만들고 가상환경을 생성합니다.

```bash
mkdir -p ~/work/korean-nlp-demo
cd ~/work/korean-nlp-demo

python3.12 -m venv .venv
source .venv/bin/activate

# pip 최신화 (선택)
python -m pip install --upgrade pip
```

이후 명령은 모두 가상환경이 활성화된 상태(`(.venv)` 프롬프트)에서 실행합니다.

---

## 4. `bpmg-korean-nlp` 설치 — 한 줄

```bash
pip install bpmg-korean-nlp
```

이 한 줄이 다음을 모두 수행합니다.

- `bpmg-korean-nlp` 본체
- `python-mecab-ko` (MeCab Python 바인딩)
- `python-mecab-ko-dic` (**한국어 사전 번들** — wheel에 포함되어 함께 설치됨)
- `soynlp`, `regex` 등 기타 런타임 의존성

따라서 Ubuntu에서는 `sudo apt-get install mecab ...` 같은 시스템 패키지 설치 단계가
필요하지 않습니다.

> **한자→한글 변환 옵션**이 필요한 경우(기본 OFF):
>
> ```bash
> pip install "bpmg-korean-nlp[hanja]"
> ```

---

## 5. 동작 확인 — 사전 가용성

설치가 끝나면 MeCab 사전이 정상적으로 잡혔는지 한 줄로 확인합니다.

```bash
python -c "from bpmg_korean_nlp import check_mecab_dict; print(check_mecab_dict())"
```

`available=True`와 사전 경로가 출력되면 성공입니다.

```
DictCheckResult(available=True, dict_path='/.../site-packages/mecab_ko_dic/dicdir', ...)
```

---

## 6. 샘플 코드 실행

간단한 정규화 / 토큰화 / 쿼리 분석 코드로 전체 파이프라인을 확인합니다.

```bash
python - <<'PY'
from bpmg_korean_nlp import (
    KoreanNormalizer,
    MeCabTokenizer,
    QueryAnalyzer,
    QueryTarget,
)

normalizer = KoreanNormalizer()
text = normalizer.normalize("안녕하세요ㅋㅋㅋㅋㅋㅋ   세종!!!")
print("normalize :", text)

tokenizer = MeCabTokenizer()
print("tokens    :", tokenizer.tokenize("세종대학교에서 한국어 NLP를 연구한다"))

analyzer = QueryAnalyzer()
print("lexical   :", analyzer.analyze("세종대학교 도서관 위치", QueryTarget.LEXICAL))
PY
```

토큰 리스트와 어휘 쿼리 결과가 출력되면 환경 구축이 끝난 것입니다.

---

## 7. 문제해결

### 7-1. `pip install` 중 C 컴파일 오류가 나는 경우

대부분의 환경에서는 미리 빌드된 wheel을 받기 때문에 컴파일이 일어나지 않습니다.
드물게 wheel이 없는 플랫폼/아키텍처에서 sdist를 받아 직접 빌드하다 실패하는 경우,
다음 시스템 패키지를 설치한 뒤 재시도하세요.

```bash
sudo apt-get update
sudo apt-get install -y build-essential libmecab-dev
pip install --no-cache-dir --force-reinstall bpmg-korean-nlp
```

- `build-essential` — `gcc`, `g++`, `make` 등 C/C++ 빌드 도구
- `libmecab-dev` — MeCab C++ 헤더/라이브러리 (Python 확장 빌드 시 필요)

### 7-2. `check_mecab_dict()`가 `available=False`로 나오는 경우

`python-mecab-ko-dic`이 어떤 이유로 함께 설치되지 않은 경우입니다. 명시적으로
재설치하세요.

```bash
pip install --upgrade --force-reinstall python-mecab-ko python-mecab-ko-dic
```

### 7-3. `ModuleNotFoundError: bpmg_korean_nlp`

가상환경 활성화가 풀린 상태에서 다른 Python 인터프리터로 실행했을 가능성이 큽니다.

```bash
which python
which pip
```

두 경로가 모두 `.venv/bin/`을 가리키는지 확인합니다.

### 7-4. 일본어 사전(`mecab-ipadic-utf8`)을 설치한 경우

이 패키지는 본 SDK와 **무관합니다.** 충돌은 없지만 디스크 공간만 차지하므로
필요 없다면 제거해도 좋습니다.

```bash
sudo apt-get remove -y mecab-ipadic-utf8
```

---

## 다음 단계

- API 사용법: [`GUIDE.md`](../GUIDE.md)
- 기능 명세: [`SPEC.md`](../SPEC.md)
- Docker 환경 구축: [`INSTALL.DOCKER.md`](INSTALL.DOCKER.md)
