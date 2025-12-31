"""
NcatBot 核心模块

提供 Bot 客户端、事件系统和 API 接口。
"""

from .client import (
    BotClient,
    EventBus,
    NcatBotEvent,
    EventType,
)
from .helper import ForwardConstructor

# 事件类型
from .event import (
    # 基础事件
    BaseEvent,
    MessageEvent,
    PrivateMessageEvent,
    GroupMessageEvent,
    NoticeEvent,
    RequestEvent,
    MetaEvent,
    # 消息段
    MessageArray,
    MessageSegment,
    Text,
    At,
    Image,
    Face,
    Reply,
    File,
    Record,
    Video,
    Node,
    Forward,
)

__all__ = [
    # 核心
    "BotClient",
    "EventBus",
    "NcatBotEvent",
    "ForwardConstructor",
    # 事件类型
    "EventType",
    # 事件
    "BaseEvent",
    "MessageEvent",
    "PrivateMessageEvent",
    "GroupMessageEvent",
    "NoticeEvent",
    "RequestEvent",
    "MetaEvent",
    # 消息段
    "MessageArray",
    "MessageSegment",
    "Text",
    "At",
    "Image",
    "Face",
    "Reply",
    "File",
    "Record",
    "Video",
    "Node",
    "Forward",
]
