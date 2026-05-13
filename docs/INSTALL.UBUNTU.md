# Ubuntu 22.04 설치 가이드

Ubuntu(Linux)에서는 **MeCab을 시스템에 별도 설치하지 않아도 됩니다.**
이유와 설치 절차를 설명합니다.

---

## 1. MeCab 설치가 불필요한 이유

`python-mecab-ko`는 Linux용으로 **`manylinux` 규격 wheel**을 제공합니다.

```
python_mecab_ko-1.x.x-cp312-cp312-manylinux_2_17_x86_64.whl
```

이 wheel은 `auditwheel repair` 도구로 빌드되어 **MeCab C 런타임 라이브러리
(`libmecab.so`)가 wheel 내부에 번들**되어 있습니다.

```
wheel 내부
└── python_mecab_ko.libs/
    └── libmecab.so.2   ← MeCab 런타임 (시스템 설치 불필요)
```

| 구성 요소 | 공급 방식 |
|---|---|
| MeCab C 런타임 (`libmecab.so`) | `python-mecab-ko` manylinux wheel 내부 번들 |
| 한국어 사전 (`mecab-ko-dic`) | `python-mecab-ko-dic` Python 패키지로 자동 설치 |

> **macOS와의 차이** — macOS는 manylinux wheel이 지원되지 않아
> `brew install mecab mecab-ko mecab-ko-dic`이 필요합니다.
> Linux에서는 이 단계가 불필요합니다.

---

## 2. 전제조건

| 항목 | 요구사항 |
|---|---|
| OS | Ubuntu 22.04 LTS 이상 (Debian 12 동일) |
| Python | 3.12 이상 (`python3 --version`으로 확인) |

Ubuntu 22.04 기본 Python은 3.10입니다. 3.12가 없다면 deadsnakes PPA로 설치합니다.

```bash
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv
```

---

## 3. SDK 설치

```bash
pip install "bpmg-korean-nlp @ git+https://github.com/Namkyungyun/nlp-core.git"
```

이 한 줄이 다음을 자동으로 수행합니다.

1. `python-mecab-ko` — MeCab manylinux wheel (libmecab.so 번들 포함)
2. `python-mecab-ko-dic` — 한국어 사전 패키지
3. `bpmg-korean-nlp` 본체 및 기타 런타임 의존성

`apt-get install mecab`, `apt-get install mecab-ko-dic` 등의 시스템 패키지 설치는 **필요하지 않습니다.**

---

## 4. 동작 확인

```bash
python -c "from bpmg_korean_nlp import check_mecab_dict; print(check_mecab_dict())"
```

`available=True`가 출력되면 MeCab과 한국어 사전이 모두 정상입니다.

```
DictCheckResult(available=True, dict_path=None, ...)
```

> `dict_path=None`은 정상입니다. 사전이 wheel 내부에 번들되어 있어
> 별도의 파일시스템 경로가 노출되지 않습니다.

---

## 5. 문제해결

### `pip install` 중 C 컴파일 오류

`manylinux` wheel이 없는 비표준 아키텍처(예: Alpine musl libc)에서 sdist 빌드가
시도되는 경우입니다. `python:3.12-slim`(Debian glibc) 환경을 사용하세요.
부득이하게 직접 빌드가 필요하다면:

```bash
sudo apt-get install -y build-essential libmecab-dev
pip install --no-cache-dir --force-reinstall bpmg-korean-nlp
```

### `available=False`

`python-mecab-ko-dic`이 설치되지 않은 경우입니다.

```bash
pip install --force-reinstall python-mecab-ko python-mecab-ko-dic
```

---

## 다음 단계

- API 사용법: [`GUIDE.md`](../GUIDE.md)
- macOS 환경: [`INSTALL.MACOS.md`](INSTALL.MACOS.md)
- Docker 환경: [`INSTALL.DOCKER.md`](INSTALL.DOCKER.md)
