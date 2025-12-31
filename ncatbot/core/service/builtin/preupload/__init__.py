"""
预上传服务

提供消息和文件的预上传功能，包括流式上传。
自己维护独立的 WebSocket 连接。
"""

from .constants import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_FILE_RETENTION,
    StreamStatus,
    StreamResponseType,
)
from .upload_connection import UploadConnection
from .client import (
    StreamUploadClient,
    FileAnalysis,
    ChunkInfo,
    UploadResult,
)
from .utils import (
    DOWNLOADABLE_TYPES,
    is_local_file,
    is_base64_data,
    is_remote_url,
    needs_upload,
    get_local_path,
    extract_base64_data,
    generate_filename_from_type,
)
from .processor import MessagePreUploadProcessor, ProcessResult
from .result import PreUploadResult
from .service import PreUploadService

__all__ = [
    # 常量
    "DEFAULT_CHUNK_SIZE",
    "DEFAULT_FILE_RETENTION",
    "StreamStatus",
    "StreamResponseType",
    # 连接
    "UploadConnection",
    # 客户端
    "StreamUploadClient",
    "FileAnalysis",
    "ChunkInfo",
    "UploadResult",
    # 工具函数
    "DOWNLOADABLE_TYPES",
    "is_local_file",
    "is_base64_data",
    "is_remote_url",
    "needs_upload",
    "get_local_path",
    "extract_base64_data",
    "generate_filename_from_type",
    # 处理器
    "MessagePreUploadProcessor",
    "ProcessResult",
    # 服务
    "PreUploadService",
    "PreUploadResult",
]
