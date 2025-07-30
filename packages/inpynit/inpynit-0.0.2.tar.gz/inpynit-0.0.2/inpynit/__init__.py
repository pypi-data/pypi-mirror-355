"""
inpynit - 무한한 가능성을 가진 파이썬 프로젝트를 시작하게 해주는 도구

이 패키지는 다양한 템플릿을 사용하여 파이썬 프로젝트를 빠르게 생성할 수 있게 해줍니다.
"""

try:
    from ._version import __version__
except ImportError:
    # setuptools-scm이 _version.py를 생성하지 못한 경우 fallback
    try:
        from importlib.metadata import version

        __version__ = version("inpynit")
    except ImportError:
        # Python < 3.8 호환성
        from importlib_metadata import version

        __version__ = version("inpynit")

__author__ = "Your Name"
__email__ = "your.email@example.com"

from .cli import main
from .core import ProjectConfig, ProjectCreator
from .templates import get_available_templates, get_template_config

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "main",
    "ProjectConfig",
    "ProjectCreator",
    "get_available_templates",
    "get_template_config",
]
