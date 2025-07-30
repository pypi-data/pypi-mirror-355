# 📝 Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### 🚧 개발 중

- 추가 템플릿 구현 (FastAPI, Flask, CLI 등)

## [0.1.0] - 2024-01-XX

### ✨ Added

- 🎯 기본 파이썬 패키지 템플릿 구현
- 🖥️ Click 기반 CLI 인터페이스
- 🎨 Rich를 사용한 아름다운 터미널 UI
- 🔧 대화형 프로젝트 생성 모드
- ⚡ `--quick` 옵션으로 빠른 프로젝트 생성
- 📋 `inpynit templates` 명령어로 템플릿 목록 확인
- 🐍 conda 환경 자동 생성
- 🌱 Git 저장소 자동 초기화 및 초기 태그 생성
- 📦 pyproject.toml 기반 모던한 파이썬 패키지 구조
- 🏷️ setuptools-scm을 통한 Git 태그 기반 자동 버전 관리
- 🎯 프로젝트 이름 유효성 검증
- 📧 Git 사용자 정보 자동 추출
- 🧪 기본 테스트 구조 포함

### 🛠️ Technical

- Jinja2 템플릿 엔진 사용
- setuptools-scm을 통한 Git 태그 = 패키지 버전 자동 동기화
- Python 3.8+ 호환성
- Cross-platform 지원 (Linux, macOS, Windows)

### 📦 Dependencies

- click >= 8.0.0
- jinja2 >= 3.0.0
- rich >= 12.0.0
- toml >= 0.10.0

### 🔧 Development Tools

- pytest for testing
- ruff for formatting and linting
- setuptools-scm for version management
- Makefile for common tasks
- GitHub Actions for automated releases

---

## 🏷️ Git Tag 규칙

- `0.1.0` - 메이저.마이너.패치 형식 (v 접두사 없음)
- 각 릴리스마다 Git 태그 생성
- setuptools-scm이 Git 태그를 읽어 패키지 버전 자동 생성
- GitHub Actions를 통한 자동 릴리스

## 📋 변경사항 분류

- `✨ Added` - 새로운 기능
- `🔧 Changed` - 기존 기능 수정
- `🗑️ Deprecated` - 곧 제거될 기능
- `❌ Removed` - 제거된 기능
- `🐛 Fixed` - 버그 수정
- `🔒 Security` - 보안 관련 수정
