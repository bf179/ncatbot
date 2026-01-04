"""
NapCat 适配器模块

提供 NapCat 服务的安装、配置、启动、登录等功能。
"""

from .service import (
    launch_napcat_service,
)
from .websocket import NapCatWebSocket


__all__ = [
    "launch_napcat_service",
    "NapCatWebSocket",
]
