# macOS 설치 가이드

이 가이드는 `bpmg-korean-nlp` SDK를 macOS에서 처음 설치하는 분을 위해 작성되었습니다.
명령어를 순서대로 따라하면 설치가 완료됩니다.

---

## 시작 전에 — 왜 macOS는 별도 설치가 필요한가?

이 SDK는 내부적으로 **MeCab**이라는 한국어 형태소 분석 엔진을 사용합니다.
MeCab은 C++로 작성된 외부 라이브러리이기 때문에 Python만으로는 설치가 완결되지 않습니다.

Linux(Ubuntu, Docker)에서는 SDK가 설치될 때 MeCab 바이너리까지 자동으로 묶어서 가져오지만,
**macOS는 이 자동 번들이 지원되지 않습니다.** 따라서 MeCab을 먼저 직접 설치해야 합니다.

설치 순서는 다음과 같습니다:

```
1단계: MeCab 엔진 + 한국어 사전 설치 (Homebrew)
2단계: SDK 설치 (pip, git URL)
3단계: 동작 확인
```

---

## 1단계. Homebrew 설치 확인

Homebrew는 macOS용 패키지 관리자입니다. 아래 명령으로 설치 여부를 확인합니다.

```bash
brew --version
```

`Homebrew 4.x.x` 같은 버전이 보이면 정상입니다.
설치되어 있지 않다면 [https://brew.sh](https://brew.sh) 에서 먼저 설치하세요.

---

## 2단계. MeCab 엔진 및 한국어 사전 설치

아래 명령 한 줄로 MeCab 엔진, 한국어 플러그인, 한국어 사전을 모두 설치합니다.

```bash
brew install mecab mecab-ko mecab-ko-dic
```

각 패키지가 하는 일:

| 패키지 | 역할 |
|---|---|
| `mecab` | 형태소 분석 엔진 본체 (C++ 바이너리) |
| `mecab-ko` | MeCab이 한국어 세종 품사 체계를 인식하도록 하는 플러그인 |
| `mecab-ko-dic` | 한국어 형태소 사전 데이터 — **이것이 없으면 한국어를 분석할 수 없습니다** |

설치가 끝나면 사전 경로를 확인합니다.

```bash
mecab-config --dicdir
```

아래처럼 경로가 출력되면 정상입니다.

```
/opt/homebrew/lib/mecab/dic        # Apple Silicon(M1/M2/M3)
/usr/local/lib/mecab/dic           # Intel Mac
```

---

## 3단계. SDK 설치

이 SDK는 PyPI에 등록되어 있지 않습니다. Git URL을 통해 설치합니다.

```bash
pip install "bpmg-korean-nlp @ git+https://github.com/Namkyungyun/nlp-core.git"
```

설치 중 아래와 같은 메시지가 나오면 정상입니다.

```
Cloning https://github.com/Namkyungyun/nlp-core.git ...
Successfully installed bpmg-korean-nlp-0.x.x python-mecab-ko-x.x.x ...
```

한자→한글 변환 기능이 필요한 경우 (`hanja_to_hangul=True` 옵션):

```bash
pip install "bpmg-korean-nlp[hanja] @ git+https://github.com/Namkyungyun/nlp-core.git"
```

---

## 4단계. 동작 확인

Python 인터프리터를 열고 아래를 실행합니다.

```python
from bpmg_korean_nlp import check_mecab_dict

result = check_mecab_dict()
print(result)
```

아래처럼 `available=True`가 보이면 MeCab과 사전이 모두 정상적으로 연결된 것입니다.

```
DictCheckResult(available=True, dict_path='/opt/homebrew/lib/mecab/dic/mecab-ko-dic', ...)
```

형태소 분석도 직접 확인해봅니다.

```python
from bpmg_korean_nlp import MeCabTokenizer

tok = MeCabTokenizer()
print(tok.tokenize("세종대학교에서 한국어 NLP를 연구한다"))
# ['세종', '대학교', '에서', '한국어', 'NLP', '를', '연구', '한다']
```

---

## 문제해결

### `brew: command not found`

Homebrew PATH가 셸에 등록되지 않은 경우입니다. 터미널을 재시작하거나 아래를 실행합니다.

```bash
# Apple Silicon
eval "$(/opt/homebrew/bin/brew shellenv)"

# Intel
eval "$(/usr/local/bin/brew shellenv)"
```

### `mecab-config: command not found`

MeCab이 설치되었지만 PATH에 없는 경우입니다. 위 명령 실행 후 다시 시도하세요.

### `check_mecab_dict()` 결과에서 `available=False`

사전이 설치되지 않았거나 경로를 찾지 못한 것입니다.

```bash
brew reinstall mecab mecab-ko mecab-ko-dic
```

재설치 후에도 해결되지 않으면 `mecab-config --dicdir` 결과를 확인하고
해당 경로 아래에 `mecab-ko-dic` 디렉터리가 존재하는지 확인하세요.

### `pip install` 중 빌드 오류 (컴파일 실패)

Xcode Command Line Tools가 설치되지 않은 경우 발생합니다.

```bash
xcode-select --install
```

설치 후 다시 pip install을 시도합니다.

---

## 다음 단계

- 전체 API 사용법: [`GUIDE.md`](../GUIDE.md)
- Ubuntu 환경에서 설치: [`INSTALL.UBUNTU.md`](INSTALL.UBUNTU.md)
- Docker 환경에서 설치: [`INSTALL.DOCKER.md`](INSTALL.DOCKER.md)
