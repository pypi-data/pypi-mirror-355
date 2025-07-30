# 🚀 inpynit

**In**finite + **Py**thon + **Init** = 무한한 가능성을 가진 파이썬 프로젝트 시작!

inpynit는 파이썬 프로젝트를 빠르고 쉽게 시작할 수 있도록 도와주는 CLI 도구입니다. 다양한 프로젝트 템플릿과 모던한 설정을 제공합니다.

## ✨ 특징

- 🎯 **다양한 템플릿**: 기본 패키지, 웹 앱, CLI 도구, 데이터 사이언스, 머신러닝 등
- 🏷️ **스마트 버전 관리**: Git 태그와 패키지 버전이 **자동으로 동일하게** 유지됨
- 🎨 **대화형 인터페이스**: 사용자 친화적인 프로젝트 설정 과정
- 📦 **자동 환경 설정**: conda 환경, Git 저장소 자동 초기화
- 🚀 **즉시 실행**: 설치 후 바로 사용 가능한 프로젝트 구조

## 🔧 설치

### pipx 방식 (권장)

**pipx**는 파이썬 CLI 도구를 격리된 환경에서 전역적으로 설치할 수 있게 해주는 도구입니다.
시스템 파이썬 환경을 깨뜨리지 않으면서 CLI 도구를 안전하게 설치하고 관리할 수 있습니다.

#### pipx 설치

```bash
# macOS (Homebrew)
brew install pipx

# Ubuntu/Debian
sudo apt install pipx

# 또는 pip로 설치
pip install --user pipx
pipx ensurepath
```

#### inpynit 설치

```bash
pipx install inpynit
```

### pip 방식

```bash
pip install inpynit
```

## 🚀 사용법

### 기본 사용법

```bash
# 기본 명령어 (도움말 보기)
inpynit

# 새 프로젝트 생성 (대화형)
inpynit create my-awesome-project

# 빠른 생성 (기본 설정)
inpynit create my-project --quick

# 사용 가능한 템플릿 보기
inpynit templates
```

### 사용 가능한 템플릿

| 템플릿        | 이름            | 설명                              |
| ------------- | --------------- | --------------------------------- |
| `basic`       | 기본 패키지     | 기본적인 파이썬 패키지 구조       |
| `fastapi`     | FastAPI 웹 앱   | FastAPI 기반 웹 애플리케이션      |
| `flask`       | Flask 웹 앱     | Flask 기반 웹 애플리케이션        |
| `cli`         | CLI 도구        | Click 기반 명령줄 인터페이스 도구 |
| `datascience` | 데이터 사이언스 | 데이터 분석 및 시각화 프로젝트    |
| `ml`          | 머신러닝        | 머신러닝 모델 개발 프로젝트       |

### 명령어 옵션

#### `inpynit create`

- `--quick, -q`: 기본 설정으로 빠른 생성
- `--template, -t`: 사용할 템플릿 지정

### 예시

```bash
# 기본 패키지 프로젝트 생성 (대화형)
inpynit create my-package

# 빠른 생성 (기본 설정)
inpynit create my-project --quick

# FastAPI 프로젝트 생성
inpynit create my-api --template fastapi

# 데이터 사이언스 프로젝트 생성
inpynit create data-analysis --template datascience
```

## 🎮 대화형 모드

대화형 모드에서는 다음 항목들을 설정할 수 있습니다:

- **프로젝트 이름**: 유효한 파이썬 패키지 이름
- **템플릿 선택**: 프로젝트 유형에 맞는 템플릿
- **작성자 정보**: 이름과 이메일 (Git 설정에서 자동 추출)
- **프로젝트 설명**: 프로젝트에 대한 간단한 설명
- **파이썬 버전**: 3.8 ~ 3.12 중 선택
- **라이선스**: MIT, Apache-2.0, GPL-3.0, BSD-3-Clause, ISC 중 선택
- **환경 설정**: conda 환경, Git 저장소 설정 여부

## 📁 생성되는 프로젝트 구조

### 기본 템플릿 (`basic`)

```
my-project/
├── my_project/
│   ├── __init__.py
│   └── main.py
├── tests/
│   └── test_main.py
├── docs/
│   └── settings.json
├── pyproject.toml
├── README.md
└── .gitignore
```

### 웹 앱 템플릿 (`fastapi`, `flask`)

```
my-api/
├── my_api/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   ├── core/
│   └── models/
├── tests/
├── docs/
├── pyproject.toml
├── requirements.txt
├── README.md
└── .gitignore
```

### 데이터 사이언스 템플릿 (`datascience`, `ml`)

```
data-project/
├── data/
│   ├── raw/
│   └── processed/
├── notebooks/
├── src/
│   └── data_project/
├── tests/
├── docs/
├── models/          # ML 템플릿만
├── pyproject.toml
├── requirements.txt
├── README.md
└── .gitignore
```

## 🛠️ 개발

### 개발 환경 설정

```bash
# 저장소 클론
git clone https://github.com/yourusername/inpynit.git
cd inpynit

# conda 환경 생성 (권장)
conda create -n inpynit-dev python=3.11 -y
conda activate inpynit-dev

# 개발 모드로 설치
pip install -e ".[dev]"

# 테스트 실행
pytest

# 코드 포매팅
ruff format .
```

### 개발 의존성

- `pytest`: 테스트 프레임워크
- `ruff`: 코드 포매팅 및 린팅

## 🏗️ 주요 기능

### 핵심 모듈

- **`cli.py`**: Click 기반 CLI 인터페이스
- **`core.py`**: 프로젝트 생성 핵심 로직
- **`templates.py`**: 템플릿 관리 및 설정
- **`utils.py`**: 유틸리티 함수들

### 자동화 기능

- 🔄 **Git 저장소 자동 초기화**: 첫 커밋과 초기 태그 자동 생성
- 🐍 **conda 환경 자동 생성**: 프로젝트별 격리된 환경
- 📝 **프로젝트 메타데이터 자동 설정**: pyproject.toml 완전 자동화
- 🏷️ **Git 태그 기반 버전 관리**: setuptools-scm 자동 설정

### 🎯 스마트 버전 관리의 장점

**Git 태그를 생성하면 패키지 버전이 자동으로 동일하게 됩니다!**

```bash
# 1. Git 태그 생성
git tag 1.2.3

# 2. 빌드 시 자동으로 동일한 버전 적용
python -m build
# 결과: my-package-1.2.3-py3-none-any.whl

# 버전 확인도 자동으로 동일
python -c "import my_package; print(my_package.__version__)"
# 출력: 1.2.3
```

**수동 버전 관리는 이제 그만!** setuptools-scm이 Git 태그를 읽어서 모든 버전을 자동으로 동기화합니다.

#### 🔄 기존 방식 vs inpynit 방식

**기존 수동 방식** ❌:

- pyproject.toml에서 `version = "1.2.3"` 수정
- \_\_init\_\_.py에서 `__version__ = "1.2.3"` 수정
- CLI 버전에서 `version="1.2.3"` 수정
- 실수 하나면 버전 불일치 발생! 😰

**inpynit 자동 방식** ✅:

- `git tag 1.2.3` 하나만 실행
- 모든 버전이 자동으로 일치! 🎯

**개발 중인 버전도 자동 관리:**

```bash
# 1.2.3 태그 이후 2번의 커밋이 있다면
python -c "import my_package; print(my_package.__version__)"
# 출력: 1.2.4.dev2+g1a2b3c4d  (자동 생성!)
```

## 🌟 특별한 기능

- **스마트 Git 정보 추출**: 시스템 Git 설정에서 작성자 정보 자동 추출
- **프로젝트 이름 검증**: 파이썬 패키지 명명 규칙 자동 검증
- **아름다운 CLI**: Rich 라이브러리를 사용한 현대적인 터미널 UI
- **실시간 진행 상황**: 프로젝트 생성 과정의 실시간 피드백

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🤝 기여

기여를 환영합니다! Pull Request를 보내주세요.

## 📚 개발 현황

현재 **기본 템플릿**만 구현되어 있으며, 다른 템플릿들은 개발 중입니다. 템플릿 구조는 `templates.py`에서 확인할 수 있습니다.

---

**inpynit**로 무한한 가능성의 파이썬 프로젝트를 시작해보세요! 🐍✨
