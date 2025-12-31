"""
事件类 - 兼容性重定向

NcatBotEvent 已移至 ncatbot.core.client.event
此文件保留以兼容旧代码的直接导入。
"""

# 从新位置导入
from ncatbot.core.client.ncatbot_event import NcatBotEvent, NcatBotEventFactory

__all__ = ["NcatBotEvent", "NcatBotEventFactory"]
