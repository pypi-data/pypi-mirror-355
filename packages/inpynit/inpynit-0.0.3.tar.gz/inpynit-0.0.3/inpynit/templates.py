"""
inpynit 템플릿 관리 모듈
"""

from typing import Any, Dict, List

# 템플릿 설정 정보
TEMPLATE_CONFIGS = {
    "basic": {
        "name": "기본 패키지",
        "description": "기본적인 파이썬 패키지 구조",
        "directories": [
            "{project_slug}",
            "tests",
            "docs",
            ".vscode",
        ],
        "files": [
            {"template": "pyproject.toml.j2", "output": "pyproject.toml"},
            {"template": "README.md.j2", "output": "README.md"},
            {"template": "main.py.j2", "output": "{project_slug}/__init__.py"},
            {"template": "main.py.j2", "output": "{project_slug}/main.py"},
            {"template": "test_main.py.j2", "output": "tests/test_main.py"},
            {"template": "gitignore.j2", "output": ".gitignore"},
            {"template": ".vscode/settings.json.j2", "output": ".vscode/settings.json"},
            {"template": "Makefile.j2", "output": "Makefile"},
        ],
    },
}


def get_available_templates() -> List[str]:
    """
    사용 가능한 템플릿 목록을 반환합니다.

    Returns:
        List[str]: 템플릿 이름 목록
    """
    return list(TEMPLATE_CONFIGS.keys())


def get_template_config(template_name: str) -> Dict[str, Any]:
    """
    특정 템플릿의 설정을 반환합니다.

    Args:
        template_name: 템플릿 이름

    Returns:
        Dict[str, Any]: 템플릿 설정

    Raises:
        KeyError: 존재하지 않는 템플릿
    """
    if template_name not in TEMPLATE_CONFIGS:
        raise KeyError(f"Template '{template_name}' not found")

    return TEMPLATE_CONFIGS[template_name]


def get_template_info(template_name: str) -> Dict[str, str]:
    """
    템플릿의 기본 정보를 반환합니다.

    Args:
        template_name: 템플릿 이름

    Returns:
        Dict[str, str]: 템플릿 정보 (name, description)
    """
    config = get_template_config(template_name)
    return {"name": config["name"], "description": config["description"]}


def list_templates_info() -> Dict[str, Dict[str, str]]:
    """
    모든 템플릿의 정보를 반환합니다.

    Returns:
        Dict[str, Dict[str, str]]: 템플릿별 정보
    """
    return {template_name: get_template_info(template_name) for template_name in get_available_templates()}
