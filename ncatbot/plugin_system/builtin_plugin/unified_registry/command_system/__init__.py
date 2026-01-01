"""命令子系统

现代化的命令行参数解析系统。
"""

from .analyzer import FuncAnalyser, get_subclass_recursive
from .registry import command_registry

__all__ = [
    "FuncAnalyser",
    "get_subclass_recursive",
    "command_registry",
]
