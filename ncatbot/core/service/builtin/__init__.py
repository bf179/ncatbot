"""
内置服务

提供 NcatBot 核心功能所需的内置服务。
"""

from .message_router import MessageRouter
from .preupload import (
    # 常量
    DEFAULT_CHUNK_SIZE,
    DEFAULT_FILE_RETENTION,
    StreamStatus,
    StreamResponseType,
    # 客户端
    StreamUploadClient,
    FileAnalysis,
    ChunkInfo,
    UploadResult,
    # 工具函数
    DOWNLOADABLE_TYPES,
    is_local_file,
    is_base64_data,
    is_remote_url,
    needs_upload,
    get_local_path,
    extract_base64_data,
    generate_filename_from_type,
    # 处理器
    MessagePreUploadProcessor,
    ProcessResult,
    # 服务
    PreUploadService,
    PreUploadResult,
)

__all__ = [
    # 消息路由
    "MessageRouter",
    # 预上传常量
    "DEFAULT_CHUNK_SIZE",
    "DEFAULT_FILE_RETENTION",
    "StreamStatus",
    "StreamResponseType",
    # 预上传客户端
    "StreamUploadClient",
    "FileAnalysis",
    "ChunkInfo",
    "UploadResult",
    # 预上传工具函数
    "DOWNLOADABLE_TYPES",
    "is_local_file",
    "is_base64_data",
    "is_remote_url",
    "needs_upload",
    "get_local_path",
    "extract_base64_data",
    "generate_filename_from_type",
    # 预上传处理器
    "MessagePreUploadProcessor",
    "ProcessResult",
    # 预上传服务
    "PreUploadService",
    "PreUploadResult",
]
