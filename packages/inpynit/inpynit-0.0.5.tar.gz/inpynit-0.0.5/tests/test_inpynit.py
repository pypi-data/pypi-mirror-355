"""
inpynit 패키지 기본 테스트
"""

from inpynit.templates import get_available_templates
from inpynit.utils import validate_project_name


def test_validate_project_name():
    """프로젝트 이름 검증 테스트"""
    assert validate_project_name("my-project")
    assert validate_project_name("my_project")
    assert not validate_project_name("123project")
    assert not validate_project_name("")


def test_get_available_templates():
    """템플릿 목록 테스트"""
    templates = get_available_templates()
    assert isinstance(templates, list)
    assert "basic" in templates
