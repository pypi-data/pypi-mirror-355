"""
inpynit의 핵심 프로젝트 생성 로직
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text

from .templates import get_available_templates, get_template_config
from .utils import validate_project_name


@dataclass
class ProjectConfig:
    """프로젝트 설정을 담는 데이터클래스"""

    name: str
    template: str
    author: str = "Developer"
    email: str = "dev@example.com"
    description: str = ""
    python_version: str = "3.11"
    license: str = "MIT"
    use_conda: bool = True
    use_git: bool = True


class ProjectCreator:
    """프로젝트 생성을 담당하는 메인 클래스"""

    def __init__(self):
        self.console = Console()
        self.templates_dir = Path(__file__).parent / "templates"

    def create_project(self, config: ProjectConfig, target_dir: Optional[Path] = None) -> bool:
        """
        주어진 설정으로 프로젝트를 생성합니다.

        Args:
            config: 프로젝트 설정
            target_dir: 생성할 디렉토리 (기본값: 현재 디렉토리)

        Returns:
            bool: 성공 여부
        """
        try:
            # 프로젝트 이름 검증
            if not validate_project_name(config.name):
                self.console.print(f"❌ 잘못된 프로젝트 이름: {config.name}", style="red")
                return False

            # 템플릿 존재 확인
            available_templates = get_available_templates()
            if config.template not in available_templates:
                self.console.print(f"❌ 존재하지 않는 템플릿: {config.template}", style="red")
                self.console.print(f"사용 가능한 템플릿: {', '.join(available_templates)}")
                return False

            # 프로젝트 디렉토리 설정
            if target_dir is None:
                target_dir = Path.cwd()

            project_path = target_dir / config.name

            # 디렉토리가 이미 존재하는지 확인
            if project_path.exists():
                self.console.print(f"❌ 디렉토리가 이미 존재합니다: {project_path}", style="red")
                return False

            # 프로젝트 생성 진행
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                # 1. 디렉토리 구조 생성
                task = progress.add_task("🏗️  프로젝트 구조 생성 중...", total=None)
                self._create_directory_structure(config, project_path)
                progress.update(task, completed=True)

                # 2. 템플릿 파일들 생성
                task = progress.add_task("📄 템플릿 파일 생성 중...", total=None)
                self._generate_template_files(config, project_path)
                progress.update(task, completed=True)

                # 3. Git 초기화
                if config.use_git:
                    task = progress.add_task("🌱 Git 저장소 초기화 중...", total=None)
                    self._initialize_git(project_path)
                    progress.update(task, completed=True)

                # 4. conda 환경 생성 (선택사항)
                if config.use_conda:
                    task = progress.add_task("🐍 conda 환경 설정 중...", total=None)
                    self._create_conda_env(config, project_path)
                    progress.update(task, completed=True)

            # 성공 메시지 출력
            self._print_success_message(config, project_path)
            return True

        except Exception as e:
            self.console.print(f"❌ 프로젝트 생성 중 오류 발생: {e}", style="red")
            return False

    def _create_directory_structure(self, config: ProjectConfig, project_path: Path):
        """프로젝트 디렉토리 구조를 생성합니다."""
        template_config = get_template_config(config.template)

        # 기본 디렉토리들
        project_path.mkdir(parents=True, exist_ok=True)

        # 템플릿별 디렉토리 구조
        for directory in template_config.get("directories", []):
            (project_path / directory).mkdir(parents=True, exist_ok=True)

    def _generate_template_files(self, config: ProjectConfig, project_path: Path):
        """템플릿 파일들을 생성합니다."""
        template_config = get_template_config(config.template)
        template_dir = self.templates_dir / config.template

        # Jinja2 환경 설정
        env = Environment(loader=FileSystemLoader(str(template_dir)))

        # 템플릿 변수들
        template_vars = {
            "project_name": config.name,
            "project_slug": config.name.lower().replace("-", "_"),
            "author": config.author,
            "email": config.email,
            "description": config.description or f"A {config.template} project created with inpynit",
            "python_version": config.python_version,
            "license": config.license,
            "use_git": config.use_git,
        }

        # 템플릿 파일들 처리
        for file_info in template_config.get("files", []):
            template_file = file_info["template"]
            output_file = file_info["output"].format(**template_vars)

            template = env.get_template(template_file)
            content = template.render(**template_vars)

            output_path = project_path / output_file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")

    def _create_conda_env(self, config: ProjectConfig, project_path: Path):
        """conda 환경을 생성합니다."""
        try:
            env_name = f"{config.name}-dev"
            # conda 환경 생성
            subprocess.run(
                [
                    "conda",
                    "create",
                    "-n",
                    env_name,
                    f"python={config.python_version}",
                    "-y",
                ],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            # conda가 설치되지 않았거나 오류가 발생한 경우 무시
            pass

    def _initialize_git(self, project_path: Path):
        """Git 저장소를 초기화합니다."""
        try:
            subprocess.run(["git", "init"], cwd=project_path, check=True, capture_output=True)
            subprocess.run(["git", "add", "."], cwd=project_path, check=True, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "🎉 Initial commit with inpynit"],
                cwd=project_path,
                check=True,
                capture_output=True,
            )
            # 초기 버전 태그 생성
            subprocess.run(
                ["git", "tag", "-a", "0.1.0", "-m", "Initial release 0.1.0"],
                cwd=project_path,
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            # Git이 설치되지 않았거나 오류가 발생한 경우 무시
            pass

    def _print_success_message(self, config: ProjectConfig, project_path: Path):
        """성공 메시지를 출력합니다."""
        success_text = Text()
        success_text.append("🎉 프로젝트가 성공적으로 생성되었습니다!\n\n", style="bold green")
        success_text.append(f"📁 프로젝트 경로: {project_path}\n", style="cyan")
        success_text.append(f"🎯 템플릿: {config.template}\n", style="yellow")

        next_steps = Text()
        next_steps.append("다음 단계:\n", style="bold blue")
        next_steps.append(f"1. cd {config.name}\n", style="white")

        if config.use_conda:
            next_steps.append(f"2. conda activate {config.name}-dev\n", style="white")
            next_steps.append("3. pip install -e .\n", style="white")
            next_steps.append("4. make help  # 개발 도구 확인\n", style="white")
            next_steps.append("5. make version-status  # 버전 확인\n", style="white")
            next_steps.append("6. 개발을 시작하세요! 🚀\n", style="white")
        else:
            next_steps.append("2. 가상환경을 직접 설정하세요\n", style="white")
            next_steps.append("3. pip install -e .\n", style="white")
            next_steps.append("4. make help  # 개발 도구 확인\n", style="white")
            next_steps.append("5. make version-status  # 버전 확인\n", style="white")
            next_steps.append("6. 개발을 시작하세요! 🚀\n", style="white")

        self.console.print(Panel(success_text, title="✨ 완료!", border_style="green"))
        self.console.print(Panel(next_steps, title="🚀 시작하기", border_style="blue"))
