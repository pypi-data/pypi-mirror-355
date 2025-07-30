"""
inpynit 유틸리티 함수들
"""

import re
import subprocess


def validate_project_name(name: str) -> bool:
    """
    프로젝트 이름의 유효성을 검사합니다.

    Args:
        name: 검사할 프로젝트 이름

    Returns:
        bool: 유효한 이름인지 여부
    """
    # 파이썬 패키지 이름 규칙에 따라 검증
    pattern = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]*$")
    return bool(pattern.match(name)) and len(name) > 0


def get_git_user_info() -> tuple[str, str]:
    """
    Git 사용자 정보를 가져옵니다.

    Returns:
        tuple: (사용자명, 이메일)
    """
    try:
        # Git 사용자명 가져오기
        name_result = subprocess.run(
            ["git", "config", "--global", "user.name"],
            capture_output=True,
            text=True,
            check=True,
        )
        name = name_result.stdout.strip()

        # Git 이메일 가져오기
        email_result = subprocess.run(
            ["git", "config", "--global", "user.email"],
            capture_output=True,
            text=True,
            check=True,
        )
        email = email_result.stdout.strip()

        return (name, email)
    except subprocess.CalledProcessError:
        return ("Developer", "dev@example.com")
