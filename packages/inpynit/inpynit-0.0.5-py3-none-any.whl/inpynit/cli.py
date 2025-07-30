"""
inpynit CLI 인터페이스
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .core import ProjectConfig, ProjectCreator
from .templates import list_templates_info
from .utils import get_git_user_info

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version="0.1.0", prog_name="inpynit")
def main(ctx):
    """🚀 inpynit: 무한한 가능성을 가진 파이썬 프로젝트를 시작하세요!"""
    if ctx.invoked_subcommand is None:
        welcome_message()


def welcome_message():
    """환영 메시지를 출력합니다."""
    title = "🚀 inpynit"
    subtitle = "Infinite + Python + Init"
    description = """
    무한한 가능성을 가진 파이썬 프로젝트를 시작하세요!

    사용법:
      inpynit create <프로젝트명>          # 대화형 모드로 프로젝트 생성
      inpynit create <프로젝트명> --quick  # 기본 설정으로 빠른 생성
      inpynit templates                    # 사용 가능한 템플릿 보기

    예시:
      inpynit create my-awesome-project    # 대화형으로 세부 설정
      inpynit create my-api --quick        # 빠른 생성
    """

    panel_content = f"[bold blue]{title}[/bold blue]\n[dim]{subtitle}[/dim]\n{description}"
    console.print(
        Panel(
            panel_content,
            border_style="blue",
            padding=(1, 2),
        )
    )


@main.command()
@click.argument("project_name")
@click.option("--template", "-t", help="사용할 템플릿 (기본값: basic)")
@click.option("--quick", "-q", is_flag=True, help="기본 설정으로 빠른 생성")
def create(project_name, template, quick):
    """새로운 파이썬 프로젝트를 생성합니다."""

    # 빠른 생성 모드
    if quick:
        # Git 사용자 정보 가져오기 (기본값으로 사용)
        git_author, git_email = get_git_user_info()

        config = ProjectConfig(
            name=project_name,
            template=template or "basic",
            author=git_author,
            email=git_email,
            description="",
            python_version="3.11",
            license="MIT",
            use_conda=True,
            use_git=True,
        )
    else:
        # 대화형 모드 (기본)
        project_name, config = interactive_create(project_name, template or "basic")

    # 프로젝트 생성
    creator = ProjectCreator()
    success = creator.create_project(config)

    if not success:
        console.print("❌ 프로젝트 생성에 실패했습니다.", style="red")
        exit(1)


def interactive_create(initial_name, initial_template):
    """대화형 프로젝트 생성"""
    console.print("🎯 대화형 프로젝트 생성을 시작합니다!\n", style="bold blue")

    # 프로젝트 이름
    project_name = click.prompt("프로젝트 이름", default=initial_name, type=str)

    # 템플릿 선택
    templates_info = list_templates_info()
    console.print("\n📋 사용 가능한 템플릿:")
    for name, info in templates_info.items():
        console.print(f"  • {name}: {info['description']}")

    # 사용 가능한 템플릿만 선택 가능하도록 제한
    available_templates = ["basic"]  # 현재 구현된 템플릿만
    template = click.prompt(
        "\n템플릿 선택",
        default=initial_template if initial_template in available_templates else "basic",
        type=click.Choice(available_templates),
    )

    # Git 사용자 정보 가져오기
    git_author, git_email = get_git_user_info()

    # 작성자 정보
    author = click.prompt("작성자", default=git_author)
    email = click.prompt("이메일", default=git_email)
    description = click.prompt("프로젝트 설명", default="", show_default=False)

    # 파이썬 버전 선택
    python_versions = ["3.8", "3.9", "3.10", "3.11", "3.12"]
    console.print(f"\n🐍 사용 가능한 파이썬 버전: {', '.join(python_versions)}")
    python_version = click.prompt("파이썬 버전", default="3.11", type=click.Choice(python_versions))

    # 라이선스 선택
    licenses = ["MIT", "Apache-2.0", "GPL-3.0", "BSD-3-Clause", "ISC", "없음"]
    console.print(f"\n📜 사용 가능한 라이선스: {', '.join(licenses)}")
    license_choice = click.prompt("라이선스", default="MIT", type=click.Choice(licenses))
    license_value = None if license_choice == "없음" else license_choice

    # 추가 옵션들
    use_conda = click.confirm("conda 환경을 생성하시겠습니까?", default=True)
    use_git = click.confirm("Git 저장소를 초기화하시겠습니까?", default=True)

    config = ProjectConfig(
        name=project_name,
        template=template,
        author=author,
        email=email,
        description=description,
        python_version=python_version,
        license=license_value or "MIT",
        use_conda=use_conda,
        use_git=use_git,
    )

    return project_name, config


@main.command()
def templates():
    """사용 가능한 템플릿 목록을 보여줍니다."""
    templates_info = list_templates_info()

    table = Table(title="🎨 사용 가능한 템플릿", show_header=True, header_style="bold magenta")
    table.add_column("템플릿", style="cyan", width=15)
    table.add_column("이름", style="green", width=20)
    table.add_column("설명", style="white")

    for template_id, info in templates_info.items():
        table.add_row(template_id, info["name"], info["description"])

    console.print(table)

    console.print("\n💡 사용법:", style="bold blue")
    console.print("  inpynit create my-project --template <템플릿명>")
    console.print("  inpynit create my-project --interactive")


if __name__ == "__main__":
    main()
