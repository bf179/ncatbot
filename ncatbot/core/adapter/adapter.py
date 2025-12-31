"""
WebSocket 适配器

负责与 NapCat 服务的 WebSocket 通信，包括消息收发。
事件分发由 EventBus 统一处理。
"""

import asyncio
import json
import traceback
from typing import Dict, Callable, Optional, Any, Awaitable
import uuid
from threading import Lock
from queue import Queue

import websockets
from websockets.exceptions import ConnectionClosedError

from .nc import napcat_service_ok
from ncatbot.utils import get_log, ncatbot_config
from ncatbot.utils.error import NcatBotError, NcatBotConnectionError

LOG = get_log("Adapter")


class Adapter:
    """
    WebSocket 适配器
    
    职责：仅负责 WebSocket 通信
    - 建立/维护连接
    - 发送 API 请求
    - 接收消息并传递给事件回调
    
    不负责：
    - 事件类型判断（由 EventBus 处理）
    - 事件解析（由 Client 处理）
    """

    def __init__(self, event_callback: Optional[Callable[[dict], Awaitable[None]]] = None):
        """
        Args:
            event_callback: 收到事件时的回调，接收原始 dict 数据
        """
        self._client: Optional[websockets.ClientConnection] = None
        self._pending: Dict[str, Queue] = {}
        self._lock = Lock()
        self._event_callback = event_callback

    # ==================== 公开接口 ====================

    @property
    def connected(self) -> bool:
        return self._client is not None

    def set_event_callback(self, callback: Callable[[dict], Awaitable[None]]):
        """设置事件回调（延迟设置）"""
        self._event_callback = callback

    async def send(self, action: str, params: Optional[dict] = None, timeout: float = 300.0) -> dict:
        """发送 API 请求并等待响应"""
        if not self._client:
            raise ConnectionError("WebSocket 未连接")

        echo = str(uuid.uuid4())
        queue = Queue(maxsize=1)

        with self._lock:
            self._pending[echo] = queue

        try:
            await self._client.send(json.dumps({
                "action": action.replace("/", ""),
                "params": params or {},
                "echo": echo,
            }))
            return await asyncio.to_thread(queue.get, timeout=timeout)
        finally:
            with self._lock:
                self._pending.pop(echo, None)

    async def connect(self) -> None:
        """连接并开始监听消息"""
        uri = ncatbot_config.get_uri_with_token()
        self._client = await websockets.connect(
            uri, close_timeout=0.2, max_size=2**30, open_timeout=1
        )
        LOG.info("WebSocket 连接成功")

        while True:
            try:
                async for raw in self._client:
                    data = json.loads(raw)
                    if "echo" in data:
                        # API 响应
                        self._dispatch_response(data)
                    else:
                        # 事件 - 直接传递原始数据给回调
                        if self._event_callback:
                            await self._event_callback(data)

            except asyncio.CancelledError:
                await self._cleanup()
                raise

            except ConnectionClosedError:
                LOG.info("连接断开，尝试重连...")
                if not await self._reconnect(uri):
                    raise NcatBotConnectionError("重连失败")

            except Exception:
                await self._cleanup()
                LOG.error(traceback.format_exc())
                raise NcatBotError("网络错误")

    # ==================== 内部方法 ====================

    def _dispatch_response(self, data: dict):
        """分发 API 响应"""
        with self._lock:
            echo = data.get("echo")
            if echo:
                queue = self._pending.get(echo)
                if queue:
                    queue.put(data)

    async def _reconnect(self, uri: str) -> bool:
        """尝试重连"""
        if napcat_service_ok(ncatbot_config.websocket_timeout):
            self._client = await websockets.connect(
                uri, close_timeout=0.2, max_size=2**30, open_timeout=1
            )
            LOG.info("重连成功")
            return True
        return False

    async def _cleanup(self):
        """清理资源"""
        with self._lock:
            self._pending.clear()
        if self._client:
            await self._client.close()
            self._client = None
        LOG.info("连接已关闭")
