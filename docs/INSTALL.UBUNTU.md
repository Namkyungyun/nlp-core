# Ubuntu 22.04 설치 가이드

이 가이드는 `bpmg-korean-nlp` SDK를 Ubuntu 22.04에서 처음 설치하는 분을 위해 작성되었습니다.
명령어를 순서대로 따라하면 설치가 완료됩니다.

---

## 시작 전에 — Ubuntu에서는 MeCab을 따로 설치하지 않아도 됩니다

macOS에서는 MeCab(형태소 분석 엔진)을 Homebrew로 별도 설치해야 하지만,
Ubuntu를 포함한 Linux 환경에서는 **SDK를 pip으로 설치하면 MeCab까지 자동으로 설치됩니다.**

이유를 간단히 설명하면 다음과 같습니다.

> `python-mecab-ko` 패키지는 Linux용으로 배포할 때 MeCab C 바이너리(`libmecab.so`)를
> 패키지 파일 내부에 **미리 묶어서(번들)** 제공합니다.
> 따라서 `pip install`만 해도 MeCab이 함께 설치됩니다.
>
> 한국어 사전 데이터도 `python-mecab-ko-dic`이라는 별도 Python 패키지로 제공되어
> SDK 설치 시 자동으로 함께 설치됩니다.

결론적으로 Ubuntu에서는 `apt-get install mecab` 같은 명령이 **필요하지 않습니다.**

설치 순서는 다음과 같습니다.

```
1단계: Python 3.12 준비 (Ubuntu 22.04 기본은 3.10이므로 확인 필요)
2단계: SDK 설치 (pip, git URL — MeCab 포함 자동 설치)
3단계: 동작 확인
```

---

## 1단계. Python 3.12 준비

이 SDK는 Python 3.12 이상이 필요합니다. 먼저 설치된 버전을 확인합니다.

```bash
python3 --version
```

`Python 3.12.x` 이상이면 2단계로 넘어가세요.
**3.10 이하라면** 아래 절차로 3.12를 설치합니다.

### Python 3.12 설치 (Ubuntu 22.04 기준)

Ubuntu 22.04의 공식 저장소에는 Python 3.10이 포함되어 있습니다.
3.12를 설치하려면 deadsnakes PPA(서드파티 패키지 저장소)를 추가해야 합니다.

```bash
# 저장소 추가 도구 설치
sudo apt-get update
sudo apt-get install -y software-properties-common

# deadsnakes PPA 추가 (Python 최신 버전 제공)
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update

# Python 3.12 설치
sudo apt-get install -y python3.12 python3.12-venv
```

설치 확인:

```bash
python3.12 --version
# Python 3.12.x
```

### 가상환경 생성 (권장)

여러 프로젝트가 서로 간섭하지 않도록 가상환경을 만들어 사용하는 것을 권장합니다.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

프롬프트 앞에 `(.venv)`가 표시되면 가상환경이 활성화된 것입니다.

---

## 2단계. SDK 설치

이 SDK는 PyPI에 등록되어 있지 않습니다. Git URL을 통해 설치합니다.

```bash
pip install "bpmg-korean-nlp @ git+https://github.com/Namkyungyun/nlp-core.git"
```

설치가 시작되면 다음과 같은 메시지가 출력됩니다.

```
Cloning https://github.com/Namkyungyun/nlp-core.git ...
Collecting python-mecab-ko ...
Downloading python_mecab_ko-x.x.x-...-manylinux_2_17_x86_64.whl   ← MeCab 번들 포함
Collecting python-mecab-ko-dic ...
Downloading python_mecab_ko_dic-x.x.x-py3-none-any.whl             ← 한국어 사전
...
Successfully installed bpmg-korean-nlp-x.x.x python-mecab-ko-x.x.x python-mecab-ko-dic-x.x.x ...
```

`manylinux_2_17`이 포함된 wheel 파일명이 보이면 MeCab이 자동 번들된 버전입니다.

---

## 3단계. 동작 확인

### MeCab 및 사전 확인

```bash
python -c "from bpmg_korean_nlp import check_mecab_dict; print(check_mecab_dict())"
```

아래처럼 `available=True`가 보이면 정상입니다.

```
DictCheckResult(available=True, dict_path=None, ...)
```

> `dict_path=None`은 오류가 아닙니다.
> 사전이 Python 패키지 내부에 포함되어 있어 별도 파일 경로가 없는 것이 정상입니다.

### 형태소 분석 확인

```bash
python -c "
from bpmg_korean_nlp import MeCabTokenizer
tok = MeCabTokenizer()
print(tok.tokenize('세종대학교에서 한국어 NLP를 연구한다'))
"
```

출력:

```
['세종', '대학교', '에서', '한국어', 'NLP', '를', '연구', '한다']
```

위 결과가 나오면 설치가 완전히 완료된 것입니다.

---

## 문제해결

### `pip install` 중 컴파일 오류가 발생하는 경우

일반적인 x86\_64 또는 arm64 Ubuntu 환경에서는 컴파일 없이 미리 빌드된 파일을 받습니다.
드물게 지원되지 않는 아키텍처에서 직접 빌드가 시도되어 실패할 수 있습니다.
이때는 아래 패키지를 먼저 설치합니다.

```bash
sudo apt-get install -y build-essential libmecab-dev
pip install --no-cache-dir --force-reinstall \
    "bpmg-korean-nlp @ git+https://github.com/Namkyungyun/nlp-core.git"
```

### `check_mecab_dict()` 결과에서 `available=False`

`python-mecab-ko-dic`이 설치되지 않은 경우입니다.

```bash
pip install --force-reinstall python-mecab-ko python-mecab-ko-dic
```

### 가상환경 밖에서 실행한 경우

`(.venv)` 프롬프트가 보이지 않으면 가상환경이 비활성화된 상태입니다.
아래 명령으로 다시 활성화합니다.

```bash
source .venv/bin/activate
```

---

## 다음 단계

- 전체 API 사용법: [`GUIDE.md`](../GUIDE.md)
- macOS 환경에서 설치: [`INSTALL.MACOS.md`](INSTALL.MACOS.md)
- Docker 환경에서 설치: [`INSTALL.DOCKER.md`](INSTALL.DOCKER.md)
