"""
OneBot 11 事件系统

提供完整的 OneBot 11 标准事件解析和处理功能。
"""

# 消息段
from .message_segments import (
    MessageSegment,
    MessageArray,
    Text,
    At,
    AtAll,
    Face,
    Reply,
    Image,
    Record,
    Video,
    File,
    Node,
    Forward,
    Share,
    Location,
    Music,
    Json,
    Markdown,
)

# 事件解析器
from .parser import EventParser

# 数据模型
from .models import GroupSender, BaseSender, Anonymous, FileInfo, Status

# 枚举
from .enums import (
    PostType,
    MessageType,
    NoticeType,
    RequestType,
    MetaEventType,
    NotifySubType,
    EventType,
)

# 事件类
from .events import (
    # 基础
    BaseEvent,
    # 消息
    MessageEvent,
    PrivateMessageEvent,
    GroupMessageEvent,
    # 通知
    NoticeEvent,
    GroupUploadNoticeEvent,
    GroupAdminNoticeEvent,
    GroupDecreaseNoticeEvent,
    GroupIncreaseNoticeEvent,
    GroupBanNoticeEvent,
    FriendAddNoticeEvent,
    GroupRecallNoticeEvent,
    FriendRecallNoticeEvent,
    NotifyEvent,
    PokeNotifyEvent,
    LuckyKingNotifyEvent,
    HonorNotifyEvent,
    # 请求
    RequestEvent,
    FriendRequestEvent,
    GroupRequestEvent,
    # 元事件
    MetaEvent,
    LifecycleMetaEvent,
    HeartbeatMetaEvent,
)

# 兼容别名
PlainText = Text

__all__ = [
    # 解析器
    "EventParser",
    # 消息段
    "MessageSegment",
    "MessageArray",
    "Text",
    "PlainText",
    "At",
    "AtAll",
    "Face",
    "Reply",
    "Image",
    "Record",
    "Video",
    "File",
    "Node",
    "Forward",
    "Share",
    "Location",
    "Music",
    "Json",
    "Markdown",
    # 模型
    "GroupSender",
    "BaseSender",
    "Anonymous",
    "FileInfo",
    "Status",
    # 枚举
    "PostType",
    "MessageType",
    "NoticeType",
    "RequestType",
    "MetaEventType",
    "NotifySubType",
    # 事件
    "BaseEvent",
    "MessageEvent",
    "PrivateMessageEvent",
    "GroupMessageEvent",
    "NoticeEvent",
    "GroupUploadNoticeEvent",
    "GroupAdminNoticeEvent",
    "GroupDecreaseNoticeEvent",
    "GroupIncreaseNoticeEvent",
    "GroupBanNoticeEvent",
    "FriendAddNoticeEvent",
    "GroupRecallNoticeEvent",
    "FriendRecallNoticeEvent",
    "NotifyEvent",
    "PokeNotifyEvent",
    "LuckyKingNotifyEvent",
    "HonorNotifyEvent",
    "RequestEvent",
    "FriendRequestEvent",
    "GroupRequestEvent",
    "MetaEvent",
    "LifecycleMetaEvent",
    "HeartbeatMetaEvent",
    # 统一事件类型
    "EventType",
]


