# Docker 설치 가이드

`bpmg-korean-nlp`을 Docker 컨테이너에서 사용하는 가이드입니다.

> **핵심 요약** — `python:3.12-slim` 베이스에서 `pip install bpmg-korean-nlp`
> 한 줄이면 끝입니다.
>
> **이유 (두 가지)**
> 1. `python-mecab-ko` Linux 배포판은 **`manylinux` 규격 wheel** 형식으로 제공됩니다.
>    `manylinux` wheel은 `auditwheel repair`를 통해 **MeCab C 런타임 라이브러리
>    (`libmecab.so`)를 wheel 내부에 번들**합니다. 따라서 시스템에 `mecab` 패키지를
>    별도로 설치하지 않아도 MeCab 분석기가 동작합니다.
> 2. `python-mecab-ko-dic` 패키지가 **한국어 사전 데이터**를 Python 패키지로 제공합니다.
>
> macOS에서는 이 번들링이 적용되지 않으므로 `brew install mecab mecab-ko mecab-ko-dic`
> 사전 설치가 필요합니다. Docker/Linux에서만 pip 한 줄로 완결됩니다.

---

## 1. 최소 Dockerfile

가장 단순한 형태입니다. 사전 포함 환경이 이미지에 그대로 구워집니다.

```dockerfile
FROM python:3.12-slim
RUN pip install --no-cache-dir bpmg-korean-nlp
```

빌드:

```bash
docker build -t bpmg-korean-nlp:demo .
```

---

## 2. 동작 확인

이미지 안에서 사전 가용성을 한 줄로 점검합니다.

```bash
docker run --rm bpmg-korean-nlp:demo \
  python -c "from bpmg_korean_nlp import check_mecab_dict; print(check_mecab_dict())"
```

`available=True` 와 사전 경로가 출력되면 정상입니다.

간단한 토큰화도 확인합니다.

```bash
docker run --rm bpmg-korean-nlp:demo python -c "
from bpmg_korean_nlp import MeCabTokenizer
print(MeCabTokenizer().tokenize('세종대학교에서 한국어 NLP를 연구한다'))
"
```

---

## 3. 애플리케이션 포함 Dockerfile

`app/` 디렉터리의 Python 코드를 함께 담는 일반적인 형태입니다.

```dockerfile
FROM python:3.12-slim

# 비루트 사용자 (선택 — 운영 시 권장)
RUN useradd -m -u 1000 app
WORKDIR /app

# 의존성 먼저 설치 (레이어 캐시 효율)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드
COPY --chown=app:app . .

USER app
CMD ["python", "-m", "app.main"]
```

`requirements.txt` 예시:

```text
bpmg-korean-nlp>=0.1.0
# 한자→한글 변환이 필요한 경우
# bpmg-korean-nlp[hanja]>=0.1.0
```

---

## 4. (선택) 멀티스테이지 빌드

이미지 크기 최적화가 필요한 경우 builder 스테이지에서 wheel을 받아두고,
runtime 스테이지로 복사하는 패턴을 사용합니다.

```dockerfile
# ── builder ──
FROM python:3.12-slim AS builder

WORKDIR /build
RUN pip install --no-cache-dir --upgrade pip wheel

# wheel만 받아 캐시
RUN pip wheel --no-cache-dir --wheel-dir=/wheels bpmg-korean-nlp

# ── runtime ──
FROM python:3.12-slim AS runtime

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels bpmg-korean-nlp \
 && rm -rf /wheels

WORKDIR /app
COPY . .

CMD ["python", "-m", "app.main"]
```

> **참고** — 본 SDK는 순수 Python wrapper + 사전 데이터 패키지로 구성되므로
> 멀티스테이지로 얻는 절감폭은 크지 않습니다. 다른 무거운 빌드 의존성과 함께
> 쓰일 때 의미가 있습니다.

---

## 5. 문제해결

### 5-1. `pip install` 중 C 컴파일 오류가 나는 경우

일반적인 `linux/amd64`, `linux/arm64`에서는 wheel을 그대로 받기 때문에
컴파일이 일어나지 않습니다. 드물게 wheel이 없는 아키텍처(예: 비표준 base image,
musl 기반 alpine 등)에서 sdist 빌드가 시도되어 실패하는 경우가 있습니다.

`python:3.12-slim`(Debian glibc)을 그대로 쓰는 것을 권장하며, 그래도 빌드가
필요하다면 다음 패키지를 추가합니다.

```dockerfile
FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        build-essential \
        libmecab-dev \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir bpmg-korean-nlp
```

- `build-essential` — `gcc`, `g++`, `make`
- `libmecab-dev` — MeCab C++ 헤더 (Python 확장 빌드 시 참조)

### 5-2. `alpine` 베이스 사용 시

`python:3.12-alpine`은 musl libc 기반이라 `python-mecab-ko` wheel이 제공되지
않을 수 있습니다. **가능하면 `python:3.12-slim`(Debian)을 사용하세요.** 굳이
alpine을 써야 한다면 위 5-1과 같은 빌드 의존성을 alpine 패키지(`build-base`,
`mecab-dev` 등)로 대체해야 합니다.

### 5-3. `check_mecab_dict()`가 `available=False`

`python-mecab-ko-dic`이 같이 설치되지 않은 환경입니다. 명시적으로 추가합니다.

```dockerfile
RUN pip install --no-cache-dir python-mecab-ko python-mecab-ko-dic bpmg-korean-nlp
```

---

## 다음 단계

- API 사용법: [`GUIDE.md`](../GUIDE.md)
- 기능 명세: [`SPEC.md`](../SPEC.md)
- Ubuntu 직접 설치: [`INSTALL.UBUNTU.md`](INSTALL.UBUNTU.md)
