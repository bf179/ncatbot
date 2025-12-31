"""
事件总线 - 兼容性重定向

EventBus 已移至 ncatbot.core.client.event_bus
此文件保留以兼容旧代码的直接导入。
"""

# 从新位置导入
from ncatbot.core.client.event_bus import EventBus, HandlerTimeoutError, _compile_regex

__all__ = ["EventBus", "HandlerTimeoutError", "_compile_regex"]
