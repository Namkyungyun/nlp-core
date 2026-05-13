# Docker 설치 가이드

Docker(Linux 컨테이너)에서는 **MeCab을 별도 설치하지 않아도 됩니다.**
이유와 Dockerfile 작성 방법을 설명합니다.

---

## 1. MeCab 설치가 불필요한 이유

Ubuntu와 동일합니다. `python-mecab-ko` manylinux wheel이 MeCab C 런타임
(`libmecab.so`)과 한국어 사전(`python-mecab-ko-dic`)을 모두 내장합니다.

| 구성 요소 | 공급 방식 |
|---|---|
| MeCab C 런타임 (`libmecab.so`) | `python-mecab-ko` manylinux wheel 내부 번들 |
| 한국어 사전 (`mecab-ko-dic`) | `python-mecab-ko-dic` Python 패키지로 자동 설치 |

> **베이스 이미지 선택 기준** — `python:3.12-slim`(Debian glibc 기반)을 사용하세요.
> `python:3.12-alpine`(musl libc 기반)은 manylinux wheel을 지원하지 않아
> 별도의 빌드 의존성 설치가 필요합니다.

---

## 2. 최소 Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# MeCab 시스템 설치 불필요 — manylinux wheel이 libmecab.so를 번들
RUN pip install --no-cache-dir \
    "bpmg-korean-nlp @ git+https://github.com/Namkyungyun/nlp-core.git"

COPY . .
```

`apt-get install mecab` 또는 `apt-get install mecab-ko-dic` 같은 줄은
**추가하지 않아도 됩니다.**

---

## 3. 동작 확인

```bash
docker build -t my-app .

docker run --rm my-app python -c \
  "from bpmg_korean_nlp import check_mecab_dict; print(check_mecab_dict())"
```

`available=True`가 출력되면 MeCab과 사전이 모두 정상입니다.

```
DictCheckResult(available=True, dict_path=None, ...)
```

> `dict_path=None`은 정상입니다. 사전이 wheel 내부에 번들되어 있어
> 별도 파일시스템 경로가 없습니다.

---

## 4. `requirements.txt` 사용 시

```text
# requirements.txt
bpmg-korean-nlp @ git+https://github.com/Namkyungyun/nlp-core.git
```

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
```

---

## 5. 문제해결

### Alpine 베이스 이미지 사용 시

`python:3.12-alpine`은 musl libc 기반으로 manylinux wheel이 지원되지 않습니다.
`python:3.12-slim`(Debian) 사용을 강력히 권장합니다.

Alpine을 꼭 써야 한다면 빌드 의존성을 직접 설치해야 합니다:

```dockerfile
FROM python:3.12-alpine

RUN apk add --no-cache build-base mecab-dev
RUN pip install --no-cache-dir \
    "bpmg-korean-nlp @ git+https://github.com/Namkyungyun/nlp-core.git"
```

### `available=False`

`python-mecab-ko-dic`이 설치되지 않은 경우입니다.

```dockerfile
RUN pip install --no-cache-dir python-mecab-ko python-mecab-ko-dic \
    "bpmg-korean-nlp @ git+https://github.com/Namkyungyun/nlp-core.git"
```

---

## 다음 단계

- API 사용법: [`GUIDE.md`](../GUIDE.md)
- macOS 환경: [`INSTALL.MACOS.md`](INSTALL.MACOS.md)
- Ubuntu 환경: [`INSTALL.UBUNTU.md`](INSTALL.UBUNTU.md)
