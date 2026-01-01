"""统一注册模块

提供过滤器和命令的统一注册功能。
"""

from .plugin import UnifiedRegistryPlugin
from .filter_system.registry import filter_registry
from .filter_system.decorators import *  # noqa: F401,F403
from .command_system import command_registry
from .command_system.registry import option, param, option_group
from .filter_system import *  # noqa: F401,F403

__all__ = [
    "UnifiedRegistryPlugin",
    "command_registry",
    "filter_registry",
    "option",
    "param",
    "option_group",
]

__all__.extend(getattr(filter_system, "__all__", [])) # type: ignore
