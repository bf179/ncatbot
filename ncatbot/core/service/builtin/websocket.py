"""
WebSocket 服务

提供与 NapCat 服务的 WebSocket 通信功能。
"""

import asyncio
import json
import uuid
from typing import Dict, Optional, Callable, Awaitable, Any
from threading import Lock
from queue import Queue

import websockets
from websockets.exceptions import ConnectionClosedError

from ..base import BaseService
from ncatbot.utils import get_log, ncatbot_config
from ncatbot.utils.error import NcatBotConnectionError

LOG = get_log("WebSocketService")


class WebSocketService(BaseService):
    """
    WebSocket 服务
    
    负责与 NapCat 服务的 WebSocket 通信，包括：
    - 建立/维护连接
    - 发送 API 请求并等待响应
    - 接收事件并传递给回调
    """
    
    name = "websocket"
    description = "WebSocket 通信服务"
    
    def __init__(
        self, 
        event_callback: Optional[Callable[[dict], Awaitable[None]]] = None,
        **config
    ):
        """
        Args:
            event_callback: 收到事件时的回调
        """
        super().__init__(**config)
        self._client: Optional[websockets.ClientConnection] = None
        self._pending: Dict[str, Queue] = {}
        self._lock = Lock()
        self._event_callback = event_callback
        self._running = False
        self._listen_task: Optional[asyncio.Task] = None
    
    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------
    
    async def on_load(self) -> None:
        """连接 WebSocket"""
        uri = ncatbot_config.get_uri_with_token()
        self._client = await websockets.connect(
            uri, close_timeout=0.2, max_size=2**30, open_timeout=1
        )
        self._running = True
        LOG.info("WebSocket 连接成功")
    
    async def on_close(self) -> None:
        """关闭 WebSocket 连接"""
        self._running = False
        
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
            self._listen_task = None
        
        with self._lock:
            self._pending.clear()
        
        if self._client:
            await self._client.close()
            self._client = None
        
        LOG.info("WebSocket 连接已关闭")
    
    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------
    
    @property
    def connected(self) -> bool:
        """是否已连接"""
        return self._client is not None and self._running
    
    def set_event_callback(self, callback: Callable[[dict], Awaitable[None]]) -> None:
        """设置事件回调"""
        self._event_callback = callback
    
    async def send(
        self, 
        action: str, 
        params: Optional[dict] = None, 
        timeout: float = 300.0
    ) -> dict:
        """
        发送 API 请求并等待响应
        
        Args:
            action: API 动作名
            params: 请求参数
            timeout: 超时时间（秒）
            
        Returns:
            API 响应字典
        """
        if not self._client:
            raise ConnectionError("WebSocket 未连接")
        
        echo = str(uuid.uuid4())
        queue: Queue = Queue(maxsize=1)
        
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
    
    async def listen(self) -> None:
        """
        开始监听消息
        
        此方法会阻塞，持续接收消息直到连接断开或服务关闭。
        """
        if not self._client:
            raise ConnectionError("WebSocket 未连接")
        
        uri = ncatbot_config.get_uri_with_token()
        
        while self._running:
            try:
                async for raw in self._client:
                    if not self._running:
                        break
                    
                    data = json.loads(raw)
                    
                    if "echo" in data:
                        # API 响应
                        self._dispatch_response(data)
                    else:
                        # 事件
                        if self._event_callback:
                            await self._event_callback(data)
            
            except asyncio.CancelledError:
                break
            
            except ConnectionClosedError:
                if not self._running:
                    break
                    
                LOG.info("连接断开，尝试重连...")
                if await self._reconnect(uri):
                    continue
                else:
                    raise NcatBotConnectionError("重连失败")
            
            except Exception as e:
                LOG.error(f"WebSocket 错误: {e}")
                raise
    
    def start_listening(self) -> asyncio.Task:
        """
        启动监听任务（非阻塞）
        
        Returns:
            监听任务
        """
        self._listen_task = asyncio.create_task(self.listen())
        return self._listen_task
    
    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------
    
    def _dispatch_response(self, data: dict) -> None:
        """分发 API 响应"""
        with self._lock:
            echo = data.get("echo")
            if echo:
                queue = self._pending.get(echo)
                if queue:
                    queue.put(data)
    
    async def _reconnect(self, uri: str) -> bool:
        """尝试重连"""
        from ncatbot.core.adapter.nc import napcat_service_ok
        
        if napcat_service_ok(ncatbot_config.websocket_timeout):
            try:
                self._client = await websockets.connect(
                    uri, close_timeout=0.2, max_size=2**30, open_timeout=1
                )
                LOG.info("重连成功")
                return True
            except Exception as e:
                LOG.error(f"重连失败: {e}")
        return False
