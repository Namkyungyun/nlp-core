# macOS 설치 가이드

macOS는 `python-mecab-ko` manylinux wheel이 적용되지 않아 **MeCab C 라이브러리와 한국어 사전을 시스템에 직접 설치**해야 합니다.

---

## 1. MeCab 설치 (필수)

Homebrew로 세 패키지를 순서대로 설치합니다.

```bash
brew install mecab mecab-ko mecab-ko-dic
```

| 패키지 | 역할 |
|---|---|
| `mecab` | MeCab 형태소 분석기 C++ 바이너리 및 런타임 라이브러리 |
| `mecab-ko` | 한국어 MeCab 플러그인 (세종 품사 태그 지원) |
| `mecab-ko-dic` | 한국어 형태소 사전 데이터 (`/usr/local/lib/mecab/dic/mecab-ko-dic`) |

> **설치 순서를 지켜야 합니다.** `mecab-ko-dic`은 `mecab-ko`에, `mecab-ko`는 `mecab`에 의존합니다.

사전 경로 확인:

```bash
mecab-config --dicdir
# → /usr/local/lib/mecab/dic 또는 /opt/homebrew/lib/mecab/dic (Apple Silicon)
```

---

## 2. SDK 설치

MeCab 설치 후 git URL로 SDK를 받습니다.

```bash
pip install "bpmg-korean-nlp @ git+https://github.com/Namkyungyun/nlp-core.git"
```

`python-mecab-ko`는 macOS에서 소스 빌드가 필요하므로 위 1단계의 시스템 MeCab이 반드시 선행되어야 합니다.

한자→한글 변환 옵션이 필요한 경우:

```bash
pip install "bpmg-korean-nlp[hanja] @ git+https://github.com/Namkyungyun/nlp-core.git"
```

---

## 3. 동작 확인

```bash
python -c "from bpmg_korean_nlp import check_mecab_dict; print(check_mecab_dict())"
```

`available=True`와 사전 경로가 출력되면 정상입니다.

```
DictCheckResult(available=True, dict_path='/opt/homebrew/lib/mecab/dic/mecab-ko-dic', ...)
```

---

## 4. 문제해결

### `available=False` 또는 사전 경로가 None

`mecab-ko-dic`이 설치되지 않았거나 경로를 찾지 못한 경우입니다.

```bash
# 설치 확인
brew list | grep mecab

# 재설치
brew reinstall mecab mecab-ko mecab-ko-dic
```

### `python-mecab-ko` 빌드 실패

Xcode Command Line Tools가 없는 경우 발생합니다.

```bash
xcode-select --install
pip install --no-cache-dir --force-reinstall python-mecab-ko
```

---

## 다음 단계

- API 사용법: [`GUIDE.md`](../GUIDE.md)
- Ubuntu 환경: [`INSTALL.UBUNTU.md`](INSTALL.UBUNTU.md)
- Docker 환경: [`INSTALL.DOCKER.md`](INSTALL.DOCKER.md)
