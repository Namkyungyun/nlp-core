# Docker 설치 가이드

이 가이드는 `bpmg-korean-nlp` SDK를 Docker 컨테이너 안에서 사용하려는 분을 위해 작성되었습니다.
Dockerfile 작성 방법과 동작 확인 방법을 단계별로 설명합니다.

---

## 시작 전에 — Docker에서도 MeCab을 따로 설치하지 않아도 됩니다

macOS에서는 MeCab(형태소 분석 엔진)을 Homebrew로 별도 설치해야 하지만,
Docker 컨테이너(Linux 환경) 안에서는 **SDK를 pip으로 설치할 때 MeCab까지 자동으로 함께 설치됩니다.**

이유를 간단히 설명하면 다음과 같습니다.

> `python-mecab-ko` 패키지는 Linux용으로 배포할 때 MeCab C 바이너리(`libmecab.so`)를
> 패키지 파일 내부에 **미리 묶어서(번들)** 제공합니다.
> 따라서 pip install 한 번으로 MeCab까지 설치가 완료됩니다.
>
> 한국어 사전 데이터도 `python-mecab-ko-dic`이라는 Python 패키지로 자동 설치됩니다.

따라서 Dockerfile에 `RUN apt-get install mecab` 같은 줄을 **추가하지 않아도 됩니다.**

---

## 베이스 이미지 선택

반드시 **`python:3.12-slim`** (Debian 기반)을 사용하세요.

| 이미지 | 사용 가능 여부 | 이유 |
|---|---|---|
| `python:3.12-slim` | ✅ 권장 | Debian(glibc) 기반 — MeCab 자동 번들 정상 동작 |
| `python:3.12` | ✅ 가능 | 동일하지만 이미지 크기가 큼 |
| `python:3.12-alpine` | ❌ 비권장 | Alpine(musl libc) 기반 — MeCab 자동 번들 미지원, 별도 빌드 필요 |

---

## 1단계. Dockerfile 작성

아래는 가장 기본적인 Dockerfile입니다.
`apt-get install mecab` 없이 pip 한 줄만으로 MeCab까지 설치됩니다.

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# MeCab 시스템 설치 불필요 — pip install 시 MeCab이 자동으로 포함됩니다
RUN pip install --no-cache-dir \
    "bpmg-korean-nlp @ git+https://github.com/Namkyungyun/nlp-core.git"

COPY . .
```

> **`git` 명령어가 필요한 경우**: pip이 git URL에서 소스를 클론하므로
> 일부 환경에서는 git이 필요합니다. 오류가 발생하면 아래를 추가하세요.
>
> ```dockerfile
> RUN apt-get update && apt-get install -y --no-install-recommends git \
>     && rm -rf /var/lib/apt/lists/*
> ```

---

## 2단계. 이미지 빌드

```bash
docker build -t my-korean-nlp-app .
```

빌드 로그에서 아래 내용이 보이면 MeCab이 자동 번들된 것입니다.

```
Downloading python_mecab_ko-x.x.x-...-manylinux_2_17_x86_64.whl   ← MeCab 번들 포함
Downloading python_mecab_ko_dic-x.x.x-py3-none-any.whl             ← 한국어 사전
...
Successfully installed bpmg-korean-nlp-x.x.x python-mecab-ko-x.x.x ...
```

---

## 3단계. 동작 확인

### MeCab 및 사전 확인

```bash
docker run --rm my-korean-nlp-app \
    python -c "from bpmg_korean_nlp import check_mecab_dict; print(check_mecab_dict())"
```

아래처럼 `available=True`가 출력되면 정상입니다.

```
DictCheckResult(available=True, dict_path=None, ...)
```

> `dict_path=None`은 오류가 아닙니다.
> 사전이 Python 패키지 내부에 포함되어 있어 별도 파일 경로가 없는 것이 정상입니다.

### 형태소 분석 확인

```bash
docker run --rm my-korean-nlp-app python -c "
from bpmg_korean_nlp import MeCabTokenizer
tok = MeCabTokenizer()
print(tok.tokenize('세종대학교에서 한국어 NLP를 연구한다'))
"
```

출력:

```
['세종', '대학교', '에서', '한국어', 'NLP', '를', '연구', '한다']
```

위 결과가 나오면 컨테이너 안에서 SDK가 정상적으로 동작하는 것입니다.

---

## 애플리케이션과 함께 사용하는 Dockerfile 예시

실제 서비스 코드를 함께 담는 일반적인 형태입니다.

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 의존성 먼저 설치 (Docker 레이어 캐시 활용)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

CMD ["python", "-m", "your_app"]
```

`requirements.txt`:

```text
bpmg-korean-nlp @ git+https://github.com/Namkyungyun/nlp-core.git
```

---

## 문제해결

### 빌드 중 `git: not found` 오류

pip이 git을 사용해 소스를 받는데, 컨테이너에 git이 없는 경우입니다.
Dockerfile에 다음을 추가합니다.

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*
```

### Alpine 베이스 이미지를 사용하는 경우

`python:3.12-alpine`은 MeCab 자동 번들을 지원하지 않아 직접 빌드가 필요합니다.
가능하면 `python:3.12-slim`으로 교체하는 것을 강력히 권장합니다.

부득이하게 Alpine을 써야 한다면:

```dockerfile
FROM python:3.12-alpine

RUN apk add --no-cache build-base mecab-dev
RUN pip install --no-cache-dir \
    "bpmg-korean-nlp @ git+https://github.com/Namkyungyun/nlp-core.git"
```

### `check_mecab_dict()` 결과에서 `available=False`

`python-mecab-ko-dic`이 설치되지 않은 경우입니다.
Dockerfile에서 명시적으로 설치합니다.

```dockerfile
RUN pip install --no-cache-dir \
    python-mecab-ko \
    python-mecab-ko-dic \
    "bpmg-korean-nlp @ git+https://github.com/Namkyungyun/nlp-core.git"
```

---

## 다음 단계

- 전체 API 사용법: [`GUIDE.md`](../GUIDE.md)
- macOS 환경에서 설치: [`INSTALL.MACOS.md`](INSTALL.MACOS.md)
- Ubuntu 환경에서 설치: [`INSTALL.UBUNTU.md`](INSTALL.UBUNTU.md)
